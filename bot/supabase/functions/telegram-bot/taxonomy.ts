// Grade & specialty options offered during onboarding.
// Keys MUST match the canonical keys in the Python taxonomy (backend/app/matching/taxonomy.py)
// so the bot writes the same values the matcher expects.

export interface Option {
  key: string;
  labelFr: string;
}

export const GRADE_OPTIONS: Option[] = [
  { key: "ingenieur_etat_1er_grade", labelFr: "Ingénieur d'État 1er grade / Échelle 11" },
  { key: "administrateur_2eme_grade", labelFr: "Administrateur 2ème grade" },
  { key: "cadre_bac_plus_5", labelFr: "Cadre Bac+5 / Master" },
];

export const SPECIALTY_OPTIONS: Option[] = [
  { key: "genie_logiciel", labelFr: "Génie Logiciel" },
  { key: "informatique", labelFr: "Informatique générale" },
  { key: "systemes_information", labelFr: "Systèmes d'Information" },
  { key: "systemes_reseaux", labelFr: "Systèmes & Réseaux" },
];

export function labelForGrade(key: string): string {
  return GRADE_OPTIONS.find((o) => o.key === key)?.labelFr ?? key;
}

export function labelForSpecialty(key: string): string {
  return SPECIALTY_OPTIONS.find((o) => o.key === key)?.labelFr ?? key;
}
