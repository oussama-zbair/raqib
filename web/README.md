# Admin Dashboard — Nuxt (Vue)

Read-only supervision dashboard for **Raqib (رقيب)**. Shows source health,
canonical competitions, and tracking stats. It never sees CIN (RLS + column selection).

## Stack
Nuxt 3 (Vue 3) + `@supabase/supabase-js`, deployed to Cloudflare Pages.

## Pages
- `/` — overview KPIs (competitions, tracked, source health, early signals, lifecycle)
- `/competitions` — recent canonical competitions
- `/sources` — source health table

## Develop
```bash
npm install
cp .env.example .env   # fill NUXT_PUBLIC_SUPABASE_URL + NUXT_PUBLIC_SUPABASE_ANON_KEY
npm run dev
```

## Deploy (Cloudflare Pages)
- Build command: `npm run build`
- Output: `dist` (via the `cloudflare-pages` nitro preset)
- Env vars: `NUXT_PUBLIC_SUPABASE_URL`, `NUXT_PUBLIC_SUPABASE_ANON_KEY`

Uses only the Supabase anon key. Sensitive tables (`users`, `profiles`) have no anon RLS
policy, so CIN and personal data are never exposed to the browser.
