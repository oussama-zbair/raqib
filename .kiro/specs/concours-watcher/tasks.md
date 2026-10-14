# Tasks — Raqib (رقيب)

Incremental, verifiable slices. Each builds on the previous.

## 1. Foundation
- [ ] 1.1 Monorepo structure + top-level README, .gitignore, .env.example
- [ ] 1.2 Database schema (`db/schema.sql`): users, profiles, announcement_sources,
      competitions, tracked_competitions + enums, indexes, RLS notes + seed sources

## 2. Python backend core
- [ ] 2.1 `config.py` settings from env; `requirements.txt`
- [ ] 2.2 `db/models.py` pydantic models; `db/client.py` Supabase REST wrapper
- [ ] 2.3 `security/crypto.py` Fernet CIN encrypt/decrypt

## 3. Matching
- [ ] 3.1 `matching/taxonomy.py` FR/AR grade + specialty synonyms + negative terms
- [ ] 3.2 `matching/normalizer.py` normalize + canonical_hash
- [ ] 3.3 `matching/matcher.py` matches_profile + negative filtering
- [ ] 3.4 unit tests for matcher & normalizer

## 4. Ingestion
- [ ] 4.1 `scrapers/base.py` Scraper protocol + RawAnnouncement model
- [ ] 4.2 `scrapers/emploi_public.py` scrape Avis/Convoqués/Résultats (FR+AR)
- [ ] 4.3 `extractors/gemini.py` structured JSON fallback

## 5. PDF roll-call
- [ ] 5.1 `pdf/rollcall.py` download + pdfplumber parse + CIN search + seat extraction
- [ ] 5.2 unit test with a synthetic convocation PDF fixture

## 6. Notify + orchestration
- [ ] 6.1 `notify/telegram.py` send helpers (message, digest, urgent convocation)
- [ ] 6.2 `jobs/ingest.py`, `jobs/monitor.py`, `jobs/digest.py`

## 7. Telegram bot (Edge Function, TS)
- [ ] 7.1 `bot/index.ts` webhook: /start onboarding state machine
- [ ] 7.2 inline `📌 Suivre` callback + `/mes_concours` dashboard

## 8. Nuxt admin web
- [ ] 8.1 Nuxt app scaffold + Supabase client + Cloudflare Pages config
- [ ] 8.2 Dashboard pages: sources health, competitions, tracking stats (no CIN)

## 9. Orchestration + docs
- [ ] 9.1 GitHub Actions cron workflows (ingest / monitor / digest)
- [ ] 9.2 Deployment + setup docs; verify structure builds
