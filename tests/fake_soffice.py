"""Minimal LibreOffice stand-in for SIGN-E subprocess tests. Writes %PDF only."""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if "--version" in argv:
        print("LibreOffice 24.8.0.0 40(Build:1) fake-soffice")
        return 0
    outdir = None
    source = None
    for index, arg in enumerate(argv):
        if arg == "--outdir" and index + 1 < len(argv):
            outdir = argv[index + 1]
        elif arg.endswith(".docx"):
            source = arg
    if not outdir or not source:
        return 1
    pdf_path = Path(outdir) / (Path(source).stem + ".pdf")
    pdf_path.write_bytes(b"%PDF-1.4\nfake-soffice\n%%EOF\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
