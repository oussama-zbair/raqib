"""Automated PDF roll-call — the platform's most critical feature.

Given a convocation/results PDF and a set of candidates (CIN + optional name), this
downloads the PDF into memory, extracts text and tables with pdfplumber, and searches
for each candidate's CIN. On a hit it extracts the exam centre, room/amphi, seat number,
and exam date from the surrounding row/context.

Design notes:
- Works on digitally-generated PDFs (text layer present). Scanned image-only PDFs won't
  yield text; those are flagged so the caller can escalate to the Gemini vision fallback
  or notify the candidate that the list could not be parsed automatically.
- CIN matching is normalization-tolerant (case, spaces, dashes removed).
"""

from __future__ import annotations

import io
import re

import httpx
import pdfplumber

from app.config import get_settings
from app.db.models import RollCallHit, RollCallMiss
from app.matching.normalizer import normalize_text

# --- field label patterns (FR + AR) used to pull seat details from a row/context ---
# --- seat-detail extraction ---
# Convocation lists come in two shapes: labeled key/value text ("Salle: Amphi C") and
# positional columns ("... Amphi C  N° de table: 142"). We try direct value patterns
# first (robust to columnar layouts) and fall back to labeled forms.

# Salle/Amphi as a direct value, e.g. "Amphi C", "Salle 12", "قاعة 3".
# The value token must be a short room id (letters/digits), and must not be the start of
# another label like "N° de table", so a header cell "Salle  N°..." is not captured.
_SALLE_VALUE_RE = re.compile(
    r"((?:amphi(?:theatre)?|salle|قاعة|مدرج)\.?\s+"
    r"(?!n[°º])[A-Za-z0-9\u0600-\u06FF]{1,4})\b",
    re.IGNORECASE,
)
# Salle/Amphi as a labeled value, e.g. "Salle: Amphi C".
_SALLE_LABEL_RE = re.compile(
    r"(?:salle|amphi|amphitheatre|قاعة|مدرج)\s*[:\-]\s*([\w\-\s]+?)(?:\s{2,}|$)",
    re.IGNORECASE,
)
# Seat number: labeled form, number must directly follow ':' or '-' so a bare row index
# like a leading "1" is never mistaken for the seat number.
_TABLE_RE = re.compile(
    r"(?:n[°º]\s*de\s*table|n[°º]\s*table|table|رقم\s*الطاولة)\s*[:\-]\s*(\d+)",
    re.IGNORECASE,
)
# Centre: labeled ("Centre: ...") or a "Faculté/Ecole/Lycée ..." value.
_CENTRE_LABEL_RE = re.compile(
    r"(?:centre(?:\s+d['e]examen)?|مركز(?:\s+الامتحان)?)\s*[:\-]\s*(.+?)(?:\s{2,}|$)",
    re.IGNORECASE,
)
_CENTRE_VALUE_RE = re.compile(
    r"((?:facult[eé]|ecole|école|lyc[eé]e|universit[eé]|كلية|مدرسة|ثانوية)"
    r"[\w\s\u0600-\u06FF\-']+?)(?:\s{2,}|amphi|salle|n[°º]|$)",
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r"(?:date|le|بتاريخ|يوم)\s*[:\-]?\s*"
    r"(\d{1,2}[/\-\s]\w+[/\-\s]\d{2,4}(?:\s+a\s+\d{1,2}[:h]\d{2})?)",
    re.IGNORECASE,
)


def normalize_cin(cin: str) -> str:
    """Uppercase, strip spaces/dashes so 'ab-12 34 56' == 'AB123456'."""
    return re.sub(r"[\s\-]", "", cin).upper()


def download_pdf(url: str) -> bytes:
    settings = get_settings()
    with httpx.Client(
        headers={"User-Agent": settings.http_user_agent},
        timeout=settings.request_timeout_seconds,
        follow_redirects=True,
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def _extract_lines(pdf_bytes: bytes) -> list[str]:
    """Return all text lines from the PDF (text + flattened table rows)."""
    lines: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.splitlines())
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [c for c in row if c]
                    if cells:
                        lines.append("  ".join(str(c) for c in cells))
    return lines


def _extract_seat_details(context: str) -> dict[str, str | None]:
    def _first(pattern: re.Pattern[str]) -> str | None:
        m = pattern.search(context)
        return m.group(1).strip() if m else None

    # Salle: prefer the direct value ("Amphi C"), fall back to the labeled form.
    salle = _first(_SALLE_VALUE_RE) or _first(_SALLE_LABEL_RE)
    # Centre: prefer the labeled form, fall back to a "Faculté ..." value.
    centre = _first(_CENTRE_LABEL_RE) or _first(_CENTRE_VALUE_RE)
    return {
        "centre": centre,
        "salle": salle,
        "table": _first(_TABLE_RE),
        "exam_date": _first(_DATE_RE),
    }


def _name_tokens(name: str | None) -> list[str]:
    """Normalized, order-independent tokens of a name (FR or AR).

    Uses the shared bilingual normalizer (strips FR accents + AR diacritics, unifies
    alef/ya variants, lowercases). Short tokens (<2 chars) are dropped to avoid noise.
    """
    if not name:
        return []
    return [tok for tok in normalize_text(name).split() if len(tok) >= 2]


def _name_in_line(tokens: list[str], line_norm: str) -> bool:
    """A name matches a line if ALL its significant tokens appear in that line.

    Order-independent (handles "Nom Prénom" vs "Prénom Nom") and tolerant of extra
    columns. Requires at least 2 tokens so a single common first name can't false-match.
    """
    if len(tokens) < 2:
        return False
    return all(tok in line_norm for tok in tokens)


def inspect_lines(
    lines: list[str],
    candidates: list[dict[str, str]],
    pdf_url: str | None = None,
) -> list[RollCallHit | RollCallMiss]:
    """Core matcher over already-extracted lines (unit-testable, no I/O).

    Each candidate is ``{"cin", "full_name_fr"?, "full_name_ar"?, "full_name"?}``.
    A candidate matches a line by **CIN OR full name (FR or AR)** — many administrations
    publish convocation lists by name, sometimes without the CIN, and in either language.
    """
    results: list[RollCallHit | RollCallMiss] = []
    # Precompute normalized copies of each line: one for CIN (digits/letters only) and
    # one for name matching (bilingual normalized text).
    norm = [(ln, normalize_cin(ln), normalize_text(ln)) for ln in lines]

    for cand in candidates:
        cin = cand.get("cin", "")
        cin_n = normalize_cin(cin) if cin else ""
        name_fr = cand.get("full_name_fr") or cand.get("full_name")
        name_ar = cand.get("full_name_ar")
        tokens_fr = _name_tokens(name_fr)
        tokens_ar = _name_tokens(name_ar)

        hit_line: str | None = None
        idx = -1
        matched_by: str | None = None
        for i, (raw, cin_line, text_line) in enumerate(norm):
            if cin_n and len(cin_n) >= 5 and cin_n in cin_line:
                hit_line, idx, matched_by = raw, i, "cin"
                break
            if _name_in_line(tokens_fr, text_line):
                hit_line, idx, matched_by = raw, i, "name_fr"
                break
            if _name_in_line(tokens_ar, text_line):
                hit_line, idx, matched_by = raw, i, "name_ar"
                break

        if hit_line is None:
            results.append(RollCallMiss(cin=cin, pdf_url=pdf_url))
            continue

        lo = max(0, idx - 1)
        hi = min(len(lines), idx + 2)
        context = "  ".join(lines[lo:hi])
        details = _extract_seat_details(context)
        results.append(
            RollCallHit(
                cin=cin,
                full_name=name_fr or name_ar,
                centre=details["centre"],
                salle=details["salle"],
                table=details["table"],
                exam_date=details["exam_date"],
                pdf_url=pdf_url,
                matched_by=matched_by,
            )
        )
    return results


def inspect_pdf(
    pdf_url: str, candidates: list[dict[str, str]]
) -> list[RollCallHit | RollCallMiss]:
    """Download a PDF and roll-call the given candidates.

    Returns a hit (with seat details) or miss per candidate. If the PDF yields no text
    (likely a scanned image), every candidate is returned as a miss — the caller should
    then escalate to the Gemini vision fallback or notify accordingly.
    """
    pdf_bytes = download_pdf(pdf_url)
    lines = _extract_lines(pdf_bytes)
    return inspect_lines(lines, candidates, pdf_url=pdf_url)


def pdf_has_text(pdf_bytes: bytes) -> bool:
    """True if the PDF has an extractable text layer (vs a scanned image)."""
    return any(line.strip() for line in _extract_lines(pdf_bytes))
