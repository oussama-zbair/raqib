# Raqib — رقيب

> **Votre veilleur des concours publics** · *رقيبك في المباريات العمومية* · *Your public-exam watchman*

**Raqib** (Arabic **رقيب**, "the watchman / the vigilant one") is a smart, zero-cost
automated platform that acts as a personal watchman for Moroccan public-sector
competitions (*concours de recrutement* / *مباريات التوظيف*).

The name says what it does: Raqib watches every concours so you never miss your CIN on a
convocation list.

It ingests announcements from official portals, ministry sites, and community feeds,
filters them to a candidate's exact profile (grade + specialty, FR/AR), and — critically —
monitors tracked exams to alert a candidate the second their **CIN** appears on a
convocation or results PDF.

## Why

The hardest part of a Moroccan concours often isn't the exam — it's the fragmented,
late, and noisy information. After you apply, there is no email notification: the
administration silently uploads a scanned PDF of *candidats convoqués*, and if you don't
catch it and find your CIN, exam center, and seat within 48–72h, you miss your chance.
This platform solves that.

## Architecture (all on always-free tiers)

| Concern | Runtime | Why |
|--------|---------|-----|
| Scraping, PDF roll-call, digests | **Python** on **GitHub Actions** (cron) | Stateless, periodic, heavy libs (pdfplumber, Telethon) |
| Interactive Telegram bot | **TypeScript** on **Supabase Edge Function** (webhook) | Sub-second button responses, no 24/7 server |
| Admin/status dashboard | **Nuxt (Vue)** on **Cloudflare Pages** | Read-only, unmetered free bandwidth |
| Shared state | **Supabase Postgres** | Single free DB for all runtimes |
| Ambiguous/scanned extraction | **Google Gemini Flash** (free tier) | Fallback only, to conserve quota |

```
backend/   Python — scrapers, matcher, PDF engine, notifier, cron jobs
bot/       TypeScript — Telegram webhook (Supabase Edge Function)
web/       Nuxt — read-only admin/status dashboard
db/        SQL — Supabase schema + seeds
docs/      Architecture & setup docs
.github/   GitHub Actions cron workflows
.kiro/     Kiro spec (requirements / design / tasks)
```

## Core flow

1. **Onboard** in the Telegram bot: name (FR/AR), CIN, target grade(s), specialty(ies).
2. **Ingest** cron scrapes sources → extracts (Gemini fallback) → normalizes → dedups
   into canonical competitions.
3. **Match** each competition to profiles by FR/AR grade + specialty, with negative
   filtering of off-target roles.
4. **Digest** pushes only matched, verified competitions to each candidate with a
   `📌 Suivre ce concours` button.
5. **Monitor** tracked competitions; when a convocation/result PDF drops, roll-call the
   candidate's CIN and send an urgent alert with centre / salle / table.

## Getting started

See [`docs/SETUP.md`](docs/SETUP.md) for full setup. Quick pointers:

- `db/schema.sql` — run in the Supabase SQL editor.
- `backend/` — `pip install -r requirements.txt`, copy `.env.example` → `.env`.
- `bot/` — deploy as a Supabase Edge Function, set the Telegram webhook.
- `web/` — `npm install && npm run dev`, deploy to Cloudflare Pages.

## Privacy

CIN is sensitive. It is stored **encrypted at rest** (Fernet) and decrypted **only in
memory** during PDF roll-call. The admin dashboard never receives CIN values.

## Status

MVP scaffold. `emploi-public.ma` is the first ingestion source; ministry portals and
Telegram/aggregator feeds are added behind the same `Scraper` interface.

## Brand

**Raqib** (رقيب) — "the watchman". The name is the promise: it watches every concours so
you never miss your CIN on a list.

**Palette**

| Role | Hex | Use |
|------|-----|-----|
| Zellij Green (primary) | `#0E7C66` / `#12987C` | logo, buttons, links |
| Night (base) | `#0B1220` | dark UI background |
| Saffron (accent) | `#F4B740` | highlights, the watching eye, CTAs |
| Atlas Red (alert) | `#D64545` | urgent convocation alerts |
| Text | `#E8EDF7` | on dark |

**Logo** — a Moroccan 8-point *khatam* star (Zellij Green) with a saffron eye in the
negative space. Assets: [`web/public/logo.svg`](web/public/logo.svg) (full),
[`web/public/favicon.svg`](web/public/favicon.svg) (small sizes / Telegram avatar).

**Suggested handles** (verify availability before claiming): GitHub `raqib`,
Telegram bot `@RaqibBot`, domain `raqib.ma`.

**Taglines** — FR: *Votre veilleur des concours publics* · AR: *رقيبك في المباريات العمومية*
· EN: *Your public-exam watchman*.
