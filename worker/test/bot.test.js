import test from "node:test";
import assert from "node:assert/strict";
import { handleUpdate, hasLink, esc } from "../src/index.js";

const env = {
  BOT_TOKEN: "t", WEBHOOK_SECRET: "s",
  CHANNEL: "@RaqibEmploi", GROUP: "@RaqibDiscussion", OWNER: "@owernam18",
};

// Fake Telegram: records calls, answers getChatMember from a status map.
function fakeTelegram(statuses) {
  const calls = [];
  const fetchFn = async (url, init) => {
    const method = url.split("/").pop();
    const body = JSON.parse(init.body);
    calls.push({ method, body });
    if (method === "getChatMember") {
      const status = statuses[`${body.chat_id}:${body.user_id}`] ?? "left";
      return { json: async () => ({ ok: true, result: { status } }) };
    }
    return { json: async () => ({ ok: true, result: {} }) };
  };
  return { calls, fetchFn };
}

const startMsg = (name = "Ahmed<b>") => ({
  message: { chat: { id: 5, type: "private" }, from: { id: 5, first_name: name }, text: "/start" },
});

test("non member sees the gate with join and verify buttons", async () => {
  const { calls, fetchFn } = fakeTelegram({});
  await handleUpdate(env, startMsg(), fetchFn);
  const sent = calls.find((c) => c.method === "sendMessage");
  assert.ok(sent.body.text.includes("تحقق"));
  const buttons = sent.body.reply_markup.inline_keyboard.flat();
  assert.ok(buttons.some((b) => b.url === "https://t.me/RaqibEmploi"));
  assert.ok(buttons.some((b) => b.callback_data === "verify:ar"));
});

test("member gets a welcome with name escaped and made-by line", async () => {
  const { calls, fetchFn } = fakeTelegram({ "@RaqibEmploi:5": "member" });
  await handleUpdate(env, startMsg(), fetchFn);
  const sent = calls.find((c) => c.method === "sendMessage");
  assert.ok(sent.body.text.includes("Ahmed&lt;b&gt;"));
  assert.ok(sent.body.text.includes("@owernam18"));
  assert.ok(!sent.body.text.includes("\u2014"));
});

test("verify fails when not joined, passes after joining", async () => {
  const cb = { callback_query: { id: "1", data: "verify:ar", from: { id: 7, first_name: "Sara" },
    message: { chat: { id: 7 }, message_id: 9 } } };
  let t = fakeTelegram({});
  await handleUpdate(env, cb, t.fetchFn);
  const alert = t.calls.find((c) => c.method === "answerCallbackQuery");
  assert.equal(alert.body.show_alert, true);
  assert.ok(!t.calls.some((c) => c.method === "editMessageText"));

  t = fakeTelegram({ "@RaqibEmploi:7": "member" });
  await handleUpdate(env, cb, t.fetchFn);
  const edit = t.calls.find((c) => c.method === "editMessageText");
  assert.ok(edit.body.text.includes("Sara"));
});

test("language toggle keeps the gate for non members", async () => {
  const cb = { callback_query: { id: "1", data: "menu:fr", from: { id: 8, first_name: "Y" },
    message: { chat: { id: 8 }, message_id: 3 } } };
  const t = fakeTelegram({});
  await handleUpdate(env, cb, t.fetchFn);
  const edit = t.calls.find((c) => c.method === "editMessageText");
  assert.ok(edit.body.text.includes("rejoignez"));
});

const groupMsg = (extra) => ({
  message: { chat: { id: -100, type: "supergroup", username: "RaqibDiscussion" },
    message_id: 11, from: { id: 20, first_name: "X" }, text: "http://spam.example", ...extra },
});
const urlEntity = [{ type: "url", offset: 0, length: 19 }];

test("link from a normal member is deleted", async () => {
  const t = fakeTelegram({});
  await handleUpdate(env, groupMsg({ entities: urlEntity }), t.fetchFn);
  assert.ok(t.calls.some((c) => c.method === "deleteMessage" && c.body.message_id === 11));
});

test("link from an admin, a plain message and channel mirrors are kept", async () => {
  let t = fakeTelegram({ "-100:20": "administrator" });
  await handleUpdate(env, groupMsg({ entities: urlEntity }), t.fetchFn);
  assert.ok(!t.calls.some((c) => c.method === "deleteMessage"));

  t = fakeTelegram({});
  await handleUpdate(env, groupMsg({ text: "bonjour", entities: undefined }), t.fetchFn);
  assert.ok(!t.calls.some((c) => c.method === "deleteMessage"));

  t = fakeTelegram({});
  await handleUpdate(env, groupMsg({ entities: urlEntity, is_automatic_forward: true }), t.fetchFn);
  assert.ok(!t.calls.some((c) => c.method === "deleteMessage"));
});

test("other chats are ignored", async () => {
  const t = fakeTelegram({});
  const u = groupMsg({ entities: urlEntity });
  u.message.chat.username = "SomeoneElse";
  await handleUpdate(env, u, t.fetchFn);
  assert.equal(t.calls.length, 0);
});

test("helpers", () => {
  assert.equal(esc("<a&b>"), "&lt;a&amp;b&gt;");
  assert.equal(hasLink({ caption_entities: [{ type: "text_link" }] }), true);
  assert.equal(hasLink({ entities: [{ type: "mention" }] }), false);
});
