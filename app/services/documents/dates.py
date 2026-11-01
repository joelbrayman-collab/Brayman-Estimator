"""Date candidates in document text, classified by the words just before them (deterministic).

Every candidate is a PROPOSAL shown to a person ("We found these dates — confirm or change"); nothing acts on it
until it is confirmed. Numeric dates whose day and month could be swapped (03/04/2027) are proposed both ways and
marked ambiguous.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.models.documents import (
    DATE_EFFECTIVE,
    DATE_EXPIRES,
    DATE_INSPECTION_DUE,
    DATE_ISSUED,
    DATE_RENEWAL_DUE,
    DATE_WARRANTY_ENDS,
)

EXTRACTOR_VERSION = "calibrayt-docs-dates-1"
MAX_PER_KIND = 2

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
     "december"], start=1)}
_MONTHS.update({k[:3]: v for k, v in list(_MONTHS.items())})
_MONTHS["sept"] = 9
_MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"

_PATTERNS = (
    ("iso", re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")),
    ("numeric", re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b")),
    ("mdy", re.compile(_MON + r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I)),
    ("dmy", re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + _MON + r",?\s+(\d{4})\b", re.I)),
)

_SENTENCE_BREAK = re.compile(r"(?:[.;]\s+|\n)")

# Order matters: the first cue that matches the text before a date decides its kind.
_CUES = (
    (DATE_WARRANTY_ENDS, re.compile(r"warranty[^.]{0,40}(until|expir|ends?|end date|through|to)|warranty period", re.I)),
    (DATE_INSPECTION_DUE, re.compile(r"next inspection|inspection due|re-?inspect|due for inspection", re.I)),
    (DATE_RENEWAL_DUE, re.compile(r"renew", re.I)),
    (DATE_EXPIRES, re.compile(r"expir|valid until|valid to|valid thru|valid through|end date|policy period[^.]{0,40}to"
                              r"|clearance[^.]{0,40}valid|good until|\bto\s*$|until\s*$", re.I)),
    (DATE_EFFECTIVE, re.compile(r"effective|valid from|start date|commenc|policy period|from\s*$", re.I)),
    (DATE_ISSUED, re.compile(r"issued|date of issue|issue date|dated", re.I)),
)


@dataclass(frozen=True)
class DateCandidate:
    kind: str
    value: date
    evidence: str
    page: Optional[int]
    ambiguous: bool = False


def _mk(y, m, d) -> Optional[date]:
    try:
        return date(int(y), int(m), int(d))
    except (TypeError, ValueError):
        return None


def _parse(kind, match) -> list:
    g = match.groups()
    if kind == "iso":
        value = _mk(g[0], g[1], g[2])
        return [(value, False)] if value else []
    if kind == "mdy":
        value = _mk(g[2], _MONTHS.get(g[0].lower().rstrip(".")[:3]), g[1])
        return [(value, False)] if value else []
    if kind == "dmy":
        value = _mk(g[2], _MONTHS.get(g[1].lower().rstrip(".")[:3]), g[0])
        return [(value, False)] if value else []
    a, b, y = int(g[0]), int(g[1]), int(g[2])
    if a > 12 and b <= 12:
        value = _mk(y, b, a)
        return [(value, False)] if value else []
    if b > 12 and a <= 12:
        value = _mk(y, a, b)
        return [(value, False)] if value else []
    if a == b:
        value = _mk(y, a, b)
        return [(value, False)] if value else []
    out = []
    for value in (_mk(y, b, a), _mk(y, a, b)):  # day/month first (Canadian forms), then month/day
        if value:
            out.append((value, True))
    return out


def _classify(before: str) -> Optional[str]:
    for kind, pattern in _CUES:
        if pattern.search(before):
            return kind
    return None


def find_dates(pages, *, today: Optional[date] = None) -> list:
    """Candidates from text pages ([str] or str). At most two per kind; out-of-range dates dropped."""
    today = today or date.today()
    earliest = today - timedelta(days=366)
    latest = today + timedelta(days=365 * 25)
    if isinstance(pages, str):
        pages = [pages]
    found = []
    seen = set()
    for page_index, page_text in enumerate(pages or []):
        page_text = page_text or ""
        for kind_name, pattern in _PATTERNS:
            for match in pattern.finditer(page_text):
                before = page_text[max(0, match.start() - 60):match.start()]
                before = _SENTENCE_BREAK.split(before)[-1]  # cue words only from the date's own sentence or line
                kind = _classify(before)
                if kind is None:
                    continue
                for value, ambiguous in _parse(kind_name, match):
                    if value is None or value < earliest or value > latest:
                        continue
                    key = (kind, value)
                    if key in seen:
                        continue
                    seen.add(key)
                    evidence = " ".join((before + match.group(0)).split())[-200:]
                    found.append(DateCandidate(kind, value, evidence, page_index if len(pages) > 1 else None,
                                               ambiguous))
    out = []
    by_kind: dict = {}
    for candidate in found:
        by_kind.setdefault(candidate.kind, []).append(candidate)
    for kind, rows in by_kind.items():
        if kind == DATE_EXPIRES:
            rows = sorted(rows, key=lambda c: c.value, reverse=True)  # latest expiry first
        out.extend(rows[:MAX_PER_KIND])
    return out
