"""Offline tests of the emploi-public.ma parser, run against saved real pages."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from app.db.models import CompetitionStage
from app.scrapers.emploi_public import parse_detail_html, parse_listing_html

FIX = Path(__file__).parent / "fixtures" / "emploi_public"


def _listing():
    return parse_listing_html((FIX / "listing.html").read_text(encoding="utf-8"))


def test_listing_extracts_cards():
    rows = _listing()
    assert len(rows) >= 9
    first = rows[0]
    assert first.source_name == "emploi-public.ma"
    assert first.stage == CompetitionStage.AVIS
    assert first.source_url == (
        "https://www.emploi-public.ma/fr/concours/details/a1c6e668-6fb2-470a-818c-6d6b8d5f574d"
    )
    assert first.grade == "Administrateur 2ème grade - Echelle 11"
    assert first.administration.startswith("Ministère de l’Agriculture")
    assert first.post_count == 38
    assert first.deadline == date(2026, 12, 15)
    assert first.exam_date == date(2027, 1, 31)
    assert first.logo_url.startswith("https://www.emploi-public.ma/backoffice/files/images/")
    assert len({r.source_url for r in rows}) == len(rows)


def test_listing_engineer_card():
    eng = next(r for r in _listing() if r.grade and r.grade.startswith("Ingénieur d'Etat"))
    assert eng.post_count == 20
    assert eng.deadline == date(2026, 12, 28)


def test_detail_adds_specialty_and_code():
    base = _listing()[0]
    full = parse_detail_html((FIX / "detail.html").read_text(encoding="utf-8"), base)
    assert full.reference_code == "C 44904/26"
    assert "Ingénierie des données" in full.specialty
    assert not full.specialty.startswith("-")
    assert full.deadline == date(2026, 12, 15)
