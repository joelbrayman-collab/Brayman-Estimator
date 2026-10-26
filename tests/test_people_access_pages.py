"""People & Access office pages (V1 defect, Joel 21 Oct 2026). Synthetic data only.

Owner / System Administrator only, current organization only; add a person (User + membership +
set-password email captured locally); deactivate / reactivate (sessions end on the next request);
access domains and System Administrator through the existing services; the guards.
"""

from __future__ import annotations

import logging
import os
import re

import pytest

from app import create_app, db
from app.models.organization import (
    ADMINISTRATOR_EVENT_APPOINT,
    ADMINISTRATOR_EVENT_REMOVE,
    Organization,
    OrganizationSystemAdministratorEvent,
)
from app.models.password_reset import PasswordResetToken
from app.models.transactional_message import (
    STATUS_LOCAL_CAPTURED,
    TEMPLATE_PASSWORD_RESET,
    TEMPLATE_ACCOUNT_INVITATION,
    TransactionalMessage,
)
from app.models.user import User, UserMembership
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, membership_has_access_domain
from app.services.instance_authority import appoint_system_administrator, set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.people_access import PeopleAccessError, add_person, deactivate_person
from tests.auth_fixtures import ensure_office_user, login_office_user

pytestmark = pytest.mark.no_office_auth

OWNER = ("office@example.com", "office-test-password")
STAFF = ("sam.staff@example.invalid", "Synthetic-staff-pass-1", "Sam Staff (synthetic)")
ADMIN = ("ada.admin@example.invalid", "Synthetic-admin-pass-1", "Ada Admin (synthetic)")
ORG_B = "ORG-PA-B"
BEA = ("bea.orgb@example.invalid", "Synthetic-orgb-pass-1", "Bea OrgB (synthetic)")
NEW_PERSON = ("Nora New (synthetic)", "nora.new@example.invalid")


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'people.db'}",
            "SECRET_KEY": "test-secret-people-access",
            "WTF_CSRF_ENABLED": False,
            "TRANSACTIONAL_EMAIL_PROVIDER": "local",
            "MAIL_CAPTURE_ROOT": str(tmp_path / "mail"),
        }
    )
    with application.app_context():
        db.create_all()
        owner = ensure_office_user()
        owner_m = UserMembership.query.filter_by(user_id=owner.id, organization_id=ORG).one()
        set_instance_owner(ORG, owner_m.id, owner.id)
        staff = ensure_office_user(email=STAFF[0], password=STAFF[1], display_name=STAFF[2])
        admin = ensure_office_user(email=ADMIN[0], password=ADMIN[1], display_name=ADMIN[2])
        admin_m = UserMembership.query.filter_by(user_id=admin.id).one()
        appoint_system_administrator(ORG, admin_m.id, owner.id)
        db.session.add(Organization(id=ORG_B, legal_name="Rival B (synthetic)", display_name="Rival B", is_active=True))
        db.session.commit()
        bea = ensure_office_user(email=BEA[0], password=BEA[1], display_name=BEA[2], organization_id=ORG_B)
        bea_m = UserMembership.query.filter_by(user_id=bea.id).one()
        set_instance_owner(ORG_B, bea_m.id, bea.id)
        application.config["IDS"] = {
            "owner": owner.id,
            "owner_m": owner_m.id,
            "staff": staff.id,
            "staff_m": UserMembership.query.filter_by(user_id=staff.id).one().id,
            "admin": admin.id,
            "admin_m": admin_m.id,
            "bea": bea.id,
            "bea_m": bea_m.id,
        }
        db.session.remove()
    # No application context stays pushed during the HTTP calls: flask-login caches the signed-in
    # user on ``g``, which would otherwise be shared by every test client.
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


def _client(app, who):
    client = app.test_client()
    response = login_office_user(client, email=who[0], password=who[1])
    assert response.status_code == 302, response.data[:300]
    return client


def _ids(app):
    return app.config["IDS"]


def _captured(app, to):
    root = app.config["MAIL_CAPTURE_ROOT"]
    if not os.path.isdir(root):
        return []
    bodies = []
    for name in sorted(os.listdir(root)):
        with open(os.path.join(root, name), encoding="utf-8") as handle:
            text = handle.read()
        if f"To: {to}" in text:
            bodies.append(text)
    return bodies


# ------------------------------------------------------------------ permissions

def test_owner_and_system_administrator_open_the_pages(app):
    ids = _ids(app)
    for who in (OWNER, ADMIN):
        client = _client(app, who)
        page = client.get("/settings/people")
        assert page.status_code == 200
        text = page.get_data(as_text=True)
        assert STAFF[2] in text and "People &amp; Access" in text
        assert client.get("/settings/people/new").status_code == 200
        assert client.get(f"/settings/people/{ids['staff_m']}").status_code == 200
        # The menu offers it.
        assert 'href="/settings/people"' in client.get("/projects/").get_data(as_text=True)


def test_ordinary_office_user_is_refused_everywhere_and_not_offered_it(app):
    ids = _ids(app)
    client = _client(app, STAFF)
    assert 'href="/settings/people"' not in client.get("/projects/").get_data(as_text=True)
    mid = ids["owner_m"]
    gets = ["/settings/people", "/settings/people/new", f"/settings/people/{mid}"]
    posts = [
        ("/settings/people/new", {"display_name": "X", "email": "x@example.invalid"}),
        (f"/settings/people/{mid}/deactivate", {}),
        (f"/settings/people/{mid}/reactivate", {}),
        (f"/settings/people/{mid}/send-link", {}),
        (f"/settings/people/{mid}/access", {"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "action": "grant"}),
        (f"/settings/people/{ids['staff_m']}/access", {"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "action": "grant"}),
        (f"/settings/people/{ids['staff_m']}/administrator", {"action": "appoint"}),
    ]
    for path in gets:
        assert client.get(path).status_code == 403, path
    for path, data in posts:
        assert client.post(path, data=data).status_code == 403, path
    with app.app_context():
        assert User.query.filter_by(email="x@example.invalid").first() is None
        staff = db.session.get(User, ids["staff"])
        assert not membership_has_access_domain(staff, ORG, ACCESS_DOMAIN_COMPANY_MANAGEMENT)


def test_signed_out_goes_to_sign_in(app):
    client = app.test_client()
    response = client.get("/settings/people")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_another_organization_is_never_visible_or_changeable(app):
    ids = _ids(app)
    owner = _client(app, OWNER)
    assert BEA[0] not in owner.get("/settings/people").get_data(as_text=True)
    assert owner.get(f"/settings/people/{ids['bea_m']}").status_code == 404
    for path, data in (
        (f"/settings/people/{ids['bea_m']}/deactivate", {}),
        (f"/settings/people/{ids['bea_m']}/send-link", {}),
        (f"/settings/people/{ids['bea_m']}/access", {"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "action": "grant"}),
        (f"/settings/people/{ids['bea_m']}/administrator", {"action": "appoint"}),
    ):
        assert owner.post(path, data=data).status_code == 404, path
    with app.app_context():
        assert db.session.get(User, ids["bea"]).is_active
    # Org B's owner sees only org B.
    bea = _client(app, BEA)
    text = bea.get("/settings/people").get_data(as_text=True)
    assert BEA[0] in text and STAFF[0] not in text and OWNER[0] not in text
    assert bea.get(f"/settings/people/{ids['staff_m']}").status_code == 404


# ------------------------------------------------------------------ add a person

def test_owner_adds_a_person_who_gets_the_set_password_email_and_signs_in(app):
    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1].upper()})
    # Sign-in reliability (26 Oct 2026): the page with the link to text is shown, emailed or not.
    assert response.status_code == 200 and 'data-one-time-link-emailed="yes"' in response.get_data(as_text=True)
    with app.app_context():
        user = User.query.filter_by(email=NEW_PERSON[1]).one()
        assert user.is_active and user.display_name == NEW_PERSON[0]
        membership = UserMembership.query.filter_by(user_id=user.id).one()
        assert membership.organization_id == ORG and membership.is_active
        assert f'/settings/people/{membership.id}/send-link' in response.get_data(as_text=True)  # that person's page
        message = TransactionalMessage.query.filter_by(to_email=NEW_PERSON[1]).one()
        assert message.template_id == TEMPLATE_ACCOUNT_INVITATION  # a proper invitation, 72 h (21 Oct 2026)
        assert message.status == STATUS_LOCAL_CAPTURED
        assert PasswordResetToken.query.filter_by(user_id=user.id, consumed_at=None).count() == 1
    mails = _captured(app, NEW_PERSON[1])
    assert len(mails) == 1
    link = "/reset-password/" + re.search(r"/reset-password#([A-Za-z0-9_\-.]+)", mails[0]).group(1)
    person = app.test_client()
    done = person.post(link, data={"password": "Synthetic-nora-pass-1", "confirm_password": "Synthetic-nora-pass-1"})
    assert done.status_code == 302
    assert login_office_user(person, email=NEW_PERSON[1], password="Synthetic-nora-pass-1").status_code == 302
    assert person.get("/projects/").status_code == 200
    assert person.get("/settings/people").status_code == 403


def test_add_person_refuses_a_taken_email_or_missing_fields(app):
    owner = _client(app, OWNER)
    for data in (
        {"display_name": "Dup", "email": STAFF[0]},
        {"display_name": "Other org dup", "email": BEA[0].upper()},
        {"display_name": "", "email": "blank.name@example.invalid"},
        {"display_name": "No email", "email": ""},
        {"display_name": "Bad", "email": "not-an-email"},
    ):
        response = owner.post("/settings/people/new", data=data)
        assert response.status_code == 400, data
    assert "already has a sign-in" in owner.post(
        "/settings/people/new", data={"display_name": "Dup", "email": STAFF[0]}
    ).get_data(as_text=True)
    with app.app_context():
        assert User.query.count() == 4
        assert TransactionalMessage.query.count() == 0


def test_owner_sent_links_do_not_use_the_office_forgot_password_budget(app):
    owner = _client(app, OWNER)
    for n in range(6):
        assert owner.post("/settings/people/new", data={"display_name": f"P{n}", "email": f"p{n}@example.invalid"}).status_code == 200
    with app.app_context():
        assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_ACCOUNT_INVITATION).count() == 6
        # plus one confirmation to the owner for each (23 Oct 2026), never counted against anyone's budget
        assert TransactionalMessage.query.filter_by(template_id="INVITATION_SENT_CONFIRMATION",
                                                    to_email=OWNER[0]).count() == 6
    # The office's own forgot-password still works from the same address.
    assert app.test_client().post("/forgot-password", data={"email": STAFF[0]}).status_code == 302
    with app.app_context():
        assert TransactionalMessage.query.filter_by(to_email=STAFF[0]).count() == 1


def test_send_link_again_is_limited_per_person(app):
    ids = _ids(app)
    owner = _client(app, OWNER)
    path = f"/settings/people/{ids['staff_m']}/send-link"
    for _ in range(3):
        assert "was emailed" in owner.post(path, follow_redirects=True).get_data(as_text=True)
    assert "Try again later" in owner.post(path, follow_redirects=True).get_data(as_text=True)
    with app.app_context():
        assert TransactionalMessage.query.filter_by(to_email=STAFF[0]).count() == 3
        assert PasswordResetToken.query.filter_by(user_id=ids["staff"], consumed_at=None).count() == 1


# ------------------------------------------------------------------ deactivate / reactivate

def test_deactivate_ends_the_session_and_reactivate_needs_a_new_sign_in(app):
    ids = _ids(app)
    staff = _client(app, STAFF)
    assert staff.get("/projects/").status_code == 200
    owner = _client(app, OWNER)
    response = owner.post(f"/settings/people/{ids['staff_m']}/deactivate", follow_redirects=True)
    assert "is deactivated" in response.get_data(as_text=True)
    assert "Deactivated" in owner.get("/settings/people").get_data(as_text=True)
    ended = staff.get("/projects/")
    assert ended.status_code == 302 and "/login" in ended.headers["Location"]
    refused = app.test_client()
    login_office_user(refused, email=STAFF[0], password=STAFF[1])
    assert refused.get("/projects/").status_code == 302
    owner.post(f"/settings/people/{ids['staff_m']}/reactivate")
    with app.app_context():
        assert db.session.get(User, ids["staff"]).is_active
    # The old session does not come back; signing in again works.
    assert staff.get("/projects/").status_code == 302
    again = _client(app, STAFF)
    assert again.get("/projects/").status_code == 200


def test_cannot_deactivate_yourself_or_the_owner(app):
    ids = _ids(app)
    owner = _client(app, OWNER)
    text = owner.post(f"/settings/people/{ids['owner_m']}/deactivate", follow_redirects=True).get_data(as_text=True)
    assert "cannot deactivate your own sign-in" in text
    admin = _client(app, ADMIN)
    text = admin.post(f"/settings/people/{ids['owner_m']}/deactivate", follow_redirects=True).get_data(as_text=True)
    assert "owner&#39;s sign-in cannot be deactivated" in text
    text = admin.post(f"/settings/people/{ids['admin_m']}/deactivate", follow_redirects=True).get_data(as_text=True)
    assert "cannot deactivate your own sign-in" in text
    with app.app_context():
        assert db.session.get(User, ids["owner"]).is_active
        assert db.session.get(User, ids["admin"]).is_active
        # Service-level guards too.
        with pytest.raises(PeopleAccessError):
            deactivate_person(organization_id=ORG, membership_id=ids["owner_m"], actor=ids["admin"])
    # The owner always keeps owner authority: still opens the page.
    assert owner.get("/settings/people").status_code == 200


def test_system_administrator_may_deactivate_an_ordinary_person(app):
    ids = _ids(app)
    admin = _client(app, ADMIN)
    admin.post(f"/settings/people/{ids['staff_m']}/deactivate")
    with app.app_context():
        assert not db.session.get(User, ids["staff"]).is_active


def test_deactivation_is_written_to_the_people_access_log(app, caplog):
    ids = _ids(app)
    owner = _client(app, OWNER)
    # Listen on the logger itself: the app's logging set-up (run by earlier tests) may stop records
    # propagating to the root logger, where caplog normally listens.
    logger = logging.getLogger("people_access")
    logger.addHandler(caplog.handler)
    level, disabled = logger.level, logger.disabled
    logger.setLevel(logging.INFO)
    logger.disabled = False  # a logging dictConfig run by an earlier test can disable existing loggers
    try:
        owner.post(f"/settings/people/{ids['staff_m']}/deactivate")
        owner.post(f"/settings/people/{ids['staff_m']}/reactivate")
        owner.post(f"/settings/people/{ids['staff_m']}/access", data={"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "action": "grant"})
    finally:
        logger.removeHandler(caplog.handler)
        logger.setLevel(level)
        logger.disabled = disabled
    lines = [r.getMessage() for r in caplog.records if r.name == "people_access"]
    assert any(f"DEACTIVATE org={ORG} actor_user_id={ids['owner']} target_user_id={ids['staff']}" in l for l in lines)
    assert any("REACTIVATE" in l for l in lines)
    assert any("GRANT_ACCESS_DOMAIN" in l and ACCESS_DOMAIN_COMPANY_MANAGEMENT in l for l in lines)


# ------------------------------------------------------------------ access and System Administrator

def test_owner_gives_and_removes_company_management(app):
    ids = _ids(app)
    owner = _client(app, OWNER)
    staff = _client(app, STAFF)
    assert staff.get("/company-attention").status_code == 403
    owner.post(f"/settings/people/{ids['staff_m']}/access", data={"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "action": "grant"})
    assert staff.get("/company-attention").status_code == 200
    owner.post(f"/settings/people/{ids['staff_m']}/access", data={"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "action": "remove"})
    assert staff.get("/company-attention").status_code == 403
    text = owner.post(
        f"/settings/people/{ids['staff_m']}/access", data={"domain": "SENSITIVE_FINANCIAL", "action": "grant"},
        follow_redirects=True,
    ).get_data(as_text=True)
    assert "Unknown access domain" in text


def test_owner_appoints_and_removes_a_system_administrator_with_event_rows(app):
    ids = _ids(app)
    owner = _client(app, OWNER)
    owner.post(f"/settings/people/{ids['staff_m']}/administrator", data={"action": "appoint"})
    staff = _client(app, STAFF)
    assert staff.get("/settings/people").status_code == 200
    owner.post(f"/settings/people/{ids['staff_m']}/administrator", data={"action": "remove"})
    assert staff.get("/settings/people").status_code == 403
    with app.app_context():
        events = OrganizationSystemAdministratorEvent.query.filter_by(membership_id=ids["staff_m"]).order_by(
            OrganizationSystemAdministratorEvent.id).all()
        assert [e.event for e in events] == [ADMINISTRATOR_EVENT_APPOINT, ADMINISTRATOR_EVENT_REMOVE]
        assert all(e.actor_user_id == ids["owner"] and e.organization_id == ORG for e in events)


def test_only_the_owner_appoints_and_the_owner_cannot_be_removed(app):
    ids = _ids(app)
    admin = _client(app, ADMIN)
    text = admin.post(f"/settings/people/{ids['staff_m']}/administrator", data={"action": "appoint"},
                      follow_redirects=True).get_data(as_text=True)
    assert "Only the Instance Owner may appoint" in text
    text = admin.post(f"/settings/people/{ids['owner_m']}/administrator", data={"action": "remove"},
                      follow_redirects=True).get_data(as_text=True)
    assert "cannot be removed" in text
    with app.app_context():
        assert OrganizationSystemAdministratorEvent.query.filter_by(membership_id=ids["staff_m"]).count() == 0
        org = db.session.get(Organization, ORG)
        assert org.instance_owner_membership_id == ids["owner_m"]


def test_service_refuses_an_ordinary_actor(app):
    ids = _ids(app)
    with app.app_context():
        with pytest.raises(PeopleAccessError):
            add_person(organization_id=ORG, actor=ids["staff"], display_name="X", email="x2@example.invalid")
        # Org B's owner is not an administrator of org A.
        with pytest.raises(PeopleAccessError):
            add_person(organization_id=ORG, actor=ids["bea"], display_name="X", email="x3@example.invalid")
        assert User.query.filter(User.email.in_(["x2@example.invalid", "x3@example.invalid"])).count() == 0


def test_owner_marks_and_clears_field_only_from_people_and_access(app):
    """Joel, 21 Oct 2026: crew are marked Field only from the People & Access pages (same service as the
    operator command); a Field only person cannot be made a System Administrator until it is removed."""
    from app.services.access_domains import membership_is_field_only

    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": "Kevin Synthetic Crew",
                                                        "email": "kevin.crew@example.invalid", "field_only": "yes"})
    assert response.status_code == 200, response.get_data(as_text=True)[:300]
    with app.app_context():
        membership_id = UserMembership.query.join(User, User.id == UserMembership.user_id).filter(
            User.email == "kevin.crew@example.invalid").one().id

    def marked():
        with app.app_context():
            return membership_is_field_only(db.session.get(UserMembership, membership_id))

    assert marked()
    assert 'data-field-only="yes"' in owner.get(f"/settings/people/{membership_id}").get_data(as_text=True)
    refused = owner.post(f"/settings/people/{membership_id}/administrator", data={"action": "appoint"}, follow_redirects=True)
    assert "Remove Field only first" in refused.get_data(as_text=True)
    owner.post(f"/settings/people/{membership_id}/field-only", data={"action": "clear"})
    assert not marked()
    owner.post(f"/settings/people/{membership_id}/field-only", data={"action": "mark"})
    assert marked()
    staff = _client(app, STAFF)
    assert staff.post(f"/settings/people/{membership_id}/field-only", data={"action": "clear"}).status_code == 403
    assert marked()


def test_invitation_activation_and_history_are_recorded(app):
    """Crew Access (21 Oct 2026): a new person gets an invitation (not a reset notice) valid 72 hours;
    choosing a password records them as activated; every change shows in the person's History."""
    from app.models.people_access_event import PeopleAccessEvent
    from app.services.password_reset import complete_password_reset

    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": "Kev Synthetic", "email": "kev.crew@example.invalid",
                                                        "field_only": "yes"})
    assert response.status_code == 200
    with app.app_context():
        membership_id = UserMembership.query.join(User, User.id == UserMembership.user_id).filter(
            User.email == "kev.crew@example.invalid").one().id
    with app.app_context():
        message = TransactionalMessage.query.filter_by(to_email="kev.crew@example.invalid").one()
        assert message.template_id == TEMPLATE_ACCOUNT_INVITATION
        token = PasswordResetToken.query.join(User, User.id == PasswordResetToken.user_id).filter(
            User.email == "kev.crew@example.invalid").one()
        assert (token.expires_at - token.created_at).total_seconds() == 72 * 3600
    mail = _captured(app, "kev.crew@example.invalid")[-1]
    assert "invited you to CalibraytAI" in mail and "72 hours" in mail
    credential = re.search(r"/reset-password#([A-Za-z0-9_.\-]+)", mail).group(1)
    with app.app_context():
        complete_password_reset(credential, "Synthetic-kev-pass-1", confirm_password="Synthetic-kev-pass-1")
    owner.post(f"/settings/people/{membership_id}/deactivate")
    with app.app_context():
        actions = [e.action for e in PeopleAccessEvent.query.filter_by(membership_id=membership_id).order_by(PeopleAccessEvent.id)]
    assert actions[:4] == ["ADDED", "FIELD_ONLY_MARKED", "INVITATION_SENT", "ACTIVATED"] and actions[-1] == "DEACTIVATED"
    page = owner.get(f"/settings/people/{membership_id}").get_data(as_text=True)
    assert "Invitation emailed" in page and "Chose a password (account active)" in page and "Deactivated" in page


# ------------------------------------------------------------------ email not delivered (defect 9, 21 Oct 2026)

def _one_time_link(html):
    match = re.search(r'id="one-time-link" value="([^"]+)"', html)
    return match.group(1) if match else None


@pytest.mark.parametrize("setting", ["allowlist", "postmark_without_token", "postmark_refused", "hosted_local"])
def test_owner_gets_a_one_time_link_when_the_invitation_email_is_not_delivered(app, caplog, setting):
    """Production sends through Postmark (TRANSACTIONAL_EMAIL_PROVIDER=postmark) with a UAT allowlist.
    When the email is held back, not configured, refused, or only captured on a hosted server, the owner
    is told plainly and is shown the person's set-password link once, on the person's page: the same
    token (72 h invitation, one use), audited in people_access_events, never logged."""
    from datetime import datetime, timedelta

    from app.models.people_access_event import PeopleAccessEvent
    from app.services.transactional_email import TransportResult

    if setting == "allowlist":
        app.config["TRANSACTIONAL_UAT_ALLOWLIST"] = "joel@example.invalid"
    elif setting == "postmark_without_token":
        app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
        app.config["POSTMARK_SERVER_TOKEN"] = ""
    elif setting == "postmark_refused":
        app.config["TRANSACTIONAL_EMAIL_PROVIDER"] = "postmark"
        app.config["POSTMARK_SERVER_TOKEN"] = "synthetic-token"
        app.config["POSTMARK_HTTP_SEND"] = lambda payload: TransportResult(status="FAILED", provider="postmark",
                                                                            error_code="POSTMARK_406")
    else:
        app.config["CALIBRAYTAI_HOSTED"] = "1"
    caplog.set_level(logging.DEBUG)
    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1]})
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and response.headers["Cache-Control"] == "no-store"
    assert "was not delivered" in html and "data-one-time-link" in html
    link = _one_time_link(html)
    assert link and "/reset-password#" in link
    path = link[link.index("/reset-password#"):]
    with app.app_context():
        user = User.query.filter_by(email=NEW_PERSON[1]).one()
        membership = UserMembership.query.filter_by(user_id=user.id).one()
        token = PasswordResetToken.query.filter_by(user_id=user.id, consumed_at=None).one()
        assert timedelta(hours=71) < token.expires_at - datetime.utcnow() <= timedelta(hours=72)  # 72 h invitation
        assert path.split("/reset-password#")[1].split(".")[0] == token.lookup_key
        event = PeopleAccessEvent.query.filter_by(membership_id=membership.id, action="INVITATION_SENT").one()
        assert event.detail.startswith("Not emailed") and "shown to" in event.detail
        assert path.split(".")[-1] not in (event.detail or "")
    secret = path.rsplit(".", 1)[1]
    assert all(secret not in record.getMessage() for record in caplog.records)  # never logged

    # Only in that one response: the person's page does not show it again.
    again = owner.get(f"/settings/people/{membership.id}").get_data(as_text=True)
    assert secret not in again and "data-one-time-link" not in again
    assert "Invitation link given in person" in again

    # The person uses it once; a second use is refused.
    # the link carries the credential after "#"; the page posts it in the form body (22 Oct 2026)
    person = app.test_client()
    credential = path.split("#", 1)[1]
    assert person.get("/reset-password").status_code == 200
    assert person.post("/reset-password", data={"step": "open", "credential": credential}).status_code == 200
    assert person.post("/reset-password", data={"credential": credential, "password": "Synthetic-nora-pass-1",
                                                "confirm_password": "Synthetic-nora-pass-1"}).status_code == 302
    assert login_office_user(person, email=NEW_PERSON[1], password="Synthetic-nora-pass-1").status_code == 302
    reuse = app.test_client().post("/reset-password", data={"credential": credential, "password": "Synthetic-other-pass-1",
                                                            "confirm_password": "Synthetic-other-pass-1"})
    assert reuse.status_code != 302 or "/login" not in reuse.headers.get("Location", "")
    with app.app_context():
        assert PasswordResetToken.query.filter_by(user_id=user.id, consumed_at=None).count() == 0


def test_a_delivered_email_still_shows_the_owner_the_link(app):
    """Sign-in reliability (Joel, 26 Oct 2026): the owner always gets the link to text, emailed or not; it is the
    same link the email carried (tests/test_signin_email_reliability.py)."""
    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1]},
                          follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "was emailed to" in html and "expires in 72 hours" in html
    assert 'data-one-time-link-emailed="yes"' in html and "/reset-password#" in html


def test_only_the_owner_side_ever_sees_the_link(app):
    """Another office user cannot send links at all (403), so cannot be shown one."""
    ids = _ids(app)
    app.config["TRANSACTIONAL_UAT_ALLOWLIST"] = "joel@example.invalid"
    staff = _client(app, STAFF)
    response = staff.post(f"/settings/people/{ids['admin_m']}/send-link")
    assert response.status_code == 403 and b"reset-password" not in response.data


# ------------------------------------------------------------------ the sender's confirmation and Email history (23 Oct 2026)


def _confirmations(app):
    root = app.config["MAIL_CAPTURE_ROOT"]
    names = sorted(n for n in os.listdir(root) if "INVITATION_SENT_CONFIRMATION" in n) if os.path.isdir(root) else []
    return [open(os.path.join(root, n), encoding="utf-8").read() for n in names]


def test_the_sender_gets_a_confirmation_without_the_link_and_the_page_shows_email_history(app):
    owner = _client(app, OWNER)
    assert owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1]}).status_code == 200
    invitation = _captured(app, NEW_PERSON[1])
    assert len(invitation) == 1
    credential = re.search(r"/reset-password#([A-Za-z0-9_\-.]+)", invitation[0]).group(1)
    lookup_key, secret = credential.split(".", 1)[0], credential.rsplit(".", 1)[1]
    confirmations = _confirmations(app)
    assert len(confirmations) == 1
    note = confirmations[0]
    assert f"To: {OWNER[0]}" in note and f"To: {NEW_PERSON[1]}" not in note  # to the person who pressed the button
    assert f"Your CalibraytAI invitation to {NEW_PERSON[0]} ({NEW_PERSON[1]}) was sent at " in note
    assert "It works once and expires " in note
    for forbidden in (credential, secret, lookup_key, "/reset-password", "reset-password", "http"):
        assert forbidden not in note, forbidden
    with app.app_context():
        row = TransactionalMessage.query.filter_by(template_id="INVITATION_SENT_CONFIRMATION").one()
        assert row.to_email == OWNER[0] and row.status == STATUS_LOCAL_CAPTURED
        user = User.query.filter_by(email=NEW_PERSON[1]).one()
        membership = UserMembership.query.filter_by(user_id=user.id).one()
    # Send the link again: a set-password link confirmation too.
    owner.post(f"/settings/people/{membership.id}/send-link")
    assert len(_confirmations(app)) == 2
    assert f"Your CalibraytAI invitation to {NEW_PERSON[0]}" in _confirmations(app)[-1]  # not activated yet
    html = owner.get(f"/settings/people/{membership.id}").get_data(as_text=True)
    section = re.search(r'data-person-email-history="(\d+)">(.*?)</section>', html, re.S)
    assert section and int(section.group(1)) == 2
    # Accepted is not delivered (26 Oct 2026): captured mail on this development office shows as kept here.
    assert section.group(2).count("data-email-history-row") == 2 and section.group(2).count("data-email-sent") == 2
    assert "Invitation" in section.group(2)
    for forbidden in (credential, secret, lookup_key, "/reset-password"):
        assert forbidden not in section.group(2)


def test_email_history_shows_the_last_five_with_a_plain_reason(app):
    ids = _ids(app)
    app.config["TRANSACTIONAL_UAT_ALLOWLIST"] = "joel@example.invalid"
    from app.models.transactional_message import STATUS_SKIPPED_ALLOWLIST

    with app.app_context():
        for n in range(7):
            db.session.add(TransactionalMessage(template_id=TEMPLATE_PASSWORD_RESET, to_email=STAFF[0],
                                                from_email="noreply@localhost", provider="local",
                                                status=STATUS_SKIPPED_ALLOWLIST, error_code="ALLOWLIST"))
        db.session.commit()
    owner = _client(app, OWNER)
    html = owner.get(f"/settings/people/{ids['staff_m']}").get_data(as_text=True)
    section = re.search(r'data-person-email-history="(\d+)">(.*?)</section>', html, re.S)
    assert int(section.group(1)) == 5 and section.group(2).count("data-email-not-sent") == 5
    assert "Set-password link" in section.group(2) and "allowlist" in section.group(2)


def test_the_confirmation_respects_the_allowlist_and_never_changes_the_invitation(app):
    # The person is on the allowlist, the sender is not: the invitation goes, the confirmation is held back
    # (recorded as SKIPPED_ALLOWLIST), and the owner is still told the invitation was emailed.
    app.config["TRANSACTIONAL_UAT_ALLOWLIST"] = NEW_PERSON[1]
    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1]},
                          follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "was emailed to" in html and 'data-one-time-link-emailed="yes"' in html
    assert _confirmations(app) == []
    with app.app_context():
        row = TransactionalMessage.query.filter_by(template_id="INVITATION_SENT_CONFIRMATION").one()
        assert row.to_email == OWNER[0] and row.status == "SKIPPED_ALLOWLIST"
        assert TransactionalMessage.query.filter_by(template_id=TEMPLATE_ACCOUNT_INVITATION,
                                                    to_email=NEW_PERSON[1]).one().status == STATUS_LOCAL_CAPTURED


def test_no_confirmation_when_the_invitation_was_not_delivered(app):
    app.config["CALIBRAYTAI_HOSTED"] = "1"  # captured mail is not delivery on a hosted office
    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1]})
    assert "data-one-time-link" in response.get_data(as_text=True)
    with app.app_context():
        assert TransactionalMessage.query.filter_by(template_id="INVITATION_SENT_CONFIRMATION").count() == 0


def test_the_confirmation_template_cannot_render_a_link():
    from app.services.transactional_email import _render

    subject, body = _render("INVITATION_SENT_CONFIRMATION", {
        "kind": "invitation", "person_name": "Nora", "person_email": "nora@example.invalid",
        "sent_at": "Oct 23, 2026 at 9:00 AM", "expires": "Oct 26, 2026 at 9:00 AM",
        "reset_url": "https://x.invalid/reset-password#abc.def", "invitation_url": "https://x.invalid/i/abc"})
    assert "abc" not in body and "reset-password" not in body and "http" not in body
    assert subject == "Your CalibraytAI invitation to Nora was sent"


def test_the_training_site_sends_the_same_confirmation_when_its_mail_server_accepts(app):
    """The training site uses the same code: captured mail is never delivery there, so the confirmation goes only
    when a real mail service accepted the invitation (here a synthetic transport that accepts everything)."""
    from app.services.transactional_email import TransportResult

    sent = []

    class Accepting:
        def send(self, payload):
            sent.append(payload)
            return TransportResult(status="ACCEPTED", provider="fake", provider_message_id=f"m{len(sent)}")

    app.config["TRAINING_ENVIRONMENT"] = True
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = Accepting()
    owner = _client(app, OWNER)
    response = owner.post("/settings/people/new", data={"display_name": NEW_PERSON[0], "email": NEW_PERSON[1]},
                          follow_redirects=True)
    assert 'data-one-time-link-emailed="yes"' in response.get_data(as_text=True)
    assert [p.template_id for p in sent] == [TEMPLATE_ACCOUNT_INVITATION, "INVITATION_SENT_CONFIRMATION"]
    invitation, note = sent
    assert invitation.to_email == NEW_PERSON[1] and note.to_email == OWNER[0]
    credential = re.search(r"/reset-password#([A-Za-z0-9_\-.]+)", invitation.text_body).group(1)
    for forbidden in (credential, credential.split(".")[0], credential.rsplit(".", 1)[1], "/reset-password"):
        assert forbidden not in note.text_body and forbidden not in note.subject
    assert not any(k in note.variables for k in ("reset_url", "invitation_url", "token", "secret"))
