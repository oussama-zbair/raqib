// Supabase data access for the bot (service role, server-side).

import { createClient, SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const url = Deno.env.get("SUPABASE_URL")!;
const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

export const supabase: SupabaseClient = createClient(url, serviceKey, {
  auth: { persistSession: false },
});

export interface UserRow {
  id: number;
  telegram_user_id: number;
  locale: string;
  is_owner: boolean;
}

export interface ProfileRow {
  id: number;
  user_id: number;
  full_name_fr: string | null;
  full_name_ar: string | null;
  cin_last4: string | null;
  target_grades: string[];
  target_specialties: string[];
  include_off_target: boolean;
  paused: boolean;
  quiet_start: number | null;
  quiet_end: number | null;
  onboarding_state: string;
}

/** Get or create a user row keyed by Telegram user id. */
export async function upsertUser(
  telegramUserId: number,
  username: string | null,
): Promise<UserRow> {
  const { data: existing } = await supabase
    .from("users")
    .select("id,telegram_user_id,locale,is_owner")
    .eq("telegram_user_id", telegramUserId)
    .maybeSingle();
  if (existing) return existing as UserRow;

  // First user matching OWNER_TELEGRAM_ID is flagged as owner automatically.
  const ownerId = Deno.env.get("OWNER_TELEGRAM_ID");
  const isOwner = ownerId != null && String(telegramUserId) === ownerId;

  const { data, error } = await supabase
    .from("users")
    .insert({ telegram_user_id: telegramUserId, telegram_username: username, is_owner: isOwner })
    .select("id,telegram_user_id,locale,is_owner")
    .single();
  if (error) throw error;
  return data as UserRow;
}

export async function setUserLocale(userId: number, locale: "fr" | "ar"): Promise<void> {
  await supabase.from("users").update({ locale }).eq("id", userId);
}

export async function getProfile(userId: number): Promise<ProfileRow | null> {
  const { data } = await supabase
    .from("profiles")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();
  return (data as ProfileRow) ?? null;
}

export async function ensureProfile(userId: number): Promise<ProfileRow> {
  const existing = await getProfile(userId);
  if (existing) return existing;
  const { data, error } = await supabase
    .from("profiles")
    .insert({ user_id: userId, onboarding_state: "NEW" })
    .select("*")
    .single();
  if (error) throw error;
  return data as ProfileRow;
}

export async function updateProfile(
  userId: number,
  patch: Record<string, unknown>,
): Promise<void> {
  const { error } = await supabase.from("profiles").update(patch).eq("user_id", userId);
  if (error) throw error;
}

/** Hard-delete a user and (via cascade) their profile + tracking. */
export async function deleteUser(userId: number): Promise<void> {
  await supabase.from("users").delete().eq("id", userId);
}

/** One-click tracking: create a tracked_competitions row (idempotent). */
export async function trackCompetition(
  userId: number,
  competitionId: number,
): Promise<void> {
  await supabase
    .from("tracked_competitions")
    .upsert(
      { user_id: userId, competition_id: competitionId, state: "EN_ATTENTE_CONVOCATION" },
      { onConflict: "user_id,competition_id" },
    );
}

export interface TrackedRow {
  state: string;
  competitions: {
    administration: string;
    title_fr: string | null;
    title_ar: string | null;
    stage: string;
    deadline: string | null;
  } | null;
}

export async function listTracked(userId: number): Promise<TrackedRow[]> {
  const { data } = await supabase
    .from("tracked_competitions")
    .select("state,competitions(administration,title_fr,title_ar,stage,deadline)")
    .eq("user_id", userId);
  return (data as TrackedRow[]) ?? [];
}

// ---- admin helpers ----

export interface AdminStats {
  users: number;
  profiles: number;
  competitions: number;
  tracked: number;
  sources: number;
}

async function count(table: string, filter?: (q: any) => any): Promise<number> {
  let q = supabase.from(table).select("*", { count: "exact", head: true });
  if (filter) q = filter(q);
  const { count: c } = await q;
  return c ?? 0;
}

export async function adminStats(): Promise<AdminStats> {
  const [users, profiles, competitions, tracked, sources] = await Promise.all([
    count("users"),
    count("profiles", (q) => q.eq("onboarding_state", "COMPLETE")),
    count("competitions"),
    count("tracked_competitions"),
    count("announcement_sources", (q) => q.like("last_status", "OK%")),
  ]);
  return { users, profiles, competitions, tracked, sources };
}

/** All Telegram chat ids (for broadcast). */
export async function allTelegramIds(): Promise<number[]> {
  const { data } = await supabase.from("users").select("telegram_user_id");
  return (data ?? []).map((r: any) => r.telegram_user_id as number);
}
