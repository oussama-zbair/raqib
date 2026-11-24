"""Offline test of the dreamjob.ma RSS parser, run against a saved real feed."""
from __future__ import annotations

from pathlib import Path

from app.db.models import CompetitionStage
from app.scrapers.dreamjob_ma import parse_feed_xml

FEED = Path(__file__).parent / "fixtures" / "dreamjob" / "feed.xml"


def test_feed_keeps_public_sector_only():
    rows = parse_feed_xml(FEED.read_bytes())
    assert len(rows) == 8
    assert all("/emploi-public/" in r.source_url for r in rows)
    avis = [r for r in rows if r.stage == CompetitionStage.AVIS]
    assert len(avis) == 5
    assert {r.stage for r in rows} == {
        CompetitionStage.AVIS,
        CompetitionStage.CONVOQUES,
        CompetitionStage.RESULTATS,
    }


def test_feed_item_fields():
    rows = parse_feed_xml(FEED.read_bytes())
    tanger = next(r for r in rows if "tanger-region-sport" in r.source_url)
    assert tanger.post_count == 6
    assert tanger.administration == "Tanger Région Sport"
    assert tanger.logo_url.endswith("tanger-region-sport.jpg")
    assert "techniciens" in tanger.text
    assert "est apparu en premier" not in tanger.text
