"""WhatsApp digest: slots, content, splitting, never twice, never empty."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.jobs.posted_state import PostedState
from app.jobs.whatsapp_digest import PART_LIMIT, build_parts, due_slot, maybe_send

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


def test_slots_follow_morocco_time():
    # Morocco is UTC+1 in late November.
    assert due_slot(_utc(2026, 11, 26, 7, 30)) == "2026-11-25-pm"  # 08:30 local
    assert due_slot(_utc(2026, 11, 26, 8, 0)) == "2026-11-26-am"   # 09:00 local
    assert due_slot(_utc(2026, 11, 26, 17, 0)) == "2026-11-26-pm"  # 18:00 local


def test_digest_content(tmp_path):
    parts = build_parts(_state(tmp_path), "2026-11-26T00:00:00+00:00", _utc(2026, 11, 26, 8, 30), SITE, TG)
    assert len(parts) == 1
    text = parts[0]
    assert text.startswith("👁 *رقيب | ملخص المباريات*")
    assert "🟢 *مباريات جديدة (1)*" in text and "💼 *تقني* · إقليم تاونات" in text
    assert "⏳ آخر أجل: 16 دجنبر · 👥 3 مناصب · 📍 تاونات" in text
    assert "https://www.emploi-public.ma/fr/concours/details/" in text  # short official link
    assert "📋 *لوائح المدعوين للكتابي* (1)" in text and "📅 تاريخ الاختبار: 29 نونبر" in text
    assert "🏆" not in text  # seeded stages are never in a digest
    assert "t.me/RaqibEmploi" in text and "raqib-emploi.pages.dev/competitions" in text
    assert "\u2014" not in text


def test_long_digest_is_split_into_paste_sized_parts(tmp_path):
    parts = build_parts(_state(tmp_path, n_new=40), "2026-11-26T00:00:00+00:00",
                        _utc(2026, 11, 26, 8, 30), SITE, TG)
    assert len(parts) > 1 and all(len(p) <= PART_LIMIT for p in parts)
    assert sum(p.count("💼") for p in parts) == 40  # nothing lost between parts


def test_sent_once_per_slot_and_never_empty(tmp_path):
    s = _state(tmp_path)
    sent: list = []
    morning = _utc(2026, 11, 26, 8, 30)
    assert maybe_send(s, "123", SITE, TG, now=morning, sender=lambda c, p: sent.append(p)) == 1
    assert maybe_send(s, "123", SITE, TG, now=morning + timedelta(minutes=30),
                      sender=lambda c, p: sent.append(p)) == 0  # same slot
    evening = _utc(2026, 11, 26, 17, 5)
    assert maybe_send(s, "123", SITE, TG, now=evening, sender=lambda c, p: sent.append(p)) == 0
    assert len(sent) == 1  # nothing new since the morning: no empty digest
    assert PostedState(tmp_path / "s.json").last_digest_slot == "2026-11-26-pm"


def test_no_owner_id_means_no_digest(tmp_path):
    assert maybe_send(_state(tmp_path), "", SITE, TG, now=_utc(2026, 11, 26, 8, 30),
                      sender=lambda c, p: 1 / 0) == 0
