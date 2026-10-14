# Raqib Telegram Bot — Supabase Edge Function

A rich, bilingual (FR / AR) Telegram bot running as a Supabase Edge Function webhook.
Onboarding, a main-menu hub, editable profile, full settings, one-click concours
tracking, and an owner-only admin panel. Scraping, PDF roll-call, and digests are handled
by the Python backend cron jobs.

## Files
```
supabase/functions/telegram-bot/
  index.ts       webhook router: commands, menu, onboarding, settings, admin
  i18n.ts        FR/AR message catalog — t(locale, key, vars)
  keyboards.ts   inline keyboard builders (menu, profile, settings, admin, language)
  db.ts          Supabase data access (service role) + admin stats + broadcast
  telegram.ts    Bot API helpers (sendMessage, sendPhoto, editMessageText, setMyCommands)
  taxonomy.ts    grade/specialty options (keys match the Python taxonomy)
  crypto.ts      Fernet-compatible CIN encryption (decryptable by the Python monitor)
```

## Features
- **Welcome banner** — sends the Raqib logo + a bilingual intro on `/start`.
- **Main menu hub** — inline buttons; users rarely need to type commands.
- **Onboarding** — name (FR/AR) → CIN (encrypted) → grade → specialties.
- **Profile** (`/profil`) — view and edit every field.
- **Settings** (`/parametres`) — language, include-off-target toggle, pause/resume
  alerts, quiet hours, delete all data.
- **Tracking** — `📌 Suivre` on a digest message adds the concours to the user's pipeline;
  `/mes_concours` lists them with their lifecycle stage.
- **Admin** (`/admin`, owner only) — stats (users, profiles, competitions, tracked,
  source health) and broadcast a message to all users.
- **Bilingual** — every message in FR or AR based on the user's chosen locale.

## Commands
`/start` `/menu` `/profil` `/parametres` `/mes_concours` `/langue` `/aide` `/admin`

## Environment (Supabase secrets)
| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | from @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | random string validating incoming webhooks |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | DB access |
| `CIN_ENCRYPTION_KEY` | same Fernet key as the Python backend |
| `OWNER_TELEGRAM_ID` | your numeric Telegram user id (grants `/admin`) |
| `LOGO_URL` | public URL to the logo PNG (e.g. `https://<site>/logo.png`) |
| `SITE_URL` | (optional) used to derive `LOGO_URL` if not set |

Find your Telegram id by messaging [@userinfobot](https://t.me/userinfobot).

---

## Deploy (3 steps)

### 1. Set secrets
```bash
supabase secrets set \
  TELEGRAM_BOT_TOKEN=123456:ABC... \
  TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 16) \
  SUPABASE_URL=https://YOUR.supabase.co \
  SUPABASE_SERVICE_ROLE_KEY=eyJ... \
  CIN_ENCRYPTION_KEY=your-fernet-key \
  OWNER_TELEGRAM_ID=123456789 \
  LOGO_URL=https://YOUR-SITE.pages.dev/logo.png
```

### 2. Deploy the function
```bash
supabase functions deploy telegram-bot --no-verify-jwt
```

### 3. Register the webhook (replace placeholders)
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<PROJECT>.functions.supabase.co/telegram-bot&secret_token=<WEBHOOK_SECRET>"
```
Verify: `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"` — `url` should be set
and `pending_update_count` should drain to 0.

---

## @BotFather setup (copy-paste)

Open [@BotFather](https://t.me/BotFather) and run these:

**Avatar** — `/setuserpic` → choose `@RaqibBot` → upload `web/public/logo.png`.

**Name** — `/setname` →
```
Raqib · رقيب
```

**About** (short, shown on the profile) — `/setabouttext` →
```
Votre veilleur des concours publics marocains. Alertes pour chaque nouveau concours + votre convocation. رقيبك في المباريات العمومية.
```

**Description** (shown before Start) — `/setdescription` →
```
Raqib surveille les portails officiels, ministères et canaux communautaires. Il vous alerte dès qu'un nouveau concours correspond à votre profil — à temps pour déposer — puis dès que votre CIN apparaît sur une liste de convoqués. Bilingue FR/AR, gratuit.
```

**Commands** — `/setcommands` → choose the bot → paste:
```
start - Démarrer / Configurer mon profil
menu - Menu principal
profil - Voir et modifier mon profil
parametres - Langue, alertes, heures silencieuses
mes_concours - Mes concours suivis
langue - Changer de langue (FR/AR)
aide - Aide
```

That's it — open the bot and send `/start`.

## CIN encryption compatibility
`crypto.ts` implements the Fernet token format so the CIN encrypted here is decryptable by
Python's `cryptography.Fernet` in the monitor job (verified with a round-trip test).
