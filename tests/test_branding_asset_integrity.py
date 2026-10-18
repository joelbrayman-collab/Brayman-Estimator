"""Approved branding assets are byte-for-byte the recorded masters (technical cleanup, 18 Oct 2026).

Checksums come from docs/branding/approved-asset-inventory.md. A change to any of these files must
be an approved replacement recorded there first; nothing here may be regenerated, recoloured or cropped.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPROVED = {
    # Cal — approved assistant identity (frozen master) and its two recorded derivatives.
    "app/static/branding/Cal_Assistant_Approved_Identity_2026-10-17.png": "d8857f1bfef06c709390e8eaedfe437aea49983236c79843ee7845d561617e87",
    "app/static/img/cal-assistant/cal-64.png": "0b10a30a284877f117fd933f8126cf68155d89591f90117b6db4b2043f92ef3d",
    "app/static/img/cal-assistant/cal-128.png": "b524454d8d3defe55d7b24728fe41ed45c5ab3121d7a5f1a63ef8e94505ad4bf",
    # CalibraytAI logos: members V1 LOGO and V2 LOGO of the approved CalibraytAI_090926_Final.zip.
    "app/static/branding/calibraytai-logo-v1-dark.png": "86a4d964cb31aa4e4fbd6360d29f77ce82dc5b8d9d5df7319b3f962f427661de",
    "docs/branding/calibraytai-opening-v1/storyboard/approved-logo-v1-dark-reference.png": "86a4d964cb31aa4e4fbd6360d29f77ce82dc5b8d9d5df7319b3f962f427661de",
    "app/static/branding/calibraytai-logo-v2.png": "b719bdd2fe7814d49d1a4065c4d6b1915f8e3cd6696f711c08e8d49b3fa53aea",
    # Installable-app icons (15 Oct 2026, from the approved gold symbol); first checksummed 18 Oct 2026.
    "app/static/branding/calibraytai-app-icon-32.png": "a1a78d21023044294fb1d21566a7d921ab5acfa7b090dbb94afaf48a04477c4a",
    "app/static/branding/calibraytai-app-icon-180.png": "4fe82fe5a6f1cce3aecd2cef8ce2c151a291ceaf1928bd562f31dbe7db153417",
    "app/static/branding/calibraytai-app-icon-192.png": "6a97220ea2a8bd4f9d6d8733b0dbb5deb24ba437c94d02d49f76d51729becbb8",
    "app/static/branding/calibraytai-app-icon-512.png": "d98dd1f6d279c13a850de726e5c3043b2a56a9424a596629c2075e039b68794e",
    "app/static/branding/calibraytai-app-icon-maskable-512.png": "2bedbfa356e82d89013d863e69e6ce7e37c19316802c302c177e89ea8b54fbb1",
    # Brayman Construction company logo (organization brand profile); first checksummed 18 Oct 2026.
    "app/static/branding/brayman-construction-logo.png": "948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9",
}


def test_every_approved_asset_matches_its_recorded_checksum():
    mismatched = {}
    for relative, expected in APPROVED.items():
        path = ROOT / relative
        assert path.is_file(), f"approved asset missing: {relative}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            mismatched[relative] = actual
    assert mismatched == {}


def test_the_inventory_records_every_checksum():
    inventory = (ROOT / "docs" / "branding" / "approved-asset-inventory.md").read_text()
    for relative, expected in APPROVED.items():
        assert relative in inventory, relative
        assert expected in inventory, relative


def test_no_unrecorded_image_in_the_branding_folder():
    folder = ROOT / "app" / "static" / "branding"
    present = {f"app/static/branding/{p.name}" for p in folder.iterdir() if p.is_file()}
    assert present - set(APPROVED) == set()
