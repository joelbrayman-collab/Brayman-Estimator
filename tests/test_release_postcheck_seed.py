"""Post-release row check with a seeding migration (Joel, 31 Oct 2026: the e2p1 follow-up).

e2p1's migration seeded project_number_sequences (1 row) and project_identity_events (2 rows), as declared with
--populated-tables. The post-release check compared the live total with the backup plus EMPTY new tables and
stopped on 2,096 vs 2,093. Now release_migrate.sh records what the migration seeded and the post-release check proves
live = backup + new tables + exactly that seed, table by table; anything else still stops.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "tools" / "release" / "migration_check.py"
POST = ROOT / "tools" / "release" / "postrelease_check.sh"
MIGRATE = ROOT / "tools" / "release" / "release_migrate.sh"
NEW = ("project_number_sequences,project_identity_events,estimate_approvals,early_procurement_exceptions,"
       "subcontract_commitments,company_schedule_change_requests,schedule_external_drafts,project_closeout_records")
POP = "project_number_sequences,project_identity_events"


def _run(**kw):
    args = [sys.executable, str(CHECK), "postcheck-rows", "--backup", kw.get("backup", "TABLES=219 ROWS=2093"),
            "--live", kw.get("live", "TABLES=227 ROWS=2096"), "--new-tables", kw.get("new", NEW),
            "--populated-tables", kw.get("pop", POP),
            "--seeded", kw.get("seeded", "project_number_sequences=1,project_identity_events=2"),
            "--live-counts", kw.get("counts", "project_number_sequences=1,project_identity_events=2")]
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, r.stdout


def test_e2p1_live_rows_are_the_backup_plus_the_declared_seed():
    code, out = _run()
    assert code == 0, out
    assert "EXPECTED_LIVE=TABLES=227 ROWS=2096" in out
    assert "SEEDED_TABLE=project_number_sequences: 1 row(s)" in out
    assert "SEEDED_TABLE=project_identity_events: 2 row(s)" in out
    assert out.strip().endswith("ROWS_CHECK=ok")


def test_an_extra_row_anywhere_else_still_stops():
    code, out = _run(live="TABLES=227 ROWS=2097")
    assert code == 1 and "FAIL=records differ" in out


def test_a_seeded_table_that_changed_after_the_migration_stops():
    code, out = _run(counts="project_number_sequences=1,project_identity_events=3", live="TABLES=227 ROWS=2097")
    assert code == 1 and "project_identity_events holds 3 row(s)" in out


def test_seed_counts_must_match_the_declared_tables():
    code, out = _run(seeded="project_number_sequences=1")
    assert code == 1 and "do not match the declared --populated-tables" in out


def test_a_populated_table_must_be_a_new_table():
    code, out = _run(pop="projects,project_identity_events", seeded="projects=1,project_identity_events=2",
                     counts="projects=1,project_identity_events=2")
    assert code == 1 and "is not a new table" in out


def test_a_missing_table_count_stops():
    code, out = _run(counts="project_identity_events=2")
    assert code == 1 and "project_number_sequences holds None" in out


def test_malformed_input_stops():
    assert _run(seeded="project_number_sequences=one")[0] == 1
    assert _run(live="227 tables")[0] == 1


def test_scripts_record_and_use_the_seed():
    migrate, post = MIGRATE.read_text(), POST.read_text()
    assert 'echo "MIGRATION_SEEDED=$SEEDED" >> "$STATE"' in migrate
    assert "POPULATED_TABLE=" in migrate
    assert "postcheck-rows" in post and '--seeded "$SEEDED"' in post and '--live-counts "$COUNTS"' in post
    assert "grep -q '^ROWS_CHECK=ok'" in post
    # the read of the seeded tables on the live database is read-only
    assert '?mode=ro"' in post
    for script in (POST, MIGRATE):
        assert subprocess.run(["bash", "-n", str(script)]).returncode == 0


def test_the_migrate_script_parses_the_migration_report_into_seed_pairs(tmp_path):
    line = next(l for l in MIGRATE.read_text().splitlines() if l.startswith("SEEDED=$(grep '^POPULATED_TABLE='"))
    report = tmp_path / "m.txt"
    report.write_text("MIGRATE=ok\nPOPULATED_TABLE=project_number_sequences: 1 row(s)\n"
                      "POPULATED_TABLE=project_identity_events: 2 row(s)\n")
    script = f'OUT="{tmp_path}/m"; cp "{report}" "$OUT-migrate.txt"; {line}; echo "$SEEDED"'
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert r.stdout.strip() == "project_number_sequences=1,project_identity_events=2", r.stderr


# Review fix M4 (1 Nov 2026): a rerun of release_migrate.sh that finds the database ALREADY_MIGRATED used to exit
# without MIGRATION_SEEDED in the state file, so postrelease_check.sh stopped. The rerun now keeps the value already
# recorded, recovers it from the first apply's saved report, records it empty when nothing was declared populated, and
# otherwise stops with a clear instruction.

def _rerun_block() -> str:
    text = MIGRATE.read_text()
    start, end = text.index("# >>> seed-on-rerun"), text.index("# <<< seed-on-rerun")
    return text[start:end]


def _rerun(tmp_path, populated, state_lines=(), earlier=None, label="docs"):
    gen = tmp_path / "gen"
    gen.mkdir(exist_ok=True)
    state = gen / f"{label}-release-state.txt"
    state.write_text("".join(f"{l}\n" for l in ("SHA=" + "a" * 40, *state_lines)))
    if earlier is not None:
        (gen / f"{label}-migrate-20261101-100000-migrate.txt").write_text(earlier)
    out = gen / f"{label}-migrate-20261101-110000"
    out.with_name(out.name + "-migrate.txt").write_text("REVISION_BEFORE=t7a8b9c0d1e2\nALREADY_MIGRATED=yes (nothing done)\n"
                                                        "MIGRATE=ok\n")
    script = (f'set -u; GEN="{gen}"; REPORTS="{gen}"; LABEL={label}; STATE="{state}"; STATUS="{gen}/{label}-release-status.txt"; OUT="{out}"; POPULATED_TABLES="{populated}"; '
              f'MIGRATION_TO=t7a8b9c0d1e2; status() {{ echo "STATUS: $1"; }}; stop() {{ echo "STOP: $1"; exit 1; }}; '
              + _rerun_block() + '\necho "DONE"')
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr, state.read_text()


def test_a_rerun_keeps_the_seed_already_recorded(tmp_path):
    code, out, state = _rerun(tmp_path, POP, ["MIGRATION_SEEDED=project_number_sequences=1,project_identity_events=2"])
    assert code == 0 and "DONE" in out, out
    assert state.count("MIGRATION_SEEDED=") == 1


def test_a_rerun_with_no_populated_tables_records_an_empty_seed(tmp_path):
    code, out, state = _rerun(tmp_path, "")
    assert code == 0 and "DONE" in out, out
    assert "MIGRATION_SEEDED=\n" in state


def test_a_rerun_recovers_the_seed_from_the_first_apply_report(tmp_path):
    first = ("REVISION_BEFORE=s6f7a8b9c0d1\nPOPULATED_TABLE=project_number_sequences: 1 row(s)\n"
             "POPULATED_TABLE=project_identity_events: 2 row(s)\nMIGRATE=ok\n")
    code, out, state = _rerun(tmp_path, POP, earlier=first)
    assert code == 0 and "DONE" in out, out
    assert "MIGRATION_SEEDED=project_number_sequences=1,project_identity_events=2\n" in state
    assert "first apply" in out


def test_a_rerun_without_any_record_of_the_seed_stops_with_an_instruction(tmp_path):
    code, out, state = _rerun(tmp_path, POP, earlier="REVISION_BEFORE=s6f7a8b9c0d1\n")  # first run's report incomplete
    assert code == 1 and "STOP:" in out and "MIGRATION_SEEDED" not in state
    assert "send Claude" in out
