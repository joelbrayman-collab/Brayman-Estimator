"""Tests for FG-008 Labour Engine Phase B."""

import os
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app import create_app, db
from app.models import (
    Client,
    CostItem,
    Organization,
    Project,
)
from app.models.historical_estimates import (
    HistoricalEstimate,
    HistoricalLabourItem,
    HistoricalSourceWorkbook,
)
from app.models.labour_engine import (
    DirectLabourCostRateStandard,
    EstimateLabourSnapshot,
    LabourAuditEvent,
    LabourCalibrationCandidate,
    LabourTask,
    LabourTaskMapping,
    ProductionRateStandard,
)
from app.services.estimate_builder import (
    add_cost_item_line,
    calculate_sell_price,
    create_section,
    update_version_pricing,
)
from app.services.estimates import create_estimate
from app.services.labour_engine import (
    LabourEngineError,
    accept_labour_task_mapping,
    calculate_direct_labour_cost,
    calculate_man_hours,
    calculate_planning_man_hours,
    create_calibration_candidate,
    create_estimate_labour_snapshot,
    create_labour_task,
    create_production_rate_standard,
    ensure_org_001_direct_labour_cost_rate_standard,
    get_labour_task_or_404,
    historical_labour_item_facts,
    list_labour_tasks,
    mark_mapping_not_labour,
    reject_labour_task_mapping,
    resolve_direct_labour_cost_rate,
    resolve_production_rate,
    suggest_labour_task_mapping,
    transition_calibration_candidate,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _task(org_id=DEFAULT_ORGANIZATION_ID, code="LT-ICF-INSTALL", **kwargs):
    defaults = dict(
        task_code=code,
        canonical_name="ICF Install",
        production_unit="sq ft wall",
        unit_of_measure="sqft",
        trade="Concrete",
        organization_id=org_id,
        created_by="Joel Brayman",
    )
    defaults.update(kwargs)
    return create_labour_task(**defaults)


def _promote(candidate, actor="Joel Brayman"):
    transition_calibration_candidate(candidate.id, "PROPOSED", actor=actor)
    transition_calibration_candidate(candidate.id, "IN_REVIEW", actor=actor)
    return transition_calibration_candidate(candidate.id, "APPROVED", actor=actor)


def _historical_labour_item(
    org_id=DEFAULT_ORGANIZATION_ID,
    description="ICF Labour",
    hourly_rate="0.13",
    hours="80",
    suffix="1",
):
    workbook = HistoricalSourceWorkbook(
        organization_id=org_id,
        source_id=f"HIST-EST-TEST-{suffix}",
        original_filename="test.xlsx",
        extension=".xlsx",
        sha256=(str(suffix) * 64)[:64],
        byte_size=100,
        template_family="FAMILY_A",
        ingestion_status="INGESTED",
        ingestion_version="v1",
        idempotency_key=f"test-key-{org_id}-{suffix}",
    )
    db.session.add(workbook)
    db.session.flush()
    estimate = HistoricalEstimate(
        organization_id=org_id,
        source_workbook_id=workbook.id,
        project_name="Test Project",
        template_family="FAMILY_A",
        evidence_tier="TIER_C",
        pricing_method="COST_PLUS_MARKUP",
        currency="CAD",
        extraction_confidence=1.0,
        review_status="EXTRACTED",
    )
    db.session.add(estimate)
    db.session.flush()
    item = HistoricalLabourItem(
        organization_id=org_id,
        historical_estimate_id=estimate.id,
        task_description=description,
        crew_size=Decimal("2"),
        duration_days=Decimal("5"),
        hours_per_day=Decimal("8.0"),
        total_man_hours=Decimal(hours),
        hourly_rate=Decimal(hourly_rate),
        extended_labour_cost=Decimal("5200.00"),
        formula_pattern="crew*days*hpd",
    )
    db.session.add(item)
    db.session.commit()
    return item


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="Labour Test Project"):
    client_row = Client(name=f"{name} Client", organization_id=org_id)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=org_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


# ---------------------------------------------------------------------------
# 1–3 Organization isolation / ownership / fail-closed
# ---------------------------------------------------------------------------


def test_labour_task_organization_ownership_and_isolation(app, org_b, client):
    t1 = _task(code="LT-ORG1")
    t2 = _task(org_id="ORG-002", code="LT-ORG1", canonical_name="Apex ICF")

    org1_tasks = list_labour_tasks(organization_id="ORG-001")
    org2_tasks = list_labour_tasks(organization_id="ORG-002")
    assert [t.task_code for t in org1_tasks] == ["LT-ORG1"]
    assert org1_tasks[0].id == t1.id
    assert [t.task_code for t in org2_tasks] == ["LT-ORG1"]
    assert org2_tasks[0].id == t2.id
    assert t1.organization_id == "ORG-001"
    assert t2.organization_id == "ORG-002"

    with pytest.raises(LabourEngineError, match="not found"):
        get_labour_task_or_404(t2.id, organization_id="ORG-001")

    resp = client.get(f"/labour-engine/tasks/{t2.id}")
    assert resp.status_code == 404

    resp_ok = client.get(f"/labour-engine/tasks/{t1.id}")
    assert resp_ok.status_code == 200
    assert b"LT-ORG1" in resp_ok.data


def test_cross_org_resolution_fail_closed(app, org_b):
    task_b = _task(org_id="ORG-002", code="LT-B")
    with pytest.raises(LabourEngineError, match="not found"):
        resolve_production_rate(
            labour_task_id=task_b.id,
            organization_id="ORG-001",
            persist_audit=False,
        )


# ---------------------------------------------------------------------------
# 4–6 Mapping
# ---------------------------------------------------------------------------


def test_mapping_suggestion_does_not_auto_accept(app):
    task = _task()
    item = _historical_labour_item()
    mapping = suggest_labour_task_mapping(
        source_string=item.task_description,
        historical_labour_item_id=item.id,
        labour_task_id=task.id,
        suggested_by="HUMAN",
        actor="Joel Brayman",
    )
    assert mapping.review_status == "SUGGESTED"
    assert mapping.labour_task_id == task.id
    assert LabourTaskMapping.query.filter_by(review_status="ACCEPTED").count() == 0


def test_mapping_accept_reject_not_labour_and_historical_unchanged(app):
    task = _task()
    item_a = _historical_labour_item(description="ICF Labour", suffix="1")
    item_b = _historical_labour_item(description="2X6X8", hourly_rate="65", suffix="2")
    item_c = _historical_labour_item(description="Install ICF", suffix="3")

    facts_a = historical_labour_item_facts(item_a)
    facts_b = historical_labour_item_facts(item_b)
    facts_c = historical_labour_item_facts(item_c)

    m_accept = suggest_labour_task_mapping(
        source_string=item_a.task_description,
        historical_labour_item_id=item_a.id,
        labour_task_id=task.id,
        actor="Joel Brayman",
    )
    m_reject = suggest_labour_task_mapping(
        source_string=item_c.task_description,
        historical_labour_item_id=item_c.id,
        labour_task_id=task.id,
        actor="Joel Brayman",
    )
    m_not = suggest_labour_task_mapping(
        source_string=item_b.task_description,
        historical_labour_item_id=item_b.id,
        actor="Joel Brayman",
    )

    accept_labour_task_mapping(m_accept.id, reviewed_by="Joel Brayman", review_notes="ok")
    reject_labour_task_mapping(m_reject.id, reviewed_by="Joel Brayman", review_notes="no")
    mark_mapping_not_labour(m_not.id, reviewed_by="Joel Brayman", review_notes="material SKU")

    db.session.refresh(m_accept)
    db.session.refresh(m_reject)
    db.session.refresh(m_not)
    db.session.refresh(item_a)
    db.session.refresh(item_b)
    db.session.refresh(item_c)

    assert m_accept.review_status == "ACCEPTED"
    assert m_reject.review_status == "REJECTED"
    assert m_not.review_status == "NOT_LABOUR"
    assert m_not.labour_task_id is None
    assert historical_labour_item_facts(item_a) == facts_a
    assert historical_labour_item_facts(item_b) == facts_b
    assert historical_labour_item_facts(item_c) == facts_c
    assert item_b.hourly_rate == Decimal("65.00")
    assert item_a.hourly_rate == Decimal("0.13")


def test_mapping_rule_suggestion_from_accepted_string_still_suggested(app):
    task = _task()
    first = suggest_labour_task_mapping(
        source_string="ICF Walls", labour_task_id=task.id, actor="Joel Brayman"
    )
    accept_labour_task_mapping(first.id, reviewed_by="Joel Brayman")
    second = suggest_labour_task_mapping(source_string="icf walls", actor="Joel Brayman")
    assert second.review_status == "SUGGESTED"
    assert second.suggested_by == "RULE"
    assert second.labour_task_id == task.id


# ---------------------------------------------------------------------------
# 7–9 Math / units / separated rates
# ---------------------------------------------------------------------------


def test_production_rate_and_direct_labour_cost_math(app):
    hours = calculate_man_hours(Decimal("100"), Decimal("0.05"))
    assert hours == Decimal("5.00")
    cost = calculate_direct_labour_cost(hours, Decimal("65"))
    assert cost == Decimal("325.00")
    planning = calculate_planning_man_hours(Decimal("2"), Decimal("8"), Decimal("5"))
    assert planning == Decimal("80")
    assert calculate_man_hours(100, Decimal("0.05")) != Decimal("65")


def test_snapshot_rejects_mismatched_unit(app):
    task = _task()
    cand = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.05"),
        proposed_production_unit="sq ft wall",
        created_by="Joel Brayman",
    )
    _promote(cand)
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-8001",
        title="Unit check",
    )
    with pytest.raises(LabourEngineError, match="does not match"):
        create_estimate_labour_snapshot(
            estimate_version_id=estimate.current_version.id,
            labour_task_id=task.id,
            quantity=10,
            unit="m2",
            created_by="Joel Brayman",
        )


# ---------------------------------------------------------------------------
# 10–13 Candidate lifecycle / approval / no auto-promote
# ---------------------------------------------------------------------------


def test_candidate_valid_and_invalid_transitions(app):
    task = _task()
    candidate = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.04"),
        created_by="Joel Brayman",
    )
    assert candidate.state == "DRAFT"
    with pytest.raises(LabourEngineError, match="Illegal candidate transition"):
        transition_calibration_candidate(
            candidate.id, "APPROVED", actor="Joel Brayman"
        )
    with pytest.raises(LabourEngineError, match="AI cannot"):
        transition_calibration_candidate(candidate.id, "PROPOSED", actor="AI")

    _promote(candidate)
    db.session.refresh(candidate)
    assert candidate.state == "APPROVED"
    standard = ProductionRateStandard.query.get(candidate.promoted_production_standard_id)
    assert standard.evidence_class == "ORG-APPROVED"
    assert standard.approval_status == "APPROVED"
    assert standard.production_rate == Decimal("0.040000")
    assert standard.approved_by == "Joel Brayman"


def test_human_approval_versions_org_approved_standard(app):
    task = _task()
    first = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.05"),
        created_by="Joel Brayman",
    )
    _promote(first)
    first_std_id = first.promoted_production_standard_id
    first_std = ProductionRateStandard.query.get(first_std_id)
    original_rate = first_std.production_rate

    second = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.06"),
        created_by="Joel Brayman",
    )
    _promote(second)
    db.session.refresh(first_std)
    db.session.refresh(first)
    assert first_std.approval_status == "SUPERSEDED"
    assert first_std.production_rate == original_rate
    assert first_std.superseded_by_id == second.promoted_production_standard_id
    assert first.state == "SUPERSEDED"
    new_std = ProductionRateStandard.query.get(second.promoted_production_standard_id)
    assert new_std.version_number == 2
    assert new_std.approval_status == "APPROVED"


def test_historical_evidence_does_not_auto_promote(app):
    task = _task()
    item = _historical_labour_item()
    mapping = suggest_labour_task_mapping(
        source_string=item.task_description,
        historical_labour_item_id=item.id,
        labour_task_id=task.id,
        actor="Joel Brayman",
    )
    accept_labour_task_mapping(mapping.id, reviewed_by="Joel Brayman")
    result = resolve_production_rate(
        labour_task_id=task.id, persist_audit=False
    )
    assert result.source_class != "ORG-APPROVED"
    assert result.production_rate is None
    assert ProductionRateStandard.query.filter_by(evidence_class="ORG-APPROVED").count() == 0


def test_cannot_create_org_approved_standard_directly(app):
    task = _task()
    with pytest.raises(LabourEngineError, match="candidate approval"):
        create_production_rate_standard(
            labour_task_id=task.id,
            production_rate=Decimal("0.05"),
            evidence_class="ORG-APPROVED",
            created_by="Joel Brayman",
        )


# ---------------------------------------------------------------------------
# 14–17 Resolution order / provenance / override / no silent multiplier
# ---------------------------------------------------------------------------


def test_rate_resolution_ordering_and_provenance(app):
    task = _task()
    create_production_rate_standard(
        labour_task_id=task.id,
        production_rate=Decimal("0.20"),
        evidence_class="PROVISIONAL",
        created_by="Joel Brayman",
    )
    create_production_rate_standard(
        labour_task_id=task.id,
        production_rate=Decimal("0.10"),
        evidence_class="BASELINE",
        created_by="Joel Brayman",
    )
    baseline = resolve_production_rate(labour_task_id=task.id, persist_audit=False)
    assert baseline.source_class == "BASELINE"
    assert baseline.production_rate == Decimal("0.10")
    assert "BASELINE" in baseline.reason_selected

    cand = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.05"),
        created_by="Joel Brayman",
    )
    _promote(cand)
    approved = resolve_production_rate(labour_task_id=task.id, persist_audit=False)
    assert approved.source_class == "ORG-APPROVED"
    assert approved.production_rate == Decimal("0.05")
    assert approved.source_record_type == "ProductionRateStandard"
    assert approved.standard_version == ProductionRateStandard.query.get(
        approved.source_record_id
    ).version_number
    assert approved.organization_id == "ORG-001"

    overridden = resolve_production_rate(
        labour_task_id=task.id,
        override_production_rate=Decimal("0.08"),
        override_reason="Restricted access on this lot",
        persist_audit=False,
    )
    assert overridden.source_class == "MANUAL"
    assert overridden.production_rate == Decimal("0.08")
    assert overridden.override_reason == "Restricted access on this lot"


def test_project_override_requires_reason(app):
    task = _task()
    with pytest.raises(LabourEngineError, match="requires a reason"):
        resolve_production_rate(
            labour_task_id=task.id,
            override_production_rate=Decimal("0.09"),
            persist_audit=False,
        )
    with pytest.raises(LabourEngineError, match="requires a reason"):
        resolve_direct_labour_cost_rate(
            override_rate=Decimal("70"),
            persist_audit=False,
        )


def test_no_silent_project_condition_multiplier(app):
    task = _task()
    cand = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.05"),
        created_by="Joel Brayman",
    )
    _promote(cand)
    with pytest.raises(LabourEngineError, match="Silent labour multipliers"):
        resolve_production_rate(
            labour_task_id=task.id,
            persist_audit=False,
            productivity_factor=Decimal("1.15"),
        )
    winter = resolve_production_rate(
        labour_task_id=task.id,
        applicable_conditions="WINTER",
        persist_audit=False,
    )
    assert winter.source_class != "ORG-APPROVED"
    assert winter.production_rate is None
    default = resolve_production_rate(labour_task_id=task.id, persist_audit=False)
    assert default.production_rate == Decimal("0.05")


# ---------------------------------------------------------------------------
# 18–20 Snapshot immutability / supersession / legacy
# ---------------------------------------------------------------------------


def test_estimate_labour_snapshot_immutable_and_survives_supersession(app):
    task = _task()
    cand = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.05"),
        created_by="Joel Brayman",
    )
    _promote(cand)
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-8002",
        title="Labour snapshot estimate",
    )
    snapshot = create_estimate_labour_snapshot(
        estimate_version_id=estimate.current_version.id,
        labour_task_id=task.id,
        quantity=Decimal("100"),
        created_by="Joel Brayman",
    )
    assert snapshot.calculated_man_hours == Decimal("5")
    assert snapshot.resolved_direct_labour_cost_rate == Decimal("65.0000")
    assert snapshot.direct_labour_cost == Decimal("325.00")
    assert snapshot.resolution_reason
    snapshot_id = snapshot.id
    pinned_rate = snapshot.resolved_production_rate
    pinned_hours = snapshot.calculated_man_hours

    snapshot.resolved_production_rate = Decimal("9")
    with pytest.raises(LabourEngineError, match="immutable"):
        db.session.commit()
    db.session.rollback()

    later = create_calibration_candidate(
        standard_kind="PRODUCTION_RATE",
        labour_task_id=task.id,
        proposed_production_rate=Decimal("0.20"),
        created_by="Joel Brayman",
    )
    _promote(later)
    frozen = EstimateLabourSnapshot.query.get(snapshot_id)
    assert frozen.resolved_production_rate == pinned_rate
    assert frozen.calculated_man_hours == pinned_hours
    assert frozen.direct_labour_cost == Decimal("325.00")


def test_legacy_estimate_without_snapshot_still_loads(client, app):
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-8003",
        title="Legacy lump labour",
    )
    assert EstimateLabourSnapshot.query.count() == 0
    resp = client.get(f"/estimates/{estimate.id}")
    assert resp.status_code == 200
    assert b"Legacy lump labour" in resp.data


# ---------------------------------------------------------------------------
# 21 ORG-001 $65 does not leak
# ---------------------------------------------------------------------------


def test_org_001_rate_does_not_leak_to_org_002(app, org_b):
    org1 = resolve_direct_labour_cost_rate(
        organization_id="ORG-001", persist_audit=False
    )
    assert org1.rate_per_man_hour == Decimal("65.0000")
    assert org1.source_class == "ORG-APPROVED"

    org2 = resolve_direct_labour_cost_rate(
        organization_id="ORG-002", persist_audit=False
    )
    assert org2.rate_per_man_hour is None
    assert org2.requires_review is True
    assert org2.source_class == "PROVISIONAL"
    assert DirectLabourCostRateStandard.query.filter_by(organization_id="ORG-002").count() == 0


# ---------------------------------------------------------------------------
# 22 Existing estimate pricing math unchanged
# ---------------------------------------------------------------------------


def test_existing_estimate_pricing_math_unchanged(app):
    assert calculate_sell_price(Decimal("264"), Decimal("20")) == Decimal("316.8")
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-8004",
        title="Pricing regression",
    )
    version = estimate.current_version
    cost_item = CostItem(
        organization_id="ORG-001",
        code="MAT-100",
        name="Concrete Mix",
        category="Material",
        unit="m3",
        unit_cost=Decimal("120.00"),
        default_markup_percent=Decimal("20.00"),
        is_active=True,
    )
    db.session.add(cost_item)
    db.session.commit()
    section = create_section(version, name="Calc")
    line = add_cost_item_line(
        section, cost_item_id=cost_item.id, quantity=2, waste_percent=10
    )
    assert line.extended_cost == Decimal("264.00")
    assert line.sell_price == Decimal("316.80")
    update_version_pricing(
        version, overhead_percent=10, profit_percent=10, tax_percent=5
    )
    assert version.overhead_amount == Decimal("31.68")
    assert version.profit_amount == Decimal("34.85")
    assert version.tax_amount == Decimal("19.17")
    assert version.total == Decimal("402.50")


# ---------------------------------------------------------------------------
# Audit + UI
# ---------------------------------------------------------------------------


def test_audit_events_recorded(app):
    task = _task()
    types = {row.event_type for row in LabourAuditEvent.query.all()}
    assert "labour_task.create" in types
    mapping = suggest_labour_task_mapping(
        source_string="ICF Labour", labour_task_id=task.id, actor="Joel Brayman"
    )
    accept_labour_task_mapping(mapping.id, reviewed_by="Joel Brayman")
    types = {row.event_type for row in LabourAuditEvent.query.all()}
    assert "mapping.suggest" in types
    assert "mapping.accept" in types


def test_office_ui_task_create_and_archive(client, app):
    resp = client.get("/labour-engine/")
    assert resp.status_code == 200
    assert b"Labour Engine" in resp.data

    resp = client.post(
        "/labour-engine/tasks/new",
        data={
            "task_code": "LT-FORM",
            "canonical_name": "Form Footings",
            "production_unit": "lf",
            "unit_of_measure": "lf",
            "reviewed_by": "Joel Brayman",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"LT-FORM" in resp.data
    task = LabourTask.query.filter_by(task_code="LT-FORM").one()
    archive = client.post(
        f"/labour-engine/tasks/{task.id}/archive",
        data={"reviewed_by": "Joel Brayman"},
        follow_redirects=True,
    )
    assert archive.status_code == 200
    db.session.refresh(task)
    assert task.status == "ARCHIVED"


def test_mapping_ui_accept(client, app):
    task = _task()
    item = _historical_labour_item()
    resp = client.post(
        "/labour-engine/mappings/suggest",
        data={
            "historical_labour_item_id": item.id,
            "labour_task_id": task.id,
            "reviewed_by": "Joel Brayman",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"SUGGESTED" in resp.data
    mapping = LabourTaskMapping.query.one()
    accept = client.post(
        f"/labour-engine/mappings/{mapping.id}/accept",
        data={"reviewed_by": "Joel Brayman", "labour_task_id": task.id},
        follow_redirects=True,
    )
    assert accept.status_code == 200
    db.session.refresh(mapping)
    assert mapping.review_status == "ACCEPTED"


# ---------------------------------------------------------------------------
# Alembic upgrade / downgrade
# ---------------------------------------------------------------------------


def test_alembic_fg008_upgrade_and_downgrade_preserves_historical(tmp_path):
    db_path = tmp_path / "fg008_migration.db"
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

        command.upgrade(alembic_cfg, "e1b2c3d4e5f6")
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO historical_source_workbooks ("
                    "organization_id, source_id, original_filename, extension, sha256, "
                    "byte_size, template_family, ingestion_status, ingestion_version, "
                    "idempotency_key, created_at"
                    ") VALUES ("
                    "'ORG-001', 'HIST-EST-0001', 'keep.xlsx', '.xlsx', :sha, "
                    "12, 'FAMILY_A', 'INGESTED', 'v1', 'keep-key', '2026-01-01 00:00:00')"
                ),
                {"sha": "c" * 64},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO historical_estimates ("
                    "organization_id, source_workbook_id, template_family, evidence_tier, "
                    "pricing_method, currency, extraction_confidence, review_status, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "'ORG-001', 1, 'FAMILY_A', 'TIER_C', 'COST_PLUS_MARKUP', 'CAD', 1.0, "
                    "'EXTRACTED', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO historical_labour_items ("
                    "organization_id, historical_estimate_id, task_description, crew_size, "
                    "duration_days, hours_per_day, total_man_hours, hourly_rate, "
                    "extended_labour_cost, formula_pattern, created_at"
                    ") VALUES ("
                    "'ORG-001', 1, 'ICF Labour', 2, 5, 8.0, 80, 0.13, 5200, 'crew*days*hpd', "
                    "'2026-01-01 00:00:00')"
                )
            )

        command.upgrade(alembic_cfg, "f2c3d4e5f6a7")
        with engine.begin() as conn:
            labour = conn.execute(
                sa.text(
                    "SELECT task_description, hourly_rate, total_man_hours, formula_pattern "
                    "FROM historical_labour_items WHERE id=1"
                )
            ).fetchone()
            assert labour[0] == "ICF Labour"
            assert Decimal(str(labour[1])) == Decimal("0.13")
            assert Decimal(str(labour[2])) == Decimal("80")
            assert labour[3] == "crew*days*hpd"
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "labour_tasks" in tables
            assert "estimate_labour_snapshots" in tables
            rate = conn.execute(
                sa.text(
                    "SELECT rate_per_man_hour, organization_id FROM "
                    "direct_labour_cost_rate_standards WHERE version_number=1"
                )
            ).fetchone()
            assert rate[1] == "ORG-001"
            assert Decimal(str(rate[0])) == Decimal("65")

        command.downgrade(alembic_cfg, "e1b2c3d4e5f6")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "labour_tasks" not in tables
            leftover = conn.execute(
                sa.text("SELECT task_description, hourly_rate FROM historical_labour_items WHERE id=1")
            ).fetchone()
            assert leftover[0] == "ICF Labour"
            assert Decimal(str(leftover[1])) == Decimal("0.13")
