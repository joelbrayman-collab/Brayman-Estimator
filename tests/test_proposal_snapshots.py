from decimal import Decimal

import pytest

from app import create_app, db
from app.models import (
    Client,
    EstimateLineItem,
    EstimateSection,
    Project,
    Proposal,
    ProposalLineItem,
    ProposalSection,
)
from app.services import create_estimate
from app.services.estimate_builder import (
    add_manual_line,
    create_section,
    delete_section,
    update_line_item,
    update_version_pricing,
)
from app.services.proposals import (
    create_proposal,
    create_proposal_template,
    update_proposal_line_item,
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
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def project(app):
    client_row = Client(name="Acme Builders", company="Acme Inc")
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name="Downtown Renovation",
        address="200 Queen St",
        client_id=client_row.id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


@pytest.fixture
def estimate(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-9100",
        title="Snapshot Estimate",
    )
    version = estimate.current_version
    section = create_section(version, name="General Requirements")
    add_manual_line(
        section,
        line_type="Custom",
        description="Mobilization",
        quantity=2,
        unit="ls",
        unit_cost=500,
        markup_percent=10,
    )
    update_version_pricing(
        version,
        overhead_percent=10,
        profit_percent=10,
        tax_percent=5,
    )
    return estimate


@pytest.fixture
def template(app):
    return create_proposal_template(
        name="Snapshot Template",
        is_default=True,
        is_active=True,
    )


def test_snapshot_creation_copies_sections_and_lines(estimate, template):
    version = estimate.current_version
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
    )

    assert len(proposal.sections) == 1
    section = proposal.sections[0]
    assert section.name == "General Requirements"
    assert len(section.line_items) == 1

    line = section.line_items[0]
    assert line.item_type == "Custom"
    assert line.description == "Mobilization"
    assert line.quantity == Decimal("2")
    assert line.source_line_item_id is not None
    assert proposal.overhead_percent == Decimal("10.00")
    assert proposal.subtotal == version.subtotal
    assert proposal.total == version.total


def test_snapshot_independence_from_estimate_edits(estimate, template):
    version = estimate.current_version
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
    )
    original_total = proposal.total
    original_desc = proposal.sections[0].line_items[0].description
    estimate_line = EstimateLineItem.query.first()

    update_line_item(estimate_line, description="Changed Live", quantity=99)
    db.session.refresh(proposal)
    assert proposal.sections[0].line_items[0].description == original_desc
    assert proposal.total == original_total
    assert version.total != original_total or version.subtotal != proposal.subtotal


def test_proposal_line_edit_recalculates_totals(estimate, template):
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
    )
    line = proposal.sections[0].line_items[0]
    estimate_total_before = estimate.current_version.total

    update_proposal_line_item(
        line,
        quantity=4,
        unit_cost=500,
        markup_percent=10,
    )

    # 4 × 500 = 2000 cost; sell = 2000 × 1.10 = 2200
    assert line.extended_cost == Decimal("2000.00")
    assert line.extended_price == Decimal("2200.00")
    assert proposal.sections[0].subtotal == Decimal("2200.00")
    assert proposal.subtotal == Decimal("2200.00")
    # overhead 220, profit 242, tax 133.10, total 2795.10
    assert proposal.overhead_amount == Decimal("220.00")
    assert proposal.profit_amount == Decimal("242.00")
    assert proposal.tax_amount == Decimal("133.10")
    assert proposal.total == Decimal("2795.10")
    assert estimate.current_version.total == estimate_total_before


def test_deleted_estimate_section_does_not_affect_proposal(estimate, template):
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
    )
    section = EstimateSection.query.first()
    delete_section(section)

    assert EstimateSection.query.count() == 0
    assert EstimateLineItem.query.count() == 0
    assert ProposalSection.query.count() == 1
    assert ProposalLineItem.query.count() == 1
    assert proposal.sections[0].line_items[0].description == "Mobilization"


def test_deleted_estimate_version_clears_fk_but_keeps_snapshot(estimate, template):
    version = estimate.current_version
    proposal = create_proposal(
        estimate=estimate,
        version=version,
        template=template,
    )
    proposal_id = proposal.id
    original_total = proposal.total

    proposal.estimate_id = None
    proposal.estimate_version_id = None
    for line in proposal.sections[0].line_items:
        line.source_line_item_id = None
    estimate.current_version_id = None
    db.session.commit()

    db.session.delete(version)
    db.session.commit()

    proposal = db.session.get(Proposal, proposal_id)
    assert proposal is not None
    assert proposal.total == original_total
    assert proposal.sections[0].name == "General Requirements"
    assert proposal.sections[0].line_items[0].extended_price > 0


def test_proposal_detail_renders_snapshot_sections(client, estimate, template):
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
    )
    response = client.get(f"/proposals/{proposal.id}")
    assert response.status_code == 200
    assert b"Snapshot from Estimate Version" in response.data
    assert b"General Requirements" in response.data
    assert b"Mobilization" in response.data
    assert b"Grand Total" in response.data


def test_edit_proposal_line_item_route(client, estimate, template):
    proposal = create_proposal(
        estimate=estimate,
        version=estimate.current_version,
        template=template,
    )
    section = proposal.sections[0]
    item = section.line_items[0]

    response = client.post(
        f"/proposals/{proposal.id}/sections/{section.id}/items/{item.id}/edit",
        data={
            "description": "Mobilization Updated",
            "quantity": "3",
            "unit": "ls",
            "unit_cost": "500",
            "markup_percent": "10",
            "notes": "Adjusted",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Proposal line item updated." in response.data
    assert b"Mobilization Updated" in response.data
    db.session.refresh(item)
    assert item.quantity == Decimal("3")
    assert item.extended_price == Decimal("1650.00")
