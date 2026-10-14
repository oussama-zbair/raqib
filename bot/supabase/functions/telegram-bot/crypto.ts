// Fernet-compatible CIN encryption in Deno, so the Python monitor (cryptography.Fernet)
// can decrypt what the bot stores.
//
// Fernet token = base64url( 0x80 | timestamp(8B) | IV(16B) | ciphertext | HMAC(32B) )
//   - AES-128-CBC with PKCS7 padding, key = first 16 bytes of the Fernet key
//   - HMAC-SHA256 over (version|timestamp|IV|ciphertext), key = last 16 bytes
// The Fernet key (CIN_ENCRYPTION_KEY) is base64url(32 bytes): [signingKey(16) | encKey(16)].

const FERNET_KEY = Deno.env.get("CIN_ENCRYPTION_KEY")!;

function b64urlToBytes(s: string): Uint8Array {
  const b64 = s.replaceAll("-", "+").replaceAll("_", "/");
  const pad = b64 + "=".repeat((4 - (b64.length % 4)) % 4);
  const bin = atob(pad);
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

function bytesToB64url(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  // Fernet tokens use url-safe base64 WITH padding; keep the trailing '='.
  return btoa(bin).replaceAll("+", "-").replaceAll("/", "_");
}

function concat(...parts: Uint8Array[]): Uint8Array {
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let off = 0;
  for (const p of parts) {
    out.set(p, off);
    off += p.length;
  }
  return out;
}

export async function encryptCin(cin: string): Promise<string> {
  const key = b64urlToBytes(FERNET_KEY);
  if (key.length !== 32) throw new Error("CIN_ENCRYPTION_KEY must be 32 url-safe base64 bytes");
  const signingKey = key.slice(0, 16);
  const encKey = key.slice(16, 32);

  const iv = crypto.getRandomValues(new Uint8Array(16));
  const plaintext = new TextEncoder().encode(cin);

  const aesKey = await crypto.subtle.importKey("raw", encKey, { name: "AES-CBC" }, false, [
    "encrypt",
  ]);
  const ctBuf = await crypto.subtle.encrypt({ name: "AES-CBC", iv }, aesKey, plaintext);
  const ciphertext = new Uint8Array(ctBuf);

  const version = new Uint8Array([0x80]);
  const timestamp = new Uint8Array(8);
  const nowSec = Math.floor(Date.now() / 1000);
  // big-endian 64-bit timestamp
  new DataView(timestamp.buffer).setBigUint64(0, BigInt(nowSec), false);

  const signingParts = concat(version, timestamp, iv, ciphertext);
  const hmacKey = await crypto.subtle.importKey(
    "raw",
    signingKey,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sigBuf = await crypto.subtle.sign("HMAC", hmacKey, signingParts);
  const hmac = new Uint8Array(sigBuf);

  return bytesToB64url(concat(signingParts, hmac));
}

export function last4(cin: string): string {
  const digits = cin.replace(/\D/g, "");
  return digits.length >= 4 ? digits.slice(-4) : cin.slice(-4);
}
