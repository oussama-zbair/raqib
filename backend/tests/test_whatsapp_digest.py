"""WhatsApp digest: slots, content, splitting, never twice, never empty."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.jobs.posted_state import PostedState
from app.jobs.whatsapp_digest import (
    CAPTION_LIMIT, MAX_CARDS, PART_LIMIT, TZ, build_cards, build_parts, due_slot, maybe_send,
)

SITE, TG = "https://raqib-emploi.pages.dev", "https://t.me/RaqibEmploi"
UUID = "aaaaaaaa-1111-2222-3333-444444444444"


def _utc(y, m, d, h, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


def _state(tmp_path, n_new=1, posted_at="2026-11-26T08:00:00+00:00"):
    s = PostedState(tmp_path / "s.json")
    future = (date(2026, 11, 26) + timedelta(days=20)).isoformat()
    for i in range(n_new):
        s.posted.append({
            "id": f"x{i}", "administration": "إقليم تاونات", "grade": "تقني من الدرجة الثالثة - سُلمْ 9",
            "post_count": 3, "deadline": future, "city": "تاونات", "posted_at": posted_at,
            "urls": [f"https://www.emploi-public.ma/ar/تفاصيل/المباريات/{UUID[:-2]}{i:02d}"],
        })
    s.stages.append({"key": f"ep:{UUID}#CONVOQUES", "stage": "CONVOQUES", "administration": "جامعة ابن طفيل",
                     "grade": "متصرف من الدرجة الثانية", "exam_date": "2026-11-29", "telegram_message_id": 9,
                     "url": f"https://www.emploi-public.ma/ar/x/{UUID}", "posted_at": posted_at})
    s.stages.append({"key": "ep:old#RESULTATS", "stage": "RESULTATS", "seeded": True,
                     "telegram_message_id": None, "posted_at": posted_at})
    return s


def _local(y, m, d, h, mi=0):
    """A Morocco wall-clock time, as UTC (whatever the current offset is)."""
    return datetime(y, m, d, h, mi, tzinfo=TZ).astimezone(timezone.utc)


def test_slots_follow_morocco_local_time():
    assert due_slot(_local(2026, 11, 26, 8, 59)) == "2026-11-25-pm"
    assert due_slot(_local(2026, 11, 26, 9, 0)) == "2026-11-26-am"
    assert due_slot(_local(2026, 11, 26, 17, 59)) == "2026-11-26-am"
    assert due_slot(_local(2026, 11, 26, 18, 0)) == "2026-11-26-pm"


def test_offset_comes_from_the_official_rules_or_the_override(monkeypatch):
    from app.jobs import whatsapp_digest as wd
    monkeypatch.delenv("MOROCCO_UTC_OFFSET", raising=False)
    assert str(wd.morocco_tz()) == "Africa/Casablanca"  # follows every official change
    monkeypatch.setenv("MOROCCO_UTC_OFFSET", "1")
    assert wd.morocco_tz().utcoffset(None) == timedelta(hours=1)
    monkeypatch.setenv("MOROCCO_UTC_OFFSET", "0")
    assert wd.morocco_tz().utcoffset(None) == timedelta(0)
    monkeypatch.setenv("MOROCCO_UTC_OFFSET", "nonsense")
    assert str(wd.morocco_tz()) == "Africa/Casablanca"  # a bad override is ignored


def test_digest_content(tmp_path):
    parts = build_parts(_state(tmp_path), "2026-11-26T00:00:00+00:00", _local(2026, 11, 26, 9, 30), SITE, TG)
    assert len(parts) == 1
    text = parts[0]
    assert text.startswith("👁 *رقيب | ملخص المباريات*")
    assert "🟢 *مباريات جديدة (1)*" in text and "💼 *تقني* · إقليم تاونات" in text
    assert "⏳ آخر أجل: 16 دجنبر · 👥 3 مناصب · 📍 تاونات" in text
    assert "https://www.emploi-public.ma/fr/concours/details/" in text  # short official link
    assert "📋 *لوائح المدعوين للكتابي* (1)" in text
    assert "🏛 جامعة ابن طفيل · *متصرف* · 📅 29 نونبر" in text
    assert "🏆" not in text  # seeded stages are never in a digest
    assert "t.me/RaqibEmploi" in text and "raqib-emploi.pages.dev/competitions" in text
    assert "\u2014" not in text


def test_long_digest_is_split_into_paste_sized_parts(tmp_path):
    parts = build_parts(_state(tmp_path, n_new=40), "2026-11-26T00:00:00+00:00",
                        _local(2026, 11, 26, 9, 30), SITE, TG)
    assert all(len(p) <= PART_LIMIT for p in parts)
    text = "\n".join(parts)
    assert text.count("💼") == 8  # a readable post; the rest is on the website
    assert "➕ و32 أخرى: https://raqib-emploi.pages.dev/competitions" in text


def test_sent_once_per_slot_and_never_empty(tmp_path):
    s = _state(tmp_path)
    sent: list = []

    def sender(chat, cards, closing):
        sent.append(cards)

    morning = _local(2026, 11, 26, 9, 30)
    assert maybe_send(s, "123", SITE, TG, now=morning, sender=sender) == 2  # 1 new + 1 list
    assert maybe_send(s, "123", SITE, TG, now=morning + timedelta(minutes=30), sender=sender) == 0
    evening = _local(2026, 11, 26, 18, 5)
    assert maybe_send(s, "123", SITE, TG, now=evening, sender=sender) == 0
    assert len(sent) == 1  # nothing new since the morning: no empty digest
    assert PostedState(tmp_path / "s.json").last_digest_slot == "2026-11-26-pm"


def test_one_card_per_item_with_logo_and_whatsapp_caption(tmp_path):
    s = _state(tmp_path)
    s.posted[0]["logo_url"] = "https://e/logo.png"
    s.posted[0]["specialty"] = "الهندسة المدنية / الاعلاميات"
    cards, closing = build_cards(s, "2026-11-26T00:00:00+00:00", _local(2026, 11, 26, 9, 30), SITE, TG)
    assert len(cards) == 2
    new, stage = cards
    assert stage["caption"].startswith("📋 *لوائح المدعوين لاجتياز الاختبار الكتابي*")
    assert "🏛 *جامعة ابن طفيل*" in stage["caption"]
    assert new["caption"].startswith("🟢 *مباراة جديدة*")
    assert new["logo"] == "https://e/logo.png"
    assert "🎓 الهندسة المدنية · الاعلاميات" in new["caption"]
    assert "⏳ آخر أجل: *" in new["caption"] and "📝 الكتابي: سيعلن عنه لاحقا" in new["caption"]
    assert "🔗 التفاصيل: https://www.emploi-public.ma/fr/concours/details/" in new["caption"]
    assert "<" not in new["caption"]  # plain text, no HTML
    assert "raqib-emploi.pages.dev/competitions" in closing


def test_cards_fit_telegram_and_overflow_goes_to_the_website(tmp_path):
    s = _state(tmp_path, n_new=30)
    s.posted[0]["administration"] = "وزارة " * 300
    s.posted[0]["specialty"] = " / ".join(f"تخصص {i}" for i in range(60))
    cards, closing = build_cards(s, "2026-11-26T00:00:00+00:00", _local(2026, 11, 26, 9, 30), SITE, TG)
    assert len(cards) == MAX_CARDS
    assert all(len(c["caption"]) <= CAPTION_LIMIT for c in cards)
    assert "➕ و11 أخرى" in closing  # 31 items, 20 cards


def test_no_owner_id_means_no_digest(tmp_path):
    assert maybe_send(_state(tmp_path), "", SITE, TG, now=_local(2026, 11, 26, 9, 30),
                      sender=lambda c, p: 1 / 0) == 0


def test_each_concours_appears_once_at_its_latest_stage(tmp_path):
    s = _state(tmp_path)
    url = s.posted[0]["urls"][0]
    key = "ep:" + url.rsplit("/", 1)[1]
    at = "2026-11-26T08:00:00+00:00"
    for stage in ("CONVOQUES", "CONVOQUES_ORAL"):
        s.stages.append({"key": f"{key}#{stage}", "stage": stage, "administration": "إقليم تاونات",
                         "grade": "تقني", "telegram_message_id": 5, "url": url, "posted_at": at})
    text = "\n".join(build_parts(s, "2026-11-26T00:00:00+00:00", _local(2026, 11, 26, 9, 30), SITE, TG))
    assert "🟢" not in text  # its list is out: no longer a new concours
    assert text.count("إقليم تاونات") == 1 and "🎤" in text  # shown once, at the oral stage
