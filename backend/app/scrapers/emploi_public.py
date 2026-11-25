"""Scraper for the official portal emploi-public.ma (French pages).

``/fr/concours-liste`` is server-rendered and lists announcements as cards with the grade
(in the title), employer, post count, deadline and exam date. ``/fr/concours/details/<uuid>``
adds the specialties and the official concours code ("C 44904/26"), which is also embedded
in wadifapublic.ma URLs and is used for cross-source dedup. robots.txt only blocks the
``download`` paths, which we never request. See plan/sources-recon.md.
"""
from __future__ import annotations

import re
from urllib.parse import unquote, urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from app.db.models import CompetitionStage, RawAnnouncement, SourceType
from app.scrapers.base import get_html, make_client
from app.scrapers.dates import parse_date, parse_int

BASE = "https://www.emploi-public.ma"
LISTING_PATH = "/fr/concours-liste"
MAX_PAGES = 3  # a light crawler: the first pages hold everything new since the last run

_TITLE_PREFIX = re.compile(r"^\s*Avis de concours de recrutement de\s+", re.IGNORECASE)
_SPEC_BULLET = re.compile(r"^[-\s]+")


def _card_footer_value(card: Tag, label: str) -> str | None:
    for div in card.select(".card-footer div"):
        text = " ".join(div.get_text(" ", strip=True).split())
        if text.startswith(label):
            return text[len(label) :].strip(" :")
    return None


def _parse_card(card: Tag) -> RawAnnouncement | None:
    title_el = card.select_one(".card-title")
    if title_el is None:
        return None
    kind = card.select_one(".card-type")
    if kind is not None and kind.get_text(strip=True).lower() != "annonce":
        return None  # convocations and results are not publishable announcements
    title = " ".join(title_el.get_text(" ", strip=True).split())
    admin_el = card.select_one(".card-text")
    administration = " ".join(admin_el.get_text(" ", strip=True).split()) if admin_el else None
    img = card.find("img")
    posts = None
    for div in card.select(".card-footer div"):
        t = div.get_text(" ", strip=True)
        if re.match(r"^\d+\s+poste", t):
            posts = parse_int(t)
            break
    url = urljoin(BASE + "/", card["href"].strip())
    return RawAnnouncement(
        source_name="emploi-public.ma",
        source_type=SourceType.PORTAL,
        source_url=url,
        detail_url=url,
        official_url=url,
        title=title,
        text=" | ".join(x for x in (title, administration) if x),
        lang="fr",
        stage=CompetitionStage.AVIS,
        administration=administration,
        grade=_TITLE_PREFIX.sub("", title) or None,
        post_count=posts,
        deadline=parse_date(_card_footer_value(card, "Limite de dépôt")),
        exam_date=parse_date(_card_footer_value(card, "Date du concours")),
        logo_url=urljoin(BASE + "/", img["src"]) if img and img.get("src") else None,
    )


def parse_listing_html(html: str) -> list[RawAnnouncement]:
    """Parse one listing page into announcements (no network I/O)."""
    soup = BeautifulSoup(html, "lxml")
    out: list[RawAnnouncement] = []
    seen: set[str] = set()
    for card in soup.select("a.card[href*='/concours/details/']"):
        ann = _parse_card(card)
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


def parse_detail_html(html: str, ann: RawAnnouncement) -> RawAnnouncement:
    """Return a copy of ``ann`` completed with specialties, concours code and exam date."""
    soup = BeautifulSoup(html, "lxml")
    tokens = list(soup.stripped_strings)
    update: dict = {}

    if "Spécialité :" in tokens and "Nombre de postes :" in tokens:
        a, b = tokens.index("Spécialité :"), tokens.index("Nombre de postes :")
        specs = [_SPEC_BULLET.sub("", t).rstrip(" ;") for t in tokens[a + 1 : b]]
        specs = [s for s in specs if s]
        if specs:
            update["specialty"] = " / ".join(specs)
    if "Code du concours :" in tokens:
        k = tokens.index("Code du concours :")
        code = " ".join(tokens[k + 1 : k + 3])
        if re.fullmatch(r"[A-Z] \d+/\d+", code):
            update["reference_code"] = code
    if ann.post_count is None:
        update["post_count"] = parse_int(_value_after(tokens, "Nombre de postes :"))
    if ann.exam_date is None:
        update["exam_date"] = parse_date(_value_after(tokens, "Date du concours"))
    if ann.deadline is None:
        update["deadline"] = parse_date(_value_after(tokens, "Délai de dépôt des candidatures"))
    return ann.model_copy(update=update)


# ---- Arabic pages: all four stages ------------------------------------------------------
# The listing filter ``procedure`` matches the portal's own timeline:
# Annonce -> Convocation écrit -> Convocation oral -> Résultats.
AR_LISTING_PATH = "/ar/قائمة-المباريات"
AR_DETAIL_SEGMENT = "/تفاصيل/المباريات/"
AR_DOWNLOAD = BASE + "/ar/تحميل/المباريات"  # linked from buttons only (robots.txt: no fetching)
STAGE_LISTINGS: list[tuple[CompetitionStage, str, int]] = [
    (CompetitionStage.AVIS, "avis", MAX_PAGES),
    (CompetitionStage.CONVOQUES, "convocation", 2),
    (CompetitionStage.CONVOQUES_ORAL, "oral", 2),
    (CompetitionStage.RESULTATS, "resultat", 2),
]
# The default listing only shows part of the portal: each administration type is its own view.
ADMIN_TYPES = ["service_etat", "collec", "etab_publics"]
STAGE_PDF = {
    CompetitionStage.CONVOQUES: "list_convoques",
    CompetitionStage.CONVOQUES_ORAL: "list_convoques_oral",
    CompetitionStage.RESULTATS: "list_resultats",
}
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
# "مباراة لتوظيف X", "لائحة المدعوين لإجراء الاختبار الكتابي لمباراة توظيف X",
# "لائحة الناجحين في مباراة التوظيف X": the grade is what follows the last "توظيف".
_AR_TITLE_PREFIX = re.compile(r"^.*?(?:لتوظيف|التوظيف|توظيف)\s+")
_AR_POSTS = re.compile(r"^(\d+)\s+(?:مناصب|منصب|منصبا)")
_AR_DEADLINE = "آخر أجل لإيداع ملفات الترشيح"
_AR_EXAM = "تاريخ إجراء المباراة"
_DEFAULT_LOGO = "default-image"
_CITY = re.compile(r"(?:عمالة\s+)?(?:إقليم|عمالة|جماعة)\s+([^\-–()]+)")


def concours_uuid(url: str | None) -> str | None:
    """The portal's concours id, shared by the announcement and all its stages."""
    m = _UUID.search(url or "")
    return m.group(0) if m else None


def _city_from_admin(admin: str | None) -> str | None:
    m = _CITY.search(admin or "")
    return m.group(1).strip() if m else None


def _ar_footer(card: Tag) -> dict[str, str]:
    out: dict[str, str] = {}
    for div in card.select(".card-footer div"):
        text = " ".join(div.get_text(" ", strip=True).split())
        if _AR_POSTS.match(text):
            out["posts"] = text
        elif text.startswith(_AR_DEADLINE):
            out["deadline"] = text
        elif text.startswith(_AR_EXAM):
            out["exam"] = text
    return out


def _parse_ar_card(card: Tag, stage: CompetitionStage) -> RawAnnouncement | None:
    title_el = card.select_one(".card-title")
    uuid = concours_uuid(card.get("href"))
    if title_el is None or uuid is None:
        return None
    title = " ".join(title_el.get_text(" ", strip=True).split())
    admin_el = card.select_one(".card-text")
    administration = " ".join(admin_el.get_text(" ", strip=True).split()) if admin_el else None
    foot = _ar_footer(card)
    img = card.find("img")
    src = img.get("src") if img else None
    url = urljoin(BASE + "/", card["href"].strip())
    return RawAnnouncement(
        source_name="emploi-public.ma",
        source_type=SourceType.PORTAL,
        source_url=url,
        detail_url=url,
        official_url=url,
        title=title,
        text=" | ".join(x for x in (title, administration) if x),
        lang="ar",
        stage=stage,
        administration=administration,
        grade=_AR_TITLE_PREFIX.sub("", title) or None,
        post_count=parse_int(foot.get("posts")),
        deadline=parse_date(foot.get("deadline")),
        # On oral and result cards this date is the written exam, already past.
        exam_date=parse_date(foot.get("exam")) if stage in (
            CompetitionStage.AVIS, CompetitionStage.CONVOQUES) else None,
        logo_url=urljoin(BASE + "/", src) if src and _DEFAULT_LOGO not in src else None,
        city=_city_from_admin(administration),
        list_pdf_url=f"{AR_DOWNLOAD}/{STAGE_PDF[stage]}/{uuid}" if stage in STAGE_PDF else None,
    )


def parse_ar_listing_html(html: str, stage: CompetitionStage) -> list[RawAnnouncement]:
    """Parse one Arabic listing page (any stage) without network I/O."""
    soup = BeautifulSoup(html, "lxml")
    out: list[RawAnnouncement] = []
    seen: set[str] = set()
    for card in soup.select("a.card[href]"):
        if AR_DETAIL_SEGMENT not in unquote(card["href"]):
            continue
        ann = _parse_ar_card(card, stage)
        if ann is None or ann.source_url in seen:
            continue
        seen.add(ann.source_url)
        out.append(ann)
    return out


def _clean_spec(token: str) -> str:
    return _SPEC_BULLET.sub("", token.replace("\t", " ")).strip(" ؛;.-")


def parse_ar_detail_html(html: str, ann: RawAnnouncement) -> RawAnnouncement:
    """Complete an Arabic item with grade, specialties, post count and concours code."""
    tokens = [" ".join(t.split()) for t in BeautifulSoup(html, "lxml").stripped_strings]
    update: dict = {}
    grade = _value_after(tokens, "الدرجة :")
    if grade:
        update["grade"] = grade
    if "تخصص :" in tokens and "عدد المناصب :" in tokens:
        a, b = tokens.index("تخصص :"), tokens.index("عدد المناصب :")
        specs = [s for s in (_clean_spec(t) for t in tokens[a + 1 : b]) if s]
        if specs:
            update["specialty"] = " / ".join(specs)
    if ann.post_count is None:
        update["post_count"] = parse_int(_value_after(tokens, "عدد المناصب :"))
    if "رمز المباراة :" in tokens:
        k = tokens.index("رمز المباراة :")
        code = " ".join(tokens[k + 1 : k + 3])
        if re.fullmatch(r"[A-Z] \d+/\d+", code):
            update["reference_code"] = code
    if ann.deadline is None:
        update["deadline"] = parse_date(_value_after(tokens, "آخر أجل لإيداع الترشيحات"))
    return ann.model_copy(update=update)


class EmploiPublicScraper:
    source_name = "emploi-public.ma"

    def fetch(self) -> list[RawAnnouncement]:
        results: list[RawAnnouncement] = []
        with make_client() as client:
            first = True
            for stat in ADMIN_TYPES:
                for stage, procedure, pages in STAGE_LISTINGS:
                    for page in range(1, pages + 1):
                        url = (f"{BASE}{AR_LISTING_PATH}?procedure={procedure}"
                               f"&stat={stat}&page={page}")
                        try:
                            html = get_html(client, url)
                        except Exception:  # noqa: BLE001 (one page must not kill the run)
                            if first:
                                raise  # the source is down or blocking us: report it
                            break
                        first = False
                        found = parse_ar_listing_html(html, stage)
                        for ann in found:
                            ann.feed = f"{self.source_name}:{stat}"
                        results.extend(found)
                        if len(found) < 9:  # last real page (4 featured cards repeat)
                            break
        return results

    def enrich(self, ann: RawAnnouncement, client: httpx.Client | None = None) -> RawAnnouncement:
        """Fetch the detail page; on any failure return ``ann`` unchanged."""
        own = client is None
        client = client or make_client()
        parse = parse_ar_detail_html if ann.lang == "ar" else parse_detail_html
        try:
            return parse(get_html(client, ann.detail_url or ann.source_url), ann)
        except Exception:  # noqa: BLE001
            return ann
        finally:
            if own:
                client.close()
