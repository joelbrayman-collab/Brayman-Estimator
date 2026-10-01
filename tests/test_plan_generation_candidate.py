"""PGE-4: a rendered sheet stays a candidate until explicit use."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect, text

from app import create_app, db
from app.models import Client, Estimate, Organization, Project
from app.models.plan_generation_candidate import PlanGenerationCandidate
from app.models.project import ProjectLocation
from app.models.project_work_package import ProjectWorkPackage
from app.plan_intelligence.models import (
    PLAN_ORIGIN_GENERATED,
    PLAN_ORIGIN_UPLOADED,
    DrawingRevision,
    PlanDocument,
)
from app.project_controls.models import ChangeOrder
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.plan_generation.candidates import (
    CODE_CANDIDATE_NOT_FOUND,
    CODE_CANDIDATE_NOT_IN_PROJECT,
    CODE_CANDIDATE_NOT_RENDERED,
    CODE_CANDIDATE_NOT_USABLE,
    persist_generated_candidate,
    use_generated_candidate,
)
from app.services.project_work_package import project_plans
from app.services.start_project_walk import (
    EVIDENCE_DRAWING_DECISION_NOT_DERIVABLE,
    EVIDENCE_DRAWINGS_PRESENT,
    resolve_start_project_walk,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "plan_generation"


def _load(name: str) -> dict:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    payload.pop("fixture_role", None)
    return payload


def _app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "pge4.db"),
            "SECRET_KEY": "test-secret-plan-candidate",
            "WTF_CSRF_ENABLED": False,
            "PLAN_UPLOAD_ROOT": str(tmp_path / "plan_uploads"),
        }
    )


def _project(org_id, name):
    client = Client(name=f"{name} client", organization_id=org_id)
    db.session.add(client)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client.id,
        organization_id=org_id,
        status="Lead",
        address="12 Oak Street",
    )
    db.session.add(project)
    db.session.commit()
    return project


def _location(project):
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="12 Oak Street",
            municipality="Ottawa",
            province_state="Ontario",
            country="Canada",
        )
    )
    db.session.commit()


def test_candidate_is_not_current_until_explicit_use(tmp_path):
    application = _app(tmp_path)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        project = _project(DEFAULT_ORGANIZATION_ID, "Dimensioned")
        _location(project)
        before = (
            project.client_id,
            project.status,
            project.address,
            Estimate.query.count(),
            ProjectWorkPackage.query.count(),
            ChangeOrder.query.count(),
        )
        persisted = persist_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            _load("rectangle_platform.json"),
        )
        assert persisted.persisted is True
        assert persisted.candidate.drawing_type == "dimensioned_plan"
        assert persisted.candidate.created_at is not None
        assert persisted.candidate.request_fingerprint
        assert persisted.candidate.plan_document_id is None
        assert json.loads(persisted.candidate.manifest_json)["title"] == "Rectangle platform"
        assert project_plans(DEFAULT_ORGANIZATION_ID, project.id) == []
        walk = resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, project.id)
        assert EVIDENCE_DRAWINGS_PRESENT not in walk.evidence
        assert EVIDENCE_DRAWING_DECISION_NOT_DERIVABLE in walk.evidence

        used = use_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            persisted.candidate.id,
        )
        assert used.used is True
        assert used.created is True
        document = db.session.get(PlanDocument, used.plan_document_id)
        assert document.origin == PLAN_ORIGIN_GENERATED
        assert document.archived_at is None
        assert len(project_plans(DEFAULT_ORGANIZATION_ID, project.id)) == 1
        again = use_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            persisted.candidate.id,
        )
        assert again.created is False
        assert again.plan_document_id == used.plan_document_id
        assert PlanDocument.query.count() == 1
        after = (
            project.client_id,
            project.status,
            project.address,
            Estimate.query.count(),
            ProjectWorkPackage.query.count(),
            ChangeOrder.query.count(),
        )
        assert before == after
        db.session.remove()
        db.drop_all()


def test_second_use_keeps_the_first_plan_and_stair_candidate(tmp_path):
    application = _app(tmp_path)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        project = _project(DEFAULT_ORGANIZATION_ID, "Two drawings")
        first = persist_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            _load("rectangle_platform.json"),
        )
        use_generated_candidate(DEFAULT_ORGANIZATION_ID, project.id, first.candidate.id)
        first_document = db.session.get(PlanDocument, first.candidate.plan_document_id)
        first_sha = first_document.sha256_hex
        second = persist_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            _load("stair_detail_alternate.json"),
        )
        assert second.candidate.drawing_type == "stair_detail"
        assert first_document.archived_at is None
        used = use_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            second.candidate.id,
        )
        assert used.created is True
        documents = (
            PlanDocument.query.filter_by(project_id=project.id)
            .order_by(PlanDocument.id.asc())
            .all()
        )
        assert [item.origin for item in documents] == [
            PLAN_ORIGIN_GENERATED,
            PLAN_ORIGIN_GENERATED,
        ]
        assert documents[0].sha256_hex == first_sha
        assert documents[0].archived_at is None
        assert documents[1].archived_at is None
        revision = DrawingRevision.query.filter_by(is_active=True).one()
        assert documents[0] in revision.documents
        assert documents[1] in revision.documents
        db.session.remove()
        db.drop_all()


def test_invalid_request_is_not_stored_or_usable(tmp_path):
    application = _app(tmp_path)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        project = _project(DEFAULT_ORGANIZATION_ID, "Invalid")
        payload = _load("stair_detail_recorded.json")
        payload.pop("stair_geometry")
        persisted = persist_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            payload,
        )
        assert persisted.persisted is False
        assert persisted.code == CODE_CANDIDATE_NOT_RENDERED
        assert PlanGenerationCandidate.query.count() == 0
        assert PlanDocument.query.count() == 0
        missing = use_generated_candidate(DEFAULT_ORGANIZATION_ID, project.id, 99)
        assert missing.code == CODE_CANDIDATE_NOT_FOUND
        empty = PlanGenerationCandidate(
            organization_id=DEFAULT_ORGANIZATION_ID,
            project_id=project.id,
            drawing_type="dimensioned_plan",
            engine_version="pge-2",
            validation_engine_version="pge-1",
            request_fingerprint="a" * 64,
            manifest_json="{}",
            uncertainty_flags_json="[]",
            pdf_sha256="b" * 64,
            pdf_bytes=b"not-a-pdf",
            created_at=datetime.utcnow(),
        )
        db.session.add(empty)
        db.session.commit()
        rejected = use_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            project.id,
            empty.id,
        )
        assert rejected.code == CODE_CANDIDATE_NOT_USABLE
        assert PlanDocument.query.count() == 0
        db.session.remove()
        db.drop_all()


def test_other_organization_and_other_project_cannot_use_a_candidate(tmp_path):
    application = _app(tmp_path)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        other = Organization(
            id="ORG-PGE4",
            legal_name="Other Company",
            display_name="Other Company",
        )
        db.session.add(other)
        db.session.commit()
        owner = _project(DEFAULT_ORGANIZATION_ID, "Owner")
        sibling = _project(DEFAULT_ORGANIZATION_ID, "Sibling")
        outsider = _project("ORG-PGE4", "Outsider")
        owned = persist_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            owner.id,
            _load("bushel_dimensioned_plan.json"),
        )
        foreign = persist_generated_candidate(
            "ORG-PGE4",
            outsider.id,
            _load("rectangle_platform.json"),
        )
        hidden = use_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            owner.id,
            foreign.candidate.id,
        )
        assert hidden.code == CODE_CANDIDATE_NOT_FOUND
        assert foreign.candidate.plan_document_id is None
        wrong_project = use_generated_candidate(
            DEFAULT_ORGANIZATION_ID,
            sibling.id,
            owned.candidate.id,
        )
        assert wrong_project.code == CODE_CANDIDATE_NOT_IN_PROJECT
        assert owned.candidate.plan_document_id is None
        assert PlanDocument.query.count() == 0
        db.session.remove()
        db.drop_all()


def test_uploaded_plan_keeps_uploaded_origin(tmp_path):
    application = _app(tmp_path)
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        project = _project(DEFAULT_ORGANIZATION_ID, "Upload")
        document = PlanDocument(
            project_id=project.id,
            original_filename="site.pdf",
            stored_filename="site.pdf",
            content_type="application/pdf",
            byte_size=12,
            sha256_hex="c" * 64,
            has_text_layer=False,
        )
        db.session.add(document)
        db.session.commit()
        assert document.origin == PLAN_ORIGIN_UPLOADED
        db.session.remove()
        db.drop_all()


def test_existing_plan_rows_upgrade_as_uploaded(tmp_path):
    database = tmp_path / "upgrade.db"
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(database),
            "SECRET_KEY": "test-secret-plan-migration",
            "WTF_CSRF_ENABLED": False,
        }
    )
    from flask_migrate import downgrade, upgrade

    with application.app_context():
        upgrade(revision="k1f2a3b4c5d6")
        ensure_default_organization()
        project = _project(DEFAULT_ORGANIZATION_ID, "Legacy")
        db.session.execute(
            text(
                """
                INSERT INTO plan_documents (
                    project_id, original_filename, stored_filename, content_type,
                    byte_size, sha256_hex, has_text_layer, created_at, processing_status
                ) VALUES (
                    :project_id, 'legacy.pdf', 'legacy.pdf', 'application/pdf',
                    20, :sha, 0, :created_at, 'pending'
                )
                """
            ),
            {
                "project_id": project.id,
                "sha": "d" * 64,
                "created_at": datetime.utcnow().isoformat(sep=" "),
            },
        )
        db.session.commit()
        upgrade()
        names = inspect(db.engine).get_table_names()
        assert "plan_generation_candidates" in names
        row = db.session.execute(
            text(
                "SELECT origin, original_filename, sha256_hex FROM plan_documents"
            )
        ).one()
        assert row.origin == PLAN_ORIGIN_UPLOADED
        assert row.original_filename == "legacy.pdf"
        assert row.sha256_hex == "d" * 64
        downgrade(revision="k1f2a3b4c5d6")
        names = inspect(db.engine).get_table_names()
        assert "plan_generation_candidates" not in names
        columns = {
            column["name"] for column in inspect(db.engine).get_columns("plan_documents")
        }
        assert "origin" not in columns
        upgrade()
        assert "plan_generation_candidates" in inspect(db.engine).get_table_names()
        db.session.remove()
