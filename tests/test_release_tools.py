"""The repository's release scripts keep every approved safeguard (technical cleanup, 18 Oct 2026).

These tests do not run a release. They read the scripts and check, on any machine, that the
gate still stops at READY_FOR_PUSH, never pushes or deploys, refuses a database change, requires
exact commits and a skip-free regression, and that the post-release check is read-only.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "tools" / "release"
GATE = RELEASE / "release_gate.sh"
POST = RELEASE / "postrelease_check.sh"

# Byte-identical to the helpers the 18 Oct Cal Phase 1 release verified by checksum before use.
PROVEN_HELPERS = {
    "hosted_preflight.py": "ea57a7374f2a4b9ed9247c4a9cd0aa4a9e545592d6bb8883c33294a839dbfc8c",
    "hosted_postcheck.py": "05653deeb6dd8ad58bf730bbe64addafef75fb18ab93586dc18930d849f6ddb6",
    "signing_readiness.py": "5fd93ffffed9313d0a48891c021b0f08c063ef2bdbada3034a36df26aa76c17c",
    "evidence_common.mjs": "6ae1562d2008f4edaf618ccc1cf9849d433eb3a202d05cf2394ca8deb69ba0f8",
    "evidence_employment_v11.mjs": "2e4f121deddfe475a66aeced6a72eb8cf0798d0d77f104f5d2a74f470bb95ebe",
    "evidence_trade_pages.mjs": "9962fe4b74983aaa14cb39117f49cdaaf892f7ab42a9fa4dd63b18a1756bb79c",
    "evidence_cal_find_it.mjs": "518f68ccbeb170c9631aaf579c52bcfde558412a32a3804544a2cec56d1ef179",
}


def _code(path: Path) -> str:
    """Script text without comment lines, so a safeguard must exist as code, not prose."""
    return "\n".join(
        line for line in path.read_text().splitlines() if not line.lstrip().startswith("#")
    )


def test_scripts_parse():
    for script in (GATE, POST, ROOT / "tools" / "setup_test_environment.sh"):
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_helpers_are_the_proven_bytes():
    for name, sha in PROVEN_HELPERS.items():
        assert hashlib.sha256((RELEASE / name).read_bytes()).hexdigest() == sha, name


def test_gate_never_pushes_or_deploys():
    for path in (GATE, POST):
        code = _code(path)
        assert not re.search(r"\bgit\s+(-C\s+\S+\s+)?push\b", code), path.name
        assert "trigger_deploy" not in code and "api.render.com" not in code, path.name
        assert "render deploys" not in code, path.name


def test_gate_stops_at_ready_for_push_after_every_gate():
    code = _code(GATE)
    order = [
        'refs/heads/main',  # GitHub main checked
        'RENDER_GIT_COMMIT',  # live instance checked
        "merge-base --is-ancestor \"$MAIN_BASE\"",  # fast-forward
        "-- migrations app/models",  # no database change
        "-c requirements-lock.txt",  # production's exact versions
        "-m pytest",  # complete regression
        "not skipped",  # no skipped test
        "test_contractor_workflow_e2e",  # end-to-end walk ran
        "evidence_cal_find_it.mjs",  # browser checks
        "evidence_calendar.mjs",  # the 12 calendar browser checks (gate total 57)
        "evidence_pro_desk.mjs",  # the 4 Supplier PRO Desk browser checks (gate total 61)
        "evidence_supplier_hub.mjs",  # the 14 Supplier Hub (Darcy) browser checks (gate total 75 before the roles walk)
        "evidence_roles.mjs",  # the 26 administrator, customer and isolation browser checks (gate total 101)
        "evidence_first_day.mjs",  # Ben's First Day: the 16 Getting started steps on a fresh synthetic company
        "evidence_training.mjs",  # the Training & Acceptance Centre on a local training site
        "evidence_workflow_map.mjs",  # the 9 Workflow Map checks (contractor, supplier, Field, Training Centre)
        "evidence_time_payroll.mjs",  # the 8 payroll-handoff checks: hours policy, QuickBooks Time (fake), banked hours
        "< tools/release/hosted_preflight.py",  # fresh backup
        "BACKUP_SHA256",
        "PRAGMA integrity_check",
        "< tools/release/signing_readiness.py",
        "READY_FOR_PUSH commit=",
    ]
    positions = [code.find(marker) for marker in order]
    assert all(p >= 0 for p in positions), dict(zip(order, positions))
    assert positions == sorted(positions), dict(zip(order, positions))
    assert code.rstrip().splitlines()[-1].startswith("echo \"== DONE")


def test_gate_requires_exact_commits_and_refuses_bad_input():
    bad = subprocess.run(
        ["bash", str(GATE), "--label", "x", "--candidate", "abc1234", "--branch", "b",
         "--main-base", "a" * 40, "--live-base", "a" * 40, "--live-deploy", "dep-x"],
        capture_output=True, text=True,
    )
    assert bad.returncode == 2
    assert "full 40-character commit SHA" in bad.stdout
    assert subprocess.run(["bash", str(GATE)], capture_output=True, text=True).returncode == 2
    assert subprocess.run(["bash", str(POST)], capture_output=True, text=True).returncode == 2


def test_gate_allows_one_run_at_a_time():
    code = _code(GATE)
    assert 'mkdir "$LOCKDIR"' in code and "another release gate is running" in code


def test_postrelease_requires_the_gate_and_rereads_the_database():
    code = _code(POST)
    assert 'READY_FOR_PUSH commit=$SHA' in code
    assert '"$MAIN" = "$SHA"' in code
    assert "hosted_postcheck.py" in code and "$BROWS" in code
    assert "ROLLBACK_TARGET=redeploy" in code
    # Post-release makes no database write: the hosted check opens SQLite read-only.
    assert "mode=ro" in (RELEASE / "hosted_postcheck.py").read_text()


def test_libreoffice_is_reported_but_not_required():
    """18 Oct 2026: the first Mac gate run stopped because LibreOffice is not installed there.
    No test needs it (converters are injected or faked) and production does not convert, so the
    environment check reports it and does not stop."""
    script = (ROOT / "tools" / "setup_test_environment.sh").read_text()
    line = next(l for l in script.splitlines() if "LibreOffice not installed" in l)
    assert line.strip().startswith("else note ")
    mac_path = "/Applications/" + "LibreOffice.app"
    for test_file in (ROOT / "tests").glob("test_*.py"):
        if test_file.name == "test_release_tools.py":
            continue
        assert mac_path not in test_file.read_text(errors="ignore"), test_file.name



def test_release_files_and_backups_live_outside_the_icloud_desktop():
    for path in (GATE, POST):
        code = _code(path)
        assert "/Desktop" not in code and "Desktop/" not in code, path.name
        assert '"$OFFICE_LOCAL/release-work"' in code
    gate = _code(GATE)
    assert 'BACKUPS="$OFFICE_LOCAL/office-backups"' in gate
    assert "relocate_local_storage.py first" in gate


def test_relocation_only_copies_and_never_overwrites(tmp_path):
    import os
    import sqlite3

    home = tmp_path
    backups = home / "Desktop" / "Brayman-office-backups"
    generated = home / "Desktop" / "Brayman-Estimator" / "generated" / "nested"
    backups.mkdir(parents=True)
    generated.mkdir(parents=True)
    db_path = backups / "pre-test.db"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE t (x)")
    connection.commit()
    connection.close()
    (generated / "run.log").write_text("log")
    before = {p: p.read_bytes() for p in (home / "Desktop").rglob("*") if p.is_file()}
    script = RELEASE / "relocate_local_storage.py"
    env = {**os.environ, "RELOCATE_HOME": str(home)}

    first = subprocess.run(["python3", str(script)], env=env, capture_output=True, text=True)
    assert first.returncode == 0, first.stdout + first.stderr
    assert (home / "CalibraytAI-Office" / "office-backups" / "pre-test.db").read_bytes() == db_path.read_bytes()
    assert (home / "CalibraytAI-Office" / "release-work" / "nested" / "run.log").read_text() == "log"
    assert {p: p.read_bytes() for p in (home / "Desktop").rglob("*") if p.is_file()} == before

    again = subprocess.run(["python3", str(script)], env=env, capture_output=True, text=True)
    assert again.returncode == 0 and "already_there=1" in again.stdout

    copy = home / "CalibraytAI-Office" / "release-work" / "nested" / "run.log"
    copy.write_text("changed")
    conflict = subprocess.run(["python3", str(script)], env=env, capture_output=True, text=True)
    assert conflict.returncode == 1 and "nothing overwritten" in conflict.stdout
    assert copy.read_text() == "changed"
    assert {p: p.read_bytes() for p in (home / "Desktop").rglob("*") if p.is_file()} == before


def test_gate_accepts_the_calendar_migration_revision():
    """Alembic revisions here are 12 lower-case letters and digits, not only hex (z3c4d5e6f7a8)."""
    match = re.search(r'\[\[ "\$MIGRATION_TO" =~ (\S+) \]\]', _code(GATE))
    assert match, "gate must validate --migration-to"
    for revision, ok in (("z3c4d5e6f7a8", True), ("y2b3c4d5e6f7", True), ("Z3C4", False), ("z3c4d5e6f7a8;", False)):
        result = subprocess.run(["bash", "-c", f'[[ "$1" =~ {match.group(1)} ]]', "_", revision])
        assert (result.returncode == 0) is ok, revision


def test_gate_and_live_apply_carry_the_named_check_constraints():
    """Supplier signing (a4d5e6f7a8b9, verified 29 Oct 2026) rebuilds three tables only to widen three checks. The gate
    must pass --altered-checks to the rehearsal and record it, and the live apply must use the same names, so both
    run the strict comparison instead of the broader --altered-tables one."""
    gate, migrate = _code(GATE), _code(RELEASE / "release_migrate.sh")
    assert '--altered-checks) ALTERED_CHECKS=$2' in gate
    assert '${ALTERED_CHECKS:+--altered-checks "$ALTERED_CHECKS"}' in gate
    assert "ALTERED_CHECKS=$ALTERED_CHECKS" in gate
    assert 'ALTERED_CHECKS=$(val ALTERED_CHECKS "$STATE")' in migrate
    assert "${ALTERED_CHECKS:+ --altered-checks $ALTERED_CHECKS}" in migrate
    match = re.search(r'\[\[ "\$ALTERED_CHECKS" =~ (\S+) \]\]', gate)
    assert match, "gate must validate --altered-checks"
    good = "ck_signing_frozen_artifacts_document_family,ck_signing_requests_document_family,ck_signing_participants_role"
    for names, ok in ((good, True), ("ck_x", True), ("signing_requests", False), ("ck_x;rm", False), ("ck_x,", False)):
        result = subprocess.run(["bash", "-c", f'[[ "$1" =~ {match.group(1)} ]]', "_", names])
        assert (result.returncode == 0) is ok, names


def test_gate_refuses_altered_checks_without_a_migration():
    sha = "a" * 40
    bad = subprocess.run(
        ["bash", str(GATE), "--label", "x", "--candidate", sha, "--branch", "b", "--main-base", sha, "--live-base", sha,
         "--live-deploy", "dep-x", "--altered-checks", "ck_signing_requests_document_family"],
        capture_output=True, text=True,
    )
    assert bad.returncode == 2 and "--altered-checks <ck_1,ck_2> needs --migration-to" in bad.stdout
