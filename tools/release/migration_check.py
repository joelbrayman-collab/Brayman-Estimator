"""Database migration for a release: rehearse on a copy, or apply on the live instance.

Joel, 19 Oct 2026 (Calendar Appointments, migration z3c4d5e6f7a8). Prints KEY=VALUE lines and ends with
MIGRATION_REHEARSAL=ok or MIGRATE=ok; anything else is a stop.

  rehearse (office Mac, inside the release clone, on a COPY of the fresh production backup):
      venv/bin/python tools/release/migration_check.py rehearse --db COPY.db --from REV --to REV --new-tables a,b
  apply (on the Render instance, after Joel authorized the release and the migration and the
  candidate is deployed, so its migration file is on the server):
      $PY tools/release/migration_check.py apply --from REV --to REV --new-tables a,b --expect-sha SHA --label L

Both modes prove the same things: the database starts at --from; every existing table keeps its
exact schema (or, for a table rebuilt only to change the named --altered-checks, the same columns,
keys, foreign keys and other check constraints) and every row (count and SHA-256 of all rows, in rowid order); exactly the --new-tables
appear, empty; the revision ends at --to; integrity is ok.

Declared data changes (30 Oct 2026, estimate-to-project release s6f7a8b9c0d1), each named on the command line and
shown to Joel with the release arguments:
  --filled-columns t.c,...   a column the migration fills: an existing column may only go from NULL to a value
                             (every value already held stays exactly as it was); an added column may start with a
                             value. Every other column of every row is still compared exactly.
  --populated-tables t,...   new tables (also in --new-tables) that the migration fills; their row counts are shown. "apply" first takes its own online
backup next to the live database (instance/backups/pre-migrate-<label>-<UTC>.db) and refuses unless
the instance runs --expect-sha. Nothing is downgraded: database recovery is that backup, with Joel.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

# The repository root: this file's folder when run as a file; the current folder when piped over SSH
# (python - < migration_check.py, run from /opt/render/project/src like the other hosted helpers).
# Piped, Python sets __file__ to "<stdin>", so check for a real file (fixed 20 Oct 2026: the piped run
# took /opt/render as the root and refused the live database, before any backup or change).
_HERE = Path(globals().get("__file__") or "<stdin>")
ROOT = _HERE.resolve().parents[2] if _HERE.is_file() else Path.cwd()
# Where the live instance folder is (the release clone itself on Render; a temporary folder in tests).
INSTANCE_ROOT = Path(os.environ.get("RELEASE_ROOT", str(ROOT)))


def out(key: str, value) -> None:
    print(f"{key}={value}", flush=True)


def fail(message: str) -> None:
    out("FAIL", message)
    sys.exit(1)


def _connect_ro(path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _split_filled(filled) -> dict:
    out_: dict = {}
    for item in filled or ():
        table, _, column = item.partition(".")
        out_.setdefault(table, set()).add(column)
    return out_


def snapshot(path: str, columns_of: dict | None = None, exclude: dict | None = None) -> dict:
    """Schema and content fingerprint of every table and index (except alembic_version).

    ``columns_of`` {table: [column, ...]} (24 Oct 2026, a declared altered table that gained a column): that
    table's rows are fingerprinted over exactly those earlier columns, and ``added`` counts the rows where any
    column not in that list holds a value (an added column must start empty in every existing row)."""
    con = _connect_ro(path)
    try:
        schema = {
            (row[0], row[1]): row[2] or ""
            for row in con.execute(
                "SELECT type, name, sql FROM sqlite_master WHERE type IN ('table','index') AND name NOT LIKE 'sqlite_%'"
            )
        }
        tables = sorted(name for kind, name in schema if kind == "table" and name != "alembic_version")
        content, columns, added = {}, {}, {}
        for table in tables:
            columns[table] = [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]
            keep = (columns_of or {}).get(table)
            skip = (exclude or {}).get(table, set())
            if keep is not None and set(keep) <= set(columns[table]):
                select = ", ".join(f'"{c}"' for c in keep if c not in skip) or "1"
                extra = [c for c in columns[table] if c not in keep]
                counted = [c for c in extra if c not in skip]  # a declared filled column may hold values
                added[table] = (extra, con.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE ' + " OR ".join(f'"{c}" IS NOT NULL' for c in counted)
                ).fetchone()[0] if counted else 0)
            elif skip:
                select = ", ".join(f'"{c}"' for c in columns[table] if c not in skip) or "1"
            else:
                select = "*"
            digest = hashlib.sha256()
            count = 0
            for row in con.execute(f'SELECT {select} FROM "{table}" ORDER BY rowid'):
                digest.update(repr(row).encode("utf-8"))
                count += 1
            content[table] = (count, digest.hexdigest())
        revision = con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        con.close()
    return {"schema": schema, "content": content, "columns": columns, "added": added, "revision": revision,
            "integrity": integrity}


def snapshot_after(path: str, before: dict, altered_tables, filled=()) -> dict:
    """The database after the upgrade; a declared altered table is compared over its earlier columns."""
    return snapshot(path, {t: before["columns"][t] for t in altered_tables if t in before.get("columns", {})},
                    _split_filled(filled))


def check_filled(before_path: str, after_path: str, filled) -> None:
    """A declared filled column that already existed: only NULL -> value; every value already held is unchanged."""
    for table, columns in _split_filled(filled).items():
        old = _connect_ro(before_path)
        try:
            existing = [r[1] for r in old.execute(f'PRAGMA table_info("{table}")')]
            if not existing:
                fail(f"declared filled table {table} does not exist")
            kept = [c for c in columns if c in existing]
            before = {row[0]: row[1:] for row in old.execute(
                f'SELECT rowid, {", ".join(chr(34) + c + chr(34) for c in kept)} FROM "{table}"')} if kept else {}
        finally:
            old.close()
        new = _connect_ro(after_path)
        try:
            after_columns = [r[1] for r in new.execute(f'PRAGMA table_info("{table}")')]
            missing = [c for c in columns if c not in after_columns]
            if missing:
                fail(f"declared filled columns do not exist after the migration: {table}." + ", ".join(missing))
            filled_count = {c: 0 for c in columns}
            if kept:
                after = {row[0]: row[1:] for row in new.execute(
                    f'SELECT rowid, {", ".join(chr(34) + c + chr(34) for c in kept)} FROM "{table}"')}
                for rowid, values in before.items():
                    for column, was, now in zip(kept, values, after.get(rowid, (None,) * len(kept))):
                        if was is not None and was != now:
                            fail(f"{table}.{column} changed a value already held (row {rowid})")
                        if was is None and now is not None:
                            filled_count[column] += 1
            for column in columns:
                if column not in kept:
                    filled_count[column] = new.execute(
                        f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NOT NULL').fetchone()[0]
        finally:
            new.close()
        for column, count in sorted(filled_count.items()):
            out("FILLED_COLUMN", f"{table}.{column}: {count} row(s) filled"
                + (" (existing column; only empty values were filled)" if column in kept else " (added column)"))


_CHECK = re.compile(r"CONSTRAINT\s+(\w+)\s+CHECK\s*\(")


def _checks(sql: str) -> dict:
    """Named CHECK constraints in a CREATE TABLE statement, with their bodies (balanced parentheses)."""
    found = {}
    for match in _CHECK.finditer(sql or ""):
        depth, i = 1, match.end()
        while i < len(sql) and depth:
            depth += {"(": 1, ")": -1}.get(sql[i], 0)
            i += 1
        found[match.group(1)] = " ".join(sql[match.end():i - 1].split())
    return found


def structure(path: str, table: str) -> dict:
    """What a table is, independent of how its CREATE TABLE text is laid out (Supplier signing, 20 Oct 2026:
    a rebuilt table keeps its meaning but SQLite stores re-formatted text)."""
    con = _connect_ro(path)
    try:
        columns = [tuple(r) for r in con.execute(f'PRAGMA table_xinfo("{table}")')]
        fks = sorted(tuple(r[2:]) for r in con.execute(f'PRAGMA foreign_key_list("{table}")'))
        keys = []
        for row in con.execute(f'PRAGMA index_list("{table}")'):
            cols = tuple(r[2] for r in con.execute(f'PRAGMA index_info("{row[1]}")'))
            keys.append((row[1] if row[3] == "c" else "", bool(row[2]), row[3], cols))
        sql = con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()[0]
    finally:
        con.close()
    return {"columns": columns, "foreign_keys": fks, "keys": sorted(keys), "checks": _checks(sql)}


def upgrade(db_path: str, revision: str) -> None:
    """Run the candidate's Alembic migrations on this database file, as the tests do."""
    sys.path.insert(0, str(ROOT))
    from flask_migrate import upgrade as flask_upgrade

    from app import create_app

    app = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
                      "SECRET_KEY": "migration-check-not-used-for-requests"})
    with app.app_context():
        flask_upgrade(directory=str(ROOT / "migrations"), revision=revision)


def _belongs_to(key, tables) -> bool:
    """A schema entry (table or index) of one of ``tables``."""
    kind, name = key
    if kind == "table":
        return name in tables
    return any(name.startswith(f"ix_{t}_") or name.startswith(f"uq_{t}_") or name.startswith(f"sqlite_autoindex_{t}_")
               for t in tables)


def compare(before: dict, after: dict, new_tables: list, to_rev: str, altered_tables: list = (), altered_checks=(),
            paths=None, filled=(), populated=()) -> None:
    out("REVISION_AFTER", after["revision"])
    out("INTEGRITY_AFTER", after["integrity"])
    if after["integrity"] != "ok":
        fail("integrity is not ok after the migration")
    if after["revision"] != to_rev:
        fail(f"revision is {after['revision']}, expected {to_rev}")
    changed = [t for t, fp in before["content"].items() if after["content"].get(t) != fp]
    if changed:
        fail("existing records changed in: " + ", ".join(changed))
    # A declared altered table may gain columns; it may never lose one, and a new column holds nothing yet.
    added_columns = []
    for table in altered_tables:
        if table not in before.get("columns", {}):
            continue
        lost = [c for c in before["columns"][table] if c not in after.get("columns", {}).get(table, [])]
        if lost:
            fail(f"columns removed from {table}: " + ", ".join(lost))
        extra, holding = after.get("added", {}).get(table, ([], 0))
        if holding:
            fail(f"new columns of {table} hold values in {holding} existing row(s)")
        declared_filled = _split_filled(filled).get(table, set())
        added_columns += [f"{table}.{c}" for c in extra if c not in declared_filled]
    # A table the release declares as altered (e.g. a widened check constraint, --altered-tables) may change
    # its schema; every one of its rows must still be identical (checked above with all the others).
    declared = [t for t in altered_tables if t not in before["content"]]
    if declared:
        fail("declared altered tables do not exist: " + ", ".join(declared))
    altered = [k for k, sql in before["schema"].items()
               if after["schema"].get(k) != sql and not _belongs_to(k, altered_tables)]
    # --altered-checks: stricter; the table may be rebuilt only for the named check constraints.
    rebuilt = []
    if altered and altered_checks and paths:
        for kind, name in altered:
            if kind != "table":
                continue
            old, new = structure(paths[0], name), structure(paths[1], name)
            same = all(old[part] == new[part] for part in ("columns", "foreign_keys", "keys"))
            others_same = ({k: v for k, v in old["checks"].items() if k not in altered_checks}
                           == {k: v for k, v in new["checks"].items() if k not in altered_checks})
            named = set(old["checks"]) & set(altered_checks)
            if same and others_same and named and set(old["checks"]) == set(new["checks"]):
                rebuilt.append((kind, name))
                for check in sorted(named):
                    out("ALTERED_CHECK", f"{name}.{check}: {new['checks'][check]}")
        altered = [k for k in altered if k not in rebuilt]
    if altered:
        fail("existing schema changed: " + ", ".join(f"{k[0]} {k[1]}" for k in altered))
    if altered_checks and not rebuilt:
        fail("the named check constraints did not change: " + ", ".join(altered_checks))
    added = sorted(set(after["content"]) - set(before["content"]))
    if added != sorted(new_tables):
        fail(f"new tables are {added}, expected {sorted(new_tables)}")
    undeclared_populated = [t for t in populated if t not in new_tables]
    if undeclared_populated:
        fail("populated tables must also be new tables: " + ", ".join(undeclared_populated))
    not_empty = [t for t in added if after["content"][t][0] != 0 and t not in populated]
    if not_empty:
        fail("new tables are not empty: " + ", ".join(not_empty))
    for table in populated:
        out("POPULATED_TABLE", f"{table}: {after['content'][table][0]} row(s)")
    if filled and paths:
        check_filled(paths[0], paths[1], filled)
    detail = "schema and every row identical"
    if rebuilt:
        detail = (f"every row identical; schema identical except the named check constraints on "
                  f"{', '.join(n for _k, n in rebuilt)}")
    if altered_tables:
        detail += f"; schema altered as declared: {','.join(altered_tables)}"
    if added_columns:
        detail += f"; added empty columns: {','.join(added_columns)} (every existing row unchanged)"
    out("EXISTING_TABLES_UNCHANGED", f"{len(before['content'])} tables, {sum(c for c, _ in before['content'].values())} rows, {detail}")
    out("NEW_TABLES", ",".join(added) + (" (empty)" if not populated else f" (populated as declared: {','.join(populated)})"))


def _reference_copy(db: str) -> str:
    """A throwaway copy of the database before the upgrade, to compare a rebuilt table's structure."""
    reference = f"{db}.before-{os.getpid()}"
    src = sqlite3.connect(db)
    dest = sqlite3.connect(reference)
    src.backup(dest)
    dest.close()
    src.close()
    return reference


def rehearse(args) -> None:
    db = os.path.abspath(args.db)
    if not os.path.exists(db):
        fail(f"{db} does not exist")
    before = snapshot(db, exclude=_split_filled(args.filled_columns))
    out("REHEARSAL_DB", db)
    out("REVISION_BEFORE", before["revision"])
    out("INTEGRITY_BEFORE", before["integrity"])
    if before["revision"] != args.from_rev:
        fail(f"copy is at {before['revision']}, expected {args.from_rev}")
    if before["integrity"] != "ok":
        fail("copy integrity is not ok")
    reference = _reference_copy(db) if (args.altered_checks or args.filled_columns) else None
    started = time.time()
    upgrade(db, args.to_rev)
    out("UPGRADE_SECONDS", "%.1f" % (time.time() - started))
    try:
        compare(before, snapshot_after(db, before, args.altered_tables, args.filled_columns), args.new_tables,
                args.to_rev, args.altered_tables, args.altered_checks, (reference, db), args.filled_columns,
                args.populated_tables)
    finally:
        if reference:
            os.remove(reference)
    out("MIGRATION_REHEARSAL", "ok")


def apply(args) -> None:
    running = os.environ.get("RENDER_GIT_COMMIT", "")
    out("RUNNING_SHA", running)
    if running != args.expect_sha:
        fail(f"the instance runs {running}, not the authorized release {args.expect_sha}")
    db = str(INSTANCE_ROOT / "instance" / "brayman_estimator.db")
    uri = os.environ.get("CALIBRAYTAI_DATABASE_URI", "")
    uri_path = uri[len("sqlite:///"):] if uri.startswith("sqlite:///") else ""
    if not uri_path or os.path.realpath(uri_path) != os.path.realpath(db):
        fail(f"live database URI does not point at {db}")
    live = _connect_ro(db)
    current = live.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    live.close()
    out("REVISION_BEFORE", current)
    if current == args.to_rev:
        out("ALREADY_MIGRATED", "yes (nothing done)")
        out("MIGRATE", "ok")
        return
    if current != args.from_rev:
        fail(f"live database is at {current}, expected {args.from_rev}")
    # The pre-migration backup (database recovery point), taken with SQLite's online backup.
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    backups = INSTANCE_ROOT / "instance" / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / f"pre-migrate-{args.label}-{stamp}.db"
    if backup.exists():
        fail("backup file already exists")
    src = sqlite3.connect(db)
    dest = sqlite3.connect(str(backup))
    src.backup(dest)
    dest.close()
    src.close()
    saved = snapshot(str(backup))
    if saved["integrity"] != "ok" or saved["revision"] != args.from_rev:
        fail("pre-migration backup did not verify")
    out("PRE_MIGRATION_BACKUP", backup)
    out("PRE_MIGRATION_BACKUP_SHA256", hashlib.sha256(backup.read_bytes()).hexdigest())
    before = snapshot(db, exclude=_split_filled(args.filled_columns))
    out("INTEGRITY_BEFORE", before["integrity"])
    if before["integrity"] != "ok":
        fail("live integrity is not ok before the migration")
    started = time.time()
    upgrade(db, args.to_rev)
    out("UPGRADE_SECONDS", "%.1f" % (time.time() - started))
    after = snapshot_after(db, before, args.altered_tables, args.filled_columns)
    # Someone may have used the app during the minute of the release; compare against the moment
    # just before the upgrade, which is what the migration itself must not change. The structure of a
    # rebuilt table is compared with the verified pre-migration backup.
    compare(before, after, args.new_tables, args.to_rev, args.altered_tables, args.altered_checks, (str(backup), db),
            args.filled_columns, args.populated_tables)
    out("MIGRATE", "ok")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("rehearse", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--from", dest="from_rev", required=True)
        p.add_argument("--to", dest="to_rev", required=True)
        # "none" (27 Oct 2026): the migration adds no table (only columns of declared --altered-tables).
        p.add_argument("--new-tables", required=True,
                       type=lambda v: [] if v == "none" else [t for t in v.split(",") if t])
        p.add_argument("--altered-tables", default=[], type=lambda v: [t for t in v.split(",") if t])
        p.add_argument("--altered-checks", default=[], type=lambda v: [t for t in v.split(",") if t],
                       help="check constraints the migration is authorized to change (tables rebuilt for them)")
        p.add_argument("--filled-columns", default=[], type=lambda v: [t for t in v.split(",") if t],
                       help="table.column the migration is authorized to fill (existing: only NULL -> value)")
        p.add_argument("--populated-tables", default=[], type=lambda v: [t for t in v.split(",") if t],
                       help="new tables the migration is authorized to fill")
        if name == "rehearse":
            p.add_argument("--db", required=True)
        else:
            p.add_argument("--expect-sha", required=True)
            p.add_argument("--label", required=True)
    args = parser.parse_args()
    (rehearse if args.mode == "rehearse" else apply)(args)


if __name__ == "__main__":
    main()
