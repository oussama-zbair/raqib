"""Home page signal, documents on concours pages, and following concours over time."""
from __future__ import annotations

import json
from pathlib import Path

from app.db.models import CompetitionStage as S
from app.db.models import RawAnnouncement, SourceType
from app.jobs import publish_channel
from app.jobs.posted_state import PostedState
from app.scrapers.emploi_public import ann_from_detail, parse_home_latest, stages_on_detail

FIX = Path(__file__).parent / "fixtures" / "emploi_public"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_home_page_cards_carry_their_stage():
    items = parse_home_latest(_read("ar_home.html"))
    assert items, "the home page lists the latest updates"
    assert {i.stage for i in items} <= set(S)
    assert all(i.administration and i.source_url for i in items)


def test_documents_on_a_concours_page():
    assert stages_on_detail(_read("ar_detail_avis.html")) == set()
    assert stages_on_detail(_read("ar_detail_convocation.html")) == {S.CONVOQUES}
    assert stages_on_detail(_read("ar_detail_oral.html")) == {S.CONVOQUES, S.CONVOQUES_ORAL}
    assert stages_on_detail(_read("ar_detail_resultat.html")) == {S.CONVOQUES, S.RESULTATS}


def test_post_built_from_the_page_alone():
    url = "https://www.emploi-public.ma/ar/x/0ce1c9ce-1d0d-4ee0-a8cb-5b05f5d4e640"
    ann = ann_from_detail(_read("ar_detail_convocation.html"), url, S.CONVOQUES)
    assert ann.administration == "وزارة الداخلية -عمالة إقليم طاطا-"
    assert ann.reference_code == "C 44579/26"
    assert ann.logo_url is None  # the portal's placeholder: the channel uses the emblem
    assert ann.city == "طاطا"
    assert ann.list_pdf_url.endswith("list_convoques/0ce1c9ce-1d0d-4ee0-a8cb-5b05f5d4e640")
    res = ann_from_detail(_read("ar_detail_resultat.html"), url, S.RESULTATS)
    assert res.logo_url and "/images/administrations/" in res.logo_url


class _PortalFake:
    """Listings return nothing new; concours pages come from saved real pages."""

    source_name = "emploi-public.ma"

    def __init__(self, pages: dict[str, str]):
        self.pages = pages

    def fetch(self):
        return []

    def detail_html(self, url, client):
        return next((html for uuid, html in self.pages.items() if uuid in url), None)

    def enrich(self, ann, client=None):
        return ann


def _env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@RaqibEmploi")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setattr("time.sleep", lambda s: None)


def test_followed_concours_posts_new_documents_and_seeds_old_ones(tmp_path, monkeypatch):
    _env(monkeypatch)
    fresh, old = "aaaaaaaa-1111-2222-3333-444444444444", "bbbbbbbb-1111-2222-3333-444444444444"
    path = tmp_path / "s.json"
    state = PostedState(path)
    # A fresh announcement we posted (baseline: no document yet) and an older concours.
    state.posted.append({"id": "x", "reference_code": None, "urls": [
        f"https://www.emploi-public.ma/ar/x/{fresh}"], "telegram_message_id": 700})
    state.track(f"ep:{fresh}", baseline_known=True)
    state.track(f"ep:{old}", baseline_known=False)
    for key in state.tracked:
        if state.tracked[key]["checked"]:
            state.tracked[key]["checked"] = "2000-01-01T00:00:00+00:00"  # due now
    state.last_discovery = "9999-12-31"
    state.save()

    pages = {fresh: _read("ar_detail_oral.html"), old: _read("ar_detail_resultat.html")}
    sent: list = []

    def sender(ann, text, channel, reply_to=None, with_button=True):
        sent.append((ann.stage, reply_to))
        return 900 + len(sent)

    res = publish_channel.run(state_path=path, scrapers=[_PortalFake(pages)], sender=sender)
    # The fresh concours gained a written and an oral list: both posted, as replies.
    assert sorted(s for s, _ in sent) == sorted([S.CONVOQUES, S.CONVOQUES_ORAL])
    assert sent[0][1] == 700 and sent[1][1] == 901  # the oral list replies to the written one
    # The older concours was read for the first time: its documents are only recorded.
    saved = json.loads(path.read_text(encoding="utf-8"))
    old_stages = [s for s in saved["stages"] if old in s["key"]]
    assert old_stages and all(s.get("seeded") for s in old_stages)
    assert res["stage_posts"] == 2
    # Nothing is due again within two hours, and nothing is posted twice.
    assert publish_channel.run(state_path=path, scrapers=[_PortalFake(pages)],
                               sender=sender)["stage_posts"] == 0
