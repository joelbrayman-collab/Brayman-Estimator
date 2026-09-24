"""PKG-F14 organization-scoped commercial numbering.

Disposable in-memory SQLite only. Does not touch instance/brayman_estimator.db.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Client, Estimate, Organization, Project
from app.project_controls import repository as repo
from app.project_controls.models import ChangeOrder
from app.project_controls.services import create_change_order
from app.services.estimates import EstimateServiceError, create_estimate, suggest_next_estimate_number
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.proposals import (
    ProposalServiceError,
    create_proposal,
    create_proposal_template,
    suggest_next_proposal_number,
    update_proposal,
)
from app.services.work_scope import create_change_order_from_extra_work, create_extra_work
from app.services.work_structure import ensure_baseline_work_catalog


ORG_B = "ORG-F14-B"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-f14-numbering",
            "WTF_CSRF_ENABLED": False,
        }
    )
    uri = application.config["SQLALCHEMY_DATABASE_URI"]
    assert "brayman_estimator.db" not in uri
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _org_b():
    org = Organization(
        id=ORG_B,
        legal_name="F14 Second Company Ltd.",
        display_name="F14 Second Company",
        primary_address="200 King St, Toronto, ON",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _project(name="F14 Project", org_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(
        organization_id=org_id,
        name=f"{name} Client",
        email="f14@example.com",
    )
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


def _estimate(project, number, title="F14 Estimate"):
    return create_estimate(
        project_id=project.id,
        estimate_number=number,
        title=title,
        organization_id=project.organization_id,
    )


def _template(org_id, name="F14 Template"):
    return create_proposal_template(
        organization_id=org_id,
        name=name,
        company_name="F14 Co",
        is_default=True,
        is_active=True,
    )


def test_estimate_next_number_considers_only_own_organization(app):
    year = datetime.utcnow().year
    project_a = _project("Est A")
    _org_b()
    project_b = _project("Est B", org_id=ORG_B)
    _estimate(project_a, f"EST-{year}-0005")
    _estimate(project_b, f"EST-{year}-0009")
    assert suggest_next_estimate_number(
        year=year, organization_id=DEFAULT_ORGANIZATION_ID
    ) == f"EST-{year}-0006"
    assert suggest_next_estimate_number(
        year=year, organization_id=ORG_B
    ) == f"EST-{year}-0010"


def test_estimate_sequences_independent_and_same_number_legal_across_orgs(app):
    year = datetime.utcnow().year
    project_a = _project("Est A")
    _org_b()
    project_b = _project("Est B", org_id=ORG_B)
    number = f"EST-{year}-0001"
    est_a = _estimate(project_a, number, title="Org A")
    est_b = _estimate(project_b, number, title="Org B")
    assert est_a.estimate_number == est_b.estimate_number == number
    assert est_a.organization_id == DEFAULT_ORGANIZATION_ID
    assert est_b.organization_id == ORG_B
    with pytest.raises(EstimateServiceError, match="already exists"):
        _estimate(project_a, number, title="Org A dup")


def test_estimate_gap_skip_and_format_preserved(app):
    year = datetime.utcnow().year
    project_a = _project("Est A")
    _org_b()
    project_b = _project("Est B", org_id=ORG_B)
    _estimate(project_a, f"EST-{year}-0001")
    _estimate(project_a, f"EST-{year}-0003")
    _estimate(project_b, f"EST-{year}-0008")
    next_a = suggest_next_estimate_number(
        year=year, organization_id=DEFAULT_ORGANIZATION_ID
    )
    assert next_a == f"EST-{year}-0004"
    assert next_a.startswith(f"EST-{year}-")
    assert len(next_a.split("-")[-1]) == 4


def test_proposal_next_number_independent_and_same_number_legal_across_orgs(app):
    year = datetime.utcnow().year
    project_a = _project("Prop A")
    _org_b()
    project_b = _project("Prop B", org_id=ORG_B)
    est_a = _estimate(project_a, f"EST-{year}-0100")
    est_b = _estimate(project_b, f"EST-{year}-0100")
    template_a = _template(DEFAULT_ORGANIZATION_ID, "Template A")
    template_b = _template(ORG_B, "Template B")
    number = f"PROP-{year}-0001"
    create_proposal(
        estimate=est_a,
        version=est_a.current_version,
        template=template_a,
        proposal_number=number,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    create_proposal(
        estimate=est_b,
        version=est_b.current_version,
        template=template_b,
        proposal_number=f"PROP-{year}-0007",
        organization_id=ORG_B,
    )
    assert suggest_next_proposal_number(
        year=year, organization_id=DEFAULT_ORGANIZATION_ID
    ) == f"PROP-{year}-0002"
    assert suggest_next_proposal_number(
        year=year, organization_id=ORG_B
    ) == f"PROP-{year}-0008"
    create_proposal(
        estimate=est_b,
        version=est_b.current_version,
        template=template_b,
        proposal_number=number,
        organization_id=ORG_B,
    )
    with pytest.raises(ProposalServiceError, match="already exists"):
        create_proposal(
            estimate=est_a,
            version=est_a.current_version,
            template=template_a,
            proposal_number=number,
            organization_id=DEFAULT_ORGANIZATION_ID,
        )


def test_proposal_gap_skip_and_format_preserved(app):
    year = datetime.utcnow().year
    project_a = _project("Prop A")
    est_a = _estimate(project_a, f"EST-{year}-0200")
    template_a = _template(DEFAULT_ORGANIZATION_ID)
    create_proposal(
        estimate=est_a,
        version=est_a.current_version,
        template=template_a,
        proposal_number=f"PROP-{year}-0001",
    )
    create_proposal(
        estimate=est_a,
        version=est_a.current_version,
        template=template_a,
        proposal_number=f"PROP-{year}-0003",
    )
    next_a = suggest_next_proposal_number(
        year=year, organization_id=DEFAULT_ORGANIZATION_ID
    )
    assert next_a == f"PROP-{year}-0004"
    assert next_a.startswith("PROP-")
    assert next_a.split("-")[-1] == "0004"


def test_proposal_update_duplicate_is_organization_scoped(app):
    year = datetime.utcnow().year
    project_a = _project("Prop A")
    _org_b()
    project_b = _project("Prop B", org_id=ORG_B)
    est_a = _estimate(project_a, f"EST-{year}-0300")
    est_b = _estimate(project_b, f"EST-{year}-0300")
    template_a = _template(DEFAULT_ORGANIZATION_ID, "Upd A")
    template_b = _template(ORG_B, "Upd B")
    prop_a1 = create_proposal(
        estimate=est_a,
        version=est_a.current_version,
        template=template_a,
        proposal_number=f"PROP-{year}-0001",
    )
    prop_a2 = create_proposal(
        estimate=est_a,
        version=est_a.current_version,
        template=template_a,
        proposal_number=f"PROP-{year}-0002",
    )
    create_proposal(
        estimate=est_b,
        version=est_b.current_version,
        template=template_b,
        proposal_number=f"PROP-{year}-0002",
        organization_id=ORG_B,
    )
    update_proposal(prop_a1, proposal_number=f"PROP-{year}-0099")
    assert prop_a1.proposal_number == f"PROP-{year}-0099"
    with pytest.raises(ProposalServiceError, match="already exists"):
        update_proposal(prop_a1, proposal_number=f"PROP-{year}-0002")
    update_proposal(prop_a2, proposal_number=f"PROP-{year}-0002")


def test_change_order_org_b_starts_at_000001_and_does_not_advance_org_a(app):
    project_a = _project("CO A")
    _org_b()
    project_b = _project("CO B", org_id=ORG_B)
    create_change_order(project=project_a, title="A1")
    create_change_order(project=project_a, title="A2")
    assert repo.next_change_order_number(
        organization_id=DEFAULT_ORGANIZATION_ID
    ) == "CO-000003"
    assert repo.next_change_order_number(organization_id=ORG_B) == "CO-000001"
    co_b = create_change_order(
        project=project_b, title="B1", organization_id=ORG_B
    )
    assert co_b.number == "CO-000001"
    assert repo.next_change_order_number(
        organization_id=DEFAULT_ORGANIZATION_ID
    ) == "CO-000003"


def test_change_order_latest_id_not_max_scan(app):
    project_a = _project("CO algo")
    create_change_order(project=project_a, title="High", number="CO-000009")
    create_change_order(project=project_a, title="Later low", number="CO-000002")
    next_number = repo.next_change_order_number(
        organization_id=DEFAULT_ORGANIZATION_ID
    )
    assert next_number == "CO-000003"
    assert next_number != "CO-000010"
    assert next_number.startswith("CO-")
    assert len(next_number.split("-")[-1]) == 6


def test_change_order_unparseable_fallback_is_organization_scoped(app):
    project_a = _project("CO fallback A")
    _org_b()
    project_b = _project("CO fallback B", org_id=ORG_B)
    create_change_order(project=project_a, title="Bad A", number="CO-BAD")
    create_change_order(
        project=project_b, title="B1", organization_id=ORG_B, number="CO-000004"
    )
    assert repo.next_change_order_number(
        organization_id=DEFAULT_ORGANIZATION_ID
    ) == "CO-000002"
    assert repo.next_change_order_number(organization_id=ORG_B) == "CO-000005"


def test_create_paths_stamp_truthful_organization_id(app):
    year = datetime.utcnow().year
    project_a = _project("Stamp A")
    _org_b()
    project_b = _project("Stamp B", org_id=ORG_B)
    est = _estimate(project_b, f"EST-{year}-0400")
    assert est.organization_id == ORG_B
    template = _template(ORG_B, "Stamp T")
    proposal = create_proposal(
        estimate=est,
        version=est.current_version,
        template=template,
        proposal_number=f"PROP-{year}-0400",
        organization_id=ORG_B,
    )
    assert proposal.organization_id == ORG_B
    co = create_change_order(
        project=project_b, title="Stamp CO", organization_id=ORG_B
    )
    assert co.organization_id == ORG_B


def test_unresolvable_organization_fails_closed(app):
    with pytest.raises(EstimateServiceError, match="Organization is required"):
        suggest_next_estimate_number(organization_id="")
    with pytest.raises(ProposalServiceError, match="Organization is required"):
        suggest_next_proposal_number(organization_id="")
    with pytest.raises(ValueError, match="Organization is required"):
        repo.next_change_order_number(organization_id="")


def test_s16_db_unique_allows_cross_org_and_rejects_same_org(app):
    year = datetime.utcnow().year
    project_a = _project("UQ A")
    _org_b()
    project_b = _project("UQ B", org_id=ORG_B)
    number = f"EST-{year}-0500"
    _estimate(project_a, number)
    _estimate(project_b, number)
    nested = db.session.begin_nested()
    with pytest.raises(IntegrityError):
        db.session.add(
            Estimate(
                organization_id=DEFAULT_ORGANIZATION_ID,
                project_id=project_a.id,
                estimate_number=number,
                title="Dup",
            )
        )
        db.session.flush()
    nested.rollback()


def test_estimate_edit_duplicate_check_is_organization_scoped(app, client):
    from tests.auth_fixtures import ensure_office_user, login_office_user

    year = datetime.utcnow().year
    ensure_office_user()
    login_office_user(client)
    project_a = _project("Edit A")
    _org_b()
    project_b = _project("Edit B", org_id=ORG_B)
    est_a1 = _estimate(project_a, f"EST-{year}-0601")
    est_a2 = _estimate(project_a, f"EST-{year}-0602")
    _estimate(project_b, f"EST-{year}-0700")
    same_org = client.post(
        f"/estimates/{est_a1.id}/edit",
        data={
            "project_id": str(project_a.id),
            "estimate_number": f"EST-{year}-0602",
            "title": est_a1.title,
            "status": "Draft",
            "overhead_percent": "0",
            "profit_percent": "0",
            "tax_percent": "0",
            "version_status": "Draft",
        },
        follow_redirects=True,
    )
    assert same_org.status_code == 200
    assert b"already exists" in same_org.data
    db.session.refresh(est_a1)
    assert est_a1.estimate_number == f"EST-{year}-0601"
    cross_org = client.post(
        f"/estimates/{est_a1.id}/edit",
        data={
            "project_id": str(project_a.id),
            "estimate_number": f"EST-{year}-0700",
            "title": est_a1.title,
            "status": "Draft",
            "overhead_percent": "0",
            "profit_percent": "0",
            "tax_percent": "0",
            "version_status": "Draft",
        },
        follow_redirects=True,
    )
    assert cross_org.status_code == 200
    db.session.refresh(est_a1)
    assert est_a1.estimate_number == f"EST-{year}-0700"
    db.session.refresh(est_a2)
    assert est_a2.estimate_number == f"EST-{year}-0602"


def test_extra_to_co_receives_organization_scoped_number(app):
    project_a = _project("Extra A")
    _org_b()
    project_b = _project("Extra B", org_id=ORG_B)
    create_change_order(project=project_a, title="Existing A1")
    extra = create_extra_work(
        project_id=project_b.id,
        description="Org B extra",
        created_by="Joel Brayman",
        organization_id=ORG_B,
    )
    change_order, _linked = create_change_order_from_extra_work(
        project_work_activity_id=extra.id,
        title="From extra",
        actor_display_name="Joel Brayman",
        organization_id=ORG_B,
    )
    assert change_order.number == "CO-000001"
    assert change_order.organization_id == ORG_B
    assert repo.next_change_order_number(
        organization_id=DEFAULT_ORGANIZATION_ID
    ) == "CO-000002"
