"""FG-023 Slice A — BUILD actuals model/service + MONITOR projection.

No Hub UI, Hub write routes, live migrate, Field Web, LEARN, or delete.
"""

from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Client, Organization, Project, ProjectDirectCostActual
from app.models.build import FieldCaptureEvent
from app.models.direct_cost_actual import COST_CLASSES, SOURCE_OFFICE_MANUAL
from app.models.labour_engine import EstimateLabourSnapshot, LabourTask
from app.models.pricing_engine import EstimatePricingSnapshot
from app.project_controls.services import (
    add_change_order_item,
    create_change_order,
    update_change_order_status,
)
from app.services import create_estimate
from app.services.direct_cost_actuals import (
    DirectCostActualConflictError,
    DirectCostActualError,
    DirectCostActualNotFoundError,
    actual_cost_by_class,
    actual_direct_cost_to_date,
    create_direct_cost_actual,
    get_direct_cost_actual,
    is_active_actual,
    list_active_direct_cost_actuals,
    list_direct_cost_actuals,
    parse_amount,
    parse_incurred_on,
    successor_direct_cost_actual,
    supersede_direct_cost_actual,
)
from app.services.estimate_builder import add_manual_line, create_section, update_version_pricing
from app.services.estimates import clone_current_version, lock_version
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.proposals import (
    create_proposal,
    create_proposal_template,
    update_proposal_status,
)


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "e3f4a5b6c7d8_add_project_direct_cost_actuals_fg023.py"
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg023",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


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


@pytest.fixture
def project(app):
    return _make_project("FG-023 Project", "FG023-001", DEFAULT_ORGANIZATION_ID)


def _make_project(name, project_number, organization_id):
    client_row = Client(
        name=f"{name} Client",
        company=f"{name} Co",
        organization_id=organization_id,
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        address="10 Main St",
        client_id=client_row.id,
        status="Estimating",
        project_number=project_number,
        organization_id=organization_id,
    )
    db.session.add(project)
    db.session.commit()
    return project


def _template(name="FG-023 Template"):
    return create_proposal_template(
        name=name,
        is_default=True,
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )


def _estimate_with_line(project, *, number, quantity=2, unit_cost=100, lock=True):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number=number,
        title=f"{number} title",
        organization_id=project.organization_id,
    )
    version = estimate.current_version
    section = create_section(version, name="General")
    add_manual_line(
        section,
        line_type="Custom",
        description="Work",
        quantity=quantity,
        unit="ea",
        unit_cost=unit_cost,
    )
    if lock:
        lock_version(version)
    db.session.refresh(version)
    return estimate, version


def _add_snapshot(version, *, direct_cost, selling, tax_amount="13.00"):
    snapshot = EstimatePricingSnapshot(
        organization_id=version.estimate.project.organization_id,
        estimate_version_id=version.id,
        method="TRUE_GROSS_MARGIN",
        resolution_source="policy",
        requires_review=False,
        direct_cost_basis=Decimal(direct_cost),
        contingency_visibility="UNSPECIFIED",
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        pre_tax_selling_price=Decimal(selling),
        tax_amount=Decimal(tax_amount),
        tax_percent=Decimal("13"),
        customer_total=Decimal(selling) + Decimal(tax_amount),
        created_by="Estimator",
    )
    db.session.add(snapshot)
    db.session.commit()
    return snapshot


def _accept(estimate, version, *, title, template=None):
    template = template or _template(f"Template {title}")
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status="Draft",
        title=title,
    )
    update_proposal_status(proposal, "Accepted")
    db.session.refresh(proposal)
    return proposal


def _enter_actual(project, *, cost_class, amount, incurred_on="2026-09-01", note=None):
    return create_direct_cost_actual(
        project,
        cost_class=cost_class,
        amount=amount,
        incurred_on=incurred_on,
        note=note,
        actor_display_name="Joel Test",
        organization_id=project.organization_id,
    )


def test_migration_parent_is_frozen_head():
    text = MIGRATION_PATH.read_text()
    assert 'revision = "e3f4a5b6c7d8"' in text
    assert 'down_revision = "d2e3f4a5b6c7"' in text
    assert "op.drop_table(" in text
    assert "project_direct_cost_actuals" in text
    assert "flask db upgrade" not in text.lower() or "Do not run live flask db upgrade" in text


def test_monitor_service_excludes_field_events_and_net_profit():
    source = inspect.getsource(inspect.getmodule(assemble_monitor_v1))
    assert "FieldCaptureEvent" not in source
    assert "from app.models.build" not in source
    assert "field_capture" not in source
    assert "net_profit" not in source
    assert "db.session.commit" not in source
    assert "forecast_final" not in source
    assert "def assemble_forecast" not in source


def test_actuals_service_has_no_delete_or_field_event_domain():
    source = inspect.getsource(inspect.getmodule(create_direct_cost_actual))
    assert "def delete_" not in source
    assert "FieldCaptureEvent" not in source
    assert "FieldCaptureOriginal" not in source


def test_create_positive_and_zero_amount(app, project):
    row = _enter_actual(project, cost_class="labour", amount="125.50")
    zero = _enter_actual(project, cost_class="material", amount="0.00")
    assert row.amount == Decimal("125.50")
    assert zero.amount == Decimal("0.00")
    assert row.source == SOURCE_OFFICE_MANUAL
    assert row.actor_display_name == "Joel Test"
    assert row.user_id is None
    assert actual_direct_cost_to_date(project.organization_id, project.id) == Decimal(
        "125.50"
    )


def test_negative_amount_rejected_before_persist(app, project):
    with pytest.raises(DirectCostActualError, match="negative"):
        parse_amount("-0.01")
    with pytest.raises(DirectCostActualError, match="negative"):
        _enter_actual(project, cost_class="labour", amount="-1.00")
    assert ProjectDirectCostActual.query.count() == 0


def test_invalid_class_and_source_rejected(app, project):
    with pytest.raises(DirectCostActualError, match="cost class"):
        _enter_actual(project, cost_class="equipment", amount="10.00")
    with pytest.raises(DirectCostActualError, match="OFFICE_MANUAL"):
        create_direct_cost_actual(
            project,
            cost_class="labour",
            amount="10.00",
            incurred_on="2026-09-01",
            actor_display_name="Joel Test",
            organization_id=project.organization_id,
            source="QUICKBOOKS",
        )
    assert ProjectDirectCostActual.query.count() == 0


def test_db_checks_reject_invalid_class_amount_and_source(app, project):
    def _flush_invalid(**fields):
        payload = {
            "organization_id": project.organization_id,
            "project_id": project.id,
            "actor_display_name": "Joel Test",
            "cost_class": "labour",
            "amount": Decimal("1.00"),
            "incurred_on": date(2026, 9, 1),
            "source": SOURCE_OFFICE_MANUAL,
        }
        payload.update(fields)
        db.session.add(ProjectDirectCostActual(**payload))
        db.session.flush()

    with pytest.raises(IntegrityError):
        _flush_invalid(amount=Decimal("-0.01"))
    db.session.rollback()
    with pytest.raises(IntegrityError):
        _flush_invalid(cost_class="payroll")
    db.session.rollback()
    with pytest.raises(IntegrityError):
        _flush_invalid(source="QUICKBOOKS")
    db.session.rollback()


def test_incurred_on_accepts_any_parseable_date_including_future(app, project):
    future = date.today() + timedelta(days=40)
    row = _enter_actual(
        project, cost_class="other_direct", amount="1.00", incurred_on=future
    )
    assert row.incurred_on == future
    assert parse_incurred_on("2026-09-06") == date(2026, 9, 6)
    assert parse_incurred_on("Sep 06, 2026") == date(2026, 9, 6)
    with pytest.raises(DirectCostActualError, match="parseable"):
        parse_incurred_on("not-a-date")


def test_create_is_incremental_even_when_class_date_amount_repeat(app, project):
    first = _enter_actual(project, cost_class="labour", amount="10.00")
    second = _enter_actual(project, cost_class="labour", amount="10.00")
    assert first.id != second.id
    assert first.supersedes_id is None
    assert second.supersedes_id is None
    assert actual_direct_cost_to_date(project.organization_id, project.id) == Decimal(
        "20.00"
    )


def test_supersession_chain_active_rollup_and_zero_successor(app, project):
    original = _enter_actual(project, cost_class="labour", amount="100.00")
    material = _enter_actual(project, cost_class="material", amount="40.00")
    successor = supersede_direct_cost_actual(
        original,
        project=project,
        cost_class="labour",
        amount="80.00",
        incurred_on="2026-09-02",
        actor_display_name="Joel Test",
        organization_id=project.organization_id,
    )
    zero = supersede_direct_cost_actual(
        successor,
        project=project,
        cost_class="labour",
        amount="0.00",
        incurred_on="2026-09-03",
        actor_display_name="Joel Test",
        organization_id=project.organization_id,
    )
    db.session.refresh(original)
    assert original.amount == Decimal("100.00")
    assert successor.supersedes_id == original.id
    assert zero.supersedes_id == successor.id
    assert successor_direct_cost_actual(original).id == successor.id
    assert not is_active_actual(original)
    assert not is_active_actual(successor)
    assert is_active_actual(zero)
    assert is_active_actual(material)
    assert actual_direct_cost_to_date(project.organization_id, project.id) == Decimal(
        "40.00"
    )
    by_class = actual_cost_by_class(project.organization_id, project.id)
    assert by_class["labour"] == Decimal("0.00")
    assert by_class["material"] == Decimal("40.00")
    assert set(by_class) == set(COST_CLASSES)
    active_ids = {row.id for row in list_active_direct_cost_actuals(
        project.organization_id, project.id
    )}
    assert active_ids == {zero.id, material.id}
    assert ProjectDirectCostActual.query.count() == 4


def test_second_direct_successor_conflicts(app, project):
    original = _enter_actual(project, cost_class="labour", amount="10.00")
    supersede_direct_cost_actual(
        original,
        project=project,
        cost_class="labour",
        amount="9.00",
        incurred_on="2026-09-02",
        actor_display_name="Joel Test",
        organization_id=project.organization_id,
    )
    with pytest.raises(DirectCostActualConflictError):
        supersede_direct_cost_actual(
            original,
            project=project,
            cost_class="labour",
            amount="8.00",
            incurred_on="2026-09-03",
            actor_display_name="Joel Test",
            organization_id=project.organization_id,
        )


def test_self_cross_project_and_cross_org_supersession_fail_closed(app, project, org_b):
    original = _enter_actual(project, cost_class="labour", amount="10.00")
    other = _make_project("Other Project", "FG023-002", DEFAULT_ORGANIZATION_ID)
    other_row = _enter_actual(other, cost_class="labour", amount="50.00")
    foreign = _make_project("Apex Secret", "FG023-ORG2", "ORG-002")
    foreign_row = create_direct_cost_actual(
        foreign,
        cost_class="labour",
        amount="99.00",
        incurred_on="2026-09-01",
        actor_display_name="Apex",
        organization_id="ORG-002",
    )

    assert get_direct_cost_actual(project.organization_id, other.id, original.id) is None
    with pytest.raises(DirectCostActualNotFoundError):
        supersede_direct_cost_actual(
            other_row,
            project=project,
            cost_class="labour",
            amount="1.00",
            incurred_on="2026-09-02",
            actor_display_name="Joel Test",
            organization_id=project.organization_id,
        )
    with pytest.raises(DirectCostActualNotFoundError):
        supersede_direct_cost_actual(
            foreign_row,
            project=project,
            cost_class="labour",
            amount="1.00",
            incurred_on="2026-09-02",
            actor_display_name="Joel Test",
            organization_id=project.organization_id,
        )
    assert successor_direct_cost_actual(original) is None
    assert original.amount == Decimal("10.00")
    assert other_row.amount == Decimal("50.00")
    assert foreign_row.organization_id == "ORG-002"


def test_missing_actuals_is_not_zero(app, project):
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["actuals_state"] == "MISSING_ACTUALS"
    assert view["actual_direct_cost_to_date"] is None
    assert view["actual_cost_by_class"] is None
    assert view["actual_to_date_gm"] is None
    assert view["current_actuals"] == []
    assert view["baseline_state"] == "MISSING_CUSTOMER_COMMITMENT"


def test_explicit_zero_active_row_is_present_actuals(app, project):
    estimate, version = _estimate_with_line(project, number="EST-FG023-0001")
    _add_snapshot(version, direct_cost="200.00", selling="400.00")
    _accept(estimate, version, title="Accepted FG023")
    _enter_actual(project, cost_class="labour", amount="0.00")
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["actuals_state"] == "PRESENT"
    assert view["actual_direct_cost_to_date"] == Decimal("0.00")
    assert view["actual_to_date_gm"] == Decimal("1")
    assert view["actual_cost_by_class"]["labour"] == Decimal("0.00")


def test_snapshot_baseline_and_labour_snapshot_excluded(app, project):
    estimate, version = _estimate_with_line(project, number="EST-FG023-0002")
    snapshot = _add_snapshot(version, direct_cost="1000.00", selling="1250.00")
    task = LabourTask(
        organization_id=DEFAULT_ORGANIZATION_ID,
        task_code="FG023-TASK",
        canonical_name="FG023 Task",
        production_unit="ea",
        unit_of_measure="ea",
    )
    db.session.add(task)
    db.session.flush()
    labour = EstimateLabourSnapshot(
        organization_id=DEFAULT_ORGANIZATION_ID,
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal("2"),
        unit="ea",
        resolved_production_rate=Decimal("1"),
        calculated_man_hours=Decimal("2"),
        resolved_direct_labour_cost_rate=Decimal("65"),
        direct_labour_cost=Decimal("77777.00"),
        source_class="MANUAL",
        resolution_reason="fg023-test",
        created_by="Estimator",
    )
    db.session.add(labour)
    db.session.commit()
    proposal = _accept(estimate, version, title="Accepted snapshot")
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["baseline_state"] == "COMPLETE"
    assert view["original_estimated_direct_cost"] == Decimal("1000.00")
    assert view["original_estimated_pre_tax_selling_price"] == Decimal("1250.00")
    assert view["estimated_gm"] == Decimal("1") - (
        Decimal("1000.00") / Decimal("1250.00")
    )
    assert view["provenance"]["pricing_snapshot_id"] == snapshot.id
    assert view["provenance"]["accepted_proposal_id"] == proposal.id
    assert view["provenance"]["source_estimate_version_id"] == version.id
    assert "77777" not in str(view["original_estimated_direct_cost"])
    assert labour.direct_labour_cost == Decimal("77777.00")
    assert snapshot.direct_cost_basis == Decimal("1000.00")
    assert snapshot.tax_amount == Decimal("13.00")
    assert view["original_estimated_pre_tax_selling_price"] != Decimal("1263.00")


def test_fallback_baseline_from_lines_and_accepted_proposal(app, project):
    estimate, version = _estimate_with_line(
        project, number="EST-FG023-0003", quantity=2, unit_cost=100, lock=False
    )
    update_version_pricing(
        version, overhead_percent=10, profit_percent=10, tax_percent=13
    )
    lock_version(version)
    proposal = _accept(estimate, version, title="Accepted fallback")
    view = assemble_monitor_v1(project, project.organization_id)
    expected_dc = Decimal("200.00")
    expected_selling = as_proposal_pre_tax(proposal)
    assert view["baseline_state"] == "COMPLETE"
    assert view["original_estimated_direct_cost"] == expected_dc
    assert view["original_estimated_pre_tax_selling_price"] == expected_selling
    assert view["provenance"]["pricing_snapshot_id"] is None
    assert proposal.tax_amount > 0
    assert view["original_estimated_pre_tax_selling_price"] != proposal.total


def as_proposal_pre_tax(proposal):
    return (
        Decimal(proposal.subtotal or 0)
        + Decimal(proposal.overhead_amount or 0)
        + Decimal(proposal.profit_amount or 0)
    ).quantize(Decimal("0.01"))


def test_later_draft_current_version_is_not_baseline(app, project):
    estimate, version = _estimate_with_line(project, number="EST-FG023-0004")
    _add_snapshot(version, direct_cost="500.00", selling="800.00")
    _accept(estimate, version, title="Locked accepted")
    clone_current_version(estimate, version_label="Later draft")
    db.session.refresh(estimate)
    assert estimate.current_version_id != version.id
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["provenance"]["source_estimate_version_id"] == version.id
    assert view["original_estimated_direct_cost"] == Decimal("500.00")


def test_ambiguous_and_unlocked_commitment_states(app, project):
    first, first_version = _estimate_with_line(project, number="EST-FG023-0005")
    _add_snapshot(first_version, direct_cost="100.00", selling="200.00")
    template = _template("Ambiguous template")
    _accept(first, first_version, title="Accepted one", template=template)
    second, second_version = _estimate_with_line(project, number="EST-FG023-0006")
    _add_snapshot(second_version, direct_cost="300.00", selling="400.00")
    _accept(second, second_version, title="Accepted two", template=template)
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["baseline_state"] == "AMBIGUOUS_COMMITMENT"
    assert view["original_estimated_direct_cost"] is None
    assert view["estimated_gm"] is None
    assert view["provenance"]["accepted_proposal_id"] is None

    other = _make_project("Draft only", "FG023-DRAFT", DEFAULT_ORGANIZATION_ID)
    estimate, version = _estimate_with_line(
        other, number="EST-FG023-0007", lock=False
    )
    _accept(estimate, version, title="Accepted unlocked")
    unlocked = assemble_monitor_v1(other, other.organization_id)
    assert unlocked["baseline_state"] == "MISSING_ORIGINAL_BASELINE"
    assert unlocked["estimated_gm"] is None


def test_authorized_cos_and_hst_excluded_and_no_co_cost(app, project):
    estimate, version = _estimate_with_line(project, number="EST-FG023-0008")
    _add_snapshot(version, direct_cost="1000.00", selling="2000.00")
    _accept(estimate, version, title="CO baseline")
    approved = create_change_order(
        project=project,
        title="Approved CO",
        markup_percent=10,
        tax_percent=13,
        status="Draft",
    )
    add_change_order_item(
        approved, description="Extra", quantity=1, unit="ea", unit_price=100
    )
    update_change_order_status(approved, "Approved")
    invoiced = create_change_order(
        project=project,
        title="Invoiced CO",
        markup_percent=0,
        tax_percent=13,
        status="Draft",
    )
    add_change_order_item(
        invoiced, description="Invoice extra", quantity=1, unit="ea", unit_price=50
    )
    update_change_order_status(invoiced, "Invoiced")
    draft = create_change_order(
        project=project,
        title="Draft CO",
        markup_percent=0,
        status="Draft",
    )
    add_change_order_item(
        draft, description="Ignore", quantity=1, unit="ea", unit_price=9999
    )
    pending = create_change_order(
        project=project,
        title="Pending CO",
        status="Pending Approval",
    )
    rejected = create_change_order(
        project=project,
        title="Rejected CO",
        status="Rejected",
    )
    cancelled = create_change_order(
        project=project,
        title="Cancelled CO",
        status="Cancelled",
    )
    db.session.refresh(approved)
    db.session.refresh(invoiced)
    expected_delta = (
        Decimal(approved.subtotal) + Decimal(approved.markup) + Decimal(invoiced.subtotal)
    )
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["approved_co_revenue_delta"] == expected_delta
    assert set(view["authorized_co_ids"]) == {approved.id, invoiced.id}
    assert view["authorized_co_count"] == 2
    assert view["current_authorized_estimated_cost"] == Decimal("1000.00")
    assert view["current_authorized_pre_tax_revenue"] == Decimal("2000.00") + expected_delta
    assert Decimal(approved.tax or 0) > 0 or approved.tax_percent == Decimal("13")
    assert view["approved_co_revenue_delta"] != Decimal(approved.total)
    assert view["co_cost_delta_stored"] is False
    assert view["co_cost_delta_copy"] == "CO cost delta not stored"
    _enter_actual(project, cost_class="subcontract", amount="100.00")
    after = assemble_monitor_v1(project, project.organization_id)
    assert after["actual_direct_cost_to_date"] == Decimal("100.00")
    assert after["current_authorized_estimated_cost"] == Decimal("1000.00")
    assert draft.id not in after["authorized_co_ids"]
    assert pending.id not in after["authorized_co_ids"]
    assert rejected.id not in after["authorized_co_ids"]
    assert cancelled.id not in after["authorized_co_ids"]


def test_gm_identities_and_zero_denominator(app, project):
    estimate, version = _estimate_with_line(project, number="EST-FG023-0009")
    _add_snapshot(version, direct_cost="250.00", selling="1000.00")
    _accept(estimate, version, title="GM identities")
    _enter_actual(project, cost_class="labour", amount="100.00")
    _enter_actual(project, cost_class="material", amount="50.00")
    view = assemble_monitor_v1(project, project.organization_id)
    estimated = Decimal("1") - (Decimal("250.00") / Decimal("1000.00"))
    actual = Decimal("1") - (Decimal("150.00") / Decimal("1000.00"))
    assert view["estimated_gm"] == estimated
    assert view["actual_to_date_gm"] == actual
    assert view["gm_variance"] == actual - estimated
    assert view["actuals_state"] == "PRESENT"

    zero_rev = _make_project("Zero revenue", "FG023-ZERO", DEFAULT_ORGANIZATION_ID)
    z_est, z_ver = _estimate_with_line(zero_rev, number="EST-FG023-0010")
    _add_snapshot(z_ver, direct_cost="10.00", selling="0.00", tax_amount="0.00")
    _accept(z_est, z_ver, title="Zero selling")
    zero_view = assemble_monitor_v1(zero_rev, zero_rev.organization_id)
    assert zero_view["estimated_gm"] is None
    _enter_actual(zero_rev, cost_class="labour", amount="5.00")
    zero_actual = assemble_monitor_v1(zero_rev, zero_rev.organization_id)
    assert zero_actual["actual_to_date_gm"] is None
    assert zero_actual["gm_variance"] is None


def test_field_events_are_not_cost(app, project):
    event = FieldCaptureEvent(
        organization_id=project.organization_id,
        project_id=project.id,
        actor_display_name="Field",
        occurred_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.session.add(event)
    db.session.commit()
    event_id = event.id
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["actuals_state"] == "MISSING_ACTUALS"
    assert view["actual_direct_cost_to_date"] is None
    db.session.refresh(event)
    assert event.id == event_id
    assert FieldCaptureEvent.query.count() == 1
    assert ProjectDirectCostActual.query.count() == 0


def test_org_mismatch_monitor_fails_closed(app, project, org_b):
    estimate, version = _estimate_with_line(project, number="EST-FG023-0011")
    _add_snapshot(version, direct_cost="100.00", selling="200.00")
    _accept(estimate, version, title="Mismatch")
    _enter_actual(project, cost_class="labour", amount="10.00")
    view = assemble_monitor_v1(project, "ORG-002")
    assert view["baseline_state"] == "MISSING_CUSTOMER_COMMITMENT"
    assert view["actuals_state"] == "MISSING_ACTUALS"
    assert view["original_estimated_direct_cost"] is None
    assert view["actual_direct_cost_to_date"] is None


def test_baseline_records_unchanged_after_actuals(app, project):
    estimate, version = _estimate_with_line(project, number="EST-FG023-0012")
    snapshot = _add_snapshot(version, direct_cost="100.00", selling="200.00")
    proposal = _accept(estimate, version, title="Immutable commercial")
    co = create_change_order(project=project, title="Keep CO", status="Approved")
    snap_dc = snapshot.direct_cost_basis
    prop_subtotal = proposal.subtotal
    co_status = co.status
    _enter_actual(project, cost_class="labour", amount="30.00")
    successor = supersede_direct_cost_actual(
        list_direct_cost_actuals(project.organization_id, project.id)[0],
        project=project,
        cost_class="labour",
        amount="25.00",
        incurred_on="2026-09-04",
        actor_display_name="Joel Test",
        organization_id=project.organization_id,
    )
    db.session.refresh(snapshot)
    db.session.refresh(proposal)
    db.session.refresh(co)
    db.session.refresh(version)
    assert snapshot.direct_cost_basis == snap_dc
    assert proposal.subtotal == prop_subtotal
    assert proposal.status == "Accepted"
    assert co.status == co_status
    assert successor.amount == Decimal("25.00")
    assert "net profit" not in str(assemble_monitor_v1(project, project.organization_id)).lower()
