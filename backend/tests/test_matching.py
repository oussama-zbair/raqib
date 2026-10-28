"""Tests for bilingual normalization and profile matching (family + level model)."""

from __future__ import annotations

from datetime import date

from app.db.models import Competition, Profile
from app.matching.matcher import matches_profile
from app.matching.normalizer import (
    canonical_hash,
    classify_family,
    classify_level,
    normalize_text,
)


def _profile(**kw) -> Profile:
    # target_grades = LEVELS, target_specialties = FAMILIES (DB columns reused).
    base = dict(
        user_id=1,
        target_grades=["master_ingenieur"],
        target_specialties=["informatique"],
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
    assert normalize_text("مُهَنْدِس") == normalize_text("مهندس")


# ---- family classification (field/domain) ----
def test_family_informatique_fr_and_ar():
    assert classify_family("Génie Logiciel") == "informatique"
    assert classify_family("هندسة البرمجيات") == "informatique"
    assert classify_family("إعلاميات") == "informatique"
    assert classify_family("Systèmes & Réseaux") == "informatique"


def test_family_other_domains():
    assert classify_family("Médecine générale") == "sante"
    assert classify_family("Droit administratif") == "droit"
    assert classify_family("Comptabilité et audit") == "finance_economie"
    assert classify_family("هندسة مدنية") == "genie_technique"
    assert classify_family("التعليم الابتدائي") == "education"


# ---- level classification (diploma/grade) ----
def test_level_fr_and_ar():
    assert classify_level("Échelle 11") == "master_ingenieur"
    assert classify_level("مهندس دولة من الدرجة الأولى") == "master_ingenieur"
    assert classify_level("Technicien spécialisé") == "technicien"
    assert classify_level("Licence professionnelle") == "licence"
    assert classify_level("الباكالوريا") == "bac"


# ---- canonical hash / dedup ----
def test_canonical_hash_is_language_agnostic():
    # Same admin + same level (master_ingenieur) + same deadline => same hash.
    h_fr = canonical_hash("Ministère de la Justice", "Ingénieur d'État", "12/10/2026")
    h_ar = canonical_hash("Ministère de la Justice", "مهندس دولة", date(2026, 10, 12))
    assert h_fr == h_ar


# ---- matching ----
def test_match_positive_it_engineer():
    comp = _comp(
        title_fr="Avis de concours Ingénieur d'État Échelle 11 - Génie Logiciel",
        grade="Ingénieur d'État 1er grade",
        specialty="Génie Logiciel",
    )
    assert matches_profile(comp, _profile()).matched


def test_match_rejects_wrong_family():
    # Civil engineering is genie_technique, profile wants informatique.
    comp = _comp(
        title_fr="Ingénieur d'État Échelle 11 - Génie Civil",
        grade="Ingénieur d'État 1er grade",
        specialty="Génie Civil",
    )
    assert not matches_profile(comp, _profile()).matched


def test_match_rejects_wrong_level():
    # Right family (informatique) but wrong level (technicien vs master_ingenieur).
    comp = _comp(
        title_fr="Technicien spécialisé en Informatique",
        grade="Technicien spécialisé",
        specialty="Informatique",
    )
    assert not matches_profile(comp, _profile()).matched


def test_match_other_family_profile():
    # A santé candidate matches a medical concours.
    comp = _comp(
        title_fr="Concours de recrutement Infirmier - Licence",
        grade="Licence",
        specialty="Infirmier",
    )
    prof = _profile(target_specialties=["sante"], target_grades=["licence"])
    assert matches_profile(comp, prof).matched


def test_match_arabic_announcement():
    comp = _comp(
        title_ar="إعلان مباراة لتوظيف مهندس دولة من الدرجة الأولى في هندسة البرمجيات",
    )
    assert matches_profile(comp, _profile()).matched


def test_negative_support_role_rejected():
    comp = _comp(title_fr="Recrutement Agent de service", specialty="Informatique")
    assert not matches_profile(comp, _profile()).matched


def test_no_constraints_matches_all():
    comp = _comp(title_fr="Concours Administrateur 2ème grade")
    prof = _profile(target_grades=[], target_specialties=[])
    assert matches_profile(comp, prof).matched
