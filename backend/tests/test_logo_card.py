"""Card images: small portal logos are placed on a 16:9 card instead of being stretched."""
from __future__ import annotations

import io

from PIL import Image

from app.notify.channel import CARD_SIZE, MAX_UPSCALE, logo_card


def _png(w, h, mode="RGBA", color=(200, 30, 30, 255)):
    out = io.BytesIO()
    Image.new(mode, (w, h), color if mode == "RGBA" else color[:3]).save(out, format="PNG")
    return out.getvalue()


def _bbox(card_bytes):
    card = Image.open(io.BytesIO(card_bytes)).convert("RGB")
    top = card.crop((0, 0, CARD_SIZE[0], CARD_SIZE[1] - 30))  # without the band
    return card.size, Image.eval(top, lambda v: 255 - v).getbbox()


def test_small_logo_is_enlarged_at_most_three_times_and_centred():
    size, box = _bbox(logo_card(_png(98, 85)))
    assert size == CARD_SIZE
    width, height = box[2] - box[0], box[3] - box[1]
    assert abs(width - 98 * MAX_UPSCALE) <= 2 and abs(height - 85 * MAX_UPSCALE) <= 2
    assert abs((box[0] + box[2]) / 2 - CARD_SIZE[0] / 2) <= 2


def test_large_logo_is_shrunk_into_the_card():
    size, box = _bbox(logo_card(_png(1418, 1298)))
    assert size == CARD_SIZE and box[3] - box[1] <= CARD_SIZE[1] * 0.6


def test_transparent_and_jpeg_logos_work_and_garbage_is_refused():
    assert logo_card(_png(120, 85, color=(0, 0, 0, 0)))
    jpg = io.BytesIO()
    Image.new("RGB", (85, 85), (10, 100, 10)).save(jpg, format="JPEG")
    assert logo_card(jpg.getvalue())
    assert logo_card(b"not an image") is None
