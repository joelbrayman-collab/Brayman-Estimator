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
    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(email=NEW_PERSON[1]).one()
        assert user.is_active and user.display_name == NEW_PERSON[0]
        membership = UserMembership.query.filter_by(user_id=user.id).one()
        assert membership.organization_id == ORG and membership.is_active
        assert response.headers["Location"].endswith(f"/settings/people/{membership.id}")
        message = TransactionalMessage.query.filter_by(to_email=NEW_PERSON[1]).one()
        assert message.template_id == TEMPLATE_PASSWORD_RESET
        assert message.status == STATUS_LOCAL_CAPTURED
        assert PasswordResetToken.query.filter_by(user_id=user.id, consumed_at=None).count() == 1
    mails = _captured(app, NEW_PERSON[1])
    assert len(mails) == 1
    link = re.search(r"/reset-password/[A-Za-z0-9_\-.]+", mails[0]).group(0)
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
        assert owner.post("/settings/people/new", data={"display_name": f"P{n}", "email": f"p{n}@example.invalid"}).status_code == 302
    with app.app_context():
        assert TransactionalMessage.query.count() == 6
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
    with caplog.at_level(logging.INFO, logger="people_access"):
        owner.post(f"/settings/people/{ids['staff_m']}/deactivate")
        owner.post(f"/settings/people/{ids['staff_m']}/reactivate")
        owner.post(f"/settings/people/{ids['staff_m']}/access", data={"domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT, "action": "grant"})
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
    assert response.status_code == 302, response.get_data(as_text=True)[:300]
    membership_id = int(response.headers["Location"].rstrip("/").rsplit("/", 1)[1])

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
