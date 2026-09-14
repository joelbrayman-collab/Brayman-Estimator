"""Governed Family 05 presentation-master identity and read-only verification.

Never writes to the master path. Always returns a copy of the bytes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from flask import current_app

FAMILY_05_FAMILY_CODE = "05"
FAMILY_05_MASTER_VERSION = "V1"
FAMILY_05_MASTER_FILENAME = (
    "05_Brayman_Ontario_Construction_Contract_COMMERCIAL_DRAFT_MASTER_V1.docx"
)
FAMILY_05_MASTER_SHA256 = (
    "24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5"
)
FAMILY_05_LEGAL_STATUS = "COMMERCIAL_DRAFT"
FAMILY_05_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
DEFAULT_FAMILY_05_MASTER_PATH = Path(
    "/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/"
    "Reusable Master Template Family V1/MASTER DOCX/"
    "05_Brayman_Ontario_Construction_Contract_COMMERCIAL_DRAFT_MASTER_V1.docx"
)

BLOCK_MISSING_PRESENTATION_MASTER = "MISSING_PRESENTATION_MASTER"
BLOCK_PRESENTATION_MASTER_SHA_MISMATCH = "PRESENTATION_MASTER_SHA_MISMATCH"


class Family05MasterError(ValueError):
    def __init__(self, block_code: str, message: str = ""):
        super().__init__(message or block_code)
        self.block_code = block_code


def governed_presentation_master() -> dict:
    return {
        "family_code": FAMILY_05_FAMILY_CODE,
        "version": FAMILY_05_MASTER_VERSION,
        "filename": FAMILY_05_MASTER_FILENAME,
        "sha256": FAMILY_05_MASTER_SHA256,
        "legal_status": FAMILY_05_LEGAL_STATUS,
    }


def family_05_master_path() -> Path:
    try:
        configured = current_app.config.get("FAMILY_05_MASTER_PATH")
    except RuntimeError:
        configured = None
    if configured:
        return Path(configured)
    return DEFAULT_FAMILY_05_MASTER_PATH


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_family_05_master_copy(*, expected_sha256: Optional[str] = None) -> bytes:
    """Read the governed master as a byte copy. Never opens the path for write."""
    path = family_05_master_path()
    if not path.is_file():
        raise Family05MasterError(
            BLOCK_MISSING_PRESENTATION_MASTER,
            "Family 05 presentation master is not available.",
        )
    data = path.read_bytes()
    digest = sha256_bytes(data)
    if digest != FAMILY_05_MASTER_SHA256:
        raise Family05MasterError(
            BLOCK_PRESENTATION_MASTER_SHA_MISMATCH,
            "Family 05 master SHA-256 does not match governed authority.",
        )
    expected = (expected_sha256 or "").strip().lower()
    if expected and expected != digest:
        raise Family05MasterError(
            BLOCK_PRESENTATION_MASTER_SHA_MISMATCH,
            "Presentation master SHA-256 does not match the governed file.",
        )
    return data
