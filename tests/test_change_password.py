"""SEC-01: a signed-in person changes their own password; the owner can set one before the bypass is removed."""

from app import db
from app.models import User
from tests.test_uat_auth_bypass import (
    UAT_AUTH_BYPASS_ENV,
    _app,
    _get,
    _hosted,
    _local,
    _seed_user_one,
)

from tests.test_uat_auth_bypass import HTTPS  # noqa: E402


def _post(client, path, data):
    return client.post(path, data=data, base_url=HTTPS)


def _sign_in(client, email="uat@example.invalid", password="office-test-password"):
    return _post(client, "/login", {"email": email, "password": password})


def test_anonymous_visitors_are_sent_to_sign_in():
    with _app(_local()) as application:
        client = application.test_client()
        response = _get(client, "/account/password")
        assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_the_current_password_is_required_and_the_new_one_replaces_it():
    with _app(_local()) as application:
        client = application.test_client()
        _seed_user_one()
        _sign_in(client)
        page = _get(client, "/account/password")
        assert page.status_code == 200 and b"Current password" in page.data and b"uat@example.invalid" in page.data
        wrong = _post(client, "/account/password", {"current_password": "nope", "password": "new-pass-123", "confirm_password": "new-pass-123"})
        assert b"current password is not correct" in wrong.data
        mismatch = _post(client, "/account/password", {"current_password": "office-test-password", "password": "new-pass-123", "confirm_password": "other-pass-123"})
        assert b"do not match" in mismatch.data
        short = _post(client, "/account/password", {"current_password": "office-test-password", "password": "short", "confirm_password": "short"})
        assert b"at least 8 characters" in short.data
        done = _post(client, "/account/password", {"current_password": "office-test-password", "password": "new-pass-123", "confirm_password": "new-pass-123"})
        assert done.status_code == 302 and "/login" in done.headers["Location"]
        # Signed out; the old password fails, the new one works.
        assert _get(client, "/").status_code == 302
        assert b"Office home" not in _sign_in(client).data
        assert _sign_in(client, password="old-is-gone").status_code == 200
        assert _sign_in(client, password="new-pass-123").status_code == 302
        assert _get(client, "/").status_code == 200


def test_a_bypass_session_sets_the_owner_password_without_the_old_one():
    with _app(_hosted(**{UAT_AUTH_BYPASS_ENV: "1"})) as application:
        client = application.test_client()
        user = _seed_user_one()
        epoch = user.credentials_epoch or 0
        _get(client, "/login")  # the bypass signs in User 1
        page = _get(client, "/account/password")
        assert page.status_code == 200 and b"Current password" not in page.data
        done = _post(client, "/account/password", {"password": "owner-pass-123", "confirm_password": "owner-pass-123"})
        assert done.status_code == 302
        refreshed = db.session.get(User, user.id)
        assert (refreshed.credentials_epoch or 0) == epoch + 1
    # With the switch removed, the owner signs in with the new password only.
    with _app(_hosted()) as application:
        client = application.test_client()
        _seed_user_one()
        assert _get(client, "/login").status_code == 200  # no bypass: the sign-in page
