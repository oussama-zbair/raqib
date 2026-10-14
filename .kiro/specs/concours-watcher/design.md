# Design — Raqib (رقيب)

## Architecture overview

Three cooperating runtimes, all on always-free tiers, sharing one Supabase Postgres DB.

```
                         ┌─────────────────────────────┐
                         │      Supabase Postgres       │
                         │  users / profiles /          │
                         │  competitions /              │
                         │  tracked_competitions /      │
                         │  announcement_sources        │
                         └──────────────┬──────────────┘
                                        │  (shared state)
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
┌───────▼────────┐            ┌─────────▼──────────┐          ┌─────────▼─────────┐
│ GitHub Actions │            │  Supabase Edge Fn  │          │  Nuxt web (CF Pages)│
│ (Python, cron) │            │  (Deno/TS)         │          │  admin/status only  │
│                │            │  Telegram webhook  │          │  read-only          │
│ ingest job     │            │  /start onboarding │          └────────────────────┘
│ monitor job    │            │  inline buttons    │
│ digest job     │            │  /mes_concours     │
└───────┬────────┘            └─────────┬──────────┘
        │                               │
        │ sends alerts/digest           │ sends replies
        └──────────────┬────────────────┘
                       ▼
                 Telegram Bot API  ───►  Candidate
```

### Why this split
- Cron jobs (scrape, PDF roll-call, digest) are stateless and periodic → GitHub Actions.
- Interactive button taps need sub-second responses → Supabase Edge Function webhook
  (no 24/7 server, native DB access, stays inside Supabase).
- Admin dashboard is read-only status → Nuxt static/SSR on Cloudflare Pages
  (unmetered bandwidth on free tier).
- Heavy libraries (pdfplumber, Telethon, BeautifulSoup) are Python → live in the Actions
  backend, not the Edge Function.

## Modules & interfaces

### Python backend (`backend/`)
- `config.py` — `Settings` loaded from env (Supabase URL/key, Telegram token,
  Gemini key, CIN encryption key).
- `db/client.py` — thin Supabase REST client wrapper (`select/insert/upsert/update`).
- `db/models.py` — pydantic models mirroring the DB tables.
- `security/crypto.py` — `encrypt_cin` / `decrypt_cin` (Fernet symmetric).
- `matching/normalizer.py` — `normalize_admin`, `normalize_grade`,
  `normalize_deadline`, `canonical_hash`.
- `matching/taxonomy.py` — FR/AR grade & specialty synonym tables + negative terms.
- `matching/matcher.py` — `matches_profile(competition, profile) -> MatchResult`.
- `scrapers/base.py` — `Scraper` protocol: `fetch() -> list[RawAnnouncement]`.
- `scrapers/emploi_public.py` — first concrete scraper (Avis/Convoqués/Résultats, FR+AR).
- `extractors/gemini.py` — `extract_structured(text|image) -> CompetitionFields` fallback.
- `pdf/rollcall.py` — `inspect_pdf(pdf_url, candidates) -> list[RollCallHit|Miss]`.
- `notify/telegram.py` — `send_message`, `send_digest`, `send_urgent_convocation`.
- `jobs/ingest.py` — scrape → extract → normalize → dedup → upsert → match → queue digest.
- `jobs/monitor.py` — for each tracked competition, poll + PDF roll-call + alert.
- `jobs/digest.py` — build & send per-candidate daily digest of new matches.

### Telegram bot Edge Function (`bot/`)
- Deno/TypeScript webhook. Handles `/start`, profile capture (a small state machine
  persisted in `profiles`), inline `📌 Suivre` callbacks (writes `tracked_competitions`),
  and `/mes_concours` (reads tracking pipeline).

### Nuxt web (`web/`)
- Read-only admin dashboard: source health, latest competitions, match stats,
  tracking counts. Talks to Supabase via the anon key with RLS restricting to
  non-sensitive columns (never exposes CIN).

## Data / domain model (glossary + tables)

**Shared vocabulary**
- **Concours** — a public-sector recruitment competition.
- **Administration** — the ministry/agency running the concours.
- **Grade / Cadre / Échelle** — the pay grade & rank (e.g. Ingénieur d'État 1er grade,
  Échelle 11, Bac+5).
- **Filière / Specialty** — field (e.g. Génie Logiciel, Systèmes & Réseaux).
- **CIN** — Carte d'Identité Nationale number; the roll-call key.
- **Avis de concours** — the announcement of a competition.
- **Convocation / Convoqués** — the list of candidates called to sit the exam.
- **Résultats** — results list.
- **EARLY_SIGNAL** — a competition seen on community feeds before the official portal.
- **Canonical id** — `hash(normalized_admin + grade + deadline)` used for dedup.
- **Roll-call** — scanning a convocation/result PDF for a candidate's CIN.

**Tables** (full DDL in `db/schema.sql`)
- `users` — Telegram identity: `telegram_user_id` (PK-ish), locale, timestamps.
- `profiles` — one per user: name FR/AR, `cin_encrypted`, target grades[], specialties[],
  `include_off_target` bool, onboarding state.
- `announcement_sources` — registry of sources: name, type (PORTAL/MINISTRY/TELEGRAM/
  AGGREGATOR), url, last_run_at, last_status.
- `competitions` — canonical competitions: canonical_hash (unique), administration,
  grade, specialty, required_degree, deadline, post_count, submission_link, reference_code,
  stage (AVIS/CONVOQUES/RESULTATS), early_signal bool, source refs, raw payload.
- `tracked_competitions` — join of user↔competition: state
  (APPLIED/EN_ATTENTE_CONVOCATION/CONVOQUE/RESULTAT), last_checked_at, last_pdf_url,
  rollcall result JSON.

## Key decisions
- Multi-user identity = Telegram user id; no passwords.
- CIN encrypted at rest (Fernet), decrypted only in-memory during roll-call.
- Two languages by design: TS bot (Edge), Python for scraping/PDF/matching.
- Gemini used only as a fallback for unstructured/scanned inputs to conserve free quota.
- Dedup via canonical hash; cross-source arrival tracked with `early_signal`.
- Admin web never receives CIN (enforced via RLS + column selection).

## Risks
- Source HTML/structure changes → scrapers isolated behind the `Scraper` protocol so a
  break is contained to one module.
- Scanned Arabic PDFs may defeat text parsing → Gemini fallback + explicit "not detected"
  messaging rather than silent failure.
- Supabase free project pauses after 7 days idle → cron jobs touch the DB regularly.
- Telegram/aggregator scraping is noisy/ToS-sensitive → community sources are additive and
  clearly flagged, official portals remain source of truth.
