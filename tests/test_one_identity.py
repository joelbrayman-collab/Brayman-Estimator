"""One CalibraytAI identity across Production and the Training Centre (Joel, 26 Oct 2026). Synthetic data only.

Two separate apps with separate databases, as in real life: "production" is the identity provider, "training" is
connected to it. The Training Centre's calls reach Production's /identity/api through Production's own test client.
Proves: one email + one password everywhere a person is authorized; password changes and resets from either site
work on both; adding a person creates one identity; existing identities are never overwritten; roles stay per site;
practice personas stay local; the owner always gets a link; emergency links; reconciliation.
"""

from __future__ import annotations

import os
import re

import pytest

from app import create_app, db
from app.models.user import User, UserMembership
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.auth_fixtures import ensure_office_user

pytestmark = pytest.mark.no_office_auth

SECRET = "synthetic-identity-secret-0123456789abcdefghij"
OWNER = ("joel.owner@example.com", "Synthetic-owner-pass-1", "Joel Owner (synthetic)")
BEN = ("ben.both@example.com", "Synthetic-ben-prod-1", "Ben Both (synthetic)")
KEVIN = ("kevin.reviewer@example.com", "Kevin Reviewer (synthetic)")
PERSONA = ("olivia@training.calibraytai.invalid", "Synthetic-olivia-1", "Olivia Office (training)")


def _app(tmp_path, name, **extra):
    config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / (name + '.db')}",
              "SECRET_KEY": f"secret-{name}", "WTF_CSRF_ENABLED": False, "TRANSACTIONAL_EMAIL_PROVIDER": "local",
              "MAIL_CAPTURE_ROOT": str(tmp_path / f"mail-{name}"), **extra}
    application = create_app(config)
    with application.app_context():
        db.create_all()
        owner = ensure_office_user(email=OWNER[0], password=OWNER[1], display_name=OWNER[2])
        set_instance_owner(ORG, UserMembership.query.filter_by(user_id=owner.id).one().id, owner.id)
    return application


@pytest.fixture
def sites(tmp_path):
    production = _app(tmp_path, "production", IDENTITY_CLIENTS=f"training={SECRET}",
                      IDENTITY_TRAINING_SITE_URL="https://training.example.invalid",
                      PUBLIC_BASE_URL="https://production.example.invalid")
    with production.app_context():
        ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
    provider = production.test_client()

    def transport(action, payload):
        response = provider.post(f"/identity/api/{action}", json=payload,
                                 headers={"Authorization": f"Bearer training:{SECRET}"})
        return response.status_code, (response.get_json(silent=True) or {})

    training = _app(tmp_path, "training", IDENTITY_PROVIDER_URL="https://production.example.invalid",
                    IDENTITY_CLIENT_ID="training", IDENTITY_CLIENT_SECRET=SECRET, IDENTITY_TRANSPORT=transport,
                    PUBLIC_BASE_URL="https://training.example.invalid")
    with training.app_context():
        ensure_office_user(email=PERSONA[0], password=PERSONA[1], display_name=PERSONA[2])
    return production, training


def _signin(app, email, password):
    client = app.test_client()
    response = client.post("/login", data={"email": email, "password": password})
    return client, response


def _ok(app, email, password):
    _client, response = _signin(app, email, password)
    return response.status_code == 302 and "/login" not in response.headers.get("Location", "")


def _owner(app):
    client, response = _signin(app, OWNER[0], OWNER[1])
    assert response.status_code == 302
    return client


def _captured(app, email):
    root = app.config["MAIL_CAPTURE_ROOT"]
    if not os.path.isdir(root):
        return []
    out = []
    for name in sorted(os.listdir(root)):
        text = open(os.path.join(root, name), encoding="utf-8").read()
        if f"To: {email}" in text:
            out.append(text)
    return out


def _credential(text):
    return re.search(r"/reset-password#([A-Za-z0-9_\-.]+)", text).group(1)


def _set_password(app, credential, password):
    response = app.test_client().post("/reset-password", data={"credential": credential, "password": password,
                                                               "confirm_password": password})
    assert response.status_code == 302, response.get_data(as_text=True)[:400]
    return response


def _add_on_training(training, name, email):
    owner = _owner(training)
    return owner.post("/settings/people/new", data={"display_name": name, "email": email}, follow_redirects=True)


# ------------------------------------------------------------------ the connection itself


def test_the_identity_api_is_closed_unless_configured_and_needs_the_sites_credentials(sites, tmp_path):
    production, _training = sites
    client = production.test_client()
    assert client.post("/identity/api/verify", json={"email": BEN[0], "password": BEN[1]}).status_code == 401
    assert client.post("/identity/api/verify", json={"email": BEN[0], "password": BEN[1]},
                       headers={"Authorization": "Bearer training:wrong-secret-0123456789abcdef"}).status_code == 401
    assert client.post("/identity/api/verify", json={"email": BEN[0], "password": BEN[1]},
                       headers={"Authorization": f"Bearer other:{SECRET}"}).status_code == 401
    plain = _app(tmp_path, "plain")  # a site without IDENTITY_CLIENTS
    assert plain.test_client().post("/identity/api/verify", json={}).status_code == 404
    ok = client.post("/identity/api/verify", json={"email": BEN[0], "password": BEN[1]},
                     headers={"Authorization": f"Bearer training:{SECRET}"}).get_json()
    assert ok["ok"] is True and set(ok) == {"ok", "name", "epoch"}  # never a password, hash or token


# ------------------------------------------------------------------ existing user: one password on both


def test_an_existing_production_user_signs_in_to_training_with_the_production_password(sites):
    production, training = sites
    html = _add_on_training(training, BEN[2], BEN[0]).get_data(as_text=True)
    assert "already has a CalibraytAI sign-in" in html and "data-one-time-link" not in html
    with production.app_context():  # Production was not changed
        ben = User.query.filter_by(email=BEN[0]).one()
        assert ben.credentials_epoch in (0, None)
    assert _ok(training, BEN[0], BEN[1]) and _ok(production, BEN[0], BEN[1])
    assert not _ok(training, BEN[0], "wrong-password")
    with training.app_context():  # the Training Centre's own random hash is never what signs him in
        assert User.query.filter_by(email=BEN[0]).one().password_hash != ""


def test_training_only_access_is_still_the_sites_choice(sites):
    """Ben has a Production identity but no Training Centre account: right password, no access there."""
    _production, training = sites
    client, response = _signin(training, BEN[0], BEN[1])
    assert response.status_code == 200
    assert "this site has not given you access" in response.get_data(as_text=True)


# ------------------------------------------------------------------ a new person: added once, one password


def test_a_new_reviewer_added_on_training_gets_one_identity_and_the_owner_gets_the_link(sites):
    production, training = sites
    response = _add_on_training(training, KEVIN[1], KEVIN[0])
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    shown = re.search(r'id="one-time-link" value="([^"]+)"', html).group(1)
    assert shown.startswith("https://production.example.invalid/reset-password#")  # Production's link
    assert "Text it" in html and 'data-one-time-link-emailed="yes"' in html
    invitation = _captured(production, KEVIN[0])
    assert len(invitation) == 1 and _credential(invitation[0]) == shown.split("#", 1)[1]
    with production.app_context():
        kevin = User.query.filter_by(email=KEVIN[0]).one()
        assert UserMembership.query.filter_by(user_id=kevin.id).count() == 0  # identity only: no Production access
    _set_password(production, shown.split("#", 1)[1], "Synthetic-Kevin-new-1")
    assert _ok(training, KEVIN[0], "Synthetic-Kevin-new-1")
    client, refused = _signin(production, KEVIN[0], "Synthetic-Kevin-new-1")
    text = refused.get_data(as_text=True)
    assert refused.status_code == 200 and "give no access to this site" in text
    assert "https://training.example.invalid" in text
    assert client.get("/").status_code == 302  # not signed in to Production
    # the reset page on Production points at the Training Centre too
    assert "data-also-training" in production.test_client().get("/reset-password/complete").get_data(as_text=True)


# ------------------------------------------------------------------ password changes, from either site


def _change(app, email, current, new):
    client, _ = _signin(app, email, current)
    return client.post("/account/password", data={"current_password": current, "password": new,
                                                  "confirm_password": new})


def test_changing_the_password_on_training_changes_it_everywhere(sites):
    production, training = sites
    _add_on_training(training, BEN[2], BEN[0])
    response = _change(training, BEN[0], BEN[1], "Synthetic-ben-changed-2")
    assert response.status_code == 302
    for site in (production, training):
        assert _ok(site, BEN[0], "Synthetic-ben-changed-2")
        assert not _ok(site, BEN[0], BEN[1])
    wrong = _change(training, BEN[0], "Synthetic-ben-changed-2", "short")
    assert "at least 8 characters" in wrong.get_data(as_text=True)


def test_changing_the_password_on_production_changes_it_on_training(sites):
    production, training = sites
    _add_on_training(training, BEN[2], BEN[0])
    assert _change(production, BEN[0], BEN[1], "Synthetic-ben-prod-2").status_code == 302
    assert _ok(training, BEN[0], "Synthetic-ben-prod-2") and not _ok(training, BEN[0], BEN[1])


def test_a_wrong_current_password_on_training_is_refused_by_production(sites):
    _production, training = sites
    _add_on_training(training, BEN[2], BEN[0])
    client, _ = _signin(training, BEN[0], BEN[1])
    html = client.post("/account/password", data={"current_password": "not-it", "password": "Synthetic-x-1234",
                                                 "confirm_password": "Synthetic-x-1234"}).get_data(as_text=True)
    assert "current password is not correct" in html


# ------------------------------------------------------------------ forgot password, from either site


@pytest.mark.parametrize("start", ["training", "production"])
def test_forgot_password_from_either_site_gives_one_new_password_for_both(sites, start):
    production, training = sites
    _add_on_training(training, BEN[2], BEN[0])
    site = training if start == "training" else production
    assert site.test_client().post("/forgot-password", data={"email": BEN[0]}).status_code == 302
    resets = [t for t in _captured(production, BEN[0]) if "Reset your CalibraytAI password" in t]
    assert len(resets) == 1  # Production sent it, whichever site it started from
    assert _captured(training, BEN[0]) == []
    _set_password(production, _credential(resets[0]), "Synthetic-ben-reset-3")
    for s in (production, training):
        assert _ok(s, BEN[0], "Synthetic-ben-reset-3") and not _ok(s, BEN[0], BEN[1])


def test_a_never_signed_in_reviewer_can_use_forgot_password_from_training(sites):
    production, training = sites
    _add_on_training(training, KEVIN[1], KEVIN[0])
    training.test_client().post("/forgot-password", data={"email": KEVIN[0]})
    reset = [t for t in _captured(production, KEVIN[0]) if "Reset your CalibraytAI password" in t]
    assert len(reset) == 1
    _set_password(production, _credential(reset[0]), "Synthetic-Kevin-reset-4")
    assert _ok(training, KEVIN[0], "Synthetic-Kevin-reset-4")


# ------------------------------------------------------------------ what stays local, and failures


def test_practice_personas_keep_signing_in_locally(sites):
    production, training = sites
    assert _ok(training, PERSONA[0], PERSONA[1])
    with production.app_context():
        assert User.query.filter_by(email=PERSONA[0]).first() is None  # never sent to Production


def test_when_production_cannot_be_reached_training_says_so(sites):
    _production, training = sites

    def down(action, payload):
        return 503, {}

    training.config["IDENTITY_TRANSPORT"] = down
    _client, response = _signin(training, BEN[0], BEN[1])
    assert "CalibraytAI sign-in is not answering right now" in response.get_data(as_text=True)
    assert _ok(training, PERSONA[0], PERSONA[1])  # practice personas are unaffected


def test_ten_wrong_passwords_lock_the_identity_for_fifteen_minutes(sites):
    production, training = sites
    _add_on_training(training, BEN[2], BEN[0])
    for _ in range(10):
        _signin(training, BEN[0], "wrong-password")
    _client, response = _signin(training, BEN[0], BEN[1])
    assert "Too many wrong passwords" in response.get_data(as_text=True)


def test_provision_never_changes_an_existing_identity_and_import_never_overwrites(sites):
    production, _training = sites
    client = production.test_client()
    headers = {"Authorization": f"Bearer training:{SECRET}"}
    answer = client.post("/identity/api/provision", json={"email": BEN[0], "name": "Someone else"},
                         headers=headers).get_json()
    assert answer == {"existing": True, "active": True, "name": BEN[2]}
    answer = client.post("/identity/api/import", json={"email": BEN[0], "name": "x",
                                                       "password_hash": "pbkdf2:sha256:1$abc$def"},
                         headers=headers).get_json()
    assert answer == {"existing": True}
    assert _ok(production, BEN[0], BEN[1])


# ------------------------------------------------------------------ reconciliation and emergency access


def test_reconcile_lists_then_carries_a_training_only_password_to_production(sites):
    from app.services.auth import hash_password

    production, training = sites
    with training.app_context():  # someone who existed only on the Training Centre before today
        old = ensure_office_user(email="early.tester@example.com", password="Synthetic-early-1",
                                 display_name="Early Tester (synthetic)")
        ensure_office_user(email=BEN[0], password="Synthetic-ben-training-old", display_name=BEN[2])
        assert old.password_hash
    runner = training.test_cli_runner()
    dry = runner.invoke(args=["identity", "reconcile"]).output
    assert "DRY RUN" in dry and "ea***@example.com (active here): only here" in dry
    assert "be***@example.com (active here): on both: Production's password wins" in dry
    assert "olivia" not in dry  # practice personas are not people
    with production.app_context():
        assert User.query.filter_by(email="early.tester@example.com").first() is None
    applied = runner.invoke(args=["identity", "reconcile", "--apply"]).output
    assert "created on Production with the password chosen here" in applied
    assert _ok(training, "early.tester@example.com", "Synthetic-early-1")  # their own password still works
    assert _ok(training, BEN[0], BEN[1]) and not _ok(training, BEN[0], "Synthetic-ben-training-old")
    with production.app_context():
        early = User.query.filter_by(email="early.tester@example.com").one()
        assert UserMembership.query.filter_by(user_id=early.id).count() == 0
    assert hash_password("x") != ""


def test_emergency_link_on_training_comes_from_production_and_works_everywhere(sites):
    production, training = sites
    _add_on_training(training, BEN[2], BEN[0])
    output = training.test_cli_runner().invoke(args=["auth", "issue-link", "--email", BEN[0]]).output
    link = re.search(r"(https://production\.example\.invalid/reset-password#\S+)", output).group(1)
    assert _captured(production, BEN[0]) == []  # no email
    _set_password(production, link.split("#", 1)[1], "Synthetic-ben-emergency-5")
    assert _ok(training, BEN[0], "Synthetic-ben-emergency-5") and _ok(production, BEN[0], "Synthetic-ben-emergency-5")


def test_emergency_link_on_production_for_the_owner(sites):
    production, _training = sites
    output = production.test_cli_runner().invoke(args=["auth", "issue-link", "--email", OWNER[0]]).output
    link = re.search(r"(https://production\.example\.invalid/reset-password#\S+)", output).group(1)
    _set_password(production, link.split("#", 1)[1], "Synthetic-owner-recovered-6")
    assert _ok(production, OWNER[0], "Synthetic-owner-recovered-6")


def test_roles_stay_per_site(sites):
    """Kevin: identity on Production, office access only on the Training Centre; the Training Centre owner's
    People & Access stays closed to him there."""
    production, training = sites
    response = _add_on_training(training, KEVIN[1], KEVIN[0])
    link = re.search(r'id="one-time-link" value="([^"]+)"', response.get_data(as_text=True)).group(1)
    _set_password(production, link.split("#", 1)[1], "Synthetic-Kevin-roles-7")
    client, response = _signin(training, KEVIN[0], "Synthetic-Kevin-roles-7")
    assert response.status_code == 302
    assert client.get("/settings/people").status_code == 403
    assert client.get("/").status_code == 200


# ------------------------------------------------------------------ Joel's one identity on Production (owner-setup)


def test_owner_setup_makes_one_identity_the_owner_and_moves_its_supplier_login(tmp_path):
    """As found on Production 26 Oct 2026: the owner is joel@braymanconstruction.ca, and the Gmail address is only a
    Supplier Hub login. owner-setup lists first, then: the Supplier Hub login moves to another address, Gmail becomes
    a member and Instance Owner, the previous owner stays as System Administrator. Passwords are untouched."""
    from app.models.supplier_portal import SupplierUserMembership
    from app.services.instance_authority import is_instance_owner, is_system_administrator
    from app.services.supplier_catalogue import (
        create_contractor_supplier_account,
        create_supplier,
        create_supplier_location,
    )
    from app.services.supplier_hub import add_supplier_user, principal_class

    application = _app(tmp_path, "owner")  # OWNER (joel.owner@example.com) is the Instance Owner
    gmail, moved_to = "joel.gmail@example.com", "joel.supplier@example.com"
    with application.app_context():
        supplier = create_supplier(code="SYN-STORE", legal_name="Synthetic Store")
        location = create_supplier_location(supplier_id=supplier.id, code="SYN-1", display_name="Synthetic Store 1")
        create_contractor_supplier_account(organization_id=ORG, supplier_id=supplier.id, supplier_location_id=location.id)
        db.session.commit()
        user, _ = add_supplier_user(organization_id=ORG, supplier=supplier, display_name="Joel Gmail (synthetic)",
                                    email=gmail, actor_name="test")
        from app.services.auth import hash_password
        user.password_hash = hash_password("Synthetic-gmail-1")
        db.session.commit()
    runner = application.test_cli_runner()
    refused = runner.invoke(args=["identity", "owner-setup", "--owner-email", gmail])
    assert refused.exit_code != 0 and "give --supplier-to" in refused.output
    dry = runner.invoke(args=["identity", "owner-setup", "--owner-email", gmail, "--supplier-to", moved_to]).output
    assert "DRY RUN" in dry and "jo***@example.com -> jo***@example.com" in dry and "add as a member" in dry
    with application.app_context():
        assert SupplierUserMembership.query.filter_by(status="ACTIVE").count() == 1  # nothing changed yet
    done = runner.invoke(args=["identity", "owner-setup", "--owner-email", gmail, "--supplier-to", moved_to, "--apply"])
    assert done.exit_code == 0, done.output
    with application.app_context():
        owner = User.query.filter_by(email=gmail).one()
        previous = User.query.filter_by(email=OWNER[0]).one()
        assert is_instance_owner(owner, ORG) and not is_instance_owner(previous, ORG)
        assert is_system_administrator(previous, ORG)
        assert principal_class(owner) == "CONTRACTOR"
        mover = User.query.filter_by(email=moved_to).one()
        assert SupplierUserMembership.query.filter_by(user_id=mover.id, status="ACTIVE").count() == 1
        assert SupplierUserMembership.query.filter_by(user_id=owner.id, status="REVOKED").count() == 1
    assert _ok(application, gmail, "Synthetic-gmail-1")  # same password as before
    owner_client, _ = _signin(application, gmail, "Synthetic-gmail-1")
    assert owner_client.get("/settings/people").status_code == 200
    assert _ok(application, OWNER[0], OWNER[1])


def test_owner_setup_on_training_creates_the_owner_who_then_signs_in_with_the_production_password(sites):
    from app.services.instance_authority import is_instance_owner, is_system_administrator
    from app.training import service as svc

    production, training = sites  # BEN's identity exists on Production; not on the Training Centre
    runner = training.test_cli_runner()
    refused = runner.invoke(args=["identity", "owner-setup", "--owner-email", BEN[0]])
    assert refused.exit_code != 0 and "--create" in refused.output
    dry = runner.invoke(args=["identity", "owner-setup", "--owner-email", BEN[0], "--create", "Ben Both"]).output
    assert "will be created" in dry and "DRY RUN" in dry
    with training.app_context():
        assert User.query.filter_by(email=BEN[0]).first() is None
    done = runner.invoke(args=["identity", "owner-setup", "--owner-email", BEN[0], "--create", "Ben Both", "--apply"])
    assert done.exit_code == 0, done.output
    with training.app_context():
        ben = User.query.filter_by(email=BEN[0]).one()
        previous = User.query.filter_by(email=OWNER[0]).one()
        assert is_instance_owner(ben, ORG) and is_system_administrator(previous, ORG)
        assert svc.is_admin(ben) == ORG  # the Training Centre administrator
    client, response = _signin(training, BEN[0], BEN[1])  # his one (Production) password
    assert response.status_code == 302 and client.get("/settings/people").status_code == 200
