"""Tests for FG-024 Slice B legal-content source / snapshot / candidate foundation."""

from __future__ import annotations

import inspect
import os
from datetime import date, datetime

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Organization, Project, ProposalTemplate
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    SOURCE_CLASSES,
    LegalContentCandidateChange,
    LegalContentCandidateImpact,
    LegalContentJurisdictionPackage,
    LegalContentObject,
    LegalContentReviewEvent,
    LegalContentSource,
    LegalContentSourceSnapshot,
)
from app.models.permit_intelligence import PermitRule
from app.services.commercial_context import create_initial_commercial_context
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.legal_content import (
    BLOCK_JURISDICTION_NOT_SUPPORTED,
    STATUS_AVAILABLE,
    STATUS_BLOCK,
    STATUS_WARN,
    WARN_PENDING_CANDIDATE,
    select_legal_content_package_for_project,
)
from app.services.legal_content_update import (
    ACTOR_AI,
    ACTOR_AUTOMATION,
    ACTOR_COUNSEL,
    ACTOR_HUMAN,
    BLOCK_ACTIVE_MUTATION_FORBIDDEN,
    BLOCK_ACTOR_IDENTIFIER_REQUIRED,
    BLOCK_AI_CANNOT_ACTIVATE,
    BLOCK_AI_CANNOT_APPROVE,
    BLOCK_AI_CANNOT_ROUTE,
    BLOCK_CANDIDATE_NOT_AUTHORITY,
    BLOCK_UNKNOWN_SOURCE_CLASS,
    CANDIDATE_COUNSEL_REVIEW,
    CANDIDATE_PROPOSED,
    LegalContentUpdateError,
    activate_legal_content,
    approve_content_version,
    assert_platform_sources_not_org_owned,
    candidate_is_legal_authority,
    create_candidate_from_snapshot,
    deactivate_active_from_candidate,
    fingerprint_source_payload,
    ingest_source_snapshot,
    register_legal_content_source,
    route_candidate_to_counsel_review,
    source_class_is_legal_authority,
    supersede_active_from_candidate,
    use_candidate_as_legal_authority,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.permit_foundation import establish_project_location_and_profile
from app.services import legal_content as legal_content_service
from app.services import legal_content_update as update_service

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

PAYLOAD_V1 = "SYNTHETIC SOURCE PAYLOAD V1 — NOT LEGAL CONTENT"
PAYLOAD_V2 = "SYNTHETIC SOURCE PAYLOAD V2 — STILL NOT LEGAL CONTENT"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg024-b",
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


def _make_project(
    *,
    name="FG024B Project",
    address="TBD",
    org_id=DEFAULT_ORGANIZATION_ID,
    client_name="FG024B Client",
):
    client_row = Client(name=client_name, organization_id=org_id)
    db.session.add(client_row)
    db.session.commit()
    project = Project(
        name=name,
        address=address,
        client_id=client_row.id,
        status="Lead",
        organization_id=org_id,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(project_id=project.id, data=COMMERCIAL_CREATE)
    db.session.commit()
    return project


def _ottawa_project(**kwargs):
    org_id = kwargs.get("org_id", DEFAULT_ORGANIZATION_ID)
    project = _make_project(**kwargs)
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        permit_context_class="Additional dwelling/coach house",
        organization_id=org_id,
        commit=True,
    )
    return project


def _node(code):
    return JurisdictionDefinition.query.filter_by(code=code).one()


def _package(
    *,
    code,
    jurisdiction_code,
    library_state,
    support_status="SUPPORTED",
    effective_from=None,
    effective_to=None,
    counsel_approved_by=None,
):
    node = _node(jurisdiction_code)
    country_code = node.code.split("-")[0]
    province = None
    if node.kind == "province_state":
        province = node.code
    elif node.kind == "municipality" and node.parent is not None:
        province = node.parent.code
    now = datetime.utcnow()
    row = LegalContentJurisdictionPackage(
        package_code=code,
        jurisdiction_definition_id=node.id,
        country_code=country_code,
        province_or_state_code=province,
        support_status=support_status,
        library_state=library_state,
        authority_class="PRODUCTION",
        effective_from=effective_from,
        effective_to=effective_to,
        counsel_approved_at=now if counsel_approved_by else None,
        counsel_approved_by=counsel_approved_by,
        activated_at=now if library_state == "ACTIVE" else None,
        activated_by="test-activator" if library_state == "ACTIVE" else None,
        provenance="TEST DATA ONLY — not counsel approval",
        created_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return row


def _object(package, *, kind="contract_provision", version_number=1, library_state="PROPOSED"):
    row = LegalContentObject(
        package_id=package.id,
        kind=kind,
        version_number=version_number,
        library_state=library_state,
        source_citation="TEST CITATION ONLY",
        body=None,
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def _source(*, source_class="OFFICIAL_PRIMARY", code="TEST-SRC-ON-001"):
    node = _node("CA-ON")
    return register_legal_content_source(
        source_code=code,
        source_class=source_class,
        source_identity="Synthetic Ontario instrument (test only)",
        issuing_identity="Test Issuer",
        source_citation="TEST-CITE-001",
        source_url="https://example.test/legal-content-source",
        jurisdiction_definition_id=node.id,
        provenance="TEST FIXTURE — not legal approval",
    )


def test_source_registration_with_governed_class(app):
    source = _source()
    assert source.source_class == "OFFICIAL_PRIMARY"
    assert source.source_class in SOURCE_CLASSES
    assert source_class_is_legal_authority(source.source_class) is False
    assert source.library_state if hasattr(source, "library_state") else True
    assert not hasattr(source, "library_state")
    assert not hasattr(LegalContentSource, "organization_id")
    with pytest.raises(LegalContentUpdateError) as exc:
        register_legal_content_source(
            source_code="BAD-CLASS",
            source_class="PRIMARY_LEGAL_AUTHORITY",
            source_identity="must fail",
        )
    assert exc.value.code == BLOCK_UNKNOWN_SOURCE_CLASS


def test_source_snapshot_persistence(app):
    source = _source()
    result = ingest_source_snapshot(source.id, PAYLOAD_V1, source_revision="r1")
    assert result.unchanged is False
    assert result.snapshot.source_id == source.id
    assert result.payload_sha256 == fingerprint_source_payload(PAYLOAD_V1)
    assert result.snapshot.payload_text == PAYLOAD_V1
    assert LegalContentSourceSnapshot.query.count() == 1
    assert LegalContentCandidateChange.query.count() == 0


def test_identical_snapshot_does_not_create_false_change(app):
    source = _source()
    first = ingest_source_snapshot(source.id, PAYLOAD_V1)
    second = ingest_source_snapshot(source.id, PAYLOAD_V1)
    assert second.unchanged is True
    assert second.snapshot.id == first.snapshot.id
    assert LegalContentSourceSnapshot.query.count() == 1
    assert LegalContentCandidateChange.query.count() == 0


def test_changed_snapshot_can_support_candidate(app):
    source = _source()
    first = ingest_source_snapshot(source.id, PAYLOAD_V1)
    second = ingest_source_snapshot(source.id, PAYLOAD_V2)
    assert second.unchanged is False
    assert second.snapshot.id != first.snapshot.id
    assert second.payload_sha256 != first.payload_sha256
    candidate = create_candidate_from_snapshot(
        second.snapshot.id,
        change_summary="Detected synthetic difference",
        detected_difference="v1 != v2",
    )
    assert candidate.candidate_state == CANDIDATE_PROPOSED
    assert candidate.snapshot_id == second.snapshot.id
    assert candidate.source_id == source.id


def test_candidate_retains_source_provenance(app):
    source = _source()
    snap = ingest_source_snapshot(source.id, PAYLOAD_V2).snapshot
    candidate = create_candidate_from_snapshot(snap.id, change_summary="provenance check")
    assert candidate.source_id == source.id
    assert candidate.snapshot_id == snap.id
    assert candidate.jurisdiction_definition_id == source.jurisdiction_definition_id
    assert candidate.source.source_class == "OFFICIAL_PRIMARY"
    assert candidate.snapshot.payload_sha256 == fingerprint_source_payload(PAYLOAD_V2)


def test_candidate_is_not_legal_authority(app):
    source = _source()
    snap = ingest_source_snapshot(source.id, PAYLOAD_V1).snapshot
    candidate = create_candidate_from_snapshot(snap.id)
    assert candidate_is_legal_authority(candidate) is False
    assert candidate.candidate_state not in {"APPROVED", "ACTIVE"}
    assert not hasattr(candidate, "library_state")
    with pytest.raises(LegalContentUpdateError) as exc:
        use_candidate_as_legal_authority(candidate.id)
    assert exc.value.code == BLOCK_CANDIDATE_NOT_AUTHORITY


def test_ai_cannot_set_approved(app):
    source = _source()
    package = _package(
        code="TEST-ON-ACTIVE-B1",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        support_status="SUPPORTED",
        effective_from=date(2026, 1, 1),
        counsel_approved_by="Counsel Test",
    )
    proposed = _object(package, version_number=2, library_state="PROPOSED")
    snap = ingest_source_snapshot(source.id, PAYLOAD_V2).snapshot
    candidate = create_candidate_from_snapshot(
        snap.id,
        affected_package_id=package.id,
        proposed_object_id=proposed.id,
        detected_difference="AI summary only",
    )
    route_candidate_to_counsel_review(
        candidate.id,
        actor_kind=ACTOR_HUMAN,
        actor_identifier="office",
    )
    with pytest.raises(LegalContentUpdateError) as exc:
        approve_content_version(
            candidate.id,
            actor_kind=ACTOR_AI,
            actor_identifier="model",
        )
    assert exc.value.code == BLOCK_AI_CANNOT_APPROVE
    db.session.refresh(proposed)
    assert proposed.library_state == "PROPOSED"
    with pytest.raises(LegalContentUpdateError) as auto_exc:
        approve_content_version(
            candidate.id,
            actor_kind=ACTOR_AUTOMATION,
            actor_identifier="job",
        )
    assert auto_exc.value.code == BLOCK_AI_CANNOT_APPROVE


def test_ai_cannot_set_active(app):
    with pytest.raises(LegalContentUpdateError) as exc:
        activate_legal_content(actor_kind=ACTOR_AI)
    assert exc.value.code == BLOCK_AI_CANNOT_ACTIVATE
    with pytest.raises(LegalContentUpdateError) as auto_exc:
        activate_legal_content(actor_kind=ACTOR_AUTOMATION)
    assert auto_exc.value.code == BLOCK_AI_CANNOT_ACTIVATE
    with pytest.raises(LegalContentUpdateError) as human_exc:
        activate_legal_content(actor_kind=ACTOR_HUMAN)
    assert human_exc.value.code == BLOCK_ACTOR_IDENTIFIER_REQUIRED


def test_candidate_does_not_supersede_or_deactivate_active(app):
    source = _source()
    package = _package(
        code="TEST-ON-ACTIVE-B2",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        support_status="SUPPORTED",
        effective_from=date(2026, 1, 1),
        counsel_approved_by="Counsel Test",
    )
    previous = _object(package, version_number=1, library_state="ACTIVE")
    proposed = _object(package, version_number=2, library_state="PROPOSED")
    snap = ingest_source_snapshot(source.id, PAYLOAD_V2).snapshot
    candidate = create_candidate_from_snapshot(
        snap.id,
        affected_package_id=package.id,
        affected_object_id=previous.id,
        proposed_object_id=proposed.id,
    )
    db.session.refresh(package)
    db.session.refresh(previous)
    assert package.library_state == "ACTIVE"
    assert package.superseded_by_id is None
    assert package.support_status == "SUPPORTED"
    assert previous.library_state == "ACTIVE"
    with pytest.raises(LegalContentUpdateError) as exc:
        supersede_active_from_candidate(candidate.id)
    assert exc.value.code == BLOCK_ACTIVE_MUTATION_FORBIDDEN
    with pytest.raises(LegalContentUpdateError) as deact:
        deactivate_active_from_candidate(candidate.id)
    assert deact.value.code == BLOCK_ACTIVE_MUTATION_FORBIDDEN
    route_candidate_to_counsel_review(
        candidate.id, actor_kind=ACTOR_COUNSEL, actor_identifier="counsel"
    )
    approved = approve_content_version(
        candidate.id, actor_kind=ACTOR_COUNSEL, actor_identifier="counsel"
    )
    db.session.refresh(package)
    db.session.refresh(previous)
    assert approved.library_state == "APPROVED"
    assert approved.library_state != "ACTIVE"
    assert package.library_state == "ACTIVE"
    assert package.superseded_by_id is None
    assert previous.library_state == "ACTIVE"


def test_legal_content_gate_remains_human_controlled(app):
    source = _source()
    package = _package(
        code="TEST-ON-PKG-GATE",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        support_status="SUPPORTED",
        effective_from=date(2026, 1, 1),
        counsel_approved_by="Counsel Test",
    )
    proposed = _object(package, version_number=2, library_state="PROPOSED")
    snap = ingest_source_snapshot(source.id, PAYLOAD_V2).snapshot
    candidate = create_candidate_from_snapshot(
        snap.id,
        affected_package_id=package.id,
        proposed_object_id=proposed.id,
    )
    with pytest.raises(LegalContentUpdateError) as route_exc:
        route_candidate_to_counsel_review(
            candidate.id, actor_kind=ACTOR_AI, actor_identifier="model"
        )
    assert route_exc.value.code == BLOCK_AI_CANNOT_ROUTE
    route_candidate_to_counsel_review(
        candidate.id, actor_kind=ACTOR_HUMAN, actor_identifier="office"
    )
    db.session.refresh(candidate)
    assert candidate.candidate_state == CANDIDATE_COUNSEL_REVIEW
    approve_content_version(
        candidate.id, actor_kind=ACTOR_COUNSEL, actor_identifier="counsel-id"
    )
    events = LegalContentReviewEvent.query.filter_by(candidate_id=candidate.id).all()
    assert any(event.action == "APPROVE_VERSION" for event in events)
    assert all(event.actor_kind != ACTOR_AI for event in events if event.action == "APPROVE_VERSION")


def test_platform_not_org_owned_and_jurisdiction_reuses_adr037(app):
    assert assert_platform_sources_not_org_owned() is True
    source = _source()
    assert source.jurisdiction_definition_id == _node("CA-ON").id
    assert source.jurisdiction.code == "CA-ON"
    for model in (
        LegalContentSource,
        LegalContentSourceSnapshot,
        LegalContentCandidateChange,
        LegalContentCandidateImpact,
        LegalContentReviewEvent,
    ):
        assert not hasattr(model, "organization_id")
        columns = {column.name for column in model.__table__.columns}
        assert "organization_id" not in columns


def test_no_permit_rules_family05_or_generic_na_fallback(app):
    permit_before = PermitRule.query.count()
    templates_before = ProposalTemplate.query.count()
    source = _source(source_class="SECONDARY_INFORMATIONAL", code="TEST-SRC-SEC")
    ingest_source_snapshot(source.id, PAYLOAD_V1)
    project = _ottawa_project()
    result = select_legal_content_package_for_project(project.id)
    assert result.available is False
    assert result.status == STATUS_BLOCK
    assert result.block_code == BLOCK_JURISDICTION_NOT_SUPPORTED
    assert PermitRule.query.count() == permit_before
    assert ProposalTemplate.query.count() == templates_before
    source_text = inspect.getsource(update_service)
    assert "PermitRule" not in source_text
    assert "ProposalTemplate" not in source_text
    assert "NORTH_AMERICA" not in source_text
    assert "generic" not in source_text.lower()


def test_no_live_monitoring_behaviour(app):
    names = set(dir(update_service))
    forbidden = {
        "start_source_watcher",
        "poll_legal_sources",
        "schedule_source_monitor",
        "send_stale_jurisdiction_alert",
        "watch_legal_sources",
        "notify_unsigned_impact",
    }
    assert forbidden.isdisjoint(names)
    source_text = inspect.getsource(update_service)
    for token in ("APScheduler", "BackgroundScheduler", "watchdog", "cron"):
        assert token not in source_text


def test_active_package_still_selected_while_candidate_exists(app):
    source = _source()
    package = _package(
        code="TEST-ON-ACTIVE-SELECT",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        support_status="SUPPORTED",
        effective_from=date(2026, 1, 1),
        counsel_approved_by="Counsel Test",
    )
    snap = ingest_source_snapshot(source.id, PAYLOAD_V2).snapshot
    create_candidate_from_snapshot(snap.id, affected_package_id=package.id)
    db.session.refresh(package)
    assert package.library_state == "ACTIVE"
    assert package.support_status == "SUPPORTED"
    project = _ottawa_project()
    result = select_legal_content_package_for_project(project.id)
    assert result.available is True
    assert result.status == STATUS_WARN
    assert result.warn_code == WARN_PENDING_CANDIDATE
    assert result.package_id == package.id
    assert result.library_state == "ACTIVE"


def test_slice_a_selector_unchanged_helpers_absent():
    names = dir(legal_content_service)
    forbidden = {
        "activate_package",
        "approve_package",
        "mark_approved",
        "mark_active",
        "promote_package",
        "create_candidate_from_snapshot",
    }
    assert forbidden.isdisjoint(set(names))


def test_alembic_fg024_slice_b_upgrade_empty_and_downgrade(tmp_path):
    db_path = tmp_path / "fg024_slice_b_migration.db"
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
        assert script.get_heads() == ["j0e1f2a3b4c5"]

        command.upgrade(alembic_cfg, "b1c2d3e4f5a6")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_jurisdiction_packages" in tables
            assert "legal_content_sources" not in tables
            assert conn.execute(
                sa.text("SELECT COUNT(*) FROM legal_content_jurisdiction_packages")
            ).scalar() == 0

        command.upgrade(alembic_cfg, "c2d3e4f5a6b7")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            for name in (
                "legal_content_sources",
                "legal_content_source_snapshots",
                "legal_content_candidate_changes",
                "legal_content_candidate_impacts",
                "legal_content_review_events",
            ):
                assert name in tables
                assert conn.execute(sa.text(f"SELECT COUNT(*) FROM {name}")).scalar() == 0
            source_cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(legal_content_sources)"))
            }
            assert "organization_id" not in source_cols
            assert "source_class" in source_cols
            assert conn.execute(sa.text("SELECT COUNT(*) FROM permit_rules")).scalar() >= 1
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c2d3e4f5a6b7"]

        command.downgrade(alembic_cfg, "b1c2d3e4f5a6")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "legal_content_sources" not in tables
            assert "legal_content_jurisdiction_packages" in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["b1c2d3e4f5a6"]
