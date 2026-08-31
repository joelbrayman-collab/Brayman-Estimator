"""BUILD Media Compatibility / Rendition service (FG-020 increment).

Compatible Renditions are regenerable working/display artifacts.
They are not Original Source, not Derived Candidates, and not archive records.

First transformation: HEIC/HEIF Original Source → JPEG display rendition.
Image-only. Local conversion only. Original Source bytes are never mutated.
"""

from __future__ import annotations

import logging
import os
import tempfile
from io import BytesIO
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps
import pillow_heif

from app.models.build import ORIGINAL_KIND_IMAGE, FieldCaptureOriginal
from app.services.build_storage import (
    BuildStorageError,
    absolute_stored_path,
    image_is_browser_displayable,
    safe_org_segment,
)

pillow_heif.register_heif_opener()

logger = logging.getLogger(__name__)

_JPEG_MAGIC = b"\xff\xd8\xff"

DISPLAY_FILENAME = "display.jpg"
JPEG_QUALITY = 85
MAX_LONG_EDGE = 2048
HEIC_HEIF_MIMES = {"image/heic", "image/heif"}

# JPEG quality 85 is standard browser-display compression: visually faithful
# for desktop Event Detail without storing a second near-lossless photo.
# 2048px long edge covers typical desktop/full-width review without keeping
# a 12MP iPhone still as a working copy. Renditions remain independently
# purgeable after a future verified Project Archive.


def get_build_rendition_root() -> Path:
    root = current_app.config.get("BUILD_RENDITION_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "build_renditions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def needs_jpeg_display_rendition(original: FieldCaptureOriginal) -> bool:
    if original is None or original.kind != ORIGINAL_KIND_IMAGE:
        return False
    if image_is_browser_displayable(original.mime_type):
        return False
    return (original.mime_type or "") in HEIC_HEIF_MIMES


def rendition_relative_path(original: FieldCaptureOriginal) -> str:
    event = original.event
    if event is None:
        raise BuildStorageError("Original is missing its Field Capture Event.")
    org = safe_org_segment(event.organization_id)
    project = str(int(event.project_id))
    event_id = str(int(event.id))
    original_id = str(int(original.id))
    return f"{org}/{project}/{event_id}/{original_id}/{DISPLAY_FILENAME}"


def absolute_rendition_path(original: FieldCaptureOriginal) -> Path:
    relative = rendition_relative_path(original)
    if relative != os.path.normpath(relative) or relative.startswith("/") or "\\" in relative:
        raise BuildStorageError("Invalid rendition relative path.")
    parts = relative.split("/")
    if len(parts) != 5 or ".." in parts or parts[-1] != DISPLAY_FILENAME:
        raise BuildStorageError("Invalid rendition relative path.")
    path = (get_build_rendition_root() / Path(*parts)).resolve()
    root = get_build_rendition_root().resolve()
    if root not in path.parents:
        raise BuildStorageError("Rendition path escapes BUILD rendition root.")
    return path


def _store_rendition_bytes(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
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


def _existing_valid_jpeg(path: Path) -> bool:
    if not path.is_file():
        return False
    data = path.read_bytes()
    return bool(data) and data.startswith(_JPEG_MAGIC)


def convert_heic_original_to_jpeg(data: bytes) -> bytes:
    """Decode HEIC/HEIF bytes to a bounded oriented JPEG. Local only."""
    if not data:
        raise BuildStorageError("Original file is empty.")
    image = Image.open(BytesIO(data))
    image = ImageOps.exif_transpose(image) or image
    if image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")
    width, height = image.size
    long_edge = max(width, height)
    if long_edge > MAX_LONG_EDGE:
        scale = MAX_LONG_EDGE / float(long_edge)
        image = image.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.Resampling.LANCZOS,
        )
    out = BytesIO()
    image.save(
        out,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
    )
    jpeg = out.getvalue()
    if not jpeg.startswith(_JPEG_MAGIC):
        raise BuildStorageError("Compatible JPEG rendition was not produced.")
    return jpeg


def ensure_compatible_rendition(original: FieldCaptureOriginal) -> Path | None:
    """Return the display JPEG path when a rendition is required and available.

    Directly renderable JPEG/PNG/GIF originals do not need a rendition.
    HEIC/HEIF originals get a JPEG display copy. Failure never mutates
    Original Source and never raises to the capture caller.
    """
    if original is None or not needs_jpeg_display_rendition(original):
        return None
    try:
        dest = absolute_rendition_path(original)
        if _existing_valid_jpeg(dest):
            return dest
        source_path = absolute_stored_path(original.stored_relative_path)
        if not source_path.is_file():
            logger.warning(
                "BUILD rendition skipped; Original Source missing for original %s.",
                original.id,
            )
            return None
        source_bytes = source_path.read_bytes()
        jpeg = convert_heic_original_to_jpeg(source_bytes)
        _store_rendition_bytes(dest, jpeg)
        return dest
    except Exception:
        logger.warning(
            "BUILD compatible JPEG rendition failed for original %s; Original Source kept.",
            getattr(original, "id", None),
            exc_info=True,
        )
        return None


def open_display_rendition(original: FieldCaptureOriginal) -> Path | None:
    return ensure_compatible_rendition(original)
