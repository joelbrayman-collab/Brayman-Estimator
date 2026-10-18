#!/usr/bin/env python3
"""Copy the office backups and release working files out of the iCloud Desktop (Joel, 18 Oct 2026).

Runs on the office Mac with the system Python (/usr/bin/python3). It only ever COPIES:

  ~/Desktop/Brayman-office-backups/          -> ~/CalibraytAI-Office/office-backups/
  ~/Desktop/Brayman-Estimator/generated/     -> ~/CalibraytAI-Office/release-work/

~/CalibraytAI-Office is in the home folder, which iCloud Drive does not sync (only Desktop and
Documents are), so release runs and backups no longer depend on a file being downloaded.

Rules:
- Nothing is deleted, moved or changed in the source folders.
- An existing file at the destination is never overwritten. If it already holds the same bytes
  it is reported as already copied; if it differs, the run stops and reports it.
- Every copied file is checked by SHA-256 against its source; every .db file must also pass
  SQLite's integrity check (opened read-only).
- A file that iCloud has moved to the cloud (not downloaded on this Mac) is NOT downloaded:
  it is listed and left where it is. Downloading iCloud files to the Desktop is Joel's call.
- Each destination gets MANIFEST-<date>.sha256 listing what it holds.

Usage:  /usr/bin/python3 relocate_local_storage.py            (copy and verify)
        /usr/bin/python3 relocate_local_storage.py --check    (report only, copy nothing)
Exit 0 only when every local file is copied and verified.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import stat
import sys
import time
from pathlib import Path

HOME = Path(os.environ.get("RELOCATE_HOME", str(Path.home())))
DEST_ROOT = HOME / "CalibraytAI-Office"
PAIRS = [
    (HOME / "Desktop" / "Brayman-office-backups", DEST_ROOT / "office-backups"),
    (HOME / "Desktop" / "Brayman-Estimator" / "generated", DEST_ROOT / "release-work"),
]
SKIP_NAMES = {".DS_Store"}
SF_DATALESS = getattr(stat, "SF_DATALESS", 0x40000000)  # macOS: content is in iCloud only


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def in_cloud_only(path: Path) -> bool:
    flags = getattr(path.stat(), "st_flags", 0)
    return bool(flags & SF_DATALESS)


def sqlite_ok(path: Path) -> bool:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        connection.close()


def main() -> int:
    check_only = "--check" in sys.argv[1:]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    problems = 0
    for source, dest in PAIRS:
        print(f"== {source}  ->  {dest}")
        if not source.is_dir():
            print(f"  [STOP] source folder not found: {source}")
            problems += 1
            continue
        copied = already = cloud = 0
        manifest = []
        if not check_only:
            dest.mkdir(parents=True, exist_ok=True)
        for path in sorted(source.rglob("*")):
            if path.is_dir() or path.name in SKIP_NAMES or path.is_symlink():
                continue
            relative = path.relative_to(source)
            target = dest / relative
            if in_cloud_only(path):
                cloud += 1
                print(f"  [iCloud only, not copied] {relative}")
                continue
            try:
                source_sha = sha256(path)
            except OSError as exc:  # e.g. an iCloud placeholder that cannot be read here
                cloud += 1
                print(f"  [not readable here, not copied: {exc.strerror}] {relative}")
                continue
            if target.exists():
                if sha256(target) == source_sha:
                    if target.suffix == ".db" and not sqlite_ok(target):
                        print(f"  [STOP] {relative}: SQLite integrity check failed on the existing copy")
                        problems += 1
                        continue
                    already += 1
                    manifest.append(f"{source_sha}  {relative}")
                    continue
                print(f"  [STOP] {target} exists with different bytes; nothing overwritten")
                problems += 1
                continue
            if check_only:
                print(f"  [would copy] {relative}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)  # copies bytes and timestamps; the source is untouched
            if sha256(target) != source_sha:
                print(f"  [STOP] copy of {relative} does not match its source")
                problems += 1
                continue
            if target.suffix == ".db" and not sqlite_ok(target):
                print(f"  [STOP] {relative}: SQLite integrity check failed on the copy")
                problems += 1
                continue
            copied += 1
            manifest.append(f"{source_sha}  {relative}")
        if not check_only and manifest:
            (dest / f"MANIFEST-{stamp}.sha256").write_text("\n".join(manifest) + "\n")
        databases = sum(1 for line in manifest if line.endswith(".db"))
        print(
            f"  copied={copied} already_there={already} verified_total={len(manifest)} "
            f"databases_integrity_ok={databases} left_in_icloud={cloud}"
        )
    if check_only:
        print("CHECK ONLY: nothing was copied.")
        return 1 if problems else 0
    if problems:
        print(f"NOT COMPLETE: {problems} problem(s) above. Originals are untouched.")
        return 1
    print(f"DONE. Everything local is copied and verified under {DEST_ROOT}. Originals are untouched.")
    print("Release scripts use the new folders from the next release (tools/release/).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
