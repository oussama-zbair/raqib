"""Scraper for the central portal emploi-public.ma.

Covers the three lifecycle sections:
  - Avis de concours  (announcements)
  - Candidats convoqués (convocation lists, often PDFs)
  - Résultats           (results, often PDFs)

The portal publishes both French and Arabic content. Because government portal markup
changes over time, parsing is defensive: we extract listing rows heuristically (links +
nearby text + attached PDFs) rather than depending on brittle, exact selectors. Anything
we can't structure here is later handed to the Gemini fallback extractor.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.db.models import CompetitionStage, RawAnnouncement, SourceType
from app.scrapers.base import get_html, make_client

BASE = "https://www.emploi-public.ma"

# Section entry points. Real slugs may differ; these are configurable in one place.
SECTIONS: dict[CompetitionStage, list[str]] = {
    CompetitionStage.AVIS: [
        "/fr/annonces.aspx",
        "/ar/annonces.aspx",
    ],
    CompetitionStage.CONVOQUES: [
        "/fr/ListeConvocation.aspx",
        "/ar/ListeConvocation.aspx",
    ],
    CompetitionStage.RESULTATS: [
        "/fr/Resultats.aspx",
        "/ar/Resultats.aspx",
    ],
}

_PDF_RE = re.compile(r"\.pdf(\?|$)", re.IGNORECASE)


def _lang_from_path(path: str) -> str:
    return "ar" if "/ar/" in path else "fr"


def _absolute(href: str) -> str:
    return urljoin(BASE + "/", href)


def _extract_rows(
    html: str, section_url: str, stage: CompetitionStage
) -> list[RawAnnouncement]:
    soup = BeautifulSoup(html, "lxml")
    lang = _lang_from_path(section_url)
    announcements: list[RawAnnouncement] = []

    # Heuristic: each meaningful listing is an anchor whose text is reasonably long,
    # or a table row containing an anchor. Collect the anchor, its text, and any PDF.
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True)
        if not href or href.startswith("#") or href.lower().startswith("javascript"):
            continue
        if len(text) < 8:  # skip nav/pagination links
            continue

        detail_url = _absolute(href)
        if detail_url in seen:
            continue
        seen.add(detail_url)

        is_pdf = bool(_PDF_RE.search(href))
        # Pull a bit of surrounding context (row text) to enrich the announcement text.
        container = a.find_parent(["tr", "li", "div"]) or a
        context = container.get_text(" ", strip=True)

        announcements.append(
            RawAnnouncement(
                source_name="emploi-public.ma",
                source_type=SourceType.PORTAL,
                source_url=detail_url,
                title=text[:300],
                text=context[:2000],
                lang=lang,
                stage=stage,
                pdf_urls=[detail_url] if is_pdf else [],
                detail_url=detail_url,
            )
        )

    return announcements


class EmploiPublicScraper:
    source_name = "emploi-public.ma"

    def fetch(self) -> list[RawAnnouncement]:
        results: list[RawAnnouncement] = []
        with make_client() as client:
            for stage, paths in SECTIONS.items():
                for path in paths:
                    url = BASE + path
                    try:
                        html = get_html(client, url)
                    except Exception:  # noqa: BLE001 — one section failing must not kill the run
                        continue
                    results.extend(_extract_rows(html, path, stage))
        return results


def parse_listing_html(
    html: str, section_url: str, stage: CompetitionStage
) -> list[RawAnnouncement]:
    """Public helper (used by tests) to parse a listing page without network I/O."""
    return _extract_rows(html, section_url, stage)
