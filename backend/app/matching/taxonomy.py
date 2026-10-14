"""Bilingual (FR/AR) taxonomy for grades and specialties.

Each canonical key maps to a set of surface synonyms in French and Arabic. Matching is
done on normalized text (see normalizer.py) so accents/case/spacing don't matter.

The taxonomy is intentionally data-driven: adding a synonym or a whole new specialty is
a one-line edit, not a code change.
"""

from __future__ import annotations

# ---- Canonical grade keys -> surface forms (FR + AR) ----
GRADE_SYNONYMS: dict[str, list[str]] = {
    "ingenieur_etat_1er_grade": [
        # FR
        "ingenieur d'etat 1er grade",
        "ingenieur d'etat premier grade",
        "ingenieur d'etat",
        "ingenieur detat",
        "echelle 11",
        "echelon 11",
        # AR
        "مهندس دولة من الدرجة الأولى",
        "مهندس دولة",
        "السلم 11",
        "الدرجة الأولى مهندس",
    ],
    "administrateur_2eme_grade": [
        "administrateur 2eme grade",
        "administrateur deuxieme grade",
        "administrateur",
        "متصرف من الدرجة الثانية",
        "متصرف",
    ],
    "cadre_bac_plus_5": [
        "cadre bac+5",
        "bac+5",
        "bac + 5",
        "niveau bac+5",
        "master",
        "diplome de master",
        "بكالوريا+5",
        "ماستر",
        "إجازة زائد خمسة",
    ],
}

# ---- Canonical specialty keys -> surface forms (FR + AR) ----
SPECIALTY_SYNONYMS: dict[str, list[str]] = {
    "genie_logiciel": [
        "genie logiciel",
        "ingenierie logicielle",
        "developpement logiciel",
        "هندسة البرمجيات",
        "هندسة برمجيات",
    ],
    "informatique": [
        "informatique",
        "informatique generale",
        "developpement informatique",
        "technologies de l'information",
        "technologie de l'information",
        "genie informatique",
        "إعلاميات",
        "المعلوميات",
        "تطوير المعلوميات",
        "تكنولوجيا المعلومات",
    ],
    "systemes_information": [
        "systemes d'information",
        "systeme d'information",
        "نظم المعلومات",
        "أنظمة المعلومات",
    ],
    "systemes_reseaux": [
        "systemes et reseaux",
        "systemes & reseaux",
        "reseaux et telecommunications",
        "الأنظمة والشبكات",
        "الشبكات",
    ],
}

# ---- Negative terms: reject by default unless the user opts in ----
# Off-target fields and sub-bac+5 roles.
NEGATIVE_TERMS: list[str] = [
    # off-target engineering fields
    "genie civil",
    "genie mecanique",
    "genie industriel",
    "genie agronomique",
    "agronomie",
    "genie electrique",
    "هندسة مدنية",
    "هندسة ميكانيكية",
    "هندسة زراعية",
    # sub-bac+5 roles
    "technicien",
    "technicien specialise",
    "adjoint",
    "adjoint technique",
    "agent",
    "tقني",
    "تقني",
    "مساعد",
    "عون",
]


def all_grade_keys() -> list[str]:
    return list(GRADE_SYNONYMS.keys())


def all_specialty_keys() -> list[str]:
    return list(SPECIALTY_SYNONYMS.keys())
