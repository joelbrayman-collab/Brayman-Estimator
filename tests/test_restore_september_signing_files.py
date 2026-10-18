"""The guarded restoration of the September signing files (prepared 18 Oct 2026, not run).

Exercised end to end against a stand-in for the live instance: ssh and scp are replaced by
local scripts that run the same commands on a temporary folder and database. Synthetic files.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "release" / "restore_september_signing_files.py"

SSH_STUB = """#!/bin/bash
cmd="${@: -1}"
cmd="${cmd//\\/opt\\/render\\/project\\/src/$FAKE_ROOT}"
cd "$FAKE_ROOT" && CALIBRAYTAI_DATABASE_URI="sqlite:///$FAKE_ROOT/instance/brayman_estimator.db" bash -c "$cmd"
"""
SCP_STUB = """#!/bin/bash
src="${@: -2:1}"; dst="${@: -1}"
dst="${dst#*:}"; dst="${dst//\\/opt\\/render\\/project\\/src/$FAKE_ROOT}"
cp "$src" "$dst"
"""


def _world(tmp_path, count=3):
    home, live, stubs = tmp_path / "home", tmp_path / "live", tmp_path / "bin"
    source = home / "Desktop" / "Brayman-Estimator" / "instance" / "signing_artifacts" / "ORG-001"
    source.mkdir(parents=True)
    (live / "instance").mkdir(parents=True)
    stubs.mkdir()
    (stubs / "ssh").write_text(SSH_STUB)
    (stubs / "scp").write_text(SCP_STUB)
    for stub in stubs.iterdir():
        stub.chmod(0o755)
    db = sqlite3.connect(live / "instance" / "brayman_estimator.db")
    db.execute("CREATE TABLE signing_frozen_artifacts (storage_key TEXT, sha256 TEXT)")
    db.execute("CREATE TABLE signing_executed_artifacts (storage_key TEXT, sha256 TEXT)")
    lines = ["table\tid\tstorage_key\tsha256\tmac_state_18oct"]
    for index in range(count):
        data = f"%PDF-1.4 synthetic september file {index}".encode()
        sha = hashlib.sha256(data).hexdigest()
        key = f"ORG-001/{sha}.pdf"
        (source / f"{sha}.pdf").write_bytes(data)
        db.execute("INSERT INTO signing_frozen_artifacts VALUES (?, ?)", (key, sha))
        lines.append(f"frozen\t{index + 1}\t{key}\t{sha}\tlocal")
    db.commit()
    db.close()
    inventory = tmp_path / "inventory.tsv"
    inventory.write_text("# synthetic\n" + "\n".join(lines) + "\n")
    env = {
        **os.environ,
        "PATH": f"{stubs}:{os.environ['PATH']}",
        "FAKE_ROOT": str(live),
        "RESTORE_HOME": str(home),
        "RESTORE_INVENTORY": str(inventory),
    }
    return env, home, live


def _run(env, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)


def test_apply_refuses_without_authorization_or_staging(tmp_path):
    env, _home, live = _world(tmp_path)
    refused = _run(env, "apply")
    assert refused.returncode == 2 and "needs --authorization" in refused.stdout
    unstaged = _run(env, "apply", "--authorization", "test")
    assert unstaged.returncode == 2 and "not staged" in unstaged.stdout
    assert not (live / "instance" / "signing_artifacts").exists()


def test_stage_verify_apply_places_each_file_once_and_verified(tmp_path):
    env, home, live = _world(tmp_path)
    staged = _run(env, "stage")
    assert staged.returncode == 0 and "STAGE verified=3 of 3" in staged.stdout, staged.stdout
    before = _run(env, "verify-live")
    assert "records_match=True files_present=0" in before.stdout, before.stdout + before.stderr
    applied = _run(env, "apply", "--authorization", "synthetic test authorization")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert "records_match=True files_present=3 files_matching=3 of 3" in applied.stdout
    placed = sorted((live / "instance" / "signing_artifacts" / "ORG-001").iterdir())
    assert len(placed) == 3
    for path in placed:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == path.stem
    assert not any(p.is_file() for p in (live / "instance" / "signing_artifacts").glob(".incoming-*/*"))
    again = _run(env, "apply", "--authorization", "synthetic test authorization")
    assert again.returncode == 2 and "already present" in again.stdout  # never twice, never overwrites


def test_apply_never_overwrites_a_file_already_on_the_instance(tmp_path):
    env, _home, live = _world(tmp_path)
    assert _run(env, "stage").returncode == 0
    existing_dir = live / "instance" / "signing_artifacts" / "ORG-001"
    existing_dir.mkdir(parents=True)
    victim = (tmp_path / "inventory.tsv").read_text().splitlines()[2].split("\t")[2]
    (live / "instance" / "signing_artifacts" / victim).write_bytes(b"something else")
    refused = _run(env, "apply", "--authorization", "synthetic test authorization")
    assert refused.returncode == 2 and "Nothing was changed" in refused.stdout
    assert (live / "instance" / "signing_artifacts" / victim).read_bytes() == b"something else"
    assert len(list(existing_dir.iterdir())) == 1


def test_a_mac_file_that_does_not_match_its_record_is_not_staged(tmp_path):
    env, home, _live = _world(tmp_path)
    source = home / "Desktop" / "Brayman-Estimator" / "instance" / "signing_artifacts" / "ORG-001"
    first = sorted(source.iterdir())[0]
    first.write_bytes(b"altered")
    staged = _run(env, "stage")
    assert staged.returncode == 1 and "does not match the database record" in staged.stdout


def test_the_real_inventory_lists_the_nineteen_records():
    rows = [line.split("\t") for line in (ROOT / "tools" / "release" / "september_signing_files.tsv").read_text().splitlines()
            if line and not line.startswith("#")][1:]
    assert len(rows) == 19
    assert sum(r[0] == "frozen" for r in rows) == 14 and sum(r[0] == "executed" for r in rows) == 5
    for table, _id, key, sha, state in rows:
        assert key.startswith("ORG-001/") and key.split("/")[1].split(".")[0] == sha
        assert state in {"local", "icloud"}
    assert sum(r[4] == "icloud" for r in rows) == 11
