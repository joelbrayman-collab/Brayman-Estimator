"""Project-owned construction-model revisions and the estimate office handoff.

The office offers one stored member group into the existing calculation
review. Confirmation still creates the ordinary estimate line.
"""

from __future__ import annotations

import copy
import inspect
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, CostItem, EstimateLineItem, Organization, Project
from app.models.calculation_estimate_mapping import (
    CalculationQuantityReview,
    CalculationResultIntake,
)
from app.models.project_construction_model import ProjectConstructionModelRevision
from app.services.calculation_estimate_mapping import confirm_quantity_mapping
from app.services.construction_model.views import read_stored_member_quantities
from app.services.deck_framing_handoff import (
    StoredMemberCountError,
    offer_stored_member_count,
    stored_member_count_result_id,
)
from app.services.estimate_builder import create_section
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_construction_model import (
    ProjectConstructionModelError,
    canonical_content,
    load_current_revision,
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
            "SECRET_KEY": "test-secret-construction-model",
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


def _project(name="Stored Model", organization_id=DEFAULT_ORGANIZATION_ID):
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


def _save(project, content=None, source_reference="office-test"):
    return save_construction_model_revision(
        organization_id=project.organization_id,
        project_id=project.id,
        content=deck_model() if content is None else content,
        source_kind="project_input",
        source_reference=source_reference,
        actor_display_name="Path Contractor",
    )


def _joist(content):
    return next(
        row for row in read_stored_member_quantities(copy.deepcopy(content)) if row["role"] == "joist"
    )


def _without_length(model, member_id):
    changed = copy.deepcopy(model)
    member = next(item for item in changed["members"] if item["id"] == member_id)
    member.pop("geometry", None)
    member.pop("length", None)
    changed["relationships"] = [
        item
        for item in changed["relationships"]
        if item.get("from_id") != member_id and item.get("to_id") != member_id
    ]
    for chain in changed["dimension_chains"]:
        chain["references"] = [item for item in chain["references"] if item != member_id]
    changed["connections"] = [
        item
        for item in changed["connections"]
        if member_id not in (item.get("participant_ids") or [])
    ]
    return changed


def test_a_project_revision_keeps_its_content_and_hash(app):
    with app.app_context():
        project = _project()
        first = _save(project, source_reference="deck fixture")
        parsed, digest = canonical_content(deck_model())
        assert first.revision_number == 1
        assert first.organization_id == project.organization_id
        assert first.project_id == project.id
        assert first.content_json == parsed
        assert first.content_sha256 == digest
        assert first.source_kind == "project_input"
        assert first.source_reference == "deck fixture"
        assert first.actor_display_name == "Path Contractor"
        stored = copy.deepcopy(first.content_json)
        stored_hash = first.content_sha256
        changed = copy.deepcopy(deck_model())
        changed["office_note"] = "revision-two"
        second = _save(project, content=changed, source_reference="revision-two")
        assert second.revision_number == 2
        assert second.content_sha256 != stored_hash
        current = load_current_revision(
            organization_id=project.organization_id,
            project_id=project.id,
        )
        assert current.id == second.id
        earlier = load_revision(
            organization_id=project.organization_id,
            project_id=project.id,
            revision_id=first.id,
        )
        assert earlier.revision_number == 1
        assert earlier.content_json == stored
        assert earlier.content_sha256 == stored_hash
        assert "office_note" not in earlier.content_json
        service_source = inspect.getsource(save_construction_model_revision)
        assert "deck_model" not in service_source
        assert "complete_deck_fixture" not in service_source


def test_a_revision_cannot_be_changed(app):
    with app.app_context():
        project = _project("Immutable")
        row = _save(project)
        original = row.content_sha256
        row.actor_display_name = "Someone else"
        with pytest.raises(ValueError, match="cannot be changed"):
            db.session.commit()
        db.session.rollback()
        again = ProjectConstructionModelRevision.query.get(row.id)
        assert again.content_sha256 == original
        assert again.actor_display_name == "Path Contractor"


def test_cross_project_and_cross_organization_access_is_rejected(app):
    with app.app_context():
        owned = _project("Owned")
        other = _project("Other project")
        row = _save(owned)
        with pytest.raises(ProjectConstructionModelError, match="not on this project"):
            load_revision(
                organization_id=owned.organization_id,
                project_id=other.id,
                revision_id=row.id,
            )
        assert (
            load_current_revision(
                organization_id=other.organization_id,
                project_id=other.id,
            )
            is None
        )
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
        with pytest.raises(ProjectConstructionModelError, match="not in this organization"):
            load_revision(
                organization_id=DEFAULT_ORGANIZATION_ID,
                project_id=outsider.id,
                revision_id=row.id,
            )
        with pytest.raises(ProjectConstructionModelError, match="not in this organization"):
            save_construction_model_revision(
                organization_id=DEFAULT_ORGANIZATION_ID,
                project_id=outsider.id,
                content=deck_model(),
                source_kind="project_input",
                source_reference="wrong organization",
                actor_display_name="Path Contractor",
            )


def test_malformed_content_and_a_missing_source_are_rejected(app):
    with app.app_context():
        project = _project("Malformed")
        with pytest.raises(ProjectConstructionModelError, match="required"):
            _save(project, content="not a model")
        for content in ({"structure_class": "house"}, {"members": []}):
            with pytest.raises(ProjectConstructionModelError, match="cannot be stored"):
                _save(project, content=content)
        with pytest.raises(ProjectConstructionModelError, match="source is not recorded"):
            save_construction_model_revision(
                organization_id=project.organization_id,
                project_id=project.id,
                content=deck_model(),
                source_kind="invented_source",
                source_reference="no",
                actor_display_name="Path Contractor",
            )
        assert ProjectConstructionModelRevision.query.count() == 0


def test_dict_offer_without_a_revision_keeps_the_original_identity(app):
    with app.app_context():
        project = _project("Dict offer")
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="MEM-DICT",
            title="Dict offer",
            organization_id=project.organization_id,
        )
        model = deck_model()
        group = _joist(model)
        intake = offer_stored_member_count(
            organization_id=project.organization_id,
            estimate_version_id=estimate.current_version_id,
            model=model,
            member_ids=group["member_ids"],
            actor="Path Contractor",
        )
        assert intake.construction_model_revision_id is None
        assert intake.result_id == stored_member_count_result_id(group)
        assert intake.frozen_result["contract_version"] == "1"
        assert "construction_model_revision_id" not in intake.frozen_result
        assert EstimateLineItem.query.count() == 0


def test_office_offers_one_group_and_confirmation_creates_one_line(client, app):
    with app.app_context():
        project = _project("Office handoff")
        revision = _save(project)
        group = _joist(revision.content_json)
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="MEM-OFFICE",
            title="Office handoff",
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
        revision_id = revision.id
        revision_number = revision.revision_number
        quantity = group["quantity"]
        role = group["role"]
        size = group["member_size"]
        member_ids = list(group["member_ids"])

    page = client.get(f"/estimates/{estimate_id}/versions/{version_id}/calculations")
    assert page.status_code == 200
    assert f"Model revision {revision_number}".encode() in page.data
    assert role.encode() in page.data
    assert size.encode() in page.data
    assert str(quantity).encode() in page.data
    assert b"Missing facts" in page.data
    assert b"Offer this count" in page.data
    assert b"ICF wall quantities" in page.data

    offered = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/stored-member-count",
        data={"revision_id": revision_id, "member_ids": member_ids},
        follow_redirects=False,
    )
    assert offered.status_code == 302
    with app.app_context():
        assert EstimateLineItem.query.count() == 0
        intake = CalculationResultIntake.query.one()
        assert intake.construction_model_revision_id == revision_id
        assert intake.frozen_result["contract_version"] == "1"
        assert intake.frozen_result["quantities"][0]["quantity"] == str(quantity)
        review = intake.reviews[0]
        assert review.status == "open"
        review_id = review.id
        intake_id = intake.id
        quantity_text = review.quantity_text
        assert offered.location.endswith(f"/calculations/{intake_id}")

    repeated = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/stored-member-count",
        data={"revision_id": revision_id, "member_ids": member_ids},
        follow_redirects=False,
    )
    assert repeated.status_code == 302
    assert repeated.location.endswith(f"/calculations/{intake_id}")
    with app.app_context():
        assert CalculationResultIntake.query.count() == 1
        assert EstimateLineItem.query.count() == 0

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
    with app.app_context():
        lines = EstimateLineItem.query.all()
        assert len(lines) == 1
        assert Decimal(lines[0].quantity) == Decimal(quantity)
        assert lines[0].unit == "ea"
        assert lines[0].id
        line_id = lines[0].id
        line_quantity = lines[0].quantity

    again = client.post(
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
    assert again.status_code == 200
    assert b"already on the estimate" in again.data
    with app.app_context():
        assert EstimateLineItem.query.count() == 1
        with pytest.raises(Exception, match="already on the estimate"):
            confirm_quantity_mapping(
                organization_id=DEFAULT_ORGANIZATION_ID,
                review_id=review_id,
                section_id=section_id,
                target_kind="cost_item",
                target_id=str(item_id),
                actor="Path Contractor",
                confirmed_quantity=quantity_text,
            )
        kept = EstimateLineItem.query.get(line_id)
        assert kept.quantity == line_quantity

        project = Project.query.filter_by(name="Office handoff").one()
        first = ProjectConstructionModelRevision.query.get(revision_id)
        first_hash = first.content_sha256
        first_content = copy.deepcopy(first.content_json)
        later = copy.deepcopy(deck_model())
        later["office_note"] = "after confirmation"
        second = _save(project, content=later, source_reference="after confirmation")
        assert load_revision(
            organization_id=project.organization_id,
            project_id=project.id,
            revision_id=revision_id,
        ).content_sha256 == first_hash
        assert first_content == ProjectConstructionModelRevision.query.get(revision_id).content_json
        later_group = _joist(second.content_json)
        second_intake = offer_stored_member_count(
            organization_id=project.organization_id,
            estimate_version_id=version_id,
            model=copy.deepcopy(second.content_json),
            member_ids=later_group["member_ids"],
            actor="Path Contractor",
            construction_model_revision_id=second.id,
        )
        assert second_intake.id != intake_id
        assert second_intake.construction_model_revision_id == second.id
        assert CalculationResultIntake.query.count() == 2
        assert EstimateLineItem.query.count() == 1
        assert EstimateLineItem.query.get(line_id).quantity == line_quantity
        assert CalculationQuantityReview.query.get(review_id).estimate_line_item_id == line_id


def test_missing_groups_and_missing_facts_fail_closed(client, app):
    with app.app_context():
        bare = _project("No model")
        bare_estimate = create_estimate(
            project_id=bare.id,
            estimate_number="MEM-NONE",
            title="No model",
            organization_id=bare.organization_id,
        )
        bare_estimate_id = bare_estimate.id
        bare_version_id = bare_estimate.current_version_id
        project = _project("Missing fact")
        model = deck_model()
        complete = _joist(model)
        incomplete = _without_length(model, complete["member_ids"][-1])
        missing = next(
            row
            for row in read_stored_member_quantities(copy.deepcopy(incomplete))
            if row["missing_fact"] == "MISSING_SCHEDULE_FACT"
        )
        revision = _save(project, content=incomplete, source_reference="missing length")
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="MEM-MISS",
            title="Missing fact",
            organization_id=project.organization_id,
        )
        estimate_id = estimate.id
        version_id = estimate.current_version_id
        revision_id = revision.id
        missing_ids = list(missing["member_ids"])

    empty = client.get(
        f"/estimates/{bare_estimate_id}/versions/{bare_version_id}/calculations"
    )
    assert empty.status_code == 200
    assert b"No construction model is stored for this project." in empty.data

    page = client.get(f"/estimates/{estimate_id}/versions/{version_id}/calculations")
    assert page.status_code == 200
    assert b"MISSING_SCHEDULE_FACT" in page.data
    offered_missing = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/stored-member-count",
        data={"revision_id": revision_id, "member_ids": missing_ids},
        follow_redirects=True,
    )
    assert offered_missing.status_code == 200
    assert b"missing" in offered_missing.data.lower()
    unknown = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/stored-member-count",
        data={"revision_id": revision_id, "member_ids": ["not-a-member"]},
        follow_redirects=True,
    )
    assert unknown.status_code == 200
    assert b"not found" in unknown.data.lower()
    with app.app_context():
        assert CalculationResultIntake.query.count() == 0
        assert EstimateLineItem.query.count() == 0
        with pytest.raises(StoredMemberCountError, match="missing"):
            offer_stored_member_count(
                organization_id=DEFAULT_ORGANIZATION_ID,
                estimate_version_id=version_id,
                model=copy.deepcopy(
                    ProjectConstructionModelRevision.query.get(revision_id).content_json
                ),
                member_ids=tuple(missing_ids),
                actor="Path Contractor",
                construction_model_revision_id=revision_id,
            )
        assert CalculationResultIntake.query.count() == 0
