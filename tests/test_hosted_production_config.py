"""Hosted office production configuration. Disposable databases only."""

from pathlib import Path

import pytest
from flask import Flask

from app import (
    DEVELOPMENT_SECRET_KEY,
    LOCAL_DATABASE_URI,
    HostedDatabaseConfigError,
    SecretKeyConfigError,
    create_app,
)
from app.services.family_05_master import (
    BLOCK_MISSING_PRESENTATION_MASTER,
    DEFAULT_FAMILY_05_MASTER_PATH,
    Family05MasterError,
    family_05_master_path,
    load_family_05_master_copy,
)
from app.services.transactional_email import public_base_url

HOSTED_SECRET = "hosted-office-test-secret"
FALLBACK_DB_NAME = "brayman_estimator.db"


@pytest.fixture
def office_env(monkeypatch, tmp_path):
    """Keep these tests off the live Mac database and off hosted env leakage."""
    instance = tmp_path / "instance"
    instance.mkdir()
    real_flask = Flask

    def flask_with_temp_instance(import_name, **kwargs):
        kwargs.setdefault("instance_path", str(instance))
        return real_flask(import_name, **kwargs)

    monkeypatch.setattr("app.Flask", flask_with_temp_instance)
    monkeypatch.delenv("CALIBRAYTAI_HOSTED", raising=False)
    monkeypatch.delenv("CALIBRAYTAI_DATABASE_URI", raising=False)
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    return tmp_path


def _sqlite_uri(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def _hosted_config(database_uri, **extra):
    config = {
        "CALIBRAYTAI_HOSTED": "1",
        "CALIBRAYTAI_DATABASE_URI": database_uri,
        "SECRET_KEY": HOSTED_SECRET,
    }
    config.update(extra)
    return config


def test_local_default_database_uri(office_env):
    application = create_app({"TESTING": True})
    assert application.config["SQLALCHEMY_DATABASE_URI"] == LOCAL_DATABASE_URI
    assert LOCAL_DATABASE_URI == "sqlite:///brayman_estimator.db"


def test_local_mode_ignores_hosted_database_uri(office_env, monkeypatch):
    monkeypatch.setenv(
        "CALIBRAYTAI_DATABASE_URI",
        _sqlite_uri(office_env / "must-not-be-used.db"),
    )
    application = create_app({"TESTING": True})
    assert application.config["SQLALCHEMY_DATABASE_URI"] == LOCAL_DATABASE_URI
    assert not (office_env / "must-not-be-used.db").exists()


def test_local_session_cookie_secure_stays_off(office_env):
    application = create_app({"TESTING": True})
    assert application.config["SESSION_COOKIE_SECURE"] is False


def test_hosted_uses_explicit_database_uri(office_env):
    database = office_env / "hosted.db"
    application = create_app(_hosted_config(_sqlite_uri(database)))
    assert application.config["SQLALCHEMY_DATABASE_URI"] == _sqlite_uri(database)
    assert not (office_env / "instance" / FALLBACK_DB_NAME).exists()


def test_hosted_missing_database_uri_fails_closed(office_env):
    with pytest.raises(HostedDatabaseConfigError, match="CALIBRAYTAI_DATABASE_URI"):
        create_app(
            {
                "CALIBRAYTAI_HOSTED": "1",
                "SECRET_KEY": HOSTED_SECRET,
            }
        )
    assert not (office_env / "instance" / FALLBACK_DB_NAME).exists()


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_hosted_blank_database_uri_fails_closed(office_env, blank):
    with pytest.raises(HostedDatabaseConfigError, match="CALIBRAYTAI_DATABASE_URI"):
        create_app(_hosted_config(blank))
    assert not (office_env / "instance" / FALLBACK_DB_NAME).exists()


def test_hosted_missing_database_uri_from_environment_fails_closed(office_env, monkeypatch):
    monkeypatch.setenv("CALIBRAYTAI_HOSTED", "1")
    with pytest.raises(HostedDatabaseConfigError, match="CALIBRAYTAI_DATABASE_URI"):
        create_app({"SECRET_KEY": HOSTED_SECRET})
    assert not (office_env / "instance" / FALLBACK_DB_NAME).exists()


def test_hosted_missing_secret_fails_closed(office_env):
    with pytest.raises(SecretKeyConfigError, match="SECRET_KEY"):
        create_app(
            {
                "CALIBRAYTAI_HOSTED": "1",
                "CALIBRAYTAI_DATABASE_URI": _sqlite_uri(office_env / "hosted.db"),
            }
        )


def test_hosted_development_secret_fails_closed(office_env):
    with pytest.raises(SecretKeyConfigError, match="development secret"):
        create_app(
            _hosted_config(
                _sqlite_uri(office_env / "hosted.db"),
                SECRET_KEY=DEVELOPMENT_SECRET_KEY,
            )
        )


def test_hosted_debug_development_secret_still_fails_closed(office_env, monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "1")
    with pytest.raises(SecretKeyConfigError, match="development secret"):
        create_app(
            _hosted_config(
                _sqlite_uri(office_env / "hosted.db"),
                SECRET_KEY=DEVELOPMENT_SECRET_KEY,
                DEBUG=True,
            )
        )


def test_hosted_valid_secret_starts(office_env):
    application = create_app(_hosted_config(_sqlite_uri(office_env / "hosted.db")))
    assert application.config["SECRET_KEY"] == HOSTED_SECRET


def test_hosted_secure_cookies(office_env):
    application = create_app(_hosted_config(_sqlite_uri(office_env / "hosted.db")))
    assert application.config["SESSION_COOKIE_SECURE"] is True
    assert application.config["SESSION_COOKIE_HTTPONLY"] is True
    assert application.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_hosted_starts_without_public_base_url(office_env):
    application = create_app(
        _hosted_config(
            _sqlite_uri(office_env / "hosted.db"),
            TRANSACTIONAL_EMAIL_PROVIDER="local",
            PUBLIC_BASE_URL="",
        )
    )
    with application.app_context():
        assert public_base_url() == "http://localhost"


def test_hosted_public_base_url_is_returned_when_set(office_env):
    application = create_app(
        _hosted_config(
            _sqlite_uri(office_env / "hosted.db"),
            PUBLIC_BASE_URL="https://office.example/",
        )
    )
    with application.app_context():
        assert public_base_url() == "https://office.example"


def test_hosted_family_05_does_not_use_mac_default(office_env):
    application = create_app(_hosted_config(_sqlite_uri(office_env / "hosted.db")))
    with application.app_context():
        with pytest.raises(Family05MasterError) as raised:
            family_05_master_path()
        assert raised.value.block_code == BLOCK_MISSING_PRESENTATION_MASTER
        with pytest.raises(Family05MasterError) as loaded:
            load_family_05_master_copy()
        assert loaded.value.block_code == BLOCK_MISSING_PRESENTATION_MASTER


def test_local_family_05_keeps_mac_default_path(office_env):
    application = create_app({"TESTING": True})
    with application.app_context():
        assert family_05_master_path() == DEFAULT_FAMILY_05_MASTER_PATH
