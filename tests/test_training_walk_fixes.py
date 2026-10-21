"""Fixes found while capturing the Training Centre's supplier lessons (21 Oct 2026). Synthetic data only."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app, db
from app.training import environment

pytestmark = pytest.mark.no_office_auth
ROOT = Path(__file__).resolve().parents[1]


def test_customer_accept_sentence_wraps_as_words_on_a_phone():
    page = (ROOT / "app/templates/supplier/pro_desk/customer.html").read_text()
    assert '<span class="pd-inline-text">I accept material quotation' in page
    css = (ROOT / "app/static/css/supplier-hub.css").read_text()
    assert "label.pd-inline > .pd-inline-text { flex: 1 1 auto; min-width: 0;" in css


def test_after_a_password_reset_a_supplier_is_sent_back_to_the_supplier_sign_in(monkeypatch):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "WTF_CSRF_ENABLED": False, "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        db.create_all()
        environment.build(application, {k: f"Synthetic-{k}-reset-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")})
        from app.models.user import User
        import app.routes.auth as auth_routes

        darcy = User.query.filter_by(email="darcy@training.calibraytai.invalid").one()
        ben = User.query.filter_by(email="ben@training.calibraytai.invalid").one()
        client = application.test_client()
        for user, link in ((darcy, "/supplier/login"), (ben, "/login")):
            monkeypatch.setattr(auth_routes, "complete_password_reset", lambda *a, _u=user, **k: _u)
            done = client.post("/reset-password/synthetic-credential", data={"password": "x", "confirm_password": "x"})
            assert done.status_code == 302
            page = client.get(done.headers["Location"]).get_data(as_text=True)
            assert f'href="{link}"' in page, link
        db.drop_all()


def test_the_training_job_has_its_town_and_its_construction_model():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        db.create_all()
        environment.build(application)
        environment.build(application)  # repeatable: nothing doubled
        from app.models import Project
        from app.models.project import ProjectLocation
        from app.models.project_construction_model import ProjectConstructionModelRevision

        job = Project.query.filter_by(name=environment.JOB).one()
        location = ProjectLocation.query.filter_by(project_id=job.id).one()
        assert location.municipality == "Merrickville"
        revisions = ProjectConstructionModelRevision.query.filter_by(project_id=job.id).all()
        assert len(revisions) == 1
        text = str(revisions[0].__dict__)
        assert "LINDA" not in text.upper() and "BUSHEL" not in text.upper()  # no real customer in training data
        db.drop_all()
