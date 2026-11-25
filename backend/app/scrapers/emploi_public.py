"""Scraper for the official portal emploi-public.ma (French pages).

``/fr/concours-liste`` is server-rendered and lists announcements as cards with the grade
(in the title), employer, post count, deadline and exam date. ``/fr/concours/details/<uuid>``
adds the specialties and the official concours code ("C 44904/26"), which is also embedded
in wadifapublic.ma URLs and is used for cross-source dedup. robots.txt only blocks the
``download`` paths, which we never request. See plan/sources-recon.md.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

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


class EmploiPublicScraper:
    source_name = "emploi-public.ma"

    def fetch(self) -> list[RawAnnouncement]:
        results: list[RawAnnouncement] = []
        with make_client() as client:
            for page in range(1, MAX_PAGES + 1):
                url = BASE + LISTING_PATH + ("" if page == 1 else f"?page={page}")
                try:
                    html = get_html(client, url)
                except Exception:  # noqa: BLE001 (one page failing must not kill the run)
                    break
                results.extend(parse_listing_html(html))
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
