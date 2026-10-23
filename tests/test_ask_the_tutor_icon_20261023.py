"""Ask the Tutor identity (23 Oct 2026): the approved master recoloured for CalibraytAI, used in the Training Tutor header.

The icons keep the master's circle with transparency outside it, are square, and are recorded in the asset inventory.
The Tutor's behaviour (minimize, ask, CSRF forms, data hooks) is unchanged by the icon."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-192.png": "4a5e77d92a1a3498bd7fa0ba61340b3298f2299aac44bac988cfbd8ecbb1ded9",
    "app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-48.png": "6e217b8b328823d6666329e3dff526a0ec733e4f7705f80a1941c0290ae3b957",
    "app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-512.png": "acd8c03d21be6bc2eedc9f5e463e2fdbc5b9f82f63d79beaaa5bcd25a7568776",
    "app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai-96.png": "fb898b27be4990521614a0cd9db94ade15237d22470b645a231c4d14893dde74",
    "app/static/branding/ask_the_tutor/ask-the-tutor-calibraytai.png": "08cc6c64e889bcd1b42374ec552e2d388ffa9c00a4febc19cd327688bba401f0",
}
INVENTORY = (ROOT / "docs" / "branding" / "approved-asset-inventory.md").read_text()
TEMPLATE = (ROOT / "app" / "templates" / "training" / "_tutor.html").read_text()
CSS = (ROOT / "app" / "static" / "training" / "training.css").read_text()


def test_icons_match_the_recorded_checksums_and_are_listed_in_the_inventory():
    for relative, expected in FILES.items():
        data = (ROOT / relative).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, relative
        assert relative in INVENTORY and expected in INVENTORY, relative


def test_icons_are_square_rgba_with_a_transparent_outside():
    for relative in FILES:
        image = Image.open(ROOT / relative)
        assert image.mode == "RGBA" and image.width == image.height, relative
        last = image.width - 1
        for corner in ((0, 0), (last, 0), (0, last), (last, last)):
            assert image.getpixel(corner)[3] == 0, (relative, corner)
        assert image.getpixel((image.width // 2, image.height // 2))[3] == 255, relative


def test_the_tutor_header_uses_the_icon_without_changing_the_tutor():
    assert "branding/ask_the_tutor/ask-the-tutor-calibraytai-96.png" in TEMPLATE
    assert "branding/ask_the_tutor/ask-the-tutor-calibraytai-192.png" in TEMPLATE
    assert 'alt=""' in TEMPLATE and "<strong>Training Tutor</strong>" in TEMPLATE
    # Behaviour hooks the page script and the server rely on are all still there.
    for hook in ('data-tutor', 'data-tutor-toggle', 'data-tutor-button', 'data-tutor-ask', 'name="csrf_token"',
                 "url_for('training.tutor_state')", "url_for('training.tutor_ask')", 'aria-label="Training Tutor"'):
        assert hook in TEMPLATE, hook
    assert "object-fit:contain" in CSS.replace(" ", "") and ".tc-tutor-icon" in CSS
