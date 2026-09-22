"""R01 SERVICE TENANCY INVARIANT — mutating services re-establish organization.

Authorized ORG-A actors cannot create or modify ORG-B data by supplying a
foreign object, id, parent, child, or related commercial/work record.
"""

from decimal import Decimal

import pytest

from app import create_app, db
from app.models import (
    Assembly,
    Client,
    CostItem,
    EstimateLineItem,
    Organization,
    Project,
    ProjectCommercialContext,
)
from app.project_controls.models import ChangeOrder, ChangeOrderItem
from app.project_controls.services import (
    ChangeOrderServiceError,
    add_change_order_item,
    create_change_order,
)
from app.services.commercial_context import (
    CommercialContextValidationError,
    create_initial_commercial_context,
    update_commercial_context,
)
from app.services.estimate_builder import add_assembly_line, add_cost_item_line, create_section
from app.services.estimates import create_estimate
from app.services.organization_records import require_organization_project
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_final_walkthrough import (
    WalkthroughNotFoundError,
    create_walkthrough_invitation,
)
from app.services.project_operating_lifecycle import (
    ProjectLifecycleError,
    close_project,
)
from app.services.project_punch_list import (
    PunchListNotFoundError,
    create_punch_list_item,
)
from app.services.proposals import ProposalServiceError, create_proposal, create_proposal_template
from tests.auth_fixtures import (
    ensure_office_user,
    login_office_user,
)

ORG_A = DEFAULT_ORGANIZATION_ID
ORG_B = "ORG-002"

COMMERCIAL = {
    "project_type": "New Build",
    "pricing_posture": "Fair Market",
    "execution_risk": "Normal",
    "schedule_condition": "Normal",
    "site_condition": "Normal",
    "estimate_stage": "Budget",
    "delivery_model": "Self-Perform",
}


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-r01-tenancy",
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
def org_b(app):
    org = Organization(
        id=ORG_B,
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


def _project(org_id=ORG_A, name="R01 Project"):
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


def _cost_item(org_id, code, name, unit_cost):
    item = CostItem(
        organization_id=org_id,
        code=code,
        name=name,
        category="Material",
        unit="ea",
        unit_cost=unit_cost,
        default_markup_percent=10,
        is_active=True,
    )
    db.session.add(item)
    db.session.commit()
    return item


def _assembly(org_id, code, name):
    assembly = Assembly(
        organization_id=org_id,
        code=code,
        name=name,
        category="Other",
        unit="ea",
        default_markup_percent=0,
        is_active=True,
    )
    db.session.add(assembly)
    db.session.commit()
    return assembly


def _estimate(project, number, organization_id=None):
    return create_estimate(
        project_id=project.id,
        estimate_number=number,
        title=f"{number} title",
        organization_id=organization_id or project.organization_id,
    )


def test_same_org_change_order_still_succeeds(app):
    project = _project(ORG_A, "Same Org Job")
    co = create_change_order(project=project, title="Same-org CO")
    assert co.project_id == project.id
    assert co.project.organization_id == ORG_A
    item = add_change_order_item(
        co, description="Plate", quantity=1, unit="ea", unit_price="10"
    )
    assert item.change_order_id == co.id
    assert ChangeOrder.query.count() == 1


def test_foreign_org_project_object_cannot_create_change_order(app, org_b):
    actor_project = _project(ORG_A, "Actor Job")
    foreign = _project(ORG_B, "Foreign Job")
    before = ChangeOrder.query.count()
    with pytest.raises(ChangeOrderServiceError, match="Project not found"):
        create_change_order(project=foreign, title="Cross-org CO")
    assert ChangeOrder.query.count() == before
    assert ChangeOrderItem.query.count() == 0
    db.session.refresh(foreign)
    assert foreign.name == "Foreign Job"
    assert actor_project.change_orders == []


def test_foreign_org_project_id_cannot_create_change_order(app, org_b):
    foreign = _project(ORG_B, "Foreign Id Job")
    with pytest.raises(ChangeOrderServiceError, match="Project not found"):
        create_change_order(project=foreign.id, title="Id CO")
    assert ChangeOrder.query.filter_by(project_id=foreign.id).count() == 0


def test_foreign_estimate_version_on_same_org_project_fails(app, org_b):
    project_a = _project(ORG_A, "A Job")
    project_b = _project(ORG_B, "B Job")
    estimate_b = _estimate(project_b, "EST-R01-B", organization_id=ORG_B)
    before = ChangeOrder.query.count()
    with pytest.raises(ChangeOrderServiceError, match="Not found"):
        create_change_order(
            project=project_a,
            title="Poisoned version",
            estimate_version=estimate_b.current_version,
            copy_estimate_lines=True,
        )
    assert ChangeOrder.query.count() == before
    assert ChangeOrderItem.query.count() == 0


def test_authorized_org_a_http_post_cannot_create_org_b_change_order(client, app, org_b):
    ensure_office_user()
    login_office_user(client)
    project_a = _project(ORG_A, "HTTP A Job")
    project_b = _project(ORG_B, "HTTP B Job")
    before = ChangeOrder.query.count()
    response = client.post(
        "/project-controls/change-orders/new",
        data={
            "title": "Stolen CO",
            "project_id": str(project_b.id),
            "status": "Draft",
            "markup_percent": "0",
            "tax_percent": "0",
        },
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Stolen CO" not in html or ChangeOrder.query.filter_by(title="Stolen CO").count() == 0
    assert "Apex" not in html
    assert ChangeOrder.query.filter_by(project_id=project_b.id).count() == 0
    assert ChangeOrder.query.count() == before
    same = client.post(
        "/project-controls/change-orders/new",
        data={
            "title": "Legitimate CO",
            "project_id": str(project_a.id),
            "status": "Draft",
            "markup_percent": "0",
            "tax_percent": "0",
        },
        follow_redirects=False,
    )
    assert same.status_code == 302
    created = ChangeOrder.query.filter_by(title="Legitimate CO").one()
    assert created.project_id == project_a.id


def test_foreign_cost_item_cannot_copy_commercial_identity(app, org_b):
    project_a = _project(ORG_A, "Estimate A")
    estimate_a = _estimate(project_a, "EST-R01-A")
    section = create_section(estimate_a.current_version, name="Carpentry")
    local = _cost_item(ORG_A, "A-LUM", "Local lumber", Decimal("12.00"))
    foreign = _cost_item(ORG_B, "B-LUM", "Secret lumber", Decimal("999.00"))
    ok = add_cost_item_line(section, cost_item_id=local.id, quantity=2)
    assert ok.unit_cost == Decimal("12.00")
    assert ok.code == "A-LUM"
    before = EstimateLineItem.query.count()
    with pytest.raises(Exception) as excinfo:
        add_cost_item_line(section, cost_item_id=foreign.id, quantity=1)
    assert "active cost item" in str(excinfo.value).lower() or "not found" in str(
        excinfo.value
    ).lower()
    assert EstimateLineItem.query.count() == before
    assert EstimateLineItem.query.filter_by(code="B-LUM").count() == 0
    assert EstimateLineItem.query.filter_by(unit_cost=Decimal("999.00")).count() == 0


def test_foreign_assembly_cannot_copy_commercial_identity(app, org_b):
    project_a = _project(ORG_A, "Assembly A")
    estimate_a = _estimate(project_a, "EST-R01-ASM")
    section = create_section(estimate_a.current_version, name="Assemblies")
    foreign = _assembly(ORG_B, "B-ASM", "Secret assembly")
    before = EstimateLineItem.query.count()
    with pytest.raises(Exception) as excinfo:
        add_assembly_line(section, assembly_id=foreign.id, quantity=1)
    assert "active assembly" in str(excinfo.value).lower() or "not found" in str(
        excinfo.value
    ).lower()
    assert EstimateLineItem.query.count() == before
    assert EstimateLineItem.query.filter_by(code="B-ASM").count() == 0


def test_commercial_context_rejects_foreign_project_id(app, org_b):
    foreign = _project(ORG_B, "Context B")
    with pytest.raises(CommercialContextValidationError, match="Project not found"):
        create_initial_commercial_context(project_id=foreign.id, data=COMMERCIAL)
    assert ProjectCommercialContext.query.filter_by(project_id=foreign.id).count() == 0
    home = _project(ORG_A, "Context A")
    create_initial_commercial_context(
        project_id=home.id, data=COMMERCIAL, organization_id=ORG_A
    )
    with pytest.raises(CommercialContextValidationError, match="Project not found"):
        update_commercial_context(project_id=foreign.id, data=COMMERCIAL)
    assert ProjectCommercialContext.query.filter_by(project_id=foreign.id).count() == 0


def test_foreign_proposal_template_cannot_bind_same_org_estimate(app, org_b):
    project_a = _project(ORG_A, "Proposal A")
    estimate_a = _estimate(project_a, "EST-R01-P")
    template_b = create_proposal_template(
        name="Apex Template",
        organization_id=ORG_B,
        is_active=True,
    )
    with pytest.raises(ProposalServiceError, match="Not found"):
        create_proposal(
            estimate=estimate_a,
            version=estimate_a.current_version,
            template=template_b,
        )


def test_punch_and_walkthrough_reject_foreign_project_object(app, org_b):
    owner = ensure_office_user()
    foreign = _project(ORG_B, "Punch B")
    with pytest.raises(PunchListNotFoundError, match="Project not found"):
        create_punch_list_item(
            foreign,
            owner,
            description="Cross-org punch",
            work_source_type="OTHER",
        )
    with pytest.raises(WalkthroughNotFoundError, match="Project not found"):
        create_walkthrough_invitation(foreign, owner)
    with pytest.raises(ProjectLifecycleError, match="Project not found"):
        close_project(foreign, owner)


def test_require_organization_project_does_not_trust_object_org_id(app, org_b):
    foreign = _project(ORG_B, "Stale Object")
    with pytest.raises(Exception):
        require_organization_project(foreign, organization_id=ORG_A)
    loaded = require_organization_project(foreign, organization_id=ORG_B)
    assert loaded.id == foreign.id
    assert loaded.organization_id == ORG_B
