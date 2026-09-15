"""FG-033 SIGN-E governed Family 05 DOCX → PDF conversion.

LibreOffice/soffice only. Convert once. No ReportLab or HTML fallback.
Missing converter BLOCKS. Failed conversion does not retain a PDF.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, Optional

from flask import current_app

DEFAULT_SOFFICE_TIMEOUT_SECONDS = 60
CONVERTER_IDENTITY_LIBREOFFICE = "libreoffice-soffice"
MAC_SOFFICE_PATH = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

BLOCK_CONVERTER_UNAVAILABLE = "CONVERTER_UNAVAILABLE"
BLOCK_CONVERSION_FAILED = "CONVERSION_FAILED"
BLOCK_CONVERSION_EMPTY = "CONVERSION_EMPTY"
BLOCK_CONVERSION_NOT_PDF = "CONVERSION_NOT_PDF"


class DocxPdfConversionError(ValueError):
    """Governed conversion BLOCK. Never a silent fallback."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class ConversionResult(NamedTuple):
    pdf_bytes: bytes
    converter_identity: str
    converter_version: str
    converted_at: datetime
    source_docx_sha256: str


def _timeout_seconds() -> int:
    try:
        return int(
            current_app.config.get(
                "SIGNING_SOFFICE_TIMEOUT_SECONDS",
                DEFAULT_SOFFICE_TIMEOUT_SECONDS,
            )
        )
    except (TypeError, ValueError):
        return DEFAULT_SOFFICE_TIMEOUT_SECONDS


def discover_soffice_path() -> Optional[str]:
    configured = (
        current_app.config.get("SIGNING_SOFFICE_PATH")
        or os.environ.get("SIGNING_SOFFICE_PATH")
        or os.environ.get("SOFFICE_PATH")
        or ""
    ).strip()
    if configured:
        return configured
    found = shutil.which("soffice")
    if found:
        return found
    if Path(MAC_SOFFICE_PATH).is_file():
        return MAC_SOFFICE_PATH
    return None


def soffice_version(executable: str) -> str:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DocxPdfConversionError(BLOCK_CONVERTER_UNAVAILABLE) from exc
    line = ((completed.stdout or "") + (completed.stderr or "")).strip().splitlines()
    if not line:
        return "unknown"
    return line[0].strip()[:120]


def _injected_converter():
    return current_app.config.get("SIGNING_DOCX_TO_PDF")


def convert_docx_to_pdf(docx_bytes: bytes, *, source_docx_sha256: str) -> ConversionResult:
    """Convert exact retained DOCX bytes once. Caller retains the PDF and hashes it."""
    if not docx_bytes:
        raise DocxPdfConversionError(BLOCK_CONVERSION_EMPTY)
    injected = _injected_converter()
    if callable(injected):
        produced = injected(docx_bytes)
        if isinstance(produced, ConversionResult):
            return produced
        pdf_bytes = produced
        if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
            raise DocxPdfConversionError(BLOCK_CONVERSION_NOT_PDF)
        return ConversionResult(
            pdf_bytes=pdf_bytes,
            converter_identity="injected-test-converter",
            converter_version="test",
            converted_at=datetime.utcnow(),
            source_docx_sha256=source_docx_sha256,
        )

    executable = discover_soffice_path()
    if not executable or not Path(executable).exists():
        raise DocxPdfConversionError(BLOCK_CONVERTER_UNAVAILABLE)

    tmp_root = None
    try:
        tmp_root = tempfile.mkdtemp(prefix="signing-docx-pdf-")
        source_path = Path(tmp_root) / "source.docx"
        source_path.write_bytes(docx_bytes)
        completed = subprocess.run(
            [
                executable,
                "--headless",
                "--norestore",
                "--nolockcheck",
                "--convert-to",
                "pdf",
                "--outdir",
                tmp_root,
                str(source_path),
            ],
            check=False,
            capture_output=True,
            timeout=_timeout_seconds(),
        )
        pdf_path = Path(tmp_root) / "source.pdf"
        if completed.returncode != 0 or not pdf_path.is_file():
            raise DocxPdfConversionError(BLOCK_CONVERSION_FAILED)
        pdf_bytes = pdf_path.read_bytes()
        if not pdf_bytes:
            raise DocxPdfConversionError(BLOCK_CONVERSION_EMPTY)
        if not pdf_bytes.startswith(b"%PDF"):
            raise DocxPdfConversionError(BLOCK_CONVERSION_NOT_PDF)
        version = soffice_version(executable)
        return ConversionResult(
            pdf_bytes=pdf_bytes,
            converter_identity=CONVERTER_IDENTITY_LIBREOFFICE,
            converter_version=version,
            converted_at=datetime.utcnow(),
            source_docx_sha256=source_docx_sha256,
        )
    except DocxPdfConversionError:
        raise
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DocxPdfConversionError(BLOCK_CONVERTER_UNAVAILABLE) from exc
    finally:
        if tmp_root:
            shutil.rmtree(tmp_root, ignore_errors=True)
