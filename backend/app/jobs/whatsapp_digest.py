"""WhatsApp digest: a ready-to-paste summary sent to the owner on Telegram.

WhatsApp has no API to post to a Channel, so the job prepares the post and the owner
pastes it (one tap copies a Telegram code block). Twice a day, Morocco time:

* from 09:00: everything published since the previous digest (the night's items);
* from 18:00: everything published during the day.

A slot that was missed (no run, Telegram down) is sent by the next run. Nothing new
means no message. WhatsApp formatting: *bold*, plain links (Telegram links are useless
to people without Telegram, so every line points to the official concours page).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.jobs.dedup import canonical_url, url_keys
from app.jobs.posted_state import PostedState
from app.matching.job_title import job_title
from app.notify.channel import AR_DAYS, AR_MONTHS, fmt_posts

log = logging.getLogger("whatsapp_digest")

TZ = ZoneInfo("Africa/Casablanca")
MORNING_HOUR, EVENING_HOUR = 9, 18
FIRST_DIGEST_HOURS = 12  # the very first digest covers the last 12 hours
PART_LIMIT = 3500  # Telegram allows 4096 characters per message
OFFICIAL = "https://www.emploi-public.ma/fr/concours/details/{uuid}"

STAGE_SECTIONS = [
    ("CONVOQUES", "📋 *لوائح المدعوين للكتابي*"),
    ("CONVOQUES_ORAL", "🎤 *لوائح المدعوين للشفوي*"),
    ("RESULTATS", "🏆 *النتائج النهائية*"),
]


def due_slot(now: datetime) -> str:
    """The latest digest slot that has started, e.g. '2026-11-26-am'."""
    local = now.astimezone(TZ)
    if local.hour >= EVENING_HOUR:
        return f"{local.date().isoformat()}-pm"
    if local.hour >= MORNING_HOUR:
        return f"{local.date().isoformat()}-am"
    return f"{(local.date() - timedelta(days=1)).isoformat()}-pm"


def _link(urls) -> str | None:
    key = next((k for k in url_keys(urls) if k.startswith("ep:")), None)
    return OFFICIAL.format(uuid=key[3:]) if key else next(iter(urls), None)


def _short_date(iso: str | None) -> str:
    if not iso:
        return ""
    d = date.fromisoformat(iso)
    return f"{d.day} {AR_MONTHS[d.month - 1]}"


def _one_line(text: str | None) -> str:
    return " ".join((text or "").split())


def _announcement_block(e: dict) -> str:
    title = job_title(e.get("grade")) or _one_line(e.get("grade"))
    lines = [f"💼 *{title}* · {_one_line(e.get('administration'))}"]
    facts = []
    if e.get("deadline"):
        facts.append(f"⏳ آخر أجل: {_short_date(e['deadline'])}")
    if e.get("post_count"):
        facts.append(f"👥 {fmt_posts(e['post_count'], 'ar')}")
    if e.get("city"):
        facts.append(f"📍 {e['city']}")
    if facts:
        lines.append(" · ".join(facts))
    link = _link(e.get("urls", []))
    if link:
        lines.append(f"🔗 {link}")
    return "\n".join(lines)


def _stage_block(s: dict) -> str:
    title = job_title(s.get("grade")) or _one_line(s.get("grade"))
    first = f"🏛 {_one_line(s.get('administration'))}"
    if title:
        first += f" · *{title}*"
    if s.get("exam_date") and s.get("stage") != "RESULTATS":
        first += f" · 📅 {_short_date(s['exam_date'])}"
    lines = [first]
    link = _link([s.get("url")] if s.get("url") else [])
    if link:
        lines.append(f"🔗 {link}")
    return "\n".join(lines)


STAGE_RANK = {"CONVOQUES": 1, "CONVOQUES_ORAL": 2, "RESULTATS": 3}
MAX_PER_SECTION = 8  # a WhatsApp post people actually read; the rest is on the website


def _concours_key(urls) -> str | None:
    return next((k for k in url_keys(urls) if k.startswith("ep:")), None)


def build_parts(state: PostedState, since: str, now: datetime, site: str, telegram: str) -> list[str]:
    """Digest text split into paste-sized parts. Empty list when nothing is new.

    Each concours appears once, at its most advanced stage (a concours whose list of
    invited candidates is already out is no longer "new"). Long sections are cut and
    point to the website for the rest.
    """
    today = now.astimezone(TZ).date().isoformat()
    latest: dict[str, dict] = {}
    for s in state.stages:
        if s.get("seeded") or s.get("telegram_message_id") is None:
            continue
        if (s.get("posted_at") or "") <= since:
            continue
        key = s["key"].split("#")[0]
        if key not in latest or STAGE_RANK.get(s["stage"], 0) > STAGE_RANK.get(latest[key]["stage"], 0):
            latest[key] = s
    stages = list(latest.values())
    new = [e for e in state.posted
           if (e.get("posted_at") or "") > since and (e.get("deadline") or "9999") >= today
           and _concours_key(e.get("urls", [])) not in latest]
    if not new and not stages:
        return []
    new.sort(key=lambda e: e.get("deadline") or "9999")  # closing soonest first

    local = now.astimezone(TZ)
    moment = "الصباح" if local.hour < EVENING_HOUR else "المساء"
    header = (f"👁 *رقيب | ملخص المباريات*\n"
              f"📅 {AR_DAYS[local.weekday()]} {local.day} {AR_MONTHS[local.month - 1]} "
              f"{local.year} · {moment}")
    footer = (f"🌐 كل المباريات مع البحث: {site}/competitions\n"
              f"✈️ تيليجرام: {telegram}\n"
              f"🤝 شارك القناة مع من يبحث عن عمل")

    blocks: list[str] = []
    if new:
        blocks.append(f"🟢 *مباريات جديدة ({len(new)})*")
        blocks += [_announcement_block(e) for e in new[:MAX_PER_SECTION]]
        if len(new) > MAX_PER_SECTION:
            blocks.append(f"➕ و{len(new) - MAX_PER_SECTION} أخرى: {site}/competitions")
    for stage, title in STAGE_SECTIONS:
        items = [s for s in stages if s.get("stage") == stage]
        if items:
            blocks.append(f"{title} ({len(items)})")
            blocks += [_stage_block(s) for s in items[:MAX_PER_SECTION]]
            if len(items) > MAX_PER_SECTION:
                blocks.append(f"➕ و{len(items) - MAX_PER_SECTION} أخرى: "
                              f"{site}/competitions?tab=updates")

    parts: list[list[str]] = [[header]]
    size = len(header)
    for block in blocks:
        if size + len(block) + 2 > PART_LIMIT - len(footer):
            parts.append([])
            size = 0
        parts[-1].append(block)
        size += len(block) + 2
    parts[-1].append(footer)
    return ["\n\n".join(p) for p in parts]


def _send(chat_id: str, parts: list[str]) -> None:
    """One short instruction, then each part as a plain message.

    Plain text (no code block): it reads right-to-left like the real post, and
    "Copy" on the message copies exactly what goes into WhatsApp, *bold* marks included.
    """
    from app.notify.channel import _request

    total = len(parts)
    how = (f"📲 <b>ملخص واتساب جاهز</b> ({total} {'رسالة' if total == 1 else 'رسائل'})\n"
           "اضغط مطولا على الرسالة التالية ← <b>نسخ</b>، ثم الصقها في قناة واتساب.\n"
           "على الحاسوب: زر الفأرة الأيمن ← Copy Text.")
    _request("sendMessage", {"chat_id": chat_id, "parse_mode": "HTML", "text": how})
    for i, part in enumerate(parts, 1):
        if total > 1:
            _request("sendMessage", {"chat_id": chat_id, "text": f"⬇️ {i}/{total}"})
        _request("sendMessage", {
            "chat_id": chat_id,
            "text": part,  # no parse_mode: the * stay as WhatsApp bold marks
            "link_preview_options": {"is_disabled": True},
        })


def maybe_send(state: PostedState, chat_id: str, site: str, telegram: str,
               now: datetime | None = None, sender=_send) -> int:
    """Send the digest when a new slot has started. Returns the number of parts sent."""
    if not chat_id:
        return 0
    now = now or datetime.now(timezone.utc)
    slot = due_slot(now)
    if state.last_digest_slot == slot:
        return 0
    since = state.last_digest_at or (now - timedelta(hours=FIRST_DIGEST_HOURS)).isoformat(
        timespec="seconds")
    parts = build_parts(state, since, now, site, telegram)
    if parts:
        sender(chat_id, parts)
        log.info("whatsapp digest sent: %d part(s)", len(parts))
    # Advance even when empty: the next digest starts from here.
    state.last_digest_slot = slot
    state.last_digest_at = now.isoformat(timespec="seconds")
    state.save()
    return len(parts)


__all__ = ["build_parts", "due_slot", "maybe_send", "canonical_url"]
