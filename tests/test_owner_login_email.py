"""Joel's permanent login (15 Oct 2026): user 1's email becomes joel@braymanconstruction.ca.

Proves on a disposable database that once the email is changed the sign-in page asks for
credentials, the temporary email no longer signs in, and the same password works with the new
email. Moving the credentials epoch on ends sessions made before the change. (Until 18 Oct 2026
this ran with the UAT bypass switch on; the bypass is removed, so the earlier session now signs
in with the password.)
"""

from flask import g

from app import db
from app.models import User
from tests.hosted_app_support import HTTPS, _app, _hosted, _seed_user_one

NEW = "joel@braymanconstruction.ca"


def _fresh(client, method, path, **kwargs):
    # The test holds one app context open; drop Flask-Login's per-context cache of the signed-in
    # user so each request loads its own session, as separate browser requests do.
    g.pop("_login_user", None)
    kwargs.setdefault("base_url", HTTPS)
    return getattr(client, method)(path, **kwargs)


def _get(client, path):
    return _fresh(client, "get", path)


def _post(client, path, data):
    return _fresh(client, "post", path, data=data)


def _change_email(user):
    user.email = NEW
    user.credentials_epoch = int(user.credentials_epoch or 0) + 1
    db.session.commit()


def test_after_the_email_change_old_sessions_end_and_the_password_signs_in():
    with _app(_hosted()) as application:
        old_session = application.test_client()
        user = _seed_user_one()
        signed = _post(old_session, "/login", {"email": "uat@example.invalid", "password": "office-test-password"})
        assert signed.status_code == 302  # signed in before the change
        assert _get(old_session, "/").status_code == 200

        _change_email(db.session.get(User, user.id))

        assert _get(old_session, "/").status_code == 302  # earlier session ended by the epoch
        visitor = application.test_client()
        page = _get(visitor, "/login")
        assert page.status_code == 200 and b'name="password"' in page.data  # no automatic sign-in
        assert _get(visitor, "/").status_code == 302
        old_email = _post(visitor, "/login", {"email": "uat@example.invalid", "password": "office-test-password"})
        assert old_email.status_code == 200  # the temporary email no longer signs in
        signed_in = _post(visitor, "/login", {"email": NEW, "password": "office-test-password"})
        assert signed_in.status_code == 302
        assert _get(visitor, "/").status_code == 200
        assert db.session.get(User, user.id).id == user.id  # same account, same id
