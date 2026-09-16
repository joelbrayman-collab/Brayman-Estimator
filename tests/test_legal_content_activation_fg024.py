"""FG-024 TECH-A human/counsel activation and authority-class safety."""

from __future__ import annotations

import os
from datetime import date, datetime

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Project
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    LegalContentActivationEvent,
    LegalContentJurisdictionPackage,
    LegalContentObject,
)
from app.services.commercial_context import create_initial_commercial_context
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    AUTHORITY_PRODUCTION,
    AUTHORITY_SYNTHETIC_UAT,
    STATUS_AVAILABLE,
    STATUS_BLOCK,
    select_legal_content_package_for_project,
    select_synthetic_uat_legal_content_package_for_project,
)
from app.services.legal_content_update import (
    ACTOR_AI,
    ACTOR_AUTOMATION,
    ACTOR_COUNSEL,
    ACTOR_HUMAN,
    BLOCK_ACTIVE_PACKAGE_EXISTS,
    BLOCK_ACTOR_IDENTIFIER_REQUIRED,
    BLOCK_AI_CANNOT_ACTIVATE,
    BLOCK_OBJECTS_NOT_APPROVED,
    BLOCK_PACKAGE_NOT_APPROVED,
    LegalContentUpdateError,
    activate_legal_content,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile

OTTAWA_LOCATION = {
    "street": "100 Test Civic Street",
    "municipality": "Ottawa",
    "province_state": "Ontario",
    "postal_zip": None,
    "country": "Canada",
}

COMMERCIAL_CREATE = {
    "project_type": "Addition",
    "pricing_posture": "Competitive",
    "execution_risk": "Normal",
    "schedule_condition": "Normal",
    "site_condition": "Normal",
    "estimate_stage": "Preliminary",
    "delivery_model": "Self-Perform",
    "justification_reason": "",
}

PROTECTED_ESTIMATE_NUMBER = "EST-2026-0019"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg024-techa",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


def _make_project(*, name="FG024 TECH-A Project"):
    client_row = Client(name="FG024 TECH-A Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.commit()
    project = Project(
        name=name,
        address="TBD",
        client_id=client_row.id,
        status="Lead",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    return project


def _ottawa_project():
    project = _make_project()
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    return project


def _node(code="CA-ON"):
    return JurisdictionDefinition.query.filter_by(code=code).one()


def _approved_package(
    *,
    code,
    authority_class=AUTHORITY_SYNTHETIC_UAT,
    object_state="APPROVED",
    with_object=True,
):
    node = _node()
    now = datetime.utcnow()
    row = LegalContentJurisdictionPackage(
        package_code=code,
        jurisdiction_definition_id=node.id,
        country_code="CA",
        province_or_state_code="CA-ON",
        support_status="SUPPORTED",
        library_state="APPROVED",
        authority_class=authority_class,
        counsel_approved_at=now,
        counsel_approved_by="Counsel Test",
        provenance="SYNTHETIC_UAT TEST DATA ONLY — not counsel approval",
        created_at=now,
    )
    db.session.add(row)
    db.session.flush()
    if with_object:
        obj = LegalContentObject(
            package_id=row.id,
            kind="contract_provision",
            version_number=1,
            library_state=object_state,
            source_citation="TEST CITATION ONLY",
            body="SYNTHETIC TEST BODY — NOT LEGAL AUTHORITY",
            created_at=now,
        )
        db.session.add(obj)
    db.session.commit()
    return row


def test_human_can_activate_approved_synthetic_package(app):
    package = _approved_package(code="TEST-ON-TECHA-HUMAN")
    result = activate_legal_content(
        package.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office-human",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 12, 31),
    )
    db.session.refresh(package)
    assert result.id == package.id
    assert package.library_state == "ACTIVE"
    assert package.authority_class == AUTHORITY_SYNTHETIC_UAT
    assert package.activated_by == "office-human"
    assert package.activated_at is not None
    assert package.effective_from == date(2026, 1, 1)
    event = LegalContentActivationEvent.query.filter_by(package_id=package.id).one()
    assert event.action == "ACTIVATE"
    assert event.actor_kind == ACTOR_HUMAN
    assert event.actor_identifier == "office-human"
    assert event.created_at is not None
    assert event.predecessor_package_id is None


def test_counsel_can_activate_approved_synthetic_package(app):
    package = _approved_package(code="TEST-ON-TECHA-COUNSEL")
    activate_legal_content(
        package.id,
        actor_kind=ACTOR_COUNSEL,
        actor_identifier="counsel-id",
        effective_from=date(2026, 1, 1),
    )
    db.session.refresh(package)
    assert package.library_state == "ACTIVE"
    event = LegalContentActivationEvent.query.filter_by(package_id=package.id).one()
    assert event.actor_kind == ACTOR_COUNSEL
    assert event.actor_identifier == "counsel-id"


def test_ai_cannot_activate(app):
    package = _approved_package(code="TEST-ON-TECHA-AI")
    with pytest.raises(LegalContentUpdateError) as exc:
        activate_legal_content(
            package.id,
            actor_kind=ACTOR_AI,
            actor_identifier="model",
            effective_from=date(2026, 1, 1),
        )
    assert exc.value.code == BLOCK_AI_CANNOT_ACTIVATE
    db.session.refresh(package)
    assert package.library_state == "APPROVED"
    assert LegalContentActivationEvent.query.count() == 0


def test_automation_cannot_activate(app):
    package = _approved_package(code="TEST-ON-TECHA-AUTO")
    with pytest.raises(LegalContentUpdateError) as exc:
        activate_legal_content(
            package.id,
            actor_kind=ACTOR_AUTOMATION,
            actor_identifier="job",
            effective_from=date(2026, 1, 1),
        )
    assert exc.value.code == BLOCK_AI_CANNOT_ACTIVATE
    db.session.refresh(package)
    assert package.library_state == "APPROVED"


def test_activation_event_is_append_only(app):
    package = _approved_package(code="TEST-ON-TECHA-APPEND")
    activate_legal_content(
        package.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office-human",
        effective_from=date(2026, 1, 1),
    )
    first = LegalContentActivationEvent.query.one()
    first_id = first.id
    first_created = first.created_at
    successor = _approved_package(code="TEST-ON-TECHA-APPEND-2")
    activate_legal_content(
        successor.id,
        actor_kind=ACTOR_COUNSEL,
        actor_identifier="counsel-id",
        effective_from=date(2026, 2, 1),
        supersede_package_id=package.id,
    )
    events = LegalContentActivationEvent.query.order_by(
        LegalContentActivationEvent.id
    ).all()
    assert len(events) == 3
    still = db.session.get(LegalContentActivationEvent, first_id)
    assert still.action == "ACTIVATE"
    assert still.created_at == first_created
    assert still.actor_identifier == "office-human"
    assert {event.action for event in events} == {"ACTIVATE", "SUPERSEDE"}
    assert not hasattr(activate_legal_content, "unactivate")
    assert not hasattr(activate_legal_content, "delete_activation_event")


def test_one_active_per_jurisdiction_node_blocks_without_supersede(app):
    first = _approved_package(code="TEST-ON-TECHA-ONE")
    activate_legal_content(
        first.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office-human",
        effective_from=date(2026, 1, 1),
    )
    second = _approved_package(code="TEST-ON-TECHA-TWO")
    with pytest.raises(LegalContentUpdateError) as exc:
        activate_legal_content(
            second.id,
            actor_kind=ACTOR_HUMAN,
            actor_identifier="office-human",
            effective_from=date(2026, 2, 1),
        )
    assert exc.value.code == BLOCK_ACTIVE_PACKAGE_EXISTS
    db.session.refresh(first)
    db.session.refresh(second)
    assert first.library_state == "ACTIVE"
    assert second.library_state == "APPROVED"
    assert LegalContentActivationEvent.query.count() == 1


def test_explicit_supersede_is_atomic(app):
    predecessor = _approved_package(code="TEST-ON-TECHA-PRED")
    activate_legal_content(
        predecessor.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office-human",
        effective_from=date(2026, 1, 1),
    )
    successor = _approved_package(code="TEST-ON-TECHA-SUCC")
    activate_legal_content(
        successor.id,
        actor_kind=ACTOR_COUNSEL,
        actor_identifier="counsel-id",
        effective_from=date(2026, 3, 1),
        supersede_package_id=predecessor.id,
    )
    db.session.refresh(predecessor)
    db.session.refresh(successor)
    assert predecessor.library_state == "SUPERSEDED"
    assert predecessor.superseded_by_id == successor.id
    assert successor.library_state == "ACTIVE"
    assert successor.activated_by == "counsel-id"
    assert LegalContentJurisdictionPackage.query.filter_by(
        jurisdiction_definition_id=predecessor.jurisdiction_definition_id,
        library_state="ACTIVE",
    ).count() == 1


def test_failed_activation_leaves_prior_state_intact(app):
    package = _approved_package(code="TEST-ON-TECHA-FAIL")
    activate_legal_content(
        package.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office-human",
        effective_from=date(2026, 1, 1),
    )
    prior_events = LegalContentActivationEvent.query.count()
    unapproved = _approved_package(
        code="TEST-ON-TECHA-PROPOSED-OBJ",
        object_state="PROPOSED",
    )
    with pytest.raises(LegalContentUpdateError) as obj_exc:
        activate_legal_content(
            unapproved.id,
            actor_kind=ACTOR_HUMAN,
            actor_identifier="office-human",
            effective_from=date(2026, 2, 1),
            supersede_package_id=package.id,
        )
    assert obj_exc.value.code == BLOCK_OBJECTS_NOT_APPROVED
    db.session.refresh(package)
    db.session.refresh(unapproved)
    assert package.library_state == "ACTIVE"
    assert unapproved.library_state == "APPROVED"
    assert LegalContentActivationEvent.query.count() == prior_events
    with pytest.raises(LegalContentUpdateError) as proposed_exc:
        activate_legal_content(
            package.id,
            actor_kind=ACTOR_HUMAN,
            actor_identifier="office-human",
            effective_from=date(2026, 3, 1),
        )
    assert proposed_exc.value.code == BLOCK_PACKAGE_NOT_APPROVED
    db.session.refresh(package)
    assert package.library_state == "ACTIVE"


def test_synthetic_uat_active_does_not_satisfy_production_selection(app):
    project = _ottawa_project()
    package = _approved_package(code="TEST-ON-TECHA-SYN-SEL")
    activate_legal_content(
        package.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office-human",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 12, 31),
    )
    production = select_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 14)
    )
    assert production.available is False
    assert production.status == STATUS_BLOCK
    assert production.package_id != package.id or production.available is False


def test_production_selection_blocks_when_no_active_production_package(app):
    project = _ottawa_project()
    result = select_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 14)
    )
    assert result.available is False
    assert result.status == STATUS_BLOCK


def test_explicit_synthetic_technical_path_uses_synthetic_uat_only(app):
    project = _ottawa_project()
    package = _approved_package(code="TEST-ON-TECHA-SYN-PATH")
    activate_legal_content(
        package.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office-human",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 12, 31),
    )
    synthetic = select_synthetic_uat_legal_content_package_for_project(
        project.id, as_of=date(2026, 9, 14)
    )
    assert synthetic.available is True
    assert synthetic.status == STATUS_AVAILABLE
    assert synthetic.package_id == package.id
    production = select_legal_content_package_for_project(
        project.id,
        as_of=date(2026, 9, 14),
        authority_class=AUTHORITY_PRODUCTION,
    )
    assert production.available is False


def test_cli_human_activation_and_ai_not_accepted(app):
    package = _approved_package(code="TEST-ON-TECHA-CLI")
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "legal-content",
            "activate",
            "--package-id",
            str(package.id),
            "--actor-kind",
            "HUMAN",
            "--actor-identifier",
            "cli-human",
            "--effective-from",
            "2026-01-01",
        ]
    )
    assert result.exit_code == 0, result.output
    db.session.refresh(package)
    assert package.library_state == "ACTIVE"
    assert package.activated_by == "cli-human"
    ai_result = runner.invoke(
        args=[
            "legal-content",
            "activate",
            "--package-id",
            str(package.id),
            "--actor-kind",
            "AI",
            "--actor-identifier",
            "model",
            "--effective-from",
            "2026-01-01",
        ]
    )
    assert ai_result.exit_code != 0


def test_empty_actor_identifier_blocks(app):
    package = _approved_package(code="TEST-ON-TECHA-EMPTY-ACTOR")
    with pytest.raises(LegalContentUpdateError) as exc:
        activate_legal_content(
            package.id,
            actor_kind=ACTOR_HUMAN,
            actor_identifier="  ",
            effective_from=date(2026, 1, 1),
        )
    assert exc.value.code == BLOCK_ACTOR_IDENTIFIER_REQUIRED


def test_protected_estimate_identity_is_not_used(app):
    from app.models.estimate import Estimate

    assert Estimate.query.filter_by(estimate_number=PROTECTED_ESTIMATE_NUMBER).count() == 0


def test_alembic_fg024_tech_a_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg024_tech_a_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == ["f6e7f8a9b0c1"]

        command.upgrade(alembic_cfg, "d3e4f5a6b7c8")
        engine = db.engine
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(legal_content_jurisdiction_packages)")
                )
            }
            assert "authority_class" not in columns
            assert "activated_by" not in columns
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_activation_events" not in tables
            conn.execute(
                sa.text(
                    "INSERT INTO legal_content_jurisdiction_packages ("
                    "package_code, jurisdiction_definition_id, country_code, "
                    "province_or_state_code, support_status, library_state, "
                    "provenance, created_at"
                    ") SELECT 'HIST-SYNTHETIC-TECHA', id, 'CA', 'CA-ON', "
                    "'SUPPORTED', 'APPROVED', "
                    "'HISTORICAL SYNTHETIC — not production', "
                    "'2026-01-01 00:00:00' FROM jurisdiction_definitions "
                    "WHERE code = 'CA-ON' LIMIT 1"
                )
            )

        command.upgrade(alembic_cfg, "e4f5a6b7c8d9")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(legal_content_jurisdiction_packages)")
                )
            }
            assert "authority_class" in columns
            assert "activated_by" in columns
            classified = conn.execute(
                sa.text(
                    "SELECT authority_class FROM legal_content_jurisdiction_packages "
                    "WHERE package_code = 'HIST-SYNTHETIC-TECHA'"
                )
            ).scalar()
            assert classified == "SYNTHETIC_UAT"
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_activation_events" in tables
            assert conn.execute(
                sa.text("SELECT COUNT(*) FROM legal_content_activation_events")
            ).scalar() == 0
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == ["e4f5a6b7c8d9"]

        command.downgrade(alembic_cfg, "d3e4f5a6b7c8")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_activation_events" not in tables
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(legal_content_jurisdiction_packages)")
                )
            }
            assert "authority_class" not in columns
            assert "activated_by" not in columns
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == ["d3e4f5a6b7c8"]
