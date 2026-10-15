"""SEC-03 (V1, 15 Oct 2026): cost, pricing and labour-rate approvals record the signed-in
person. A name typed on the form is ignored, so nobody can approve under another name."""

from decimal import Decimal

import pytest

from app import db
from app.models.estimate_costing import EstimateCostingSnapshot
from app.models.pricing_engine import EstimatePricingSnapshot, OrganizationPricingPolicy
from app.services.auth import AuthServiceError, signed_in_approver
from app.services.pricing_engine import create_pricing_policy
from tests.auth_fixtures import DEFAULT_OFFICE_DISPLAY_NAME
from tests.scope_delivery_support import ensure_confirmed_scope_routing
from tests.test_estimate_output_consistency import _direct_estimate, app, client  # noqa: F401

FORGED = "Someone Else"


def _versions_url(estimate):
    return f"/estimates/{estimate.id}/versions/{estimate.current_version.id}"


def test_approving_costing_records_the_signed_in_person_not_the_typed_name(client, app):
    estimate = _direct_estimate("EST-SEC03-1")
    ensure_confirmed_scope_routing(estimate.current_version, actor="Office Test User")
    client.post(f"{_versions_url(estimate)}/approve-all-costing", data={"approved_by": FORGED})
    snap = EstimateCostingSnapshot.query.filter_by(estimate_version_id=estimate.current_version.id).one()
    assert snap.actor_display_name == DEFAULT_OFFICE_DISPLAY_NAME
    assert snap.actor_user_id is not None


def test_applying_pricing_records_the_signed_in_person(client, app):
    estimate = _direct_estimate("EST-SEC03-2")
    ensure_confirmed_scope_routing(estimate.current_version, actor="Office Test User")
    create_pricing_policy(policy_code="SEC03-GM", method="TRUE_GROSS_MARGIN", actor="Joel Brayman",
                          target_gross_margin=Decimal("0.15"), tax_jurisdiction="CA-ON", tax_percent=Decimal("13"),
                          overhead_treatment="UNSPECIFIED", profit_treatment="UNSPECIFIED",
                          contingency_visibility="UNSPECIFIED", provenance="test", is_default=True)
    db.session.commit()
    client.post(f"{_versions_url(estimate)}/approve-all-costing", data={})
    client.post(f"{_versions_url(estimate)}/apply-org-pricing", data={"approved_by": FORGED})
    snap = EstimatePricingSnapshot.query.filter_by(estimate_version_id=estimate.current_version.id).one()
    assert snap.created_by == DEFAULT_OFFICE_DISPLAY_NAME


def test_approving_a_pricing_policy_records_the_signed_in_person(client, app):
    policy = create_pricing_policy(policy_code="SEC03-DRAFT", method="TRUE_GROSS_MARGIN", actor="Joel Brayman",
                                   target_gross_margin=Decimal("0.20"), tax_jurisdiction="CA-ON", tax_percent=Decimal("13"),
                                   overhead_treatment="UNSPECIFIED", profit_treatment="UNSPECIFIED",
                                   contingency_visibility="UNSPECIFIED", provenance="test")
    db.session.commit()
    client.post(f"/pricing-engine/policies/{policy.id}/approve", data={"approved_by": FORGED})
    assert db.session.get(OrganizationPricingPolicy, policy.id).approved_by == DEFAULT_OFFICE_DISPLAY_NAME


def test_approval_pages_show_who_is_approving_and_have_no_name_box(client, app):
    estimate = _direct_estimate("EST-SEC03-3")
    page = client.get(_versions_url(estimate)).get_data(as_text=True)
    assert f"Approving as <strong>{DEFAULT_OFFICE_DISPLAY_NAME}</strong>" in page
    assert 'name="approved_by"' not in page


def test_without_a_signed_in_person_there_is_no_approver(app):
    with app.test_request_context("/"):
        with pytest.raises(AuthServiceError, match="Sign in to approve"):
            signed_in_approver()
