// Family (field) and Level (diploma/grade) options offered during onboarding.
// Keys MUST match the Python taxonomy (backend/app/matching/taxonomy.py) so the bot
// writes the same canonical keys the matcher expects.
//
// Stored on the profile: families -> target_specialties column, levels -> target_grades
// column (DB columns reused; semantically families + levels now).

export interface Option {
  key: string;
  labelFr: string;
  labelAr: string;
}

export const FAMILY_OPTIONS: Option[] = [
  { key: "informatique", labelFr: "Informatique / Réseaux", labelAr: "المعلوميات / الشبكات" },
  { key: "genie_technique", labelFr: "Génie & Technique", labelAr: "الهندسة والتقنية" },
  { key: "administration_gestion", labelFr: "Administration & Gestion", labelAr: "الإدارة والتدبير" },
  { key: "finance_economie", labelFr: "Finance & Économie", labelAr: "المالية والاقتصاد" },
  { key: "droit", labelFr: "Droit", labelAr: "القانون" },
  { key: "sante", labelFr: "Santé", labelAr: "الصحة" },
  { key: "education", labelFr: "Éducation / Enseignement", labelAr: "التربية والتعليم" },
  { key: "enseignement_superieur", labelFr: "Enseignement supérieur", labelAr: "التعليم العالي" },
  { key: "securite_defense", labelFr: "Sécurité & Défense", labelAr: "الأمن والدفاع" },
  { key: "agriculture_environnement", labelFr: "Agriculture & Environnement", labelAr: "الفلاحة والبيئة" },
  { key: "lettres_sciences_sociales", labelFr: "Lettres & Sciences sociales", labelAr: "الآداب والعلوم الاجتماعية" },
];

export const LEVEL_OPTIONS: Option[] = [
  { key: "bac", labelFr: "Baccalauréat", labelAr: "الباكالوريا" },
  { key: "technicien", labelFr: "Technicien (Bac+2, échelle 8/9)", labelAr: "تقني (باك+2، السلم 8/9)" },
  { key: "licence", labelFr: "Licence (Bac+3, échelle 10)", labelAr: "إجازة (باك+3، السلم 10)" },
  { key: "master_ingenieur", labelFr: "Master / Ingénieur (Bac+5, échelle 11)", labelAr: "ماستر / مهندس (باك+5، السلم 11)" },
  { key: "doctorat", labelFr: "Doctorat (Bac+8)", labelAr: "دكتوراه (باك+8)" },
];

function label(options: Option[], key: string, locale: "fr" | "ar"): string {
  const o = options.find((x) => x.key === key);
  if (!o) return key;
  return locale === "ar" ? o.labelAr : o.labelFr;
}

export function labelForFamily(key: string, locale: "fr" | "ar" = "fr"): string {
  return label(FAMILY_OPTIONS, key, locale);
}

export function labelForLevel(key: string, locale: "fr" | "ar" = "fr"): string {
  return label(LEVEL_OPTIONS, key, locale);
}

// ---- Backward-compatible aliases (old names used in keyboards/index) ----
export const GRADE_OPTIONS = LEVEL_OPTIONS;
export const SPECIALTY_OPTIONS = FAMILY_OPTIONS;
export const labelForGrade = labelForLevel;
export const labelForSpecialty = labelForFamily;
