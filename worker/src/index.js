import { addStrike, containsBadWord, MAX_STRIKES, MUTE_SECONDS } from "./moderation.js";

// Raqib bot: Cloudflare Worker webhook.
//  1. Private chat: join-the-channel gate, then a welcome menu ("made by" included).
//  2. Discussion group: delete links and insults from non-admins. Insults earn strikes:
//     1st warning, 2nd mute for 24h, 3rd ban (strikes live in the STRIKES KV namespace).
// Secrets (wrangler secret put): BOT_TOKEN, WEBHOOK_SECRET.
// Vars (wrangler.toml): CHANNEL (@name), GROUP (@name), OWNER (@name).

const MEMBER_STATUSES = new Set(["creator", "administrator", "member"]);
const ADMIN_STATUSES = new Set(["creator", "administrator"]);

export function esc(text) {
  return String(text ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export const TEXTS = {
  ar: {
    gate: "👁 <b>رقيب</b>\n\nللاستمرار، انضم أولا إلى القناة، ثم اضغط «تحقق».",
    join: "📢 انضم إلى القناة",
    verify: "✅ تحقق",
    notYet: "لم تنضم إلى القناة بعد. انضم ثم اضغط «تحقق» مرة أخرى.",
    channel: "📢 القناة",
    group: "💬 النقاش",
    other: "🇫🇷 Français",
    welcome: (name, owner) =>
      `أهلا ${esc(name)} 👋\nمرحبا بك في <b>رقيب</b> 👁\n\n` +
      "كل مباريات التوظيف العمومي تصلك في القناة فور صدورها.\n" +
      "✨ قريبا: إشعارات مخصصة حسب تخصصك.\n\n" +
      `صُنع بـ ❤️ من طرف ${esc(owner)}`,
  },
  fr: {
    gate: "👁 <b>Raqib</b>\n\nPour continuer, rejoignez d'abord la chaîne, puis appuyez sur « Vérifier ».",
    join: "📢 Rejoindre la chaîne",
    verify: "✅ Vérifier",
    notYet: "Vous n'avez pas encore rejoint la chaîne. Rejoignez-la puis réessayez.",
    channel: "📢 Chaîne",
    group: "💬 Discussion",
    other: "🇲🇦 العربية",
    welcome: (name, owner) =>
      `Bonjour ${esc(name)} 👋\nBienvenue sur <b>Raqib</b> 👁\n\n` +
      "Tous les concours publics arrivent dans la chaîne dès leur publication.\n" +
      "✨ Bientôt : des alertes personnalisées selon votre spécialité.\n\n" +
      `Fait avec ❤️ par ${esc(owner)}`,
  },
};

const link = (handle) => `https://t.me/${String(handle).replace(/^@/, "")}`;
const otherLang = (lang) => (lang === "fr" ? "ar" : "fr");

export function gateKeyboard(env, lang) {
  const t = TEXTS[lang];
  return {
    inline_keyboard: [
      [{ text: t.join, url: link(env.CHANNEL) }],
      [{ text: t.verify, callback_data: `verify:${lang}` }],
      [{ text: t.other, callback_data: `gate:${otherLang(lang)}` }],
    ],
  };
}

export function menuKeyboard(env, lang) {
  const t = TEXTS[lang];
  return {
    inline_keyboard: [
      [
        { text: t.channel, url: link(env.CHANNEL) },
        { text: t.group, url: link(env.GROUP) },
      ],
      [{ text: t.other, callback_data: `menu:${otherLang(lang)}` }],
    ],
  };
}

async function tg(env, method, payload, fetchFn = fetch) {
  const res = await fetchFn(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  // Never log the URL: it contains the bot token.
  return res.json().catch(() => ({ ok: false }));
}

export async function isMember(env, userId, fetchFn = fetch) {
  const res = await tg(env, "getChatMember", { chat_id: env.CHANNEL, user_id: userId }, fetchFn);
  if (!res.ok) return false;
  const r = res.result;
  return MEMBER_STATUSES.has(r.status) || (r.status === "restricted" && r.is_member === true);
}

async function isAdmin(env, chatId, userId, fetchFn) {
  const res = await tg(env, "getChatMember", { chat_id: chatId, user_id: userId }, fetchFn);
  return Boolean(res.ok && ADMIN_STATUSES.has(res.result.status));
}

export function hasLink(message) {
  const entities = [...(message.entities || []), ...(message.caption_entities || [])];
  return entities.some((e) => e.type === "url" || e.type === "text_link");
}

function showName(user) {
  return user.first_name || user.username || "";
}

async function handleStart(env, message, fetchFn) {
  const lang = "ar";
  const joined = await isMember(env, message.from.id, fetchFn);
  if (joined) {
    await tg(env, "sendMessage", {
      chat_id: message.chat.id,
      text: TEXTS[lang].welcome(showName(message.from), env.OWNER),
      parse_mode: "HTML",
      reply_markup: menuKeyboard(env, lang),
    }, fetchFn);
  } else {
    await tg(env, "sendMessage", {
      chat_id: message.chat.id,
      text: TEXTS[lang].gate,
      parse_mode: "HTML",
      reply_markup: gateKeyboard(env, lang),
    }, fetchFn);
  }
}

async function handleCallback(env, cb, fetchFn) {
  const [action, rawLang] = String(cb.data || "").split(":");
  const lang = rawLang === "fr" ? "fr" : "ar";
  const edit = { chat_id: cb.message.chat.id, message_id: cb.message.message_id, parse_mode: "HTML" };
  const joined = await isMember(env, cb.from.id, fetchFn);
  if (!joined) {
    // Gate again on every action, so someone who left the channel is locked out.
    if (action === "verify") {
      await tg(env, "answerCallbackQuery", {
        callback_query_id: cb.id, text: TEXTS[lang].notYet, show_alert: true,
      }, fetchFn);
      return;
    }
    await tg(env, "answerCallbackQuery", { callback_query_id: cb.id }, fetchFn);
    await tg(env, "editMessageText", {
      ...edit, text: TEXTS[lang].gate, reply_markup: gateKeyboard(env, lang),
    }, fetchFn);
    return;
  }
  await tg(env, "answerCallbackQuery", { callback_query_id: cb.id }, fetchFn);
  await tg(env, "editMessageText", {
    ...edit,
    text: TEXTS[lang].welcome(showName(cb.from), env.OWNER),
    reply_markup: menuKeyboard(env, lang),
  }, fetchFn);
}

const WARNINGS = {
  1: "⚠️ {name}، تم حذف رسالتك لاحتوائها على كلمات غير لائقة. تحذير 1/3.",
  2: "🔇 {name}، تم كتمك لمدة 24 ساعة بسبب تكرار الإساءة. تحذير 2/3.",
  3: "🚫 {name}، تم حظرك من المجموعة بسبب تكرار الإساءة.",
};

async function punish(env, message, fetchFn) {
  const user = message.from;
  const strikes = Math.min(await addStrike(env, message.chat.id, user.id), MAX_STRIKES);
  const name = `<a href="tg://user?id=${user.id}">${esc(showName(user))}</a>`;
  if (strikes === 2) {
    await tg(env, "restrictChatMember", {
      chat_id: message.chat.id,
      user_id: user.id,
      permissions: { can_send_messages: false },
      until_date: Math.floor(Date.now() / 1000) + MUTE_SECONDS,
    }, fetchFn);
  } else if (strikes >= MAX_STRIKES) {
    await tg(env, "banChatMember", { chat_id: message.chat.id, user_id: user.id }, fetchFn);
  }
  await tg(env, "sendMessage", {
    chat_id: message.chat.id,
    text: WARNINGS[strikes].replace("{name}", name),
    parse_mode: "HTML",
  }, fetchFn);
}

async function handleGroupMessage(env, message, fetchFn) {
  if (message.is_automatic_forward || !message.from || message.from.is_bot) return;
  if (message.sender_chat) return; // channel posts mirrored into the group
  const insulting = containsBadWord(message.text || message.caption || "");
  if (!hasLink(message) && !insulting) return;
  if (await isAdmin(env, message.chat.id, message.from.id, fetchFn)) return;
  await tg(env, "deleteMessage", {
    chat_id: message.chat.id, message_id: message.message_id,
  }, fetchFn);
  if (insulting) await punish(env, message, fetchFn);
}

export async function handleUpdate(env, update, fetchFn = fetch) {
  if (update.callback_query) {
    if (update.callback_query.message) await handleCallback(env, update.callback_query, fetchFn);
    return;
  }
  const message = update.message || update.edited_message;
  if (!message) return;
  if (message.chat.type === "private") {
    if (typeof message.text === "string" && message.text.startsWith("/start")) {
      await handleStart(env, message, fetchFn);
    }
    return;
  }
  const group = String(env.GROUP || "").replace(/^@/, "").toLowerCase();
  if (message.chat.username && message.chat.username.toLowerCase() === group) {
    await handleGroupMessage(env, message, fetchFn);
  }
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("Raqib bot", { status: 200 });
    if (request.headers.get("x-telegram-bot-api-secret-token") !== env.WEBHOOK_SECRET) {
      return new Response("forbidden", { status: 403 });
    }
    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("bad request", { status: 400 });
    }
    try {
      await handleUpdate(env, update);
    } catch {
      // Swallow errors: a 500 would make Telegram retry the same update.
    }
    return new Response("ok", { status: 200 });
  },
};
