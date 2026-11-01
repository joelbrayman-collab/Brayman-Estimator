"""Connecting existing Calibrayt files as documents: by reference (no copy, no move), idempotent, missing files
marked, relationships correct, bytes read through the owner's reader with its SHA-256 check. Synthetic data only."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta

import pytest
from werkzeug.datastructures import FileStorage

from app import db
from app.models.documents import (
    CONTEXT_COMPANY,
    CONTEXT_CUSTOMER,
    CONTEXT_PROJECT,
    CONTEXT_SUPPLIER,
    MISSING,
    Document,
    DocumentLink,
    DocumentText,
    DocumentVersion,
)
from app.services.documents.access import office_scope
from app.services.documents.search import Filters, search
from app.services.documents.sources import DocumentUnavailable, connect_existing_documents, read_version_bytes
from tests.documents_support import ORG, OTHER_ORG, TODAY, make_app, make_world, text_pdf


@pytest.fixture
def app(tmp_path):
    from app.services.organizations import ensure_default_organization

    application = make_app(PLAN_UPLOAD_ROOT=str(tmp_path / "plans"), HISTORICAL_UPLOAD_ROOT=str(tmp_path / "hist"))
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def _plan(project, name="A1 site plan.pdf", text="Site plan ledger detail"):
    from app.plan_intelligence.services import upload_plan_pdf

    data = text_pdf(text)
    return upload_plan_pdf(project, FileStorage(stream=__import__("io").BytesIO(data), filename=name,
                                                content_type="application/pdf")), data


def _contract(world, *, with_file=True):
    from app.models.project_contract import GeneratedProjectContract
    from app.services.contract_artifact_storage import store_immutable_docx
    from tests.documents_support import docx_bytes

    data = docx_bytes("Construction contract (synthetic)")
    key, digest = store_immutable_docx(ORG, data) if with_file else (None, hashlib.sha256(data).hexdigest())
    row = GeneratedProjectContract(organization_id=ORG, client_id=world["customer"].id, project_id=world["project"].id,
                                   estimate_id=1, estimate_version_id=1, contract_number=f"BC-C-{digest[:4]}",
                                   artifact_sha256=digest, artifact_storage_key=key,
                                   artifact_media_type="application/vnd.openxmlformats-officedocument."
                                                       "wordprocessingml.document",
                                   generated_at=datetime.utcnow(), generated_by_identifier="synthetic",
                                   generation_process="synthetic")
    db.session.add(row)
    db.session.commit()
    return row, data


def _signed(world, family="CONTRACT", *, with_file=True, number="SR-0001", source_id=1):
    from app.models.signing import SigningConsentVersion, SigningExecutedArtifact, SigningFrozenArtifact, SigningRequest
    from app.services.signing_artifact_storage import store_immutable_bytes

    data = text_pdf(f"Executed {family} (synthetic)")
    key, digest = store_immutable_bytes(ORG, data, extension=".pdf")
    frozen = SigningFrozenArtifact(organization_id=ORG, document_family=family, source_record_id=source_id,
                                   media_type="application/pdf", storage_key=key, sha256=digest)
    consent = SigningConsentVersion(version_code="synthetic-v1", authority_class="SYNTHETIC_UAT", body_text="x",
                                    created_by_identifier="synthetic")
    db.session.add_all([frozen, consent])
    db.session.flush()
    request = SigningRequest(organization_id=ORG, request_number=number, document_family=family,
                             source_record_id=source_id, project_id=world["project"].id,
                             client_id=world["customer"].id, frozen_artifact_id=frozen.id,
                             authority_class="SYNTHETIC_UAT", status="EXECUTED", countersign_required=False,
                             consent_version_id=consent.id, expires_at=datetime.utcnow() + timedelta(days=7),
                             created_by_user_id=world["staff"].id, created_by_identifier="synthetic",
                             executed_at=datetime.utcnow())
    db.session.add(request)
    db.session.flush()
    if not with_file:
        key = f"{ORG}/{'d' * 64}.pdf"
        digest = "d" * 64
    executed = SigningExecutedArtifact(organization_id=ORG, signing_request_id=request.id,
                                       source_frozen_artifact_id=frozen.id, media_type="application/pdf",
                                       storage_key=key, sha256=digest)
    db.session.add(executed)
    db.session.commit()
    return request, executed, data


def _snapshot_other_tables():
    """Row counts of every table that is not a document table (connect-existing must not write them)."""
    import sqlalchemy as sa

    names = [r[0] for r in db.session.execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'document%' AND name NOT LIKE 'sqlite_%'"))]
    return {n: db.session.execute(sa.text(f'SELECT COUNT(*) FROM "{n}"')).scalar() for n in names}


def _links(document):
    return {(link.context_kind, link.target_id) for link in
            DocumentLink.query.filter_by(document_id=document.id, unlinked_at=None)}


def test_connect_existing_registers_every_source_by_reference_and_is_idempotent(app, tmp_path):
    world = make_world(crew=False)
    plan, plan_bytes = _plan(world["project"])
    contract, contract_bytes = _contract(world)
    request, executed, signed_bytes = _signed(world)
    files_before = sorted(str(p) for p in tmp_path.rglob("*") if p.is_file())
    before = _snapshot_other_tables()

    report = connect_existing_documents(ORG)
    assert report.reconciled
    assert (report.rows, report.registered, report.already, report.missing, report.failed) == (3, 3, 0, 0, 0)
    assert _snapshot_other_tables() == before  # nothing outside the document tables written
    assert sorted(str(p) for p in tmp_path.rglob("*") if p.is_file()) == files_before  # nothing copied or moved

    by_source = {v.source_kind: v for v in DocumentVersion.query.all()}
    assert by_source["PLAN_DOCUMENT"].source_id == plan.id and by_source["PLAN_DOCUMENT"].storage_key is None
    plan_doc = db.session.get(Document, by_source["PLAN_DOCUMENT"].document_id)
    assert plan_doc.document_type == "DRAWING" and plan_doc.type_basis == "CONFIRMED"
    assert _links(plan_doc) == {(CONTEXT_PROJECT, world["project"].id), (CONTEXT_CUSTOMER, world["customer"].id)}
    assert read_version_bytes(by_source["PLAN_DOCUMENT"]) == plan_bytes  # through the plan register's reader
    assert "ledger" in DocumentText.query.filter_by(version_id=by_source["PLAN_DOCUMENT"].id).one().body  # reused text

    contract_doc = db.session.get(Document, by_source["GENERATED_CONTRACT"].document_id)
    assert contract_doc.document_type == "CONTRACT"
    assert read_version_bytes(by_source["GENERATED_CONTRACT"]) == contract_bytes
    link = DocumentLink.query.filter_by(document_id=contract_doc.id, is_primary=True).one()
    assert (link.record_kind, link.record_id) == ("GENERATED_CONTRACT", contract.id)

    signed_doc = db.session.get(Document, by_source["SIGNING_EXECUTED"].document_id)
    assert signed_doc.document_type == "SIGNED_CONTRACT" and signed_doc.title.endswith(request.request_number)
    assert read_version_bytes(by_source["SIGNING_EXECUTED"]) == signed_bytes  # CaliSIGN's verified reader
    link = DocumentLink.query.filter_by(document_id=signed_doc.id, is_primary=True).one()
    assert (link.record_kind, link.record_id) == ("SIGNING_REQUEST", request.id)

    again = connect_existing_documents(ORG)
    assert (again.rows, again.registered, again.already) == (3, 0, 3) and again.reconciled
    assert Document.query.count() == 3


def test_missing_files_are_marked_not_fatal(app):
    world = make_world(crew=False)
    _contract(world, with_file=False)
    _signed(world, with_file=False)
    plan, _ = _plan(world["project"])
    from app.plan_intelligence.storage import absolute_stored_path

    os.remove(absolute_stored_path(plan.project_id, plan.stored_filename))
    report = connect_existing_documents(ORG)
    assert report.reconciled and report.registered == 3 and report.missing == 3 and report.failed == 0
    for version in DocumentVersion.query.all():
        assert version.availability == MISSING
        with pytest.raises(DocumentUnavailable):
            read_version_bytes(version)
    review = search(office_scope(world["staff"], ORG), Filters(review=True), today=TODAY)
    assert review.total == 3


def test_tampered_bytes_fail_the_owner_sha_check(app):
    world = make_world(crew=False)
    plan, _ = _plan(world["project"])
    connect_existing_documents(ORG)
    from app.plan_intelligence.storage import absolute_stored_path

    absolute_stored_path(plan.project_id, plan.stored_filename).write_bytes(b"%PDF-1.4 tampered")
    version = DocumentVersion.query.filter_by(source_kind="PLAN_DOCUMENT").one()
    with pytest.raises(DocumentUnavailable):
        read_version_bytes(version)


def test_archived_plan_is_an_archived_document_and_drawing_set_not_doubled(app):
    from app.models.construction_drawing import ConstructionDrawingSet
    from app.plan_intelligence.services import archive_plan_document

    world = make_world(crew=False)
    plan, _ = _plan(world["project"])
    archive_plan_document(plan)
    pdf = text_pdf("Drawing set")
    for i, plan_document_id in ((1, plan.id), (2, None)):  # the first was saved to plans: the plan covers it
        db.session.add(ConstructionDrawingSet(
            organization_id=ORG, project_id=world["project"].id, construction_model_revision_id=1,
            model_revision_number=1, model_content_sha256="a" * 64, takeoff_fingerprint="b" * 64, drawing_revision=i,
            engine_version="synthetic", input_fingerprint=str(i) * 64, sheet_count=1, sheet_index_json="[]",
            pdf_bytes=pdf, pdf_sha256=hashlib.sha256(pdf).hexdigest(), dxf_bytes=b"0", dxf_sha256="c" * 64,
            plan_document_id=plan_document_id, created_by="synthetic"))
    db.session.commit()
    report = connect_existing_documents(ORG)
    assert report.kinds["DRAWING_SET"].rows == 1 and report.kinds["PLAN_DOCUMENT"].rows == 1
    plan_version = DocumentVersion.query.filter_by(source_kind="PLAN_DOCUMENT").one()
    assert db.session.get(Document, plan_version.document_id).status == "ARCHIVED"
    set_version = DocumentVersion.query.filter_by(source_kind="DRAWING_SET").one()
    assert read_version_bytes(set_version) == pdf


def test_project_limited_connect_and_organization_isolation(app):
    world = make_world(crew=False)
    _plan(world["project"], "a.pdf", "first job")
    _plan(world["second"], "b.pdf", "second job")
    _plan(world["other_project"], "c.pdf", "other organization")
    report = connect_existing_documents(ORG, project_id=world["project"].id)
    assert report.registered == 1
    assert connect_existing_documents(ORG).registered == 1  # the second project's plan
    assert connect_existing_documents(OTHER_ORG).registered == 1
    assert Document.query.filter_by(organization_id=ORG).count() == 2
    for version in DocumentVersion.query.all():
        document = db.session.get(Document, version.document_id)
        assert version.organization_id == document.organization_id


def test_dry_run_keeps_nothing(app):
    world = make_world(crew=False)
    _plan(world["project"])
    report = connect_existing_documents(ORG, dry_run=True)
    assert report.registered == 1
    assert Document.query.count() == 0 and DocumentVersion.query.count() == 0


def test_supplier_order_links_the_supplier_the_org_has_an_account_with(app):
    from app.models.supplier_portal import SupplierPurchaseOrder

    world = make_world(crew=False)
    columns = {c.name for c in SupplierPurchaseOrder.__table__.columns if not c.nullable and c.default is None
               and not c.primary_key}
    values = {"organization_id": ORG, "project_id": world["project"].id, "supplier_id": world["supplier"].id}
    for name in columns - set(values):
        column = SupplierPurchaseOrder.__table__.columns[name]
        python_type = getattr(column.type, "python_type", str)
        values[name] = (datetime.utcnow() if python_type is datetime else 1 if python_type is int else
                        __import__("decimal").Decimal("1") if python_type.__name__ == "Decimal" else
                        __import__("datetime").date.today() if python_type.__name__ == "date" else "SYN")
    order = SupplierPurchaseOrder(**values)
    db.session.add(order)
    db.session.commit()
    _signed(world, "SUPPLIER_ORDER", number="SR-PO-1", source_id=order.id)
    connect_existing_documents(ORG)
    version = DocumentVersion.query.filter_by(source_kind="SIGNING_EXECUTED").one()
    document = db.session.get(Document, version.document_id)
    assert document.document_type == "PURCHASE_ORDER"
    assert (CONTEXT_SUPPLIER, world["supplier"].id) in _links(document)
    assert (CONTEXT_CUSTOMER, world["customer"].id) not in _links(document)


def test_historical_workbook_is_a_company_document(app):
    from app.models.historical_estimates import HistoricalSourceWorkbook
    from app.services.historical_ingestion.storage import store_immutable_bytes

    make_world(crew=False)
    data = b"PK\x03\x04 synthetic workbook"
    digest = hashlib.sha256(data).hexdigest()
    store_immutable_bytes(ORG, digest, ".xlsm", data)
    db.session.add(HistoricalSourceWorkbook(organization_id=ORG, source_id="HIST-EST-0001", original_filename="job.xlsm",
                                            extension=".xlsm", sha256=digest, byte_size=len(data),
                                            template_family="FAMILY_A", idempotency_key="synthetic-1"))
    db.session.commit()
    connect_existing_documents(ORG)
    version = DocumentVersion.query.filter_by(source_kind="HISTORICAL_WORKBOOK").one()
    assert _links(db.session.get(Document, version.document_id)) == {(CONTEXT_COMPANY, None)}
    assert read_version_bytes(version) == data
