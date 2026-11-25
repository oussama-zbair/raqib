import test from "node:test";
import assert from "node:assert/strict";
import { handleUpdate } from "../src/index.js";
import { containsBadWord, normalize } from "../src/moderation.js";

function kv() {
  const m = new Map();
  return { get: async (k) => m.get(k) ?? null, put: async (k, v) => void m.set(k, v) };
}

function setup(adminIds = []) {
  const env = {
    BOT_TOKEN: "t", WEBHOOK_SECRET: "s", CHANNEL: "@RaqibEmploi",
    GROUP: "@RaqibDiscussion", OWNER: "@owernam18", STRIKES: kv(),
  };
  const calls = [];
  const fetchFn = async (url, init) => {
    const method = url.split("/").pop();
    const body = JSON.parse(init.body);
    calls.push({ method, body });
    if (method === "getChatMember") {
      const status = adminIds.includes(body.user_id) ? "administrator" : "member";
      return { json: async () => ({ ok: true, result: { status } }) };
    }
    return { json: async () => ({ ok: true, result: {} }) };
  };
  return { env, calls, fetchFn };
}

const say = (text, extra = {}) => ({
  message: {
    chat: { id: -100, type: "supergroup", username: "RaqibDiscussion" },
    message_id: 5, from: { id: 30, first_name: "Omar" }, text, ...extra,
  },
});
const has = (calls, method) => calls.some((c) => c.method === method);

test("word list matches insults in several spellings and not innocent text", () => {
  assert.equal(containsBadWord("you are a FUUUUCK"), true);
  assert.equal(containsBadWord("putain de concours"), true);
  assert.equal(containsBadWord("يا قَحْبَة"), true);
  assert.equal(containsBadWord("ولد القحبة"), true);
  assert.equal(containsBadWord("l9a7ba"), false); // not in the list, only exact entries
  assert.equal(containsBadWord("9a7ba"), true);
  assert.equal(containsBadWord("تبون رئيس الجمهورية"), false);
  assert.equal(containsBadWord("concours technicien informatique, merci"), false);
  assert.equal(containsBadWord("class assistant"), false);
  assert.equal(normalize("Éèêë"), "e");
});

test("strike 1 deletes and warns, strike 2 mutes 24h, strike 3 bans", async () => {
  const t = setup();
  await handleUpdate(t.env, say("putain"), t.fetchFn);
  assert.ok(has(t.calls, "deleteMessage") && has(t.calls, "sendMessage"));
  assert.ok(!has(t.calls, "restrictChatMember") && !has(t.calls, "banChatMember"));

  t.calls.length = 0;
  await handleUpdate(t.env, say("putain"), t.fetchFn);
  const mute = t.calls.find((c) => c.method === "restrictChatMember");
  assert.equal(mute.body.permissions.can_send_messages, false);
  const delta = mute.body.until_date - Math.floor(Date.now() / 1000);
  assert.ok(delta > 86300 && delta <= 86400);

  t.calls.length = 0;
  await handleUpdate(t.env, say("putain"), t.fetchFn);
  assert.ok(has(t.calls, "banChatMember"));
});

test("admins are never punished and clean messages are left alone", async () => {
  const t = setup([30]);
  await handleUpdate(t.env, say("putain"), t.fetchFn);
  assert.ok(!has(t.calls, "deleteMessage"));

  const t2 = setup();
  await handleUpdate(t2.env, say("bonjour tout le monde"), t2.fetchFn);
  assert.equal(t2.calls.length, 0);
});

test("edited messages are moderated and a missing KV only warns", async () => {
  const t = setup();
  delete t.env.STRIKES;
  const edited = { edited_message: say("fuck").message };
  await handleUpdate(t.env, edited, t.fetchFn);
  assert.ok(has(t.calls, "deleteMessage"));
  t.calls.length = 0;
  await handleUpdate(t.env, edited, t.fetchFn);
  assert.ok(!has(t.calls, "banChatMember"));
});

test("a link that also insults is deleted once with one strike", async () => {
  const t = setup();
  await handleUpdate(t.env, say("putain http://x.co", { entities: [{ type: "url", offset: 7, length: 11 }] }), t.fetchFn);
  assert.equal(t.calls.filter((c) => c.method === "deleteMessage").length, 1);
  assert.ok(!has(t.calls, "restrictChatMember"));
});

