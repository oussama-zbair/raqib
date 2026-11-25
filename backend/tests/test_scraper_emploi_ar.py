"""emploi-public.ma Arabic pages: the four stages, details, ids (saved real pages)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.db.models import CompetitionStage as S
from app.jobs.dedup import canonical_url
from app.scrapers.emploi_public import (
    concours_uuid,
    parse_ar_detail_html,
    parse_ar_listing_html,
)

FIX = Path(__file__).parent / "fixtures" / "emploi_public"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("proc,stage", [
    ("avis", S.AVIS), ("convocation", S.CONVOQUES),
    ("oral", S.CONVOQUES_ORAL), ("resultat", S.RESULTATS),
])
def test_every_stage_listing_parses(proc, stage):
    items = parse_ar_listing_html(_read(f"ar_listing_{proc}.html"), stage)
    assert len(items) >= 10
    for it in items:
        assert it.stage == stage and it.lang == "ar"
        assert it.administration and it.grade
        assert concours_uuid(it.source_url)
        assert "توظيف" not in it.grade  # title prefix removed
        if stage == S.AVIS:
            assert it.list_pdf_url is None
        else:
            assert it.list_pdf_url.endswith(concours_uuid(it.source_url))


def test_announcement_card_fields():
    first = parse_ar_listing_html(_read("ar_listing_avis.html"), S.AVIS)[0]
    assert first.administration.startswith("وزارة الفلاحة")
    assert first.grade == "متصرف من الدرجة الثانية - سلم 11"
    assert first.post_count == 38
    assert first.deadline == date(2026, 12, 15)
    assert first.exam_date == date(2027, 1, 31)
    assert first.logo_url.startswith("https://www.emploi-public.ma/backoffice/files/images/")


def test_default_logo_is_dropped_and_city_found():
    conv = parse_ar_listing_html(_read("ar_listing_convocation.html"), S.CONVOQUES)[0]
    assert conv.logo_url is None  # the portal's placeholder image: our emblem is used instead
    assert conv.city == "طاطا"
    assert "list_convoques/" in conv.list_pdf_url


def test_oral_and_result_cards_never_carry_the_written_exam_date():
    for proc, stage in (("oral", S.CONVOQUES_ORAL), ("resultat", S.RESULTATS)):
        for it in parse_ar_listing_html(_read(f"ar_listing_{proc}.html"), stage):
            assert it.exam_date is None
    oral = parse_ar_listing_html(_read("ar_listing_oral.html"), S.CONVOQUES_ORAL)[0]
    assert "list_convoques_oral/" in oral.list_pdf_url


def test_detail_adds_code_specialties_and_full_grade():
    ann = parse_ar_listing_html(_read("ar_listing_avis.html"), S.AVIS)[0]
    full = parse_ar_detail_html(_read("ar_detail_avis.html"), ann)
    assert full.reference_code == "C 44904/26"
    assert full.grade == "متصرف من الدرجة الثانية - سُلمْ 11"
    specs = full.specialty.split(" / ")
    assert "الموارد البشرية" in specs and "التواصل" in specs
    assert all(not s.startswith("-") for s in specs)


def test_french_and_arabic_pages_of_one_concours_share_an_id():
    uuid = "a1c6e668-6fb2-470a-818c-6d6b8d5f574d"
    fr = f"https://www.emploi-public.ma/fr/concours/details/{uuid}"
    ar = f"https://www.emploi-public.ma/ar/تفاصيل/المباريات/{uuid}"
    ar_encoded = ("https://www.emploi-public.ma/ar/%D8%AA%D9%81%D8%A7%D8%B5%D9%8A%D9%84/"
                  f"%D8%A7%D9%84%D9%85%D8%A8%D8%A7%D8%B1%D9%8A%D8%A7%D8%AA/{uuid}")
    assert canonical_url(fr) == canonical_url(ar) == canonical_url(ar_encoded) == f"ep:{uuid}"
    assert canonical_url("https://other.site/x") == "https://other.site/x"
