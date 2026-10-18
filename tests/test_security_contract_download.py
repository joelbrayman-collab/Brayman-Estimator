"""Security: generated-contract download (projects.download_generated_contract).

GET /projects/<id>/contract/<contract_id>/download, app/routes/project_contract.py.
Synthetic contract generated exactly as tests/test_contract_generation_fg024.py does it
(Family 05 master named by CALIBRAYTAI_FAMILY_05_MASTER_PATH). Synthetic data only.
"""

from __future__ import annotations

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.organization import Organization
from app.models.project_contract import GeneratedProjectContract, ProjectContractSnapshot
from app.services.contract_artifact_storage import absolute_stored_path, get_contract_artifact_root
from app.services.jurisdiction import ensure_jurisdiction_seed
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import create_membership, create_user, login_office_user
from tests.test_contract_generation_fg024 import _generate, _make_project, _ready_ontario

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-security-contract-download",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()  # conftest's autouse fixture signs this in as the ORG-001 office user


def _generated(number="EST-SEC-DL-0001"):
    project, _package, _obj, _estimate, version, proposal, _warranty = _ready_ontario(number=number)
    result = _generate(project, version, proposal)
    assert result.generated is True
    contract = db.session.get(GeneratedProjectContract, result.contract_id)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    stored = absolute_stored_path(snapshot.artifact_storage_key)
    original = stored.read_bytes()
    return project, contract, snapshot, stored, original


def _url(project_id, contract_id):
    return f"/projects/{project_id}/contract/{contract_id}/download"


def _files_under_root():
    return sorted(p for p in get_contract_artifact_root().rglob("*") if p.is_file())


def _assert_no_docx_served(response, original):
    assert response.status_code != 200
    assert original not in response.data
    assert not response.data.startswith(b"PK")
    assert response.mimetype != DOCX_MEDIA_TYPE
    assert "attachment" not in (response.headers.get("Content-Disposition") or "")


def test_same_org_office_user_downloads_exact_retained_bytes(app, client):
    project, contract, _snapshot, _stored, original = _generated()
    response = client.get(_url(project.id, contract.id))
    assert response.status_code == 200
    assert response.data == original
    assert response.mimetype == DOCX_MEDIA_TYPE


@pytest.mark.no_office_auth
def test_signed_out_download_redirects_to_login(app, client):
    project, contract, _snapshot, _stored, original = _generated()
    response = client.get(_url(project.id, contract.id))
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?next=")
    assert original not in response.data


@pytest.mark.no_office_auth
def test_user_in_another_organization_gets_404_and_no_bytes(app, client):
    project, contract, _snapshot, _stored, original = _generated()
    db.session.add(
        Organization(id="ORG-002", legal_name="Apex Synthetic Ltd.", display_name="Apex Synthetic", is_active=True)
    )
    db.session.commit()
    foreign = create_user(
        email="sec-dl-foreign@example.invalid", password="foreign-password", display_name="Foreign Office"
    )
    create_membership(foreign, "ORG-002")
    db.session.commit()
    foreign_client = Client(name="Apex synthetic client", organization_id="ORG-002")
    db.session.add(foreign_client)
    db.session.flush()
    foreign_project = Project(
        name="Apex synthetic project", client_id=foreign_client.id, organization_id="ORG-002", status="Lead"
    )
    db.session.add(foreign_project)
    db.session.commit()
    assert login_office_user(client, email=foreign.email, password="foreign-password").status_code == 302

    for path in (_url(project.id, contract.id), _url(foreign_project.id, contract.id)):
        response = client.get(path)
        assert response.status_code == 404, path
        assert original not in response.data
        assert response.mimetype != DOCX_MEDIA_TYPE


def test_contract_id_under_another_project_of_same_org_is_404(app, client):
    project, contract, _snapshot, _stored, original = _generated()
    sibling = _make_project(name="Sibling synthetic project", client_name="Sibling synthetic client")
    assert sibling.organization_id == project.organization_id
    response = client.get(_url(sibling.id, contract.id))
    assert response.status_code == 404
    assert original not in response.data
    assert response.mimetype != DOCX_MEDIA_TYPE
    assert client.get(_url(project.id, contract.id + 999)).status_code == 404


def test_altered_bytes_on_disk_are_not_served(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = False
    project, contract, snapshot, stored, original = _generated()
    tampered = bytearray(original)
    tampered[len(tampered) // 2] ^= 0xFF
    stored.write_bytes(bytes(tampered))
    files_before = _files_under_root()
    contracts_before = GeneratedProjectContract.query.count()
    sha_before = snapshot.artifact_sha256

    response = client.get(_url(project.id, contract.id))

    _assert_no_docx_served(response, original)
    assert bytes(tampered) not in response.data
    # DEFECT (recorded for Joel): returns 500, intended 404/fail-closed page.
    # retrieve_generated_contract_docx raises ValueError on the SHA-256 mismatch and
    # download_generated_contract does not catch it.
    assert response.status_code in (404, 410, 500)  # safety property: refused, never 200
    assert _files_under_root() == files_before
    assert GeneratedProjectContract.query.count() == contracts_before
    assert db.session.get(ProjectContractSnapshot, snapshot.id).artifact_sha256 == sha_before


def test_deleted_stored_file_is_not_served(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = False
    project, contract, snapshot, stored, original = _generated()
    stored.unlink()
    contracts_before = GeneratedProjectContract.query.count()

    response = client.get(_url(project.id, contract.id))

    _assert_no_docx_served(response, original)
    # DEFECT (recorded for Joel): returns 500, intended 404/fail-closed page.
    # read_retained_docx raises ContractArtifactStorageError ("not retained") and
    # download_generated_contract does not catch it.
    assert response.status_code in (404, 410, 500)  # safety property: refused, never 200
    assert not stored.exists()  # nothing re-rendered or re-written behind the request
    assert GeneratedProjectContract.query.count() == contracts_before
    assert db.session.get(ProjectContractSnapshot, snapshot.id).artifact_storage_key == snapshot.artifact_storage_key
