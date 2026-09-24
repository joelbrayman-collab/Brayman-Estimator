"""PKG-F07 — Extra Work approved internal direct cost + MONITOR truth.

Synthetic SQLite only. No live DB. No schema. No migration.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Project
from app.models.pricing_engine import EstimatePricingSnapshot
from app.models.user import UserMembership
from app.models.work_structure import SCOPE_CHANGE_ORDER, SCOPE_EXTRA_WORK
from app.project_controls.models import ChangeOrder
from app.project_controls.services import (
    APPROVED_INTERNAL_COST_FROZEN,
    APPROVED_INTERNAL_COST_REQUIRED,
    ChangeOrderServiceError,
    add_change_order_item,
    create_change_order,
    update_change_order,
    update_change_order_status,
)
from app.services import create_estimate
from app.services.direct_cost_actuals import create_direct_cost_actual
from app.services.estimate_builder import add_manual_line, create_section
from app.services.estimates import lock_version
from app.services.instance_authority import set_instance_owner
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.proposals import create_proposal, create_proposal_template, update_proposal_status
from app.services.work_scope import (
    add_authorized_change_order_activity,
    change_order_is_extra_work,
    create_change_order_from_extra_work,
    create_extra_work,
    link_extra_work_to_change_order,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user


def _app(tmp_path):
    db_path = tmp_path / "f07-approved-internal-cost.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-f07",
            "WTF_CSRF_ENABLED": False,
        }
    )


@pytest.fixture
def app(tmp_path):
    application = _app(tmp_path)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


def _office_membership():
    user = ensure_office_user()
    return UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    ).one()


def _make_owner():
    user = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, user)
    return user, membership


def _project(name="F07 Project"):
    _make_owner()
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="f07@example.com",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _extra(project, description="Temp heat"):
    return create_extra_work(
        project_id=project.id,
        description=description,
        created_by="Joel Brayman",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )


def _draft_extra_co(project, extra, title="Extra CO"):
    change_order, linked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title=title,
        actor_display_name="Joel Brayman",
    )
    db.session.refresh(change_order)
    db.session.refresh(linked)
    return change_order, linked


def _baseline(project, *, direct="1000.00", selling="2000.00"):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-F07-0001",
        title="F07 baseline",
        organization_id=project.organization_id,
    )
    version = estimate.current_version
    section = create_section(version, name="General")
    add_manual_line(
        section,
        line_type="Custom",
        description="Work",
        quantity=1,
        unit="ea",
        unit_cost=1000,
    )
    lock_version(version)
    snapshot = EstimatePricingSnapshot(
        organization_id=project.organization_id,
        estimate_version_id=version.id,
        method="TRUE_GROSS_MARGIN",
        resolution_source="policy",
        requires_review=False,
        direct_cost_basis=Decimal(direct),
        contingency_visibility="UNSPECIFIED",
        overhead_treatment="UNSPECIFIED",
        profit_treatment="UNSPECIFIED",
        pre_tax_selling_price=Decimal(selling),
        tax_amount=Decimal("13.00"),
        tax_percent=Decimal("13"),
        customer_total=Decimal(selling) + Decimal("13.00"),
        created_by="Estimator",
    )
    db.session.add(snapshot)
    db.session.commit()
    template = create_proposal_template(
        name="F07 Template",
        is_default=True,
        is_active=True,
        default_intro_text="Intro",
        default_payment_terms="Net 30",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
        status="Draft",
        title="F07 accepted",
    )
    update_proposal_status(proposal, "Accepted")
    return estimate, version


def test_a_b_extra_work_approval_captures_positive_cost(app):
    project = _project()
    extra = _extra(project)
    change_order, _linked = _draft_extra_co(project, extra)
    add_change_order_item(
        change_order, description="Sell line", quantity=1, unit="ea", unit_price=400
    )
    db.session.refresh(change_order)
    sell = Decimal(change_order.subtotal)
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost="125.50"
    )
    db.session.refresh(change_order)
    assert change_order.status == "Approved"
    assert change_order.approved_internal_direct_cost == Decimal("125.50")
    assert change_order.approved_internal_direct_cost != sell
    assert change_order_is_extra_work(change_order) is True


def test_c_zero_is_distinct_from_null(app):
    project = _project()
    extra = _extra(project)
    change_order, _linked = _draft_extra_co(project, extra)
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost="0.00"
    )
    db.session.refresh(change_order)
    assert change_order.approved_internal_direct_cost == Decimal("0.00")
    assert change_order.approved_internal_direct_cost is not None


def test_d_blank_persists_as_null(app):
    project = _project()
    extra = _extra(project)
    change_order, _linked = _draft_extra_co(project, extra)
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost=""
    )
    db.session.refresh(change_order)
    assert change_order.approved_internal_direct_cost is None


def test_e_f_negative_fails_and_does_not_approve(app):
    project = _project()
    extra = _extra(project)
    change_order, _linked = _draft_extra_co(project, extra)
    with pytest.raises(ChangeOrderServiceError, match="cannot be negative"):
        update_change_order_status(
            change_order, "Approved", approved_internal_direct_cost="-0.01"
        )
    db.session.refresh(change_order)
    assert change_order.status == "Draft"
    assert change_order.approved_internal_direct_cost is None


def test_g_h_i_sell_markup_total_are_not_copied(app):
    project = _project()
    extra = _extra(project)
    change_order, _linked = _draft_extra_co(project, extra)
    add_change_order_item(
        change_order, description="Customer line", quantity=2, unit="ea", unit_price=50
    )
    update_change_order(change_order, markup_percent="10")
    db.session.refresh(change_order)
    assert Decimal(change_order.subtotal) > 0
    assert Decimal(change_order.markup) > 0
    assert Decimal(change_order.total) > 0
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost=""
    )
    db.session.refresh(change_order)
    assert change_order.approved_internal_direct_cost is None
    assert change_order.approved_internal_direct_cost != Decimal(change_order.subtotal)
    assert change_order.approved_internal_direct_cost != Decimal(change_order.markup)
    assert change_order.approved_internal_direct_cost != Decimal(change_order.total)


def test_j_standalone_commercial_co_does_not_capture(app):
    project = _project()
    change_order = create_change_order(
        project=project, title="Standalone commercial", status="Draft"
    )
    add_change_order_item(
        change_order, description="Sell only", quantity=1, unit="ea", unit_price=999
    )
    update_change_order_status(change_order, "Approved")
    db.session.refresh(change_order)
    assert change_order_is_extra_work(change_order) is False
    assert change_order.approved_internal_direct_cost is None
    assert change_order.status == "Approved"


def test_k_identification_stored_extra_work_origin(app):
    project = _project()
    extra = _extra(project)
    change_order, linked = _draft_extra_co(project, extra)
    assert linked.scope_origin == SCOPE_EXTRA_WORK
    assert change_order_is_extra_work(change_order) is True


def test_l_identification_change_order_origin_with_extra_history(app):
    project = _project()
    extra = _extra(project)
    approved = create_change_order(
        project=project, title="Already approved", status="Approved"
    )
    linked = link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=approved.id,
        actor_display_name="Joel Brayman",
        approved_internal_direct_cost="40.00",
    )
    assert linked.scope_origin == SCOPE_CHANGE_ORDER
    db.session.refresh(approved)
    assert change_order_is_extra_work(approved) is True
    assert approved.approved_internal_direct_cost == Decimal("40.00")


def test_m_authorized_created_work_without_extra_history_is_excluded(app):
    project = _project()
    extra = _extra(project, "Unrelated extra")
    change_order = create_change_order(
        project=project, title="Authorized created", status="Approved"
    )
    add_authorized_change_order_activity(
        project_work_element_id=extra.project_work_element_id,
        change_order_id=change_order.id,
        display_name="Pad from CO",
        estimated_hours="4",
        created_by="Joel Brayman",
    )
    db.session.refresh(change_order)
    assert change_order_is_extra_work(change_order) is False
    update_change_order_status(change_order, "Draft")
    update_change_order_status(change_order, "Approved")
    db.session.refresh(change_order)
    assert change_order.approved_internal_direct_cost is None


def test_n_cannot_edit_while_authorized(app):
    project = _project()
    extra = _extra(project)
    change_order, _linked = _draft_extra_co(project, extra)
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost="80.00"
    )
    with pytest.raises(ChangeOrderServiceError, match=APPROVED_INTERNAL_COST_FROZEN):
        update_change_order(
            change_order,
            notes="try to change cost",
            approved_internal_direct_cost="99.00",
        )
    db.session.refresh(change_order)
    assert change_order.approved_internal_direct_cost == Decimal("80.00")
    update_change_order_status(change_order, "Invoiced")
    with pytest.raises(ChangeOrderServiceError, match=APPROVED_INTERNAL_COST_FROZEN):
        update_change_order(
            change_order,
            notes="still frozen",
            approved_internal_direct_cost="1.00",
        )


def test_o_p_q_r_reverse_keeps_value_and_reapproval_processes_field(app):
    project = _project()
    extra = _extra(project)
    change_order, _linked = _draft_extra_co(project, extra)
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost="60.00"
    )
    update_change_order_status(change_order, "Draft")
    db.session.refresh(change_order)
    assert change_order.status == "Draft"
    assert change_order.approved_internal_direct_cost == Decimal("60.00")
    with pytest.raises(ChangeOrderServiceError, match=APPROVED_INTERNAL_COST_REQUIRED):
        update_change_order_status(change_order, "Approved")
    db.session.refresh(change_order)
    assert change_order.status == "Draft"
    assert change_order.approved_internal_direct_cost == Decimal("60.00")
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost=""
    )
    db.session.refresh(change_order)
    assert change_order.status == "Approved"
    assert change_order.approved_internal_direct_cost is None
    update_change_order_status(change_order, "Pending Approval")
    update_change_order_status(
        change_order, "Approved", approved_internal_direct_cost="0.00"
    )
    db.session.refresh(change_order)
    assert change_order.approved_internal_direct_cost == Decimal("0.00")


def test_s_t_late_link_to_authorizing_co_captures_and_negative_fails(app):
    project = _project()
    extra = _extra(project)
    approved = create_change_order(
        project=project, title="Standalone then extra", status="Approved"
    )
    with pytest.raises(Exception, match="cannot be negative"):
        link_extra_work_to_change_order(
            project_work_activity_id=extra.id,
            change_order_id=approved.id,
            actor_display_name="Joel Brayman",
            approved_internal_direct_cost="-5",
        )
    db.session.refresh(approved)
    db.session.refresh(extra)
    assert extra.change_order_id is None
    assert extra.scope_origin == SCOPE_EXTRA_WORK
    assert approved.approved_internal_direct_cost is None
    linked = link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=approved.id,
        actor_display_name="Joel Brayman",
        approved_internal_direct_cost="33.00",
    )
    db.session.refresh(approved)
    assert linked.change_order_id == approved.id
    assert approved.approved_internal_direct_cost == Decimal("33.00")


def test_u_v_w_x_y_z_monitor_complete_set_and_not_captured(app):
    project = _project()
    _baseline(project)
    extra_a = _extra(project, "Extra A")
    extra_b = _extra(project, "Extra B")
    co_a, _linked_a = _draft_extra_co(project, extra_a, title="Extra A CO")
    co_b, _linked_b = _draft_extra_co(project, extra_b, title="Extra B CO")
    standalone = create_change_order(
        project=project, title="Standalone revenue", status="Draft"
    )
    add_change_order_item(
        standalone, description="Revenue", quantity=1, unit="ea", unit_price="200"
    )
    update_change_order_status(standalone, "Approved")
    update_change_order_status(co_a, "Approved", approved_internal_direct_cost="50.00")
    update_change_order_status(co_b, "Approved", approved_internal_direct_cost="")
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["extra_work_internal_cost_state"] == "NOT_CAPTURED"
    assert view["extra_work_approved_internal_direct_cost"] is None
    assert view["current_authorized_estimated_cost"] == Decimal("1000.00")
    assert view["co_cost_delta_copy"] == "Not captured"
    assert view["approved_co_revenue_delta"] == Decimal(standalone.subtotal) + Decimal(
        standalone.markup or 0
    ) + Decimal(co_a.subtotal or 0) + Decimal(co_a.markup or 0) + Decimal(
        co_b.subtotal or 0
    ) + Decimal(co_b.markup or 0)
    assert "cost_variance" not in view
    assert "variance_percent" not in view
    update_change_order_status(co_b, "Draft")
    update_change_order_status(
        co_b, "Approved", approved_internal_direct_cost="25.00"
    )
    complete = assemble_monitor_v1(project, project.organization_id)
    assert complete["extra_work_internal_cost_state"] == "COMPLETE"
    assert complete["extra_work_approved_internal_direct_cost"] == Decimal("75.00")
    assert complete["current_authorized_estimated_cost"] == Decimal("1075.00")
    assert complete["co_cost_delta_stored"] is True
    create_direct_cost_actual(
        project,
        cost_class="labour",
        amount="10.00",
        incurred_on="2026-09-01",
        actor_display_name="Joel Test",
        organization_id=project.organization_id,
    )
    after_actual = assemble_monitor_v1(project, project.organization_id)
    assert after_actual["actual_direct_cost_to_date"] == Decimal("10.00")
    assert after_actual["actual_cost_by_class"]["labour"] == Decimal("10.00")
    reversed_view_status = update_change_order_status(co_a, "Draft")
    ignored = assemble_monitor_v1(project, project.organization_id)
    assert reversed_view_status.approved_internal_direct_cost == Decimal("50.00")
    assert ignored["extra_work_approved_internal_direct_cost"] == Decimal("25.00")
    assert ignored["current_authorized_estimated_cost"] == Decimal("1025.00")


def test_create_already_approved_extra_work_processes_cost(app):
    project = _project()
    extra = _extra(project)
    change_order, linked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title="Created approved",
        actor_display_name="Joel Brayman",
        status="Approved",
        approved_internal_direct_cost="15.00",
    )
    db.session.refresh(change_order)
    db.session.refresh(linked)
    assert change_order.status == "Approved"
    assert change_order.approved_date is not None
    assert change_order.approved_internal_direct_cost == Decimal("15.00")
    assert linked.scope_origin == SCOPE_CHANGE_ORDER
