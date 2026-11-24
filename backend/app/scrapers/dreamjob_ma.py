"""Scraper for dreamjob.ma through its public RSS feed.

Cloudflare blocks every HTML page of the site for non-browser clients (HTTP 403), but
``/feed/`` answers normally and is listed in the site's own ``<link rel="alternate">``.
The feed mixes private and public sector items. Public sector concours live under
``/emploi-public/`` and carry the category "Emploi Public"; everything else is dropped here.
Detail pages are not fetchable, so the feed text is all we get (no deadline, no specialties).
See plan/sources-recon.md.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from app.db.models import CompetitionStage, RawAnnouncement, SourceType
from app.scrapers.base import get_html, make_client
from app.scrapers.dates import parse_int

FEED_URL = "https://www.dreamjob.ma/feed/"

_POSTS_RE = re.compile(r"(\d+)\s+postes?", re.IGNORECASE)
_ADMIN_RE = re.compile(
    r"^(?:Concours(?: de Recrutement)?|Recrutement)\s+(?P<admin>.+?)\s+(?:20\d\d|\()", re.IGNORECASE
)


def _stage_from_url(url: str) -> CompetitionStage:
    if "/resultats-concours/" in url:
        slug = url.lower()
        return CompetitionStage.CONVOQUES if "convoqu" in slug else CompetitionStage.RESULTATS
    return CompetitionStage.AVIS


def parse_feed_xml(xml_text: str | bytes) -> list[RawAnnouncement]:
    """Parse the RSS feed into public sector announcements (no network I/O)."""
    root = ET.fromstring(xml_text)
    out: list[RawAnnouncement] = []
    for item in root.findall("./channel/item"):
        link = (item.findtext("link") or "").strip()
        if "/emploi-public/" not in link:
            continue
        title = (item.findtext("title") or "").strip()
        html = item.findtext("description") or ""
        soup = BeautifulSoup(html, "lxml")
        img = soup.find("img")
        logo = img.get("src") if img else None
        for p in soup.find_all("p"):
            if p.find("a", rel="nofollow") or p.find("img"):
                p.decompose()  # drop the thumbnail and the "L'article ... est apparu" footer
        body = " ".join(soup.get_text(" ", strip=True).split())
        m = _POSTS_RE.search(title) or _POSTS_RE.search(body)
        admin = _ADMIN_RE.match(title)
        out.append(
            RawAnnouncement(
                source_name="dreamjob.ma",
                source_type=SourceType.AGGREGATOR,
                source_url=link,
                detail_url=link,
                title=title,
                text=f"{title}. {body}".strip(". "),
                lang="fr",
                stage=_stage_from_url(link),
                administration=admin.group("admin").strip() if admin else None,
                post_count=parse_int(m.group(1)) if m else None,
                logo_url=logo,
            )
        )
    return out


class DreamjobScraper:
    source_name = "dreamjob.ma"

    def fetch(self) -> list[RawAnnouncement]:
        with make_client() as client:
            return parse_feed_xml(get_html(client, FEED_URL).encode("utf-8"))

    def enrich(self, ann: RawAnnouncement, client=None) -> RawAnnouncement:
        """Detail pages are behind Cloudflare, so there is nothing more to fetch."""
        return ann
