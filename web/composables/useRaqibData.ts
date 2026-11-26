// Live data written by the publish job (state/public.json), fetched in the browser.
// No database and no server: the file is refreshed in the repo every 30 minutes.

export type Stage = "AVIS" | "CONVOQUES" | "CONVOQUES_ORAL" | "RESULTATS";
export const STAGES: Stage[] = ["AVIS", "CONVOQUES", "CONVOQUES_ORAL", "RESULTATS"];

export interface Concours {
  id: string;
  code: string | null;
  administration: string | null;
  grade: string | null;
  title: string | null;
  family: string | null;
  scale: number | null;
  specialty: string | null;
  posts: number | null;
  deadline: string | null;
  exam_date: string | null;
  city: string | null;
  logo: string | null;
  url: string | null;
  tags: string[];
  stages: Stage[];
  posted_at: string | null;
}

export interface StageUpdate {
  id: string;
  stage: Stage;
  administration: string | null;
  grade: string | null;
  title: string | null;
  family: string | null;
  exam_date: string | null;
  city: string | null;
  logo: string | null;
  pdf: string | null;
  url: string | null;
  posted_at: string | null;
}

export interface PublicData {
  updated_at: string | null;
  channel: string;
  sources: { name: string; url: string; status: string }[];
  stats: { open: number; posted_total: number; stage_posts_total: number; followed: number };
  concours: Concours[];
  updates: StageUpdate[];
}

export function useRaqibData() {
  const config = useRuntimeConfig();
  return useLazyFetch<PublicData>(config.public.dataUrl as string, {
    key: "raqib-public",
    server: false, // always the latest file, never a copy frozen at build time
    // raw.githubusercontent.com answers text/plain: parse it ourselves.
    parseResponse: (text: string) => JSON.parse(text),
  });
}

/** Days until a YYYY-MM-DD date (negative when past). */
export function daysUntil(iso: string | null): number | null {
  if (!iso) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((new Date(iso + "T00:00:00").getTime() - today.getTime()) / 86_400_000);
}

/** Locale-aware date and relative time helpers. */
export function useFormat() {
  const { locale } = useI18n();
  const tag = computed(() => (locale.value === "ar" ? "ar-MA" : "fr-FR"));
  function date(iso: string | null): string {
    if (!iso) return "";
    return new Intl.DateTimeFormat(tag.value, {
      weekday: "long", day: "numeric", month: "long", year: "numeric",
    }).format(new Date(iso.length === 10 ? iso + "T00:00:00" : iso));
  }
  function ago(iso: string | null): string {
    if (!iso) return "";
    const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60_000);
    const rtf = new Intl.RelativeTimeFormat(tag.value, { numeric: "auto" });
    if (Math.abs(minutes) < 60) return rtf.format(-minutes, "minute");
    const hours = Math.round(minutes / 60);
    if (Math.abs(hours) < 48) return rtf.format(-hours, "hour");
    return rtf.format(-Math.round(hours / 24), "day");
  }
  return { date, ago };
}
