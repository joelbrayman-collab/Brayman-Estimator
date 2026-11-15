"""A protected plan PDF at project creation (Joel, 15 Nov 2026; Production error BC-2026-0004).

Joel's real plan was AES-protected. Production could not open it ("cryptography>=3.1 is required for AES algorithm")
and the screen showed the project created and "Error creating project" together. Now: the AES library is a
requirement, a plan that needs a password says so plainly, and no plan problem ever reads as a failed project.
Synthetic data only.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.errors import DependencyError

from app import db
from app.models import Project
from app.plan_intelligence.models import PlanDocument
from tests.test_plan_upload import _make_searchable_pdf_bytes
from tests.test_project_plan_access import _new_project, env  # noqa: F401 - env is a fixture

REPO = Path(__file__).resolve().parents[1]


def _protected(user_password="", algorithm="AES-256"):
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(_make_searchable_pdf_bytes("Synthetic framing plan"))))
    writer.encrypt(user_password=user_password, owner_password="designer-owner-secret", algorithm=algorithm)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _create(http, client_row, data):
    return _new_project(http, client_row, plan_start="upload", plan_file=(io.BytesIO(data), "protected-plan.pdf"))


def _flashes(http):
    with http.session_transaction() as session:
        return [message for _category, message in session.get("_flashes", [])]


def test_aes_protected_plan_opens_and_uploads_with_the_project(env):
    http, client_row = env
    for algorithm in ("AES-128", "AES-256"):
        response = _new_project(http, client_row, name=f"Synthetic {algorithm} Job", plan_start="upload",
                                plan_file=(io.BytesIO(_protected(algorithm=algorithm)), "protected-plan.pdf"))
        project = Project.query.filter_by(name=f"Synthetic {algorithm} Job").one()
        assert response.headers["Location"].endswith(f"/projects/{project.id}/plans/{PlanDocument.query.filter_by(project_id=project.id).one().id}")
        assert "Error creating project" not in " ".join(_flashes(http))


def test_a_plan_that_needs_a_password_says_so_and_keeps_the_project(env):
    http, client_row = env
    response = _create(http, client_row, _protected(user_password="needs-a-password"))
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    assert response.headers["Location"].endswith(f"/projects/{project.id}/plans/upload")
    text = " ".join(_flashes(http))
    assert "project was saved" in text and "password" in text
    assert "Error creating project" not in text
    assert PlanDocument.query.filter_by(project_id=project.id).count() == 0


def test_a_missing_aes_library_never_reads_as_a_failed_project(env, monkeypatch):
    http, client_row = env

    class _NoAes:
        def __init__(self, *_args, **_kwargs):
            raise DependencyError("cryptography>=3.1 is required for AES algorithm")

    monkeypatch.setattr("app.plan_intelligence.services.PdfReader", _NoAes)
    response = _create(http, client_row, _protected())
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    assert response.headers["Location"].endswith(f"/projects/{project.id}/plans/upload")
    text = " ".join(_flashes(http))
    assert "project was saved" in text and "Error creating project" not in text and "cryptography" not in text


def test_any_unexpected_plan_failure_keeps_the_project_and_says_so(env, monkeypatch):
    http, client_row = env

    def _boom(*_args, **_kwargs):
        raise RuntimeError("storage unavailable (synthetic)")

    monkeypatch.setattr("app.plan_intelligence.services.upload_plan_pdf", _boom)
    response = _create(http, client_row, _make_searchable_pdf_bytes("Synthetic plan"))
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    assert response.headers["Location"].endswith(f"/projects/{project.id}/plans/upload")
    text = " ".join(_flashes(http))
    assert "project was saved" in text and "Error creating project" not in text
    assert db.session.get(Project, project.id) is not None


def test_cryptography_is_a_requirement_and_in_the_lock():
    for name in ("requirements.txt", "requirements-lock.txt"):
        lines = [line.split("#")[0].strip().lower() for line in (REPO / name).read_text().splitlines()]
        assert any(line.startswith("cryptography==") for line in lines), name
    lock = (REPO / "requirements-lock.txt").read_text().lower()
    assert "cffi==" in lock and "pycparser==" in lock
