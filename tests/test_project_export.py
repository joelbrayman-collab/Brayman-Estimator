"""Sync.com project archive export queue (Joel, 16 Nov 2026)."""
import hashlib

import pytest

from app import db
from app.models import Project
from app.models.estimating_assistant import ProjectExport
from app.services import project_export as PX
from tests.test_internal_approval_calisign import env  # noqa: F401


def _project(env_):
    from tests.test_guided_tasks import _project as mk

    return mk(env_[1]["owner"], "Export test job")


def test_name_queue_idempotence_never_overwrite_and_mac_roundtrip(env, monkeypatch):
    app, c, _u = env
    project = _project(env)
    data = b"%PDF-1.4 synthetic"
    row = PX.enqueue(project, data=data, extension=".pdf", folder_code="05", document_type="Customer-Quotation",
                     revision="R1", source_kind="TEST", on=__import__("datetime").date(2026, 11, 16))
    assert row.target_name.startswith(f"{project.project_number}_") and row.target_name.endswith(
        "_Customer-Quotation_R1_2026-11-16.pdf")
    assert PX.enqueue(project, data=data, extension=".pdf", folder_code="05", document_type="Customer-Quotation",
                      revision="R1", source_kind="TEST", on=__import__("datetime").date(2026, 11, 16)).id == row.id
    with pytest.raises(PX.ExportError):  # same name, other bytes: never overwritten
        PX.enqueue(project, data=b"other", extension=".pdf", folder_code="05", document_type="Customer-Quotation",
                   revision="R1", source_kind="TEST", on=__import__("datetime").date(2026, 11, 16))
    monkeypatch.setenv("PROJECT_EXPORT_TOKEN", "t0ken")
    http = c["public"].http
    assert http.get("/sync-export/pending").status_code == 401
    h = {"Authorization": "Bearer t0ken"}
    listing = http.get("/sync-export/pending", headers=h).get_json()
    assert [i["id"] for i in listing] == [row.id] and listing[0]["folder"] == "05 - Customer Quotations"
    blob = http.get(f"/sync-export/{row.id}/file", headers=h).data
    assert hashlib.sha256(blob).hexdigest() == row.sha256
    assert http.post(f"/sync-export/{row.id}/done", headers=h, json={"sha256": "bad"}).status_code == 409
    assert db.session.get(ProjectExport, row.id).status == "FAILED"
    assert http.post(f"/sync-export/{row.id}/done", headers=h, json={"sha256": row.sha256}).status_code == 200
    assert db.session.get(ProjectExport, row.id).status == "EXPORTED" and PX.pending(row.organization_id) == []


def test_api_is_404_until_a_token_is_configured(env, monkeypatch):
    monkeypatch.delenv("PROJECT_EXPORT_TOKEN", raising=False)
    assert env[1]["public"].http.get("/sync-export/pending").status_code == 404
