"""Approved Master Template Family V1 — the only presentation for the seven governed document types.

Joel, 27 Oct 2026 (permanent document-governance requirement): "DATA CHANGES BY PROJECT. THE APPROVED
DOCUMENT FORMAT DOES NOT." Each governed document type below resolves to exactly one approved master
(FG-022; identity register docs/testing/reusable-approved-document-template-family-v1-register.md). A
document of one of these types is produced only by populating a byte copy of that master:

- the master bytes must match the governed SHA-256, or nothing is produced;
- only the designated variable content changes: the CLIENT / PROJECT / SITE / DATE / AMOUNT / PRICE
  tokens, the rows of the master's data tables (placeholder "—" rows are filled; extra rows are copies of
  the master's own row, so their formatting is the master's), and the master's list of bullet paragraphs;
- headings, typography, spacing, margins, header, logo, footer and page structure are the master's;
- there is no fallback writer. A project-specific PDF writer or another layout cannot satisfy a
  governed document type (``assert_governed_route``). If a document cannot be produced from its master,
  ``ApprovedMasterError`` names the limitation and nothing is written.

The master files are confidential office files outside Git (ADR-032). Never written; always copied.
PDFs come from the same LibreOffice conversion the signing documents use (signing_docx_pdf).
"""

from __future__ import annotations

import copy
import hashlib
import os
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional, Sequence

FAMILY_VERSION = "V1"
MASTER_DIR_ENV = "CALIBRAYTAI_APPROVED_MASTER_DIR"
DEFAULT_MASTER_DIR = Path(
    "/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/"
    "Reusable Master Template Family V1/MASTER DOCX"
)

LABOUR_CALCULATION_DETAIL = "LABOUR_CALCULATION_DETAIL"
INTERNAL_DETAILED_COST_BREAKDOWN = "INTERNAL_DETAILED_COST_BREAKDOWN"
CUSTOMER_FACING_ESTIMATE = "CUSTOMER_FACING_ESTIMATE"
QUICKBOOKS_ESTIMATE_ENTRY = "QUICKBOOKS_ESTIMATE_ENTRY"
ONTARIO_CONSTRUCTION_CONTRACT = "ONTARIO_CONSTRUCTION_CONTRACT"
DOOR_WINDOW_SKYLIGHT_SCHEDULE = "DOOR_WINDOW_SKYLIGHT_SCHEDULE"
CLIENT_CONSTRUCTION_PROPOSAL = "CLIENT_CONSTRUCTION_PROPOSAL"
CUSTOMER_DETAILED_COST_ESTIMATE = "CUSTOMER_DETAILED_COST_ESTIMATE"

PLACEHOLDER = "—"


@dataclass(frozen=True)
class ApprovedMaster:
    family: str
    document_type: str
    title: str
    filename: str
    sha256: str
    classification: str


# Identity from the FG-022 register (Joel approval 4 Sep 2026; Family 08 added 27 Oct 2026). Family 05 is also governed by
# app/services/family_05_master.py with the same SHA-256.
APPROVED_MASTERS = {
    m.document_type: m for m in (
        ApprovedMaster("01", LABOUR_CALCULATION_DETAIL, "Labour Calculation Detail",
                       "01_Brayman_Labour_Calculation_Detail_MASTER_V1.docx",
                       "57748abe7cc3e24f135e94d54aad2c61c7a0748c4f5afb28567d55c06d785c39", "INTERNAL"),
        ApprovedMaster("02", INTERNAL_DETAILED_COST_BREAKDOWN, "Internal Detailed Cost Breakdown",
                       "02_Brayman_Internal_Detailed_Cost_Breakdown_MASTER_V1.docx",
                       "b187911a02b808d3dcad81aa718e4e89a330c8b97b4bcd274231c1beff461a93", "INTERNAL"),
        ApprovedMaster("03", CUSTOMER_FACING_ESTIMATE, "Customer-Facing Estimate",
                       "03_Brayman_Customer_Facing_Estimate_MASTER_V1.docx",
                       "25a816cdc11ec312993ca78c653152b8f4666e55716720dd7c1dcc27377c3825", "CUSTOMER-FACING"),
        ApprovedMaster("04", QUICKBOOKS_ESTIMATE_ENTRY, "QuickBooks Estimate Entry",
                       "04_Brayman_QuickBooks_Estimate_Entry_MASTER_V1.docx",
                       "28a65779d80b7f942c0b362ece01e438b8310e74607831834d3086b8008727bb", "INTERNAL ENTRY REFERENCE"),
        ApprovedMaster("05", ONTARIO_CONSTRUCTION_CONTRACT, "Ontario Construction Contract",
                       "05_Brayman_Ontario_Construction_Contract_COMMERCIAL_DRAFT_MASTER_V1.docx",
                       "24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5", "COMMERCIAL_DRAFT"),
        ApprovedMaster("06", DOOR_WINDOW_SKYLIGHT_SCHEDULE, "Door / Window / Skylight Schedule",
                       "06_Brayman_Door_Window_Skylight_Schedule_MASTER_V1.docx",
                       "3224e5945c83d90254d681ade168ee0a53d99041ac473978a00d152fb08714f2", "CUSTOMER-FACING"),
        ApprovedMaster("07", CLIENT_CONSTRUCTION_PROPOSAL, "Client Construction Proposal",
                       "07_Brayman_Client_Construction_Proposal_MASTER_V1.docx",
                       "213ce5c93dcf09b1299d066dc29e8cd68cfad3178b4a149a5f4ecf39349ba498", "CUSTOMER-FACING"),
        # Family 08 (Joel's explicit instruction, 27 Oct 2026): derived from Master 02's presentation with
        # internal-only content removed; customer selling prices, never contractor cost or margin.
        ApprovedMaster("08", CUSTOMER_DETAILED_COST_ESTIMATE, "Customer Detailed Cost Estimate",
                       "08_Brayman_Customer_Detailed_Cost_Estimate_MASTER_V1.docx",
                       "f9e7a27cf6924d55e7c92e53b5cb27dc77379ed421b7d982c79cbbb3588f100f", "CUSTOMER-FACING"),
    )
}
GOVERNED_DOCUMENT_TYPES = frozenset(APPROVED_MASTERS)

BLOCK_UNKNOWN_DOCUMENT_TYPE = "UNKNOWN_GOVERNED_DOCUMENT_TYPE"
BLOCK_MISSING_MASTER = "MISSING_APPROVED_MASTER"
BLOCK_MASTER_SHA_MISMATCH = "APPROVED_MASTER_SHA_MISMATCH"
BLOCK_ALTERNATE_WRITER = "ALTERNATE_WRITER_FOR_GOVERNED_DOCUMENT"
BLOCK_TABLE_NOT_IN_MASTER = "TABLE_NOT_IN_MASTER"
BLOCK_TOKEN_NOT_IN_MASTER = "TOKEN_NOT_IN_MASTER"
BLOCK_UNRESOLVED_PLACEHOLDER = "UNRESOLVED_MASTER_PLACEHOLDER"


class ApprovedMasterError(ValueError):
    def __init__(self, block_code: str, message: str = ""):
        super().__init__(f"{block_code}: {message}" if message else block_code)
        self.block_code = block_code


def master_for(document_type: str) -> ApprovedMaster:
    """The one approved master for a governed document type. There is no alternative."""
    try:
        return APPROVED_MASTERS[document_type]
    except KeyError:
        raise ApprovedMasterError(BLOCK_UNKNOWN_DOCUMENT_TYPE, f"{document_type!r} is not a governed document type")


def assert_governed_route(document_type: str, writer: str) -> None:
    """Refuse any writer other than this module for a governed document type."""
    if document_type in GOVERNED_DOCUMENT_TYPES and writer != __name__:
        raise ApprovedMasterError(BLOCK_ALTERNATE_WRITER, f"{document_type} must be produced from approved master "
                                  f"{APPROVED_MASTERS[document_type].family} ({__name__}), not by {writer}")


def master_dir() -> Path:
    configured = os.environ.get(MASTER_DIR_ENV, "").strip()
    try:
        from flask import current_app

        configured = current_app.config.get("APPROVED_MASTER_DIR") or configured
    except RuntimeError:
        pass
    return Path(configured) if configured else DEFAULT_MASTER_DIR


def load_master_copy(document_type: str, directory: Optional[Path] = None) -> bytes:
    master = master_for(document_type)
    path = Path(directory or master_dir()) / master.filename
    if not path.is_file():
        raise ApprovedMasterError(BLOCK_MISSING_MASTER, f"approved master {master.family} not found at {path}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != master.sha256:
        raise ApprovedMasterError(BLOCK_MASTER_SHA_MISMATCH, f"{path} is not the approved master {master.family}")
    return bytes(data)


# ---------------------------------------------------------------------------------------------- population
def _text(element) -> str:
    return "".join(node.text or "" for node in element.iter() if node.tag.endswith("}t"))


def _replace_in_paragraph(paragraph, old: str, new: str) -> bool:
    """Replace inside the runs, keeping each run's own formatting."""
    if old not in paragraph.text:
        return False
    for run in paragraph.runs:
        if old in run.text:
            run.text = run.text.replace(old, new)
            return True
    # The token spans runs: put the whole new text in the first run, keeping that run's formatting.
    full = paragraph.text.replace(old, new)
    runs = paragraph.runs
    runs[0].text = full
    for run in runs[1:]:
        run.text = ""
    return True


def _all_paragraphs(document) -> Iterable:
    yield from document.paragraphs
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs
    for section in document.sections:
        for part in (section.header, section.footer, section.first_page_header, section.first_page_footer):
            yield from part.paragraphs
            for table in part.tables:
                for row in table.rows:
                    for cell in row.cells:
                        yield from cell.paragraphs


def _set_cell(cell, value: str) -> None:
    paragraph = cell.paragraphs[0]
    runs = paragraph.runs
    if runs:
        runs[0].text = value
        for run in runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(value)
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


def _table_by_header(document, header: Sequence[str]):
    for table in document.tables:
        if [c.text.strip() for c in table.rows[0].cells] == list(header):
            return table
    raise ApprovedMasterError(BLOCK_TABLE_NOT_IN_MASTER, f"no table with header {list(header)} in the master")


def _fill_table(table, rows: Sequence[Sequence[str]]) -> None:
    template = table.rows[1]._tr if len(table.rows) > 1 else None
    if template is None:
        raise ApprovedMasterError(BLOCK_TABLE_NOT_IN_MASTER, "master table has no data row to repeat")
    for _ in range(len(rows) - (len(table.rows) - 1)):
        table._tbl.append(copy.deepcopy(template))  # a copy of the master's own row
    for row_xml in list(table._tbl.findall("{*}tr"))[1 + len(rows):]:
        table._tbl.remove(row_xml)  # unused placeholder rows
    for row, values in zip(table.rows[1:], rows):
        if len(values) != len(row.cells):
            raise ApprovedMasterError(BLOCK_TABLE_NOT_IN_MASTER, f"row {list(values)} does not match the master columns")
        for cell, value in zip(row.cells, values):
            _set_cell(cell, value)


def _fill_bullets(document, bullets: Sequence[str]) -> None:
    """The master's bullet list takes the project's items. Items keep the formatting of the master's list
    items; the master's closing bullet (the last one) keeps its own formatting and stays last."""
    existing = [p for p in document.paragraphs if p.text.startswith("•")]
    if len(existing) < 2:
        raise ApprovedMasterError(BLOCK_TABLE_NOT_IN_MASTER, "the master has no bullet list")
    items, closing = list(bullets[:-1]), bullets[-1]
    body = existing[:-1]
    anchor = body[-1]._p
    for _ in range(len(items) - len(body)):
        clone = copy.deepcopy(body[-1]._p)  # a copy of the master's own list item
        anchor.addnext(clone)
        anchor = clone
    current = [p for p in document.paragraphs if p.text.startswith("•")]
    for paragraph in current[len(items):-1]:
        paragraph._p.getparent().remove(paragraph._p)
    current = [p for p in document.paragraphs if p.text.startswith("•")]
    for paragraph, text in zip(current, items + [closing]):
        runs = paragraph.runs
        runs[0].text = "• " + text
        for run in runs[1:]:
            run.text = ""


def populate(document_type: str, *, tokens: dict, tables: dict, bullets: Optional[Sequence[str]] = None,
             directory: Optional[Path] = None) -> bytes:
    """Populate a byte copy of the approved master. Returns DOCX bytes."""
    from docx import Document

    document = Document(BytesIO(load_master_copy(document_type, directory)))
    for token, value in tokens.items():
        if not any(_replace_in_paragraph(p, token, value) for p in list(_all_paragraphs(document))):
            raise ApprovedMasterError(BLOCK_TOKEN_NOT_IN_MASTER, f"{token!r} is not in master {master_for(document_type).family}")
        for paragraph in list(_all_paragraphs(document)):
            while token in paragraph.text and _replace_in_paragraph(paragraph, token, value):
                pass
    for header, rows in tables.items():
        _fill_table(_table_by_header(document, header), rows)
    if bullets is not None:
        _fill_bullets(document, bullets)
    for table in document.tables:
        for row in table.rows[1:]:
            if all(c.text.strip() == PLACEHOLDER for c in row.cells):
                raise ApprovedMasterError(BLOCK_UNRESOLVED_PLACEHOLDER, "a master table was left unpopulated")
    out = BytesIO()
    document.save(out)
    return out.getvalue()


def render_pdf(docx_bytes: bytes) -> bytes:
    from app.services.signing_docx_pdf import convert_docx_to_pdf

    result = convert_docx_to_pdf(docx_bytes, source_docx_sha256=hashlib.sha256(docx_bytes).hexdigest())
    pdf = getattr(result, "pdf_bytes", None)
    if not pdf:
        raise ApprovedMasterError("PDF_CONVERSION_FAILED", getattr(result, "block_code", "") or "LibreOffice conversion failed")
    return pdf


def styles_sha256(docx_bytes: bytes) -> str:
    """SHA-256 of word/styles.xml: a populated document keeps the master's styles byte for byte."""
    import zipfile

    with zipfile.ZipFile(BytesIO(docx_bytes)) as archive:
        return hashlib.sha256(archive.read("word/styles.xml")).hexdigest()
