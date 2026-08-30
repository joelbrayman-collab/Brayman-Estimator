"""Private filesystem custody for organization brand logos (ADR-040 / FG-017)."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

from flask import current_app

_ORG_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,50}$")
_SHA_RE = re.compile(r"^[a-f0-9]{64}$")

SUPPORTED_LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif"}
DEFAULT_MAX_LOGO_BYTES = 5 * 1024 * 1024
_PNG_MAGIC = b"\x89PNG"
_JPEG_MAGIC = b"\xff\xd8\xff"
_GIF_MAGICS = (b"GIF87a", b"GIF89a")
_LOGO_MIMETYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
}


class BrandLogoStorageError(ValueError):
    """Raised when logo bytes or a storage path cannot be accepted."""


def max_logo_bytes() -> int:
    try:
        configured = int(current_app.config.get("BRAND_LOGO_MAX_BYTES") or 0)
    except (TypeError, ValueError):
        configured = 0
    return configured if configured > 0 else DEFAULT_MAX_LOGO_BYTES


def get_brand_logo_root() -> Path:
    root = current_app.config.get("BRAND_LOGO_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "brand_logos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_org_segment(organization_id: str) -> str:
    if not organization_id or not _ORG_SEGMENT_RE.fullmatch(organization_id):
        raise BrandLogoStorageError("Invalid organization id for brand logo storage.")
    return organization_id


def is_remote_url(value: str | None) -> bool:
    raw = (value or "").strip().lower()
    return raw.startswith(("http://", "https://", "//"))


def sanitize_original_filename(filename: str | None) -> str | None:
    if not filename or not str(filename).strip():
        return None
    if is_remote_url(filename):
        raise BrandLogoStorageError("Remote logo URLs are not allowed.")
    name = os.path.basename(str(filename).replace("\\", "/")).strip()
    if not name or name in {".", ".."}:
        return None
    if ".." in name or "/" in name:
        raise BrandLogoStorageError("Logo filename is not allowed.")
    return name[:255]


def _extension_from_filename(filename: str | None) -> str:
    cleaned = sanitize_original_filename(filename) or ""
    ext = os.path.splitext(cleaned)[1].lower()
    if ext not in SUPPORTED_LOGO_SUFFIXES:
        raise BrandLogoStorageError(
            "Logo must be a PNG, JPEG, or GIF file."
        )
    return ext


def _magic_matches(data: bytes, extension: str) -> bool:
    if extension == ".png":
        return data.startswith(_PNG_MAGIC)
    if extension in {".jpg", ".jpeg"}:
        return data.startswith(_JPEG_MAGIC)
    if extension == ".gif":
        return any(data.startswith(magic) for magic in _GIF_MAGICS)
    return False


def validate_logo_bytes(data: bytes, filename: str | None) -> tuple[str, str, int]:
    """Return (sha256, extension, byte_size) after validation."""
    if is_remote_url(filename):
        raise BrandLogoStorageError("Remote logo URLs are not allowed.")
    if not data:
        raise BrandLogoStorageError("Logo file is empty.")
    limit = max_logo_bytes()
    if len(data) > limit:
        raise BrandLogoStorageError("Logo exceeds the 5 MiB size limit.")
    extension = _extension_from_filename(filename)
    if not _magic_matches(data, extension):
        raise BrandLogoStorageError(
            "Logo file contents do not match the declared PNG, JPEG, or GIF type."
        )
    digest = hashlib.sha256(data).hexdigest()
    return digest, extension, len(data)


def controlled_stored_name(sha256: str, extension: str) -> str:
    ext = (extension or "").lower()
    if ext not in SUPPORTED_LOGO_SUFFIXES:
        raise BrandLogoStorageError("Invalid stored logo extension.")
    digest = (sha256 or "").lower()
    if not _SHA_RE.fullmatch(digest):
        raise BrandLogoStorageError("Invalid SHA-256 for stored logo filename.")
    return f"{digest}{ext}"


def stored_relative_path(organization_id: str, sha256: str, extension: str) -> str:
    org = safe_org_segment(organization_id)
    name = controlled_stored_name(sha256, extension)
    return f"{org}/{name}"


def absolute_brand_logo_path(relative_path: str) -> Path:
    if not relative_path or relative_path != os.path.normpath(relative_path):
        raise BrandLogoStorageError("Invalid stored logo relative path.")
    if relative_path.startswith("/") or "\\" in relative_path:
        raise BrandLogoStorageError("Invalid stored logo relative path.")
    parts = relative_path.split("/")
    if len(parts) != 2 or ".." in parts:
        raise BrandLogoStorageError("Invalid stored logo relative path.")
    org, name = parts
    safe_org_segment(org)
    ext = os.path.splitext(name)[1].lower()
    digest = os.path.splitext(name)[0].lower()
    if name != controlled_stored_name(digest, ext):
        raise BrandLogoStorageError("Invalid stored logo filename.")
    path = (get_brand_logo_root() / org / name).resolve()
    root = get_brand_logo_root().resolve()
    if root not in path.parents:
        raise BrandLogoStorageError("Stored logo path escapes brand logo root.")
    return path


def resolve_logo_filesystem_path(
    organization_id: str,
    sha256: str | None,
    extension: str | None,
) -> Path | None:
    if not sha256 or not extension:
        return None
    rel = stored_relative_path(organization_id, sha256, extension)
    path = absolute_brand_logo_path(rel)
    if not path.is_file():
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size <= 0 or size > max_logo_bytes():
        return None
    return path


def logo_mimetype(extension: str | None) -> str:
    return _LOGO_MIMETYPES.get((extension or "").lower(), "application/octet-stream")


def store_logo_bytes(
    organization_id: str,
    data: bytes,
    filename: str | None,
) -> tuple[str, str, int, str | None]:
    """Write validated logo bytes once under a SHA-named path.

    Never overwrites an existing SHA path whose bytes differ.
    """
    digest, extension, byte_size = validate_logo_bytes(data, filename)
    original = sanitize_original_filename(filename)
    rel = stored_relative_path(organization_id, digest, extension)
    dest = absolute_brand_logo_path(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        existing = dest.read_bytes()
        existing_sha = hashlib.sha256(existing).hexdigest()
        if existing_sha != digest:
            raise BrandLogoStorageError(
                "Refusing to overwrite stored brand logo bytes."
            )
        return digest, extension, byte_size, original

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
    return digest, extension, byte_size, original
