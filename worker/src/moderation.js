import { BAD_WORDS } from "./badwords.js";

// Same normalisation for the word list and for messages.
export function normalize(text) {
  let t = String(text ?? "").toLowerCase().normalize("NFKD");
  t = t.replace(/[\u0300-\u036f\u064b-\u065f\u0670\u0640]/g, ""); // accents, tashkeel, tatweel
  t = t.replace(/[أإآٱ]/g, "ا").replace(/ى/g, "ي").replace(/ة/g, "ه");
  t = t.replace(/ؤ/g, "و").replace(/ئ/g, "ي");
  return t.replace(/(.)\1+/g, "$1"); // collapse repeated letters
}

const tokenize = (text) => normalize(text).split(/[^\p{L}\p{N}]+/u).filter(Boolean);

const WORDS = new Set();
const PHRASES = [];
for (const entry of BAD_WORDS) {
  const tokens = tokenize(entry);
  if (tokens.length === 1) WORDS.add(tokens[0]);
  else if (tokens.length > 1) PHRASES.push(` ${tokens.join(" ")} `);
}

// Arabic attaches small prefixes to words ("وزامل", "الزامل").
function withoutPrefix(token) {
  if (token.startsWith("ال") && token.length > 4) return token.slice(2);
  if ("وفبلك".includes(token[0]) && token.length > 3) return token.slice(1);
  return token;
}

export function containsBadWord(text) {
  const tokens = tokenize(text);
  if (tokens.some((t) => WORDS.has(t) || WORDS.has(withoutPrefix(t)))) return true;
  const joined = ` ${tokens.join(" ")} `;
  return PHRASES.some((p) => joined.includes(p));
}

export const MAX_STRIKES = 3;
export const MUTE_SECONDS = 24 * 60 * 60;
const STRIKE_TTL_SECONDS = 30 * 24 * 60 * 60;

// Counts offenses per user and group in Workers KV. Without the KV binding every
// offense counts as the first one (delete and warn only).
export async function addStrike(env, chatId, userId) {
  if (!env.STRIKES) return 1;
  const key = `strike:${chatId}:${userId}`;
  const count = (parseInt(await env.STRIKES.get(key), 10) || 0) + 1;
  await env.STRIKES.put(key, String(count), { expirationTtl: STRIKE_TTL_SECONDS });
  return count;
}
