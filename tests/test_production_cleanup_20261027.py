"""The 27 Oct 2026 Production cleanup tool, on small synthetic databases (no Production data, no app)."""
from __future__ import annotations

import importlib.util
import os
import sqlite3
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "hosting" / "production_cleanup_20261027.py"


def _tool(monkeypatch, **plan):
    spec = importlib.util.spec_from_file_location("cleanup_tool", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "REVISION", "rev-synthetic")
    monkeypatch.setattr(mod, "REMOVE", plan.get("remove", {"projects": {1: "UAT one"}, "clients": {}}))
    monkeypatch.setattr(mod, "CLIENT_PIN", {})
    monkeypatch.setattr(mod, "LABEL", {"projects": "name", "clients": "name", "users": "email"})
    monkeypatch.setattr(mod, "PROTECT_ROWS", plan.get("protect", {"projects": {2: "Real job"}}))
    monkeypatch.setattr(mod, "PROTECT_PROJECT_TREE", {2})
    monkeypatch.setattr(mod, "PROTECT_TABLES", {"alembic_version", "history"})
    monkeypatch.setattr(mod, "AUDIT_TABLES", {"audit"})
    monkeypatch.setattr(mod, "UNDECLARED", {("snapshots", "project_id"): "projects"})
    monkeypatch.setattr(mod, "SOFT", [])
    monkeypatch.setattr(mod, "RENAME", plan.get("rename", {("users", 1): ("display_name", "Joel (test)", "Joel Brayman",
                                                                       "email", "joel@example.invalid")}))
    monkeypatch.setattr(mod, "OWNED_BY_REFERRERS", {})
    monkeypatch.setattr(mod, "FILE_PROJECT", [mod.re.compile(r"^plan_uploads/(\d+)/")])
    monkeypatch.setattr(mod, "FILE_KEYED", [])
    return mod


def _db(tmp_path):
    inst = tmp_path / "instance"
    (inst / "plan_uploads" / "1").mkdir(parents=True)
    (inst / "plan_uploads" / "2").mkdir(parents=True)
    (inst / "plan_uploads" / "1" / "a.pdf").write_bytes(b"synthetic plan for the UAT project")
    (inst / "plan_uploads" / "2" / "b.pdf").write_bytes(b"synthetic plan for the real job")
    path = inst / "brayman_estimator.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE alembic_version (version_num TEXT);
        INSERT INTO alembic_version VALUES ('rev-synthetic');
        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, display_name TEXT);
        CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, lead_user_id INTEGER REFERENCES users(id));
        CREATE TABLE estimates (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id));
        CREATE TABLE lines (id INTEGER PRIMARY KEY, estimate_id INTEGER NOT NULL REFERENCES estimates(id) ON DELETE CASCADE);
        CREATE TABLE snapshots (id INTEGER PRIMARY KEY, project_id INTEGER);
        CREATE TABLE audit (id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES projects(id));
        CREATE TABLE history (id INTEGER PRIMARY KEY, note TEXT);
        INSERT INTO users VALUES (1, 'joel@example.invalid', 'Joel (test)');
        INSERT INTO projects VALUES (1, 'UAT one', 1), (2, 'Real job', 1);
        INSERT INTO estimates VALUES (10, 1), (20, 2);
        INSERT INTO lines VALUES (100, 10), (101, 10), (200, 20);
        INSERT INTO snapshots VALUES (5, 1), (6, 2);
        INSERT INTO history VALUES (1, 'kept');
    """)
    con.commit()
    con.close()
    return str(path), str(inst)


def _listing(inst):
    return [("plan_uploads/1/a.pdf", 33), ("plan_uploads/2/b.pdf", 30)]


def test_plan_follows_links_and_undeclared_links_and_files(tmp_path, monkeypatch):
    mod = _tool(monkeypatch)
    db, inst = _db(tmp_path)
    p = mod.plan(mod.open_db(db), _listing(inst))
    assert p["counts"] == {"estimates": 1, "lines": 2, "projects": 1, "snapshots": 1}
    assert not p["blockers"] and not p["problems"]
    assert [(f["path"], f["action"]) for f in p["files"]] == [("plan_uploads/1/a.pdf", "quarantine"),
                                                            ("plan_uploads/2/b.pdf", "keep")]


def test_apply_removes_exactly_the_plan_quarantines_files_and_verify_passes(tmp_path, monkeypatch):
    mod = _tool(monkeypatch)
    db, inst = _db(tmp_path)
    before = str(tmp_path / "before.db")
    sqlite3.connect(db).backup(sqlite3.connect(before))
    p = mod.plan(mod.open_db(db), mod.scan_files(inst))
    mod.apply(db, inst, p["hash"])
    con = sqlite3.connect(db)
    assert con.execute("SELECT id FROM projects").fetchall() == [(2,)]
    assert con.execute("SELECT id FROM lines").fetchall() == [(200,)]  # the real job's line, untouched
    assert con.execute("SELECT display_name FROM users").fetchone()[0] == "Joel Brayman"
    assert not os.path.exists(os.path.join(inst, "plan_uploads/1/a.pdf"))
    assert os.path.exists(os.path.join(inst, "cleanup-quarantine-20261027/files/plan_uploads/1/a.pdf"))
    assert os.path.exists(os.path.join(inst, "plan_uploads/2/b.pdf"))
    assert os.path.exists(os.path.join(inst, "cleanup-quarantine-20261027/manifest.json"))
    assert mod.verify(before, db)


def test_refuses_when_a_protected_project_would_lose_records(tmp_path, monkeypatch):
    mod = _tool(monkeypatch)
    db, inst = _db(tmp_path)
    sqlite3.connect(db).execute("UPDATE estimates SET project_id=1 WHERE id=20").connection.commit()
    con = sqlite3.connect(db)
    con.execute("INSERT INTO lines VALUES (300, 10)")
    con.execute("CREATE TABLE p2_links (id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES projects(id), "
                "estimate_id INTEGER REFERENCES estimates(id))")
    con.execute("INSERT INTO p2_links VALUES (1, 2, 10)")  # the real job points at a removed estimate
    con.commit()
    p = mod.plan(mod.open_db(db), [])
    assert any("P27's p2_links" in x for x in p["problems"])
    with pytest.raises(mod.Refuse):
        mod.apply(db, inst, p["hash"])


def test_audit_rows_pointing_at_removed_records_block_and_are_never_deleted(tmp_path, monkeypatch):
    mod = _tool(monkeypatch)
    db, inst = _db(tmp_path)
    con = sqlite3.connect(db)
    con.execute("INSERT INTO audit VALUES (1, 1)")
    con.commit()
    p = mod.plan(mod.open_db(db), [])
    assert p["blockers"] == [{"table": "audit", "column": "project_id", "points_to": "projects", "rows": [1]}]
    with pytest.raises(mod.Refuse):
        mod.apply(db, inst, p["hash"])
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 1


def test_refuses_on_a_changed_pin_a_changed_plan_and_the_live_database(tmp_path, monkeypatch):
    mod = _tool(monkeypatch)
    db, inst = _db(tmp_path)
    p = mod.plan(mod.open_db(db), [])
    with pytest.raises(mod.Refuse, match="plan changed"):
        mod.apply(db, inst, "0000000000000000")
    monkeypatch.setattr(mod, "LIVE_DB", os.path.realpath(db))
    with pytest.raises(mod.Refuse, match="live Production"):
        mod.apply(db, inst, p["hash"])
    with pytest.raises(mod.Refuse, match="--backup"):
        mod.apply(db, inst, p["hash"], live=True)
    sqlite3.connect(db).execute("UPDATE projects SET name='Someone real' WHERE id=1").connection.commit()
    with pytest.raises(mod.Refuse, match="not the approved"):
        mod.plan(mod.open_db(db), [])


def test_a_failure_before_commit_changes_nothing(tmp_path, monkeypatch):
    mod = _tool(monkeypatch)
    db, inst = _db(tmp_path)
    p = mod.plan(mod.open_db(db), mod.scan_files(inst))
    snapshot = sqlite3.connect(db).execute("SELECT COUNT(*) FROM lines").fetchone()[0]

    def boom(*_a, **_k):
        raise RuntimeError("synthetic failure just before the commit")
    monkeypatch.setattr(mod, "dangling_undeclared", boom)
    with pytest.raises(RuntimeError):
        mod.apply(db, inst, p["hash"])
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM lines").fetchone()[0] == snapshot
    assert con.execute("SELECT display_name FROM users").fetchone()[0] == "Joel (test)"
    assert os.path.exists(os.path.join(inst, "plan_uploads/1/a.pdf"))
    assert not os.path.exists(os.path.join(inst, "cleanup-quarantine-20261027/files/plan_uploads/1/a.pdf"))
