"""Revision u8b9c0d1e2f3: employee cost profiles, estimate crews and the recorded pricing method (2 Nov 2026).

Disposable SQLite database upgraded from t7a8b9c0d1e2 with rows in existing tables: exactly the new tables and the five
new nullable columns appear, every existing row is unchanged (no backfill: the new columns are NULL), the insert-only
triggers exist, the downgrade refuses while anything new is held and otherwise restores the earlier schema exactly.
"""

from __future__ import annotations

import os
from datetime import datetime

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app

REVISION = "u8b9c0d1e2f3"
PRIOR = "t7a8b9c0d1e2"
NEW_TABLES = {"organization_person_cost_profiles", "organization_labour_cost_settings", "estimate_crew_members",
              "internal_summary_revisions"}
NEW_COLUMNS = {("organization_pricing_policies", "subcontract_markup_rate"),
               ("estimate_pricing_snapshots", "labour_rate"),
               ("estimate_pricing_snapshots", "subcontract_markup_rate"),
               ("estimate_versions", "pricing_method"),
               ("estimate_versions", "package_pricing_json"),
               ("estimate_versions", "pricing_rules_json"),
               ("organization_pricing_policies", "pricing_rules_json"),
               ("estimate_pricing_snapshots", "pricing_rules_json"),
               ("estimate_line_items", "pricing_treatment"),
               ("change_order_items", "cost_kind")}


def _config(db_path):
    cfg = Config("migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _tables(engine):
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type = 'table'"))}


def _columns(engine, tables):
    inspector = sa.inspect(engine)
    return {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)] for t in tables}


def _snapshot(engine, tables):
    out = {}
    with engine.connect() as conn:
        for t in sorted(tables - {"alembic_version"}):
            out[t] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"')))
    return out


def test_graph_head_is_the_cost_profiles_revision():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        script = ScriptDirectory.from_config(_config(":memory:"))
        assert script.get_heads() == [REVISION]
        assert script.get_revision(REVISION).down_revision == PRIOR


def _seed(engine):
    now = datetime(2026, 11, 2, 12, 0, 0)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT OR IGNORE INTO organizations (id, legal_name, display_name, currency, is_active, created_at, "
            "updated_at) VALUES ('ORG-001', 'Synthetic Builder', 'Synthetic', 'CAD', 1, :t, :t)"), {"t": now})
        conn.execute(sa.text("INSERT INTO clients (name, organization_id, created_at) VALUES "
                             "('Synthetic Client', 'ORG-001', :t)"), {"t": now})
        conn.execute(sa.text(
            "INSERT INTO organization_pricing_policies (organization_id, policy_code, version_number, method, "
            "target_gross_margin, overhead_treatment, profit_treatment, contingency_visibility, is_default, "
            "approval_status, created_at, updated_at) VALUES ('ORG-001', 'SYN-GM', 1, 'TRUE_GROSS_MARGIN', 0.15, "
            "'UNSPECIFIED', 'UNSPECIFIED', 'UNSPECIFIED', 1, 'ORG_APPROVED', :t, :t)"), {"t": now})
        conn.execute(sa.text(
            "INSERT INTO users (email, display_name, password_hash, is_active, created_at, updated_at) VALUES "
            "('owner@example.invalid', 'Owner Synthetic', 'x', 1, :t, :t)"), {"t": now})
    return now


def test_upgrade_is_additive_and_downgrade_is_guarded_and_reversible(tmp_path):
    db_path = tmp_path / "disposable.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        now = _seed(engine)
        before_tables = _tables(engine)
        before_columns = _columns(engine, before_tables)
        before = _snapshot(engine, before_tables)
        command.upgrade(cfg, REVISION)
        assert _tables(engine) - before_tables == NEW_TABLES
        after_columns = _columns(engine, before_tables)
        before_names = {t: {c[0] for c in cols} for t, cols in before_columns.items()}
        added = {(t, c[0]) for t in before_tables for c in after_columns[t] if c[0] not in before_names[t]}
        assert added == NEW_COLUMNS
        # The only other column change: signing_requests.client_id becomes NULL-able (for INTERNAL_APPROVAL only).
        changed = {(t, c[0]) for t in before_tables for c in after_columns[t]
                   if c[0] in before_names[t] and c not in before_columns[t]}
        assert changed == {("signing_requests", "client_id")}
        assert all(c[2] for t, cols in after_columns.items() for c in cols if (t, c[0]) in NEW_COLUMNS)  # nullable
        after = _snapshot(engine, before_tables)
        # Existing rows are unchanged apart from the new NULL columns (no backfill, no rewrite).
        assert after["clients"] == before["clients"] and after["organizations"] == before["organizations"]
        assert after["organization_pricing_policies"] == [r + ("None", "None") for r in before["organization_pricing_policies"]]
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
            assert conn.execute(sa.text("SELECT subcontract_markup_rate FROM organization_pricing_policies")).scalar() is None
            triggers = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))}
            assert {"organization_person_cost_profiles_no_update", "organization_person_cost_profiles_no_delete",
                    "organization_labour_cost_settings_no_update",
                    "organization_labour_cost_settings_no_delete"} <= triggers
        with engine.begin() as conn:
            conn.execute(sa.text(
                "INSERT INTO organization_labour_cost_settings (organization_id, wsib_rate_per_100, created_at, "
                "actor_user_id, actor_name) VALUES ('ORG-001', 3.55, :t, 1, 'Owner Synthetic')"), {"t": now})
        with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
            with engine.begin() as conn:
                conn.execute(sa.text("UPDATE organization_labour_cost_settings SET wsib_rate_per_100 = 1"))
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.begin() as conn:
            conn.execute(sa.text("DROP TRIGGER organization_labour_cost_settings_no_delete"))
            conn.execute(sa.text("DELETE FROM organization_labour_cost_settings"))
            conn.execute(sa.text("UPDATE organization_pricing_policies SET subcontract_markup_rate = 0.05"))
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):  # a new column holds a value
            command.downgrade(cfg, PRIOR)
        with engine.begin() as conn:
            conn.execute(sa.text("UPDATE organization_pricing_policies SET subcontract_markup_rate = NULL"))
        command.downgrade(cfg, PRIOR)
        assert _tables(engine) == before_tables
        assert _columns(engine, before_tables) == before_columns
        assert _snapshot(engine, before_tables) == before
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
        command.upgrade(cfg, REVISION)
        assert NEW_TABLES <= _tables(engine)
        engine.dispose()


def test_models_match_the_migration_columns(tmp_path):
    """db.create_all() (tests) and the migration (production) build the same new tables and columns."""
    from app import db

    migrated = tmp_path / "migrated.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{migrated}"})
    with application.app_context():
        command.upgrade(_config(migrated), REVISION)
    created = tmp_path / "created.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{created}"})
    with application.app_context():
        db.create_all()

    def shape(path):
        engine = sa.create_engine(f"sqlite:///{path}")
        inspector = sa.inspect(engine)
        tables = {t: {(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)} for t in NEW_TABLES}
        idx = {t: {i["name"] for i in inspector.get_indexes(t)} for t in NEW_TABLES}
        cols = {(t, c): next((str(x["type"]), x["nullable"]) for x in inspector.get_columns(t) if x["name"] == c)
                for t, c in NEW_COLUMNS}
        engine.dispose()
        return tables, idx, cols

    assert shape(migrated) == shape(created)


# ================================================================================ CaliSIGN internal approval (3 Nov 2026)
SIGNING_TABLES = ("signing_consent_versions", "signing_frozen_artifacts", "signing_requests", "signing_participants",
                  "signing_events", "signing_executed_artifacts", "signing_token_access_attempts")
FAMILIES = ("CHANGE_ORDER", "CONTRACT", "SUPPLIER_ORDER", "SUPPLIER_DELIVERY_CHANGE", "SUBCONTRACT")
ROLES = ("CUSTOMER", "ORGANIZATION_COUNTERSIGN", "CONTRACTOR", "SUPPLIER", "SUBCONTRACTOR")


def _seed_signing_rows(engine):
    """A signing request in every existing class at t7a8b9c0d1e2, with a participant of every role, events, an
    executed artifact and access attempts."""
    import hashlib

    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO signing_consent_versions (version_code, authority_class, body_text, "
                             "created_by_identifier, created_at) VALUES ('C-1', 'PRODUCTION', 'Synthetic consent', 't', "
                             "'2026-10-01 00:00:00')"))
        for n, family in enumerate(FAMILIES, 1):
            sha = hashlib.sha256(family.encode()).hexdigest()
            conn.execute(sa.text(
                "INSERT INTO signing_frozen_artifacts (organization_id, document_family, source_record_id, media_type, "
                "storage_key, sha256, created_at) VALUES ('ORG-001', :f, :n, 'application/pdf', :k, :s, "
                "'2026-10-01 00:00:00')"), {"f": family, "n": n, "k": f"ORG-001/{sha[:2]}/{sha}.pdf", "s": sha})
            conn.execute(sa.text(
                "INSERT INTO signing_requests (organization_id, request_number, document_family, source_record_id, "
                "project_id, client_id, frozen_artifact_id, authority_class, status, countersign_required, "
                "consent_version_id, expires_at, created_at, created_by_user_id, created_by_identifier, executed_at) "
                "VALUES ('ORG-001', :num, :f, :n, 1, 1, :n, 'PRODUCTION', 'EXECUTED', 1, 1, '2026-10-08 00:00:00', "
                "'2026-10-01 00:00:00', 1, 'owner@example.invalid', '2026-10-02 00:00:00')"),
                {"num": f"SIGN-2026-{n:04d}", "f": family, "n": n})
            for seq, role in enumerate(ROLES, 1):
                conn.execute(sa.text(
                    "INSERT INTO signing_participants (signing_request_id, sequence, role, invited_name, invited_email, "
                    "lookup_key, token_hash, confirmed_signer_name, signed_at, completion_ip, user_agent, created_at) "
                    "VALUES (:r, :seq, :role, 'Synthetic Signer', 's@example.invalid', :lk, :th, 'Synthetic Signer', "
                    "'2026-10-02 00:00:00', '203.0.113.9', 'Synthetic UA', '2026-10-01 00:00:00')"),
                    {"r": n, "seq": seq, "role": role, "lk": f"lk{n}{seq}", "th": "b" * 64})
            for event in ("REQUEST_CREATED", "SENT", "SIGNED", "EXECUTED"):
                conn.execute(sa.text(
                    "INSERT INTO signing_events (signing_request_id, event_type, actor_kind, actor_identifier, "
                    "artifact_sha256, created_at) VALUES (:r, :e, 'HUMAN', 'owner', :s, '2026-10-02 00:00:00')"),
                    {"r": n, "e": event, "s": sha})
            conn.execute(sa.text(
                "INSERT INTO signing_executed_artifacts (organization_id, signing_request_id, source_frozen_artifact_id, "
                "media_type, storage_key, sha256, created_at) VALUES ('ORG-001', :n, :n, 'application/pdf', :k, :s, "
                "'2026-10-02 00:00:00')"), {"n": n, "k": f"ORG-001/x/{n}.pdf", "s": "c" * 64})
        conn.execute(sa.text("INSERT INTO signing_token_access_attempts (presented_lookup_key, client_ip, outcome, "
                             "created_at) VALUES ('lk11', '203.0.113.9', 'SUCCESS', '2026-10-02 00:00:00')"))


def _rows_sha(engine, table):
    import hashlib

    with engine.connect() as conn:
        rows = conn.execute(sa.text(f'SELECT * FROM "{table}" ORDER BY rowid')).fetchall()
    return len(rows), hashlib.sha256(repr([tuple(r) for r in rows]).encode()).hexdigest()


def test_signing_rows_in_every_class_survive_upgrade_and_downgrade_byte_for_byte(tmp_path):
    db_path = tmp_path / "signing.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        _seed(engine)
        _seed_signing_rows(engine)
        before = {t: _rows_sha(engine, t) for t in SIGNING_TABLES}
        assert before["signing_requests"][0] == 5 and before["signing_participants"][0] == 25
        before_shape = _columns(engine, SIGNING_TABLES)
        command.upgrade(cfg, REVISION)
        assert {t: _rows_sha(engine, t) for t in SIGNING_TABLES} == before  # every row, byte for byte
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
        # The new class and role are accepted; a client is still required for every other class.
        insert_request = sa.text(
            "INSERT INTO signing_requests (organization_id, request_number, document_family, source_record_id, "
            "project_id, client_id, frozen_artifact_id, authority_class, status, countersign_required, "
            "consent_version_id, expires_at, created_at, created_by_user_id, created_by_identifier) VALUES "
            "('ORG-001', :num, :f, 99, 1, :c, 1, 'PRODUCTION', 'CREATED', 0, 1, '2026-11-10', '2026-11-03', 1, 'o')")
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(insert_request, {"num": "SIGN-X-1", "f": "CONTRACT", "c": None})
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(insert_request, {"num": "SIGN-X-2", "f": "SOMETHING", "c": 1})
        with engine.begin() as conn:
            conn.execute(insert_request, {"num": "SIGN-X-3", "f": "INTERNAL_APPROVAL", "c": None})
            conn.execute(sa.text("INSERT INTO signing_participants (signing_request_id, sequence, role, invited_name, "
                                 "invited_email, created_at) VALUES (6, 1, 'APPROVER', 'A', 'a@example.invalid', "
                                 "'2026-11-03')"))
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        assert {t: _rows_sha(engine, t) for t in SIGNING_TABLES if t not in ("signing_requests",
                                                                              "signing_participants")} == {
            t: v for t, v in before.items() if t not in ("signing_requests", "signing_participants")}
        with engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM signing_participants WHERE role = 'APPROVER'"))
            conn.execute(sa.text("DELETE FROM signing_requests WHERE document_family = 'INTERNAL_APPROVAL'"))
        command.downgrade(cfg, PRIOR)
        assert {t: _rows_sha(engine, t) for t in SIGNING_TABLES} == before
        assert _columns(engine, SIGNING_TABLES) == before_shape  # client_id NOT NULL again; constraints as before
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(insert_request, {"num": "SIGN-X-4", "f": "INTERNAL_APPROVAL", "c": 1})
        engine.dispose()


RELEASE_ARGS = ["--new-tables", "estimate_crew_members,internal_summary_revisions,organization_labour_cost_settings,"
                "organization_person_cost_profiles",
                "--altered-tables", "change_order_items,estimate_line_items,estimate_pricing_snapshots,"
                "estimate_versions,organization_pricing_policies,signing_requests",
                "--altered-checks", "ck_documents_sensitivity,ck_signing_frozen_artifacts_document_family,"
                "ck_signing_participants_role"]


# ================================================================================ Documents sensitivities (review B2)
DOCUMENT_TABLES = ("documents", "document_versions", "document_links", "document_events")


def _seed_documents(engine):
    """A document at every sensitivity that exists at t7a8b9c0d1e2, with a version, a link and an event."""
    with engine.begin() as conn:
        for n, sensitivity in enumerate(("STANDARD", "PEOPLE", "FINANCIAL"), 1):
            conn.execute(sa.text(
                "INSERT INTO documents (public_id, organization_id, title, document_type, type_basis, status, "
                "sensitivity, origin, created_by_name, created_at, updated_at) VALUES (:p, 'ORG-001', :t, 'OTHER', "
                "'CONFIRMED', 'ACTIVE', :s, 'UPLOAD', 'Owner Synthetic', '2026-10-01 00:00:00', '2026-10-01 00:00:00')"),
                {"p": f"{n:032x}", "t": f"Synthetic document {n}", "s": sensitivity})
            conn.execute(sa.text(
                "INSERT INTO document_versions (organization_id, document_id, version_number, is_current, source_kind, "
                "storage_key, sha256, byte_size, media_type, original_filename, availability, created_by_name, created_at) "
                "VALUES ('ORG-001', :n, 1, 1, 'UPLOAD', 'ORG-001/synthetic.pdf', :sha, 10, 'application/pdf', 'synthetic.pdf', 'AVAILABLE', "
                "'Owner Synthetic', '2026-10-01 00:00:00')"), {"n": n, "sha": f"{n}" * 64})
            conn.execute(sa.text(
                "INSERT INTO document_links (organization_id, document_id, context_kind, is_primary, linked_by_name, "
                "linked_at) VALUES ('ORG-001', :n, 'COMPANY', 1, 'Owner Synthetic', '2026-10-01 00:00:00')"), {"n": n})
            conn.execute(sa.text(
                "INSERT INTO document_events (organization_id, document_id, event_type, actor_name, at) VALUES "
                "('ORG-001', :n, 'CREATED', 'Owner Synthetic', '2026-10-01 00:00:00')"), {"n": n})


def test_documents_survive_the_sensitivity_widening_and_its_downgrade_byte_for_byte(tmp_path):
    db_path = tmp_path / "documents.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        _seed(engine)
        _seed_documents(engine)
        before = {t: _rows_sha(engine, t) for t in DOCUMENT_TABLES}
        assert before["documents"][0] == 3
        before_shape = _columns(engine, DOCUMENT_TABLES)
        command.upgrade(cfg, REVISION)
        assert {t: _rows_sha(engine, t) for t in DOCUMENT_TABLES} == before
        assert _columns(engine, DOCUMENT_TABLES) == before_shape
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("PRAGMA foreign_key_check")).fetchall() == []
        update = sa.text("UPDATE documents SET sensitivity = :s WHERE id = 3")
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(update, {"s": "SOMETHING"})
        with engine.begin() as conn:
            conn.execute(update, {"s": "ECONOMICS"})
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.begin() as conn:
            conn.execute(update, {"s": "EMPLOYEE_COST"})
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.begin() as conn:
            conn.execute(update, {"s": "FINANCIAL"})
        command.downgrade(cfg, PRIOR)
        assert {t: _rows_sha(engine, t) for t in DOCUMENT_TABLES} == before
        assert _columns(engine, DOCUMENT_TABLES) == before_shape
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(update, {"s": "ECONOMICS"})
        engine.dispose()


def test_a_customer_estimate_revision_is_frozen_and_never_carries_wages(tmp_path):
    db_path = tmp_path / "revisions.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, REVISION)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        cols = [c[0] for c in _columns(engine, ("internal_summary_revisions",))["internal_summary_revisions"]]
        assert "document_type" in cols
        with engine.connect() as conn:
            sql = conn.execute(sa.text("SELECT sql FROM sqlite_master WHERE name = 'internal_summary_revisions'")).scalar()
        assert "ck_internal_summary_revisions_document_type" in sql
        assert "ck_internal_summary_revisions_customer_estimate" in sql
        assert 'UNIQUE (estimate_id, document_type, revision_number)' in sql
        assert "ck_internal_summary_revisions_pairing" in sql and "paired_revision_id" in sql
        with engine.connect() as conn:
            index = conn.execute(sa.text("SELECT sql FROM sqlite_master WHERE name = "
                                         "'uq_internal_summary_revisions_series'")).scalar()
        assert "UNIQUE INDEX" in index and "WHERE paired_revision_id IS NULL" in index  # review m1
        engine.dispose()


def test_the_release_rehearsal_proves_every_row_identical(tmp_path):
    """The release gate's migration rehearsal (tools/release/migration_check.py) with this release's arguments, on a
    database at t7a8b9c0d1e2 holding signing rows in every class."""
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "rehearse.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        command.upgrade(_config(db_path), PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        _seed(engine)
        _seed_signing_rows(engine)
        _seed_documents(engine)
        engine.dispose()
    result = subprocess.run([sys.executable, str(root / "tools" / "release" / "migration_check.py"), "rehearse",
                             "--db", str(db_path), "--from", PRIOR, "--to", REVISION] + RELEASE_ARGS,
                            cwd=root, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MIGRATION_REHEARSAL=ok" in result.stdout and "every row identical" in result.stdout
    assert result.stdout.count("ALTERED_CHECK=") == 3 and "INTERNAL_APPROVAL" in result.stdout
    assert "ECONOMICS" in result.stdout
