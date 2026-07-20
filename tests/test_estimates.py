from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, Estimate, EstimateVersion, Project
from app.services import (
    EstimateServiceError,
    clone_current_version,
    create_estimate,
    set_current_version,
    set_version_status,
    suggest_next_estimate_number,
    update_estimate_version,
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
    client = Client(name="Acme Builders")
    db.session.add(client)
    db.session.flush()
    project = Project(
        name="Downtown Renovation",
        client_id=client.id,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def test_create_estimate_creates_version_one_as_current(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0001",
        title="Base Estimate",
    )

    assert estimate.current_version_id is not None
    assert len(estimate.versions) == 1

    version = estimate.current_version
    assert version.version_number == 1
    assert version.version_label == "Initial Estimate"
    assert version.status == "Draft"
    assert version.is_locked is False
    assert estimate.current_version_id == version.id


def test_duplicate_estimate_number_rejected(client, project):
    create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0001",
        title="First",
    )

    response = client.post(
        "/estimates/new",
        data={
            "project_id": str(project.id),
            "estimate_number": "EST-2026-0001",
            "title": "Duplicate Title",
            "status": "Draft",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"already exists" in response.data
    assert b"Duplicate Title" in response.data
    assert Estimate.query.count() == 1


def test_suggested_estimate_number_increments(project):
    year = datetime.utcnow().year
    assert suggest_next_estimate_number(year=year) == f"EST-{year}-0001"

    create_estimate(
        project_id=project.id,
        estimate_number=f"EST-{year}-0001",
        title="One",
    )
    create_estimate(
        project_id=project.id,
        estimate_number=f"EST-{year}-0003",
        title="Three",
    )

    assert suggest_next_estimate_number(year=year) == f"EST-{year}-0004"


def test_new_version_clones_values_and_becomes_current(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0100",
        title="Clone Test",
    )
    v1 = estimate.current_version
    update_estimate_version(
        v1,
        subtotal=Decimal("1000.00"),
        overhead_percent=Decimal("10.00"),
        profit_percent=Decimal("15.00"),
        tax_percent=Decimal("5.00"),
        total=Decimal("1265.00"),
    )

    v1_id = v1.id
    v1_total = v1.total

    v2 = clone_current_version(
        estimate,
        version_label="Issued for Tender",
        revision_reason="Client request",
    )

    assert v2.version_number == 2
    assert v2.version_label == "Issued for Tender"
    assert v2.revision_reason == "Client request"
    assert v2.subtotal == Decimal("1000.00")
    assert v2.overhead_percent == Decimal("10.00")
    assert v2.profit_percent == Decimal("15.00")
    assert v2.tax_percent == Decimal("5.00")
    assert v2.total == Decimal("1265.00")
    assert v2.status == "Draft"
    assert v2.is_locked is False

    earlier = db.session.get(EstimateVersion, v1_id)
    assert earlier.total == v1_total
    assert earlier.version_label == "Initial Estimate"
    assert earlier.version_number == 1

    estimate = db.session.get(Estimate, estimate.id)
    assert estimate.current_version_id == v2.id


def test_set_current_version(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0200",
        title="Current Switch",
    )
    v1 = estimate.current_version
    v2 = clone_current_version(estimate, version_label="Revision 2")

    assert estimate.current_version_id == v2.id

    set_current_version(estimate, v1)
    assert estimate.current_version_id == v1.id


def test_locked_version_cannot_be_edited(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0300",
        title="Lock Test",
    )
    version = estimate.current_version
    version.is_locked = True
    db.session.commit()

    with pytest.raises(EstimateServiceError, match="locked"):
        update_estimate_version(version, total=Decimal("500.00"))


def test_issued_version_locks_automatically(project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0400",
        title="Issue Test",
    )
    version = estimate.current_version

    set_version_status(version, "Issued")

    assert version.status == "Issued"
    assert version.is_locked is True


def test_version_from_other_estimate_cannot_be_accessed(client, project):
    first = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0500",
        title="First",
    )
    second = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0501",
        title="Second",
    )
    foreign_version = first.current_version

    response = client.get(
        f"/estimates/{second.id}/versions/{foreign_version.id}"
    )
    assert response.status_code == 404

    response = client.post(
        f"/estimates/{second.id}/versions/{foreign_version.id}/set-current",
        follow_redirects=True,
    )
    assert response.status_code == 404

    response = client.post(
        f"/estimates/{second.id}/versions/{foreign_version.id}/lock",
        follow_redirects=True,
    )
    assert response.status_code == 404


def test_estimate_list_and_detail_render(client, project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0600",
        title="Render Test",
    )

    list_response = client.get("/estimates/")
    assert list_response.status_code == 200
    assert b"EST-2026-0600" in list_response.data
    assert b"Render Test" in list_response.data
    assert b"Downtown Renovation" in list_response.data
    assert b"Acme Builders" in list_response.data
    assert b"Initial Estimate" in list_response.data

    detail_response = client.get(f"/estimates/{estimate.id}")
    assert detail_response.status_code == 200
    assert b"Current Version" in detail_response.data
    assert b"v1" in detail_response.data
    assert b"Initial Estimate" in detail_response.data
    assert b"Create New Version" in detail_response.data
    assert b"Edit Estimate" in detail_response.data


def test_create_version_via_route(client, project):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-0700",
        title="Route Clone",
    )
    update_estimate_version(
        estimate.current_version,
        total=Decimal("250.00"),
    )

    response = client.post(
        f"/estimates/{estimate.id}/versions/new",
        data={
            "version_label": "Client Revision",
            "revision_reason": "Scope change",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"v2" in response.data
    assert b"Client Revision" in response.data
    assert EstimateVersion.query.filter_by(estimate_id=estimate.id).count() == 2
    assert estimate.current_version.version_number == 2
