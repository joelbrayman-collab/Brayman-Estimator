"""PROOF ONLY. Run the QCAD Professional sheet from a governed specification.

QCAD stays outside the application process. This module is not imported by Flask.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from tools.qcad_proof.specification import drawing_specification

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("qcad_sheet.js")
QCAD = Path(
    os.environ.get(
        "QCAD_BIN",
        "/Volumes/qcad-3.33.1-trial-macos-13-26-qt6-arm64/QCAD.app/Contents/MacOS/QCAD",
    )
)
DWG2PDF = Path(
    os.environ.get(
        "QCAD_DWG2PDF",
        "/Volumes/qcad-3.33.1-trial-macos-13-26-qt6-arm64/QCAD.app/Contents/Resources/dwg2pdf",
    )
)


def write_specification(path: Path, omit_relationship_ids=()) -> dict:
    packet = drawing_specification(omit_relationship_ids=omit_relationship_ids)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    return packet


def render(spec_path: Path, dxf_path: Path, pdf_path: Path, log_path: Path) -> None:
    env = os.environ.copy()
    env["QCAD_PROOF_SPEC"] = str(spec_path)
    env["QCAD_PROOF_DXF"] = str(dxf_path)
    env["QCAD_PROOF_LOG"] = str(log_path)
    log_path.write_text("")
    if dxf_path.exists():
        dxf_path.unlink()
    drawing = subprocess.Popen(
        [str(QCAD), "-no-gui", "-allow-multiple-instances", "-exec", str(SCRIPT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = drawing.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        drawing.kill()
        stdout, stderr = drawing.communicate()
    log_path.write_text(log_path.read_text() + "\n--- qcad stderr ---\n" + (stderr or "")[-4000:])
    if "exported " not in log_path.read_text() or not dxf_path.exists():
        raise RuntimeError(f"QCAD did not write {dxf_path}. Log: {log_path}")
    plotted = subprocess.run(
        [
            str(DWG2PDF),
            "-f",
            "-flat",
            "-n",
            "-block=S-1",
            "-p",
            "431.8x279.4",
            "-o",
            str(pdf_path),
            str(dxf_path),
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    log_path.write_text(log_path.read_text() + "\n--- dwg2pdf ---\n" + plotted.stdout[-2000:] + plotted.stderr[-2000:])
    if not pdf_path.exists():
        raise RuntimeError(f"dwg2pdf did not write {pdf_path}. Log: {log_path}")
