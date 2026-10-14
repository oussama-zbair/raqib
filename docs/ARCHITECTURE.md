# Architecture

## Runtimes

Three cooperating runtimes share a single Supabase Postgres database. Each was chosen
to stay inside an always-free tier while matching the workload.

### 1. Python backend — GitHub Actions (cron)
Stateless, scheduled jobs. Runs the heavy libraries (pdfplumber, BeautifulSoup,
Telethon) that don't belong in an edge runtime.

- **ingest** (frequent, e.g. every 2–4h): scrape → extract → normalize → dedup → upsert
  competitions → match to profiles → queue digest items.
- **monitor** (frequent): for each tracked competition, poll Convoqués/Résultats + the
  relevant ministry, and run PDF roll-call on new lists.
- **digest** (daily): send each candidate the day's matched competitions.

### 2. Telegram bot — Supabase Edge Function (webhook)
Deno/TypeScript. Handles interactive traffic that needs to respond instantly:
`/start` onboarding, profile capture, inline `📌 Suivre` callbacks, `/mes_concours`.
Uses the Supabase service role key (server-side) to read/write profiles and tracking.

### 3. Nuxt web — Cloudflare Pages
Read-only admin/status dashboard. Uses the Supabase anon key with RLS so it can only
read non-sensitive columns (never CIN).

## Data flow

```
Sources ──► ingest (Python)
  emploi-public.ma        │  scrape raw announcements
  ministry portals        │  Gemini fallback for scanned/unstructured
  telegram/aggregators     ▼
                       normalize + canonical_hash
                             │  merge duplicates, flag EARLY_SIGNAL
                             ▼
                       competitions  ◄──────────────┐
                             │ match(profile)         │
                             ▼                        │
                      digest queue ──► Telegram      │
                                                      │
User taps 📌 (bot) ──► tracked_competitions ─────────┘
                             │
                       monitor (Python) polls PDFs
                             │  roll-call CIN
                             ▼
                    urgent convocation alert ──► Telegram
```

## Deduplication & cross-referencing

- Canonical id = `hash(normalized_admin + grade + deadline)`.
- Records with the same canonical id merge into one competition; source references are
  appended so we know every place it appeared.
- A competition first seen on a community/Telegram feed is stored `early_signal = true`.
  When the official portal later publishes it (matching canonical id), the flag clears
  and the official reference code is attached.

## Security

- CIN encrypted at rest with Fernet (`CIN_ENCRYPTION_KEY`).
- Only the Python monitor decrypts a CIN, in memory, at roll-call time.
- Web dashboard uses anon key + RLS; CIN column is never exposed to it.
- Telegram webhook validates a shared secret header.

## Extensibility

New sources implement the `Scraper` protocol (`backend/scrapers/base.py`) and return
`RawAnnouncement`s. The rest of the pipeline (extract → normalize → dedup → match) is
source-agnostic, so adding a ministry site or Telegram channel is contained to one module.
