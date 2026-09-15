"""FG-035 TAX/WBS work-structure catalog, seed, Hub, and migration tests."""

from __future__ import annotations

import os
import re
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.work_structure import (
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkStructureSeed,
    WorkElementTemplate,
    WorkType,
)
from app.services import create_estimate
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.work_structure import (
    WorkStructureError,
    add_project_activity,
    add_project_element,
    create_org_element_template,
    create_org_work_type,
    deactivate_catalog_row,
    deactivate_project_work_row,
    ensure_baseline_work_catalog,
    rename_project_work_row,
    seed_project_work_structure,
    set_project_work_sort_order,
)
from tests.auth_fixtures import (
    DEFAULT_OFFICE_EMAIL,
    DEFAULT_OFFICE_PASSWORD,
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)


def _csrf_token(response):
    html = response.get_data(as_text=True)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert match, html[:500]
    return match.group(1)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-tax-wbs",
            "WTF_CSRF_ENABLED": False,
        }
    )
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


@pytest.fixture
def org_b(app):
    org = Organization(
        id="ORG-002",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 TAX/WBS Project"):
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


def _task(org_id=DEFAULT_ORGANIZATION_ID, code="LT-FG035-FORM", **kwargs):
    defaults = dict(
        task_code=code,
        canonical_name="Forms",
        production_unit="sq ft",
        unit_of_measure="sqft",
        trade="Concrete",
        category="Foundation",
        organization_id=org_id,
        created_by="Joel Brayman",
    )
    defaults.update(kwargs)
    return create_labour_task(**defaults)


def _snapshot(version, task, quantity="100"):
    return create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal(quantity),
        override_production_rate=Decimal("0.05"),
        override_production_reason="TAX/WBS test",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="TAX/WBS test",
        created_by="Joel Brayman",
        organization_id=version.estimate.project.organization_id,
    )


def _eligible_estimate(project, *, task=None, extra_task=None):
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-FG035",
        title="FG035 TAX/WBS synthetic estimate",
    )
    version = estimate.current_version
    task = task or _task()
    snap = _snapshot(version, task)
    extra = None
    if extra_task is not None:
        extra = _snapshot(version, extra_task, quantity="40")
    set_version_status(version, "Issued")
    db.session.refresh(version)
    return estimate, version, snap, extra


def test_baseline_catalog_visible_and_not_org_owned(app):
    ensure_baseline_work_catalog()
    types = WorkType.query.filter_by(organization_id=None).all()
    assert any(row.code == "GEN" for row in types)
    foundation = WorkElementTemplate.query.filter_by(
        organization_id=None, code="FOUND"
    ).one()
    codes = {row.code for row in foundation.activity_templates}
    assert {"LAYOUT", "EXCAV", "FORM", "PLACE"} <= codes


def test_organization_extension_isolated(app, org_b):
    create_org_work_type(display_name="Thickened edge slab", organization_id="ORG-001")
    org1 = WorkType.query.filter_by(organization_id="ORG-001", code="THICKENED-EDGE-SLAB").one()
    org2 = WorkType.query.filter_by(organization_id="ORG-002").all()
    assert org1.display_name == "Thickened edge slab"
    assert org2 == []
    baseline = WorkType.query.filter_by(organization_id=None, code="GEN").one()
    assert baseline.id != org1.id


def test_cannot_retire_baseline_catalog(app):
    baseline = WorkType.query.filter_by(organization_id=None, code="GEN").one()
    with pytest.raises(WorkStructureError, match="cannot be changed"):
        deactivate_catalog_row(baseline, organization_id="ORG-001")
    db.session.refresh(baseline)
    assert baseline.status == "ACTIVE"


def test_seed_fail_closed_unlocked_and_no_snapshots(app):
    project = _project()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-FG035-DRAFT",
        title="Draft",
    )
    version = estimate.current_version
    with pytest.raises(WorkStructureError, match="locked issued or accepted"):
        seed_project_work_structure(
            project_id=project.id,
            estimate_version_id=version.id,
            seeded_by="Joel Brayman",
        )
    task = _task(code="LT-FG035-EMPTY")
    _snapshot(version, task)
    set_version_status(version, "Issued")
    empty_project = _project(name="FG035 empty snapshots")
    empty_estimate = create_estimate(
        project_id=empty_project.id,
        estimate_number="EST-2026-FG035-EMPTY",
        title="Empty labour",
    )
    empty_version = empty_estimate.current_version
    set_version_status(empty_version, "Accepted")
    with pytest.raises(WorkStructureError, match="no labour hours"):
        seed_project_work_structure(
            project_id=empty_project.id,
            estimate_version_id=empty_version.id,
            seeded_by="Joel Brayman",
        )


def test_seed_pins_and_idempotent(app):
    project = _project()
    site = _task(
        code="LT-FG035-CLEAR",
        canonical_name="Clearing",
        category="Site work",
        trade="Earthwork",
    )
    forms = _task()
    estimate, version, snap, extra = _eligible_estimate(project, task=forms, extra_task=site)
    seed = seed_project_work_structure(
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    assert seed.estimate_version_id == version.id
    activities = ProjectWorkActivity.query.filter_by(project_work_element_id=ProjectWorkElement.query.filter_by(project_id=project.id).first().id).all()
    all_activities = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project.id
    ).all()
    assert len(all_activities) == 2
    forms_activity = next(row for row in all_activities if row.labour_task_id == forms.id)
    assert forms_activity.source_estimate_version_id == version.id
    assert forms_activity.source_estimate_labour_snapshot_id == snap.id
    assert forms_activity.estimated_hours == snap.calculated_man_hours
    assert forms_activity.quantity == snap.quantity
    assert forms_activity.unit == snap.unit
    assert forms_activity.production_rate == snap.resolved_production_rate
    names = {row.display_name for row in ProjectWorkElement.query.filter_by(project_id=project.id)}
    assert "Foundation" in names
    assert "Site work" in names
    with pytest.raises(WorkStructureError, match="already built"):
        seed_project_work_structure(
            project_id=project.id,
            estimate_version_id=version.id,
            seeded_by="Joel Brayman",
        )
    assert ProjectWorkStructureSeed.query.filter_by(project_id=project.id).count() == 1
    assert ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project.id
    ).count() == 2


def test_rename_does_not_break_snapshot_pin(app):
    project = _project()
    _, version, snap, _ = _eligible_estimate(project)
    seed_project_work_structure(
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    element = ProjectWorkElement.query.filter_by(project_id=project.id).one()
    activity = element.activities[0]
    rename_project_work_row(element, "Foundation regrouped")
    rename_project_work_row(activity, "Forms regrouped")
    db.session.refresh(activity)
    assert activity.source_estimate_labour_snapshot_id == snap.id
    assert activity.source_estimate_version_id == version.id
    assert element.display_name == "Foundation regrouped"


def test_project_specific_add_does_not_enter_catalog(app):
    project = _project()
    before_types = WorkType.query.filter_by(organization_id="ORG-001").count()
    element = add_project_element(project_id=project.id, display_name="Temporary access")
    add_project_activity(
        project_work_element_id=element.id,
        display_name="Snow clearing",
    )
    assert element.source_kind == "PROJECT"
    assert WorkType.query.filter_by(organization_id="ORG-001").count() == before_types
    assert WorkElementTemplate.query.filter_by(organization_id="ORG-001").count() == 0


def test_retire_does_not_delete(app):
    project = _project()
    element = add_project_element(project_id=project.id, display_name="Keep")
    deactivate_project_work_row(element)
    db.session.refresh(element)
    assert element.status == "INACTIVE"
    assert ProjectWorkElement.query.get(element.id) is not None


def test_catalog_and_hub_office_surface(client, app):
    project = _project()
    _eligible_estimate(project)
    catalog = client.get("/work-structure/")
    assert catalog.status_code == 200
    html = catalog.get_data(as_text=True)
    assert "Work types" in html
    assert "General construction" in html
    assert "csrf_token" in html
    assert "ESTIMATE_SEED" not in html
    hub = client.get(f"/projects/{project.id}")
    assert hub.status_code == 200
    hub_html = hub.get_data(as_text=True)
    assert "Project work" in html or "Project work" in hub_html
    assert "Build project work" in hub_html
    assert "source_estimate_labour_snapshot_id" not in hub_html
    assert "ESTIMATE_SEED" not in hub_html
    add = client.post(
        "/work-structure/types",
        data={"display_name": "TES extra"},
        follow_redirects=True,
    )
    assert add.status_code == 200
    assert WorkType.query.filter_by(organization_id="ORG-001", code="TES-EXTRA").one()
    seed = client.post(
        f"/work-structure/projects/{project.id}/seed",
        data={"estimate_version_id": project.estimates[0].current_version.id},
        follow_redirects=True,
    )
    assert seed.status_code == 200
    seeded_html = seed.get_data(as_text=True)
    assert "From estimate" in seeded_html
    assert "source_estimate" not in seeded_html
    duplicate = client.post(
        f"/work-structure/projects/{project.id}/seed",
        data={"estimate_version_id": project.estimates[0].current_version.id},
        follow_redirects=True,
    )
    assert b"already built" in duplicate.data
    plan = client.get(f"/work-structure/projects/{project.id}")
    assert plan.status_code == 200
    assert b"Forms" in plan.data


def test_org_b_cannot_see_org_a_extension(client, app, org_b):
    create_org_work_type(display_name="ORG-001 only type", organization_id="ORG-001")
    user_b = create_user(
        email="apex@example.com",
        password="apex-test-password",
        display_name="Apex User",
    )
    create_membership(user_b, "ORG-002")
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email="apex@example.com", password="apex-test-password")
    page = client.get("/work-structure/")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "ORG-001 only type" not in html
    assert "General construction" in html


def test_csrf_required_when_enabled(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-csrf",
            "WTF_CSRF_ENABLED": True,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        ensure_office_user()
        csrf_client = application.test_client()
        token = _csrf_token(csrf_client.get("/login"))
        login = login_office_user(
            csrf_client,
            email=DEFAULT_OFFICE_EMAIL,
            password=DEFAULT_OFFICE_PASSWORD,
            csrf_token=token,
        )
        assert login.status_code == 302
        denied = csrf_client.post(
            "/work-structure/types",
            data={"display_name": "No token"},
        )
        assert denied.status_code == 400
        office_token = _csrf_token(csrf_client.get("/work-structure/"))
        allowed = csrf_client.post(
            "/work-structure/types",
            data={"display_name": "With token", "csrf_token": office_token},
            follow_redirects=True,
        )
        assert allowed.status_code == 200
        assert WorkType.query.filter_by(organization_id="ORG-001", code="WITH-TOKEN").one()
        db.session.remove()
        db.drop_all()


def test_sort_order_and_org_element_on_baseline_type(app):
    work_type = WorkType.query.filter_by(organization_id=None, code="GEN").one()
    element = create_org_element_template(
        work_type_id=work_type.id,
        display_name="Thickened edge",
        organization_id="ORG-001",
    )
    assert element.organization_id == "ORG-001"
    project = _project()
    first = add_project_element(project_id=project.id, display_name="A")
    second = add_project_element(project_id=project.id, display_name="B")
    set_project_work_sort_order(second, 1)
    set_project_work_sort_order(first, 20)
    ordered = ProjectWorkElement.query.filter_by(project_id=project.id).order_by(
        ProjectWorkElement.sort_order.asc()
    ).all()
    assert [row.display_name for row in ordered] == ["B", "A"]


def test_alembic_fg035_tax_wbs_upgrade_downgrade_and_fresh(tmp_path):
    db_path = tmp_path / "fg035_tax_wbs.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == ["f3b4c5d6e7f8"]

        command.upgrade(alembic_cfg, "f2a3b4c5d6e7")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_types" not in tables
            assert "project_work_elements" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f2a3b4c5d6e7"]

        command.upgrade(alembic_cfg, "f3b4c5d6e7f8")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_types" in tables
            assert "work_element_templates" in tables
            assert "work_activity_templates" in tables
            assert "project_work_elements" in tables
            assert "project_work_activities" in tables
            assert "project_work_structure_seeds" in tables
            gen = conn.execute(
                sa.text(
                    "SELECT display_name FROM work_types "
                    "WHERE code='GEN' AND organization_id IS NULL"
                )
            ).fetchone()
            assert gen[0] == "General construction"
            activity_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM work_activity_templates "
                    "WHERE organization_id IS NULL"
                )
            ).scalar()
            assert activity_count == 6
            cols = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_work_activities)")
                )
            }
            assert "production_rate" in cols
            assert "source_estimate_labour_snapshot_id" in cols
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f3b4c5d6e7f8"]

        command.downgrade(alembic_cfg, "f2a3b4c5d6e7")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "work_types" not in tables
            assert "project_work_activities" not in tables
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f2a3b4c5d6e7"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f3b4c5d6e7f8"]
            gen = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM work_types "
                    "WHERE code='GEN' AND organization_id IS NULL"
                )
            ).scalar()
            assert gen == 1
