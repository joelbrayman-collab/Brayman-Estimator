"""FG-010 / M012 AI take-off quantity extraction foundation tests.

Provider-neutral mock only. No network. No estimate/labour/pricing writes.
"""

from __future__ import annotations

import inspect
import os
from decimal import Decimal
from io import BytesIO

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.estimate import EstimateLineItem, EstimateVersion
from app.models.labour_engine import (
    DirectLabourCostRateStandard,
    EstimateLabourSnapshot,
    LabourCalibrationCandidate,
    LabourTask,
    LabourTaskMapping,
    ProductionRateStandard,
)
from app.models.pricing_engine import EstimatePricingSnapshot, OrganizationPricingPolicy
from app.plan_intelligence.models import (
    DrawingRevision,
    PlanAuditEvent,
    PlanDocument,
    PlanMeasurement,
    PlanPage,
    TakeoffCandidate,
    TakeoffExtractionRun,
    TakeoffPackage,
    TakeoffPackageItem,
)
from app.plan_intelligence.packages import ensure_default_revision
from app.plan_intelligence.processing import process_document_deterministic
from app.plan_intelligence.services import PlanIntelligenceServiceError
from app.plan_intelligence.sheets import create_sheet, map_page_to_sheet
from app.plan_intelligence.takeoff import (
    approve_package,
    compute_run_reviewed_total,
    create_draft_package,
    get_candidate_or_404,
    get_package_or_404,
    get_run_or_404,
    mutate_package,
    review_candidate,
    start_extraction_run,
    validate_normalized_bbox,
)
from app.plan_intelligence.takeoff_extractors import (
    MockInteriorDoorExtractor,
    confidence_band_for,
    get_extractor,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)


def _make_searchable_pdf_bytes(text='A-101 Floor Plan Scale: 1/4" = 1\'-0"'):
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 50 750 Td ({safe}) Tj ET"
    content_bytes = content.encode("latin-1")
    objects = []

    def obj(n, body):
        objects.append((n, body))

    obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    obj(
        3,
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    )
    obj(
        4,
        f"<< /Length {len(content_bytes)} >>\nstream\n".encode()
        + content_bytes
        + b"\nendstream",
    )
    obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = {0: 0}
    for n, body in objects:
        offsets[n] = out.tell()
        out.write(f"{n} 0 obj\n".encode())
        out.write(body)
        out.write(b"\nendobj\n")
    xref_pos = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for n in range(1, len(objects) + 1):
        out.write(f"{offsets[n]:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    )
    out.write(f"startxref\n{xref_pos}\n%%EOF".encode())
    return out.getvalue()


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SECRET_KEY": "test-secret-takeoff",
            "WTF_CSRF_ENABLED": False,
            "PLAN_UPLOAD_ROOT": str(tmp_path / "plan_uploads"),
            "PLAN_UPLOAD_MAX_BYTES": 2 * 1024 * 1024,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _seed_eligible_plan(*, organization_id=DEFAULT_ORGANIZATION_ID, name="Takeoff Project"):
    from app.plan_intelligence.storage import project_upload_dir

    c = Client(name=f"{name} Client", organization_id=organization_id)
    db.session.add(c)
    db.session.flush()
    p = Project(name=name, client_id=c.id, organization_id=organization_id)
    db.session.add(p)
    db.session.commit()

    pdf_bytes = _make_searchable_pdf_bytes("A-101 Floor Plan interior doors")
    doc = PlanDocument(
        project_id=p.id,
        original_filename="architectural_set.pdf",
        stored_filename="architectural_set.pdf",
        byte_size=len(pdf_bytes),
        sha256_hex=f"test_sha_{organization_id}_{p.id}",
        content_type="application/pdf",
    )
    db.session.add(doc)
    dest = project_upload_dir(p.id) / "architectural_set.pdf"
    dest.write_bytes(pdf_bytes)
    db.session.flush()

    rev = ensure_default_revision(p)
    rev.documents.append(doc)
    db.session.flush()
    process_document_deterministic(doc, force=True)
    db.session.commit()

    sheet = create_sheet(
        revision=rev,
        number="A-101",
        title="Ground Floor Plan",
        discipline_code="ARCH",
        review_status="reviewed",
        drawing_status="reviewed",
    )
    map_page_to_sheet(sheet, plan_document_id=doc.id, page_index=0)
    db.session.commit()
    return {
        "organization_id": organization_id,
        "project_id": p.id,
        "revision_id": rev.id,
        "document_id": doc.id,
        "sheet_id": sheet.id,
        "package_id": rev.package_id,
    }


def _start_run(seed, created_by="office-reviewer"):
    return start_extraction_run(
        organization_id=seed["organization_id"],
        project_id=seed["project_id"],
        plan_document_id=seed["document_id"],
        drawing_revision_id=seed["revision_id"],
        created_by=created_by,
    )


def _review_fixture(run, actor="office-reviewer"):
    """3 accepted + 1 duplicate → approved total 3."""
    cands = list(run.candidates)
    assert len(cands) == 4
    for cand in cands[:3]:
        review_candidate(
            organization_id=run.organization_id,
            candidate_id=cand.id,
            action="accept",
            reviewed_by=actor,
        )
    review_candidate(
        organization_id=run.organization_id,
        candidate_id=cands[3].id,
        action="duplicate",
        reviewed_by=actor,
        review_reason="Same west corridor door detected twice.",
        canonical_candidate_id=cands[0].id,
    )
    db.session.refresh(run)
    return run


def test_run_creation_and_rerun_new_id(app):
    seed = _seed_eligible_plan()
    run1 = _start_run(seed)
    assert run1.status == "succeeded"
    assert run1.id is not None
    assert run1.element_type == "INTERIOR_DOOR_OPENING"
    assert run1.provider == "calibai-mock"
    run2 = _start_run(seed)
    assert run2.id != run1.id
    assert TakeoffExtractionRun.query.count() == 2
    db.session.refresh(run1)
    assert run1.status == "succeeded"
    assert run1.candidate_count == 4


def test_failed_run_does_not_mutate_earlier_run(app, monkeypatch):
    seed = _seed_eligible_plan()
    run1 = _start_run(seed)
    first_ids = [c.id for c in run1.candidates]
    first_status = run1.status

    def boom(self, **kwargs):
        raise RuntimeError("synthetic extractor failure")

    monkeypatch.setattr(MockInteriorDoorExtractor, "extract", boom)
    with pytest.raises(PlanIntelligenceServiceError, match="Extraction failed"):
        _start_run(seed)

    earlier = TakeoffExtractionRun.query.get(run1.id)
    assert earlier.status == first_status
    assert [c.id for c in earlier.candidates] == first_ids
    failed = (
        TakeoffExtractionRun.query.filter(TakeoffExtractionRun.id != run1.id)
        .order_by(TakeoffExtractionRun.id.desc())
        .first()
    )
    assert failed.status == "failed"
    assert failed.id != run1.id


def test_org_ownership_and_cross_org_run_lookup_fails(app, org_b):
    seed_a = _seed_eligible_plan(organization_id="ORG-001", name="Org A Project")
    seed_b = _seed_eligible_plan(organization_id="ORG-002", name="Org B Project")
    run_a = _start_run(seed_a)
    run_b = _start_run(seed_b)
    assert run_a.organization_id == "ORG-001"
    assert run_b.organization_id == "ORG-002"
    found = get_run_or_404("ORG-001", run_a.id)
    assert found.id == run_a.id
    with pytest.raises(PlanIntelligenceServiceError, match="not found"):
        get_run_or_404("ORG-001", run_b.id)
    with pytest.raises(PlanIntelligenceServiceError, match="not found"):
        get_candidate_or_404("ORG-001", run_b.candidates[0].id)
    with pytest.raises(PlanIntelligenceServiceError, match="Project not found"):
        start_extraction_run(
            organization_id="ORG-001",
            project_id=seed_b["project_id"],
            plan_document_id=seed_b["document_id"],
            drawing_revision_id=seed_b["revision_id"],
            created_by="office-reviewer",
        )


def test_candidate_provenance_bbox_and_confidence(app):
    seed = _seed_eligible_plan()
    run = _start_run(seed)
    assert run.candidate_count == 4
    for cand in run.candidates:
        assert cand.plan_document_id == seed["document_id"]
        assert cand.drawing_revision_id == seed["revision_id"]
        assert cand.plan_page_id is not None
        assert cand.plan_sheet_id == seed["sheet_id"]
        assert cand.takeoff_run_id == run.id
        assert cand.element_type == "INTERIOR_DOOR_OPENING"
        geom = validate_normalized_bbox(cand.geometry_data)
        assert geom["type"] == "bbox"
        assert 0.0 <= cand.confidence_numeric <= 1.0
        assert cand.confidence_band in ("LOW", "MEDIUM", "HIGH")
        assert cand.confidence_band == confidence_band_for(cand.confidence_numeric)
        assert cand.source_evidence
        assert cand.status == "suggested"
        assert cand.reviewed_by is None


def test_invalid_bbox_rejected(app):
    with pytest.raises(PlanIntelligenceServiceError, match="outside normalized"):
        validate_normalized_bbox({"x1": -0.1, "y1": 0.0, "x2": 0.2, "y2": 0.2})
    with pytest.raises(PlanIntelligenceServiceError, match="outside normalized"):
        validate_normalized_bbox({"x1": 0.0, "y1": 0.0, "x2": 1.2, "y2": 0.2})


def test_confidence_does_not_auto_accept(app):
    seed = _seed_eligible_plan()
    run = _start_run(seed)
    assert all(c.status == "suggested" for c in run.candidates)
    assert all(c.confidence_numeric >= 0.5 for c in run.candidates)
    pkg = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    with pytest.raises(PlanIntelligenceServiceError, match="remain suggested"):
        approve_package(
            organization_id=seed["organization_id"],
            package_id=pkg.id,
            approved_by="office-reviewer",
        )


def test_human_review_actions_require_actor_and_reasons(app):
    seed = _seed_eligible_plan()
    run = _start_run(seed)
    cand = run.candidates[0]
    with pytest.raises(PlanIntelligenceServiceError, match="human actor"):
        review_candidate(
            organization_id=seed["organization_id"],
            candidate_id=cand.id,
            action="accept",
            reviewed_by="",
        )
    with pytest.raises(PlanIntelligenceServiceError, match="AI/system actor"):
        review_candidate(
            organization_id=seed["organization_id"],
            candidate_id=cand.id,
            action="accept",
            reviewed_by="ai",
        )
    with pytest.raises(PlanIntelligenceServiceError, match="Adjustment reason"):
        review_candidate(
            organization_id=seed["organization_id"],
            candidate_id=cand.id,
            action="adjust",
            reviewed_by="office-reviewer",
            reviewed_quantity=2.0,
        )
    with pytest.raises(PlanIntelligenceServiceError, match="reviewed quantity"):
        review_candidate(
            organization_id=seed["organization_id"],
            candidate_id=cand.id,
            action="adjust",
            reviewed_by="office-reviewer",
            review_reason="no quantity provided",
        )
    review_candidate(
        organization_id=seed["organization_id"],
        candidate_id=cand.id,
        action="adjust",
        reviewed_by="office-reviewer",
        review_reason="Estimator counted a pair.",
        reviewed_quantity=2.0,
    )
    db.session.refresh(cand)
    assert cand.status == "adjusted"
    assert cand.reviewed_quantity == 2.0
    review_candidate(
        organization_id=seed["organization_id"],
        candidate_id=run.candidates[1].id,
        action="reject",
        reviewed_by="office-reviewer",
        review_reason="Exterior door.",
    )
    review_candidate(
        organization_id=seed["organization_id"],
        candidate_id=run.candidates[2].id,
        action="not_applicable",
        reviewed_by="office-reviewer",
        review_reason="Not an opening.",
    )
    review_candidate(
        organization_id=seed["organization_id"],
        candidate_id=run.candidates[3].id,
        action="duplicate",
        reviewed_by="office-reviewer",
        review_reason="Duplicate of adjusted candidate.",
        canonical_candidate_id=cand.id,
    )
    db.session.refresh(run)
    assert run.candidates[1].status == "rejected"
    assert run.candidates[2].status == "not_applicable"
    assert run.candidates[3].status == "duplicate"
    assert run.candidates[3].canonical_candidate_id == cand.id
    assert compute_run_reviewed_total(run) == 2.0


def test_package_total_includes_accepted_adjusted_excludes_others(app):
    seed = _seed_eligible_plan()
    run = _review_fixture(_start_run(seed))
    assert compute_run_reviewed_total(run) == 3.0
    suggested = [c for c in run.candidates if c.status == "suggested"]
    accepted = [c for c in run.candidates if c.status == "accepted"]
    duplicates = [c for c in run.candidates if c.status == "duplicate"]
    assert not suggested
    assert len(accepted) == 3
    assert len(duplicates) == 1
    pkg = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    approved = approve_package(
        organization_id=seed["organization_id"],
        package_id=pkg.id,
        approved_by="office-reviewer",
    )
    assert approved.status == "approved"
    assert approved.approved_total == 3.0
    assert approved.approved_unit == "count"
    assert len(approved.items) == 3
    assert all(item.review_status in ("accepted", "adjusted") for item in approved.items)


def test_approved_package_immutability_and_rerun_does_not_float(app):
    seed = _seed_eligible_plan()
    run = _review_fixture(_start_run(seed))
    pkg = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    approved = approve_package(
        organization_id=seed["organization_id"],
        package_id=pkg.id,
        approved_by="Joel Brayman",
    )
    frozen_qty = [(i.id, i.reviewed_quantity, i.geometry_data) for i in approved.items]
    frozen_ids = [i.takeoff_candidate_id for i in approved.items]

    with pytest.raises(PlanIntelligenceServiceError, match="immutable"):
        mutate_package(
            organization_id=seed["organization_id"],
            package_id=approved.id,
            approved_total=99,
        )
    with pytest.raises(PlanIntelligenceServiceError, match="Only draft"):
        approve_package(
            organization_id=seed["organization_id"],
            package_id=approved.id,
            approved_by="Joel Brayman",
        )

    review_candidate(
        organization_id=seed["organization_id"],
        candidate_id=frozen_ids[0],
        action="adjust",
        reviewed_by="office-reviewer",
        review_reason="Later correction must not float approved package.",
        reviewed_quantity=99.0,
    )
    run2 = _start_run(seed)
    assert run2.id != run.id
    unchanged = TakeoffPackage.query.get(approved.id)
    assert unchanged.status == "approved"
    assert [(i.id, i.reviewed_quantity, i.geometry_data) for i in unchanged.items] == frozen_qty
    assert unchanged.approved_total == 3.0


def test_drawing_revision_separation(app):
    seed = _seed_eligible_plan()
    run_a = _review_fixture(_start_run(seed))
    pkg_a = approve_package(
        organization_id=seed["organization_id"],
        package_id=create_draft_package(
            organization_id=seed["organization_id"],
            run_id=run_a.id,
            created_by="office-reviewer",
        ).id,
        approved_by="office-reviewer",
    )
    project = Project.query.get(seed["project_id"])
    rev_b = DrawingRevision(package_id=seed["package_id"], label="B", is_active=False)
    db.session.add(rev_b)
    db.session.flush()
    doc = PlanDocument.query.get(seed["document_id"])
    rev_b.documents.append(doc)
    db.session.flush()
    sheet_b = create_sheet(
        revision=rev_b,
        number="A-101",
        title="Ground Floor Plan Rev B",
        discipline_code="ARCH",
        review_status="reviewed",
        drawing_status="reviewed",
    )
    map_page_to_sheet(sheet_b, plan_document_id=doc.id, page_index=0)
    db.session.commit()

    run_b = start_extraction_run(
        organization_id=seed["organization_id"],
        project_id=project.id,
        plan_document_id=doc.id,
        drawing_revision_id=rev_b.id,
        created_by="office-reviewer",
    )
    assert run_b.drawing_revision_id == rev_b.id
    assert run_b.id != run_a.id
    with pytest.raises(PlanIntelligenceServiceError, match="same extraction run"):
        review_candidate(
            organization_id=seed["organization_id"],
            candidate_id=run_b.candidates[0].id,
            action="duplicate",
            reviewed_by="office-reviewer",
            review_reason="Cannot merge across revisions.",
            canonical_candidate_id=run_a.candidates[0].id,
        )
    db.session.refresh(pkg_a)
    assert pkg_a.drawing_revision_id == seed["revision_id"]
    assert pkg_a.status == "approved"
    assert pkg_a.approved_total == 3.0


def test_provider_neutral_mock_extractor_and_no_external_calls(app):
    src = inspect.getsource(inspect.getmodule(MockInteriorDoorExtractor))
    lowered = src.lower()
    for banned in ("openai", "anthropic", "httpx", "requests", "boto3", "google.generativeai"):
        assert banned not in lowered
    extractor = get_extractor("INTERIOR_DOOR_OPENING")
    assert extractor.provider == "calibai-mock"
    seed = _seed_eligible_plan()
    run = _start_run(seed)
    assert run.extraction_method == "deterministic_mock"
    assert run.model_name == "interior-door-count-v1"
    assert run.config_hash
    assert "openai" not in (run.provider or "").lower()


def test_searchable_pdf_eligibility_and_scanned_fail_closed(app):
    seed = _seed_eligible_plan()
    doc = PlanDocument.query.get(seed["document_id"])
    doc.has_text_layer = False
    db.session.commit()
    with pytest.raises(PlanIntelligenceServiceError, match="searchable PDF"):
        _start_run(seed)

    doc.has_text_layer = True
    page = PlanPage.query.filter_by(plan_document_id=doc.id, page_index=0).first()
    page.has_text = False
    db.session.commit()
    with pytest.raises(PlanIntelligenceServiceError, match="searchable/text-capable"):
        _start_run(seed)


def test_package_approval_refuses_ai_actor(app):
    seed = _seed_eligible_plan()
    run = _review_fixture(_start_run(seed))
    pkg = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    with pytest.raises(PlanIntelligenceServiceError, match="cannot approve"):
        approve_package(
            organization_id=seed["organization_id"],
            package_id=pkg.id,
            approved_by="ai",
        )
    with pytest.raises(PlanIntelligenceServiceError, match="cannot approve"):
        approve_package(
            organization_id=seed["organization_id"],
            package_id=pkg.id,
            approved_by="system",
        )


def test_package_cross_org_id_fails(app, org_b):
    seed_a = _seed_eligible_plan(organization_id="ORG-001")
    seed_b = _seed_eligible_plan(organization_id="ORG-002", name="Org B Takeoff")
    run_a = _review_fixture(_start_run(seed_a))
    pkg_a = create_draft_package(
        organization_id="ORG-001",
        run_id=run_a.id,
        created_by="office-reviewer",
    )
    run_b = _review_fixture(_start_run(seed_b))
    pkg_b = create_draft_package(
        organization_id="ORG-002",
        run_id=run_b.id,
        created_by="office-reviewer",
    )
    with pytest.raises(PlanIntelligenceServiceError, match="not found"):
        get_package_or_404("ORG-001", pkg_b.id)
    with pytest.raises(PlanIntelligenceServiceError, match="not found"):
        approve_package(
            organization_id="ORG-001",
            package_id=pkg_b.id,
            approved_by="office-reviewer",
        )
    found = get_package_or_404("ORG-001", pkg_a.id)
    assert found.id == pkg_a.id


def test_plan_audit_events_emitted(app):
    seed = _seed_eligible_plan()
    run = _review_fixture(_start_run(seed))
    pkg = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    approve_package(
        organization_id=seed["organization_id"],
        package_id=pkg.id,
        approved_by="office-reviewer",
    )
    types = {e.event_type for e in PlanAuditEvent.query.all()}
    expected = {
        "takeoff.run.create",
        "takeoff.run.start",
        "takeoff.run.complete",
        "takeoff.candidate.create",
        "takeoff.candidate.accept",
        "takeoff.candidate.duplicate",
        "takeoff.package.create",
        "takeoff.package.approve",
    }
    assert expected.issubset(types)
    run_events = PlanAuditEvent.query.filter_by(extraction_run_id=run.id).all()
    assert run_events


def test_no_estimate_labour_or_pricing_writes(app):
    seed = _seed_eligible_plan()
    before = {
        "estimate_versions": EstimateVersion.query.count(),
        "estimate_line_items": EstimateLineItem.query.count(),
        "labour_tasks": LabourTask.query.count(),
        "labour_mappings": LabourTaskMapping.query.count(),
        "production_rates": ProductionRateStandard.query.count(),
        "dlcr": DirectLabourCostRateStandard.query.count(),
        "labour_cal": LabourCalibrationCandidate.query.count(),
        "labour_snap": EstimateLabourSnapshot.query.count(),
        "pricing_policies": OrganizationPricingPolicy.query.count(),
        "pricing_snap": EstimatePricingSnapshot.query.count(),
        "measurements": PlanMeasurement.query.count(),
    }
    run = _review_fixture(_start_run(seed))
    pkg = create_draft_package(
        organization_id=seed["organization_id"],
        run_id=run.id,
        created_by="office-reviewer",
    )
    approve_package(
        organization_id=seed["organization_id"],
        package_id=pkg.id,
        approved_by="office-reviewer",
    )
    after = {
        "estimate_versions": EstimateVersion.query.count(),
        "estimate_line_items": EstimateLineItem.query.count(),
        "labour_tasks": LabourTask.query.count(),
        "labour_mappings": LabourTaskMapping.query.count(),
        "production_rates": ProductionRateStandard.query.count(),
        "dlcr": DirectLabourCostRateStandard.query.count(),
        "labour_cal": LabourCalibrationCandidate.query.count(),
        "labour_snap": EstimateLabourSnapshot.query.count(),
        "pricing_policies": OrganizationPricingPolicy.query.count(),
        "pricing_snap": EstimatePricingSnapshot.query.count(),
        "measurements": PlanMeasurement.query.count(),
    }
    assert after == before


def test_office_takeoff_ui(client, app):
    seed = _seed_eligible_plan()
    resp = client.get(f"/projects/{seed['project_id']}/plans/takeoff")
    assert resp.status_code == 200
    assert b"AI Take-off" in resp.data
    resp = client.post(
        f"/projects/{seed['project_id']}/plans/takeoff/runs",
        data={
            "plan_document_id": str(seed["document_id"]),
            "drawing_revision_id": str(seed["revision_id"]),
            "created_by": "office-reviewer",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Candidate #" in resp.data
    assert b"HIGH" in resp.data or b"MEDIUM" in resp.data


def test_alembic_fg010_upgrade_and_downgrade_preserves_legacy(tmp_path):
    db_path = tmp_path / "fg010_migration.db"
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

        command.upgrade(alembic_cfg, "a3b4c5d6e7f8")
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO historical_source_workbooks ("
                    "organization_id, source_id, original_filename, extension, sha256, "
                    "byte_size, template_family, ingestion_status, ingestion_version, "
                    "idempotency_key, created_at"
                    ") VALUES ("
                    "'ORG-001', 'HIST-EST-0010', 'keep.xlsx', '.xlsx', :sha, "
                    "12, 'FAMILY_A', 'INGESTED', 'v1', 'keep-key-010', '2026-01-01 00:00:00')"
                ),
                {"sha": "f" * 64},
            )
            conn.execute(
                sa.text(
                    "INSERT INTO historical_estimates ("
                    "organization_id, source_workbook_id, template_family, evidence_tier, "
                    "pricing_method, currency, extraction_confidence, review_status, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "'ORG-001', 1, 'FAMILY_A', 'TIER_C', 'COST_PLUS_MARKUP', 'CAD', 1.0, "
                    "'EXTRACTED', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO historical_labour_items ("
                    "organization_id, historical_estimate_id, task_description, crew_size, "
                    "duration_days, hours_per_day, total_man_hours, hourly_rate, "
                    "extended_labour_cost, formula_pattern, created_at"
                    ") VALUES ("
                    "'ORG-001', 1, 'ICF Labour', 2, 5, 8.0, 80, 0.13, 5200, 'crew*days*hpd', "
                    "'2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO clients (name, organization_id, created_at) "
                    "VALUES ('Legacy Client', 'ORG-001', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO projects (name, status, client_id, organization_id, created_at) "
                    "VALUES ('Legacy Project', 'Estimating', 1, 'ORG-001', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO estimates (project_id, estimate_number, title, status, created_at, updated_at) "
                    "VALUES (1, 'EST-LEG-010', 'Legacy Estimate', 'Draft', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO estimate_versions ("
                    "estimate_id, version_number, version_label, status, subtotal, "
                    "overhead_percent, profit_percent, tax_percent, total, is_locked, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "1, 1, 'v1', 'Draft', 316.80, 10, 10, 5, 402.50, 0, "
                    "'2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO plan_documents ("
                    "project_id, original_filename, stored_filename, content_type, "
                    "byte_size, sha256_hex, has_text_layer, processing_status, created_at"
                    ") VALUES ("
                    "1, 'legacy.pdf', 'legacy.pdf', 'application/pdf', 12, :sha, 1, 'succeeded', "
                    "'2026-01-01 00:00:00')"
                ),
                {"sha": "a" * 64},
            )

        command.upgrade(alembic_cfg, "b4c5d6e7f8a9")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "takeoff_extraction_runs" in tables
            assert "takeoff_candidates" in tables
            assert "takeoff_packages" in tables
            assert "takeoff_package_items" in tables
            version = conn.execute(
                sa.text("SELECT total FROM estimate_versions WHERE id=1")
            ).scalar()
            assert Decimal(str(version)) == Decimal("402.50")
            labour = conn.execute(
                sa.text("SELECT hourly_rate FROM historical_labour_items WHERE id=1")
            ).scalar()
            assert Decimal(str(labour)) == Decimal("0.13")
            filename = conn.execute(
                sa.text("SELECT original_filename FROM plan_documents WHERE id=1")
            ).scalar()
            assert filename == "legacy.pdf"
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(plan_audit_events)"))
            }
            assert "extraction_run_id" in cols
            assert "takeoff_candidate_id" in cols
            assert "takeoff_package_id" in cols

        command.downgrade(alembic_cfg, "a3b4c5d6e7f8")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "takeoff_extraction_runs" not in tables
            assert "takeoff_candidates" not in tables
            assert "takeoff_packages" not in tables
            assert "takeoff_package_items" not in tables
            leftover = conn.execute(
                sa.text("SELECT total FROM estimate_versions WHERE id=1")
            ).scalar()
            assert Decimal(str(leftover)) == Decimal("402.50")
            labour = conn.execute(
                sa.text("SELECT hourly_rate FROM historical_labour_items WHERE id=1")
            ).scalar()
            assert Decimal(str(labour)) == Decimal("0.13")
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(plan_audit_events)"))
            }
            assert "extraction_run_id" not in cols
