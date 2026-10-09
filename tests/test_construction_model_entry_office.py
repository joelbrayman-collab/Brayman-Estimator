"""A contractor saves deck construction information from the project page.

The office form uses the existing revision save. Confirmation still uses
the existing calculation review.
"""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, EstimateLineItem, Organization, Project
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.project_construction_model import ProjectConstructionModelRevision
from app.services.construction_model.views import read_stored_member_quantities
from app.services.construction_model_entry import OFFICE_REFERENCE
from app.services.estimate_builder import create_section
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_construction_model import (
    load_revision,
    save_construction_model_revision,
)
from tests.fixtures.construction_model.complete_deck_fixture import deck_model


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-construction-entry",
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


def _project(name="Office deck", organization_id=DEFAULT_ORGANIZATION_ID):
    row = Client(name=name + " Client", organization_id=organization_id)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=row.id,
        organization_id=organization_id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _entry(**overrides):
    form = {
        "project_document_status": "preliminary_construction_drawing",
        "measurement_system": "imperial",
        "level_id": "level-1",
        "level_name": "Deck",
        "level_elevation": "0",
        "member_role_0": "joist",
        "member_size_0": "2x8",
        "member_length_0": "12",
        "member_length_unit_0": "ft",
        "member_count_0": "8",
        "member_role_1": "beam",
        "member_size_1": "2x10",
        "member_length_1": "",
        "member_length_unit_1": "",
        "member_count_1": "2",
        "support_kind_0": "pier",
        "support_count_0": "4",
    }
    form.update(overrides)
    return form


def test_contractor_can_open_the_entry_page_and_save_revision_one(client, app):
    with app.app_context():
        project = _project()
        project_id = project.id
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="DECK-1",
            title="Deck estimate",
            organization_id=project.organization_id,
        )
        estimate_id = estimate.id
        version_id = estimate.current_version_id

    hub = client.get(f"/projects/{project_id}")
    assert hub.status_code == 200
    assert b"Enter construction information" in hub.data

    page = client.get(f"/projects/{project_id}/construction")
    assert page.status_code == 200
    assert b"Enter construction information" in page.data
    assert b"Member role" in page.data
    assert b"Missing facts" in page.data

    saved = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(),
        follow_redirects=True,
    )
    assert saved.status_code == 200
    assert b"Update construction information" in saved.data
    assert b"Model revision 1" in saved.data
    assert b"joist" in saved.data
    assert b"2x8" in saved.data
    assert b"beam" in saved.data
    assert b"MISSING_SCHEDULE_FACT" in saved.data
    assert f"Add from calculation — DECK-1".encode() in saved.data
    with app.app_context():
        row = ProjectConstructionModelRevision.query.one()
        assert row.revision_number == 1
        assert row.project_id == project_id
        assert row.organization_id == DEFAULT_ORGANIZATION_ID
        assert row.source_kind == "project_input"
        assert row.source_reference == OFFICE_REFERENCE
        assert row.actor_display_name == "Office Test User"
        assert row.content_sha256
        assert row.created_at is not None
        assert EstimateLineItem.query.count() == 0
        reopened = client.get(f"/projects/{project_id}/construction")
    assert b'value="Deck"' in reopened.data
    assert b'value="12"' in reopened.data
    assert b'value="8"' in reopened.data

    listed = client.get(f"/estimates/{estimate_id}/versions/{version_id}/calculations")
    assert listed.status_code == 200
    assert b"joist" in listed.data
    assert b"2x8" in listed.data
    assert b"8" in listed.data
    assert b"MISSING_SCHEDULE_FACT" in listed.data
    assert listed.data.count(b"Offer this count") == 1


def test_a_later_save_creates_revision_two_and_leaves_revision_one(client, app):
    with app.app_context():
        project = _project("Second revision")
        project_id = project.id
    client.post(f"/projects/{project_id}/construction", data=_entry(), follow_redirects=True)
    with app.app_context():
        first = ProjectConstructionModelRevision.query.one()
        first_id = first.id
        first_hash = first.content_sha256
        first_content = copy.deepcopy(first.content_json)
    changed = _entry(member_count_0="9")
    second = client.post(
        f"/projects/{project_id}/construction",
        data=changed,
        follow_redirects=True,
    )
    assert second.status_code == 200
    assert b"Model revision 2" in second.data
    with app.app_context():
        assert ProjectConstructionModelRevision.query.count() == 2
        kept = load_revision(
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=project_id,
            revision_id=first_id,
        )
        assert kept.revision_number == 1
        assert kept.content_sha256 == first_hash
        assert kept.content_json == first_content
        current = ProjectConstructionModelRevision.query.filter_by(revision_number=2).one()
        assert current.content_sha256 != first_hash
        joists = [
            item for item in current.content_json["members"] if item["role"] == "joist"
        ]
        assert len(joists) == 9


def test_invalid_input_and_another_organization_do_not_save(client, app):
    with app.app_context():
        project = _project("Invalid entry")
        project_id = project.id
        db.session.add(
            Organization(
                id="ORG-OTHER",
                legal_name="Other Construction",
                display_name="Other Construction",
                currency="CAD",
                is_active=True,
            )
        )
        db.session.commit()
        outsider = _project("Outsider", organization_id="ORG-OTHER")
        outsider_id = outsider.id

    refused = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(
            member_role_0="",
            member_size_0="",
            member_length_0="",
            member_length_unit_0="",
            member_count_0="",
            member_role_1="",
            member_size_1="",
            member_length_1="",
            member_count_1="",
        ),
        follow_redirects=False,
    )
    assert refused.status_code == 400
    assert b"was not saved" in refused.data
    assert b"at least one member" in refused.data.lower() or b"Enter at least one member." in refused.data
    with app.app_context():
        assert ProjectConstructionModelRevision.query.count() == 0

    blocked = client.get(f"/projects/{outsider_id}/construction")
    assert blocked.status_code == 404
    with app.app_context():
        save_construction_model_revision(
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=project_id,
            content=deck_model(),
            source_kind="instance_configuration",
            source_reference="fixture",
            actor_display_name="Path Contractor",
        )
        before = ProjectConstructionModelRevision.query.one().content_sha256
    held = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(),
        follow_redirects=False,
    )
    assert held.status_code == 400
    assert b"does not change" in held.data
    with app.app_context():
        assert ProjectConstructionModelRevision.query.count() == 1
        assert ProjectConstructionModelRevision.query.one().content_sha256 == before


def test_confirmation_creates_one_line_and_a_later_revision_leaves_it(client, app):
    with app.app_context():
        project = _project("Confirmed line")
        project_id = project.id
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="DECK-LINE",
            title="Deck line",
            organization_id=project.organization_id,
        )
        version = estimate.current_version
        section = create_section(version, name="Framing")
        item = CostItem(
            organization_id=DEFAULT_ORGANIZATION_ID,
            code="JOIST-EA",
            name="Joist member",
            category="Material",
            unit="ea",
            unit_cost=Decimal("12.00"),
            default_markup_percent=Decimal("0"),
            is_active=True,
        )
        db.session.add(item)
        db.session.commit()
        estimate_id = estimate.id
        version_id = version.id
        section_id = section.id
        item_id = item.id

    client.post(f"/projects/{project_id}/construction", data=_entry(), follow_redirects=True)
    with app.app_context():
        revision = ProjectConstructionModelRevision.query.one()
        group = next(
            row
            for row in read_stored_member_quantities(copy.deepcopy(revision.content_json))
            if row["role"] == "joist"
        )
        assert group["quantity"] == 8
        assert group["missing_fact"] == ""
        missing = next(
            row
            for row in read_stored_member_quantities(copy.deepcopy(revision.content_json))
            if row["missing_fact"] == "MISSING_SCHEDULE_FACT"
        )
        revision_id = revision.id
        member_ids = list(group["member_ids"])
        missing_ids = list(missing["member_ids"])

    missing_offer = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/stored-member-count",
        data={"revision_id": revision_id, "member_ids": missing_ids},
        follow_redirects=True,
    )
    assert b"missing" in missing_offer.data.lower()
    with app.app_context():
        assert CalculationResultIntake.query.count() == 0
        assert EstimateLineItem.query.count() == 0

    offered = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/stored-member-count",
        data={"revision_id": revision_id, "member_ids": member_ids},
        follow_redirects=False,
    )
    assert offered.status_code == 302
    with app.app_context():
        assert EstimateLineItem.query.count() == 0
        intake = CalculationResultIntake.query.one()
        review = intake.reviews[0]
        review_id = review.id
        intake_id = intake.id
        quantity_text = review.quantity_text

    confirmed = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/quantities/{review_id}/confirm",
        data={
            "section_id": section_id,
            "target": f"cost_item:{item_id}",
            "confirmed_quantity": quantity_text,
            "intake_id": intake_id,
            "actor": "Path Contractor",
        },
        follow_redirects=False,
    )
    assert confirmed.status_code == 302
    repeated = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/quantities/{review_id}/confirm",
        data={
            "section_id": section_id,
            "target": f"cost_item:{item_id}",
            "confirmed_quantity": quantity_text,
            "intake_id": intake_id,
            "actor": "Path Contractor",
        },
        follow_redirects=True,
    )
    assert b"already on the estimate" in repeated.data
    with app.app_context():
        lines = EstimateLineItem.query.all()
        assert len(lines) == 1
        assert Decimal(lines[0].quantity) == Decimal("8")
        line_id = lines[0].id
        line_quantity = lines[0].quantity

    client.post(
        f"/projects/{project_id}/construction",
        data=_entry(member_count_1="3"),
        follow_redirects=True,
    )
    with app.app_context():
        assert ProjectConstructionModelRevision.query.count() == 2
        kept = EstimateLineItem.query.get(line_id)
        assert kept.quantity == line_quantity
        assert EstimateLineItem.query.count() == 1
