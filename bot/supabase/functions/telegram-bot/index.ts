// Raqib Telegram bot — Supabase Edge Function (Deno).
//
// A rich, bilingual (FR/AR) bot: welcome banner, main-menu hub, editable profile,
// full settings (language, off-target, pause, quiet hours, delete data), one-click
// concours tracking, and an owner-only admin panel (stats + broadcast).
//
// Conversation state is persisted in `profiles.onboarding_state`. Alongside the real
// onboarding states we use ephemeral "AWAIT_*" states for edit / quiet / broadcast flows.

import {
  answerCallbackQuery,
  editMessageText,
  InlineButton,
  sendMessage,
  sendPhoto,
} from "./telegram.ts";
import {
  adminStats,
  allTelegramIds,
  deleteUser,
  ensureProfile,
  ProfileRow,
  setUserLocale,
  trackCompetition,
  listTracked,
  updateProfile,
  upsertUser,
  UserRow,
} from "./db.ts";
import {
  adminMenu,
  backRow,
  confirmDelete,
  gradeButtons,
  languageMenu,
  mainMenu,
  profileMenu,
  settingsMenu,
  specialtyKeyboard,
} from "./keyboards.ts";
import { normalizeLocale, t, type Locale } from "./i18n.ts";
import { labelForGrade, labelForSpecialty } from "./taxonomy.ts";
import { encryptCin, last4 } from "./crypto.ts";

const WEBHOOK_SECRET = Deno.env.get("TELEGRAM_WEBHOOK_SECRET") ?? "";
// A public URL to the logo image (PNG/JPG that Telegram can fetch). Falls back to the site.
const LOGO_URL =
  Deno.env.get("LOGO_URL") ??
  `${Deno.env.get("SITE_URL") ?? "https://raqib.pages.dev"}/logo.png`;

// Ephemeral conversation states (stored in onboarding_state alongside COMPLETE).
const S = {
  editNameFr: "EDIT_NAME_FR",
  editNameAr: "EDIT_NAME_AR",
  editCin: "EDIT_CIN",
  quiet: "AWAIT_QUIET",
  broadcast: "AWAIT_BROADCAST",
} as const;

// ---------- helpers ----------

function profileSummary(locale: Locale, p: ProfileRow): string {
  const none = t(locale, "profile.none");
  const grades = (p.target_grades ?? []).map((k) => labelForGrade(k, locale)).join(", ") || none;
  const specs = (p.target_specialties ?? []).map((k) => labelForSpecialty(k, locale)).join(", ") || none;
  return [
    t(locale, "profile.title"),
    "",
    `👤 ${t(locale, "profile.nameFr")}: ${p.full_name_fr ?? none}`,
    `🖋 ${t(locale, "profile.nameAr")}: ${p.full_name_ar ?? none}`,
    `🪪 ${t(locale, "profile.cin")}: ${p.cin_last4 ? "***" + p.cin_last4 : none}`,
    `🎯 ${t(locale, "profile.grades")}: ${grades}`,
    `🧩 ${t(locale, "profile.specialties")}: ${specs}`,
  ].join("\n");
}

// ---------- command / message handling ----------

async function showMenu(chatId: number, user: UserRow, locale: Locale, edit?: number) {
  const kb = mainMenu(locale, user.is_owner);
  const text = t(locale, "menu.title");
  if (edit) await editMessageText(chatId, edit, text, kb);
  else await sendMessage(chatId, text, kb);
}

async function startFlow(chatId: number, user: UserRow, locale: Locale) {
  const profile = await ensureProfile(user.id);
  if (profile.onboarding_state === "COMPLETE") {
    await sendPhoto(chatId, LOGO_URL, t(locale, "welcome.caption"));
    await sendMessage(chatId, t(locale, "welcome.back"), mainMenu(locale, user.is_owner));
    return;
  }
  await sendPhoto(chatId, LOGO_URL, t(locale, "welcome.caption"));
  await updateProfile(user.id, { onboarding_state: "AWAIT_NAME_FR" });
  await sendMessage(chatId, t(locale, "welcome.intro"));
  await sendMessage(chatId, t(locale, "onb.askNameFr"));
}

async function handleText(chatId: number, user: UserRow, locale: Locale, text: string) {
  const profile = await ensureProfile(user.id);
  const state = profile.onboarding_state;

  switch (state) {
    // ----- onboarding -----
    case "AWAIT_NAME_FR":
      await updateProfile(user.id, { full_name_fr: text, onboarding_state: "AWAIT_NAME_AR" });
      await sendMessage(chatId, t(locale, "onb.askNameAr"));
      return;
    case "AWAIT_NAME_AR":
      await updateProfile(user.id, {
        full_name_ar: text === "-" ? null : text,
        onboarding_state: "AWAIT_CIN",
      });
      await sendMessage(chatId, t(locale, "onb.askCin"));
      return;
    case "AWAIT_CIN": {
      const cin = text.trim().toUpperCase();
      await updateProfile(user.id, {
        cin_encrypted: await encryptCin(cin),
        cin_last4: last4(cin),
        onboarding_state: "AWAIT_GRADE",
      });
      await sendMessage(chatId, t(locale, "onb.askGrade"), gradeButtons(locale));
      return;
    }

    // ----- profile edits -----
    case S.editNameFr:
      await updateProfile(user.id, { full_name_fr: text, onboarding_state: "COMPLETE" });
      await sendMessage(chatId, t(locale, "settings.saved"));
      await sendProfile(chatId, user, locale);
      return;
    case S.editCin: {
      const cin = text.trim().toUpperCase();
      await updateProfile(user.id, {
        cin_encrypted: await encryptCin(cin),
        cin_last4: last4(cin),
        onboarding_state: "COMPLETE",
      });
      await sendMessage(chatId, t(locale, "settings.saved"));
      await sendProfile(chatId, user, locale);
      return;
    }

    // ----- quiet hours -----
    case S.quiet: {
      const v = text.trim().toLowerCase();
      if (v === "off") {
        await updateProfile(user.id, {
          quiet_start: null, quiet_end: null, onboarding_state: "COMPLETE",
        });
        await sendMessage(chatId, t(locale, "settings.quietSet", { value: t(locale, "settings.quietOff") }));
      } else {
        const m = v.match(/^(\d{1,2})\s*[-–]\s*(\d{1,2})$/);
        if (m) {
          const start = Math.min(23, parseInt(m[1], 10));
          const end = Math.min(23, parseInt(m[2], 10));
          await updateProfile(user.id, {
            quiet_start: start, quiet_end: end, onboarding_state: "COMPLETE",
          });
          await sendMessage(chatId, t(locale, "settings.quietSet", { value: `${start}h–${end}h` }));
        } else {
          await sendMessage(chatId, t(locale, "settings.quietPrompt"));
          return;
        }
      }
      await sendSettings(chatId, user, locale);
      return;
    }

    // ----- admin broadcast -----
    case S.broadcast: {
      if (!user.is_owner) {
        await updateProfile(user.id, { onboarding_state: "COMPLETE" });
        return;
      }
      await updateProfile(user.id, { onboarding_state: "COMPLETE" });
      const ids = await allTelegramIds();
      let sent = 0;
      for (const id of ids) {
        try {
          await sendMessage(id, `📣 ${text}`);
          sent++;
        } catch { /* skip blocked users */ }
      }
      await sendMessage(chatId, t(locale, "admin.broadcastSent", { count: sent }));
      return;
    }

    default:
      await sendMessage(chatId, t(locale, "common.unknown"), mainMenu(locale, user.is_owner));
  }
}

async function sendProfile(chatId: number, user: UserRow, locale: Locale, edit?: number) {
  const p = await ensureProfile(user.id);
  const text = profileSummary(locale, p);
  if (edit) await editMessageText(chatId, edit, text, profileMenu(locale));
  else await sendMessage(chatId, text, profileMenu(locale));
}

async function sendSettings(chatId: number, user: UserRow, locale: Locale, edit?: number) {
  const p = await ensureProfile(user.id);
  const text = t(locale, "settings.title") + "\n\n" + t(locale, "settings.offTargetHint");
  if (edit) await editMessageText(chatId, edit, text, settingsMenu(locale, p));
  else await sendMessage(chatId, text, settingsMenu(locale, p));
}

async function sendTracked(chatId: number, user: UserRow, locale: Locale, edit?: number) {
  const rows = await listTracked(user.id);
  let text: string;
  if (rows.length === 0) {
    text = t(locale, "tracked.title") + "\n\n" + t(locale, "tracked.empty");
  } else {
    const lines = rows.map((r, i) => {
      const c = r.competitions;
      const title = (locale === "ar" ? c?.title_ar : c?.title_fr) || c?.title_fr || c?.administration || "Concours";
      const state = t(locale, `tracked.state.${r.state}`);
      return `${i + 1}. <b>${title}</b>\n   ${state}`;
    });
    text = t(locale, "tracked.title") + "\n\n" + lines.join("\n\n");
  }
  const kb = [backRow(locale)];
  if (edit) await editMessageText(chatId, edit, text, kb);
  else await sendMessage(chatId, text, kb);
}

// ---------- callback (button) handling ----------

async function handleCallback(
  chatId: number,
  messageId: number,
  user: UserRow,
  locale: Locale,
  data: string,
  cbId: string,
) {
  // onboarding grade / specialty
  if (data.startsWith("grade:")) {
    const key = data.slice(6);
    await updateProfile(user.id, { target_grades: [key], onboarding_state: "AWAIT_SPECIALTY" });
    await answerCallbackQuery(cbId, labelForGrade(key, locale));
    await editMessageText(chatId, messageId, t(locale, "onb.askSpecialty"), specialtyKeyboard(locale, []));
    return;
  }
  if (data.startsWith("spec:")) {
    const key = data.slice(5);
    const p = await ensureProfile(user.id);
    const set = new Set(p.target_specialties ?? []);
    set.has(key) ? set.delete(key) : set.add(key);
    const list = [...set];
    await updateProfile(user.id, { target_specialties: list });
    await answerCallbackQuery(cbId);
    await editMessageText(chatId, messageId, t(locale, "onb.askSpecialty"), specialtyKeyboard(locale, list));
    return;
  }
  if (data === "spec_done") {
    await updateProfile(user.id, { onboarding_state: "COMPLETE" });
    await answerCallbackQuery(cbId, t(locale, "onb.done"));
    await editMessageText(chatId, messageId, t(locale, "onb.done"));
    await sendMenu(chatId, user, locale);
    return;
  }

  // navigation
  switch (data) {
    case "menu":
      await answerCallbackQuery(cbId);
      await showMenu(chatId, user, locale, messageId);
      return;
    case "profile":
      await answerCallbackQuery(cbId);
      await sendProfile(chatId, user, locale, messageId);
      return;
    case "tracked":
      await answerCallbackQuery(cbId);
      await sendTracked(chatId, user, locale, messageId);
      return;
    case "settings":
      await answerCallbackQuery(cbId);
      await sendSettings(chatId, user, locale, messageId);
      return;
    case "help":
      await answerCallbackQuery(cbId);
      await editMessageText(chatId, messageId, `${t(locale, "help.title")}\n\n${t(locale, "help.body")}`, [backRow(locale)]);
      return;
    case "language":
      await answerCallbackQuery(cbId);
      await editMessageText(chatId, messageId, t(locale, "lang.title"), languageMenu());
      return;

    // profile edits
    case "edit_name":
      await updateProfile(user.id, { onboarding_state: S.editNameFr });
      await answerCallbackQuery(cbId);
      await sendMessage(chatId, t(locale, "onb.askNameFr"));
      return;
    case "edit_cin":
      await updateProfile(user.id, { onboarding_state: S.editCin });
      await answerCallbackQuery(cbId);
      await sendMessage(chatId, t(locale, "onb.askCin"));
      return;
    case "edit_grades":
      await answerCallbackQuery(cbId);
      await editMessageText(chatId, messageId, t(locale, "onb.askGrade"), gradeButtons(locale));
      return;
    case "edit_specialties": {
      const p = await ensureProfile(user.id);
      await answerCallbackQuery(cbId);
      await editMessageText(chatId, messageId, t(locale, "onb.askSpecialty"), specialtyKeyboard(locale, p.target_specialties ?? []));
      return;
    }

    // settings toggles
    case "toggle_offtarget": {
      const p = await ensureProfile(user.id);
      await updateProfile(user.id, { include_off_target: !p.include_off_target });
      await answerCallbackQuery(cbId, t(locale, "settings.saved"));
      await sendSettings(chatId, user, locale, messageId);
      return;
    }
    case "toggle_pause": {
      const p = await ensureProfile(user.id);
      const paused = !p.paused;
      await updateProfile(user.id, { paused });
      await answerCallbackQuery(cbId, paused ? t(locale, "settings.pausedMsg") : t(locale, "settings.resumedMsg"));
      await sendSettings(chatId, user, locale, messageId);
      return;
    }
    case "set_quiet":
      await updateProfile(user.id, { onboarding_state: S.quiet });
      await answerCallbackQuery(cbId);
      await sendMessage(chatId, t(locale, "settings.quietPrompt"));
      return;
    case "delete_data":
      await answerCallbackQuery(cbId);
      await editMessageText(chatId, messageId, t(locale, "settings.deleteConfirm"), confirmDelete(locale));
      return;
    case "delete_confirm":
      await answerCallbackQuery(cbId);
      await deleteUser(user.id);
      await editMessageText(chatId, messageId, t(locale, "settings.deleted"));
      return;

    // admin
    case "admin":
      if (!user.is_owner) return void answerCallbackQuery(cbId, t(locale, "admin.denied"));
      await answerCallbackQuery(cbId);
      await editMessageText(chatId, messageId, t(locale, "admin.title"), adminMenu(locale));
      return;
    case "admin_stats": {
      if (!user.is_owner) return void answerCallbackQuery(cbId, t(locale, "admin.denied"));
      await answerCallbackQuery(cbId);
      const s = await adminStats();
      const body = `${t(locale, "admin.title")}\n\n${t(locale, "admin.statsBody", { ...s })}`;
      await editMessageText(chatId, messageId, body, adminMenu(locale));
      return;
    }
    case "admin_broadcast":
      if (!user.is_owner) return void answerCallbackQuery(cbId, t(locale, "admin.denied"));
      await updateProfile(user.id, { onboarding_state: S.broadcast });
      await answerCallbackQuery(cbId);
      await sendMessage(chatId, t(locale, "admin.broadcastPrompt"));
      return;
  }

  // language set
  if (data.startsWith("setlang:")) {
    const loc = normalizeLocale(data.slice(8));
    await setUserLocale(user.id, loc);
    await answerCallbackQuery(cbId, t(loc, "lang.set"));
    await showMenu(chatId, { ...user, locale: loc }, loc, messageId);
    return;
  }

  // one-click tracking (from digest messages)
  if (data.startsWith("track:")) {
    const id = parseInt(data.slice(6), 10);
    if (!Number.isNaN(id)) {
      await trackCompetition(user.id, id);
      await answerCallbackQuery(cbId, t(locale, "tracked.added"));
      await sendMessage(chatId, t(locale, "tracked.added"));
    }
    return;
  }

  await answerCallbackQuery(cbId);
}

// alias used after onboarding finish
async function sendMenu(chatId: number, user: UserRow, locale: Locale) {
  await sendMessage(chatId, t(locale, "menu.title"), mainMenu(locale, user.is_owner));
}

// ---------- webhook entrypoint ----------

Deno.serve(async (req: Request) => {
  if (WEBHOOK_SECRET) {
    const got = req.headers.get("x-telegram-bot-api-secret-token");
    if (got !== WEBHOOK_SECRET) return new Response("forbidden", { status: 403 });
  }

  let update: Record<string, any>;
  try {
    update = await req.json();
  } catch {
    return new Response("bad request", { status: 400 });
  }

  try {
    if (update.message) {
      const msg = update.message;
      const from = msg.from;
      const chatId = msg.chat.id;
      const user = await upsertUser(from.id, from.username ?? null);
      const locale = normalizeLocale(user.locale);
      const text: string = msg.text ?? "";

      if (text.startsWith("/start")) await startFlow(chatId, user, locale);
      else if (text.startsWith("/menu")) await showMenu(chatId, user, locale);
      else if (text.startsWith("/profil")) await sendProfile(chatId, user, locale);
      else if (text.startsWith("/parametres")) await sendSettings(chatId, user, locale);
      else if (text.startsWith("/mes_concours")) await sendTracked(chatId, user, locale);
      else if (text.startsWith("/langue")) await sendMessage(chatId, t(locale, "lang.title"), languageMenu());
      else if (text.startsWith("/aide")) await sendMessage(chatId, `${t(locale, "help.title")}\n\n${t(locale, "help.body")}`, [backRow(locale)]);
      else if (text.startsWith("/admin")) {
        if (user.is_owner) await sendMessage(chatId, t(locale, "admin.title"), adminMenu(locale));
        else await sendMessage(chatId, t(locale, "admin.denied"));
      } else await handleText(chatId, user, locale, text);
    } else if (update.callback_query) {
      const cq = update.callback_query;
      const from = cq.from;
      const chatId = cq.message.chat.id;
      const messageId = cq.message.message_id;
      const user = await upsertUser(from.id, from.username ?? null);
      const locale = normalizeLocale(user.locale);
      await handleCallback(chatId, messageId, user, locale, cq.data ?? "", cq.id);
    }
  } catch (err) {
    console.error("handler error", err);
  }

  return new Response("ok", { status: 200 });
});
