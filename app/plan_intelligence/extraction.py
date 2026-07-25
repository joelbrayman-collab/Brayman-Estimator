"""Deterministic PDF metadata and embedded-text extraction (no OCR)."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from pypdf import PdfReader
from pypdf.errors import PdfReadError


EXTRACTOR_NAME = "deterministic_pdf"
EXTRACTOR_VERSION = "1.0.0"


class ExtractionError(Exception):
    """Raised when deterministic extraction cannot read the PDF."""


def _info_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_deterministic_pdf(data: bytes) -> Dict[str, Any]:
    """Extract PDF info dict fields and per-page embedded text.

    Page indexes are **0-based**. Does not perform OCR.
    """
    try:
        reader = PdfReader(BytesIO(data))
    except PdfReadError as exc:
        raise ExtractionError("Could not read PDF for indexing.") from exc

    meta = reader.metadata
    pdf_info = {
        "title": _info_str(meta.title) if meta else None,
        "author": _info_str(meta.author) if meta else None,
        "subject": _info_str(meta.subject) if meta else None,
        "creator": _info_str(meta.creator) if meta else None,
    }

    pages: List[Dict[str, Any]] = []
    for index, page in enumerate(reader.pages):
        width = None
        height = None
        try:
            box = page.mediabox
            width = float(box.width)
            height = float(box.height)
        except Exception:
            pass

        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        stripped = text.strip()
        has_text = bool(stripped)
        pages.append(
            {
                "page_index": index,
                "width": width,
                "height": height,
                "extracted_text": text if has_text else "",
                "has_text": has_text,
                "is_blank": not has_text,
            }
        )

    return {
        "extractor_name": EXTRACTOR_NAME,
        "extractor_version": EXTRACTOR_VERSION,
        "pdf_info": pdf_info,
        "page_count": len(pages),
        "pages_with_text": sum(1 for p in pages if p["has_text"]),
        "has_text_layer": any(p["has_text"] for p in pages),
        "pages": pages,
    }
