"""Tests for the ingestion pipeline (normalize + dedup)."""

from __future__ import annotations

from app.db.models import CompetitionStage, RawAnnouncement, SourceType
from app.jobs.pipeline import dedup_batch, raw_to_competition


def _raw(**kw) -> RawAnnouncement:
    base = dict(
        source_name="emploi-public.ma",
        source_type=SourceType.PORTAL,
        source_url="https://x/1",
        title="Avis Ingénieur d'État Échelle 11 - Génie Logiciel - Ministère de la Justice",
        text="Délai 12/10/2026",
        lang="fr",
        stage=CompetitionStage.AVIS,
    )
    base.update(kw)
    return RawAnnouncement(**base)


def test_raw_to_competition_infers_level_family():
    comp = raw_to_competition(_raw())
    # grade column = LEVEL key, specialty column = FAMILY key
    assert comp.grade == "master_ingenieur"
    assert comp.specialty == "informatique"
    assert comp.canonical_hash


def test_dedup_merges_same_canonical_and_clears_early_signal():
    # Same competition: one from an aggregator (early signal), one from the portal.
    portal = raw_to_competition(_raw())
    aggregator = raw_to_competition(
        _raw(
            source_name="Alwadifa-Maroc",
            source_type=SourceType.AGGREGATOR,
            source_url="https://y/2",
        )
    )
    assert aggregator.early_signal is True

    merged = dedup_batch([aggregator, portal])
    assert len(merged) == 1
    # Official portal presence clears the early signal.
    assert merged[0].early_signal is False
    # Both source URLs retained.
    assert len(merged[0].source_urls) == 2


def test_dedup_prefers_more_advanced_stage():
    avis = raw_to_competition(_raw(stage=CompetitionStage.AVIS))
    conv = raw_to_competition(
        _raw(stage=CompetitionStage.CONVOQUES, pdf_urls=["https://x/list.pdf"])
    )
    merged = dedup_batch([avis, conv])
    assert len(merged) == 1
    assert merged[0].stage == CompetitionStage.CONVOQUES
    assert merged[0].convocation_pdf_url == "https://x/list.pdf"
