"""Scraper for wadifapublic.ma (Arabic pages).

The site is a server-rendered Next.js app. The concours listing already carries the
employer, grade, specialties, post count and deadline, so the listing is enough to build
an announcement. ``enrich_detail`` adds what the listing lacks (exam date, official link).
robots.txt allows ``/ar/`` pages and ``?page=N``; it forbids ``/api/``, ``?q=`` and
``?status=``, which we never request. See plan/sources-recon.md.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.db.models import CompetitionStage, RawAnnouncement, SourceType
from app.scrapers.base import get_html, make_client
from app.scrapers.dates import parse_date, parse_int

BASE = "https://www.wadifapublic.ma"
LISTING_PATH = "/ar/الوظيفة-العمومية/مباريات"
MAX_PAGES = 3  # a light crawler: the first pages hold everything new since the last run

_DETAIL_HREF = re.compile(r"/c\d+-\d+/")
_CODE_IN_URL = re.compile(r"/c(\d+)-(\d+)/")
_EMPLOYER_LABEL = "الجهة المشغلة"
_PUBLISHED_LABEL = "تاريخ النشر الرسمي"
_DEADLINE_LABEL = "آخر أجل"
_COUNT_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")


# Stage listings (allowed by robots.txt, unlike the ``?status=`` filters).
STAGE_PATHS = ["/ar/استدعاءات-المباريات", "/ar/نتائج-المباريات"]


def _stage_from_badge(badge: str) -> CompetitionStage | None:
    """Map the card badge to a stage; None for badges we do not publish (e.g. postponed)."""
    b = badge.strip()
    if b == "إعلان":
        return CompetitionStage.AVIS
    if "شفو" in b or "شفه" in b:
        return CompetitionStage.CONVOQUES_ORAL
    if "كتاب" in b or "استدعاء" in b:
        return CompetitionStage.CONVOQUES
    if "نتيج" in b or "نتائج" in b:
        return CompetitionStage.RESULTATS
    return None


# Words in the attachment titles of the detail page, per stage.
_PDF_HINTS = {
    CompetitionStage.CONVOQUES: ("للكتابي", "الكتابي"),
    CompetitionStage.CONVOQUES_ORAL: ("للشفوي", "الشفوي", "الشفهي"),
    CompetitionStage.RESULTATS: ("النتائج", "الناجحين"),
}


def _reference_code(href: str) -> str | None:
    m = _CODE_IN_URL.search(href)
    return f"C {m.group(1)}/{m.group(2)}" if m else None


def _logo_url(card: Tag) -> str | None:
    """The card thumbnail is a next/image URL wrapping /logos/<id>.<ext>; return the original."""
    img = card.find("img")
    src = img.get("src") if img else None
    if not src:
        return None
    inner = parse_qs(urlparse(src).query).get("url")
    return urljoin(BASE + "/", unquote(inner[0])) if inner else urljoin(BASE + "/", src)


def _parse_card(card: Tag) -> RawAnnouncement | None:
    tokens = list(card.stripped_strings)
    if _EMPLOYER_LABEL not in tokens:
        return None
    i = tokens.index(_EMPLOYER_LABEL)
    try:
        administration = tokens[i + 1]
        post_count = parse_int(tokens[i + 2])
        title = tokens[i + 4]
        stage = _stage_from_badge(tokens[i + 5])
        published = parse_date(tokens[i + 6])
        city = tokens[i + 8]
        grade = tokens[i + 9]
    except IndexError:
        return None
    if stage is None:
        return None

    j = next((k for k, t in enumerate(tokens) if t.startswith(_PUBLISHED_LABEL)), len(tokens))
    specialties = [t for t in tokens[i + 10 : j]]
    deadline = None
    for k, t in enumerate(tokens):
        if t.startswith(_DEADLINE_LABEL) and k + 1 < len(tokens):
            deadline = parse_date(tokens[k + 1])
            break

    href = card["href"].strip()
    url = urljoin(BASE + "/", href)
    return RawAnnouncement(
        source_name="wadifapublic.ma",
        source_type=SourceType.AGGREGATOR,
        source_url=url,
        detail_url=url,
        title=title,
        text=" | ".join([administration, grade, *specialties, city]),
        lang="ar",
        stage=stage,
        administration=administration,
        grade=grade,
        specialty=" / ".join(specialties) or None,
        post_count=post_count,
        deadline=deadline,
        logo_url=_logo_url(card),
        reference_code=_reference_code(href),
        city=city or None,
        published=published,
    )


def parse_listing_html(html: str) -> list[RawAnnouncement]:
    """Parse one listing page into announcements (no network I/O)."""
    soup = BeautifulSoup(html, "lxml")
    out: list[RawAnnouncement] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        if not _DETAIL_HREF.search(a["href"]) or _EMPLOYER_LABEL not in a.get_text():
            continue
        ann = _parse_card(a)
        if ann is None or ann.source_url in seen:
            continue
        seen.add(ann.source_url)
        out.append(ann)
    return out


def _value_after(tokens: list[str], label: str) -> str | None:
    for k, t in enumerate(tokens):
        if t == label and k + 1 < len(tokens):
            return tokens[k + 1]
    return None


def _official_link(soup: BeautifulSoup) -> str | None:
    """The 'apply' redirect points to the official emploi-public.ma page."""
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/redirect?" not in href:
            continue
        q = parse_qs(urlparse(href).query)
        if q.get("type", [""])[0] == "apply" and q.get("to"):
            return unquote(q["to"][0])
    return None


def _list_pdf(soup: BeautifulSoup, stage: CompetitionStage) -> str | None:
    """The convocation or results PDF of this stage (an official emploi-public.ma link)."""
    hints = _PDF_HINTS.get(stage)
    if not hints:
        return None
    found = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/redirect?" not in href:
            continue
        q = parse_qs(urlparse(href).query)
        if q.get("type", [""])[0] != "pdf" or not q.get("to"):
            continue
        if any(h in a.get_text(" ", strip=True) for h in hints):
            found = unquote(q["to"][0])  # keep the last match: the newest document
    return found


def parse_detail_html(html: str, ann: RawAnnouncement) -> RawAnnouncement:
    """Return a copy of ``ann`` completed with fields found on the detail page."""
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main") or soup
    tokens = list(main.stripped_strings)
    update: dict = {}
    if ann.stage != CompetitionStage.AVIS:
        pdf = _list_pdf(soup, ann.stage)
        if pdf:
            update["list_pdf_url"] = pdf
    exam = parse_date(_value_after(tokens, "تاريخ الاختبار:"))
    if exam is None and ann.stage != CompetitionStage.CONVOQUES_ORAL:
        # The card's concours date is the written exam: never show it on an oral post.
        exam = parse_date(_value_after(tokens, "تاريخ إجراء المباراة"))
    if exam:
        update["exam_date"] = exam
    if ann.post_count is None:
        update["post_count"] = parse_int(_value_after(tokens, "عدد المناصب"))
    if ann.grade is None:
        update["grade"] = _value_after(tokens, "الدرجة / المنصب")
    if ann.deadline is None:
        update["deadline"] = parse_date(_value_after(tokens, "آخر أجل للترشيح"))
    if "التخصصات المطلوبة" in tokens and "تفاصيل الإعلان" in tokens:
        a, b = tokens.index("التخصصات المطلوبة"), tokens.index("تفاصيل الإعلان")
        specs = [_COUNT_SUFFIX.sub("", t) for t in tokens[a + 1 : b]]
        if specs and not ann.specialty:
            update["specialty"] = " / ".join(specs)
    og = soup.find("meta", property="og:image")
    if ann.logo_url is None and og and og.get("content"):
        update["logo_url"] = og["content"]
    official = _official_link(soup)
    if official:
        update["official_url"] = official
    return ann.model_copy(update=update)


class WadifaPublicScraper:
    source_name = "wadifapublic.ma"

    def fetch(self) -> list[RawAnnouncement]:
        results: list[RawAnnouncement] = []
        with make_client() as client:
            for page in range(1, MAX_PAGES + 1):
                url = BASE + LISTING_PATH + ("" if page == 1 else f"?page={page}")
                try:
                    html = get_html(client, url)
                except Exception:  # noqa: BLE001 (one page failing must not kill the run)
                    if page == 1:
                        raise  # the source is down or blocking us: report it
                    break
                results.extend(parse_listing_html(html))
            for path in STAGE_PATHS:  # first page only: the newest convocations and results
                try:
                    html = get_html(client, BASE + path)
                except Exception:  # noqa: BLE001
                    continue
                results.extend(
                    a for a in parse_listing_html(html) if a.stage != CompetitionStage.AVIS
                )
        return results

    def enrich(self, ann: RawAnnouncement, client: httpx.Client | None = None) -> RawAnnouncement:
        """Fetch the detail page; on any failure return ``ann`` unchanged."""
        own = client is None
        client = client or make_client()
        try:
            return parse_detail_html(get_html(client, ann.detail_url or ann.source_url), ann)
        except Exception:  # noqa: BLE001
            return ann
        finally:
            if own:
                client.close()
