"""Suggestions read from a plan's title block (Joel, 15 Nov 2026).

Dropping a plan on Set Up This Project offers the job address, the designer and the plan version it can find in the
text of the first sheets. These are SUGGESTIONS for the person to check: they fill only empty boxes, are marked as read
from the plan, and nothing is saved until the person creates the project. Deterministic text matching only: no OCR, no
external service, no AI. A value that is not clearly there is left out, never guessed.
"""

from __future__ import annotations

import re
from io import BytesIO
from typing import Dict, List, Optional

from pypdf import PdfReader

MAX_PAGES = 3  # the title block is on the first sheets
POSTAL = re.compile(r"\b([ABCEGHJ-NPRSTVXY]\d[A-Z])[ -]?(\d[A-Z]\d)\b")
STREET_TYPES = (
    r"Road|Rd|Street|St|Avenue|Ave|Drive|Dr|Lane|Ln|Court|Ct|Crescent|Cres|Way|Line|Boulevard|Blvd|Concession|"
    r"Trail|Circle|Cir|Place|Pl|Terrace|Terr|Highway|Hwy|Side Road|Sideroad"
)
STREET = re.compile(
    rf"\b(\d{{1,6}}[A-Za-z]?\s+(?:[A-Za-z0-9.'\-]+\s+){{0,4}}?(?:County\s+)?(?:{STREET_TYPES})\.?(?:\s+\d{{1,4}})?)\b",
    re.IGNORECASE,
)
DESIGNER = re.compile(
    r"(?:designed\s+by|drawn\s+by|drafted\s+by|designer|prepared\s+by|architect|engineer|design\s+by)\s*[:\-]\s*"
    r"([A-Za-z][A-Za-z0-9 .,&'\-]{2,60})",
    re.IGNORECASE,
)
VERSION = re.compile(
    r"(?:revision|rev\.?|issue|version)\s*(?:no\.?|number|#)?\s*[:#\-]?\s*([A-Za-z0-9][A-Za-z0-9.\-]{0,11})\b",
    re.IGNORECASE,
)
WORDS_NOT_A_VERSION = {"date", "by", "description", "for", "of", "the", "no", "and"}


def _page_lines(data: bytes) -> List[str]:
    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted and not reader.decrypt(""):
        return []
    lines: List[str] = []
    for page in list(reader.pages)[:MAX_PAGES]:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        lines.extend(line.strip() for line in text.splitlines() if line.strip())
    return lines


def _clean(value: str, *, keep_period: bool = False) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" ,;:-")
    return cleaned if keep_period else cleaned.rstrip(".")


def read_plan_details(data: bytes) -> Dict[str, Optional[str]]:
    """{street, municipality, province_state, postal_zip, designer, version}: each a clear match or None."""
    out: Dict[str, Optional[str]] = {key: None for key in
                                     ("street", "municipality", "province_state", "postal_zip", "designer", "version")}
    try:
        lines = _page_lines(data)
    except Exception:
        return out
    for index, line in enumerate(lines):
        if out["street"] is None:
            match = STREET.search(line)
            if match:
                out["street"] = _clean(match.group(1))
                rest = line[match.end():].strip(" ,")
                if not rest and index + 1 < len(lines):
                    rest = lines[index + 1]  # the town is on the next line of the title block
                town = re.split(r",|\bON\b|\bOntario\b|" + POSTAL.pattern, rest, maxsplit=1)[0]
                town = _clean(town)
                if town and re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{1,40}", town):
                    out["municipality"] = town
                if re.search(r"\bON\b|\bOntario\b", rest, re.IGNORECASE):
                    out["province_state"] = "Ontario"
        if out["postal_zip"] is None:
            match = POSTAL.search(line.upper())
            if match:
                out["postal_zip"] = f"{match.group(1)} {match.group(2)}"
        if out["designer"] is None:
            match = DESIGNER.search(line)
            if match:
                out["designer"] = _clean(match.group(1), keep_period=True)
        if out["version"] is None:
            match = VERSION.search(line)
            if match and match.group(1).lower() not in WORDS_NOT_A_VERSION:
                out["version"] = _clean(match.group(1)).upper()
    return out
