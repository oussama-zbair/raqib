# Setup & Deployment

## 0. Prerequisites
- A Supabase account (free tier) — 1 project.
- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- A Google AI Studio key for Gemini (free tier).
- A Cloudflare account (Pages, free).
- Python 3.11+, Node 20+, and the Supabase CLI.

## 1. Database (Supabase)
1. Create a project at supabase.com.
2. Open the SQL editor and run [`db/schema.sql`](../db/schema.sql).
3. From Project Settings → API, copy the **URL**, **anon key**, and **service_role key**.

## 2. Secrets
Generate a CIN encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Copy `.env.example` to `.env` and fill values (see the file for each variable).

## 3. Python backend (GitHub Actions)
Local run:
```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate    # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.jobs.ingest      # one-shot ingest
python -m app.jobs.monitor     # one-shot lifecycle monitor
python -m app.jobs.digest      # one-shot digest
```
For CI, add these repository secrets (Settings → Secrets → Actions), matching
`.env.example`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `TELEGRAM_BOT_TOKEN`,
`GEMINI_API_KEY`, `CIN_ENCRYPTION_KEY`. Workflows live in `.github/workflows/`.

## 4. Telegram bot (Supabase Edge Function)
```bash
supabase functions deploy telegram-bot --no-verify-jwt
supabase secrets set TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_SECRET=... \
  SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=...
```
Register the webhook (replace placeholders):
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<PROJECT>.functions.supabase.co/telegram-bot&secret_token=<WEBHOOK_SECRET>"
```

## 5. Nuxt admin web (Cloudflare Pages)
```bash
cd web
npm install
npm run dev        # local
npm run build      # production build
```
On Cloudflare Pages, set build command `npm run build`, output `dist/` (or `.output/public`
per adapter), and env vars `NUXT_PUBLIC_SUPABASE_URL`, `NUXT_PUBLIC_SUPABASE_ANON_KEY`.

## 6. Scheduled jobs (GitHub Actions)
Three cron workflows live in `.github/workflows/`:

| Workflow | Schedule (UTC) | Purpose |
|----------|----------------|---------|
| `ingest.yml`  | every 3 hours   | scrape → dedup → upsert → match → queue digests |
| `monitor.yml` | every 30 min    | poll tracked concours, roll-call CIN on new PDFs |
| `digest.yml`  | daily 07:00     | send each candidate their matched competitions |

`ci.yml` runs the backend test suite and the Nuxt build on every push/PR. All schedules
can be triggered manually via the Actions tab (`workflow_dispatch`).

## 7. Verify
- Backend tests: `cd backend && python -m pytest` (22 tests).
- Web build: `cd web && npm run build`.
- Send `/start` to the bot and complete onboarding.
- Trigger the ingest workflow manually (`workflow_dispatch`) and confirm rows in
  `competitions`.
- Track a competition, then run `monitor` against a known convocation PDF.
