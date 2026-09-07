"""FG-025 Slice 1 contractor-facing MONITOR display mapping.

Presentation tests only. Internal domain keys stay authoritative.
"""

from __future__ import annotations

import pytest

from app import create_app, db
from app.models import Client, Project
from app.presentation.contractor_copy import (
    CO_COST_DELTA_INTERNAL,
    CO_COST_DELTA_LABEL,
    CORRECTED_BY_HEADING,
    CORRECTED_ITEM_LABEL,
    CURRENT_ACTUALS_EMPTY,
    CURRENT_ACTUALS_HEADING,
    PERMIT_ADVISORY_EYEBROW,
    PERMIT_FOUNDATION_EYEBROW,
    PERMIT_RECHECK_HEADING,
    PREVIOUS_ENTRIES_EMPTY,
    PREVIOUS_ENTRIES_HEADING,
    PRICING_ASSUMPTIONS_HEADING,
    LEGACY_PRICING_ASSUMPTIONS_HEADING,
    NO_PRICING_ASSUMPTIONS,
    RECORD_CORRECTION_BUTTON,
    SOURCE_HEADLINE,
    co_cost_delta_label,
    cost_class_label,
    entry_reference,
    monitor_empty_copy,
    monitor_source_detail,
    monitor_source_headline,
    monitor_state_label,
    sentence_label,
)
from app.services.direct_cost_actuals import list_active_direct_cost_actuals, list_direct_cost_actuals
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.test_monitor_v1_fg023 import (
    _accept,
    _add_snapshot,
    _complete_baseline,
    _estimate_with_line,
    _html,
    _monitor_html,
    _post_actual,
    _template,
)


RAW_STATE_LABELS = (
    "MISSING_ACTUALS",
    "MISSING ACTUALS",
    "MISSING_CUSTOMER_COMMITMENT",
    "MISSING CUSTOMER COMMITMENT",
    "AMBIGUOUS_COMMITMENT",
    "AMBIGUOUS COMMITMENT",
    "MISSING_ORIGINAL_BASELINE",
    "MISSING ORIGINAL BASELINE",
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg025",
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
def client(app):
    return app.test_client()


@pytest.fixture
def project(app):
    client_row = Client(name="FG-025 Client", company="FG-025 Co")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="FG-025 Project",
        address="10 Main St",
        client_id=client_row.id,
        status="Estimating",
        project_number="FG025-001",
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    db.session.add(project)
    db.session.commit()
    return project


def test_monitor_state_labels_are_pinned():
    assert monitor_state_label("MISSING_ACTUALS") == "No actual costs entered yet"
    assert monitor_state_label("MISSING_CUSTOMER_COMMITMENT") == "No accepted proposal yet"
    assert monitor_state_label("AMBIGUOUS_COMMITMENT") == (
        "More than one accepted proposal — this screen will not pick one"
    )
    assert monitor_state_label("MISSING_ORIGINAL_BASELINE") == (
        "An accepted proposal exists, but the original estimate cannot be used"
    )


def test_cost_class_labels_are_pinned():
    assert cost_class_label("other_direct") == "Other direct cost"
    assert cost_class_label("labour") == "Labour"
    assert cost_class_label("material") == "Material"
    assert cost_class_label("subcontract") == "Subcontract"


def test_actual_group_and_correction_copy_are_pinned():
    assert CURRENT_ACTUALS_HEADING == "Current actual costs"
    assert CURRENT_ACTUALS_EMPTY == "No current actual-cost entries"
    assert PREVIOUS_ENTRIES_HEADING == "Previous entries"
    assert CORRECTED_ITEM_LABEL == "Corrected"
    assert CORRECTED_BY_HEADING == "Corrected by"
    assert PREVIOUS_ENTRIES_EMPTY == "No previous cost corrections."
    assert RECORD_CORRECTION_BUTTON == "Record correction"
    assert PRICING_ASSUMPTIONS_HEADING == "Pricing assumptions"
    assert NO_PRICING_ASSUMPTIONS == "No pricing assumptions recorded."
    assert LEGACY_PRICING_ASSUMPTIONS_HEADING == (
        "Legacy project — pricing assumptions not recorded"
    )
    assert PERMIT_FOUNDATION_EYEBROW == "Preliminary / foundation only"
    assert PERMIT_ADVISORY_EYEBROW == "Advisory only"
    assert PERMIT_RECHECK_HEADING == "Recheck required"
    assert entry_reference(123) == "Entry reference 123"
    assert sentence_label("interior_door") == "interior door"
    assert sentence_label("superseded-in-set") == "superseded in set"


def test_co_cost_delta_and_source_copy_are_pinned():
    assert co_cost_delta_label(CO_COST_DELTA_INTERNAL) == CO_COST_DELTA_LABEL
    assert CO_COST_DELTA_LABEL == (
        "Change Order estimated cost is not stored on the Change Order"
    )
    assert monitor_source_headline() == SOURCE_HEADLINE
    assert SOURCE_HEADLINE == "Source of these numbers"
    detail = monitor_source_detail({}, 0)
    assert "proposal" in detail.lower() or "No proposal" in detail
    assert "EstimatePricingSnapshot" not in detail
    assert "ProjectDirectCostActual" not in detail


def test_missing_actuals_empty_copy_follows_what_why_next():
    copy = monitor_empty_copy("MISSING_ACTUALS")
    assert copy["what"] == "No actual costs have been entered yet."
    assert copy["why"] == "Margin so far cannot be shown as $0.00."
    assert copy["next"] == "Use Record actual direct cost below."


def test_internal_domain_keys_remain_unchanged(project):
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["actuals_state"] == "MISSING_ACTUALS"
    assert view["baseline_state"] == "MISSING_CUSTOMER_COMMITMENT"
    assert view["co_cost_delta_copy"] == "CO cost delta not stored"
    assert view["actual_cost_by_class"] is None
    assert "actuals_state" in view
    assert "baseline_state" in view


def _assert_no_raw_monitor_labels(html):
    for label in RAW_STATE_LABELS:
        assert label not in html
    assert ">other_direct<" not in html
    assert "Actual Direct Cost — other_direct" not in html
    assert "ProjectDirectCostActual" not in html
    assert "EstimatePricingSnapshot" not in html
    assert "source version" not in html
    assert "Provenance:" not in html


def test_rendered_hub_maps_missing_states_and_preserves_monitor(client, project):
    html = _html(client.get(f"/projects/{project.id}"))
    monitor = _monitor_html(html)
    assert "No actual costs entered yet" in monitor
    assert "No actual costs have been entered yet." in monitor
    assert "Margin so far cannot be shown as $0.00." in monitor
    assert "Use Record actual direct cost below." in monitor
    assert "No accepted proposal yet" in monitor
    assert "Other direct cost" in monitor
    assert "Labour" in monitor
    assert "Material" in monitor
    assert "Subcontract" in monitor
    assert CURRENT_ACTUALS_HEADING in monitor
    assert CURRENT_ACTUALS_EMPTY in monitor
    assert PREVIOUS_ENTRIES_HEADING in monitor
    assert PREVIOUS_ENTRIES_EMPTY in monitor
    assert SOURCE_HEADLINE in monitor
    assert CO_COST_DELTA_LABEL in monitor
    assert "CO cost delta not stored" not in monitor
    _assert_no_raw_monitor_labels(monitor)
    assert 'value="other_direct"' in monitor
    assert "$0.00</p>" not in monitor.split("Actual Direct Cost to Date", 1)[-1][:200]
    assert "MONITOR" in html
    assert 'id="hub-monitor"' in html
    assert "Estimated versus actual" in html
    assert "MONITOR · Future" not in html
    assert "LEARN · Future" in html
    assert "LEARN is not operational" in html
    assert "NET PROFIT" not in html
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["actuals_state"] == "MISSING_ACTUALS"
    assert view["baseline_state"] == "MISSING_CUSTOMER_COMMITMENT"
    assert "Commercial Decision Gate Context" not in html
    assert "No commercial context recorded." not in html
    assert PRICING_ASSUMPTIONS_HEADING in html
    assert NO_PRICING_ASSUMPTIONS in html
    assert PERMIT_FOUNDATION_EYEBROW in html
    assert "PRELIMINARY / FOUNDATION ONLY" not in html
    assert "RECHECK REQUIRED" not in html
    assert "Original Estimated Direct Cost" in html
    assert "Original Estimated Pre-Tax Selling Price" in html
    assert "Original Estimated GM" in html
    assert "Approved/Invoiced CO Revenue Delta" in html
    assert "Current Authorized Pre-Tax Revenue" in html
    assert "Current Authorized Estimated Cost" in html
    assert "Actual Direct Cost to Date" in html
    assert "Actual-to-Date Project Gross Margin" in html
    assert "GM Variance" in html
    assert "Current Contract Value" not in html


def test_rendered_hub_maps_ambiguous_commitment(client, project):
    first, first_version = _estimate_with_line(project, number="EST-FG025-AMB1")
    _add_snapshot(first_version, direct_cost="100.00", selling="200.00")
    template = _template("FG-025 ambiguous template")
    _accept(first, first_version, title="Accepted one", template=template)
    second, second_version = _estimate_with_line(project, number="EST-FG025-AMB2")
    _add_snapshot(second_version, direct_cost="300.00", selling="400.00")
    _accept(second, second_version, title="Accepted two", template=template)
    html = _monitor_html(_html(client.get(f"/projects/{project.id}")))
    assert (
        "More than one accepted proposal — this screen will not pick one" in html
    )
    assert "AMBIGUOUS_COMMITMENT" not in html
    assert "AMBIGUOUS COMMITMENT" not in html
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["baseline_state"] == "AMBIGUOUS_COMMITMENT"


def test_rendered_hub_maps_missing_original_baseline(client, project):
    estimate, version = _estimate_with_line(
        project, number="EST-FG025-MOB", lock=False
    )
    _accept(estimate, version, title="Accepted unlocked")
    html = _monitor_html(_html(client.get(f"/projects/{project.id}")))
    assert (
        "An accepted proposal exists, but the original estimate cannot be used" in html
    )
    assert "MISSING_ORIGINAL_BASELINE" not in html
    assert "MISSING ORIGINAL BASELINE" not in html
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["baseline_state"] == "MISSING_ORIGINAL_BASELINE"


def test_rendered_hub_maps_current_and_previous_actuals(client, project):
    _complete_baseline(project, number="EST-FG025-ACT")
    created = _post_actual(
        client,
        project.id,
        cost_class="other_direct",
        amount="100.00",
        note="original",
    )
    assert created.status_code == 302
    html = _monitor_html(_html(client.get(f"/projects/{project.id}")))
    assert CURRENT_ACTUALS_HEADING in html
    assert CURRENT_ACTUALS_EMPTY not in html
    assert "Other direct cost" in html
    assert ">other_direct<" not in html
    assert "ACTIVE actuals" not in html
    original = list_direct_cost_actuals(project.organization_id, project.id)[0]
    correction = client.post(
        f"/projects/{project.id}/direct-cost-actuals/{original.id}/supersede",
        data={
            "cost_class": "labour",
            "amount": "80.00",
            "incurred_on": "2026-09-04",
            "note": "corrected",
        },
    )
    assert correction.status_code == 302
    html = _monitor_html(_html(client.get(f"/projects/{project.id}")))
    assert PREVIOUS_ENTRIES_HEADING in html
    assert CORRECTED_ITEM_LABEL in html
    assert CORRECTED_BY_HEADING in html
    assert "Record correction" in html
    assert "SUPERSEDED</span>" not in html
    assert "Superseded actuals" not in html
    assert "Superseded by" not in html
    assert "No superseded actual-cost history." not in html
    successor_id = list_active_direct_cost_actuals(project.organization_id, project.id)[0].id
    assert entry_reference(successor_id) in html
    assert f"#{successor_id}" not in html
    assert "<th>Id</th>" not in html
    assert "<th>ID</th>" not in html
    assert "Source of these numbers" in html
    assert "pricing lock" in html
    assert "accepted proposal" in html
    assert "EstimatePricingSnapshot" not in html
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["actuals_state"] == "PRESENT"
    assert view["actual_direct_cost_to_date"] is not None
