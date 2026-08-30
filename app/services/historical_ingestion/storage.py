"""Private filesystem storage for productized historical workbooks (ADR-032 / FG-013)."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from flask import current_app

_ORG_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,50}$")
_SHA_RE = re.compile(r"^[a-f0-9]{64}$")
ALLOWED_STORED_EXTENSIONS = {".xlsx", ".xlsm"}


def get_historical_upload_root() -> Path:
    root = current_app.config.get("HISTORICAL_UPLOAD_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "historical_uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_org_segment(organization_id: str) -> str:
    if not organization_id or not _ORG_SEGMENT_RE.fullmatch(organization_id):
        raise ValueError("Invalid organization id for historical upload storage.")
    return organization_id


def organization_upload_dir(organization_id: str) -> Path:
    path = get_historical_upload_root() / _safe_org_segment(organization_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def controlled_stored_name(sha256: str, extension: str) -> str:
    ext = (extension or "").lower()
    if ext not in ALLOWED_STORED_EXTENSIONS:
        raise ValueError("Invalid stored extension.")
    digest = (sha256 or "").lower()
    if not _SHA_RE.fullmatch(digest):
        raise ValueError("Invalid SHA-256 for stored filename.")
    return f"{digest}{ext}"


def stored_relative_path(organization_id: str, sha256: str, extension: str) -> str:
    org = _safe_org_segment(organization_id)
    name = controlled_stored_name(sha256, extension)
    return f"{org}/{name}"


def absolute_stored_path(relative_path: str) -> Path:
    """Resolve a controlled relative path under the upload root (no traversal)."""
    if not relative_path or relative_path != os.path.normpath(relative_path):
        raise ValueError("Invalid stored relative path.")
    parts = relative_path.split("/")
    if len(parts) != 2 or ".." in parts or "\\" in relative_path:
        raise ValueError("Invalid stored relative path.")
    org, name = parts
    _safe_org_segment(org)
    ext = os.path.splitext(name)[1].lower()
    digest = os.path.splitext(name)[0].lower()
    if name != controlled_stored_name(digest, ext):
        raise ValueError("Invalid stored filename.")
    path = (get_historical_upload_root() / org / name).resolve()
    root = get_historical_upload_root().resolve()
    if root not in path.parents:
        raise ValueError("Stored path escapes upload root.")
    return path


def store_immutable_bytes(organization_id: str, sha256: str, extension: str, data: bytes) -> str:
    """Write bytes once under a SHA-named path. Never overwrite existing content."""
    rel = stored_relative_path(organization_id, sha256, extension)
    dest = absolute_stored_path(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        existing = dest.read_bytes()
        import hashlib

        existing_sha = hashlib.sha256(existing).hexdigest()
        if existing_sha != sha256.lower():
            raise ValueError("Refusing to overwrite stored historical workbook bytes.")
        return rel

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
    return rel
