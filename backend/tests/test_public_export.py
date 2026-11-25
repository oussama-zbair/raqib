"""state/public.json: what the website shows, and what it must never show."""
from __future__ import annotations

from datetime import date, timedelta

from app.db.models import CompetitionStage as S
from app.db.models import RawAnnouncement, SourceType
from app.jobs import public_export
from app.jobs.posted_state import PostedState

UUID = "cccccccc-1111-2222-3333-444444444444"
URL = f"https://www.emploi-public.ma/ar/x/{UUID}"


def _ann(stage=S.AVIS, **kw):
    kw.setdefault("deadline", date.today() + timedelta(days=10))
    return RawAnnouncement(
        source_name="emploi-public.ma", source_type=SourceType.PORTAL, source_url=URL,
        detail_url=URL, official_url=URL, title="t", lang="ar", stage=stage,
        administration="وزارة الصحة", grade="ممرض من الدرجة الأولى", specialty="الممرضين",
        city="الرباط", logo_url="https://e/logo.png", **kw)


def test_export_lists_open_concours_with_their_timeline(tmp_path):
    state = PostedState(tmp_path / "s.json")
    state.add_posted(_ann(), 123)
    state.add_stage(_ann(S.CONVOQUES, list_pdf_url="https://e/list.pdf"), 124)
    old = _ann(deadline=date.today() - timedelta(days=90)).model_copy(
        update={"source_url": "https://www.emploi-public.ma/ar/x/dddddddd-1111-2222-3333-444444444444"})
    state.add_posted(old, 125)
    out = public_export.build(state, {"finished_at": "2026-11-25T18:00:00+00:00",
                                      "sources": {"emploi-public.ma": "ok (10 items)"}})
    assert [c["id"] for c in out["concours"]] == [f"ep:{UUID}"]  # long-closed one dropped
    c = out["concours"][0]
    assert c["stages"] == ["AVIS", "CONVOQUES"]
    assert c["tags"] == ["صحة"] and c["city"] == "الرباط" and c["url"] == URL
    assert out["updates"][0]["pdf"] == "https://e/list.pdf"
    assert out["stats"]["open"] == 1
    assert out["sources"][0]["status"].startswith("ok")
    text = str(out)
    assert "telegram_message_id" not in text and "123" not in text  # no internal ids
