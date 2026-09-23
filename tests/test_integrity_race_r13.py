"""R13 INTEGRITY-RACE — expected unique collisions become contractor domain errors.

Synthetic sqlite only. No live DB. No schema. No migration.
R11 duplicate-Time policy is not invented. R14 numbering scope is not decided.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.query import Query

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.estimate import Estimate
from app.models.organization_crew import OrganizationCrew
from app.models.schedule import (
    ProjectWorkDependency,
    WorkScheduleAssignment,
    WorkScheduleHistory,
    WorkScheduleItem,
)
from app.models.time_entry import LabourTimeEntry
from app.models.work_structure import (
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkStructureSeed,
)
from app.services import schedule as schedule_svc
from app.services.organization_crew import CrewError, create_crew
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import (
    ScheduleError,
    _new_item,
    _raise_if_expected_schedule_integrity,
    assign_crew,
    assign_user,
    create_schedule_item,
    create_work_dependency,
)
from app.services.work_structure import (
    WorkStructureError,
    add_project_activity,
    add_project_element,
    ensure_baseline_work_catalog,
    seed_project_work_structure,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    login_office_user,
    logout_office_user,
)
from tests.test_work_structure_tax_wbs_fg035 import _eligible_estimate, _task

TODAY = date(2026, 9, 23)

UNSAFE_FRAGMENTS = (
    "sqlite",
    "sqlalchemy",
    "integrityerror",
    "unique constraint",
    "work_schedule_items.project_work_element_id",
    "work_schedule_items.project_work_activity_id",
    "work_schedule_assignments",
    "project_work_dependencies",
    "project_work_structure_seeds",
    "source_estimate_labour_snapshot_id",
    "uq_work_schedule",
    "uq_organization_crews",
    "organization_crews.organization_id",
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-r13-integrity-race",
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
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="R13 Project"):
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


def _work(project, element_name="Foundation", activity_name="Forms"):
    element = add_project_element(
        project_id=project.id,
        display_name=element_name,
        organization_id=project.organization_id,
    )
    activity = add_project_activity(
        project_work_element_id=element.id,
        display_name=activity_name,
        organization_id=project.organization_id,
    )
    return element, activity


def _assert_contractor_safe(body: str) -> None:
    lowered = body.lower()
    for fragment in UNSAFE_FRAGMENTS:
        assert fragment not in lowered, fragment


def _skip_assignment_lookup(monkeypatch):
    orig = Query.first

    def first(self):
        try:
            stmt = str(self.statement.compile(compile_kwargs={"literal_binds": True}))
        except Exception:
            stmt = str(self)
        lowered = stmt.lower()
        if "work_schedule_assignments" in lowered and (
            "worker_user_id" in lowered or "crew_id" in lowered
        ):
            return None
        return orig(self)

    monkeypatch.setattr(Query, "first", first)


def test_stale_element_create_raises_schedule_error_and_rolls_back(app, monkeypatch):
    project = _project()
    element, _activity = _work(project)
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    before_items = WorkScheduleItem.query.count()
    before_history = WorkScheduleHistory.query.count()
    monkeypatch.setattr(schedule_svc, "_active_element_item", lambda *a, **k: None)
    with pytest.raises(ScheduleError, match="already scheduled"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY + timedelta(days=1),
            organization_id=project.organization_id,
        )
    assert WorkScheduleItem.query.count() == before_items
    assert WorkScheduleHistory.query.count() == before_history


def test_stale_activity_create_raises_schedule_error_and_rolls_back(app, monkeypatch):
    project = _project()
    element, activity = _work(project)
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY + timedelta(days=3),
        organization_id=project.organization_id,
    )
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        project_work_activity_id=activity.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    before_items = WorkScheduleItem.query.count()
    before_history = WorkScheduleHistory.query.count()
    monkeypatch.setattr(schedule_svc, "_active_activity_item", lambda *a, **k: None)
    with pytest.raises(ScheduleError, match="already scheduled"):
        create_schedule_item(
            project_id=project.id,
            project_work_element_id=element.id,
            project_work_activity_id=activity.id,
            scheduled_start=TODAY + timedelta(days=1),
            scheduled_end=TODAY + timedelta(days=1),
            organization_id=project.organization_id,
        )
    assert WorkScheduleItem.query.count() == before_items
    assert WorkScheduleHistory.query.count() == before_history


def test_stale_person_assign_raises_schedule_error_and_rolls_back(app, monkeypatch):
    project = _project()
    element, _activity = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    worker = create_user(email="r13-worker@example.com", password="x", display_name="R13 Worker")
    create_membership(worker)
    db.session.commit()
    assign_user(item.id, worker_user_id=worker.id, organization_id=project.organization_id)
    before = WorkScheduleAssignment.query.count()
    before_history = WorkScheduleHistory.query.count()
    _skip_assignment_lookup(monkeypatch)
    with pytest.raises(ScheduleError, match="already assigned"):
        assign_user(item.id, worker_user_id=worker.id, organization_id=project.organization_id)
    assert WorkScheduleAssignment.query.count() == before
    assert WorkScheduleHistory.query.count() == before_history


def test_stale_crew_assign_raises_schedule_error_and_rolls_back(app, monkeypatch):
    project = _project()
    element, _activity = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    crew = create_crew(name="R13 Crew", organization_id=project.organization_id)
    assign_crew(item.id, crew_id=crew.id, organization_id=project.organization_id)
    before = WorkScheduleAssignment.query.count()
    _skip_assignment_lookup(monkeypatch)
    with pytest.raises(ScheduleError, match="already assigned"):
        assign_crew(item.id, crew_id=crew.id, organization_id=project.organization_id)
    assert WorkScheduleAssignment.query.count() == before


def test_stale_dependency_raises_schedule_error_and_rolls_back(app, monkeypatch):
    project = _project()
    first, _ = _work(project, element_name="Prior", activity_name="A")
    second, _ = _work(project, element_name="After", activity_name="B")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=first.id,
        successor_element_id=second.id,
        organization_id=project.organization_id,
    )
    before = ProjectWorkDependency.query.count()
    before_history = WorkScheduleHistory.query.count()
    monkeypatch.setattr(schedule_svc, "_active_edge", lambda *a, **k: None)
    monkeypatch.setattr(schedule_svc, "_would_create_cycle", lambda *a, **k: False)
    with pytest.raises(ScheduleError, match="already exists"):
        create_work_dependency(
            project_id=project.id,
            predecessor_element_id=first.id,
            successor_element_id=second.id,
            organization_id=project.organization_id,
        )
    assert ProjectWorkDependency.query.count() == before
    assert WorkScheduleHistory.query.count() == before_history


def test_stale_seed_raises_work_structure_error_and_rolls_back(app, monkeypatch):
    project = _project(name="R13 Seed")
    _estimate, version, _snap, _extra = _eligible_estimate(project)
    seed_project_work_structure(
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    before_seed = ProjectWorkStructureSeed.query.filter_by(project_id=project.id).count()
    before_elements = ProjectWorkElement.query.filter_by(project_id=project.id).count()
    before_activities = (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .filter(ProjectWorkElement.project_id == project.id)
        .count()
    )
    monkeypatch.setattr(
        "app.services.work_structure.get_project_seed", lambda *a, **k: None
    )
    with pytest.raises(WorkStructureError, match="already built"):
        seed_project_work_structure(
            project_id=project.id,
            estimate_version_id=version.id,
            seeded_by="Joel Brayman",
        )
    assert ProjectWorkStructureSeed.query.filter_by(project_id=project.id).count() == before_seed
    assert ProjectWorkElement.query.filter_by(project_id=project.id).count() == before_elements
    assert (
        ProjectWorkActivity.query.join(ProjectWorkElement)
        .filter(ProjectWorkElement.project_id == project.id)
        .count()
        == before_activities
    )


def test_stale_crew_name_raises_crew_error_and_rolls_back(app, monkeypatch):
    create_crew(name="Site crew", organization_id=DEFAULT_ORGANIZATION_ID)
    before = OrganizationCrew.query.count()

    class _Skip:
        def filter_by(self, **kwargs):
            class _None:
                def first(self_inner):
                    return None

            return _None()

    monkeypatch.setattr(
        "app.services.organization_crew.OrganizationCrew.query",
        _Skip(),
    )
    with pytest.raises(CrewError, match="already exists"):
        create_crew(name="Site crew", organization_id=DEFAULT_ORGANIZATION_ID)
    assert db.session.query(OrganizationCrew).count() == before


def test_schedule_create_route_expected_collision_is_contractor_safe(client, app, monkeypatch):
    project = _project()
    element, _activity = _work(project)
    create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    monkeypatch.setattr(schedule_svc, "_active_element_item", lambda *a, **k: None)
    response = client.post(
        "/schedule/items/new",
        data={
            "project_id": project.id,
            "project_work_element_id": element.id,
            "scheduled_start": TODAY.isoformat(),
            "scheduled_end": (TODAY + timedelta(days=1)).isoformat(),
        },
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "already scheduled" in body
    assert "Schedule saved." not in body
    _assert_contractor_safe(body)
    assert WorkScheduleItem.query.filter_by(project_work_element_id=element.id).count() == 1


def test_assignment_route_expected_collision_is_contractor_safe(client, app, monkeypatch):
    project = _project()
    element, _activity = _work(project)
    item = create_schedule_item(
        project_id=project.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=project.organization_id,
    )
    worker = create_user(email="r13-assign@example.com", password="x", display_name="Assign")
    create_membership(worker)
    db.session.commit()
    assign_user(item.id, worker_user_id=worker.id, organization_id=project.organization_id)
    _skip_assignment_lookup(monkeypatch)
    response = client.post(
        f"/schedule/items/{item.id}/assignments",
        data={"worker_user_id": worker.id},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "already assigned" in body
    assert "Assignment saved." not in body
    _assert_contractor_safe(body)
    assert WorkScheduleAssignment.query.filter_by(work_schedule_item_id=item.id).count() == 1


def test_dependency_route_expected_collision_is_contractor_safe(client, app, monkeypatch):
    project = _project()
    first, _ = _work(project, element_name="Prior", activity_name="A")
    second, _ = _work(project, element_name="After", activity_name="B")
    create_work_dependency(
        project_id=project.id,
        predecessor_element_id=first.id,
        successor_element_id=second.id,
        organization_id=project.organization_id,
    )
    monkeypatch.setattr(schedule_svc, "_active_edge", lambda *a, **k: None)
    monkeypatch.setattr(schedule_svc, "_would_create_cycle", lambda *a, **k: False)
    response = client.post(
        f"/schedule/projects/{project.id}/dependencies",
        data={
            "predecessor_element_id": first.id,
            "successor_element_id": second.id,
        },
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "already exists" in body
    assert "Work order saved." not in body
    _assert_contractor_safe(body)
    assert ProjectWorkDependency.query.filter_by(project_id=project.id).count() == 1


def test_seed_route_expected_collision_is_contractor_safe(client, app, monkeypatch):
    project = _project(name="R13 Seed Route")
    _task(code="LT-R13-SEED")
    _estimate, version, _snap, _extra = _eligible_estimate(project)
    seed_project_work_structure(
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    monkeypatch.setattr(
        "app.services.work_structure.get_project_seed", lambda *a, **k: None
    )
    response = client.post(
        f"/work-structure/projects/{project.id}/seed",
        data={"estimate_version_id": version.id},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "already built" in body
    assert "Project work built from the estimate." not in body
    _assert_contractor_safe(body)
    assert ProjectWorkStructureSeed.query.filter_by(project_id=project.id).count() == 1


def test_crew_route_expected_collision_is_contractor_safe(client, app, monkeypatch):
    create_crew(name="Finish crew", organization_id=DEFAULT_ORGANIZATION_ID)

    class _Skip:
        def filter_by(self, **kwargs):
            class _None:
                def first(self_inner):
                    return None

            return _None()

    monkeypatch.setattr(
        "app.services.organization_crew.OrganizationCrew.query",
        _Skip(),
    )
    response = client.post(
        "/settings/crews/new",
        data={"name": "Finish crew"},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "already exists" in body
    assert "Crew saved." not in body
    _assert_contractor_safe(body)
    assert (
        db.session.query(OrganizationCrew).filter_by(name="Finish crew").count() == 1
    )


def test_unmatched_integrity_error_is_not_recast_as_expected_schedule(app):
    fabricated = IntegrityError(
        "INSERT",
        {},
        Exception("UNIQUE constraint failed: estimates.estimate_number"),
    )
    with pytest.raises(IntegrityError):
        _raise_if_expected_schedule_integrity(fabricated)


def test_schedule_check_constraint_is_not_recast_as_already_scheduled(app):
    project = _project()
    element, _activity = _work(project)
    with pytest.raises(IntegrityError) as caught:
        _new_item(
            organization_id=project.organization_id,
            project=project,
            element=element,
            activity=None,
            scheduled_start=TODAY + timedelta(days=2),
            scheduled_end=TODAY,
        )
    assert "already scheduled" not in str(caught.value).lower()
    db.session.rollback()
    assert WorkScheduleItem.query.count() == 0


def test_r01_cross_org_schedule_create_does_not_use_foreign_project(app, org_b):
    home = _project(name="Home")
    element, _activity = _work(home)
    create_schedule_item(
        project_id=home.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=home.organization_id,
    )
    with pytest.raises(ScheduleError, match="not found"):
        create_schedule_item(
            project_id=home.id,
            project_work_element_id=element.id,
            scheduled_start=TODAY,
            scheduled_end=TODAY,
            organization_id=org_b.id,
        )
    assert WorkScheduleItem.query.filter_by(organization_id=org_b.id).count() == 0


def test_r01_route_does_not_leak_foreign_collision(client, app, org_b):
    home = _project(name="Home Collision")
    element, _activity = _work(home)
    create_schedule_item(
        project_id=home.id,
        project_work_element_id=element.id,
        scheduled_start=TODAY,
        scheduled_end=TODAY,
        organization_id=home.organization_id,
    )
    outsider = create_user(
        email="apex-r13@example.com", password="secret", display_name="Apex"
    )
    create_membership(outsider, organization_id=org_b.id)
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email="apex-r13@example.com", password="secret")
    response = client.post(
        "/schedule/items/new",
        data={
            "project_id": home.id,
            "project_work_element_id": element.id,
            "scheduled_start": TODAY.isoformat(),
            "scheduled_end": TODAY.isoformat(),
        },
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    _assert_contractor_safe(body)
    assert "Home Collision" not in body
    assert WorkScheduleItem.query.filter_by(organization_id=org_b.id).count() == 0


def test_r11_policy_not_invented(app):
    names = []
    for arg in LabourTimeEntry.__table_args__:
        if isinstance(arg, UniqueConstraint):
            names.extend(arg.columns.keys())
    assert names == ["supersedes_id"]


def test_r14_numbering_scope_not_decided(app):
    assert Estimate.estimate_number.unique is True
    # R13 must not recast a commercial-number collision as a Schedule story.
    fabricated = IntegrityError(
        "INSERT",
        {},
        Exception("UNIQUE constraint failed: estimates.estimate_number"),
    )
    with pytest.raises(IntegrityError):
        _raise_if_expected_schedule_integrity(fabricated)
