"""Tests for Gemini response parsing (no network / no model call)."""

from __future__ import annotations

from datetime import date

from app.extractors.gemini import build_fields, parse_model_json

FENCED = """Here is the data:
```json
{
  "administration": "Ministère de la Justice",
  "grade": "Ingénieur d'État 1er grade",
  "specialty": "Génie Logiciel",
  "required_degree": "Diplôme d'ingénieur",
  "deadline": "12/10/2026",
  "post_count": 5,
  "submission_link": "https://example.ma/apply"
}
```
"""

BARE = '{"administration":"OCP","post_count":"3","deadline":null}'


def test_parse_fenced_json():
    data = parse_model_json(FENCED)
    assert data["administration"] == "Ministère de la Justice"
    fields = build_fields(data)
    assert fields.post_count == 5
    assert fields.deadline == date(2026, 10, 12)
    assert fields.specialty == "Génie Logiciel"


def test_parse_bare_json_and_coercion():
    data = parse_model_json(BARE)
    fields = build_fields(data)
    assert fields.administration == "OCP"
    assert fields.post_count == 3  # coerced from string
    assert fields.deadline is None


def test_parse_garbage_returns_empty():
    assert parse_model_json("no json here") == {}
