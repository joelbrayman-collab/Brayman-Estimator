"""One rectangular footing on the existing construction page.

The prism and the cubic-metre conversion stay unchanged. The page does
not write an estimate line.
"""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, EstimateLineItem, Organization, Project
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.material_requirement import MaterialRequirement
from app.models.project_construction_model import ProjectConstructionModelRevision
from app.services.construction_measurement import rectangular_prism_cubic_yards
from app.services.construction_model_entry import rectangular_footing_volume
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_construction_model import (
    ProjectConstructionModelError,
    load_revision,
)
from app.services.unit_conversion import convert


YARDS = Decimal(40) / Decimal(27)
METRES = (Decimal(40) * (Decimal("0.9144") ** 3)) / Decimal(27)


def _exact(quantity):
    text = format(quantity, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-rectangular-footing",
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


def _project(name="Footing deck", organization_id=DEFAULT_ORGANIZATION_ID):
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
        "level_elevation": "",
        "member_role_0": "joist",
        "member_size_0": "2x8",
        "member_length_0": "12",
        "member_length_unit_0": "ft",
        "member_count_0": "8",
        "support_kind_0": "pier",
        "support_count_0": "4",
        "footing_length_ft": "20",
        "footing_width_ft": "2",
        "footing_thickness_in": "12",
    }
    form.update(overrides)
    return form


def _footing(content):
    return next(
        support
        for support in content["supports"]
        if support.get("kind") == "footing" and "length_ft" in support
    )


def test_a_saved_footing_reopens_with_the_same_dimensions_and_both_units(client, app):
    with app.app_context():
        project = _project()
        project_id = project.id
    saved = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(),
        follow_redirects=True,
    )
    assert saved.status_code == 200
    assert b"Model revision 1" in saved.data
    assert f"Construction volume {_exact(YARDS)} yd3".encode() in saved.data
    assert f"Supplier quantity {_exact(METRES)} m3".encode() in saved.data
    assert b"cubic feet to cubic yards" in saved.data
    assert b"cubic yards to cubic metres" in saved.data
    assert b"No waste is added" in saved.data
    assert b"No truck count is calculated" in saved.data
    assert b"not on an estimate" in saved.data
    with app.app_context():
        row = ProjectConstructionModelRevision.query.one()
        footing = _footing(row.content_json)
        footing_id = footing["id"]
        assert footing["length_ft"] == "20"
        assert footing["width_ft"] == "2"
        assert footing["thickness_in"] == "12"
        measured = rectangular_prism_cubic_yards("20", "2", "12")
        shown = rectangular_footing_volume(row.content_json)
        assert measured["cubic_yards"] == YARDS
        assert shown["cubic_yards"] == measured["cubic_yards"]
        assert shown["cubic_feet"] == Decimal(40)
        assert shown["cubic_metres"] == METRES
        assert shown["cubic_metres"] == convert(measured["cubic_yards"], "YD3", "M3")["quantity"]
        assert shown["cubic_metres"] != convert(Decimal("1.481"), "YD3", "M3")["quantity"]
        assert shown["waste"] is None
        assert shown["truck_count"] is None
        assert EstimateLineItem.query.count() == 0
        assert CalculationResultIntake.query.count() == 0
        assert MaterialRequirement.query.count() == 0
        joists = [member for member in row.content_json["members"] if member["role"] == "joist"]
        piers = [support for support in row.content_json["supports"] if support["kind"] == "pier"]
        assert len(joists) == 8
        assert len(piers) == 4
    reopened = client.get(f"/projects/{project_id}/construction")
    assert f'value="{footing_id}"'.encode() in reopened.data
    assert b'name="footing_length_ft" inputmode="decimal" value="20"' in reopened.data
    assert b'value="2"' in reopened.data
    assert b'value="12"' in reopened.data


def test_revision_two_leaves_revision_one_unchanged(client, app):
    with app.app_context():
        project = _project("Revision footing")
        project_id = project.id
    client.post(f"/projects/{project_id}/construction", data=_entry(), follow_redirects=True)
    with app.app_context():
        first = ProjectConstructionModelRevision.query.one()
        first_id = first.id
        first_hash = first.content_sha256
        first_content = copy.deepcopy(first.content_json)
        footing_id = _footing(first.content_json)["id"]
    second = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(footing_id=footing_id, footing_thickness_in="8"),
        follow_redirects=True,
    )
    assert b"Model revision 2" in second.data
    with app.app_context():
        kept = load_revision(
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=project_id,
            revision_id=first_id,
        )
        assert kept.content_sha256 == first_hash
        assert kept.content_json == first_content
        assert _footing(kept.content_json)["thickness_in"] == "12"
        current = ProjectConstructionModelRevision.query.filter_by(revision_number=2).one()
        assert _footing(current.content_json)["id"] == footing_id
        assert _footing(current.content_json)["thickness_in"] == "8"
        other = _project("Other footing project")
        with pytest.raises(ProjectConstructionModelError):
            load_revision(
                organization_id=other.organization_id,
                project_id=other.id,
                revision_id=first_id,
            )


def test_missing_and_invalid_dimensions_are_refused(client, app):
    with app.app_context():
        project = _project("Refused footing")
        project_id = project.id
    missing = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(footing_thickness_in=""),
        follow_redirects=True,
    )
    assert b"Enter the footing thickness in inches." in missing.data
    assert b"Model revision" not in missing.data
    invalid = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(footing_length_ft="abc"),
        follow_redirects=True,
    )
    assert b"number greater than zero" in invalid.data
    zero = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(footing_width_ft="0"),
        follow_redirects=True,
    )
    assert b"number greater than zero" in zero.data
    negative = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(footing_thickness_in="-1"),
        follow_redirects=True,
    )
    assert b"number greater than zero" in negative.data
    metric = client.post(
        f"/projects/{project_id}/construction",
        data=_entry(
            measurement_system="metric",
            member_length_unit_0="m",
        ),
        follow_redirects=True,
    )
    assert b"entered in feet and inches" in metric.data
    with app.app_context():
        assert ProjectConstructionModelRevision.query.count() == 0
        assert EstimateLineItem.query.count() == 0


def test_a_missing_stored_measure_does_not_calculate(app):
    with app.app_context():
        content = {
            "supports": [
                {
                    "id": "footing-abcdef12",
                    "kind": "footing",
                    "length_ft": "20",
                    "width_ft": "2",
                }
            ]
        }
        result = rectangular_footing_volume(content)
        assert result["cubic_yards"] is None
        assert result["cubic_metres"] is None
        assert "footing thickness in inches" in result["missing"]


def test_another_organization_cannot_load_the_footing_revision(client, app):
    with app.app_context():
        project = _project("Owned footing")
        project_id = project.id
    client.post(f"/projects/{project_id}/construction", data=_entry(), follow_redirects=True)
    with app.app_context():
        revision_id = ProjectConstructionModelRevision.query.one().id
        other_org = Organization(
            id="ORG-OTHER",
            legal_name="Other Construction",
            display_name="Other Construction",
            currency="CAD",
            is_active=True,
        )
        db.session.add(other_org)
        db.session.commit()
        outsider = _project("Outsider footing", organization_id="ORG-OTHER")
        with pytest.raises(ProjectConstructionModelError):
            load_revision(
                organization_id=outsider.organization_id,
                project_id=outsider.id,
                revision_id=revision_id,
            )
