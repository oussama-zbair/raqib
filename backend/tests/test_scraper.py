"""Offline test of the emploi-public.ma listing parser (no network)."""

from __future__ import annotations

from app.db.models import CompetitionStage
from app.scrapers.emploi_public import parse_listing_html

SAMPLE_FR = """
<html><body>
<table>
  <tr><td>
    <a href="/fr/annonce.aspx?id=101">Avis de concours Ingénieur d'État Génie Logiciel - Ministère de la Justice</a>
    <span>Délai: 12/10/2026 — 5 postes</span>
  </td></tr>
  <tr><td>
    <a href="/files/convocation-123.pdf">Liste des candidats convoqués à l'épreuve écrite</a>
  </td></tr>
</table>
<a href="#">Suivant</a>
<a href="javascript:void(0)">Menu</a>
</body></html>
"""


def test_parse_extracts_listing_and_pdf():
    rows = parse_listing_html(SAMPLE_FR, "/fr/annonces.aspx", CompetitionStage.AVIS)
    assert len(rows) == 2  # nav (#) and javascript links are skipped

    listing = rows[0]
    assert "Génie Logiciel" in listing.title
    assert listing.lang == "fr"
    assert listing.source_url.startswith("https://www.emploi-public.ma")
    assert listing.pdf_urls == []

    pdf_row = rows[1]
    assert pdf_row.pdf_urls and pdf_row.pdf_urls[0].endswith(".pdf")


def test_parse_arabic_lang_detection():
    rows = parse_listing_html(SAMPLE_FR, "/ar/annonces.aspx", CompetitionStage.AVIS)
    assert all(r.lang == "ar" for r in rows)
