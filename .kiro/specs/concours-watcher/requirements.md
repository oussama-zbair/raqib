# Requirements — Raqib (رقيب)

## Problem

Moroccan graduates hunting for public-sector competitions (*concours de recrutement*)
lose opportunities not because exams are hard, but because information is fragmented,
late, and buried. Announcements are scattered across the central portal
(`emploi-public.ma`), individual ministry sites, and noisy Telegram/aggregator feeds.
Third-party reposts are often late, misleading, or omit the exact degree/specialty
requirements. Worst of all, after applying there is no email alert: convocation and
result PDFs are silently uploaded, and a candidate must manually scan hundreds of pages
for their CIN within 48–72h or miss the exam entirely.

## Users

- **Candidate** — a graduate (e.g. *Ingénieur d'État en Génie Logiciel, Échelle 11*)
  who registers a profile via a Telegram bot and receives filtered alerts.
- **Operator / Admin** — the person running the platform, who monitors source health,
  ingestion, and matching quality via a read-only Nuxt web dashboard.

## Scope (in)

- Multi-user profiles keyed by Telegram user ID, on always-free infrastructure.
- Ingestion + cross-referencing from `emploi-public.ma` first, then ministry sites and
  Telegram/aggregator feeds.
- Bilingual (FR/AR) grade & specialty matching with negative filtering.
- Gemini Flash fallback extraction for unstructured/scanned announcements.
- Lifecycle monitoring with automated PDF CIN roll-call and urgent alerts.
- Telegram bot as the primary user interface (onboarding, digest, tracking, alerts).
- Nuxt web app as an admin/status dashboard only.

## Scope (out / non-goals)

- No public web sign-up or candidate-facing web UX in v1 (bot handles that).
- No WhatsApp/SMS/email channels in v1.
- No paid infrastructure. Everything must run within always-free tiers.
- No professional/legal advice about the concours themselves.

## Success criteria

- A candidate can complete onboarding in the bot and store Name (FR/AR), CIN,
  target grade(s), and specialty(ies).
- Only competitions matching a candidate's grade + specialty are pushed to them;
  off-target roles (Technicien, civil/mécanique, sub-bac+5) are filtered out by default.
- Duplicate announcements from multiple sources collapse into one canonical record.
- When a tracked competition's convocation/result PDF is published, the system finds
  the candidate's CIN and returns centre/salle/table, or reports "not found".
- The whole pipeline runs on scheduled GitHub Actions + Supabase + Cloudflare free tiers.

## Acceptance criteria (EARS)

### Onboarding & profile
- WHEN a user sends `/start`, THE SYSTEM SHALL guide them to provide full name (FR & AR),
  CIN, target grade(s), and target specialty(ies), and persist a profile keyed by their
  Telegram user ID.
- THE SYSTEM SHALL store each CIN encrypted at rest and decrypt it only in memory during
  PDF roll-call.
- IF a user re-runs `/start` with an existing profile, THEN THE SYSTEM SHALL let them
  update fields rather than create a duplicate.

### Ingestion & deduplication
- WHEN the ingestion job runs, THE SYSTEM SHALL scrape `emploi-public.ma` sections
  (Avis de concours, Candidats convoqués, Résultats) in both FR and AR.
- THE SYSTEM SHALL compute a canonical identifier `hash(normalized_admin + grade + deadline)`
  for each competition and merge records sharing that identifier.
- IF a competition appears on a community/Telegram source before the official portal,
  THEN THE SYSTEM SHALL store it flagged `EARLY_SIGNAL` and clear the flag once the
  official portal publishes the formal notice/reference code.

### Matching
- THE SYSTEM SHALL match competitions to candidate profiles using FR and AR terminology
  for grade and specialty.
- THE SYSTEM SHALL reject postings for civil/agronomic/mechanical engineering or
  sub-bac+5 roles (e.g. Technicien, Adjoint) UNLESS the candidate explicitly opts in.
- WHEN an announcement is unstructured or a scanned image/PDF, THE SYSTEM SHALL pass its
  raw text to Gemini Flash to extract structured JSON
  `{administration, grade, specialty, required_degree, deadline, post_count, submission_link}`.

### Tracking & lifecycle
- WHEN a candidate taps `📌 Suivre ce concours`, THE SYSTEM SHALL move that competition
  into their tracking pipeline with state `APPLIED / EN ATTENTE DE CONVOCATION`.
- WHILE a competition is tracked, THE SYSTEM SHALL poll the Convoqués and Résultats tabs
  and the relevant ministry portal for updates matching that reference.
- WHEN a convocation/result PDF is published for a tracked competition, THE SYSTEM SHALL
  download it, parse text/tables, and search for the candidate's CIN and full name.
- IF the CIN is found, THEN THE SYSTEM SHALL extract centre, salle/amphi, and table number
  and send an urgent notification including a link to the source PDF.
- IF the list is published but the CIN is absent, THEN THE SYSTEM SHALL notify the
  candidate that they were not detected on the list.

### Interfaces
- THE SYSTEM SHALL deliver digests and alerts via the Telegram bot with inline buttons.
- THE SYSTEM SHALL expose a read-only admin dashboard (Nuxt) showing source health,
  ingested competitions, match stats, and tracking states.

### Infrastructure
- THE SYSTEM SHALL run ingestion, lifecycle monitoring, and digest jobs as scheduled
  GitHub Actions cron workflows.
- THE SYSTEM SHALL serve the interactive bot as a Supabase Edge Function webhook.
- THE SYSTEM SHALL store all shared state in a Supabase Postgres database.
