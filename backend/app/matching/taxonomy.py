"""Bilingual (FR/AR) taxonomy for Moroccan public-sector competitions.

Raqib covers ALL concours, not just engineering. Matching is modeled on two axes:

- FAMILY  : the field / domain  (Informatique, Santé, Administration, Droit, ...)
- LEVEL   : the diploma / grade (Bac, Technicien, Licence, Master/Ingénieur, Doctorat)

Each canonical key maps to surface synonyms in French and Arabic. Matching runs on
normalized text (see normalizer.py), so accents / case / spacing / Arabic diacritics
don't matter. Adding a synonym or a whole new family is a one-line, data-only edit.
"""

from __future__ import annotations

# ============================================================
# FAMILIES (field / domain)
# ============================================================
FAMILY_SYNONYMS: dict[str, list[str]] = {
    "informatique": [
        # FR
        "informatique", "informatique generale", "genie informatique",
        "genie logiciel", "ingenierie logicielle", "developpement logiciel",
        "developpement informatique", "systemes d'information", "systeme d'information",
        "systemes et reseaux", "systemes reseaux", "reseaux et telecommunications",
        "reseaux informatiques", "reseaux",
        "technologies de l'information", "technologie de l'information", "data", "donnees",
        "cybersecurite", "securite informatique", "intelligence artificielle",
        # AR
        "اعلاميات", "المعلوميات", "معلوميات", "هندسة البرمجيات", "هندسة المعلوميات",
        "تطوير المعلوميات", "نظم المعلومات", "انظمة المعلومات", "الشبكات",
        "الشبكات والاتصالات", "تكنولوجيا المعلومات", "الامن المعلوماتي", "الذكاء الاصطناعي",
    ],
    "genie_technique": [
        # FR (engineering/technical fields outside IT)
        "genie civil", "genie mecanique", "genie industriel", "genie electrique",
        "genie des procedes", "genie energetique", "genie rural", "topographie",
        "mecanique", "electrotechnique", "electronique", "automatisme", "maintenance",
        "batiment", "travaux publics", "architecture", "urbanisme",
        # AR
        "هندسة مدنية", "هندسة ميكانيكية", "هندسة صناعية", "هندسة كهربائية",
        "هندسة الطرق", "الهندسة المعمارية", "التعمير", "الطبوغرافيا", "الميكانيك",
        "الكهرباء", "الالكترونيك", "الصيانة", "البناء", "الاشغال العمومية",
    ],
    "administration_gestion": [
        # FR
        "administration", "administrateur", "gestion", "management", "ressources humaines",
        "secretariat", "assistant administratif", "redacteur", "gestion administrative",
        "gestion des entreprises", "commerce", "marketing", "logistique",
        # AR
        "ادارة", "تدبير", "متصرف", "التدبير الاداري", "الموارد البشرية", "التسيير",
        "كتابة", "مساعد اداري", "التجارة", "التسويق", "اللوجستيك", "تدبير المقاولات",
    ],
    "finance_economie": [
        # FR
        "finance", "finances", "economie", "comptabilite", "audit", "fiscalite",
        "gestion financiere", "controle de gestion", "banque", "assurance",
        "sciences economiques", "statistique", "econometrie",
        # AR
        "مالية", "المالية", "اقتصاد", "الاقتصاد", "محاسبة", "المحاسبة", "التدقيق",
        "الجباية", "التدبير المالي", "مراقبة التسيير", "البنك", "التامين", "الاحصاء",
    ],
    "droit": [
        # FR
        "droit", "juridique", "sciences juridiques", "droit public", "droit prive",
        "droit administratif", "juriste", "notariat", "huissier",
        # AR
        "قانون", "الحقوق", "العلوم القانونية", "القانون العام", "القانون الخاص",
        "القانون الاداري", "قانوني", "الشؤون القانونية",
    ],
    "sante": [
        # FR
        "sante", "medecine", "medecin", "infirmier", "infirmiere", "pharmacie",
        "pharmacien", "chirurgie dentaire", "sage-femme", "technicien de sante",
        "paramedical", "biologie medicale", "kinesitherapie",
        # AR
        "صحة", "الصحة", "طب", "الطب", "طبيب", "ممرض", "ممرضة", "تمريض", "صيدلة",
        "صيدلي", "طب الاسنان", "قابلة", "تقني الصحة", "شبه طبي", "التحاليل الطبية",
    ],
    "education": [
        # FR
        "education", "enseignement", "enseignant", "professeur", "instituteur",
        "education nationale", "cadre pedagogique", "formateur",
        # AR
        "تعليم", "التعليم", "التربية", "استاذ", "مدرس", "معلم", "التربية الوطنية",
        "اطر التدريس", "مكون", "التعليم الاولي",
    ],
    "enseignement_superieur": [
        # FR
        "enseignement superieur", "professeur universitaire", "professeur assistant",
        "recherche scientifique", "chercheur",
        # AR
        "التعليم العالي", "استاذ التعليم العالي", "استاذ مساعد", "البحث العلمي", "باحث",
    ],
    "securite_defense": [
        # FR
        "securite", "police", "gendarmerie", "forces auxiliaires", "protection civile",
        "douane", "armee", "militaire", "surveillance",
        # AR
        "الامن", "الشرطة", "الدرك", "القوات المساعدة", "الوقاية المدنية", "الجمارك",
        "الجيش", "عسكري", "المراقبة",
    ],
    "agriculture_environnement": [
        # FR
        "agriculture", "agronomie", "agronomique", "eaux et forets", "environnement",
        "peche maritime", "veterinaire", "developpement rural",
        # AR
        "الفلاحة", "الزراعة", "المياه والغابات", "البيئة", "الصيد البحري", "بيطري",
        "التنمية القروية",
    ],
    "lettres_sciences_sociales": [
        # FR
        "lettres", "langues", "traduction", "histoire", "geographie", "sociologie",
        "sciences sociales", "communication", "journalisme", "documentation",
        # AR
        "الاداب", "اللغات", "الترجمة", "التاريخ", "الجغرافيا", "علم الاجتماع",
        "العلوم الاجتماعية", "التواصل", "الصحافة", "التوثيق",
    ],
}

# ============================================================
# LEVELS (diploma / grade / échelle)
# ============================================================
LEVEL_SYNONYMS: dict[str, list[str]] = {
    "bac": [
        "baccalaureat", "niveau bac", "bac", "diplome du baccalaureat",
        "الباكالوريا", "البكالوريا", "مستوى الباكالوريا", "شهادة الباكالوريا",
    ],
    "technicien": [
        "technicien", "technicien specialise", "diplome de technicien",
        "echelle 8", "echelle 9", "bac+2", "dut", "bts", "dts",
        "تقني", "تقني متخصص", "السلم 8", "السلم 9", "باك+2", "دبلوم التقني",
    ],
    "licence": [
        "licence", "licence professionnelle", "bac+3", "echelle 10", "diplome de licence",
        "اجازة", "الاجازة", "اجازة مهنية", "باك+3", "السلم 10",
    ],
    "master_ingenieur": [
        # FR
        "master", "diplome de master", "bac+5", "bac + 5", "cadre bac+5",
        "ingenieur", "ingenieur d'etat", "ingenieur detat", "ingenieur d'etat 1er grade",
        "echelle 11", "echelon 11", "diplome d'ingenieur",
        # AR
        "ماستر", "الماستر", "باك+5", "مهندس", "مهندس دولة",
        "مهندس دولة من الدرجة الاولى", "السلم 11", "دبلوم المهندس",
    ],
    "doctorat": [
        "doctorat", "phd", "docteur", "bac+8",
        "دكتوراه", "الدكتوراه", "دكتور", "باك+8",
    ],
}

# ============================================================
# Negative terms (reject by default unless the user opts in)
# Sub-bac roles and clearly off-target labels. Note: with the broad family model, we no
# longer treat whole engineering families as "negative" (the user picks families); we
# only hard-reject low-level support roles unless opted in.
# ============================================================
NEGATIVE_TERMS: list[str] = [
    "adjoint", "adjoint technique", "agent de service", "agent d'execution",
    "manoeuvre", "ouvrier",
    "عون", "عون الخدمة", "مساعد تقني", "عامل", "يدوي",
]


# ============================================================
# Backward-compatible aliases
# The codebase (normalizer, matcher, tests) referenced GRADE_SYNONYMS / SPECIALTY_SYNONYMS
# and the canonical keys ingenieur_etat_1er_grade / genie_logiciel / informatique / etc.
# We keep those names working by mapping them onto the new family/level tables, so nothing
# downstream breaks while we migrate the profile model to families[] + levels[].
# ============================================================
GRADE_SYNONYMS: dict[str, list[str]] = LEVEL_SYNONYMS
SPECIALTY_SYNONYMS: dict[str, list[str]] = FAMILY_SYNONYMS


# ============================================================
# IT / software engineering filter (channel publisher)
# ============================================================
# Loose on purpose (see plan/README.md, Risks): rejected items are logged so the lists can
# be tuned. Matching runs on normalize_text() output.
# IT_PHRASES match as substrings (long, unambiguous stems).
IT_PHRASES: list[str] = [
    # FR
    "informatique", "informaticien", "genie logiciel", "ingenierie logicielle",
    "developpement logiciel", "developpement digital", "developpement web",
    "developpement mobile", "developpeur", "systeme d'information", "systemes d'information",
    "systemes et reseaux", "reseaux et systemes", "reseaux informatiques",
    "reseaux et telecommunications", "reseaux et telecoms", "administrateur systeme",
    "administration systeme", "telecommunications", "telecoms", "cybersecurite",
    "securite informatique", "securite des systemes", "intelligence artificielle",
    "big data", "data science", "data scientist", "data engineer", "science des donnees",
    "sciences des donnees", "ingenierie des donnees", "analyse de donnees",
    "base de donnees", "bases de donnees", "transformation digitale",
    "transformation numerique", "technologies de l'information", "technologie de l'information",
    "multimedia et web", "devops", "cloud computing",
    # EN
    "software", "computer science", "information technology", "web developer",
    "network engineer", "cybersecurity",
    # AR (normalize_text folds alef variants and strips diacritics)
    "معلوميات", "اعلاميات", "المعلوميات", "الاعلاميات", "مبرمج", "برمجة", "البرمجيات",
    "هندسة البرمجيات", "تطوير المعلوميات", "نظم المعلومات", "انظمة المعلومات",
    "نظام المعلومات", "تكنولوجيا المعلومات", "تقنيات المعلومات", "امن المعلومات",
    "الامن السيبراني", "الامن المعلوماتي", "الذكاء الاصطناعي", "علوم البيانات",
    "هندسة البيانات", "البيانات الضخمة", "تحليل البيانات", "قواعد البيانات",
    "قواعد المعطيات", "الشبكات والاتصالات", "الشبكات المعلوماتية", "الشبكات والنظم",
    "الاتصالات السلكية", "التحول الرقمي", "الرقمنة", "التنمية الرقمية", "تطوير رقمي",
    "التطوير الرقمي",
]
# IT_WORDS must match as whole words (short tokens that would otherwise hit unrelated text).
IT_WORDS: list[str] = [
    "data", "ia", "ai", "web", "reseaux", "network", "networks", "cloud", "digital",
    "numerique", "devs", "dev", "programmeur", "analyste programmeur",
    "الشبكات", "رقمي",
]
# Whole-word tokens that look IT but are not (checked on the matched word's context).
IT_EXCLUDE_PHRASES: list[str] = [
    "reseaux d'eau", "reseau d'eau", "reseaux d'assainissement", "reseaux routiers",
    "reseaux electriques", "reseau electrique", "reseaux d'electricite",
    "شبكات الماء", "شبكات الطرق", "شبكات التطهير",
]


def all_family_keys() -> list[str]:
    return list(FAMILY_SYNONYMS.keys())


def all_level_keys() -> list[str]:
    return list(LEVEL_SYNONYMS.keys())


# legacy helpers kept so older imports don't break
def all_grade_keys() -> list[str]:
    return all_level_keys()


def all_specialty_keys() -> list[str]:
    return all_family_keys()
