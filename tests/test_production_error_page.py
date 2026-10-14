"""SEC-06: an unexpected error shows a plain page with a reference, rolls back, and is logged."""

import logging

from app import create_app, db


def _app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "x",
                      "PROPAGATE_EXCEPTIONS": False})

    @app.route("/_boom")
    def boom():
        raise RuntimeError("synthetic failure")

    @app.route("/api/_boom")
    def api_boom():
        raise RuntimeError("synthetic api failure")

    return app


def test_an_unhandled_error_shows_a_plain_page_with_a_reference(caplog):
    app = _app()
    app.config["LOGIN_DISABLED"] = True
    with app.app_context():
        db.create_all()
    client = app.test_client()
    from tests.auth_fixtures import ensure_office_user, login_office_user

    with app.app_context():
        ensure_office_user()
        db.session.commit()
    login_office_user(client)
    with caplog.at_level(logging.ERROR):
        response = client.get("/_boom")
    assert response.status_code == 500
    body = response.get_data(as_text=True)
    assert "Something went wrong" in body and "synthetic failure" not in body and "Traceback" not in body
    reference = body.split("<strong>")[1].split("</strong>")[0]
    assert len(reference) == 8
    assert any(reference in rec.getMessage() for rec in caplog.records)
