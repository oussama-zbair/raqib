"""Tests for bilingual normalization and profile matching."""

from __future__ import annotations

from datetime import date

from app.db.models import Competition, Profile
from app.matching.matcher import matches_profile
from app.matching.normalizer import (
    canonical_hash,
    normalize_grade,
    normalize_specialty,
    normalize_text,
)


def _profile(**kw) -> Profile:
    base = dict(
        user_id=1,
        target_grades=["ingenieur_etat_1er_grade"],
        target_specialties=["genie_logiciel", "informatique"],
        include_off_target=False,
    )
    base.update(kw)
    return Profile(**base)


def _comp(**kw) -> Competition:
    base = dict(canonical_hash="x", administration="Ministère")
    base.update(kw)
    return Competition(**base)


# ---- normalization ----
def test_normalize_strips_accents_and_case():
    assert normalize_text("Ingénieur d'État") == "ingenieur d etat"


def test_normalize_arabic_diacritics():
    # Same word with and without harakat should normalize equal.
    assert normalize_text("مُهَنْدِس") == normalize_text("مهندس")


def test_grade_synonyms_fr_and_ar():
    assert normalize_grade("Échelle 11") == "ingenieur_etat_1er_grade"
    assert normalize_grade("مهندس دولة من الدرجة الأولى") == "ingenieur_etat_1er_grade"


def test_specialty_synonyms_fr_and_ar():
    assert normalize_specialty("Génie Logiciel") == "genie_logiciel"
    assert normalize_specialty("هندسة البرمجيات") == "genie_logiciel"
    assert normalize_specialty("إعلاميات") == "informatique"


# ---- canonical hash / dedup ----
def test_canonical_hash_is_language_agnostic():
    h_fr = canonical_hash("Ministère de la Justice", "Ingénieur d'État", "12/10/2026")
    h_ar = canonical_hash("Ministère de la Justice", "مهندس دولة", date(2026, 10, 12))
    assert h_fr == h_ar


# ---- matching ----
def test_match_positive_software_engineer():
    comp = _comp(
        title_fr="Avis de concours Ingénieur d'État Échelle 11 - Génie Logiciel",
        grade="Ingénieur d'État 1er grade",
        specialty="Génie Logiciel",
    )
    assert matches_profile(comp, _profile()).matched


def test_match_rejects_civil_engineering():
    comp = _comp(
        title_fr="Ingénieur d'État Échelle 11 - Génie Civil",
        grade="Ingénieur d'État 1er grade",
        specialty="Génie Civil",
    )
    assert not matches_profile(comp, _profile()).matched


def test_match_rejects_technicien():
    comp = _comp(title_fr="Recrutement Technicien Spécialisé Informatique")
    assert not matches_profile(comp, _profile()).matched


def test_off_target_opt_in_allows_more():
    comp = _comp(
        title_fr="Technicien Informatique",
        specialty="Informatique",
        grade=None,
    )
    # Without grade constraint but specialty matches; opt-in disables negative filter.
    prof = _profile(target_grades=[], include_off_target=True)
    assert matches_profile(comp, prof).matched


def test_match_arabic_announcement():
    comp = _comp(
        title_ar="إعلان مباراة لتوظيف مهندس دولة من الدرجة الأولى في هندسة البرمجيات",
    )
    assert matches_profile(comp, _profile()).matched
