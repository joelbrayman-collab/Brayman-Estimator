"""FG-025 contractor-facing display mapping (Slice 1 MONITOR + Slice 2 Hub + Slice 3 PRICE + Slice 4 office shell + Slice 5 Field Web).

Presentation tests only. Internal domain keys stay authoritative.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

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
    LABOUR_RATES_HEADING,
    PERMIT_ADVISORY_EYEBROW,
    PERMIT_FOUNDATION_EYEBROW,
    PERMIT_RECHECK_HEADING,
    PREVIOUS_ENTRIES_EMPTY,
    PREVIOUS_ENTRIES_HEADING,
    PRICING_ASSUMPTIONS_HEADING,
    PRICING_HEADING,
    LEGACY_PRICING_ASSUMPTIONS_HEADING,
    NO_PRICING_ASSUMPTIONS,
    RECORD_CORRECTION_BUTTON,
    SOURCE_HEADLINE,
    SOURCE_NOTES_LABEL,
    CATALOGUE_COLUMN_LABEL,
    DASHBOARD_HEADING,
    DASHBOARD_LEDE,
    LOGIN_LEDE,
    SIGN_OUT_LABEL,
    BRAND_PROFILE_HEADING,
    FIELD_SAVE_ORIGINAL,
    FIELD_NOTES_LABEL,
    FIELD_CHANGE_PROJECT,
    FIELD_CONFIRM_BEFORE_CAPTURE,
    FIELD_NO_PROJECTS,
    FIELD_RETRY_HEADING,
    FIELD_RETRY_LINK,
    FIELD_RETRY_ONE,
    FIELD_RETRY_MANY_SUFFIX,
    FIELD_SAVED,
    FIELD_SAVING,
    FIELD_NEEDS_RETRY,
    FIELD_EVENT_SAVE_FAILED,
    FIELD_ORIGINAL_SAVE_FAILED,
    FIELD_CAPTURE_START_FAILED,
    FIELD_ADD_BEFORE_SAVE,
    FIELD_LOGOUT_CONFIRM,
    FIELD_OTHER_PROJECT_PENDING,
    FIELD_DISCARD_OTHER_PENDING,
    co_cost_delta_label,
    cost_class_label,
    entry_reference,
    monitor_empty_copy,
    monitor_source_detail,
    monitor_source_headline,
    monitor_state_label,
    office_status_label,
    pricing_method_label,
    sentence_label,
)
from app.services.direct_cost_actuals import list_active_direct_cost_actuals, list_direct_cost_actuals
from app.services.monitor import assemble_monitor_v1
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.pricing_engine import create_pricing_policy
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


def test_slice3_pricing_method_labels_are_pinned():
    assert LABOUR_RATES_HEADING == "Labour rates"
    assert PRICING_HEADING == "Pricing"
    assert SOURCE_NOTES_LABEL == "Source notes"
    assert CATALOGUE_COLUMN_LABEL == "Catalogue"
    assert pricing_method_label("TRUE_GROSS_MARGIN") == "Gross Margin Pricing"
    assert pricing_method_label("COST_PLUS_MARKUP") == "Cost plus markup"
    assert pricing_method_label("COST_PLUS_MARKUP_STACK") == (
        "Cost plus markup (legacy stack)"
    )
    assert "Markup" not in pricing_method_label("TRUE_GROSS_MARGIN")
    assert office_status_label("ORG_APPROVED") == "Organization approved"
    assert office_status_label("ORG-APPROVED") == "Organization approved"
    assert office_status_label("NOT_LABOUR") == "Not labour"
    assert office_status_label("DRAFT") == "Draft"


def test_slice3_internal_pricing_method_keys_remain():
    from app.models.pricing_engine import PRICING_METHODS

    assert "TRUE_GROSS_MARGIN" in PRICING_METHODS
    assert pricing_method_label("TRUE_GROSS_MARGIN") != "TRUE_GROSS_MARGIN"
    assert pricing_method_label("TRUE_GROSS_MARGIN") != "Markup Pricing"


def test_slice3_labour_and_pricing_office_copy(client, project):
    labour = _html(client.get("/labour-engine/"))
    assert "<h1>Labour rates</h1>" in labour
    assert "Canonical Labour Tasks" not in labour
    assert "Labour tasks" in labour
    assert "FG-008" not in labour
    assert "organization_id" not in labour
    create_pricing_policy(
        policy_code="ORG-001-TRUE-GM-15",
        method="TRUE_GROSS_MARGIN",
        actor="Joel Brayman",
        target_gross_margin=Decimal("0.15"),
        tax_percent=Decimal("13"),
        is_default=True,
    )
    from app import db

    db.session.commit()
    pricing = _html(client.get("/pricing-engine/"))
    assert "<h1>Pricing</h1>" in pricing
    assert "TRUE_GROSS_MARGIN" not in pricing
    assert "Gross Margin Pricing" in pricing
    assert "Markup Pricing" not in pricing
    assert "FG-009" not in pricing
    assert "organization_id" not in pricing
    catalogue = _html(client.get("/material-catalogue/"))
    assert "Material Catalogue" in catalogue
    assert "Organization ORG-001" not in catalogue
    assert ">GENERIC<" not in catalogue
    assert ">ACTIVE<" not in catalogue
    library = _html(client.get("/cost-library/"))
    assert "Cost Library" in library
    assemblies = _html(client.get("/assemblies/"))
    assert "Assemblies" in assemblies
    hub = _html(client.get(f"/projects/{project.id}"))
    method_block = hub.split("Organization methodology:", 1)[1][:500]
    assert "Labour rates" in method_block
    assert "Pricing Engine" not in method_block
    assert "Labour Engine" not in method_block
    assert "LEARN · Future" in hub
    assert "NET PROFIT" not in hub
    assert PRICING_ASSUMPTIONS_HEADING in hub
    assert PERMIT_FOUNDATION_EYEBROW in hub
    assert "Original Estimated Direct Cost" in hub
    view = assemble_monitor_v1(project, project.organization_id)
    assert view["actuals_state"] == "MISSING_ACTUALS"


def test_slice4_office_shell_labels_are_pinned():
    assert LABOUR_RATES_HEADING == "Labour rates"
    assert PRICING_HEADING == "Pricing"
    assert LOGIN_LEDE == "Sign in with your email and password."
    assert SIGN_OUT_LABEL == "Sign out"
    assert DASHBOARD_HEADING == "Office home"
    assert DASHBOARD_LEDE == "Open a project, start an estimate, or issue a proposal."
    assert BRAND_PROFILE_HEADING == "Brand profile"


def test_slice4_nav_routes_and_engine_labels(client, project):
    from app.navigation import NAV_ITEMS

    labour = next(item for item in NAV_ITEMS if item["endpoint"] == "labour_engine.index")
    pricing = next(item for item in NAV_ITEMS if item["endpoint"] == "pricing_engine.index")
    assert labour["title"] == LABOUR_RATES_HEADING
    assert pricing["title"] == PRICING_HEADING
    home = _html(client.get("/"))
    assert 'href="/labour-engine/"' in home
    assert 'href="/pricing-engine/"' in home
    assert ">Labour rates<" in home
    assert ">Pricing<" in home
    assert "Labour Engine" not in home
    assert "Pricing Engine" not in home
    assert DASHBOARD_HEADING in home
    assert "Executive overview" not in home
    assert SIGN_OUT_LABEL in home
    assert 'aria-label="Log out"' not in home
    hub = _html(client.get(f"/projects/{project.id}"))
    assert "LEARN · Future" in hub
    assert "NET PROFIT" not in hub
    settings = _html(client.get("/settings/brand-profile"))
    assert f"<h1>{BRAND_PROFILE_HEADING}</h1>" in settings
    assert "Organization Brand Profile" not in settings
    assert "Remote URLs" not in settings
    assert " MiB" not in settings
    field = _html(client.get("/field/today"))
    assert SIGN_OUT_LABEL in field
    assert "Log out" not in field
    assert "shell-sidebar" not in field


@pytest.mark.no_office_auth
def test_slice4_login_copy_and_auth_behavior(client):
    from tests.auth_fixtures import ensure_office_user, login_office_user

    page = _html(client.get("/login"))
    assert LOGIN_LEDE in page
    assert "organization membership credentials" not in page
    assert "Office sign in" in page
    ensure_office_user()
    response = login_office_user(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    follow = client.get("/")
    assert follow.status_code == 200
    assert DASHBOARD_HEADING.encode() in follow.data


FIELD_JS = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "field.js"


def test_slice5_field_copy_constants_are_pinned():
    assert SIGN_OUT_LABEL == "Sign out"
    assert FIELD_SAVE_ORIGINAL == "Save original"
    assert FIELD_NOTES_LABEL == "Notes"
    assert FIELD_CHANGE_PROJECT == "Change project"
    assert FIELD_CONFIRM_BEFORE_CAPTURE == "Confirm the project before capturing."
    assert FIELD_NO_PROJECTS == "No projects are available."
    assert FIELD_RETRY_HEADING == "Not sent yet"
    assert FIELD_RETRY_LINK == "Try sending again"
    assert FIELD_RETRY_ONE == "1 capture did not send."
    assert FIELD_RETRY_MANY_SUFFIX == " captures did not send."
    assert FIELD_SAVED == "Saved"
    assert FIELD_SAVING == "Saving…"
    assert FIELD_NEEDS_RETRY == "Could not send"
    assert FIELD_EVENT_SAVE_FAILED == "This observation could not be saved."
    assert FIELD_ORIGINAL_SAVE_FAILED == (
        "The original photo or file could not be saved."
    )
    assert FIELD_CAPTURE_START_FAILED == (
        "This phone could not start a capture. Try again."
    )
    assert FIELD_ADD_BEFORE_SAVE == "Add a photo, recording, or note before saving."
    assert FIELD_LOGOUT_CONFIRM == (
        "Unsent captures will be removed from this phone. Sign out?"
    )
    assert FIELD_OTHER_PROJECT_PENDING == (
        "A capture is still waiting on another project. "
        "Open that project to send it, or discard it?"
    )
    assert FIELD_DISCARD_OTHER_PENDING == (
        "Discard the waiting capture for the other project?"
    )


def test_slice5_field_web_surfaces_hide_raw_internal_copy(client, project):
    today = _html(client.get("/field/today"))
    assert SIGN_OUT_LABEL in today
    assert "Log out" not in today
    assert FIELD_CONFIRM_BEFORE_CAPTURE in today
    assert "Choose Project" in today
    assert 'action="/logout"' in today
    assert "shell-sidebar" not in today
    assert "app-shell" not in today
    assert "Observation Delete" not in today
    assert "Delete observation" not in today
    assert "NET PROFIT" not in today
    assert "FieldEvidenceEvent" not in today
    assert "event_id" not in today
    assert "FieldCaptureEvent" not in today
    projects = _html(client.get("/field/projects"))
    assert SIGN_OUT_LABEL in projects
    assert "Log out" not in projects
    assert "Select the job you are standing on." in projects
    assert "Observation Delete" not in projects
    confirm = client.post(
        f"/field/projects/{project.id}",
        data={"next": "capture"},
        follow_redirects=False,
    )
    assert confirm.status_code == 302
    capture = _html(client.get(f"/field/projects/{project.id}/capture"))
    assert FIELD_SAVE_ORIGINAL in capture
    assert FIELD_NOTES_LABEL in capture
    assert "Take Photo" in capture
    assert "Choose Photo" in capture
    assert "Save original" in capture
    assert "Short text" not in capture
    assert "Log out" not in capture
    assert "rendition" not in capture.lower()
    assert "Observation Delete" not in capture
    assert "Delete observation" not in capture
    assert "NET PROFIT" not in capture
    today_confirmed = _html(client.get("/field/today"))
    assert FIELD_CHANGE_PROJECT in today_confirmed
    assert FIELD_RETRY_HEADING in today_confirmed
    assert FIELD_RETRY_LINK in today_confirmed
    assert "Capture" in today_confirmed
    assert "Switch Project" not in today_confirmed
    assert "Needs Retry" not in today_confirmed
    hub = _html(client.get(f"/projects/{project.id}"))
    assert "LEARN · Future" in hub
    assert "NET PROFIT" not in hub


def test_slice5_field_js_pins_python_copy_and_internal_keys():
    source = FIELD_JS.read_text(encoding="utf-8")
    assert f'signOut: "{SIGN_OUT_LABEL}"' in source
    assert f'saved: "{FIELD_SAVED}"' in source
    assert f'saving: "{FIELD_SAVING}"' in source
    assert f'needsRetry: "{FIELD_NEEDS_RETRY}"' in source
    assert f'eventSaveFailed: "{FIELD_EVENT_SAVE_FAILED}"' in source
    assert f'originalSaveFailed: "{FIELD_ORIGINAL_SAVE_FAILED}"' in source
    assert f'captureStartFailed: "{FIELD_CAPTURE_START_FAILED}"' in source
    assert f'addBeforeSave: "{FIELD_ADD_BEFORE_SAVE}"' in source
    assert f'logoutConfirm: "{FIELD_LOGOUT_CONFIRM}"' in source
    assert FIELD_OTHER_PROJECT_PENDING in source
    assert f'discardOtherPending: "{FIELD_DISCARD_OTHER_PENDING}"' in source
    assert f'retryOne: "{FIELD_RETRY_ONE}"' in source
    assert f'retryManySuffix: "{FIELD_RETRY_MANY_SUFFIX}"' in source
    assert 'setAttribute("data-state", state)' in source
    assert '"needs_retry"' in source
    assert "pending_captures" in source
    assert "pending_originals" in source
    assert "Log out" not in source
    assert "Event could not be saved." not in source
    assert "Original could not be saved." not in source
    assert "This browser cannot create a capture identity." not in source
    assert "NEEDS RETRY" not in source
    assert 'setFeedback("SAVED"' not in source
    assert 'setStatus("SAVED")' not in source
    assert 'setFeedback("SAVING"' not in source
    assert "short text" not in source
    assert "Observation Delete" not in source
    assert "Delete observation" not in source
    assert "NET PROFIT" not in source
