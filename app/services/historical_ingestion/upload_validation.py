"""Bounded OpenXML / ZIP validation for productized historical uploads (FG-013)."""

from __future__ import annotations

import hashlib
import io
import os
import zipfile
from dataclasses import dataclass
from typing import Optional

from flask import current_app

ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}
ZIP_MAGIC = b"PK\x03\x04"
MAX_FAILURE_REASON = 2000
WORKBOOK_XML = "xl/workbook.xml"


class HistoricalUploadValidationError(Exception):
    """Raised when a productized historical upload fails validation."""

    def __init__(self, message: str, outcome: str):
        super().__init__(message)
        self.outcome = outcome
        self.message = message


@dataclass
class ValidatedUpload:
    original_filename: str
    extension: str
    byte_size: int
    sha256: str
    data: bytes


def get_max_upload_bytes() -> int:
    return int(current_app.config.get("HISTORICAL_UPLOAD_MAX_BYTES", 25 * 1024 * 1024))


def get_zip_max_uncompressed() -> int:
    return int(
        current_app.config.get("HISTORICAL_UPLOAD_ZIP_MAX_UNCOMPRESSED", 80 * 1024 * 1024)
    )


def get_zip_max_member() -> int:
    return int(
        current_app.config.get("HISTORICAL_UPLOAD_ZIP_MAX_MEMBER", 40 * 1024 * 1024)
    )


def get_zip_max_files() -> int:
    return int(current_app.config.get("HISTORICAL_UPLOAD_ZIP_MAX_FILES", 200))


def safe_original_filename(raw_name: Optional[str]) -> str:
    name = (raw_name or "").replace("\\", "/")
    base = os.path.basename(name).strip()
    if not base or base in {".", ".."} or "\x00" in base:
        raise HistoricalUploadValidationError(
            "Filename is missing or unsafe.",
            "FAILED",
        )
    if ".." in base:
        raise HistoricalUploadValidationError(
            "Filename contains a path-traversal sequence.",
            "FAILED",
        )
    return base[:255]


def extension_of(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def bound_reason(text: str) -> str:
    return (text or "")[:MAX_FAILURE_REASON]


def validate_upload_bytes(raw_name: Optional[str], data: bytes) -> ValidatedUpload:
    """Validate extension, size, ZIP/OpenXML structure. Does not trust Content-Type."""
    filename = safe_original_filename(raw_name)
    ext = extension_of(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HistoricalUploadValidationError(
            f"Unsupported format '{ext or '(none)'}'. FG-013 accepts .xlsx and .xlsm only.",
            "UNSUPPORTED",
        )

    max_bytes = get_max_upload_bytes()
    byte_size = len(data or b"")
    if byte_size <= 0:
        raise HistoricalUploadValidationError("Uploaded file is empty.", "FAILED")
    if byte_size > max_bytes:
        raise HistoricalUploadValidationError(
            f"File exceeds the {max_bytes} byte per-file maximum.",
            "FAILED",
        )

    if not data.startswith(ZIP_MAGIC):
        raise HistoricalUploadValidationError(
            "File is not a valid OpenXML package (missing ZIP header).",
            "FAILED",
        )

    _validate_zip_safety(data)
    digest = hashlib.sha256(data).hexdigest()
    return ValidatedUpload(
        original_filename=filename,
        extension=ext,
        byte_size=byte_size,
        sha256=digest,
        data=data,
    )


def _validate_zip_safety(data: bytes) -> None:
    max_uncompressed = get_zip_max_uncompressed()
    max_member = get_zip_max_member()
    max_files = get_zip_max_files()
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            infos = zf.infolist()
            if len(infos) > max_files:
                raise HistoricalUploadValidationError(
                    "ZIP package contains too many members.",
                    "FAILED",
                )
            total = 0
            names = []
            for info in infos:
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or name.startswith("\\") or ".." in name.split("/"):
                    raise HistoricalUploadValidationError(
                        "ZIP package contains an unsafe member path.",
                        "FAILED",
                    )
                if info.file_size > max_member:
                    raise HistoricalUploadValidationError(
                        "ZIP member exceeds the uncompressed size limit.",
                        "FAILED",
                    )
                total += info.file_size
                if total > max_uncompressed:
                    raise HistoricalUploadValidationError(
                        "ZIP package exceeds the uncompressed size limit.",
                        "FAILED",
                    )
                names.append(name)
            if WORKBOOK_XML not in names:
                raise HistoricalUploadValidationError(
                    "Invalid OpenXML workbook: missing xl/workbook.xml.",
                    "FAILED",
                )
            zf.read(WORKBOOK_XML)
    except HistoricalUploadValidationError:
        raise
    except zipfile.BadZipFile:
        raise HistoricalUploadValidationError(
            "File is not a valid OpenXML/ZIP package.",
            "FAILED",
        ) from None
    except Exception:
        raise HistoricalUploadValidationError(
            "OpenXML structure could not be verified.",
            "FAILED",
        ) from None
