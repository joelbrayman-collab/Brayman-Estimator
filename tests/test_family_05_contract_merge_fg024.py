"""FG-024 TECH-C Family 05 merge + generated-contract artifact custody."""

from __future__ import annotations

import hashlib
import os
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from docx import Document

from app import create_app, db
from app.models.project_contract import GeneratedProjectContract, ProjectContractSnapshot
from app.services.contract_artifact_storage import read_retained_docx
from app.services.contract_generation import (
    BLOCK_MISSING_COMMERCIAL_FACTS,
    BLOCK_MISSING_REQUIRED_LEGAL_OBJECT,
    BLOCK_PRESENTATION_MASTER_SHA_MISMATCH,
    retrieve_generated_contract_docx,
)
from app.services.family_05_contract_merge import (
    SAFETY_LABELS,
    TOKEN_CLIENT,
    TOKEN_DATE,
    TOKEN_PROJECT,
    TOKEN_SITE,
    family_05_merge_source,
    merge_family_05_from_frozen,
)
from app.services.family_05_master import (
    DEFAULT_FAMILY_05_MASTER_PATH,
    FAMILY_05_MASTER_SHA256,
    FAMILY_05_MEDIA_TYPE,
    governed_presentation_master,
    load_family_05_master_copy,
    sha256_bytes,
)
from tests.test_contract_generation_fg024 import (
    SYNTHETIC_CANDIDATE_BODY,
    SYNTHETIC_LEGAL_BODY,
    SYNTHETIC_WARRANTY_BODY,
    _generate,
    _object,
    _ottawa_project,
    _package,
    _ready_ontario,
)
from tests.test_contract_generation_policy_fg024 import _estimate, _proposal


def _docx_text(data: bytes) -> str:
    document = Document(BytesIO(data))
    parts = []

    def walk(container):
        parts.extend(p.text or "" for p in getattr(container, "paragraphs", []) or [])
        for table in getattr(container, "tables", []) or []:
            for row in table.rows:
                for cell in row.cells:
                    walk(cell)

    walk(document)
    for section in document.sections:
        walk(section.header)
        walk(section.footer)
    return "\n".join(parts)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg024-tech-c",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        from app.services.organizations import ensure_default_organization
        from app.services.jurisdiction import ensure_jurisdiction_seed

        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


def test_family_05_master_sha_matches_governed_authority(app):
    data = load_family_05_master_copy(expected_sha256=FAMILY_05_MASTER_SHA256)
    assert sha256_bytes(data) == FAMILY_05_MASTER_SHA256
    assert DEFAULT_FAMILY_05_MASTER_PATH.is_file()
    assert hashlib.sha256(DEFAULT_FAMILY_05_MASTER_PATH.read_bytes()).hexdigest() == (
        FAMILY_05_MASTER_SHA256
    )


def test_renderer_copies_master_and_never_mutates_master(app):
    before = DEFAULT_FAMILY_05_MASTER_PATH.read_bytes()
    before_sha = hashlib.sha256(before).hexdigest()
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-MASTER")
    result = _generate(project, version, proposal)
    assert result.generated is True
    after = DEFAULT_FAMILY_05_MASTER_PATH.read_bytes()
    assert hashlib.sha256(after).hexdigest() == before_sha
    assert after == before
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    retained = retrieve_generated_contract_docx(snapshot)
    assert retained != before
    assert sha256_bytes(retained) == snapshot.artifact_sha256


def test_master_sha_mismatch_blocks(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-SHA")
    bad = dict(governed_presentation_master())
    bad["sha256"] = "0" * 64
    result = _generate(project, version, proposal, master=bad)
    assert result.generated is False
    assert result.block_code == BLOCK_PRESENTATION_MASTER_SHA_MISMATCH
    assert GeneratedProjectContract.query.count() == 0


def test_html_reportlab_not_substituted_for_master():
    source = family_05_merge_source()
    assert "reportlab" not in source.lower()
    assert "<html" not in source.lower()
    assert "merge_family_05_from_frozen" in source
    assert "load_family_05_master_copy" in source


def test_commercial_tokens_mapped_from_frozen_snapshot(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-TOKENS")
    result = _generate(project, version, proposal)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    commercial = snapshot.commercial_variables_json
    text = _docx_text(retrieve_generated_contract_docx(snapshot))
    assert commercial["client_name"] in text
    assert commercial["project_name"] in text
    assert commercial["site"] in text
    assert commercial["contract_date"] in text
    assert TOKEN_CLIENT not in text.replace(commercial["client_name"], "")
    assert TOKEN_PROJECT not in text.replace(commercial["project_name"], "")
    assert TOKEN_SITE not in text.replace(commercial["site"], "")
    assert TOKEN_DATE not in text.replace(commercial["contract_date"], "")


def test_missing_required_frozen_commercial_fact_blocks(app):
    project = _ottawa_project(address="", estimate_number="EST-FG024C-NOSITE")
    package = _package(
        code="TEST-ON-NOSITE",
        jurisdiction_code="CA-ON",
        library_state="ACTIVE",
        counsel_approved_by="Counsel Test",
        effective_from=date(2026, 1, 1),
    )
    _object(package)
    _object(package, kind="warranty", body=SYNTHETIC_WARRANTY_BODY)
    estimate, version = _estimate(project, number="EST-FG024C-NOSITE", status="Issued")
    proposal = _proposal(estimate, version, number="PROP-FG024C-NOSITE")
    result = _generate(project, version, proposal)
    assert result.generated is False
    assert result.block_code == BLOCK_MISSING_COMMERCIAL_FACTS


def test_later_live_commercial_mutation_does_not_change_retained_docx(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-IMMUT")
    result = _generate(project, version, proposal)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    original = retrieve_generated_contract_docx(snapshot)
    old_sha = snapshot.artifact_sha256
    project.name = "MUTATED LIVE PROJECT NAME"
    project.address = "MUTATED LIVE SITE"
    project.client.name = "MUTATED LIVE CLIENT"
    version.total = Decimal("9999.00")
    db.session.commit()
    frozen = db.session.get(ProjectContractSnapshot, snapshot.id)
    retained = retrieve_generated_contract_docx(frozen)
    assert retained == original
    assert hashlib.sha256(retained).hexdigest() == old_sha
    assert frozen.commercial_variables_json["project_name"] != "MUTATED LIVE PROJECT NAME"


def test_frozen_legal_bodies_inserted_and_candidate_excluded(app):
    project, package, provision, _, version, proposal, warranty = _ready_ontario(
        number="EST-FG024C-LEGAL"
    )
    result = _generate(project, version, proposal)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    text = _docx_text(retrieve_generated_contract_docx(snapshot))
    assert SYNTHETIC_LEGAL_BODY in text
    assert SYNTHETIC_WARRANTY_BODY in text
    assert SYNTHETIC_CANDIDATE_BODY not in text
    assert provision.body == SYNTHETIC_LEGAL_BODY
    assert warranty.body == SYNTHETIC_WARRANTY_BODY
    package.content_objects
    provision.body = "MUTATED LIVE LEGAL BODY"
    warranty.body = "MUTATED LIVE WARRANTY BODY"
    db.session.commit()
    frozen = db.session.get(ProjectContractSnapshot, snapshot.id)
    retained_text = _docx_text(retrieve_generated_contract_docx(frozen))
    assert SYNTHETIC_LEGAL_BODY in retained_text
    assert "MUTATED LIVE LEGAL BODY" not in retained_text
    assert "MUTATED LIVE WARRANTY BODY" not in retained_text


def test_missing_legal_objects_block_merge(app):
    commercial = {
        "client_name": "Client",
        "project_name": "Project",
        "site": "Site",
        "contract_date": "2026-09-14",
    }
    missing_warranty = merge_family_05_from_frozen(
        presentation_master=governed_presentation_master(),
        commercial=commercial,
        legal_objects=[{"kind": "contract_provision", "body": SYNTHETIC_LEGAL_BODY}],
    )
    assert missing_warranty.merged is False
    assert missing_warranty.block_code == BLOCK_MISSING_REQUIRED_LEGAL_OBJECT
    missing_provision = merge_family_05_from_frozen(
        presentation_master=governed_presentation_master(),
        commercial=commercial,
        legal_objects=[{"kind": "warranty", "body": SYNTHETIC_WARRANTY_BODY}],
    )
    assert missing_provision.merged is False
    assert missing_provision.block_code == BLOCK_MISSING_REQUIRED_LEGAL_OBJECT


def test_synthetic_safety_labels_remain_present(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-SAFE")
    result = _generate(project, version, proposal)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    text = _docx_text(retrieve_generated_contract_docx(snapshot))
    for label in SAFETY_LABELS:
        assert label in text
    assert "NOT ONTARIO LEGAL AUTHORITY" in text


def test_artifact_custody_and_retrieval(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-STORE")
    result = _generate(project, version, proposal)
    snapshot = db.session.get(ProjectContractSnapshot, result.snapshot_id)
    contract = db.session.get(GeneratedProjectContract, result.contract_id)
    assert snapshot.artifact_storage_key
    assert snapshot.artifact_media_type == FAMILY_05_MEDIA_TYPE
    assert contract.artifact_storage_key == snapshot.artifact_storage_key
    assert ".." not in snapshot.artifact_storage_key
    assert not snapshot.artifact_storage_key.startswith("/")
    assert snapshot.artifact_storage_key.endswith(".docx")
    retained = retrieve_generated_contract_docx(snapshot)
    assert hashlib.sha256(retained).hexdigest() == snapshot.artifact_sha256
    reread = read_retained_docx(snapshot.artifact_storage_key)
    assert reread == retained
    first_key = snapshot.artifact_storage_key
    again = retrieve_generated_contract_docx(snapshot)
    assert again == retained
    assert snapshot.artifact_storage_key == first_key
    assert snapshot.presentation_master_sha256 == FAMILY_05_MASTER_SHA256
    assert snapshot.presentation_family_code == "05"


def test_historical_generated_contracts_remain_valid_without_storage_key(app):
    project, _, _, _, version, proposal, _ = _ready_ontario(number="EST-FG024C-HIST")
    now = date.today()
    from datetime import datetime

    now_dt = datetime.utcnow()
    contract = GeneratedProjectContract(
        organization_id=project.organization_id,
        client_id=project.client_id,
        project_id=project.id,
        estimate_id=version.estimate_id,
        estimate_version_id=version.id,
        proposal_id=None,
        contract_number="CTR-2026-0199",
        status="GENERATED",
        artifact_sha256="b" * 64,
        artifact_storage_key=None,
        generated_at=now_dt,
        generated_by_identifier="historical-slice-c",
        generation_process="fg024_slice_c",
        created_at=now_dt,
    )
    db.session.add(contract)
    db.session.commit()
    assert contract.proposal_id is None
    assert contract.artifact_storage_key is None
    snapshot = ProjectContractSnapshot(
        generated_contract_id=contract.id,
        organization_id=project.organization_id,
        client_id=project.client_id,
        client_name="Historical",
        project_id=project.id,
        project_name=project.name,
        jurisdiction_definition_id=1,
        jurisdiction_code="CA-ON",
        package_id=1,
        package_code="HIST",
        package_library_state="ACTIVE",
        package_support_status="SUPPORTED",
        legal_content_sha256="c" * 64,
        presentation_family_code="05",
        presentation_master_filename="shell.docx",
        presentation_master_version="V1-UAT-SYNTHETIC",
        presentation_master_sha256="d" * 64,
        presentation_legal_status="COMMERCIAL_DRAFT",
        estimate_version_id=version.id,
        estimate_number="EST-HIST",
        estimate_version_number=1,
        estimate_version_status="Issued",
        commercial_variables_json={"client_name": "Historical"},
        commercial_sha256="e" * 64,
        artifact_text="HISTORICAL TEXT ARTIFACT",
        artifact_sha256="b" * 64,
        artifact_storage_key=None,
        generated_at=now_dt,
        generated_by_identifier="historical-slice-c",
        generation_process="fg024_slice_c",
        created_at=now_dt,
    )
    db.session.add(snapshot)
    db.session.commit()
    assert retrieve_generated_contract_docx(snapshot) is None
    assert snapshot.artifact_text == "HISTORICAL TEXT ARTIFACT"


def test_alembic_fg024_tech_c_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "fg024_tech_c_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == ["a0b1c2d3e4f5"]

        command.upgrade(alembic_cfg, "f5a6b7c8d9e0")
        engine = db.engine
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_generated_contracts)")
                )
            }
            assert "artifact_storage_key" not in columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f5a6b7c8d9e0"]

        command.upgrade(alembic_cfg, "a6b7c8d9e0f1")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_generated_contracts)")
                )
            }
            snap_columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_contract_snapshots)")
                )
            }
            assert "artifact_storage_key" in columns
            assert "artifact_media_type" in columns
            assert "artifact_storage_key" in snap_columns
            assert "artifact_media_type" in snap_columns
            production_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM legal_content_jurisdiction_packages "
                    "WHERE authority_class = 'PRODUCTION'"
                )
            ).scalar()
            assert production_count == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["a6b7c8d9e0f1"]

        command.downgrade(alembic_cfg, "f5a6b7c8d9e0")
        with engine.begin() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    sa.text("PRAGMA table_info(project_generated_contracts)")
                )
            }
            assert "artifact_storage_key" not in columns
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["f5a6b7c8d9e0"]
