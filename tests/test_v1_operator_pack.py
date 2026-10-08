"""The V1 operating pack matches the office Ben is told to use."""

from pathlib import Path

import importlib.util

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "render_v1_operator_pack",
    ROOT / "docs/operations/render_v1_operator_pack.py",
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
render_pack = _MODULE.render_pack
GUIDE = ROOT / "docs/operations/v1-operator-recovery-guide.md"
FIRST = ROOT / "docs/operations/v1-first-day-checklist.md"
BACKUP = ROOT / "docs/operations/v1-backup-restore-checklist.md"


def test_operator_pack_states_the_office_rules():
    guide = GUIDE.read_text(encoding="utf-8")
    first = FIRST.read_text(encoding="utf-8")
    backup = BACKUP.read_text(encoding="utf-8")
    assert "flask run --port 5001" in guide
    for text in (guide, first):
        assert "127.0.0.1:5001" in text
        assert "Family 05" in text
        assert "Production contract unavailable" in text
    assert "does not approve" in guide
    assert "h8c9d0e1f2a3" in guide
    assert "234a4eb7e9ddcfab07bf795fd7bfc23c61237ca7" in guide
    assert "https://calibryatai.onrender.com" in guide
    assert "Joel Brayman" in guide
    assert "v1-issue-log.md" in guide
    assert ".backup" in backup
    assert "PRAGMA integrity_check" in backup
    assert "Ben does not" in backup
    assert "empty office" in backup


def test_operator_pack_pdfs_keep_those_rules(tmp_path):
    written = render_pack(tmp_path)
    by_name = {path.name: path for path in written}
    first = PdfReader(str(by_name["v1-first-day-checklist.pdf"]))
    assert len(first.pages) == 1
    first_text = first.pages[0].extract_text()
    assert "Family 05" in first_text
    assert "127.0.0.1:5001" in first_text
    guide = PdfReader(str(by_name["v1-operator-recovery-guide.pdf"]))
    guide_text = "\n".join(page.extract_text() or "" for page in guide.pages)
    assert "Production contract unavailable" in guide_text
    assert "does not approve" in guide_text
    assert "h8c9d0e1f2a3" in guide_text
    backup = PdfReader(str(by_name["v1-backup-restore-checklist.pdf"]))
    backup_text = "\n".join(page.extract_text() or "" for page in backup.pages)
    assert "integrity_check" in backup_text
    assert "Ben does not" in backup_text
