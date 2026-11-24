"""Offline tests of the wadifapublic.ma parser, run against saved real pages."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from app.db.models import CompetitionStage, RawAnnouncement, SourceType
from app.scrapers.wadifapublic_ma import parse_detail_html, parse_listing_html

FIX = Path(__file__).parent / "fixtures" / "wadifapublic"


def _listing():
    return parse_listing_html((FIX / "listing.html").read_text(encoding="utf-8"))


def test_listing_extracts_main_cards_only():
    rows = _listing()
    assert len(rows) == 6  # the 3 sidebar article cards have no employer label
    assert all(r.stage == CompetitionStage.AVIS for r in rows)
    assert len({r.source_url for r in rows}) == 6


def test_listing_card_fields():
    eng = next(r for r in _listing() if "مهندس دولة" in (r.grade or ""))
    assert eng.administration == "وزارة الصحة والحماية الاجتماعية"
    assert eng.post_count == 20
    assert eng.grade == "مهندس دولة من الدرجة الأولى - سُلمْ 11"
    assert eng.specialty == "هندسة بيوطبية / المعلوميات"
    assert eng.deadline == date(2026, 12, 28)
    assert eng.reference_code == "C 44891/26"
    assert eng.logo_url == (
        "https://www.wadifapublic.ma/logos/06823af8-1574-4772-96e7-428280bc8d2f.png"
    )
    assert eng.lang == "ar"


def test_detail_adds_official_link_and_keeps_listing_fields():
    base = RawAnnouncement(
        source_name="wadifapublic.ma",
        source_type=SourceType.AGGREGATOR,
        source_url="https://www.wadifapublic.ma/ar/x/c44713-26/y",
        administration="الوكالة الوطنية للدعم الاجتماعي",
    )
    full = parse_detail_html((FIX / "detail.html").read_text(encoding="utf-8"), base)
    assert full.official_url == (
        "https://www.emploi-public.ma/fr/concours/details/2fef0122-6371-4de3-af5f-54385044d832"
    )
    assert full.exam_date is None  # the page says "غير محدد" (not set yet)
    assert full.post_count == 1
    assert full.specialty == "السمعي البصري واللوجستيك"
    assert full.deadline == date(2026, 11, 26)
    assert full.logo_url.endswith("/logos/2d735195-3de4-497e-a402-8878bf668945.png")
