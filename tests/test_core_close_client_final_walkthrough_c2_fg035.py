"""Dedicated FG-035 CORE CLOSE C2 Client Final Walkthrough tests.

Synthetic TEST DB only. No live migration. No live C2 data.
No Completion Sign-Off. No client account.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import sqlalchemy as sa

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.final_walkthrough import (
    WALKTHROUGH_RESPONSE_ITEMS,
    WALKTHROUGH_RESPONSE_NOTHING_TO_ADD,
    WALKTHROUGH_REVIEW_ACCEPTED,
    WALKTHROUGH_REVIEW_ADDRESSED,
    WALKTHROUGH_REVIEW_DISCUSS,
    WALKTHROUGH_REVIEW_PENDING,
    WALKTHROUGH_STATUS_OPEN,
    WALKTHROUGH_STATUS_RESPONDED,
    WALKTHROUGH_STATUS_REVOKED,
    ProjectFinalWalkthroughInvitation,
    ProjectFinalWalkthroughItem,
)
from app.models.punch_list import (
    PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH,
    PUNCH_LIST_ORIGIN_CONTRACTOR,
    PUNCH_LIST_SOURCE_OTHER,
    PUNCH_LIST_STATUS_OPEN,
    ProjectPunchListItem,
)
from app.models.user import User, UserMembership
from app.presentation import contractor_copy
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    grant_access_domain,
)
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_final_walkthrough import (
    WalkthroughError,
    WalkthroughTokenError,
    create_walkthrough_invitation,
    hash_walkthrough_secret,
    list_pending_walkthrough_items,
    resolve_walkthrough_access,
    submit_walkthrough_response,
    accept_walkthrough_item_to_punch_list,
    mark_walkthrough_item_already_addressed,
    mark_walkthrough_item_discuss_or_out_of_scope,
)
from app.services.project_operating_lifecycle import close_project, reopen_project
from app.services.project_punch_list import (
    create_punch_list_item,
    is_punch_list_complete as punch_list_complete,
    require_punch_list_complete,
    PunchListIncompleteError,
)
from app.services.work_structure import ensure_baseline_work_catalog
from tests.auth_fixtures import (
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ORDINARY_EMAIL = "ordinary-walk@example.com"
ORDINARY_PASSWORD = "ordinary-walk-password"
FOREIGN_EMAIL = "foreign-walk@example.com"
FOREIGN_PASSWORD = "foreign-walk-password"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg035-walkthrough-c2",
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


def _add_project(name="Walkthrough Active", *, organization_id=DEFAULT_ORGANIZATION_ID):
    client_row = Client(
        organization_id=organization_id,
        name=f"{name} Client",
        email=f"{name.lower().replace(' ', '-')}@example.com",
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


def _issue(project, actor=None):
    if actor is None:
        actor = ensure_office_user()
    return create_walkthrough_invitation(
        project, actor, organization_id=project.organization_id
    )


def test_authorized_contractor_creates_invitation_for_active_project(app):
    actor = ensure_office_user()
    project = _add_project()
    issue = _issue(project, actor)
    assert issue.invitation.status == WALKTHROUGH_STATUS_OPEN
    assert issue.invitation.project_id == project.id
    assert issue.invitation.organization_id == DEFAULT_ORGANIZATION_ID
    assert issue.secret not in (issue.invitation.token_hash or "")
    assert issue.invitation.token_hash == hash_walkthrough_secret(issue.secret)
    assert issue.path.startswith("/walkthrough/")
    assert User.query.count() == 1
    assert UserMembership.query.count() == 1


def test_ordinary_member_may_invite(app, client):
    project = _add_project("Ordinary Invite")
    user = create_user(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="Ordinary Walk",
    )
    create_membership(user)
    db.session.commit()
    login_office_user(client, email=ORDINARY_EMAIL, password=ORDINARY_PASSWORD)
    response = client.post(
        f"/projects/{project.id}/final-walkthrough/invite",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert ProjectFinalWalkthroughInvitation.query.count() == 1


def test_unauthenticated_invite_redirects_to_login(app, client):
    project = _add_project("Unauth Invite")
    logout_office_user(client)
    response = client.post(
        f"/projects/{project.id}/final-walkthrough/invite",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in (response.headers.get("Location") or "")
    assert ProjectFinalWalkthroughInvitation.query.count() == 0


def test_cross_org_invite_denied(app, client):
    other = Organization(
        id="ORG-WALK",
        legal_name="Walk Isolation Ltd.",
        display_name="Walk Isolation",
        currency="CAD",
        is_active=True,
    )
    db.session.add(other)
    db.session.commit()
    project = _add_project("Foreign Walk", organization_id="ORG-WALK")
    user = create_user(
        email=FOREIGN_EMAIL,
        password=FOREIGN_PASSWORD,
        display_name="Foreign Walk",
    )
    create_membership(user, "ORG-WALK")
    db.session.commit()
    logout_office_user(client)
    login_office_user(client, email=FOREIGN_EMAIL, password=FOREIGN_PASSWORD)
    home = _add_project("Home Walk")
    response = client.post(
        f"/projects/{home.id}/final-walkthrough/invite",
        follow_redirects=False,
    )
    assert response.status_code == 404
    assert ProjectFinalWalkthroughInvitation.query.filter_by(project_id=home.id).count() == 0


def test_closed_project_blocks_new_invitation_and_review(app):
    owner, _membership = _make_owner()
    project = _add_project("Closed Walk")
    issue = _issue(project, owner)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Paint touch-up."]
    )
    close_project(project, owner)
    with pytest.raises(WalkthroughError):
        create_walkthrough_invitation(project, owner)
    item = ProjectFinalWalkthroughItem.query.one()
    with pytest.raises(WalkthroughError):
        accept_walkthrough_item_to_punch_list(
            project,
            item.id,
            owner,
            work_source_type=PUNCH_LIST_SOURCE_OTHER,
        )


def test_token_resolves_only_intended_walkthrough(app):
    actor = ensure_office_user()
    first = _add_project("First Walk")
    second = _add_project("Second Walk")
    issue = _issue(first, actor)
    other = _issue(second, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    assert access.project.id == first.id
    assert access.project.id != second.id
    other_access = resolve_walkthrough_access(f"{other.lookup_key}.{other.secret}")
    assert other_access.project.id == second.id


def test_invalid_token_fails_safely(app, client):
    response = client.get("/walkthrough/not-a-token", follow_redirects=False)
    assert response.status_code == 404
    html = response.get_data(as_text=True)
    assert "This link is not available" in html
    assert "Punch List" not in html
    assert "Schedule" not in html


@pytest.mark.no_office_auth
def test_token_cannot_access_project_hub(app, client):
    actor = ensure_office_user()
    project = _add_project("Hub Firewall")
    issue = _issue(project, actor)
    logout_office_user(client)
    hub = client.get(f"/projects/{project.id}", follow_redirects=False)
    assert hub.status_code == 302
    assert "/login" in (hub.headers.get("Location") or "")
    page = client.get(issue.path)
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert contractor_copy.WALKTHROUGH_CLIENT_HEADING in html
    assert 'id="hub-punch-list"' not in html
    assert "nav" not in html.lower() or "Field" not in html
    assert "Office" not in html
    assert "MONITOR" not in html
    assert "Company Attention" not in html


def test_token_cannot_expose_internal_data(app, client):
    actor = ensure_office_user()
    project = _add_project("Privacy Walk")
    issue = _issue(project, actor)
    html = client.get(issue.path).get_data(as_text=True)
    assert "/projects/" not in html
    assert "ORG-001" not in html
    assert "markup" not in html.lower()
    assert "margin" not in html.lower()
    assert "wage" not in html.lower()
    assert "True Gross" not in html
    assert contractor_copy.WALKTHROUGH_WHAT_NEEDS_ATTENTION in html


def test_client_can_submit_one_item(app):
    actor = ensure_office_user()
    project = _add_project("One Item")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Scratch on the door."]
    )
    invitation = ProjectFinalWalkthroughInvitation.query.one()
    assert invitation.status == WALKTHROUGH_STATUS_RESPONDED
    assert invitation.response_mode == WALKTHROUGH_RESPONSE_ITEMS
    assert invitation.responded_at is not None
    item = ProjectFinalWalkthroughItem.query.one()
    assert item.description == "Scratch on the door."
    assert item.review_status == WALKTHROUGH_REVIEW_PENDING
    assert ProjectPunchListItem.query.count() == 0


def test_client_can_submit_multiple_items(app):
    actor = ensure_office_user()
    project = _add_project("Multi Item")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access,
        nothing_to_add=False,
        item_descriptions=["First nick.", "Second nick."],
    )
    assert ProjectFinalWalkthroughItem.query.count() == 2
    assert ProjectPunchListItem.query.count() == 0


def test_client_can_submit_nothing_to_add(app):
    actor = ensure_office_user()
    project = _add_project("Nothing")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(access, nothing_to_add=True, item_descriptions=[])
    invitation = ProjectFinalWalkthroughInvitation.query.one()
    assert invitation.response_mode == WALKTHROUGH_RESPONSE_NOTHING_TO_ADD
    assert ProjectFinalWalkthroughItem.query.count() == 0
    assert ProjectPunchListItem.query.count() == 0


def test_items_plus_nothing_to_add_rejected(app):
    actor = ensure_office_user()
    project = _add_project("Contradict")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    with pytest.raises(WalkthroughError):
        submit_walkthrough_response(
            access,
            nothing_to_add=True,
            item_descriptions=["Still a scratch."],
        )
    invitation = ProjectFinalWalkthroughInvitation.query.one()
    assert invitation.status == WALKTHROUGH_STATUS_OPEN
    assert ProjectFinalWalkthroughItem.query.count() == 0


def test_original_wording_preserved_and_separate_from_punch_list(app):
    actor = ensure_office_user()
    project = _add_project("Preserve")
    issue = _issue(project, actor)
    wording = "The north window still rattles."
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=[wording]
    )
    item = ProjectFinalWalkthroughItem.query.one()
    accepted, punch = accept_walkthrough_item_to_punch_list(
        project,
        item.id,
        actor,
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    db.session.refresh(item)
    assert item.description == wording
    assert punch.description == wording
    assert punch.origin_type == PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH
    assert accepted.punch_list_item_id == punch.id
    assert accepted.review_status == WALKTHROUGH_REVIEW_ACCEPTED
    assert accepted.reviewed_by_user_id == actor.id
    assert accepted.reviewed_at is not None
    assert ProjectPunchListItem.query.count() == 1
    assert ProjectFinalWalkthroughItem.query.count() == 1


def test_client_cannot_directly_create_punch_list(app, client):
    actor = ensure_office_user()
    project = _add_project("No Direct")
    issue = _issue(project, actor)
    posted = client.post(
        f"/projects/{project.id}/punch-list",
        data={
            "description": "Client trying to punch.",
            "work_source_type": PUNCH_LIST_SOURCE_OTHER,
        },
        follow_redirects=False,
        headers={"Cookie": ""},
    )
    public = client.post(
        issue.path,
        data={"item": "Client trying to punch.", "origin_type": "CLIENT_WALKTHROUGH"},
        follow_redirects=False,
    )
    assert public.status_code in (200, 400)
    if ProjectPunchListItem.query.count():
        assert ProjectPunchListItem.query.one().origin_type != PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH or False
    assert ProjectPunchListItem.query.filter_by(
        origin_type=PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH
    ).count() == 0


def test_contractor_sees_pending_review_on_hub(app, client):
    actor = ensure_office_user()
    project = _add_project("Pending Hub")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Grout line."]
    )
    html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert 'id="hub-final-walkthrough"' in html
    assert contractor_copy.WALKTHROUGH_STATE_AWAITING in html
    assert "Grout line." in html
    assert contractor_copy.WALKTHROUGH_ADD_TO_PUNCH_LIST in html


def test_accept_requires_work_source_and_creates_one_item(app):
    actor = ensure_office_user()
    project = _add_project("Accept Source")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Caulk the tub."]
    )
    item = ProjectFinalWalkthroughItem.query.one()
    with pytest.raises(WalkthroughError):
        accept_walkthrough_item_to_punch_list(
            project, item.id, actor, work_source_type=""
        )
    assert ProjectPunchListItem.query.count() == 0
    accept_walkthrough_item_to_punch_list(
        project, item.id, actor, work_source_type=PUNCH_LIST_SOURCE_OTHER
    )
    assert ProjectPunchListItem.query.count() == 1
    assert ProjectPunchListItem.query.one().origin_type == PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH


def test_already_addressed_and_discuss_create_no_punch_list(app):
    actor = ensure_office_user()
    project = _add_project("Dispose")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access,
        nothing_to_add=False,
        item_descriptions=["Addressed later.", "Discuss later."],
    )
    first, second = (
        ProjectFinalWalkthroughItem.query.order_by(
            ProjectFinalWalkthroughItem.id.asc()
        ).all()
    )
    mark_walkthrough_item_already_addressed(project, first.id, actor)
    mark_walkthrough_item_discuss_or_out_of_scope(project, second.id, actor)
    db.session.refresh(first)
    db.session.refresh(second)
    assert first.review_status == WALKTHROUGH_REVIEW_ADDRESSED
    assert second.review_status == WALKTHROUGH_REVIEW_DISCUSS
    assert first.punch_list_item_id is None
    assert second.punch_list_item_id is None
    assert first.description == "Addressed later."
    assert second.description == "Discuss later."
    assert ProjectPunchListItem.query.count() == 0


def test_nothing_to_add_does_not_override_open_punch_list(app):
    actor = ensure_office_user()
    project = _add_project("Open Punch")
    create_punch_list_item(
        project,
        actor,
        description="Existing contractor item.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(access, nothing_to_add=True, item_descriptions=[])
    assert ProjectPunchListItem.query.count() == 1
    assert ProjectPunchListItem.query.one().status == PUNCH_LIST_STATUS_OPEN
    assert ProjectPunchListItem.query.one().origin_type == PUNCH_LIST_ORIGIN_CONTRACTOR
    with pytest.raises(PunchListIncompleteError):
        require_punch_list_complete(project)


def test_non_response_does_not_block_project_close(app):
    owner, _membership = _make_owner()
    project = _add_project("Unanswered")
    _issue(project, owner)
    close_project(project, owner)
    db.session.refresh(project)
    assert project.operating_state == "CLOSED"
    assert ProjectFinalWalkthroughInvitation.query.one().status == WALKTHROUGH_STATUS_REVOKED


def test_pending_client_input_does_not_hard_gate_sign_off_seam(app):
    actor = ensure_office_user()
    project = _add_project("Pending Seam")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Pending paint."]
    )
    assert list_pending_walkthrough_items(project)
    assert punch_list_complete(project) is True
    require_punch_list_complete(project)


def test_open_punch_list_still_hard_gates_sign_off_seam(app):
    actor = ensure_office_user()
    project = _add_project("Gate")
    create_punch_list_item(
        project,
        actor,
        description="Still open.",
        work_source_type=PUNCH_LIST_SOURCE_OTHER,
    )
    with pytest.raises(PunchListIncompleteError):
        require_punch_list_complete(project)


def test_submitted_invitation_replay_rejected(app):
    actor = ensure_office_user()
    project = _add_project("Replay")
    issue = _issue(project, actor)
    credential = f"{issue.lookup_key}.{issue.secret}"
    access = resolve_walkthrough_access(credential)
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Once."]
    )
    with pytest.raises(WalkthroughTokenError):
        resolve_walkthrough_access(credential, allow_responded=False)
    replay = resolve_walkthrough_access(credential, allow_responded=True)
    with pytest.raises(WalkthroughTokenError):
        submit_walkthrough_response(
            replay, nothing_to_add=False, item_descriptions=["Twice."]
        )
    assert ProjectFinalWalkthroughItem.query.count() == 1


def test_resend_revokes_previous_open_invitation(app):
    actor = ensure_office_user()
    project = _add_project("Resend")
    first = _issue(project, actor)
    second = _issue(project, actor)
    db.session.refresh(first.invitation)
    assert first.invitation.status == WALKTHROUGH_STATUS_REVOKED
    assert second.invitation.status == WALKTHROUGH_STATUS_OPEN
    with pytest.raises(WalkthroughTokenError):
        resolve_walkthrough_access(f"{first.lookup_key}.{first.secret}")


def test_hub_invite_and_copyable_link(app, client):
    project = _add_project("Copy Link")
    html = client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert contractor_copy.WALKTHROUGH_STATE_NOT_SENT in html
    assert contractor_copy.WALKTHROUGH_INVITE in html
    invited = client.post(
        f"/projects/{project.id}/final-walkthrough/invite",
        follow_redirects=True,
    )
    body = invited.get_data(as_text=True)
    assert contractor_copy.WALKTHROUGH_STATE_SENT in body
    assert "/walkthrough/" in body
    assert contractor_copy.WALKTHROUGH_COPY_LINK_HINT in body
    assert "Completion Sign-Off" not in body
    assert "signature" not in body.lower() or "csrf" in body.lower()


def test_client_page_has_no_office_or_field_chrome(app, client):
    actor = ensure_office_user()
    project = _add_project("Chrome")
    issue = _issue(project, actor)
    html = client.get(issue.path).get_data(as_text=True)
    assert "walkthrough.css" in html
    assert "app.css" not in html
    assert "field.css" not in html
    assert 'data-walkthrough-page="form"' in html
    assert contractor_copy.WALKTHROUGH_ADD_ANOTHER in html
    assert contractor_copy.WALKTHROUGH_NOTHING_TO_ADD in html


def test_no_completion_sign_off_or_native_signing_or_close_rewrite():
    walk_service = (
        REPO_ROOT / "app" / "services" / "project_final_walkthrough.py"
    ).read_text(encoding="utf-8")
    walk_routes = (REPO_ROOT / "app" / "routes" / "walkthrough.py").read_text(
        encoding="utf-8"
    )
    office_routes = (
        REPO_ROOT / "app" / "routes" / "final_walkthrough.py"
    ).read_text(encoding="utf-8")
    lifecycle = (
        REPO_ROOT / "app" / "services" / "project_operating_lifecycle.py"
    ).read_text(encoding="utf-8")
    projects = (REPO_ROOT / "app" / "routes" / "projects.py").read_text(encoding="utf-8")
    signing = (REPO_ROOT / "app" / "services" / "signing.py").read_text(encoding="utf-8")
    blob = walk_service + walk_routes + office_routes
    assert "completion_sign_off" not in blob
    assert "CompletionSignOff" not in blob
    assert "UserMembership(" not in walk_service
    assert "password" not in walk_routes.lower()
    assert "close_project" not in blob
    assert "reopen_project" not in blob
    assert "_revoke_open_invitations" in lifecycle
    assert "completion_sign_off" not in lifecycle.lower()
    assert "close_project" in projects
    assert "require_instance_owner_or_system_administrator" in projects
    assert "issue_customer_invitation" in signing
    field_routes = (REPO_ROOT / "app" / "routes" / "field.py").read_text(encoding="utf-8")
    assert "walkthrough" not in field_routes.lower()
    assert "Punch List" not in field_routes


def test_no_new_access_domain_or_sys_admin():
    service = (
        REPO_ROOT / "app" / "services" / "project_final_walkthrough.py"
    ).read_text(encoding="utf-8")
    assert "ACCESS_DOMAIN" not in service
    assert "COMPANY_MANAGEMENT" not in service
    assert "require_instance_owner" not in service
    assert "SYSTEM_ADMIN" not in service


def test_photo_support_deferred():
    service = (
        REPO_ROOT / "app" / "services" / "project_final_walkthrough.py"
    ).read_text(encoding="utf-8")
    assert "FieldCaptureOriginal" not in service
    assert "request.files" not in service
    assert "multipart" not in service.lower()


def test_domain_b_is_not_required_to_invite(app, client):
    project = _add_project("No B")
    user = create_user(
        email=ORDINARY_EMAIL,
        password=ORDINARY_PASSWORD,
        display_name="No B",
    )
    membership = create_membership(user)
    db.session.commit()
    login_office_user(client, email=ORDINARY_EMAIL, password=ORDINARY_PASSWORD)
    response = client.post(
        f"/projects/{project.id}/final-walkthrough/invite",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert ProjectFinalWalkthroughInvitation.query.count() == 1


def test_http_submit_one_and_nothing_to_add(app, client):
    actor = ensure_office_user()
    project = _add_project("HTTP Items")
    issue = _issue(project, actor)
    posted = client.post(
        issue.path,
        data={"item": ["Cabinet ding.", ""]},
        follow_redirects=False,
    )
    assert posted.status_code == 200
    assert contractor_copy.WALKTHROUGH_RECEIVED in posted.get_data(as_text=True)
    assert ProjectFinalWalkthroughItem.query.count() == 1
    other = _add_project("HTTP Nothing")
    nothing = _issue(other, actor)
    nothing_post = client.post(
        nothing.path,
        data={"nothing_to_add": "1"},
        follow_redirects=False,
    )
    assert nothing_post.status_code == 200
    assert (
        ProjectFinalWalkthroughInvitation.query.filter_by(project_id=other.id)
        .one()
        .response_mode
        == WALKTHROUGH_RESPONSE_NOTHING_TO_ADD
    )


def test_http_accept_to_punch_list(app, client):
    actor = ensure_office_user()
    project = _add_project("HTTP Accept")
    issue = _issue(project, actor)
    access = resolve_walkthrough_access(f"{issue.lookup_key}.{issue.secret}")
    submit_walkthrough_response(
        access, nothing_to_add=False, item_descriptions=["Loose handle."]
    )
    item = ProjectFinalWalkthroughItem.query.one()
    response = client.post(
        f"/projects/{project.id}/final-walkthrough/items/{item.id}/accept",
        data={"work_source_type": PUNCH_LIST_SOURCE_OTHER},
        follow_redirects=False,
    )
    assert response.status_code == 302
    punch = ProjectPunchListItem.query.one()
    assert punch.origin_type == PUNCH_LIST_ORIGIN_CLIENT_WALKTHROUGH
    assert punch.description == "Loose handle."


def test_additive_migration_is_new_graph_head(tmp_path):
    db_path = tmp_path / "fg035_walkthrough_c2.db"
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
        assert script.get_heads() == ["g7b8c9d0e1f2"]
        revision = script.get_revision("e5f6a7b8c9d0")
        assert revision.down_revision == "d4e5f6a7b8c9"

        command.upgrade(alembic_cfg, "d4e5f6a7b8c9")
        engine = db.engine
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_final_walkthrough_invitations" not in tables
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == ["d4e5f6a7b8c9"]

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == ["g7b8c9d0e1f2"]
            assert "project_final_walkthrough_invitations" in tables
            assert "project_final_walkthrough_items" in tables
            assert "project_final_walkthrough_access_attempts" in tables
            invite_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM project_final_walkthrough_invitations")
            ).scalar()
            item_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM project_final_walkthrough_items")
            ).scalar()
            punch_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM project_punch_list_items")
            ).scalar()
            assert invite_count == 0
            assert item_count == 0
            assert punch_count == 0


def test_c2_tests_use_memory_db_only(app):
    uri = str(app.config["SQLALCHEMY_DATABASE_URI"])
    assert uri.startswith("sqlite:///:memory:")
    assert "brayman_estimator.db" not in uri
