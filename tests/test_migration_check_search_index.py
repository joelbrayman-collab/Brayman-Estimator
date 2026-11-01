"""migration_check.py and search indexes (review fix C1, 1 Nov 2026).

Revision t7a8b9c0d1e2 creates the FTS5 table document_search when SQLite has FTS5. FTS5 writes rows into its shadow
tables when it is created (document_search_data 2, document_search_config 1), and two shadow tables are WITHOUT ROWID
(document_search_idx, document_search_config). The release check used to fingerprint every table "ORDER BY rowid" and
require every new table to be empty, so the release-gate rehearsal of this migration stopped, and so would every later
release's before-snapshot of a database that holds the index.

Now virtual tables and their shadow tables are a search index: counted and reported (SEARCH_INDEX), never row-hashed,
never part of --new-tables or of the release's TABLES=/ROWS= totals (count-rows), and an ordinary WITHOUT ROWID table
is fingerprinted in primary-key order.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app import create_app

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "release" / "migration_check.py"
HOSTED_POSTCHECK = ROOT / "tools" / "release" / "hosted_postcheck.py"
PRIOR, HEAD = "s6f7a8b9c0d1", "t7a8b9c0d1e2"
NEW = ("organization_equipment,organization_equipment_events,documents,document_versions,document_links,"
       "document_dates,document_events,document_text")
FTS = ("document_search", "document_search_config", "document_search_content", "document_search_data",
       "document_search_docsize", "document_search_idx")

sys.path.insert(0, str(ROOT / "tools" / "release"))
import migration_check as M  # noqa: E402


def _fts5() -> bool:
    con = sqlite3.connect(":memory:")
    try:
        con.execute("CREATE VIRTUAL TABLE p USING fts5(x)")
        return True
    finally:
        con.close()


def test_this_python_has_fts5():
    # The rehearsal below must exercise the FTS5 path (production's SQLite has FTS5), not the fallback.
    assert _fts5()


def _upgrade(path: Path, revision: str) -> None:
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    with app.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
        command.upgrade(cfg, revision)


def _database_at_prior(path: Path) -> None:
    _upgrade(path, PRIOR)
    con = sqlite3.connect(path)
    con.execute("INSERT OR IGNORE INTO organizations (id, legal_name, display_name, primary_address, default_region, "
                "currency, tax_jurisdiction, is_active, created_at, updated_at) VALUES ('ORG-001', 'Synthetic Ltd.', "
                "'Synthetic', '1 Test Rd', 'Ontario', 'CAD', 'Ontario (HST 13%)', 1, '2026-10-19 00:00:00', "
                "'2026-10-19 00:00:00')")
    con.execute("INSERT INTO clients (id, organization_id, name, created_at) VALUES (1, 'ORG-001', "
                "'Client (synthetic)', '2026-10-19 00:00:00')")
    con.commit()
    con.close()


def _run(*args, env=None, stdin=None, cwd=ROOT):
    return subprocess.run([sys.executable, *( [str(SCRIPT)] if stdin is None else ["-"]), *args], cwd=cwd,
                          capture_output=True, text=True, env={**os.environ, **(env or {})}, timeout=300,
                          input=stdin)


def _values(text):
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


@pytest.fixture(scope="module")
def prior_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("prior") / "prior.db"
    _database_at_prior(path)
    return path


def _copy(src: Path, dest: Path) -> Path:
    a, b = sqlite3.connect(src), sqlite3.connect(dest)
    a.backup(b)
    a.close()
    b.close()
    return dest


def test_the_release_rehearsal_of_the_documents_migration_passes(prior_db, tmp_path):
    db = _copy(prior_db, tmp_path / "copy.db")
    result = _run("rehearse", "--db", str(db), "--from", PRIOR, "--to", HEAD, "--new-tables", NEW)
    values = _values(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
    assert values["MIGRATION_REHEARSAL"] == "ok"
    assert "schema and every row identical" in values["EXISTING_TABLES_UNCHANGED"]
    assert values["NEW_TABLES"] == ",".join(sorted(NEW.split(","))) + " (empty)"
    # The FTS5 index and its shadow tables are reported separately, never as new tables to declare.
    assert values["SEARCH_INDEX_NEW"].startswith(",".join(FTS) + " ")
    assert "search index" in values["SEARCH_INDEX_NEW"]


def test_declaring_the_fts_tables_as_new_tables_is_refused(prior_db, tmp_path):
    db = _copy(prior_db, tmp_path / "copy.db")
    result = _run("rehearse", "--db", str(db), "--from", PRIOR, "--to", HEAD, "--new-tables", NEW + ",document_search")
    assert result.returncode == 1 and "FAIL=new tables are" in result.stdout


def test_a_real_row_in_a_new_table_still_stops(prior_db, tmp_path):
    db = _copy(prior_db, tmp_path / "copy.db")
    _upgrade(db, HEAD)
    before = M.snapshot(str(prior_db))
    con = sqlite3.connect(db)
    con.execute("INSERT INTO organization_equipment (organization_id, name, category, status, created_at, updated_at) "
                "VALUES ('ORG-001', 'Skid steer', 'HEAVY_EQUIPMENT', 'ACTIVE', '2026-11-01', '2026-11-01')")
    con.commit()
    con.close()
    with pytest.raises(SystemExit):
        M.compare(before, M.snapshot(str(db)), NEW.split(","), HEAD)


def _database_at_head_with_indexed_rows(prior_db, tmp_path) -> Path:
    db = _copy(prior_db, tmp_path / "head.db")
    _upgrade(db, HEAD)
    con = sqlite3.connect(db)
    for i in range(3):
        con.execute("INSERT INTO document_search (rowid, organization_id, sensitivity, status, title, filename, "
                    "keywords, labels, body) VALUES (?, 'ORG-001', 'STANDARD', 'ACTIVE', ?, 'a.pdf', '', '', ?)",
                    (i + 1, f"Permit {i}", "foundation drawings " * 50))
    con.commit()
    con.close()
    return db


def test_the_next_release_can_snapshot_a_database_that_holds_the_index(prior_db, tmp_path):
    db = _database_at_head_with_indexed_rows(prior_db, tmp_path)
    snap = M.snapshot(str(db))  # used to raise "no such column: rowid" on document_search_idx
    assert not set(FTS) & set(snap["content"])
    assert set(snap["search_index"]) == set(FTS)
    assert snap["search_index"]["document_search"] == 3
    # Unchanged database, unchanged snapshot; the next migration compares cleanly.
    again = M.snapshot(str(db))
    assert again["content"] == snap["content"]


def test_count_rows_excludes_the_search_index_and_reports_it_separately(prior_db, tmp_path):
    db = _database_at_head_with_indexed_rows(prior_db, tmp_path)
    result = _run("count-rows", "--db", str(db))
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.strip().splitlines()
    con = sqlite3.connect(db)
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    core = [n for n in names if n not in FTS]
    rows = sum(con.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in core)
    index_rows = sum(con.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in FTS)
    con.close()
    assert lines[0] == f"TABLES={len(core)} ROWS={rows}"
    assert lines[1] == f"SEARCH_INDEX=TABLES=6 ROWS={index_rows}"


def test_count_rows_reads_the_live_database_when_piped(prior_db, tmp_path):
    db = _database_at_head_with_indexed_rows(prior_db, tmp_path)
    local = _run("count-rows", "--db", str(db)).stdout
    piped = _run("count-rows", "--live", env={"CALIBRAYTAI_DATABASE_URI": f"sqlite:///{db}"},
                 stdin=SCRIPT.read_text(), cwd=tmp_path)
    assert piped.returncode == 0, piped.stdout + piped.stderr
    assert piped.stdout == local


def test_post_release_rows_balance_end_to_end_with_the_index(prior_db, tmp_path):
    """Release gate counts the backup (count-rows); release_migrate applies; postrelease reads the live database
    with count-rows: backup + 8 empty new tables, FTS rows reported separately, nothing else."""
    backup = _run("count-rows", "--db", str(prior_db)).stdout.splitlines()[0]
    instance = tmp_path / "instance"
    instance.mkdir()
    live_db = _copy(prior_db, instance / "brayman_estimator.db")
    env = {"RELEASE_ROOT": str(tmp_path), "CALIBRAYTAI_DATABASE_URI": f"sqlite:///{live_db}",
           "RENDER_GIT_COMMIT": "a" * 40}
    applied = _run("apply", "--from", PRIOR, "--to", HEAD, "--new-tables", NEW, "--expect-sha", "a" * 40,
                   "--label", "docs", env=env)
    assert applied.returncode == 0 and "MIGRATE=ok" in applied.stdout, applied.stdout + applied.stderr
    assert "SEARCH_INDEX_NEW=" in applied.stdout
    live = _run("count-rows", "--db", str(live_db)).stdout.splitlines()
    assert live[1].startswith("SEARCH_INDEX=TABLES=6 ")
    btables, brows = M._tables_rows(backup)
    assert live[0] == f"TABLES={btables + 8} ROWS={brows}"
    ok = _run("postcheck-rows", "--backup", backup, "--live", live[0], "--new-tables", NEW)
    assert ok.returncode == 0 and "ROWS_CHECK=ok" in ok.stdout, ok.stdout
    # The pinned hosted post-check counts every table, the index included: that total is NOT the comparison.
    hosted = subprocess.run([sys.executable, str(HOSTED_POSTCHECK)], capture_output=True, text=True,
                            env={**os.environ, "CALIBRAYTAI_DATABASE_URI": f"sqlite:///{live_db}"})
    hosted_line = next(l for l in hosted.stdout.splitlines() if l.startswith("TABLES="))
    assert hosted_line != live[0]


def test_an_ordinary_without_rowid_table_is_fingerprinted_in_key_order(tmp_path):
    db = tmp_path / "w.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE alembic_version (version_num TEXT)")
    con.execute("INSERT INTO alembic_version VALUES ('x')")
    con.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID")
    con.executemany("INSERT INTO kv VALUES (?, ?)", [("b", "2"), ("a", "1")])
    con.commit()
    con.close()
    first = M.snapshot(str(db))
    assert first["content"]["kv"][0] == 2 and "kv" not in first["search_index"]
    con = sqlite3.connect(db)
    con.execute("UPDATE kv SET v = '9' WHERE k = 'a'")
    con.commit()
    con.close()
    assert M.snapshot(str(db))["content"]["kv"] != first["content"]["kv"]


def test_scripts_count_rows_with_the_shared_helper():
    gate = (ROOT / "tools" / "release" / "release_gate.sh").read_text()
    post = (ROOT / "tools" / "release" / "postrelease_check.sh").read_text()
    assert "tools/release/migration_check.py count-rows --db \"$LOCALB\"" in gate
    assert "BACKUP_SEARCH_INDEX=" in gate
    assert "count-rows --live" in post and '< "$DEST/tools/release/migration_check.py"' in post
    assert "LROWS=$(grep '^TABLES=' \"$OUT-rows-live.txt\")" in post
