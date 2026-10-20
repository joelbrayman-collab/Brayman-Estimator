"""The change order signer is filled in from the customer who accepted the proposal (job lifecycle walk, 20 Oct 2026).

The contract form already does this; the office can still change both fields. Synthetic data only.
"""

from __future__ import annotations

from decimal import Decimal

from app import db
from app.project_controls.models import ChangeOrderItem
from app.project_controls.routes import _signer_prefill
from app.project_controls.services import create_change_order
from app.services import proposal_acceptance as PA
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.auth_fixtures import login_office_user
from tests.test_proposal_client_acceptance import CLIENT, _credential, _sent, app, client  # noqa: F401


def test_change_order_signer_comes_from_the_proposal_acceptance(app, client):
    _user, project, _proposal, sent = _sent("EST-CO-SIGNER")
    change_order = create_change_order(project=project, title="Synthetic extra footing", tax_percent=13)
    assert _signer_prefill(change_order, DEFAULT_ORGANIZATION_ID) is None  # nothing accepted yet: blank fields
    PA.accept_via_link(_credential(sent), confirmed_name=CLIENT[0], accepted=True, client_ip=None, user_agent=None)
    prefill = _signer_prefill(change_order, DEFAULT_ORGANIZATION_ID)
    assert prefill == {"name": CLIENT[0], "email": CLIENT[1]}
    assert _signer_prefill(change_order, "ORG-OTHER") is None  # never another organization's customer
    db.session.add(ChangeOrderItem(change_order_id=change_order.id, description="Extra footing", quantity=Decimal("1"),
                                   unit="ea", unit_price=Decimal("600")))
    change_order.status = "Approved"
    db.session.commit()
    login_office_user(client)
    page = client.get(f"/project-controls/change-orders/{change_order.id}").get_data(as_text=True)
    assert 'data-signer-from-acceptance="true"' in page
    assert f'value="{CLIENT[0]}"' in page and f'value="{CLIENT[1]}"' in page
