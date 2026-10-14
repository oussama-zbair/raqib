import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

/** True when both the Supabase URL and anon key are present. */
export function isSupabaseConfigured(): boolean {
  const config = useRuntimeConfig();
  return Boolean(config.public.supabaseUrl && config.public.supabaseAnonKey);
}

/**
 * Read-only Supabase client for the admin dashboard.
 * Uses the ANON key; RLS restricts it to non-sensitive columns (never CIN).
 *
 * Returns `null` when credentials are missing so pages can render a friendly
 * "not configured" state instead of crashing with a 500.
 */
export function useSupabase(): SupabaseClient | null {
  if (!isSupabaseConfigured()) return null;
  const config = useRuntimeConfig();
  if (!client) {
    client = createClient(
      config.public.supabaseUrl as string,
      config.public.supabaseAnonKey as string,
      { auth: { persistSession: false } },
    );
  }
  return client;
}
