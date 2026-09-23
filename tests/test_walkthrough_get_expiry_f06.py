"""PKG-F06 R06 — public Walkthrough GET expiry is read-only for lifecycle.

Synthetic file SQLite only. No live invitation mutation. No live Project Close.
Access-attempt / rate-limit security instrumentation is preserved.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.final_walkthrough import (
    WALKTHROUGH_ACCESS_FAIL,
    WALKTHROUGH_ACCESS_OK,
    WALKTHROUGH_ACCESS_RATE_LIMITED,
    WALKTHROUGH_STATUS_EXPIRED,
    WALKTHROUGH_STATUS_OPEN,
    WALKTHROUGH_STATUS_RESPONDED,
    WALKTHROUGH_STATUS_REVOKED,
    ProjectFinalWalkthroughAccessAttempt,
    ProjectFinalWalkthroughInvitation,
    ProjectFinalWalkthroughItem,
)
from app.models.project import OPERATING_STATE_CLOSED
from app.models.user import UserMembership
from app.presentation.contractor_copy import WALKTHROUGH_TOKEN_EXPIRED
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_final_walkthrough import (
    BLOCK_TOKEN_EXPIRED,
    BLOCK_TOKEN_INVALID,
    BLOCK_TOKEN_RATE_LIMITED,
    WalkthroughTokenError,
    create_walkthrough_invitation,
    resolve_walkthrough_access,
    submit_walkthrough_response,
)
from app.services.project_operating_lifecycle import close_project
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user


def _app(*, fail_limit=8):
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-f06-expiry",
            "WTF_CSRF_ENABLED": False,
            "WALKTHROUGH_TOKEN_FAIL_LIMIT": fail_limit,
            "WALKTHROUGH_TOKEN_FAIL_WINDOW_SECONDS": 900,
        }
    )


@pytest.fixture
def app():
    application = _app()
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


def _make_owner():
    user = ensure_office_user()
    membership = UserMembership.query.filter_by(
        user_id=user.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        is_active=True,
    ).one()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, user)
    return user, membership


def _add_project(name="F06 Walkthrough"):
    client_row = Client(
        organization_id=DEFAULT_ORGANIZATION_ID,
        name=f"{name} Client",
        email="f06@example.com",
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


def _set_expires_at(invitation, when):
    invitation.expires_at = when
    db.session.commit()
    db.session.refresh(invitation)
    return invitation


def _fail_attempts(lookup_key):
    return ProjectFinalWalkthroughAccessAttempt.query.filter_by(
        presented_lookup_key=lookup_key,
        outcome=WALKTHROUGH_ACCESS_FAIL,
    ).count()


def test_open_future_get_remains_usable_and_open(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Future Get")
    issue = _issue(project, owner)
    response = client.get(issue.path, follow_redirects=False)
    assert response.status_code == 200
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    ok = ProjectFinalWalkthroughAccessAttempt.query.filter_by(
        presented_lookup_key=issue.lookup_key,
        outcome=WALKTHROUGH_ACCESS_OK,
    ).count()
    assert ok >= 1


def test_open_past_get_fails_expired_and_stays_open(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Past Get")
    issue = _issue(project, owner)
    _set_expires_at(issue.invitation, datetime.utcnow() - timedelta(minutes=5))
    response = client.get(issue.path, follow_redirects=False)
    html = response.get_data(as_text=True)
    assert response.status_code == 410
    assert "not available" in html
    assert WALKTHROUGH_TOKEN_EXPIRED in html or "expired" in html.lower()
    assert "because you opened" not in html.lower()
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert _fail_attempts(issue.lookup_key) >= 1
    with pytest.raises(WalkthroughTokenError) as exc:
        resolve_walkthrough_access(_credential(issue))
    assert exc.value.code == BLOCK_TOKEN_EXPIRED
    db.session.expire_all()
    assert (
        db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id).status
        == WALKTHROUGH_STATUS_OPEN
    )


def test_repeated_expired_get_does_not_persist_expired(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Repeat Get")
    issue = _issue(project, owner)
    _set_expires_at(issue.invitation, datetime.utcnow() - timedelta(hours=1))
    first = client.get(issue.path, follow_redirects=False)
    second = client.get(issue.path, follow_redirects=False)
    third = client.get(issue.path, follow_redirects=False)
    assert first.status_code == 410
    assert second.status_code == 410
    assert third.status_code == 410
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert _fail_attempts(issue.lookup_key) >= 3


def test_expired_post_fails_closed_without_prior_get(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Past Post")
    issue = _issue(project, owner)
    _set_expires_at(issue.invitation, datetime.utcnow() - timedelta(minutes=2))
    posted = client.post(
        issue.path,
        data={"item": ["Must not land."]},
        follow_redirects=False,
    )
    assert posted.status_code == 410
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert invitation.response_mode is None
    assert ProjectFinalWalkthroughItem.query.count() == 0


def test_stale_resolved_access_cannot_submit_after_clock_expiry(app):
    owner, _membership = _make_owner()
    project = _add_project("Stale Access")
    issue = _issue(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    _set_expires_at(access.invitation, datetime.utcnow() - timedelta(seconds=1))
    with pytest.raises(WalkthroughTokenError) as exc:
        submit_walkthrough_response(
            access, nothing_to_add=False, item_descriptions=["Late item."]
        )
    assert exc.value.code == BLOCK_TOKEN_EXPIRED
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert ProjectFinalWalkthroughItem.query.count() == 0


def test_persisted_expired_row_follows_existing_expired_law(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Persisted Expired")
    issue = _issue(project, owner)
    invitation = issue.invitation
    invitation.status = WALKTHROUGH_STATUS_EXPIRED
    invitation.expires_at = datetime.utcnow() - timedelta(days=1)
    db.session.commit()
    got = client.get(issue.path, follow_redirects=False)
    posted = client.post(
        issue.path,
        data={"nothing_to_add": "1"},
        follow_redirects=False,
    )
    assert got.status_code == 410
    assert posted.status_code == 410
    db.session.expire_all()
    loaded = db.session.get(ProjectFinalWalkthroughInvitation, invitation.id)
    assert loaded.status == WALKTHROUGH_STATUS_EXPIRED


def test_responded_is_not_rewritten_to_expired(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Keep Responded")
    issue = _issue(project, owner)
    access = resolve_walkthrough_access(_credential(issue))
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Keep this."]
    )
    _set_expires_at(issue.invitation, datetime.utcnow() - timedelta(days=1))
    got = client.get(issue.path, follow_redirects=False)
    assert got.status_code == 200
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_RESPONDED
    assert ProjectFinalWalkthroughItem.query.one().description == "Keep this."


def test_revoked_is_not_rewritten_to_expired(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Keep Revoked")
    issue = _issue(project, owner)
    close_project(project, owner)
    _set_expires_at(issue.invitation, datetime.utcnow() - timedelta(days=1))
    got = client.get(issue.path, follow_redirects=False)
    assert got.status_code == 404
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_REVOKED
    with pytest.raises(WalkthroughTokenError) as exc:
        resolve_walkthrough_access(_credential(issue))
    assert exc.value.code == BLOCK_TOKEN_INVALID


def test_close_revokes_unexpired_open_invitation(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Close Unexpired")
    issue = _issue(project, owner)
    close_project(project, owner)
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    loaded = db.session.get(Project, project.id)
    assert loaded.operating_state == OPERATING_STATE_CLOSED
    assert invitation.status == WALKTHROUGH_STATUS_REVOKED
    got = client.get(issue.path, follow_redirects=False)
    assert got.status_code == 404


def test_close_revokes_clock_expired_open_invitation(app, client):
    owner, _membership = _make_owner()
    project = _add_project("Close Clock Expired")
    issue = _issue(project, owner)
    _set_expires_at(issue.invitation, datetime.utcnow() - timedelta(hours=3))
    close_project(project, owner)
    db.session.expire_all()
    invitation = db.session.get(ProjectFinalWalkthroughInvitation, issue.invitation.id)
    assert invitation.status == WALKTHROUGH_STATUS_REVOKED
    got = client.get(issue.path, follow_redirects=False)
    posted = client.post(
        issue.path,
        data={"item": ["After close expired."]},
        follow_redirects=False,
    )
    assert got.status_code == 404
    assert posted.status_code == 404
    assert ProjectFinalWalkthroughItem.query.count() == 0


def test_rate_limiting_still_blocks_after_fail_threshold():
    application = _app(fail_limit=2)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        http = application.test_client()
        first = http.get("/walkthrough/not-a-token", follow_redirects=False)
        second = http.get("/walkthrough/still-not-valid", follow_redirects=False)
        third = http.get("/walkthrough/rate-limited-now", follow_redirects=False)
        assert first.status_code == 404
        assert second.status_code == 404
        assert third.status_code == 429
        limited = ProjectFinalWalkthroughAccessAttempt.query.filter_by(
            outcome=WALKTHROUGH_ACCESS_RATE_LIMITED
        ).count()
        assert limited >= 1
        db.session.remove()
        db.drop_all()
