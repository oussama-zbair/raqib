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
def test_card_is_arabic_when_any_source_is_arabic():
    text = format_channel_post(merge_group([_wadifa(), _emploi()]), "@RaqibEmploi")
    assert text.split("\n") == [
        "🟢 <b>مباراة جديدة</b>",
        "",
        "🏛 <b>وزارة الصحة</b>",
        "💼 مهندس دولة",
        "🎓 هندسة بيوطبية · المعلوميات",
        "👥 20 منصبا",
        "",
        "⏳ آخر أجل: <b>الاثنين 28 دجنبر 2026</b>",
        "📝 الكتابي: الأحد 10 يناير 2027",
        "",
        "#معلوميات #هندسة #مباراة",
    ]
    assert "http" not in text and "t.me" not in text  # links live in the buttons


def test_card_is_french_when_only_french_exists():
    text = format_channel_post(_emploi().model_copy(update={"specialty": "Génie logiciel"}))
    assert text.startswith("🟢 <b>Nouveau concours</b>")
    assert "⏳ Date limite : <b>lundi 28 décembre 2026</b>" in text
    assert "👥 20 postes" in text
    assert "#معلوميات" in text  # tags stay Arabic for one channel-wide search


def test_exam_placeholder_and_escaping():
    ann = _wadifa().model_copy(update={"administration": "وزارة <b> & B \u2014 C"})
    text = format_channel_post(ann)
    assert "سيعلن عنه لاحقا" in text
    assert "وزارة &lt;b&gt; &amp; B - C" in text
    assert "\u2014" not in text


def test_arabic_post_count_agreement():
    from app.notify.channel import fmt_posts
    assert [fmt_posts(n, "ar") for n in (1, 2, 3, 10, 11, 100)] == [
        "منصب واحد", "منصبان", "3 مناصب", "10 مناصب", "11 منصبا", "100 منصب"]
    assert fmt_posts(1, "fr") == "1 poste"


def test_caption_fits_and_keeps_it_specialties():
    specs = " / ".join([f"قانون {i}" for i in range(40)] + ["هندسة البرمجيات"])
    ann = _wadifa().model_copy(update={"specialty": specs, "administration": "وزارة " * 120})
    assert "هندسة البرمجيات" in format_channel_post(ann)
    assert len(format_for_send(ann)) <= CAPTION_LIMIT


def test_update_post():
    text = format_update_post(_emploi(), {"deadline": date(2027, 1, 5)}, None)
    assert "mardi 5 janvier 2027" in text and text.startswith("🔄")


def test_stage_cards_and_tags():
    from app.db.models import CompetitionStage
    from app.notify.channel import format_stage_post, keyboard
    conv = _wadifa().model_copy(update={
        "stage": CompetitionStage.CONVOQUES, "exam_date": date(2026, 11, 29),
        "city": "الدار البيضاء", "list_pdf_url": "https://e/list.pdf"})
    text = format_stage_post(conv)
    assert text.startswith("📋 <b>لوائح المدعوين لاجتياز الاختبار الكتابي</b>")
    assert "📅 تاريخ الاختبار: <b>الأحد 29 نونبر 2026</b>" in text
    assert text.endswith("#استدعاء_الكتابي #الدار_البيضاء")
    assert keyboard(conv)["inline_keyboard"][0][0] == {
        "text": "📄 تحميل اللائحة", "url": "https://e/list.pdf"}
    res = conv.model_copy(update={"stage": CompetitionStage.RESULTATS, "city": "المغرب"})
    text = format_stage_post(res)
    assert text.startswith("🏆") and "تهانينا" in text and text.endswith("#نتائج")
    oral = conv.model_copy(update={"stage": CompetitionStage.CONVOQUES_ORAL})
    assert format_stage_post(oral).startswith("🎤")


def test_field_tags_use_whole_words():
    from app.matching.domains import field_tags
    nurse = _wadifa().model_copy(update={"grade": "ممرض من الدرجة الأولى", "specialty": None})
    assert field_tags(nurse) == ["صحة"]
    eighth = _wadifa().model_copy(update={"grade": "متصرف من الدرجة الثامنة", "specialty": None})
    assert field_tags(eighth) == ["إدارة"]  # 'امن' inside 'الثامنة' is not security
    guard = _emploi().model_copy(update={"grade": "Surveillant pénitentiaire", "specialty": None})
    assert field_tags(guard) == ["أمن"]


def test_sender_uploads_logo_then_falls_back_to_emblem(monkeypatch):
    from app.notify import channel as ch
    calls = []

    def fake_request(method, data, files=None):
        calls.append((method, files["photo"][0] if files else None))
        if method == "sendPhoto" and files["photo"][0].startswith("logo"):
            raise ch.TelegramError("sendPhoto", 400, "bad image")
        return {"ok": True, "result": {"message_id": 77}}

    monkeypatch.setattr(ch, "_request", fake_request)
    monkeypatch.setattr(ch, "fetch_image", lambda url: ("logo.png", b"x", "image/png"))
    assert ch.send_post(_wadifa(), "t", "@RaqibEmploi") == 77
    assert calls == [("sendPhoto", "logo.png"), ("sendPhoto", "morocco.png"),
                     ("editMessageReplyMarkup", None)]


def test_telegram_errors_never_contain_the_token(monkeypatch):
    from app.notify import channel as ch
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:SECRET")
    from app.config import get_settings
    get_settings.cache_clear()

    class Resp:
        status_code = 401
        def json(self):
            return {"ok": False, "description": "Unauthorized"}

    class Client:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def post(self, url, **k): return Resp()

    monkeypatch.setattr(ch.httpx, "Client", Client)
    try:
        ch._request("sendMessage", {})
    except ch.TelegramError as exc:
        assert "SECRET" not in str(exc) and "401" in str(exc)
    get_settings.cache_clear()


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
    monkeypatch.setenv("PUBLISH_IT_ONLY", "true")
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
    assert sent[0][0].startswith("🟢")

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
    assert "مباراة جديدة" in capsys.readouterr().out
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

def test_default_mode_posts_every_concours_and_tags_only_it(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@RaqibEmploi")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.delenv("PUBLISH_IT_ONLY", raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setattr("time.sleep", lambda s: None)
    nonit = _wadifa().model_copy(update={"specialty": "الطب العام", "grade": "طبيب",
                                         "reference_code": "C 1/26", "source_url": "https://w/2",
                                         "detail_url": "https://w/2"})
    expired = nonit.model_copy(update={"reference_code": "C 2/26", "source_url": "https://w/3",
                                       "detail_url": "https://w/3", "deadline": date(2020, 1, 1)})
    scrapers = [_FakeScraper("wadifapublic.ma", [_wadifa(), nonit, expired])]
    sent: list = []
    first = _run(tmp_path, scrapers, sent)
    assert first["posts"] == 2  # IT + non-IT, expired one skipped
    texts = [s[0] for s in sent]
    assert sum("#معلوميات" in x for x in texts) == 1
    assert _run(tmp_path, scrapers, sent)["posts"] == 0
    get_settings.cache_clear()


def test_convocation_and_result_items_are_not_announcements():
    from app.jobs.publish_channel import _is_announcement
    base = _wadifa()
    assert _is_announcement(base)
    for title in ("Liste des Convoqués Concours ONCF", "Résultats du concours X", "نتائج مباراة توظيف"):
        assert not _is_announcement(base.model_copy(update={"title": title}))


def test_stages_are_seeded_first_then_posted_as_replies(tmp_path, monkeypatch):
    from app.db.models import CompetitionStage, SourceType
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@RaqibEmploi")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setattr("time.sleep", lambda s: None)
    uuid = "11111111-2222-3333-4444-555555555555"
    ar = f"https://www.emploi-public.ma/ar/x/{uuid}"

    def item(stage, **kw):
        return RawAnnouncement(
            source_name="emploi-public.ma", source_type=SourceType.PORTAL, source_url=ar,
            detail_url=ar, official_url=ar, title="t", lang="ar", stage=stage,
            administration="وزارة الصحة", grade="ممرض", **kw)

    old_conv = item(CompetitionStage.CONVOQUES, exam_date=date(2099, 1, 1))
    other_uuid = "99999999-2222-3333-4444-555555555555"
    old_res = old_conv.model_copy(update={
        "stage": CompetitionStage.RESULTATS,
        "source_url": f"https://www.emploi-public.ma/ar/x/{other_uuid}"})
    scrapers = [_FakeScraper("emploi-public.ma", [old_conv, old_res])]
    sent: list = []
    first = _run(tmp_path, scrapers, sent)
    assert first["stage_posts"] == 0 and not sent  # first watch: recorded only

    # The announcement is posted later; then a new oral list for the same concours.
    state = PostedState(tmp_path / "s.json")
    state.add_posted(item(CompetitionStage.AVIS, deadline=date(2099, 1, 1)), 555)
    state.save()
    oral = item(CompetitionStage.CONVOQUES_ORAL)
    past = item(CompetitionStage.CONVOQUES, exam_date=date(2020, 1, 1)).model_copy(
        update={"source_url": "https://www.emploi-public.ma/ar/x/aaaaaaaa-2222-3333-4444-555555555555"})
    scrapers = [_FakeScraper("emploi-public.ma", [old_conv, old_res, oral, past])]
    second = _run(tmp_path, scrapers, sent)
    assert second["stage_posts"] == 1
    assert sent[0][0].startswith("🎤") and sent[0][1] == 555  # reply to the announcement
    assert _run(tmp_path, scrapers, sent)["stage_posts"] == 0  # never twice
    get_settings.cache_clear()


def test_a_refused_post_is_skipped_retried_then_dropped(tmp_path, monkeypatch):
    from app.notify.channel import TelegramError
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@RaqibEmploi")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setattr("time.sleep", lambda s: None)
    bad = _wadifa().model_copy(update={"reference_code": "C 2/26", "source_url": "https://w/2",
                                       "detail_url": "https://w/2", "post_count": 3,
                                       "administration": "Autre administration"})
    scrapers = [_FakeScraper("wadifapublic.ma", [_wadifa(), bad])]
    sent: list = []

    def sender(ann, text, channel, reply_to=None, with_button=True):
        if ann.reference_code == "C 2/26":
            raise TelegramError("sendPhoto", 400, "Bad Request: can't parse entities")
        sent.append(ann.reference_code)
        return 300 + len(sent)

    def go():
        return publish_channel.run(state_path=tmp_path / "s.json", scrapers=scrapers, sender=sender)

    first = go()
    assert first["posts"] == 1 and sent == ["C 44891/26"]  # the good post still went out
    assert "can't parse entities" in first["errors"][0]
    assert go()["posts"] == 0 and go()["posts"] == 0  # retried on the next runs
    assert "errors" not in go()  # dropped after three refusals, never tried again
    assert sent == ["C 44891/26"]

    def unauthorized(*a, **k):
        raise TelegramError("sendPhoto", 401, "Unauthorized")
    fresh = _wadifa().model_copy(update={"reference_code": "C 3/26", "source_url": "https://w/3",
                                         "detail_url": "https://w/3", "administration": "Troisième"})
    try:
        publish_channel.run(state_path=tmp_path / "s.json",
                            scrapers=[_FakeScraper("wadifapublic.ma", [fresh])], sender=unauthorized)
        raised = False
    except TelegramError:
        raised = True
    assert raised  # a bad token stops the run (red in GitHub)
    get_settings.cache_clear()
