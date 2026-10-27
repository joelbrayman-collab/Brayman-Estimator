"""The interim J1 case writer cannot produce a current governed document (Joel, 27 Oct 2026).

It is kept only to reproduce the historical 1 Oct 2026 J1 issue. Current documents come from the approved
masters (app/services/approved_masters.py; tests/test_approved_master_governance.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TAKEOFF = Path(__file__).resolve().parents[1] / "docs/estimating-cases/2026/linda-bushel-pool-deck/takeoff"


def test_interim_writer_refuses_any_issue_other_than_the_historical_j1(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(TAKEOFF))
    import branded_issue_pdf

    source = tmp_path / "estimate.md"
    source.write_text("# Estimate\n\nSynthetic.\n", encoding="utf-8")
    for title, date in (("CUSTOMER-FACING ESTIMATE", "27 Oct 2026"), ("INTERNAL COST FOR BEN", "28 Oct 2026"),
                        ("LABOUR CALCULATION DETAIL", "2 Oct 2026")):
        with pytest.raises(branded_issue_pdf.InterimWriterRetired) as raised:
            branded_issue_pdf.build(source, tmp_path / "out.pdf", title, "status", footer_date=date)
        assert raised.value.block_code == "ALTERNATE_WRITER_FOR_GOVERNED_DOCUMENT"
        assert not (tmp_path / "out.pdf").exists()
    assert branded_issue_pdf.HISTORICAL_ISSUE_DATES == {"1 Oct 2026"}


def test_the_27_oct_issue_scripts_do_not_use_the_interim_writer():
    for name in ("issue_2026_10_27.py", "issue_masters_2026_10_27.py", "price_2026_10_27.py"):
        text = (TAKEOFF / name).read_text(encoding="utf-8")
        assert "import branded_issue_pdf" not in text and "from branded_issue_pdf" not in text, name
    assert "approved_masters" in (TAKEOFF / "issue_masters_2026_10_27.py").read_text(encoding="utf-8")
