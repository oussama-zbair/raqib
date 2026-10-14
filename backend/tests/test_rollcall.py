"""Tests for the PDF roll-call matcher (over extracted lines, no network)."""

from __future__ import annotations

from app.db.models import RollCallHit, RollCallMiss
from app.pdf.rollcall import inspect_lines, normalize_cin

# Simulated lines as pdfplumber would extract them from a convocation list.
LINES = [
    "Liste des candidats convoqués à l'épreuve écrite",
    "Ministère de l'Inclusion Économique - Ingénieur d'État 1er Grade (Génie Logiciel)",
    "Date: Dimanche 12 Octobre 2026 a 08:00",
    "N°  Nom et Prénom  CIN  Centre  Salle  N° de table",
    "1  Amine Bennani  AB123456  Faculté Souissi Rabat  Amphi C  N° de table: 142",
    "2  Sara Alaoui  CD654321  Faculté Souissi Rabat  Amphi B  N° de table: 77",
]


def test_normalize_cin_tolerant():
    assert normalize_cin("ab-12 34 56") == "AB123456"


def test_rollcall_hit_extracts_seat():
    results = inspect_lines(
        LINES,
        [{"cin": "AB123456", "full_name": "Amine Bennani"}],
        pdf_url="http://x/list.pdf",
    )
    assert len(results) == 1
    hit = results[0]
    assert isinstance(hit, RollCallHit)
    assert hit.found is True
    assert hit.table == "142"
    assert hit.salle and "Amphi C" in hit.salle
    assert hit.centre and "Souissi" in hit.centre
    assert hit.pdf_url == "http://x/list.pdf"


def test_rollcall_miss():
    results = inspect_lines(LINES, [{"cin": "ZZ999999"}])
    assert len(results) == 1
    assert isinstance(results[0], RollCallMiss)
    assert results[0].found is False


def test_rollcall_multiple_candidates():
    results = inspect_lines(
        LINES,
        [{"cin": "AB123456"}, {"cin": "ZZ000000"}, {"cin": "CD654321"}],
    )
    found = [r for r in results if r.found]
    missed = [r for r in results if not r.found]
    assert len(found) == 2
    assert len(missed) == 1
