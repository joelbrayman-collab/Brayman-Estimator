"""Private instance custody for Native Signing frozen artifacts.

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
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class SigningArtifactStorageError(ValueError):
    """Raised when signing artifact bytes or a path cannot be accepted."""


def get_signing_artifact_root() -> Path:
    root = current_app.config.get("SIGNING_ARTIFACT_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "signing_artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_org_segment(organization_id: str) -> str:
    if not organization_id or not _ORG_SEGMENT_RE.fullmatch(organization_id):
        raise SigningArtifactStorageError(
            "Invalid organization id for signing artifact storage."
        )
    return organization_id


def _safe_extension(extension: str) -> str:
    ext = (extension or "").lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    if ext not in ALLOWED_EXTENSIONS:
        raise SigningArtifactStorageError("Unsupported signing artifact extension.")
    return ext


def controlled_stored_name(sha256: str, extension: str) -> str:
    digest = (sha256 or "").lower()
    if not _SHA_RE.fullmatch(digest):
        raise SigningArtifactStorageError("Invalid SHA-256 for stored artifact filename.")
    return f"{digest}{_safe_extension(extension)}"


def stored_relative_path(organization_id: str, sha256: str, extension: str) -> str:
    org = _safe_org_segment(organization_id)
    return f"{org}/{controlled_stored_name(sha256, extension)}"


def absolute_stored_path(relative_path: str) -> Path:
    if not relative_path or relative_path != os.path.normpath(relative_path):
        raise SigningArtifactStorageError("Invalid stored relative path.")
    if relative_path.startswith("/") or "\\" in relative_path:
        raise SigningArtifactStorageError("Invalid stored relative path.")
    parts = relative_path.split("/")
    if len(parts) != 2 or ".." in parts:
        raise SigningArtifactStorageError("Invalid stored relative path.")
    org, name = parts
    _safe_org_segment(org)
    digest, ext = os.path.splitext(name)
    digest = digest.lower()
    if name != controlled_stored_name(digest, ext):
        raise SigningArtifactStorageError("Invalid stored artifact filename.")
    path = (get_signing_artifact_root() / org / name).resolve()
    root = get_signing_artifact_root().resolve()
    if root not in path.parents:
        raise SigningArtifactStorageError("Stored path escapes signing artifact root.")
    return path


def store_immutable_bytes(
    organization_id: str,
    data: bytes,
    *,
    extension: str,
) -> tuple[str, str]:
    """Write frozen signing bytes once. Returns (relative_key, sha256)."""
    if not data:
        raise SigningArtifactStorageError("Signing artifact is empty.")
    digest = sha256_hex(data)
    rel = stored_relative_path(organization_id, digest, extension)
    dest = absolute_stored_path(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        existing = dest.read_bytes()
        if sha256_hex(existing) != digest:
            raise SigningArtifactStorageError(
                "Refusing to overwrite stored signing artifact bytes."
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


def read_retained_bytes(relative_path: str) -> bytes:
    path = absolute_stored_path(relative_path)
    if not path.is_file():
        raise SigningArtifactStorageError("Signing artifact is not retained.")
    return path.read_bytes()
