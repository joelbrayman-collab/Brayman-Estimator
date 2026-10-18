#!/usr/bin/env python3
"""Guarded restoration of the 19 September signing files to the live disk (prepared 18 Oct 2026).

NOT RUN. Each stage is separate; only `apply` changes production, and it refuses to run without
Joel's written authorization text. Runs on the office Mac (system Python, SSH key for Render).

The live database has 14 frozen and 5 executed signing records from the 14-15 Sep 2026 synthetic
UAT whose files were never copied when the hosted database was seeded from the Mac on 25 Sep.
The files are on the Mac in ~/Desktop/Brayman-Estimator/instance/signing_artifacts/ORG-001/.
Inventory with the recorded SHA-256 of each: september_signing_files.tsv.

  stage        Mac only. Copy each file to ~/CalibraytAI-Office/signing-restore/ and check it
               against the SHA-256 recorded in the database. Files iCloud keeps only in the
               cloud are skipped unless --download-from-icloud is given; a file downloaded that
               way is sent back to the cloud afterwards (brctl evict) so the Desktop is as before.
  verify-live  Read-only on the live instance: for each record, does the database still hold the
               same SHA-256, and is the file present (it should not be)?
  apply        PRODUCTION WRITE. Needs: every file staged and verified, verify-live showing every
               file absent, and --authorization "<Joel's authorization text>". For each file it
               uploads to a temporary folder on the instance, checks the SHA-256 there, then links
               it into place only if nothing is there yet (never overwrites), and checks again.
               Then runs verify-live. No database row is changed.

Rollback for apply: delete only the 19 files it added (listed in its log); the records are as
they were before, and nothing else is touched.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
INVENTORY = Path(os.environ.get("RESTORE_INVENTORY", str(HERE / "september_signing_files.tsv")))
HOME = Path(os.environ.get("RESTORE_HOME", str(Path.home())))
SOURCE = HOME / "Desktop" / "Brayman-Estimator" / "instance" / "signing_artifacts"
STAGING = HOME / "CalibraytAI-Office" / "signing-restore"
HOST = "srv-dar95mh42hec73df4rug@ssh.virginia.render.com"
SSH = ["ssh", "-o", "UpdateHostKeys=no"]
SCP = ["scp", "-o", "UpdateHostKeys=no", "-q"]
REMOTE_ROOT = "/opt/render/project/src/instance/signing_artifacts"
REMOTE_PY = (
    "cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; "
    "else PY=$(command -v python3); fi; $PY -"
)
SF_DATALESS = getattr(stat, "SF_DATALESS", 0x40000000)


def inventory():
    with INVENTORY.open() as handle:
        rows = [line for line in handle if not line.startswith("#")]
    return list(csv.DictReader(rows, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def cloud_only(path: Path) -> bool:
    return bool(getattr(path.stat(), "st_flags", 0) & SF_DATALESS)


def stage(args) -> int:
    rows = inventory()
    ok = skipped = problems = 0
    for row in rows:
        key, want = row["storage_key"], row["sha256"]
        source, target = SOURCE / key, STAGING / key
        if target.exists():
            if sha256(target) == want:
                ok += 1
                print(f"  [staged already, verified] {key}")
            else:
                problems += 1
                print(f"  [STOP] staged copy differs from the record: {target} (not overwritten)")
            continue
        if not source.exists():
            problems += 1
            print(f"  [MISSING on the Mac] {key}")
            continue
        was_cloud = cloud_only(source)
        if was_cloud and not args.download_from_icloud:
            skipped += 1
            print(f"  [iCloud only, skipped] {key}")
            continue
        try:
            have = sha256(source)  # reading a cloud-only file downloads it
        except OSError as exc:
            problems += 1
            print(f"  [STOP] cannot read {key}: {exc.strerror}")
            continue
        if have != want:
            problems += 1
            print(f"  [STOP] {key} on the Mac does not match the database record ({have})")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha256(target) != want:
            problems += 1
            print(f"  [STOP] staged copy of {key} does not match")
            continue
        if was_cloud:
            subprocess.run(["brctl", "evict", str(source)], check=False, capture_output=True)
        ok += 1
        print(f"  [staged, verified] {key}{' (downloaded from iCloud, then evicted again)' if was_cloud else ''}")
    print(f"STAGE verified={ok} of {len(rows)} skipped_icloud={skipped} problems={problems}")
    return 0 if ok == len(rows) else 1


REMOTE_VERIFY = r'''
import hashlib, os, sqlite3, sys
uri = os.environ.get("CALIBRAYTAI_DATABASE_URI", "")
db = uri[len("sqlite:///"):] if uri.startswith("sqlite:///") else ""
root = os.path.join(os.path.dirname(db), "signing_artifacts")
c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
rows = {}
for table in ("signing_frozen_artifacts", "signing_executed_artifacts"):
    for key, sha in c.execute("SELECT storage_key, sha256 FROM " + table):
        rows[key] = sha
for line in sys.stdin.read().split("\n"):
    if not line.strip():
        continue
    key, want = line.split("\t")
    path = os.path.join(root, key)
    present = os.path.isfile(path)
    match = present and hashlib.sha256(open(path, "rb").read()).hexdigest() == want
    print("ROW key=%s db_sha_matches=%s file_present=%s file_matches=%s" % (key, rows.get(key) == want, present, match))
print("VERIFY=done")
'''


def _remote_verify(rows):
    payload = "\n".join(f"{r['storage_key']}\t{r['sha256']}" for r in rows) + "\n"
    script = REMOTE_VERIFY.replace("sys.stdin.read()", repr(payload))
    result = subprocess.run(SSH + [HOST, REMOTE_PY], input=script, capture_output=True, text=True)
    lines = [line for line in result.stdout.splitlines() if line.startswith("ROW ")]
    return result, lines


def verify_live(_args) -> int:
    rows = inventory()
    result, lines = _remote_verify(rows)
    for line in lines:
        print("  " + line)
    if "VERIFY=done" not in result.stdout or len(lines) != len(rows):
        print("VERIFY-LIVE could not read the live instance:\n" + result.stderr[-2000:])
        return 1
    db_ok = all("db_sha_matches=True" in line for line in lines)
    present = sum("file_present=True" in line for line in lines)
    matching = sum("file_matches=True" in line for line in lines)
    print(f"VERIFY-LIVE records_match={db_ok} files_present={present} files_matching={matching} of {len(rows)}")
    return 0 if db_ok else 1


REMOTE_PLACE = r'''
import hashlib, os, sys
incoming, final, want = sys.argv[1], sys.argv[2], sys.argv[3]
if hashlib.sha256(open(incoming, "rb").read()).hexdigest() != want:
    print("PLACE=FAIL incoming checksum differs"); sys.exit(1)
os.makedirs(os.path.dirname(final), exist_ok=True)
try:
    os.link(incoming, final)  # fails if anything is already there: never overwrites
except FileExistsError:
    print("PLACE=FAIL a file is already at the destination; nothing changed"); sys.exit(1)
os.unlink(incoming)
if hashlib.sha256(open(final, "rb").read()).hexdigest() != want:
    print("PLACE=FAIL placed file checksum differs"); sys.exit(1)
print("PLACE=ok")
'''


def apply(args) -> int:
    if not (args.authorization or "").strip():
        print("REFUSED: apply changes production. It needs --authorization with Joel's written authorization.")
        return 2
    rows = inventory()
    for row in rows:
        target = STAGING / row["storage_key"]
        if not target.exists() or sha256(target) != row["sha256"]:
            print(f"REFUSED: {row['storage_key']} is not staged and verified; run stage first.")
            return 2
    result, lines = _remote_verify(rows)
    if len(lines) != len(rows) or not all("db_sha_matches=True" in l and "file_present=False" in l for l in lines):
        print("REFUSED: the live records changed, or a file is already present. Nothing was changed.")
        for line in lines:
            print("  " + line)
        return 2
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = STAGING / f"apply-{stamp}.log"
    incoming_dir = f"{REMOTE_ROOT}/.incoming-{stamp}"
    with log.open("w") as handle:
        handle.write(f"authorization: {args.authorization}\n")
        for row in rows:
            key, want = row["storage_key"], row["sha256"]
            incoming = f"{incoming_dir}/{os.path.basename(key)}"
            final = f"{REMOTE_ROOT}/{key}"
            made = subprocess.run(SSH + ["-n", HOST, f"mkdir -p '{incoming_dir}'"], capture_output=True)
            sent = subprocess.run(SCP + [str(STAGING / key), f"{HOST}:{incoming}"], capture_output=True)
            if made.returncode or sent.returncode:
                print(f"STOP: upload of {key} failed; files placed so far are in {log}")
                return 1
            placed = subprocess.run(
                SSH + [HOST, REMOTE_PY.replace("$PY -", f"$PY - '{incoming}' '{final}' '{want}'")],
                input=REMOTE_PLACE, capture_output=True, text=True,
            )
            if "PLACE=ok" not in placed.stdout:
                print(f"STOP at {key}: {placed.stdout.strip()} {placed.stderr.strip()[-300:]}")
                return 1
            handle.write(f"placed {final} {want}\n")
            print(f"  [placed, verified] {key}")
    print(f"APPLY done; log {log}. Re-checking:")
    return verify_live(args)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage", required=True)
    staging = sub.add_parser("stage")
    staging.add_argument("--download-from-icloud", action="store_true")
    sub.add_parser("verify-live")
    applying = sub.add_parser("apply")
    applying.add_argument("--authorization", default="")
    args = parser.parse_args()
    return {"stage": stage, "verify-live": verify_live, "apply": apply}[args.stage](args)


if __name__ == "__main__":
    sys.exit(main())
