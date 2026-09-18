"""FG-035 SCOPE lineage: original, Change Order, Extra Work."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.work_structure import (
    SCOPE_CHANGE_ORDER,
    SCOPE_EXTRA_WORK,
    SCOPE_ORIGINAL,
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkScopeHistory,
)
from app.project_controls.services import create_change_order
from app.services import create_estimate
from app.services.estimates import set_version_status
from app.services.labour_engine import create_estimate_labour_snapshot, create_labour_task
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.work_scope import (
    WorkScopeError,
    activity_scope_totals,
    add_authorized_change_order_activity,
    add_authorized_change_order_element,
    apply_change_order_delta,
    create_change_order_from_extra_work,
    create_extra_work,
    inherit_scope_lineage,
    inherit_scope_lineage_from_delta,
    link_extra_work_to_change_order,
    list_unresolved_extra_work,
    project_scope_totals,
    reclassify_extra_work_to_original,
    reclassify_original_to_extra_work,
)
from app.services.work_structure import (
    add_project_element,
    ensure_baseline_work_catalog,
    seed_project_work_structure,
)
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-scope",
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


def _project(org_id=DEFAULT_ORGANIZATION_ID, name="FG035 SCOPE Project"):
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


def _task(org_id=DEFAULT_ORGANIZATION_ID, code="LT-FG035-SCOPE-FORM", **kwargs):
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


def _snapshot(version, task, quantity="800"):
    return create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal(quantity),
        override_production_rate=Decimal("0.05"),
        override_production_reason="SCOPE test",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="SCOPE test",
        created_by="Joel Brayman",
        organization_id=version.estimate.project.organization_id,
    )


def _seeded_project(name="FG035 SCOPE seeded"):
    project = _project(name=name)
    task = _task()
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-2026-FG035-SCOPE",
        title="FG035 SCOPE synthetic estimate",
    )
    version = estimate.current_version
    snap = _snapshot(version, task)
    set_version_status(version, "Issued")
    db.session.refresh(version)
    seed_project_work_structure(
        project_id=project.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    activity = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project.id
    ).one()
    return project, version, snap, activity


def _approved_co(project, title="Additional Forms", status="Approved"):
    return create_change_order(project=project, title=title, status=status)


def test_estimate_seeded_work_is_original_and_pins_hold(app):
    project, version, snap, activity = _seeded_project()
    assert activity.scope_origin == SCOPE_ORIGINAL
    assert activity.source_estimate_version_id == version.id
    assert activity.source_estimate_labour_snapshot_id == snap.id
    assert activity.estimated_hours == snap.calculated_man_hours
    assert activity.quantity == snap.quantity
    assert activity.production_rate == snap.resolved_production_rate
    element = activity.element
    assert element.scope_origin == SCOPE_ORIGINAL
    totals = activity_scope_totals(activity)
    assert totals["original_hours"] == snap.calculated_man_hours
    assert totals["current_authorized_hours"] == snap.calculated_man_hours
    lineage = inherit_scope_lineage(activity)
    assert lineage["scope_origin"] == SCOPE_ORIGINAL
    assert lineage["effective_origin"] == SCOPE_ORIGINAL
    assert lineage["authorized"] is True
    assert lineage["source_estimate_labour_snapshot_id"] == snap.id


def test_later_change_order_does_not_rewrite_original_labour(app):
    project, version, snap, activity = _seeded_project()
    original_hours = activity.estimated_hours
    original_qty = activity.quantity
    original_rate = activity.production_rate
    co = _approved_co(project, title="Additional Forms")
    apply_change_order_delta(
        project_work_activity_id=activity.id,
        change_order_id=co.id,
        hours_delta="12",
        created_by="Joel Brayman",
    )
    db.session.refresh(activity)
    assert activity.estimated_hours == original_hours
    assert activity.quantity == original_qty
    assert activity.production_rate == original_rate
    assert activity.source_estimate_version_id == version.id
    assert activity.source_estimate_labour_snapshot_id == snap.id
    totals = activity_scope_totals(activity)
    assert totals["original_hours"] == original_hours
    assert totals["approved_change_hours"] == Decimal("12")
    assert totals["current_authorized_hours"] == original_hours + Decimal("12")


def test_eligible_co_adds_new_element_and_activity_lineage(app):
    project, *_rest = _seeded_project()
    co = _approved_co(project, title="Exterior Equipment Pad")
    element = add_authorized_change_order_element(
        project_id=project.id,
        change_order_id=co.id,
        display_name="Equipment Pad",
        created_by="Joel Brayman",
    )
    assert element.scope_origin == SCOPE_CHANGE_ORDER
    assert element.change_order_id == co.id
    activity = add_authorized_change_order_activity(
        project_work_element_id=element.id,
        change_order_id=co.id,
        display_name="Excavation",
        estimated_hours="8",
        created_by="Joel Brayman",
    )
    assert activity.scope_origin == SCOPE_CHANGE_ORDER
    assert activity.change_order_id == co.id
    lineage = inherit_scope_lineage(activity)
    assert lineage["effective_origin"] == SCOPE_CHANGE_ORDER
    assert lineage["change_order_number"] == co.number
    plumbing = ProjectWorkElement.query.filter_by(
        project_id=project.id, scope_origin=SCOPE_ORIGINAL
    ).one()
    drain = add_authorized_change_order_activity(
        project_work_element_id=plumbing.id,
        change_order_id=co.id,
        display_name="Additional Garage Drain",
        estimated_hours="6",
        created_by="Joel Brayman",
    )
    assert plumbing.scope_origin == SCOPE_ORIGINAL
    assert drain.scope_origin == SCOPE_CHANGE_ORDER
    assert drain.change_order_id == co.id


def test_wrong_project_and_org_and_ineligible_co_blocked(app, org_b):
    project_a, *_rest = _seeded_project(name="SCOPE A")
    project_b = _project(org_id="ORG-002", name="SCOPE B")
    activity_a = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project_a.id
    ).one()
    co_b = create_change_order(project=project_b, title="Other project", status="Approved")
    with pytest.raises(WorkScopeError, match="does not belong to this project"):
        apply_change_order_delta(
            project_work_activity_id=activity_a.id,
            change_order_id=co_b.id,
            hours_delta="1",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    draft = _approved_co(project_a, title="Draft pad", status="Draft")
    with pytest.raises(WorkScopeError, match="not approved"):
        add_authorized_change_order_element(
            project_id=project_a.id,
            change_order_id=draft.id,
            display_name="Should not exist",
        )
    pending = _approved_co(project_a, title="Pending pad", status="Pending Approval")
    with pytest.raises(WorkScopeError, match="not approved"):
        apply_change_order_delta(
            project_work_activity_id=activity_a.id,
            change_order_id=pending.id,
            hours_delta="4",
        )


def test_multiple_change_orders_and_reductions(app):
    project, _version, snap, activity = _seeded_project()
    original = activity.estimated_hours
    co4 = _approved_co(project, title="Additional Forms")
    co9 = _approved_co(project, title="More Forms")
    apply_change_order_delta(
        project_work_activity_id=activity.id,
        change_order_id=co4.id,
        hours_delta="12",
    )
    apply_change_order_delta(
        project_work_activity_id=activity.id,
        change_order_id=co9.id,
        hours_delta="8",
    )
    totals = activity_scope_totals(activity)
    assert totals["original_hours"] == original
    assert totals["approved_change_hours"] == Decimal("20")
    assert totals["current_authorized_hours"] == original + Decimal("20")
    decorative = _project(name="Decorative")
    task = _task(code="LT-FG035-DECO", canonical_name="Decorative Concrete", category="Flatwork")
    estimate = create_estimate(
        project_id=decorative.id,
        estimate_number="EST-2026-FG035-DECO",
        title="Decorative",
    )
    version = estimate.current_version
    create_estimate_labour_snapshot(
        estimate_version_id=version.id,
        labour_task_id=task.id,
        quantity=Decimal("480"),
        override_production_rate=Decimal("0.05"),
        override_production_reason="SCOPE test",
        override_direct_labour_cost_rate=Decimal("65"),
        override_direct_labour_reason="SCOPE test",
        created_by="Joel Brayman",
        organization_id=decorative.organization_id,
    )
    set_version_status(version, "Accepted")
    seed_project_work_structure(
        project_id=decorative.id,
        estimate_version_id=version.id,
        seeded_by="Joel Brayman",
    )
    deco_activity = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == decorative.id
    ).one()
    original_deco = deco_activity.estimated_hours
    assert original_deco == Decimal("24")
    co6 = create_change_order(project=decorative, title="Remove decorative", status="Approved")
    apply_change_order_delta(
        project_work_activity_id=deco_activity.id,
        change_order_id=co6.id,
        hours_delta="-24",
    )
    db.session.refresh(deco_activity)
    assert deco_activity.estimated_hours == original_deco
    deco_totals = activity_scope_totals(deco_activity)
    assert deco_totals["original_hours"] == Decimal("24")
    assert deco_totals["current_authorized_hours"] == Decimal("0")
    with pytest.raises(WorkScopeError, match="less than zero"):
        apply_change_order_delta(
            project_work_activity_id=deco_activity.id,
            change_order_id=co6.id,
            hours_delta="-1",
        )
    co_partial = _approved_co(project, title="Reduce forms")
    apply_change_order_delta(
        project_work_activity_id=activity.id,
        change_order_id=co_partial.id,
        hours_delta="-10",
    )
    after_partial = activity_scope_totals(activity)
    assert after_partial["current_authorized_hours"] == original + Decimal("10")


def test_extra_work_create_link_reclass_and_unresolved(app):
    project, *_rest = _seeded_project(name="Speakeasy")
    plumbing = ProjectWorkElement.query.filter_by(project_id=project.id).one()
    extra = create_extra_work(
        project_id=project.id,
        description="Move/add garage drain",
        project_work_element_id=plumbing.id,
        created_by="Field User",
    )
    assert extra.scope_origin == SCOPE_EXTRA_WORK
    assert extra.element.id == plumbing.id
    assert plumbing.scope_origin == SCOPE_ORIGINAL
    assert inherit_scope_lineage(extra)["effective_origin"] == SCOPE_EXTRA_WORK
    unresolved = list_unresolved_extra_work(project.id)
    assert extra in unresolved["activities"]
    standalone = create_extra_work(
        project_id=project.id,
        description="Temp heat",
        new_element_name="Temporary heat",
        created_by="Field User",
    )
    assert standalone.element.scope_origin == SCOPE_EXTRA_WORK
    draft = create_change_order(project=project, title="Garage drain CO", status="Draft")
    linked = link_extra_work_to_change_order(
        project_work_activity_id=extra.id,
        change_order_id=draft.id,
        actor_display_name="Joel Brayman",
    )
    assert linked.scope_origin == SCOPE_EXTRA_WORK
    assert linked.change_order_id == draft.id
    assert inherit_scope_lineage(linked)["effective_origin"] == SCOPE_EXTRA_WORK
    assert extra.id in {row.id for row in list_unresolved_extra_work(project.id)["activities"]}
    draft.status = "Approved"
    db.session.commit()
    db.session.refresh(linked)
    assert inherit_scope_lineage(linked)["effective_origin"] == SCOPE_CHANGE_ORDER
    assert extra not in list_unresolved_extra_work(project.id)["activities"]
    approved = _approved_co(project, title="Temp heat CO")
    linked_approved = link_extra_work_to_change_order(
        project_work_activity_id=standalone.id,
        change_order_id=approved.id,
        actor_display_name="Joel Brayman",
    )
    assert linked_approved.scope_origin == SCOPE_CHANGE_ORDER
    history = ProjectWorkScopeHistory.query.filter_by(work_id=extra.id, work_kind="ACTIVITY").all()
    assert any(row.prior_scope_origin == SCOPE_EXTRA_WORK for row in history)
    mistaken = create_extra_work(
        project_id=project.id,
        description="Was original",
        project_work_element_id=plumbing.id,
        created_by="Joel Brayman",
    )
    reclassified = reclassify_extra_work_to_original(
        project_work_activity_id=mistaken.id,
        actor_display_name="Joel Brayman",
        reason="This was original plumbing.",
    )
    assert reclassified.scope_origin == SCOPE_ORIGINAL
    original_activity = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project.id,
        ProjectWorkActivity.source_estimate_labour_snapshot_id.isnot(None),
    ).one()
    hours = original_activity.estimated_hours
    pin = original_activity.source_estimate_labour_snapshot_id
    reviewed = reclassify_original_to_extra_work(
        project_work_activity_id=original_activity.id,
        actor_display_name="Joel Brayman",
    )
    assert reviewed.scope_origin == SCOPE_EXTRA_WORK
    assert reviewed.estimated_hours == hours
    assert reviewed.source_estimate_labour_snapshot_id == pin
    created = create_extra_work(
        project_id=project.id,
        description="Site extra",
        created_by="Joel Brayman",
    )
    create_change_order_from_extra_work(
        project_work_activity_id=created.id,
        title="From extra work",
        actor_display_name="Joel Brayman",
    )


def test_project_specific_add_is_fail_closed_extra_work(app):
    project = _project(name="No seed")
    element = add_project_element(project_id=project.id, display_name="Temporary access")
    assert element.scope_origin == SCOPE_EXTRA_WORK
    assert element.source_kind == "PROJECT"


def test_hub_and_field_extra_work_surface(client, app):
    project, *_rest = _seeded_project(name="Hub SCOPE")
    hub = client.get(f"/projects/{project.id}")
    html = hub.get_data(as_text=True)
    assert "Original work" in hub.get_data(as_text=True) or "Original labour" in html
    assert "scope_origin" not in html
    assert "source_estimate_labour_snapshot_id" not in html
    ensure_office_user()
    login_office_user(client)
    extra = client.post(
        f"/work-structure/projects/{project.id}/extra-work",
        data={"description": "Move drain", "project_work_element_id": ProjectWorkElement.query.filter_by(project_id=project.id).one().id},
        follow_redirects=True,
    )
    assert extra.status_code == 200
    extra_html = extra.get_data(as_text=True)
    assert "Extra work" in extra_html
    assert "Move drain" in extra_html
    confirm = client.post(f"/field/projects/{project.id}", follow_redirects=True)
    assert confirm.status_code == 200
    field_page = client.get(f"/field/projects/{project.id}/extra-work")
    assert field_page.status_code == 200
    field_html = field_page.get_data(as_text=True)
    assert "outside the work you were sent to do" in field_html
    posted = client.post(
        f"/field/projects/{project.id}/extra-work",
        data={"description": "Add another drain", "new_element_name": "Field extra"},
        follow_redirects=True,
    )
    assert posted.status_code == 200
    activity = ProjectWorkActivity.query.filter_by(display_name="Add another drain").one()
    assert activity.scope_origin == SCOPE_EXTRA_WORK


def test_future_time_and_schedule_inherit_without_time_entry(app):
    project, *_rest = _seeded_project()
    original = ProjectWorkActivity.query.join(ProjectWorkElement).filter(
        ProjectWorkElement.project_id == project.id
    ).one()
    co = _approved_co(project)
    delta = apply_change_order_delta(
        project_work_activity_id=original.id,
        change_order_id=co.id,
        hours_delta="12",
    )
    extra = create_extra_work(
        project_id=project.id,
        description="Night work",
        created_by="Field",
    )
    assert inherit_scope_lineage(original)["scope_origin"] == SCOPE_ORIGINAL
    delta_lineage = inherit_scope_lineage_from_delta(delta)
    assert delta_lineage["scope_origin"] == SCOPE_CHANGE_ORDER
    assert delta_lineage["change_order_id"] == co.id
    assert inherit_scope_lineage(extra)["effective_origin"] == SCOPE_EXTRA_WORK
    totals = project_scope_totals(project.id)
    assert totals["original_hours"] == original.estimated_hours
    assert totals["approved_change_hours"] == Decimal("12")
    assert totals["current_authorized_hours"] == original.estimated_hours + Decimal("12")


def test_alembic_fg035_scope_upgrade_downgrade_and_backfill(tmp_path):
    db_path = tmp_path / "fg035_scope.db"
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
        assert script.get_heads() == ["c3d4e5f6a7b8"]

        command.upgrade(alembic_cfg, "f3b4c5d6e7f8")
        engine = db.engine
        with engine.begin() as conn:
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(project_work_activities)"))
            }
            assert "scope_origin" not in cols
            assert "project_work_scope_deltas" not in {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            conn.execute(
                sa.text(
                    "INSERT INTO organizations (id, legal_name, display_name, currency, is_active, created_at, updated_at) "
                    "VALUES ('ORG-SCOPE-MIG', 'Scope Mig', 'Scope Mig', 'CAD', 1, '2026-09-15', '2026-09-15')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO clients (name, organization_id, created_at) "
                    "VALUES ('SCOPE mig', 'ORG-SCOPE-MIG', '2026-09-15')"
                )
            )
            client_id = conn.execute(sa.text("SELECT id FROM clients WHERE name='SCOPE mig'")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO projects (name, client_id, organization_id, status, created_at) "
                    "VALUES ('SCOPE mig project', :client_id, 'ORG-SCOPE-MIG', 'Estimating', '2026-09-15')"
                ),
                {"client_id": client_id},
            )
            project_id = conn.execute(
                sa.text("SELECT id FROM projects WHERE name='SCOPE mig project'")
            ).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO project_work_elements "
                    "(organization_id, project_id, display_name, status, sort_order, source_kind, created_at) "
                    "VALUES ('ORG-SCOPE-MIG', :project_id, 'Seeded', 'ACTIVE', 10, 'ESTIMATE_SEED', '2026-09-15')"
                ),
                {"project_id": project_id},
            )
            element_id = conn.execute(
                sa.text("SELECT id FROM project_work_elements WHERE display_name='Seeded'")
            ).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO project_work_activities "
                    "(organization_id, project_work_element_id, display_name, status, sort_order, source_kind, created_at) "
                    "VALUES ('ORG-SCOPE-MIG', :element_id, 'Forms', 'ACTIVE', 10, 'ESTIMATE_SEED', '2026-09-15')"
                ),
                {"element_id": element_id},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO project_work_elements "
                    "(organization_id, project_id, display_name, status, sort_order, source_kind, created_at) "
                    "VALUES ('ORG-SCOPE-MIG', :project_id, 'Ambiguous', 'ACTIVE', 20, 'PROJECT', '2026-09-15')"
                ),
                {"project_id": project_id},
            )

        command.upgrade(alembic_cfg, "f4c5d6e7f8a9")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_work_scope_deltas" in tables
            assert "project_work_scope_history" in tables
            seeded = conn.execute(
                sa.text(
                    "SELECT scope_origin FROM project_work_activities WHERE display_name='Forms'"
                )
            ).scalar()
            assert seeded == "ORIGINAL"
            element_origin = conn.execute(
                sa.text(
                    "SELECT scope_origin FROM project_work_elements WHERE display_name='Seeded'"
                )
            ).scalar()
            assert element_origin == "ORIGINAL"
            ambiguous = conn.execute(
                sa.text(
                    "SELECT scope_origin FROM project_work_elements WHERE display_name='Ambiguous'"
                )
            ).scalar()
            assert ambiguous == "EXTRA_WORK"
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f4c5d6e7f8a9"]
            indexes = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA index_list(project_work_scope_deltas)"))
            }
            assert "ix_project_work_scope_deltas_activity_co" in indexes

        command.downgrade(alembic_cfg, "f3b4c5d6e7f8")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_work_scope_deltas" not in tables
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(project_work_activities)"))
            }
            assert "scope_origin" not in cols
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f3b4c5d6e7f8"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c3d4e5f6a7b8"]
