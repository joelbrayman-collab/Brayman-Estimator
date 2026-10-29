"""The approved consent wording in the register and in the code stay identical (Joel approved
CONSENT-SUPPLIER-V1-001 exactly as written, 29 Oct 2026). A wording change needs a new version and a new approval."""

import re
from pathlib import Path

from app.services.supplier_signing import CONSENT_SUPPLIER_V1_BODY, CONSENT_SUPPLIER_V1_CODE

REGISTER = Path(__file__).resolve().parents[1] / "docs" / "governance" / "signing-consent-register.md"


def test_the_approved_supplier_consent_is_the_wording_in_the_code():
    text = REGISTER.read_text(encoding="utf-8")
    section = text.split(f"## {CONSENT_SUPPLIER_V1_CODE} — APPROVED — 29 OCTOBER 2026", 1)[1]
    quoted = " ".join(line[2:].strip() for line in section.splitlines() if line.startswith("> "))
    assert re.sub(r"\s+", " ", quoted).strip() == CONSENT_SUPPLIER_V1_BODY
    assert f"| `{CONSENT_SUPPLIER_V1_CODE}` | PRODUCTION |" in text and "**APPROVED — 29 OCTOBER 2026" in text
