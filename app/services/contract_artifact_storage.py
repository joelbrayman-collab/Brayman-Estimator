"""Private instance custody for generated Family 05 DOCX artifacts.

Exact bytes retained. SHA-256 filenames. Never overwrite mismatched bytes.
Retrieval reads retained bytes; it does not re-render.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

from flask import current_app

_ORG_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,50}$")
_SHA_RE = re.compile(r"^[a-f0-9]{64}$")
DOCX_EXTENSION = ".docx"


class ContractArtifactStorageError(ValueError):
    """Raised when generated-contract artifact bytes or a path cannot be accepted."""


def get_contract_artifact_root() -> Path:
    root = current_app.config.get("CONTRACT_ARTIFACT_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "generated_contracts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_org_segment(organization_id: str) -> str:
    if not organization_id or not _ORG_SEGMENT_RE.fullmatch(organization_id):
        raise ContractArtifactStorageError(
            "Invalid organization id for contract artifact storage."
        )
    return organization_id


def controlled_stored_name(sha256: str) -> str:
    digest = (sha256 or "").lower()
    if not _SHA_RE.fullmatch(digest):
        raise ContractArtifactStorageError("Invalid SHA-256 for stored artifact filename.")
    return f"{digest}{DOCX_EXTENSION}"


def stored_relative_path(organization_id: str, sha256: str) -> str:
    org = _safe_org_segment(organization_id)
    return f"{org}/{controlled_stored_name(sha256)}"


def absolute_stored_path(relative_path: str) -> Path:
    if not relative_path or relative_path != os.path.normpath(relative_path):
        raise ContractArtifactStorageError("Invalid stored relative path.")
    if relative_path.startswith("/") or "\\" in relative_path:
        raise ContractArtifactStorageError("Invalid stored relative path.")
    parts = relative_path.split("/")
    if len(parts) != 2 or ".." in parts:
        raise ContractArtifactStorageError("Invalid stored relative path.")
    org, name = parts
    _safe_org_segment(org)
    digest = os.path.splitext(name)[0].lower()
    if name != controlled_stored_name(digest):
        raise ContractArtifactStorageError("Invalid stored artifact filename.")
    path = (get_contract_artifact_root() / org / name).resolve()
    root = get_contract_artifact_root().resolve()
    if root not in path.parents:
        raise ContractArtifactStorageError("Stored path escapes contract artifact root.")
    return path


def store_immutable_docx(organization_id: str, data: bytes) -> tuple[str, str]:
    """Write merged DOCX bytes once. Returns (relative_key, sha256)."""
    if not data:
        raise ContractArtifactStorageError("Generated contract artifact is empty.")
    digest = sha256_hex(data)
    rel = stored_relative_path(organization_id, digest)
    dest = absolute_stored_path(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        existing = dest.read_bytes()
        if sha256_hex(existing) != digest:
            raise ContractArtifactStorageError(
                "Refusing to overwrite stored generated-contract artifact bytes."
            )
        return rel, digest

    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(dest.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, dest)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    return rel, digest


def read_retained_docx(relative_path: str) -> bytes:
    path = absolute_stored_path(relative_path)
    if not path.is_file():
        raise ContractArtifactStorageError("Generated contract artifact is not retained.")
    return path.read_bytes()
