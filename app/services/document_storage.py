"""Private, content-addressed, write-once storage for uploaded company documents (31 Oct 2026).

Same rules as signing_artifact_storage.py, with its own root:

    <DOCUMENT_ROOT or instance/documents>/<organization_id>/<sha[0:2]>/<sha256><ext>

Exact bytes are retained under their SHA-256; the same bytes uploaded twice in one organization are one file. A file
is never overwritten with different bytes and never deleted (documents are archived, not destroyed). Bytes are never
shared across organizations (organization segment).
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
ALLOWED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif", ".docx", ".xlsx", ".xlsm", ".csv",
                      ".txt")
DEFAULT_MAX_BYTES = 25 * 1024 * 1024

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".csv": "text/csv",
    ".txt": "text/plain",
}
# Shown in the page (inline); everything else downloads.
INLINE_MEDIA_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png", "image/gif"})


class DocumentStorageError(ValueError):
    """Raised when document bytes or a stored path cannot be accepted."""


def get_document_root() -> Path:
    root = current_app.config.get("DOCUMENT_ROOT")
    path = Path(root) if root else Path(current_app.instance_path) / "documents"
    path.mkdir(parents=True, exist_ok=True)
    return path


def max_bytes() -> int:
    return int(current_app.config.get("DOCUMENT_MAX_BYTES") or DEFAULT_MAX_BYTES)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_org_segment(organization_id: str) -> str:
    if not organization_id or not _ORG_SEGMENT_RE.fullmatch(organization_id) or organization_id in (".", ".."):
        raise DocumentStorageError("Invalid organization for document storage.")
    return organization_id


def safe_extension(filename_or_ext: str) -> str:
    raw = (filename_or_ext or "").lower()
    ext = raw if raw.startswith(".") and "/" not in raw and raw.count(".") == 1 else os.path.splitext(raw)[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentStorageError("This kind of file can't be filed. Use PDF, a photo, Word, Excel, CSV or text.")
    return ext


def media_type_for(ext: str) -> str:
    return MEDIA_TYPES.get(safe_extension(ext), "application/octet-stream")


def validate_bytes(data: bytes, ext: str) -> None:
    """Size and magic-byte checks (PDF and the common image types)."""
    if not data:
        raise DocumentStorageError("The file is empty.")
    limit = max_bytes()
    if len(data) > limit:
        raise DocumentStorageError(f"The file is larger than {limit // (1024 * 1024)} MB.")
    ext = safe_extension(ext)
    if ext == ".pdf" and not data.startswith(b"%PDF-"):
        raise DocumentStorageError("The file is not a PDF.")
    if ext in (".jpg", ".jpeg") and not data.startswith(b"\xff\xd8\xff"):
        raise DocumentStorageError("The file is not a JPEG photo.")
    if ext == ".png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise DocumentStorageError("The file is not a PNG image.")
    if ext == ".gif" and not data[:6] in (b"GIF87a", b"GIF89a"):
        raise DocumentStorageError("The file is not a GIF image.")
    if ext in (".docx", ".xlsx", ".xlsm") and not data.startswith(b"PK\x03\x04"):
        raise DocumentStorageError("The file is not a valid Office document.")


def storage_key(organization_id: str, sha256: str, ext: str) -> str:
    org = _safe_org_segment(organization_id)
    digest = (sha256 or "").lower()
    if not _SHA_RE.fullmatch(digest):
        raise DocumentStorageError("Invalid SHA-256 for a stored document.")
    return f"{org}/{digest[:2]}/{digest}{safe_extension(ext)}"


def absolute_stored_path(key: str) -> Path:
    if not key or key != os.path.normpath(key) or key.startswith("/") or "\\" in key:
        raise DocumentStorageError("Invalid stored document path.")
    parts = key.split("/")
    if len(parts) != 3 or ".." in parts:
        raise DocumentStorageError("Invalid stored document path.")
    org, prefix, name = parts
    digest, ext = os.path.splitext(name)
    if storage_key(org, digest, ext) != key or prefix != digest[:2]:
        raise DocumentStorageError("Invalid stored document path.")
    root = get_document_root().resolve()
    candidate = get_document_root() / org / prefix / name
    if candidate.is_symlink():
        raise DocumentStorageError("Stored document path is a link.")
    path = candidate.resolve()
    if root not in path.parents:
        raise DocumentStorageError("Stored document path escapes the documents folder.")
    return path


def store_bytes(organization_id: str, data: bytes, ext: str) -> tuple[str, str]:
    """Write bytes once. Returns (storage_key, sha256). Same bytes again = the same file."""
    validate_bytes(data, ext)
    digest = sha256_hex(data)
    key = storage_key(organization_id, digest, ext)
    dest = absolute_stored_path(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if sha256_hex(dest.read_bytes()) != digest:
            raise DocumentStorageError("Refusing to overwrite a stored document with different bytes.")
        return key, digest
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
    return key, digest


def stored_file_exists(key: str) -> bool:
    try:
        return absolute_stored_path(key).is_file()
    except DocumentStorageError:
        return False


def read_verified(key: str, expected_sha256: str) -> bytes:
    path = absolute_stored_path(key)
    if not path.is_file():
        raise DocumentStorageError("The stored file is not available.")
    data = path.read_bytes()
    if sha256_hex(data) != expected_sha256:
        current_app.logger.error("Stored document failed its SHA-256 check: %s", key)
        raise DocumentStorageError("The stored file failed its integrity check.")
    return data
