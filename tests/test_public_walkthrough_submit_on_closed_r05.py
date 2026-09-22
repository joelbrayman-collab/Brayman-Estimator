"""R05 PUBLIC-WALKTHROUGH-SUBMIT-ON-CLOSED.

Synthetic file SQLite only. No live Project Close. No live invitation mutation.
Token GET / expiry is R06 and is asserted unchanged, not redesigned.
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Project, ProjectOperatingStateEvent
from app.models.final_walkthrough import (
    WALKTHROUGH_STATUS_OPEN,
    WALKTHROUGH_STATUS_RESPONDED,
    ProjectFinalWalkthroughInvitation,
    ProjectFinalWalkthroughItem,
)
from app.models.project import OPERATING_EVENT_CLOSE, OPERATING_STATE_CLOSED
from app.models.punch_list import PUNCH_LIST_SOURCE_OTHER
from app.models.user import UserMembership
from app.presentation.contractor_copy import PROJECT_CLOSED_NEW_WORK
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_final_walkthrough import (
    WalkthroughError,
    create_walkthrough_invitation,
    resolve_walkthrough_access,
    submit_walkthrough_response,
)
from app.services.project_operating_lifecycle import (
    ProjectClosedError,
    ProjectLifecycleUnauthorizedError,
    claim_active_project_for_write,
    close_project,
    reopen_project,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import create_membership, create_user, ensure_office_user


def _app(tmp_path):
    db_path = tmp_path / "r05-walkthrough.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-r05-walkthrough",
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


def _add_project(name="R05 Walkthrough"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="r05@example.com",
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


def _issue(project, actor):
    return create_walkthrough_invitation(
        project, actor, organization_id=project.organization_id
    )


def _credential(issue):
    return f"{issue.lookup_key}.{issue.secret}"


def _close_events(project_id):
    return ProjectOperatingStateEvent.query.filter_by(
        project_id=project_id, event=OPERATING_EVENT_CLOSE
    ).count()


def test_active_public_submit_still_succeeds(app):
    owner, _membership = _make_owner()
    project = _add_project("Active Submit")
    issue = _issue(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    invitation = submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Paint touch-up."]
    )
    assert invitation.status == WALKTHROUGH_STATUS_RESPONDED
    assert ProjectFinalWalkthroughItem.query.filter_by(project_id=project.id).count() == 1
    db.session.refresh(project)
    assert project.operating_state != OPERATING_STATE_CLOSED


def test_active_nothing_to_add_still_succeeds(app):
    owner, _membership = _make_owner()
    project = _add_project("Active Nothing")
    issue = _issue(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    invitation = submit_walkthrough_response(
        access, nothing_to_add=True, item_descriptions=[]
    )
    assert invitation.status == WALKTHROUGH_STATUS_RESPONDED
    assert ProjectFinalWalkthroughItem.query.filter_by(project_id=project.id).count() == 0


def test_sequential_closed_public_submit_fails(app):
    owner, _membership = _make_owner()
    project = _add_project("Seq Closed Items")
    issue = _issue(project, owner)
    close_project(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    with pytest.raises(WalkthroughError, match=PROJECT_CLOSED_NEW_WORK):
        submit_walkthrough_response(
            access, nothing_to_add=False, item_descriptions=["After close item."]
        )
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert ProjectFinalWalkthroughItem.query.filter_by(project_id=project.id).count() == 0
    assert _close_events(project.id) == 1


def test_sequential_closed_nothing_to_add_fails(app):
    owner, _membership = _make_owner()
    project = _add_project("Seq Closed Nothing")
    issue = _issue(project, owner)
    close_project(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    with pytest.raises(WalkthroughError, match=PROJECT_CLOSED_NEW_WORK):
        submit_walkthrough_response(access, nothing_to_add=True, item_descriptions=[])
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert invitation.response_mode is None
    assert _close_events(project.id) == 1


def test_token_get_after_close_does_not_expire_or_respond(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Get After Close")
    issue = _issue(project, owner)
    close_project(project, owner)
    response = client.get(issue.path, follow_redirects=False)
    assert response.status_code == 200
    invitation = ProjectFinalWalkthroughInvitation.query.one()
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert invitation.response_mode is None


def test_http_submit_after_close_fails_closed(app, client):
    owner, _membership = _make_owner()
    project = _add_project("HTTP Closed")
    issue = _issue(project, owner)
    close_project(project, owner)
    posted = client.post(
        issue.path,
        data={"item": ["After close HTTP."]},
        follow_redirects=False,
    )
    assert posted.status_code == 400
    assert PROJECT_CLOSED_NEW_WORK in posted.get_data(as_text=True)
    invitation = ProjectFinalWalkthroughInvitation.query.one()
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert ProjectFinalWalkthroughItem.query.count() == 0


def test_reopen_preserves_still_open_invitation_submit(app):
    owner, _membership = _make_owner()
    project = _add_project("Reopen Submit")
    issue = _issue(project, owner)
    close_project(project, owner)
    reopen_project(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    invitation = submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["After reopen."]
    )
    assert invitation.status == WALKTHROUGH_STATUS_RESPONDED
    assert ProjectFinalWalkthroughItem.query.filter_by(project_id=project.id).count() == 1


def test_contractor_invitation_issue_remains_fail_closed_on_closed(app):
    owner, _membership = _make_owner()
    project = _add_project("No New Invite")
    close_project(project, owner)
    with pytest.raises(WalkthroughError, match=PROJECT_CLOSED_NEW_WORK):
        create_walkthrough_invitation(project, owner)


def test_contractor_accept_remains_fail_closed_on_closed(app):
    owner, _membership = _make_owner()
    project = _add_project("No Accept")
    issue = _issue(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Needs punch."]
    )
    item = ProjectFinalWalkthroughItem.query.one()
    close_project(project, owner)
    from app.services.project_final_walkthrough import accept_walkthrough_item_to_punch_list

    with pytest.raises(WalkthroughError, match=PROJECT_CLOSED_NEW_WORK):
        accept_walkthrough_item_to_punch_list(
            project,
            item.id,
            owner,
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )


def test_unauthorized_actor_still_cannot_close(app):
    ordinary = create_user(
        email="r05-ordinary@example.com",
        password="ordinary-password",
        display_name="Ordinary",
    )
    create_membership(ordinary)
    db.session.commit()
    project = _add_project("No Close")
    with pytest.raises(ProjectLifecycleUnauthorizedError):
        close_project(project, ordinary)
    db.session.refresh(project)
    assert project.operating_state != OPERATING_STATE_CLOSED
    assert _close_events(project.id) == 0


def _install_stale_window(monkeypatch, started, close_done):
    original = claim_active_project_for_write

    def delayed(project, error_cls=ProjectClosedError):
        started.set()
        if not close_done.wait(20):
            raise AssertionError("Close did not finish during the TOCTOU window")
        return original(project, error_cls)

    monkeypatch.setattr(
        "app.services.project_operating_lifecycle.claim_active_project_for_write",
        delayed,
    )


def _race_public_submit(app, monkeypatch, *, nothing_to_add, descriptions):
    owner, _membership = _make_owner()
    project = _add_project("Race Submit")
    issue = _issue(project, owner)
    project_id = project.id
    owner_id = owner.id
    credential = _credential(issue)
    invitation_id = issue.invitation.id
    started = threading.Event()
    close_done = threading.Event()
    errors = []
    _install_stale_window(monkeypatch, started, close_done)

    def closer():
        with app.app_context():
            if not started.wait(20):
                errors.append(("close", AssertionError("writer never entered claim")))
                close_done.set()
                return
            try:
                close_project(project_id, owner_id)
            except Exception as exc:
                errors.append(("close", exc))
            finally:
                close_done.set()

    def writer():
        with app.app_context():
            access = resolve_walkthrough_access(credential)
            submit_walkthrough_response(
                access,
                nothing_to_add=nothing_to_add,
                item_descriptions=descriptions,
            )

    def run_writer():
        try:
            writer()
        except Exception as exc:
            errors.append(("write", exc))

    threads = [threading.Thread(target=closer), threading.Thread(target=run_writer)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(40)
    db.session.expire_all()
    loaded = db.session.get(Project, project_id)
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, invitation_id)
    write_errors = [exc for kind, exc in errors if kind == "write"]
    close_errors = [exc for kind, exc in errors if kind == "close"]
    return {
        "project": loaded,
        "invitation": invitation,
        "items": ProjectFinalWalkthroughItem.query.filter_by(project_id=project_id).count(),
        "events": _close_events(project_id),
        "write_errors": write_errors,
        "close_errors": close_errors,
    }


def test_concurrent_close_vs_public_item_submit_fails_closed(app, monkeypatch):
    result = _race_public_submit(
        app, monkeypatch, nothing_to_add=False, descriptions=["Raced item."]
    )
    assert result["close_errors"] == []
    assert result["project"].operating_state == OPERATING_STATE_CLOSED
    assert result["events"] == 1
    assert result["invitation"].status == WALKTHROUGH_STATUS_OPEN
    assert result["items"] == 0
    assert result["write_errors"]
    assert any(PROJECT_CLOSED_NEW_WORK in str(exc) for exc in result["write_errors"])


def test_concurrent_close_vs_nothing_to_add_fails_closed(app, monkeypatch):
    result = _race_public_submit(
        app, monkeypatch, nothing_to_add=True, descriptions=[]
    )
    assert result["close_errors"] == []
    assert result["project"].operating_state == OPERATING_STATE_CLOSED
    assert result["events"] == 1
    assert result["invitation"].status == WALKTHROUGH_STATUS_OPEN
    assert result["invitation"].response_mode is None
    assert result["items"] == 0
    assert result["write_errors"]
    assert any(PROJECT_CLOSED_NEW_WORK in str(exc) for exc in result["write_errors"])
