"""Dedup, posted state, channel formatting and the publish job (offline, fake sources)."""
from __future__ import annotations

import json
from datetime import date

from app.db.models import RawAnnouncement, SourceType
from app.jobs import publish_channel
from app.jobs.dedup import dedup_items, merge_group
from app.jobs.posted_state import PostedState
from app.notify.channel import (
    CAPTION_LIMIT,
    channel_footer,
    format_channel_post,
    format_for_send,
    format_update_post,
)


def _ann(source="wadifapublic.ma", url="https://w/1", **kw) -> RawAnnouncement:
    kw.setdefault("title", "x")
    return RawAnnouncement(
        source_name=source, source_type=SourceType.AGGREGATOR, source_url=url, detail_url=url, **kw
    )


def _wadifa():
    return _ann(
        administration="وزارة الصحة",
        grade="مهندس دولة",
        specialty="هندسة بيوطبية / المعلوميات",
        post_count=20,
        deadline=date(2026, 12, 28),
        reference_code="C 44891/26",
        logo_url="https://w/logo.png",
    )


def _emploi():
    return _ann(
        source="emploi-public.ma",
        url="https://e/9",
        administration="Ministère de la Santé",
        grade="Ingénieur d'Etat",
        post_count=20,
        deadline=date(2026, 12, 28),
        exam_date=date(2027, 1, 10),
        reference_code="C 44891/26",
        official_url="https://e/9",
    )


# ---- dedup ---------------------------------------------------------------------------
def test_same_reference_code_merges_across_languages():
    groups = dedup_items([_wadifa(), _emploi()])
    assert len(groups) == 1
    merged = merge_group(groups[0])
    assert merged.source_name == "emploi-public.ma"  # official source wins
    assert merged.specialty == "هندسة بيوطبية / المعلوميات"  # missing field filled from wadifa
    assert merged.official_url == "https://e/9"


def test_different_reference_codes_stay_apart():
    other = _emploi().model_copy(update={"reference_code": "C 1/26", "source_url": "https://e/2",
                                         "detail_url": "https://e/2", "official_url": "https://e/2"})
    assert len(dedup_items([_wadifa(), other])) == 2


def test_fuzzy_admin_and_deadline_without_reference_code():
    a = _ann(source="dreamjob.ma", url="https://d/1", administration="Ministère de la Santé",
             deadline=date(2026, 12, 28))
    b = _emploi().model_copy(update={"reference_code": None})
    assert len(dedup_items([a, b])) == 1


def test_item_without_deadline_matches_on_admin_and_post_count():
    d = _ann(source="dreamjob.ma", url="https://d/1", administration="Ministère de la Santé",
             post_count=20)
    assert len(dedup_items([d, _emploi()])) == 1
    d2 = d.model_copy(update={"post_count": 21})
    assert len(dedup_items([d2, _emploi()])) == 2


# ---- channel formatting --------------------------------------------------------------
def test_post_layout_matches_wadifa():
    text = format_channel_post(merge_group([_wadifa(), _emploi()]), "@RaqibEmploi")
    assert text.split("\n") == [
        "🟢 إعلان توظيف جديد",
        "🏛 Ministère de la Santé",
        "👥 عدد المناصب: 20",
        "💼 الدرجة: Ingénieur d'Etat",
        "🛠 التخصصات المطلوبة:",
        "🔷 هندسة بيوطبية",
        "🔷 المعلوميات",
        "⏳ آخر أجل للتسجيل: 28/12/2026",
        "📅 تاريخ الاختبار الكتابي: 10/01/2027",
        "🔗 اضغط هنا للتفاصيل: https://e/9",
        "",
        "📢 t.me/RaqibEmploi",
    ]


def test_exam_date_placeholder_footer_and_escaping():
    ann = _wadifa().model_copy(update={"administration": "A <b> & B \u2014 C"})
    text = format_channel_post(ann, None)
    assert "سيتم الإعلان عنه لاحقا" in text
    assert "t.me" not in text  # footer omitted when TELEGRAM_CHANNEL_ID is unset
    assert "A &lt;b&gt; &amp; B - C" in text
    assert "\u2014" not in text
    assert channel_footer("@RaqibEmploi") == "📢 t.me/RaqibEmploi"
    assert channel_footer("", dry_run=True) == "📢 t.me/RaqibEmploi"
    assert channel_footer("") is None


def test_caption_fits_and_keeps_it_specialties():
    specs = " / ".join([f"Droit {i}" for i in range(30)] + ["Génie logiciel"])
    ann = _wadifa().model_copy(update={"specialty": specs, "administration": "A" * 300})
    assert "Génie logiciel" in format_channel_post(ann, "@c")
    assert len(format_for_send(ann, "@RaqibEmploi")) <= CAPTION_LIMIT


def test_update_post():
    text = format_update_post(_emploi(), {"deadline": date(2027, 1, 5)}, "📢 t.me/RaqibEmploi")
    assert "05/01/2027" in text and text.startswith("🔄")


# ---- state ---------------------------------------------------------------------------
def test_state_roundtrip_and_update_detection(tmp_path):
    path = tmp_path / "posted.json"
    state = PostedState(path)
    entry = state.add_posted(merge_group([_wadifa(), _emploi()]), 42)
    state.reject("https://rejected/1")
    state.save()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["posted"][0]["telegram_message_id"] == 42
    assert "\\u" not in path.read_text(encoding="utf-8")  # Arabic stays readable

    again = PostedState(path)
    assert again.knows_url("https://rejected/1")
    assert again.find(_wadifa()) is not None  # matched by reference code
    moved = _emploi().model_copy(update={"deadline": date(2027, 1, 5)})
    assert again.changes(entry, moved) == {"deadline": date(2027, 1, 5)}
    assert again.changes(entry, _emploi()) == {}


# ---- the job -------------------------------------------------------------------------
class _FakeScraper:
    def __init__(self, name, items, fail=False):
        self.source_name = name
        self._items = items
        self._fail = fail

    def fetch(self):
        if self._fail:
            raise RuntimeError("boom")
        return list(self._items)

    def enrich(self, ann, client=None):
        # Like the real detail fetch: fills the specialty the listing does not carry.
        return ann.model_copy(update={"specialty": ann.specialty or "Informatique"})


def _run(tmp_path, scrapers, sent, **kw):
    def sender(ann, text, channel, reply_to=None, with_button=True):
        sent.append((text, reply_to))
        return 100 + len(sent)

    return publish_channel.run(
        state_path=tmp_path / "s.json", scrapers=scrapers, sender=sender, **kw
    )


def test_job_posts_once_dedups_and_survives_a_failing_source(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@RaqibEmploi")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("time.sleep", lambda s: None)
    nonit = _wadifa().model_copy(update={"specialty": "الطب العام", "grade": "طبيب",
                                         "reference_code": "C 1/26", "source_url": "https://w/2",
                                         "detail_url": "https://w/2"})
    scrapers = [
        _FakeScraper("wadifapublic.ma", [_wadifa(), nonit]),
        _FakeScraper("emploi-public.ma", [_emploi()]),
        _FakeScraper("dreamjob.ma", [], fail=True),
    ]
    sent: list = []
    first = _run(tmp_path, scrapers, sent)
    assert first["posts"] == 1  # duplicate merged, non-IT dropped
    assert first["sources"]["dreamjob.ma"].startswith("FAILED")
    assert "t.me/RaqibEmploi" in sent[0][0]

    second = _run(tmp_path, scrapers, sent)
    assert second["posts"] == 0 and second["updates"] == 0
    assert len(sent) == 1

    changed = _emploi().model_copy(update={"deadline": date(2027, 1, 5)})
    scrapers[1] = _FakeScraper("emploi-public.ma", [changed])
    third = _run(tmp_path, scrapers, sent)
    assert third["posts"] == 0 and third["updates"] == 1
    assert sent[1][1] == 101  # reply to the original message
    assert _run(tmp_path, scrapers, sent)["updates"] == 0
    get_settings.cache_clear()


def test_dry_run_sends_nothing_and_keeps_state_unless_asked(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "")
    monkeypatch.setattr("time.sleep", lambda s: None)
    from app.config import get_settings

    get_settings.cache_clear()
    sent: list = []
    scrapers = [_FakeScraper("wadifapublic.ma", [_wadifa()])]
    res = _run(tmp_path, scrapers, sent, dry_run=True)
    assert res["posts"] == 1 and not sent
    assert "📢 t.me/RaqibEmploi" in capsys.readouterr().out  # placeholder footer
    assert not (tmp_path / "s.json").exists()
    _run(tmp_path, scrapers, sent, dry_run=True, save_state=True)
    assert _run(tmp_path, scrapers, sent, dry_run=True)["posts"] == 0
    get_settings.cache_clear()


def test_state_is_saved_after_each_send_when_a_later_send_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@RaqibEmploi")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setattr("time.sleep", lambda s: None)
    from app.config import get_settings
    get_settings.cache_clear()
    second = _wadifa().model_copy(update={"reference_code": "C 2/26", "source_url": "https://w/2",
                                          "detail_url": "https://w/2", "post_count": 3,
                                          "administration": "Autre administration"})
    scrapers = [_FakeScraper("wadifapublic.ma", [_wadifa(), second])]
    calls: list = []

    def flaky(ann, text, channel, reply_to=None, with_button=True):
        calls.append(ann.reference_code)
        if len(calls) == 2:
            raise RuntimeError("telegram down")
        return 200 + len(calls)

    try:
        publish_channel.run(state_path=tmp_path / "s.json", scrapers=scrapers, sender=flaky)
        raised = False
    except RuntimeError:
        raised = True
    assert raised
    saved = json.loads((tmp_path / "s.json").read_text(encoding="utf-8"))
    assert len(saved["posted"]) == 1  # the delivered post is remembered
    sent: list = []
    again = _run(tmp_path, scrapers, sent)
    assert again["posts"] == 1 and len(sent) == 1  # only the undelivered one is sent
    get_settings.cache_clear()