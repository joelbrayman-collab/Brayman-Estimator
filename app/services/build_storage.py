"""Private filesystem custody for BUILD original audio/image evidence (FG-020)."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

from flask import current_app

_ORG_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,50}$")
_ID_SEGMENT_RE = re.compile(r"^[1-9][0-9]*$")

DEFAULT_MAX_BYTES = 25 * 1024 * 1024

_PNG_MAGIC = b"\x89PNG"
_JPEG_MAGIC = b"\xff\xd8\xff"
_GIF_MAGICS = (b"GIF87a", b"GIF89a")
_WAV_RIFF = b"RIFF"
_WAV_WAVE = b"WAVE"
_ID3 = b"ID3"
_WEBM_EBML = b"\x1a\x45\xdf\xa3"
# ISO/IEC 23008-12 HEIF still-image brands. Not AVIF, not generic MP4.
_HEIF_IMAGE_BRANDS = {
    b"heic",
    b"heix",
    b"heif",
    b"heis",
    b"heim",
    b"hevc",
    b"hevx",
    b"mif1",
    b"msf1",
}

# Audio MP4 / M4A brands. Generic video-only brands are not sufficient alone
# if the declared type is audio; we still require an audio-oriented brand or
# a common ISO-BMFF audio major/compatible set, and reject HEIF image brands.
_AUDIO_MP4_BRANDS = {
    b"M4A ",
    b"M4B ",
    b"mp41",
    b"mp42",
    b"isom",
    b"iso2",
    b"iso5",
}

_IMAGE_BY_EXT = {
    ".jpg": ("image/jpeg", ".jpg"),
    ".jpeg": ("image/jpeg", ".jpg"),
    ".png": ("image/png", ".png"),
    ".gif": ("image/gif", ".gif"),
    ".heic": ("image/heic", ".heic"),
    ".heif": ("image/heif", ".heif"),
}

_AUDIO_BY_EXT = {
    ".m4a": ("audio/mp4", ".m4a"),
    ".mp4": ("audio/mp4", ".m4a"),
    ".aac": ("audio/aac", ".aac"),
    ".mp3": ("audio/mpeg", ".mp3"),
    ".wav": ("audio/wav", ".wav"),
    ".webm": ("audio/webm", ".webm"),
}

BROWSER_PLAYABLE_AUDIO = {
    "audio/mpeg",
    "audio/wav",
    "audio/mp4",
    "audio/aac",
    "audio/x-m4a",
    "audio/webm",
}

BROWSER_DISPLAYABLE_IMAGE = {
    "image/jpeg",
    "image/png",
    "image/gif",
}


class BuildStorageError(ValueError):
    """Raised when BUILD original bytes or a storage path cannot be accepted."""


def max_original_bytes() -> int:
    try:
        configured = int(current_app.config.get("BUILD_ORIGINAL_MAX_BYTES") or 0)
    except (TypeError, ValueError):
        configured = 0
    return configured if configured > 0 else DEFAULT_MAX_BYTES


def get_build_original_root() -> Path:
    root = current_app.config.get("BUILD_ORIGINAL_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "build_originals"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_org_segment(organization_id: str) -> str:
    if not organization_id or not _ORG_SEGMENT_RE.fullmatch(organization_id):
        raise BuildStorageError("Invalid organization id for BUILD original storage.")
    return organization_id


def _safe_id_segment(value, label: str) -> str:
    text = str(value)
    if not _ID_SEGMENT_RE.fullmatch(text):
        raise BuildStorageError(f"Invalid {label} for BUILD original storage.")
    return text


def sanitize_original_filename(filename: str | None) -> str | None:
    if not filename or not str(filename).strip():
        return None
    raw = str(filename).strip().lower()
    if raw.startswith(("http://", "https://", "//")):
        raise BuildStorageError("Remote original URLs are not allowed.")
    name = os.path.basename(str(filename).replace("\\", "/")).strip()
    if not name or name in {".", ".."}:
        return None
    if ".." in name or "/" in name or "\x00" in name:
        raise BuildStorageError("Original filename is not allowed.")
    return name[:255]


def extension_of(filename: str | None) -> str:
    cleaned = sanitize_original_filename(filename) or ""
    return os.path.splitext(cleaned)[1].lower()


def parse_ftyp_brands(data: bytes) -> tuple[bytes, list[bytes]] | None:
    """Return (major_brand, compatible_brands) for an ISO-BMFF ftyp box."""
    if len(data) < 16:
        return None
    if data[4:8] != b"ftyp":
        return None
    box_size = int.from_bytes(data[0:4], "big")
    if box_size == 1:
        return None
    if box_size == 0:
        box_size = len(data)
    if box_size < 16 or box_size > len(data):
        return None
    major = data[8:12]
    compatible = []
    offset = 16
    end = box_size
    while offset + 4 <= end:
        compatible.append(data[offset : offset + 4])
        offset += 4
    return major, compatible


def _brands_include(parsed, allowed: set) -> bool:
    if parsed is None:
        return False
    major, compatible = parsed
    if major in allowed:
        return True
    return any(brand in allowed for brand in compatible)


def _is_heif_image(data: bytes) -> bool:
    parsed = parse_ftyp_brands(data)
    if parsed is None:
        return False
    major, _compatible = parsed
    if not _brands_include(parsed, _HEIF_IMAGE_BRANDS):
        return False
    if major in {b"avif", b"avis", b"mp41", b"mp42", b"qt  ", b"M4A ", b"M4B "}:
        return False
    return True


def _is_jpeg(data: bytes) -> bool:
    return data.startswith(_JPEG_MAGIC)


def _is_png(data: bytes) -> bool:
    return data.startswith(_PNG_MAGIC)


def _is_gif(data: bytes) -> bool:
    return any(data.startswith(magic) for magic in _GIF_MAGICS)


def _is_wav(data: bytes) -> bool:
    return len(data) >= 12 and data.startswith(_WAV_RIFF) and data[8:12] == _WAV_WAVE


def _is_mp3(data: bytes) -> bool:
    if data.startswith(_ID3):
        return True
    if len(data) < 2 or data[0] != 0xFF:
        return False
    second = data[1]
    if (second & 0xE0) != 0xE0:
        return False
    layer = (second >> 1) & 0x03
    return layer != 0


def _is_adts_aac(data: bytes) -> bool:
    if len(data) < 2:
        return False
    header = int.from_bytes(data[0:2], "big")
    return (header & 0xFFF6) == 0xFFF0


def _is_webm(data: bytes) -> bool:
    return data.startswith(_WEBM_EBML)


def _is_audio_mp4(data: bytes) -> bool:
    parsed = parse_ftyp_brands(data)
    if parsed is None:
        return False
    major, _compatible = parsed
    if _brands_include(parsed, _HEIF_IMAGE_BRANDS) and major in _HEIF_IMAGE_BRANDS:
        return False
    if major in {b"avif", b"avis"}:
        return False
    return _brands_include(parsed, _AUDIO_MP4_BRANDS) or major in _AUDIO_MP4_BRANDS


def validate_image_bytes(data: bytes, filename: str | None) -> tuple[str, str, str, int]:
    """Return (sha256, canonical_ext, mime_type, byte_size)."""
    if not data:
        raise BuildStorageError("Original file is empty.")
    limit = max_original_bytes()
    if len(data) > limit:
        raise BuildStorageError(
            f"Original exceeds the {limit // (1024 * 1024)} MB size limit."
        )
    ext = extension_of(filename)
    if ext not in _IMAGE_BY_EXT:
        raise BuildStorageError(
            "Image original must be JPEG, PNG, GIF, HEIC, or HEIF."
        )
    mime, stored_ext = _IMAGE_BY_EXT[ext]
    if stored_ext == ".jpg" and not _is_jpeg(data):
        raise BuildStorageError(
            "Image file contents do not match the declared JPEG type."
        )
    if stored_ext == ".png" and not _is_png(data):
        raise BuildStorageError(
            "Image file contents do not match the declared PNG type."
        )
    if stored_ext == ".gif" and not _is_gif(data):
        raise BuildStorageError(
            "Image file contents do not match the declared GIF type."
        )
    if stored_ext in {".heic", ".heif"}:
        if not _is_heif_image(data):
            raise BuildStorageError(
                "Image file contents are not a supported HEIC/HEIF original."
            )
        parsed = parse_ftyp_brands(data)
        if parsed is not None and parsed[0] in {b"mp41", b"mp42", b"isom"}:
            if not _brands_include(parsed, _HEIF_IMAGE_BRANDS):
                raise BuildStorageError(
                    "Generic ISO-BMFF / MP4 bytes are not accepted as HEIC/HEIF."
                )
    digest = hashlib.sha256(data).hexdigest()
    return digest, stored_ext, mime, len(data)


def validate_audio_bytes(data: bytes, filename: str | None) -> tuple[str, str, str, int]:
    """Return (sha256, canonical_ext, mime_type, byte_size)."""
    if not data:
        raise BuildStorageError("Original file is empty.")
    limit = max_original_bytes()
    if len(data) > limit:
        raise BuildStorageError(
            f"Original exceeds the {limit // (1024 * 1024)} MB size limit."
        )
    ext = extension_of(filename)
    if ext not in _AUDIO_BY_EXT:
        raise BuildStorageError(
            "Audio original must be M4A, AAC, MP3, WAV, or WebM."
        )
    mime, stored_ext = _AUDIO_BY_EXT[ext]
    if stored_ext == ".m4a":
        if not _is_audio_mp4(data):
            raise BuildStorageError(
                "Audio file contents do not match a supported M4A / audio MP4 original."
            )
    elif stored_ext == ".aac":
        if not (_is_adts_aac(data) or _is_audio_mp4(data)):
            raise BuildStorageError(
                "Audio file contents do not match the declared AAC type."
            )
    elif stored_ext == ".mp3":
        if not _is_mp3(data):
            raise BuildStorageError(
                "Audio file contents do not match the declared MP3 type."
            )
    elif stored_ext == ".wav":
        if not _is_wav(data):
            raise BuildStorageError(
                "Audio file contents do not match the declared WAV type."
            )
    elif stored_ext == ".webm":
        if not _is_webm(data):
            raise BuildStorageError(
                "Audio file contents do not match the declared WebM type."
            )
    digest = hashlib.sha256(data).hexdigest()
    return digest, stored_ext, mime, len(data)


def stored_relative_path(
    organization_id: str,
    project_id,
    event_id,
    original_id,
    extension: str,
) -> str:
    org = safe_org_segment(organization_id)
    project = _safe_id_segment(project_id, "project id")
    event = _safe_id_segment(event_id, "event id")
    original = _safe_id_segment(original_id, "original id")
    ext = (extension or "").lower()
    allowed = {item[1] for item in _IMAGE_BY_EXT.values()} | {
        item[1] for item in _AUDIO_BY_EXT.values()
    }
    if ext not in allowed:
        raise BuildStorageError("Invalid stored original extension.")
    return f"{org}/{project}/{event}/{original}{ext}"


def absolute_stored_path(relative_path: str) -> Path:
    if not relative_path or relative_path != os.path.normpath(relative_path):
        raise BuildStorageError("Invalid stored original relative path.")
    if relative_path.startswith("/") or "\\" in relative_path:
        raise BuildStorageError("Invalid stored original relative path.")
    parts = relative_path.split("/")
    if len(parts) != 4 or ".." in parts:
        raise BuildStorageError("Invalid stored original relative path.")
    org, project, event, name = parts
    safe_org_segment(org)
    _safe_id_segment(project, "project id")
    _safe_id_segment(event, "event id")
    ext = os.path.splitext(name)[1].lower()
    original_id = os.path.splitext(name)[0]
    expected = stored_relative_path(org, project, event, original_id, ext)
    if relative_path != expected:
        raise BuildStorageError("Invalid stored original filename.")
    path = (get_build_original_root() / org / project / event / name).resolve()
    root = get_build_original_root().resolve()
    if root not in path.parents:
        raise BuildStorageError("Stored original path escapes BUILD original root.")
    return path


def store_immutable_bytes(relative_path: str, data: bytes, sha256: str) -> str:
    dest = absolute_stored_path(relative_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    digest = (sha256 or "").lower()
    if dest.exists():
        existing = dest.read_bytes()
        existing_sha = hashlib.sha256(existing).hexdigest()
        if existing_sha != digest:
            raise BuildStorageError(
                "Refusing to overwrite stored BUILD original bytes."
            )
        return relative_path

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
    return relative_path


def image_is_browser_displayable(mime_type: str | None) -> bool:
    return (mime_type or "") in BROWSER_DISPLAYABLE_IMAGE


def audio_is_browser_playable(mime_type: str | None) -> bool:
    return (mime_type or "") in BROWSER_PLAYABLE_AUDIO
