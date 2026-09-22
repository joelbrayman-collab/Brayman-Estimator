"""R03A BUSINESS-ACTION-ATOMICITY — Walkthrough Accept → Punch.

Synthetic file SQLite only. No live Walkthrough Accept. No live Project Close.
No schema. No migration.
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Project
from app.models.final_walkthrough import (
    WALKTHROUGH_REVIEW_ACCEPTED,
    WALKTHROUGH_REVIEW_PENDING,
    ProjectFinalWalkthroughItem,
)
from app.models.punch_list import (
    PUNCH_LIST_EVENT_CREATED,
    PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH,
    PUNCH_LIST_ORIGIN_CONTRACTOR,
    PUNCH_LIST_SOURCE_OTHER,
    PUNCH_LIST_STATUS_COMPLETE,
    PUNCH_LIST_STATUS_OPEN,
    ProjectPunchListItem,
    ProjectPunchListItemEvent,
)
from app.models.user import UserMembership
from app.presentation.contractor_copy import (
    PROJECT_CLOSED_NEW_WORK,
    WALKTHROUGH_ALREADY_REVIEWED,
)
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_final_walkthrough import (
    WalkthroughError,
    accept_walkthrough_item_to_punch_list,
    create_walkthrough_invitation,
    resolve_walkthrough_access,
    submit_walkthrough_response,
)
from app.services.project_operating_lifecycle import close_project
from app.services.project_punch_list import (
    complete_punch_list_item,
    create_punch_list_item,
    create_punch_list_item_from_client_walkthrough,
    reopen_punch_list_item,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import create_membership, create_user, ensure_office_user


class InjectedAcceptLinkFailure(Exception):
    """Test-only failure after Punch create/flush and before Walkthrough link."""


def _app(tmp_path):
    db_path = tmp_path / "r03a-accept.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-r03a-accept",
            "WTF_CSRF_ENABLED": False,
        }
    )


@pytest.fixture
def app(tmp_path):
    application = _app(tmp_path)
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


def _office_membership():
    user = ensure_office_user()
    return UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    ).one()


def _make_owner():
    user = ensure_office_user()
    membership = _office_membership()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, user)
    return user, membership


def _add_project(name="R03A Accept"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="r03a@example.com",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _pending_item(project, actor, description="Needs punch."):
    issue = create_walkthrough_invitation(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=[description]
    )
    return ProjectFinalWalkthroughItem.query.filter_by(project_id=project.id).one()


def _counts(project_id):
    return {
        "punches": ProjectPunchListItem.query.filter_by(project_id=project_id).count(),
        "events": ProjectPunchListItemEvent.query.filter_by(project_id=project_id).count(),
        "created_events": ProjectPunchListItemEvent.query.filter_by(
            project_id=project_id, event=PUNCH_LIST_EVENT_CREATED
        ).count(),
    }


def _accept(project, item, actor):
    return accept_walkthrough_item_to_punch_list(
        project,
        item.id,
        actor,
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )


def test_eligible_active_accept_creates_one_punch_and_link(app):
    owner, _membership = _make_owner()
    project = _add_project("Happy Accept")
    item = _pending_item(project, owner, "North window.")
    before = _counts(project.id)
    accepted, punch = _accept(project, item, owner)
    db.session.expire_all()
    item = db.session.get(ProjectFinalWalkthroughItem, item.id)
    after = _counts(project.id)
    assert before == {"punches": 0, "events": 0, "created_events": 0}
    assert after == {"punches": 1, "events": 1, "created_events": 1}
    assert punch.origin_type == PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH
    assert punch.status == PUNCH_LIST_STATUS_OPEN
    assert punch.description == "North window."
    assert accepted.review_status == WALKTHROUGH_REVIEW_ACCEPTED
    assert accepted.punch_list_item_id == punch.id
    assert item.review_status == WALKTHROUGH_REVIEW_ACCEPTED
    assert item.punch_list_item_id == punch.id
    assert item.reviewed_by_user_id == owner.id
    assert item.reviewed_at is not None


def test_failure_after_punch_create_before_link_rolls_back(app, monkeypatch):
    owner, _membership = _make_owner()
    project = _add_project("Injected Fail")
    item = _pending_item(project, owner, "Orphan bait.")
    item_id = item.id
    project_id = project.id
    original = create_punch_list_item_from_client_walkthrough

    def explode(*args, **kwargs):
        result = original(*args, **kwargs)
        raise InjectedAcceptLinkFailure("after punch create, before walkthrough link")

    monkeypatch.setattr(
        "app.services.project_final_walkthrough.create_punch_list_item_from_client_walkthrough",
        explode,
    )
    with pytest.raises(InjectedAcceptLinkFailure):
        _accept(project, item, owner)
    db.session.expire_all()
    loaded = db.session.get(ProjectFinalWalkthroughItem, item_id)
    after = _counts(project_id)
    assert after == {"punches": 0, "events": 0, "created_events": 0}
    assert loaded.review_status == WALKTHROUGH_REVIEW_PENDING
    assert loaded.punch_list_item_id is None
    assert loaded.reviewed_at is None
    assert loaded.reviewed_by_user_id is None


def test_retry_after_injected_failure_succeeds_once(app, monkeypatch):
    owner, _membership = _make_owner()
    project = _add_project("Retry After Fail")
    item = _pending_item(project, owner, "Retry me.")
    item_id = item.id
    original = create_punch_list_item_from_client_walkthrough

    def explode(*args, **kwargs):
        result = original(*args, **kwargs)
        raise InjectedAcceptLinkFailure("after punch create, before walkthrough link")

    monkeypatch.setattr(
        "app.services.project_final_walkthrough.create_punch_list_item_from_client_walkthrough",
        explode,
    )
    with pytest.raises(InjectedAcceptLinkFailure):
        _accept(project, item, owner)
    monkeypatch.setattr(
        "app.services.project_final_walkthrough.create_punch_list_item_from_client_walkthrough",
        original,
    )
    accepted, punch = _accept(project, item, owner)
    db.session.expire_all()
    loaded = db.session.get(ProjectFinalWalkthroughItem, item_id)
    after = _counts(project.id)
    assert after == {"punches": 1, "events": 1, "created_events": 1}
    assert accepted.punch_list_item_id == punch.id
    assert loaded.review_status == WALKTHROUGH_REVIEW_ACCEPTED
    assert loaded.punch_list_item_id == punch.id


def test_retry_after_success_does_not_create_second_punch(app):
    owner, _membership = _make_owner()
    project = _add_project("Retry After Success")
    item = _pending_item(project, owner, "Once only.")
    accepted, punch = _accept(project, item, owner)
    with pytest.raises(WalkthroughError, match=WALKTHROUGH_ALREADY_REVIEWED):
        _accept(project, item, owner)
    db.session.expire_all()
    after = _counts(project.id)
    loaded = db.session.get(ProjectFinalWalkthroughItem, item.id)
    assert after == {"punches": 1, "events": 1, "created_events": 1}
    assert loaded.review_status == WALKTHROUGH_REVIEW_ACCEPTED
    assert loaded.punch_list_item_id == punch.id
    assert accepted.punch_list_item_id == punch.id


def test_concurrent_double_accept_creates_one_punch(app):
    owner, _membership = _make_owner()
    project = _add_project("Double Accept")
    item = _pending_item(project, owner, "Race item.")
    project_id = project.id
    item_id = item.id
    owner_id = owner.id
    errors = []
    results = []

    def worker():
        with app.app_context():
            try:
                accepted, punch = accept_walkthrough_item_to_punch_list(
                    project_id,
                    item_id,
                    owner_id,
                    work_source_type=PUNCH_LIST_SOURCE_OTHER,
                    organization_id=DEFAULT_ORGANIZATION_ID,
                )
                results.append((accepted.id, punch.id))
            except Exception as exc:
                errors.append(exc)

    threads = [threading.Thread(target=worker), threading.Thread(target=worker)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(40)
    db.session.expire_all()
    after = _counts(project_id)
    loaded = db.session.get(ProjectFinalWalkthroughItem, item_id)
    already = [
        exc
        for exc in errors
        if isinstance(exc, WalkthroughError) and WALKTHROUGH_ALREADY_REVIEWED in str(exc)
    ]
    assert after["punches"] == 1
    assert after["events"] == 1
    assert after["created_events"] == 1
    assert len(results) == 1
    assert len(already) == 1
    assert loaded.review_status == WALKTHROUGH_REVIEW_ACCEPTED
    assert loaded.punch_list_item_id == results[0][1]


def test_closed_project_accept_creates_no_punch(app):
    owner, _membership = _make_owner()
    project = _add_project("Closed Accept")
    item = _pending_item(project, owner, "After close.")
    close_project(project, owner)
    with pytest.raises(WalkthroughError, match=PROJECT_CLOSED_NEW_WORK):
        _accept(project, item, owner)
    db.session.expire_all()
    loaded = db.session.get(ProjectFinalWalkthroughItem, item.id)
    after = _counts(project.id)
    assert after == {"punches": 0, "events": 0, "created_events": 0}
    assert loaded.review_status == WALKTHROUGH_REVIEW_PENDING
    assert loaded.punch_list_item_id is None


def test_standalone_punch_create_complete_reopen_still_commit(app):
    owner, _membership = _make_owner()
    project = _add_project("Standalone Punch")
    item = create_punch_list_item(
        project,
        owner,
        description="Contractor item.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    db.session.expire_all()
    loaded = db.session.get(ProjectPunchListItem, item.id)
    assert loaded is not None
    assert loaded.origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR
    assert loaded.status == PUNCH_LIST_STATUS_OPEN
    complete_punch_list_item(project, loaded.id, owner)
    db.session.expire_all()
    loaded = db.session.get(ProjectPunchListItem, item.id)
    assert loaded.status == PUNCH_LIST_STATUS_COMPLETE
    reopen_punch_list_item(project, loaded.id, owner)
    db.session.expire_all()
    loaded = db.session.get(ProjectPunchListItem, item.id)
    assert loaded.status == PUNCH_LIST_STATUS_OPEN
    events = ProjectPunchListItemEvent.query.filter_by(
        punch_list_item_id=item.id
    ).count()
    assert events == 3


def test_walkthrough_punch_provenance_is_client_walkthrough(app):
    owner, _membership = _make_owner()
    project = _add_project("Provenance")
    item = _pending_item(project, owner, "Client wording.")
    _accepted, punch = _accept(project, item, owner)
    assert punch.origin_type == PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH
    assert punch.work_source_type == PUNCH_LIST_SOURCE_OTHER
    created = ProjectPunchListItemEvent.query.filter_by(
        punch_list_item_id=punch.id, event=PUNCH_LIST_EVENT_CREATED
    ).one()
    assert created.actor_user_id == owner.id
    contractor = create_punch_list_item(
        project,
        owner,
        description="Office wording.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    assert contractor.origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR
    assert ProjectPunchListItem.query.filter_by(project_id=project.id).count() == 2


def test_http_accept_then_retry_does_not_duplicate(app, client):
    owner, _membership = _make_owner()
    project = _add_project("HTTP Accept")
    item = _pending_item(project, owner, "Loose handle.")
    first = client.post(
        f"/projects/{project.id}/final-walkthrough/items/{item.id}/accept",
        data={"work_source_type": PUNCH_LIST_SOURCE_OTHER},
        follow_redirects=False,
    )
    second = client.post(
        f"/projects/{project.id}/final-walkthrough/items/{item.id}/accept",
        data={"work_source_type": PUNCH_LIST_SOURCE_OTHER},
        follow_redirects=False,
    )
    assert first.status_code == 302
    assert second.status_code == 302
    assert _counts(project.id)["punches"] == 1
    loaded = db.session.get(ProjectFinalWalkthroughItem, item.id)
    assert loaded.review_status == WALKTHROUGH_REVIEW_ACCEPTED
    assert ProjectPunchListItem.query.one().origin_type == PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH
