"""Injected Family 05 converter for tests. Not a product fallback."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfWriter


def _valid_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


MINIMAL_PDF = _valid_pdf()

_calls: list[int] = []


def reset_conversion_calls() -> None:
    _calls.clear()


def conversion_call_count() -> int:
    return len(_calls)


def injected_docx_to_pdf(docx_bytes: bytes) -> bytes:
    if not docx_bytes:
        raise ValueError("empty docx")
    _calls.append(len(docx_bytes))
    return MINIMAL_PDF


def not_pdf_converter(_docx_bytes: bytes) -> bytes:
    return b"NOT-A-PDF"
