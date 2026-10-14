// Minimal Telegram Bot API helpers for the Edge Function.

const TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN")!;
const API = `https://api.telegram.org/bot${TOKEN}`;

export interface InlineButton {
  text: string;
  callback_data?: string;
  url?: string;
}

async function call(method: string, body: Record<string, unknown>): Promise<any> {
  const resp = await fetch(`${API}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return resp.json().catch(() => ({}));
}

export async function sendMessage(
  chatId: number,
  text: string,
  buttons?: InlineButton[][],
): Promise<void> {
  const body: Record<string, unknown> = {
    chat_id: chatId,
    text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
  };
  if (buttons) body.reply_markup = { inline_keyboard: buttons };
  await call("sendMessage", body);
}

export async function sendPhoto(
  chatId: number,
  photoUrl: string,
  caption?: string,
): Promise<void> {
  await call("sendPhoto", {
    chat_id: chatId,
    photo: photoUrl,
    caption: caption ?? "",
    parse_mode: "HTML",
  });
}

/** Edit the message a callback came from (keeps the chat tidy for menu navigation). */
export async function editMessageText(
  chatId: number,
  messageId: number,
  text: string,
  buttons?: InlineButton[][],
): Promise<void> {
  const body: Record<string, unknown> = {
    chat_id: chatId,
    message_id: messageId,
    text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
  };
  if (buttons) body.reply_markup = { inline_keyboard: buttons };
  const res = await call("editMessageText", body);
  // If the message can't be edited (e.g. it was a photo), fall back to a new message.
  if (res && res.ok === false) await sendMessage(chatId, text, buttons);
}

export async function answerCallbackQuery(id: string, text?: string): Promise<void> {
  await call("answerCallbackQuery", { callback_query_id: id, text: text ?? "" });
}

/** Set the bot's command menu (the "/" list). Call once, e.g. from a setup route. */
export async function setMyCommands(
  commands: { command: string; description: string }[],
  languageCode?: string,
): Promise<void> {
  await call("setMyCommands", { commands, ...(languageCode ? { language_code: languageCode } : {}) });
}
