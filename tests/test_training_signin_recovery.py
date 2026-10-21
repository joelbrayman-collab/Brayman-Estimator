"""Training site sign-in and password recovery (Joel, 21 Oct 2026).

Joel's sign-in to the training site was refused and no reset email came. Causes: the training site had no
account for its real administrator (only synthetic people with .invalid addresses), it could not send email
(no mail service), its pages did not say so, and on-screen links fell back to http://localhost. These tests
hold the fix: an administrator account from the site's settings, the sign-in method stated on every sign-in
page, an honest forgot-password page, one-use expiring links an administrator can give in person (contractor
staff from People & Access, supplier staff from Company -> Suppliers), wrong passwords refused.
Synthetic data only; no password or link is printed."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import pytest
from flask import g

from app import create_app, db
from app.models.password_reset import PasswordResetToken
from app.models.supplier_portal import SupplierUserMembership
from app.models.user import User
from app.services.instance_authority import is_system_administrator
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.transactional_email import TransportResult
from app.training import environment

pytestmark = pytest.mark.no_office_auth
PW = {k: f"Synthetic-{k}-training-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat", "admin")}
ADMIN = ("Joel Brayman", "joel.admin@training-test.invalid")
NEW_PW = "Synthetic-new-password-42"
HOST = "https://training.example.test"
LINK = re.compile(r"(https?://[^\s\"'<]+)?(/reset-password/[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)")


def _app(**extra):
    config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
              "WTF_CSRF_ENABLED": False, "TRAINING_ENVIRONMENT": True}
    config.update(extra)
    return create_app(config)


@pytest.fixture
def app():
    application = _app()
    with application.app_context():
        db.create_all()
        environment.build(application, PW, administrator=ADMIN)
        yield application
        db.session.remove()
        db.drop_all()


def _email(key):
    return next(e for k, _n, e, *_ in environment.OFFICE_PEOPLE + environment.SUPPLIER_PEOPLE if k == key)


def _get(client, path, **kw):
    g.pop("_login_user", None)
    return client.get(path, **kw)


def _post(client, path, **kw):
    g.pop("_login_user", None)
    return client.post(path, **kw)


def _sign_in(app, email, password, base_url=None):
    client = app.test_client()
    kw = {"base_url": base_url} if base_url else {}
    return client, _post(client, "/login", data={"email": email, "password": password}, **kw)


class _Accepting:
    """A mail service that accepts every message (stands in for Postmark)."""

    def __init__(self):
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)
        return TransportResult(status="ACCEPTED", provider="fake", provider_message_id="m1")


# ------------------------------------------------------------------ the administrator account

def test_administrator_account_from_the_site_settings(app):
    admin = User.query.filter_by(email=ADMIN[1]).one()
    assert admin.display_name == "Joel Brayman" and admin.is_active
    assert is_system_administrator(admin, "ORG-001")
    client, r = _sign_in(app, ADMIN[1], PW["admin"])
    assert r.status_code == 302
    assert _get(client, "/training/admin").status_code == 200
    assert _get(client, "/settings/people").status_code == 200


def test_building_again_keeps_the_administrator_password(app):
    environment.build(app, {"admin": "Something-else-entirely-9"}, administrator=ADMIN)
    _client, r = _sign_in(app, ADMIN[1], PW["admin"])
    assert r.status_code == 302
    assert User.query.filter_by(email=ADMIN[1]).count() == 1


def test_administrator_from_env(monkeypatch):
    monkeypatch.delenv("TRAINING_ADMIN_EMAIL", raising=False)
    assert environment.administrator_from_env() is None
    monkeypatch.setenv("TRAINING_ADMIN_EMAIL", " Joel.Admin@Training-Test.invalid ")
    monkeypatch.setenv("TRAINING_ADMIN_NAME", "Joel Brayman")
    assert environment.administrator_from_env() == ("Joel Brayman", "joel.admin@training-test.invalid")


# ------------------------------------------------------------------ sign-in

def test_wrong_password_is_refused_and_right_one_works(app):
    _c, bad = _sign_in(app, ADMIN[1], "not-the-password")
    assert bad.status_code == 200 and "/training" not in bad.headers.get("Location", "")
    _c, unknown = _sign_in(app, "nobody@training-test.invalid", "whatever-1234")
    assert unknown.status_code == 200
    _c, good = _sign_in(app, _email("ben"), PW["ben"])
    assert good.status_code == 302


def test_every_sign_in_page_states_the_training_method(app):
    client = app.test_client()
    for path in ("/training/signin", "/login", "/supplier/login"):
        page = client.get(path).get_data(as_text=True)
        assert "data-training-signin-method" in page, path
        assert "training account" in page and "ChatGPT" in page, path
    assert "Training sign in" in client.get("/login").get_data(as_text=True)


def test_office_sign_in_is_unchanged_off_the_training_site():
    application = _app(TRAINING_ENVIRONMENT=False)
    with application.app_context():
        db.create_all()
        page = application.test_client().get("/login").get_data(as_text=True)
        assert "Office sign in" in page and "data-training-signin-method" not in page
        db.drop_all()


# ------------------------------------------------------------------ forgot password

def test_without_a_mail_service_the_forgot_pages_say_so(app):
    client = app.test_client()
    form = client.get("/forgot-password").get_data(as_text=True)
    assert "data-no-email" in form and "People &amp; Access" in form
    r = client.post("/forgot-password", data={"email": ADMIN[1]})
    sent = client.get(r.headers["Location"]).get_data(as_text=True)
    assert "no email is on its way" in sent
    # the same words whether or not the address has an account
    r2 = client.post("/forgot-password", data={"email": "nobody@training-test.invalid"})
    assert client.get(r2.headers["Location"]).get_data(as_text=True) == sent
    supplier = client.get("/forgot-password?portal=supplier").get_data(as_text=True)
    assert "Company &rarr; Suppliers" in supplier


def test_with_a_mail_service_forgot_password_emails_a_one_use_expiring_link(app):
    mail = _Accepting()
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = mail
    app.config["PUBLIC_BASE_URL"] = "https://training.example.test"
    client = app.test_client()
    assert "data-no-email" not in client.get("/forgot-password").get_data(as_text=True)
    r = client.post("/forgot-password", data={"email": ADMIN[1]})
    assert "data-no-email" not in client.get(r.headers["Location"]).get_data(as_text=True)
    assert len(mail.sent) == 1 and mail.sent[0].to_email == ADMIN[1]
    base, path = LINK.search(mail.sent[0].text_body).groups()
    assert base == "https://training.example.test"
    assert _get(client, path).status_code == 200
    done = _post(client, path, data={"password": NEW_PW, "confirm_password": NEW_PW})
    assert done.status_code == 302
    # used once: the same link is refused, the old password no longer works, the new one does
    again = _post(client, path, data={"password": NEW_PW + "x", "confirm_password": NEW_PW + "x"})
    assert "reset" in again.get_data(as_text=True).lower() and again.status_code == 200
    assert _sign_in(app, ADMIN[1], PW["admin"])[1].status_code == 200
    assert _sign_in(app, ADMIN[1], NEW_PW)[1].status_code == 302


def test_an_expired_link_is_refused(app):
    mail = _Accepting()
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = mail
    client = app.test_client()
    client.post("/forgot-password", data={"email": ADMIN[1]})
    _base, path = LINK.search(mail.sent[0].text_body).groups()
    token = PasswordResetToken.query.order_by(PasswordResetToken.id.desc()).first()
    token.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.session.commit()
    r = _post(client, path, data={"password": NEW_PW, "confirm_password": NEW_PW})
    assert r.status_code == 200
    assert _sign_in(app, ADMIN[1], NEW_PW)[1].status_code == 200


def test_a_newer_link_replaces_the_older_one(app):
    mail = _Accepting()
    app.config["TRANSACTIONAL_EMAIL_TRANSPORT"] = mail
    client = app.test_client()
    client.post("/forgot-password", data={"email": ADMIN[1]})
    client.post("/forgot-password", data={"email": ADMIN[1]})
    first = LINK.search(mail.sent[0].text_body).group(2)
    second = LINK.search(mail.sent[1].text_body).group(2)
    _post(client, first, data={"password": NEW_PW, "confirm_password": NEW_PW})
    assert _sign_in(app, ADMIN[1], NEW_PW)[1].status_code == 200
    assert _post(client, second, data={"password": NEW_PW, "confirm_password": NEW_PW}).status_code == 302


# ------------------------------------------------------------------ administrator recovery

def _one_time_link(page):
    m = LINK.search(page)
    assert m, "no one-time link on the page"
    return m.group(1), m.group(2)


def test_administrator_gives_office_staff_a_one_time_link(app):
    admin, _r = _sign_in(app, ADMIN[1], PW["admin"], base_url=HOST)
    from app.models.user import UserMembership

    olivia = User.query.filter_by(email=_email("olivia")).one()
    membership = UserMembership.query.filter_by(user_id=olivia.id).one()
    r = _post(admin, f"/settings/people/{membership.id}/send-link", base_url=HOST)
    page = r.get_data(as_text=True)
    base, path = _one_time_link(page)
    assert base == "https://training.example.test", "the link must not point at localhost"
    assert r.headers.get("Cache-Control") == "no-store"
    fresh = app.test_client()
    assert _post(fresh, path, data={"password": NEW_PW, "confirm_password": NEW_PW}).status_code == 302
    assert _sign_in(app, _email("olivia"), NEW_PW)[1].status_code == 302
    assert _post(fresh, path, data={"password": NEW_PW, "confirm_password": NEW_PW}).status_code == 200


def test_administrator_gives_supplier_staff_a_one_time_link(app):
    admin, _r = _sign_in(app, ADMIN[1], PW["admin"], base_url=HOST)
    darcy = User.query.filter_by(email=_email("darcy")).one()
    membership = SupplierUserMembership.query.filter_by(user_id=darcy.id).one()
    page = _get(admin, "/suppliers", base_url=HOST).get_data(as_text=True)
    assert f'data-supplier-send-link="{membership.id}"' in page
    r = _post(admin, f"/suppliers/memberships/{membership.id}/send-link", base_url=HOST)
    assert r.status_code == 200 and r.headers.get("Cache-Control") == "no-store"
    base, path = _one_time_link(r.get_data(as_text=True))
    assert base == "https://training.example.test"
    fresh = app.test_client()
    assert _post(fresh, path, data={"password": NEW_PW, "confirm_password": NEW_PW}).status_code == 302
    signed = fresh.post("/supplier/login", data={"email": _email("darcy"), "password": NEW_PW, "next": "/training"})
    assert signed.status_code == 302
    # the link is gone from the next page view
    assert LINK.search(_get(admin, "/suppliers", base_url=HOST).get_data(as_text=True)) is None


def test_a_new_supplier_person_gets_an_activation_link(app):
    admin, _r = _sign_in(app, ADMIN[1], PW["admin"], base_url=HOST)
    darcy = User.query.filter_by(email=_email("darcy")).one()
    supplier_id = SupplierUserMembership.query.filter_by(user_id=darcy.id).one().supplier_id
    r = _post(admin, f"/suppliers/{supplier_id}/users", base_url="https://training.example.test",
              data={"display_name": "Sam (BMR training)", "email": "sam@training-test.invalid"})
    _base, path = _one_time_link(r.get_data(as_text=True))
    fresh = app.test_client()
    assert _post(fresh, path, data={"password": NEW_PW, "confirm_password": NEW_PW}).status_code == 302
    r = fresh.post("/supplier/login", data={"email": "sam@training-test.invalid", "password": NEW_PW,
                                            "next": "/training"})
    assert r.status_code == 302


def test_supplier_links_are_refused_for_removed_and_unrelated_sign_ins(app):
    admin, _r = _sign_in(app, ADMIN[1], PW["admin"])
    pat = User.query.filter_by(email=_email("pat")).one()
    membership = SupplierUserMembership.query.filter_by(user_id=pat.id).one()
    membership.status = "REVOKED"
    db.session.commit()
    r = _post(admin, f"/suppliers/memberships/{membership.id}/send-link")
    assert r.status_code == 302 and PasswordResetToken.query.filter_by(user_id=pat.id).count() == 0
    assert _post(admin, "/suppliers/memberships/999999/send-link").status_code == 404
    # field crew cannot send links
    kevin, _r = _sign_in(app, _email("kevin"), PW["kevin"])
    darcy = User.query.filter_by(email=_email("darcy")).one()
    m = SupplierUserMembership.query.filter_by(user_id=darcy.id).one()
    assert _post(kevin, f"/suppliers/memberships/{m.id}/send-link").status_code in (302, 403, 404)
    assert PasswordResetToken.query.filter_by(user_id=darcy.id).count() == 0


# ------------------------------------------------------------------ owner review of the Workflow Maps

def test_owner_reviews_both_maps_without_registering(app):
    from app.models.training import TrainingTrainee

    admin, _r = _sign_in(app, ADMIN[1], PW["admin"])
    home = _get(admin, "/training").get_data(as_text=True)
    assert 'data-owner-review-start' in home and 'data-review-map-link="supplier"' in home
    for key in ("contractor", "supplier", "field"):
        r = _get(admin, f"/training/review/{key}")
        page = r.get_data(as_text=True)
        assert r.status_code == 200 and f'data-review-map="{key}"' in page, key
        hrefs = set(re.findall(r'href="(/training/review/(?:lessons|uat)/[^"]+)"', page))
        assert hrefs, f"no lessons or tests on the {key} map"
        for href in hrefs:
            sub = _get(admin, href.replace("&amp;", "&"))
            assert sub.status_code == 200, href
            back = re.search(r'data-review-back[^>]*|href="([^"]+)"[^>]*data-review-back', sub.get_data(as_text=True))
            assert f"/training/review/{key}" in sub.get_data(as_text=True), href
        # every stage opens on its own (?stage=) and keeps the place
        stages = set(re.findall(r'href="/training/review/' + key + r'\?stage=([a-z0-9_-]+)', page))
        assert stages
        for sid in stages:
            assert _get(admin, f"/training/review/{key}?stage={sid}").status_code == 200
    assert TrainingTrainee.query.count() == 0, "review must not register anyone"
    # the trainee map link sends an unregistered administrator to review
    r = _get(admin, "/training/workflow")
    assert r.status_code == 302 and "/training/review/contractor" in r.headers["Location"]


def test_lesson_review_returns_to_the_same_stage(app):
    admin, _r = _sign_in(app, ADMIN[1], PW["admin"])
    page = _get(admin, "/training/review/contractor").get_data(as_text=True)
    href = re.search(r'href="(/training/review/lessons/[^"]+stage=[^"]+)"', page).group(1).replace("&amp;", "&")
    stage = re.search(r"stage=([a-z0-9_-]+)", href).group(1)
    lesson = _get(admin, href).get_data(as_text=True)
    assert f"/training/review/contractor?stage={stage}#workflow-stage" in lesson


def test_owner_review_is_for_administrators_only(app):
    for key in ("olivia", "kevin"):
        client, _r = _sign_in(app, _email(key), PW[key])
        assert _get(client, "/training/review").status_code == 403, key
        assert _get(client, "/training/review/supplier").status_code == 403, key
    darcy = app.test_client()
    darcy.post("/supplier/login", data={"email": _email("darcy"), "password": PW["darcy"], "next": "/training"})
    assert _get(darcy, "/training/review/contractor").status_code == 403
    assert _get(app.test_client(), "/training/review/contractor").status_code == 302  # signed out -> sign in


def test_supplier_map_review_explains_supplier_screens(app):
    admin, _r = _sign_in(app, ADMIN[1], PW["admin"])
    page = _get(admin, "/training/review/supplier").get_data(as_text=True)
    assert "Opens in the Supplier Hub for the supplier" in page
    assert 'href="/supplier/' not in page, "no Supplier Hub link the administrator cannot open"
