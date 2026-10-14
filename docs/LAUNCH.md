# 🚀 Raqib — Launch Guide (step by step)

Follow these in order. Each step says **what to do** and **how to verify** it worked.
Nothing here is destructive. Total time: ~45–60 min.

Legend: 🧑 = you do it · 🤖 = already done in the repo

---

## Phase 0 — Accounts you need (free)
🧑 Create these if you don't have them:
- [ ] GitHub account
- [ ] Supabase account → https://supabase.com
- [ ] Cloudflare account → https://dash.cloudflare.com
- [ ] Google AI Studio key (Gemini) → https://aistudio.google.com/apikey
- [ ] Telegram + the bot you already made (`@RaqibBot`) via https://t.me/BotFather

Install CLIs:
```bash
npm install -g supabase        # Supabase CLI
# Node 20+ and Python 3.11+ should already be installed
```

---

## Phase 1 — Push the code to GitHub
🧑 From the repo root `raqib/`:
```bash
git init
git add .
git commit -m "Raqib: initial"
git branch -M main
# create an empty repo on github.com named "raqib", then:
git remote add origin https://github.com/<YOUR_USERNAME>/raqib.git
git push -u origin main
```
✅ **Verify:** your code shows on github.com, and the **Actions** tab lists the 4 workflows
(they'll fail until secrets are set — that's expected, we fix it in Phase 5).

> ⚠️ Confirm `.env` files are NOT pushed (they're in `.gitignore`). Only `.env.example` should appear.

---

## Phase 2 — Supabase project + database
🧑
1. Create a new project at supabase.com (pick a region close to Morocco, e.g. Paris).
2. Open **SQL Editor** → New query → paste all of [`db/schema.sql`](../db/schema.sql) → Run.
3. New query → paste [`db/migrations/001_bot_settings.sql`](../db/migrations/001_bot_settings.sql) → Run.
4. Go to **Project Settings → API** and copy three values:
   - Project URL
   - `anon` public key
   - `service_role` secret key

✅ **Verify:** in **Table Editor** you see `users`, `profiles`, `competitions`,
`tracked_competitions`, `announcement_sources`, `digest_queue`, and
`announcement_sources` already has 5 seed rows.

---

## Phase 3 — Generate the shared secrets
🧑 Generate the CIN encryption key (used by BOTH backend and bot — must be identical):
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Copy the output. Find your numeric Telegram id by messaging https://t.me/userinfobot.

Keep these handy for the next phases:
| Secret | Value |
|--------|-------|
| `SUPABASE_URL` | from Phase 2 |
| `SUPABASE_SERVICE_ROLE_KEY` | from Phase 2 |
| `SUPABASE_ANON_KEY` | from Phase 2 |
| `TELEGRAM_BOT_TOKEN` | from @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | run `openssl rand -hex 16` (or any random string) |
| `GEMINI_API_KEY` | from Google AI Studio |
| `CIN_ENCRYPTION_KEY` | the Fernet key above |
| `OWNER_TELEGRAM_ID` | your Telegram id |

---

## Phase 4 — Deploy the website (Cloudflare Pages)
🧑
1. Cloudflare Dashboard → **Workers & Pages** → Create → **Pages** → Connect to Git → pick your `raqib` repo.
2. Build settings:
   - **Framework preset:** Nuxt (or None)
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
   - **Root directory:** `web`
3. Add environment variables:
   - `NUXT_PUBLIC_SUPABASE_URL` = your Supabase URL
   - `NUXT_PUBLIC_SUPABASE_ANON_KEY` = your anon key
   - `NUXT_PUBLIC_TELEGRAM_BOT_URL` = `https://t.me/RaqibBot`
   - `NUXT_PUBLIC_GITHUB_URL` = your repo URL
4. Deploy.

✅ **Verify:** your site loads at `https://raqib-xxxx.pages.dev`, landing page renders,
`/competitions` + `/sources` show empty tables (not the "non configuré" banner).
Note the URL — the bot's logo banner uses `https://<that-url>/logo.png`.

---

## Phase 5 — GitHub Actions secrets (so the scrapers run)
🧑 GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add each of these (names must match exactly):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`
- `CIN_ENCRYPTION_KEY`

✅ **Verify:** Actions tab → run **"Ingest concours"** manually (Run workflow). It should
go green, and new rows appear in the `competitions` table in Supabase.

> If ingest finds 0 competitions, that's the scraper needing live-page tuning (a known
> MVP gap) — not a deployment failure. See Phase 8.

---

## Phase 6 — Deploy the Telegram bot (Supabase Edge Function)
🧑 From the repo root:
```bash
supabase login
supabase link --project-ref <YOUR_PROJECT_REF>   # ref is in your Supabase URL

# set all secrets (one command)
supabase secrets set \
  TELEGRAM_BOT_TOKEN=... \
  TELEGRAM_WEBHOOK_SECRET=... \
  SUPABASE_URL=... \
  SUPABASE_SERVICE_ROLE_KEY=... \
  CIN_ENCRYPTION_KEY=... \
  OWNER_TELEGRAM_ID=... \
  LOGO_URL=https://<your-cloudflare-url>/logo.png

# deploy
supabase functions deploy telegram-bot --no-verify-jwt
```
Register the webhook (replace `<TOKEN>`, `<PROJECT_REF>`, `<SECRET>`):
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<PROJECT_REF>.functions.supabase.co/telegram-bot&secret_token=<SECRET>"
```
✅ **Verify:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```
`url` is set and `pending_update_count` drains to 0. Then open `@RaqibBot`, press **Start** —
you should get the logo banner + bilingual welcome + onboarding.

---

## Phase 7 — Dress up the bot in @BotFather
🧑 Open https://t.me/BotFather and run (copy from [`bot/README.md`](../bot/README.md)):
- `/setuserpic` → upload `web/public/logo.png`
- `/setname` → `Raqib · رقيب`
- `/setabouttext` → (short tagline, in README)
- `/setdescription` → (full description, in README)
- `/setcommands` → (the 7-command list, in README)

✅ **Verify:** the bot profile shows the avatar + description, and typing `/` lists the commands.

---

## Phase 8 — First real end-to-end test
🧑
1. In `@RaqibBot`: `/start` → complete onboarding (name, CIN, grade, specialty).
2. `/menu` → check Profile, Settings (toggle language FR↔AR), `/admin` (you should see stats).
3. In Supabase, confirm your `users` + `profiles` rows exist and `is_owner = true`.
4. Actions → run **Ingest** again; if competitions appear and match your profile, run
   **"Send daily digest"** → you should receive a Telegram digest with a `📌 Suivre` button.

✅ If the digest arrives and the button tracks the concours → the full pipeline works.

---

## Phase 9 — Known gaps to tackle after launch (code side — I can help)
These don't block launch but are needed for real-world coverage:
- [ ] **Tune the `emploi-public.ma` scraper** against the live site (section URLs + parsing).
- [ ] **Wire Gemini vision** into the monitor job for scanned (image-only) convocation PDFs.
- [ ] **Add ministry scrapers** (Finances, Justice, Intérieur…).
- [ ] **Telethon community ingestion** for the EARLY_SIGNAL feature.

---

## Quick reference — which secret goes where
| Secret | GitHub Actions | Supabase Edge Fn | Cloudflare Pages |
|--------|:---:|:---:|:---:|
| SUPABASE_URL | ✓ | ✓ | (public) |
| SUPABASE_SERVICE_ROLE_KEY | ✓ | ✓ | ✗ |
| SUPABASE_ANON_KEY | ✗ | ✗ | ✓ (public) |
| TELEGRAM_BOT_TOKEN | ✓ | ✓ | ✗ |
| TELEGRAM_WEBHOOK_SECRET | ✗ | ✓ | ✗ |
| GEMINI_API_KEY | ✓ | ✗ | ✗ |
| CIN_ENCRYPTION_KEY | ✓ | ✓ | ✗ |
| OWNER_TELEGRAM_ID | ✗ | ✓ | ✗ |
| LOGO_URL | ✗ | ✓ | ✗ |

> The `service_role` key is powerful — only ever in server-side places (Actions, Edge Fn).
> The website only ever gets the `anon` key.
