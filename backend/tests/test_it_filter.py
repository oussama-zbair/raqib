"""IT filter tests: real fixture items plus titles seen on the sites."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.db.models import RawAnnouncement, SourceType
from app.matching.it_filter import is_it_related
from app.scrapers import emploi_public, wadifapublic_ma

FIX = Path(__file__).parent / "fixtures"


def _ann(**kw) -> RawAnnouncement:
    return RawAnnouncement(
        source_name="test", source_type=SourceType.AGGREGATOR, source_url="https://x/1", **kw
    )


def _wadifa() -> dict[str, RawAnnouncement]:
    rows = wadifapublic_ma.parse_listing_html(
        (FIX / "wadifapublic" / "listing.html").read_text(encoding="utf-8")
    )
    return {r.reference_code: r for r in rows}


def test_wadifa_it_items_kept():
    rows = _wadifa()
    assert is_it_related(rows["C 44891/26"])[0]  # state engineer, specialty المعلوميات
    assert is_it_related(rows["C 44904/26"])[0]  # administrator list includes data engineering


def test_wadifa_non_it_items_dropped():
    rows = _wadifa()
    assert not is_it_related(rows["C 44903/26"])[0]  # doctor
    assert not is_it_related(rows["C 44901/26"])[0]  # administrator, law and finance


def test_emploi_public_detail_specialties():
    listing = emploi_public.parse_listing_html(
        (FIX / "emploi_public" / "listing.html").read_text(encoding="utf-8")
    )
    first = listing[0]
    assert not is_it_related(first)[0]  # the listing has no specialty yet
    detail = emploi_public.parse_detail_html(
        (FIX / "emploi_public" / "detail.html").read_text(encoding="utf-8"), first
    )
    ok, reason = is_it_related(detail)
    assert ok and reason.startswith("specialty:")


@pytest.mark.parametrize(
    "title",
    [
        "Ingénieur d'Etat en informatique",
        "Technicien spécialisé en développement digital",
        "Technicien spécialisé en réseaux et systèmes",
        "Administrateur spécialité systèmes d'information",
        "Concours de recrutement 3 Développeurs web",
        "Cybersécurité: ingénieur 1er grade",
        "Data engineer, Big Data",
        "مباراة توظيف مهندس دولة تخصص المعلوميات",
        "تقني متخصص في تطوير الإعلاميات",
        "مهندس الأمن السيبراني",
        "متصرف تخصص نظم المعلومات",
        "Software engineer",
    ],
)
def test_it_titles_kept(title):
    assert is_it_related(_ann(title=title))[0], title


@pytest.mark.parametrize(
    "title",
    [
        "Concours de Recrutement Ministère de la Santé 2027 (370 Postes)",
        "Infirmier polyvalent",
        "Médecin premier grade",
        "Rédacteur judiciaire 3ème grade",
        "Ingénieur d'Etat spécialité génie civil",
        "Technicien spécialisé en réseaux d'eau potable",
        "Surveillant pénitentiaire adjoint",
        "مباراة توظيف طبيب من الدرجة الأولى",
        "تقني تجاري - مهندس فلاحي",
        "متصرف تخصص التواصل والإعلام",
        "Responsable d'exploitation de la gare routière",
    ],
)
def test_non_it_titles_dropped(title):
    assert not is_it_related(_ann(title=title))[0], title


def test_short_tokens_match_whole_words_only():
    assert not is_it_related(_ann(title="Medical assistant, radiologie"))[0]
    assert is_it_related(_ann(title="Chargé de la data"))[0]
