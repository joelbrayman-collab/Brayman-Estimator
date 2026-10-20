"""The Project page shows the job address and the contract's signing status (job lifecycle walk, 20 Oct 2026).

Found by tests/e2e/job_lifecycle.mjs: a job entered with only the structured location showed Address "—"
on the Project page, and the Project page never said a contract had been generated, sent or signed (only
whether a contract package was available). Both are read-only facts from records kept elsewhere.
Synthetic data only.
"""

from __future__ import annotations

from app import db
from app.services import signing as S
from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.test_contract_signing_v1 import (  # noqa: F401
    SIGNER,
    _credential,
    _eastern_ontario_project,
    _generate,
    _issued,
    _send,
    app,
    client,
)


def _hub(client, project):
    response = client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_the_project_page_shows_the_job_location_when_the_free_text_address_is_blank(client, app):
    ensure_office_user(); db.session.commit()
    login_office_user(client)
    project = _eastern_ontario_project("Merrickville")
    project.address = ""; db.session.commit()
    assert '<p class="eyebrow">Address</p><p>12 Main Street, Merrickville, Ontario</p>' in _hub(client, project)
    project.address = "Lot 4, Concession 2"; db.session.commit()  # a typed address still wins
    assert '<p class="eyebrow">Address</p><p>Lot 4, Concession 2</p>' in _hub(client, project)


def test_the_project_page_follows_the_contract_from_generated_to_signed(client, app):
    user = ensure_office_user(); db.session.commit()
    login_office_user(client)
    ensure_brayman_v1_interim_ontario_package()
    project = _eastern_ontario_project("Merrickville")
    assert "data-hub-contract=" not in _hub(client, project)
    version, proposal = _issued(project, number="EST-HUB-CONTRACT")
    result = _generate(project, version, proposal)
    assert result.generated, result.block_code
    number = db.session.get(S.GeneratedProjectContract, result.contract_id).contract_number
    assert f"<strong>{number}</strong> · Generated — not signed" in _hub(client, project)
    issue = _send(result.contract_id, user)
    assert f"<strong>{number}</strong> · {S.hub_signing_label(S.STATUS_SENT)}" in _hub(client, project)
    S.accept_and_sign(_credential(issue), confirmed_signer_name=SIGNER[0], consent_accepted=True,
                      client_ip="127.0.0.1", user_agent="pytest")
    S.countersign_and_execute(issue.request.id, organization_id=DEFAULT_ORGANIZATION_ID, actor_kind="HUMAN",
                              actor_user_id=user.id, actor_identifier=user.email)
    assert f"<strong>{number}</strong> · Signed — executed" in _hub(client, project)
