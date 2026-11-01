"""Text extraction for filed documents (extractor "calibrayt-docs-text" v1). No OCR, no network.

PDF: the text layer through Calibrayt's own deterministic extractor (pypdf). DOCX: python-docx paragraphs and
tables. TXT/CSV: UTF-8. Images and spreadsheets: no text in this release.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from app.models.documents import TEXT_EXTRACTED, TEXT_FAILED, TEXT_NO_TEXT, TEXT_UNSUPPORTED

EXTRACTOR_NAME = "calibrayt-docs-text"
EXTRACTOR_VERSION = "1"
MAX_BODY_CHARS = 1_000_000
MAX_SYNC_BYTES = 10 * 1024 * 1024
MAX_SYNC_PAGES = 200


@dataclass
class Extraction:
    status: str
    pages: list = field(default_factory=list)
    page_count: int | None = None
    title: str | None = None

    @property
    def body(self) -> str:
        return "\n\n".join(p for p in self.pages if p)[:MAX_BODY_CHARS]


def extract_text(data: bytes, media_type: str) -> Extraction:
    media_type = (media_type or "").lower()
    try:
        if media_type == "application/pdf":
            from app.plan_intelligence.extraction import ExtractionError, extract_deterministic_pdf

            try:
                result = extract_deterministic_pdf(data)
            except ExtractionError:
                return Extraction(TEXT_FAILED)
            pages = [(p.get("extracted_text") or p.get("text") or "") for p in result.get("pages") or []]
            title = (result.get("pdf_info") or {}).get("title")
            status = TEXT_EXTRACTED if any(p.strip() for p in pages) else TEXT_NO_TEXT
            return Extraction(status, pages[:MAX_SYNC_PAGES], len(pages), title)
        if media_type.endswith("wordprocessingml.document"):
            import docx

            document = docx.Document(BytesIO(data))
            parts = [p.text for p in document.paragraphs if p.text]
            for table in document.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            text = "\n".join(parts)
            return Extraction(TEXT_EXTRACTED if text.strip() else TEXT_NO_TEXT, [text], 1)
        if media_type in ("text/plain", "text/csv"):
            text = data.decode("utf-8", errors="replace")[:MAX_BODY_CHARS]
            return Extraction(TEXT_EXTRACTED if text.strip() else TEXT_NO_TEXT, [text], 1)
    except Exception:  # noqa: BLE001 - a bad file never blocks filing it
        return Extraction(TEXT_FAILED)
    return Extraction(TEXT_UNSUPPORTED)
