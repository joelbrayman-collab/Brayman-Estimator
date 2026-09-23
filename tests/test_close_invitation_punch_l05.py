"""PKG-L05 PROJECT CLOSE — invitation revocation + open Punch confirmation.

Synthetic file SQLite only. No live Project Close. No live invitation mutation.
No live Punch mutation. R06 expiry-on-GET is not redesigned here.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta

import pytest
from sqlalchemy.pool import NullPool

from app import create_app, db
from app.models import Client, Organization, Project, ProjectOperatingStateEvent
from app.models.final_walkthrough import (
    WALKTHROUGH_STATUS_EXPIRED,
    WALKTHROUGH_STATUS_OPEN,
    WALKTHROUGH_STATUS_RESPONDED,
    WALKTHROUGH_STATUS_REVOKED,
    ProjectFinalWalkthroughInvitation,
    ProjectFinalWalkthroughItem,
)
from app.models.project import OPERATING_EVENT_CLOSE, OPERATING_STATE_CLOSED
from app.models.punch_list import (
    PUNCH_LIST_SOURCE_OTHER,
    PUNCH_LIST_STATUS_OPEN,
    ProjectPunchListItem,
    ProjectPunchListItemEvent,
)
from app.models.user import UserMembership
from app.presentation import contractor_copy
from app.presentation.contractor_copy import (
    PROJECT_ALREADY_CLOSED,
    PROJECT_CLOSE_OPEN_PUNCH_REQUIRED,
    PROJECT_CLOSED_NEW_WORK,
    WALKTHROUGH_TOKEN_INVALID,
)
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_final_walkthrough import (
    BLOCK_TOKEN_INVALID,
    WalkthroughTokenError,
    create_walkthrough_invitation,
    resolve_walkthrough_access,
    submit_walkthrough_response,
    walkthrough_summary_copy,
)
from app.services.project_operating_lifecycle import (
    ProjectLifecycleError,
    ProjectLifecycleUnauthorizedError,
    close_project,
    reopen_project,
)
from app.services.project_punch_list import (
    create_punch_list_item,
    list_open_punch_list_items,
    project_has_open_punch_list_items,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import create_membership, create_user, ensure_office_user


def _app(tmp_path):
    db_path = tmp_path / "l05-close.db"
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "poolclass": NullPool,
            },
            "SECRET_KEY": "test-secret-l05-close",
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


def _add_project(name="L05 Close", *, organization_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(
        organization_id=organization_id,
        name=f"{name} Client",
        email="l05@example.com",
    )
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=organization_id,
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


def _open_punch(project, actor, description="Still open."):
    return create_punch_list_item(
        project,
        actor,
        description=description,
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )


def test_close_revokes_open_invitation(app):
    owner, _membership = _make_owner()
    project = _add_project("Revoke Open")
    issue = _issue(project, owner)
    closed = close_project(project, owner)
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    loaded = db.session.get(Project, project.id)
    assert closed.operating_state == OPERATING_STATE_CLOSED
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    assert invitation.status == WALKTHROUGH_STATUS_REVOKED
    assert _close_events(project.id) == 1


def test_revoke_failure_rolls_back_close(app, monkeypatch):
    owner, _membership = _make_owner()
    project = _add_project("Atomic Rollback")
    issue = _issue(project, owner)

    def boom(project_row, *, now):
        raise RuntimeError("forced revoke failure")

    monkeypatch.setattr(
        "app.services.project_final_walkthrough._revoke_open_invitations",
        boom,
    )
    with pytest.raises(RuntimeError, match="forced revoke failure"):
        close_project(project, owner)
    db.session.expire_all()
    loaded = db.session.get(Project, project.id)
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert loaded.operating_state != OPERATING_STATE_CLOSED
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert _close_events(project.id) == 0


def test_public_get_and_post_follow_revoked_token_law(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Revoked Public")
    issue = _issue(project, owner)
    close_project(project, owner)
    got = client.get(issue.path, follow_redirects=False)
    posted = client.post(
        issue.path,
        data={"item": ["Must not land."]},
        follow_redirects=False,
    )
    assert got.status_code == 404
    assert posted.status_code == 404
    assert "not available" in got.get_data(as_text=True)
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_REVOKED
    assert ProjectFinalWalkthroughItem.query.count() == 0
    with pytest.raises(WalkthroughTokenError) as exc:
        resolve_walkthrough_access(_credential(issue))
    assert exc.value.code == BLOCK_TOKEN_INVALID
    assert WALKTHROUGH_TOKEN_INVALID in str(exc.value)


def test_responded_invitation_and_items_remain_historical(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Keep Responded")
    issue = _issue(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Keep this item."]
    )
    close_project(project, owner)
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    item = ProjectFinalWalkthroughItem.query.one()
    assert invitation.status == WALKTHROUGH_STATUS_RESPONDED
    assert item.description == "Keep this item."
    response = client.get(issue.path, follow_redirects=False)
    assert response.status_code == 200
    assert contractor_copy.WALKTHROUGH_RECEIVED in response.get_data(as_text=True)


def test_expired_and_already_revoked_stay_terminal(app):
    owner, _membership = _make_owner()
    project = _add_project("Terminal States")
    expired_issue = _issue(project, owner)
    expired = expired_issue.invitation
    expired.status = WALKTHROUGH_STATUS_EXPIRED
    expired.expires_at = datetime.utcnow() - timedelta(days=1)
    db.session.commit()
    already_revoked = _issue(project, owner).invitation
    already_revoked.status = WALKTHROUGH_STATUS_REVOKED
    db.session.commit()
    still_open = _issue(project, owner)
    close_project(project, owner)
    db.session.expire_all()
    assert (
        db.session.get(ProjectFinalWalkthroughInvitation, expired.id).status
        == WALKTHROUGH_STATUS_EXPIRED
    )
    assert (
        db.session.get(ProjectFinalWalkthroughInvitation, already_revoked.id).status
        == WALKTHROUGH_STATUS_REVOKED
    )
    assert (
        db.session.get(ProjectFinalWalkthroughInvitation, still_open.invitation.id).status
        == WALKTHROUGH_STATUS_REVOKED
    )


def test_reopen_does_not_revive_and_new_invite_has_new_identity(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Reopen Identity")
    issue = _issue(project, owner)
    close_project(project, owner)
    reopen_project(project, owner)
    db.session.expire_all()
    old = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert old.status == WALKTHROUGH_STATUS_REVOKED
    hub = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert contractor_copy.WALKTHROUGH_STATE_REVOKED in hub
    assert contractor_copy.WALKTHROUGH_INVITE in hub
    assert contractor_copy.WALKTHROUGH_SEND_ANOTHER not in hub
    assert walkthrough_summary_copy(project) == contractor_copy.WALKTHROUGH_STATE_REVOKED
    with pytest.raises(WalkthroughTokenError) as exc:
        resolve_walkthrough_access(_credential(issue))
    assert exc.value.code == BLOCK_TOKEN_INVALID
    fresh = _issue(project, owner)
    assert fresh.lookup_key != issue.lookup_key
    assert fresh.secret != issue.secret
    assert fresh.invitation.id != old.id
    assert fresh.invitation.status == WALKTHROUGH_STATUS_OPEN
    access = resolve_walkthrough_access(_credential(fresh))
    submitted = submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["New invite item."]
    )
    assert submitted.status == WALKTHROUGH_STATUS_RESPONDED
    with pytest.raises(WalkthroughTokenError):
        resolve_walkthrough_access(_credential(issue))
    posted = client.post(
        issue.path,
        data={"item": ["Old credential after reopen."]},
        follow_redirects=False,
    )
    assert posted.status_code == 404
    assert ProjectFinalWalkthroughItem.query.filter_by(
        invitation_id=old.id
    ).count() == 0


def test_zero_open_punch_close_needs_no_extra_confirmation(app, client):
    owner, _membership = _make_owner()
    project = _add_project("No Punch")
    html = client.get(f"/projects/{project.id}/close").get_data(as_text=True)
    assert contractor_copy.PROJECT_CLOSE_CONFIRM_TITLE in html
    assert "Punch List" not in html
    assert 'name="confirm_open_punch"' not in html
    posted = client.post(f"/projects/{project.id}/close", follow_redirects=False)
    assert posted.status_code == 302
    db.session.refresh(project)
    assert project.operating_state == OPERATING_STATE_CLOSED
    assert _close_events(project.id) == 1


def test_close_get_warns_with_open_punch_count(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Warn Punch")
    _open_punch(project, owner, "First open.")
    _open_punch(project, owner, "Second open.")
    response = client.get(f"/projects/{project.id}/close")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert contractor_copy.PROJECT_CLOSE_OPEN_PUNCH_WARNING in html
    assert contractor_copy.PROJECT_CLOSE_OPEN_PUNCH_CONFIRM in html
    assert 'data-open-punch-count="2"' in html
    assert "Open Punch List items: 2." in html
    assert 'name="confirm_open_punch"' in html
    db.session.refresh(project)
    assert project.operating_state != OPERATING_STATE_CLOSED


def test_unconfirmed_open_punch_does_not_close_revoke_or_mutate_punch(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Need Confirm")
    punch = _open_punch(project, owner, "Must stay open.")
    prior_updated = punch.status
    issue = _issue(project, owner)
    with pytest.raises(ProjectLifecycleError, match=PROJECT_CLOSE_OPEN_PUNCH_REQUIRED):
        close_project(project, owner)
    db.session.expire_all()
    loaded = db.session.get(Project, project.id)
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    item = db.session.get(ProjectPunchListItem, punch.id)
    assert loaded.operating_state != OPERATING_STATE_CLOSED
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert item.status == PUNCH_LIST_STATUS_OPEN
    assert item.description == "Must stay open."
    assert _close_events(project.id) == 0
    assert ProjectPunchListItemEvent.query.filter_by(
        punch_list_item_id=punch.id
    ).count() == 1
    posted = client.post(f"/projects/{project.id}/close", follow_redirects=False)
    assert posted.status_code == 400
    html = posted.get_data(as_text=True)
    assert PROJECT_CLOSE_OPEN_PUNCH_REQUIRED in html
    db.session.expire_all()
    assert db.session.get(Project, project.id).operating_state != OPERATING_STATE_CLOSED
    assert (
        db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id).status
        == WALKTHROUGH_STATUS_OPEN
    )
    assert db.session.get(ProjectPunchListItem, punch.id).status == prior_updated


def test_confirmed_close_with_open_punch_succeeds_and_revokes(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Confirmed Punch")
    punch = _open_punch(project, owner, "Remains open after close.")
    issue = _issue(project, owner)
    closed = close_project(project, owner, confirm_open_punch=True)
    db.session.expire_all()
    item = db.session.get(ProjectPunchListItem, punch.id)
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert closed.operating_state == OPERATING_STATE_CLOSED
    assert item.status == PUNCH_LIST_STATUS_OPEN
    assert item.description == "Remains open after close."
    assert invitation.status == WALKTHROUGH_STATUS_REVOKED
    assert project_has_open_punch_list_items(closed) is True
    assert len(list_open_punch_list_items(closed)) == 1
    reopen_project(project, owner)
    punch2 = _open_punch(project, owner, "Second still open.")
    posted = client.post(
        f"/projects/{project.id}/close",
        data={"confirm_open_punch": "1"},
        follow_redirects=False,
    )
    assert posted.status_code == 302
    db.session.expire_all()
    assert db.session.get(Project, project.id).operating_state == OPERATING_STATE_CLOSED
    assert db.session.get(ProjectPunchListItem, punch.id).status == PUNCH_LIST_STATUS_OPEN
    assert db.session.get(ProjectPunchListItem, punch2.id).status == PUNCH_LIST_STATUS_OPEN


def test_lost_close_predicate_does_not_revoke(app):
    owner, _membership = _make_owner()
    project = _add_project("Lost Predicate")
    issue = _issue(project, owner)
    project.operating_state = OPERATING_STATE_CLOSED
    db.session.commit()
    with pytest.raises(ProjectLifecycleError, match=PROJECT_ALREADY_CLOSED):
        close_project(project, owner)
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert _close_events(project.id) == 0


def test_concurrent_close_one_transition_and_one_revoke(app):
    owner, _membership = _make_owner()
    project = _add_project("Double Close")
    issue = _issue(project, owner)
    project_id = project.id
    owner_id = owner.id
    invitation_id = issue.invitation.id
    start = threading.Barrier(2)
    results = []

    def attempt(label):
        with app.app_context():
            start.wait(10)
            try:
                close_project(project_id, owner_id)
                results.append(label)
            except Exception as exc:
                results.append((label, type(exc).__name__, str(exc)))

    threads = [
        threading.Thread(target=attempt, args=("first",)),
        threading.Thread(target=attempt, args=("second",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(40)
    db.session.expire_all()
    loaded = db.session.get(Project, project_id)
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, invitation_id)
    wins = [row for row in results if row in ("first", "second")]
    losses = [row for row in results if isinstance(row, tuple)]
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    assert _close_events(project_id) == 1
    assert invitation.status == WALKTHROUGH_STATUS_REVOKED
    assert len(wins) == 1
    assert len(losses) == 1
    assert PROJECT_ALREADY_CLOSED in losses[0][2]


def test_unauthorized_actor_cannot_close_or_revoke(app):
    ordinary = create_user(
        email="l05-ordinary@example.com",
        password="ordinary-password",
        display_name="Ordinary",
    )
    create_membership(ordinary)
    db.session.commit()
    owner, _membership = _make_owner()
    project = _add_project("No Close")
    issue = _issue(project, owner)
    punch = _open_punch(project, owner)
    with pytest.raises(ProjectLifecycleUnauthorizedError):
        close_project(project, ordinary, confirm_open_punch=True)
    db.session.expire_all()
    loaded = db.session.get(Project, project.id)
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    item = db.session.get(ProjectPunchListItem, punch.id)
    assert loaded.operating_state != OPERATING_STATE_CLOSED
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert item.status == PUNCH_LIST_STATUS_OPEN
    assert _close_events(project.id) == 0


def test_tenancy_close_does_not_expose_foreign_punch_or_walkthrough(app):
    owner, _membership = _make_owner()
    foreign_org = Organization(
        id="ORG-L05-B",
        legal_name="Foreign L05 Ltd.",
        display_name="Foreign L05",
        primary_address="200 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(foreign_org)
    db.session.commit()
    home = _add_project("Home Close")
    foreign = _add_project("Foreign Close", organization_id="ORG-L05-B")
    home_issue = _issue(home, owner)
    _open_punch(home, owner, "Home punch.")
    with pytest.raises(ProjectLifecycleError, match="Project not found"):
        close_project(foreign, owner, confirm_open_punch=True)
    db.session.expire_all()
    assert db.session.get(Project, home.id).operating_state != OPERATING_STATE_CLOSED
    assert db.session.get(Project, foreign.id).operating_state != OPERATING_STATE_CLOSED
    assert (
        db.session.get(
            ProjectFinalWalkthroughInvitation, home_issue.invitation.id
        ).status
        == WALKTHROUGH_STATUS_OPEN
    )


def test_public_submit_on_closed_still_fail_closed(app):
    owner, _membership = _make_owner()
    project = _add_project("R05 Remainder")
    issue = _issue(project, owner)
    close_project(project, owner)
    with pytest.raises(WalkthroughTokenError):
        resolve_walkthrough_access(_credential(issue))
    assert ProjectFinalWalkthroughItem.query.count() == 0
    assert PROJECT_CLOSED_NEW_WORK
