"""Company documents: identity, versions, audit, storage, duplicates, classification, extraction and dates.
Synthetic data only."""

from __future__ import annotations

import os
from datetime import date

import pytest
import sqlalchemy as sa

from app import db
from app.models.documents import (
    CONTEXT_COMPANY,
    CONTEXT_EQUIPMENT,
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    CONTEXT_SUBCONTRACTOR,
    CONTEXT_SUPPLIER,
    DATE_CONFIRMED,
    DATE_EXPIRES,
    DATE_INSPECTION_DUE,
    DATE_ISSUED,
    DATE_PROPOSED,
    DATE_REJECTED,
    DATE_RENEWAL_DUE,
    DATE_WARRANTY_ENDS,
    DATE_EFFECTIVE,
    SENSITIVITY_FINANCIAL,
    SENSITIVITY_PEOPLE,
    Document,
    DocumentDate,
    DocumentEvent,
    DocumentLink,
    DocumentText,
    DocumentVersion,
)
from app.services import document_storage as storage
from app.services.documents import dates as date_rules
from app.services.documents import ingest
from app.services.documents.contexts import DocumentNotFound, resolve_context
from app.services.documents.extract import extract_text
from app.services.documents.ingest import Actor, DocumentError, prepare_upload
from app.services.documents.sources import read_version_bytes
from app.services.documents.types import classify
from tests.documents_support import (
    ORG,
    OTHER_ORG,
    PNG_1PX,
    TODAY,
    app,  # noqa: F401  (fixture)
    blank_pdf,
    ctx,
    docx_bytes,
    file_pdf,
    make_world,
    text_pdf,
)


@pytest.fixture
def world(app):
    return make_world(crew=False)


def _events(document):
    return [e.event_type for e in DocumentEvent.query.filter_by(document_id=document.id).order_by(DocumentEvent.id)]


# ------------------------------------------------------------------ identity


def test_system_assigns_identity_and_same_filename_twice_is_two_documents(world):
    a = file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "deck-plan.pdf", "Sheet A1 deck framing")
    b = file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "deck-plan.pdf", "Sheet A2 stairs")
    assert a.public_id != b.public_id and len(a.public_id) == 32
    assert a.title == "deck-plan"  # falls back to the file name
    assert Document.query.count() == 2


def test_upload_creates_card_version_link_and_events_in_one_go(world):
    doc = file_pdf(world["staff"], CONTEXT_SUBCONTRACTOR, world["sub"].id, "WSIB_clearance_Acme.pdf",
                   "Workplace Safety and Insurance Board", "Clearance certificate valid until March 31, 2027")
    v = doc.current_version
    assert v.version_number == 1 and v.is_current and v.source_kind == "UPLOAD"
    assert v.sha256 == storage.sha256_hex(read_version_bytes(v))
    assert doc.document_type == "WSIB_CLEARANCE" and doc.type_rule.startswith("WSIB_CLEARANCE:")
    link = DocumentLink.query.filter_by(document_id=doc.id).one()
    assert link.context_kind == CONTEXT_SUBCONTRACTOR and link.subcontractor_id == world["sub"].id and link.is_primary
    assert _events(doc)[:3] == ["CREATED", "VERSION_ADDED", "LINK_ADDED"]
    assert "TEXT_EXTRACTED" in _events(doc) and "DATE_PROPOSED" in _events(doc)
    row = DocumentDate.query.filter_by(document_id=doc.id, date_kind=DATE_EXPIRES).one()
    assert row.status == DATE_PROPOSED and row.value == date(2027, 3, 31)
    assert "valid until" in row.evidence_text


# ------------------------------------------------------------------ versions


def test_new_version_supersedes_keeps_history_and_old_bytes(world):
    actor = Actor.of(world["staff"])
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "insurance-2026.pdf", "Certificate of insurance 2026")
    first = doc.current_version
    old_bytes = read_version_bytes(first)
    v2 = ingest.add_version(doc, actor, prepare_upload("insurance-2027.pdf", text_pdf("Certificate of insurance 2027")),
                            "Renewed for 2027")
    versions = DocumentVersion.query.filter_by(document_id=doc.id).order_by(DocumentVersion.version_number).all()
    assert [v.version_number for v in versions] == [1, 2]
    assert [v.is_current for v in versions] == [False, True]
    assert read_version_bytes(versions[0]) == old_bytes
    assert v2.note == "Renewed for 2027"
    assert "VERSION_SUPERSEDED" in _events(doc)


def test_identical_upload_to_current_version_is_refused(world):
    data = text_pdf("Same bytes")
    doc = ingest.file_document(ORG, Actor.of(world["staff"]), blob=prepare_upload("a.pdf", data),
                               context=ctx(CONTEXT_COMPANY))
    with pytest.raises(DocumentError, match="already the current version"):
        ingest.add_version(doc, Actor.of(world["staff"]), prepare_upload("b.pdf", data))


def test_database_refuses_a_second_current_version(world):
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "policy.pdf", "Policy")
    v = doc.current_version
    db.session.add(DocumentVersion(organization_id=ORG, document_id=doc.id, version_number=2, is_current=True,
                                   source_kind="UPLOAD", storage_key=v.storage_key, sha256=v.sha256, byte_size=1,
                                   media_type=v.media_type, original_filename="x.pdf", created_by_name="t"))
    with pytest.raises(sa.exc.IntegrityError):
        db.session.flush()
    db.session.rollback()


# ------------------------------------------------------------------ audit


def test_audit_events_are_insert_only_in_the_database(world):
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "policy.pdf", "Policy")
    with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
        db.session.execute(sa.text("UPDATE document_events SET actor_name = 'x'"))
    db.session.rollback()
    with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
        db.session.execute(sa.text("DELETE FROM document_events"))
    db.session.rollback()
    assert DocumentEvent.query.filter_by(document_id=doc.id).count() >= 3


def test_corrections_need_a_reason_and_record_previous_and_new(world):
    actor = Actor.of(world["staff"])
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "policy.pdf", "Policy")
    with pytest.raises(DocumentError, match="why"):
        ingest.correct_field(doc, actor, "title", "Safety policy", "")
    with pytest.raises(DocumentError):
        ingest.correct_field(doc, actor, "organization_id", "ORG-X", "nope")
    with pytest.raises(DocumentError, match="people administrator"):
        ingest.correct_field(doc, actor, "sensitivity", "PEOPLE", "reason")
    ingest.correct_field(doc, actor, "title", "Safety policy", "Proper name")
    event = DocumentEvent.query.filter_by(document_id=doc.id, event_type="FIELD_CORRECTED").one()
    assert (event.field_name, event.previous_value, event.new_value, event.reason) == (
        "title", "policy", "Safety policy", "Proper name")


def test_no_file_content_or_extracted_text_reaches_events(world):
    secret = "ZEBRA-CONTENT-MARKER"
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "notes.pdf", f"Body text {secret}")
    assert secret in DocumentText.query.filter_by(version_id=doc.current_version.id).one().body
    for e in DocumentEvent.query.filter_by(document_id=doc.id):
        blob = " ".join(str(x) for x in (e.previous_value, e.new_value, e.reason, e.detail_json))
        assert secret not in blob


def test_archive_needs_a_reason_and_restore_works(world):
    actor = Actor.of(world["staff"])
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "old-form.pdf", "Old form")
    with pytest.raises(DocumentError):
        ingest.archive(doc, actor, " ")
    ingest.archive(doc, actor, "Replaced by the 2027 form")
    assert doc.status == "ARCHIVED" and doc.archive_reason == "Replaced by the 2027 form"
    ingest.restore(doc, actor)
    assert doc.status == "ACTIVE"
    assert Document.query.count() == 1  # never deleted


# ------------------------------------------------------------------ storage


def test_storage_is_content_addressed_write_once_and_contained(app, world):
    data = text_pdf("stored once")
    key, digest = storage.store_bytes(ORG, data, ".pdf")
    assert key == f"{ORG}/{digest[:2]}/{digest}.pdf"
    again, _ = storage.store_bytes(ORG, data, ".pdf")
    assert again == key
    path = storage.absolute_stored_path(key)
    root = storage.get_document_root().resolve()
    assert root in path.parents
    path.write_bytes(b"%PDF-tampered")
    with pytest.raises(storage.DocumentStorageError, match="overwrite"):
        storage.store_bytes(ORG, data, ".pdf")
    with pytest.raises(storage.DocumentStorageError):
        storage.read_verified(key, digest)
    for bad in ("../x/aa/" + "a" * 64 + ".pdf", f"{ORG}/../../etc/passwd", "/etc/passwd", f"{ORG}/aa/notasha.pdf",
                f"..{os.sep}{ORG}/aa/{'a' * 64}.pdf", f"{ORG}/bb/{'a' * 64}.pdf"):
        with pytest.raises(storage.DocumentStorageError):
            storage.absolute_stored_path(bad)
    with pytest.raises(storage.DocumentStorageError):
        storage.store_bytes("../evil", data, ".pdf")


def test_storage_refuses_symlinks(app, world):
    target = storage.get_document_root() / "outside.pdf"
    target.write_bytes(text_pdf("outside"))
    digest = "c" * 64
    link_dir = storage.get_document_root() / ORG / digest[:2]
    link_dir.mkdir(parents=True, exist_ok=True)
    (link_dir / f"{digest}.pdf").symlink_to(target)
    with pytest.raises(storage.DocumentStorageError):
        storage.absolute_stored_path(f"{ORG}/{digest[:2]}/{digest}.pdf")


def test_upload_validation_type_size_and_magic(app, world):
    with pytest.raises(DocumentError, match="can't be filed"):
        prepare_upload("tool.exe", b"MZ....")
    with pytest.raises(DocumentError, match="not a PDF"):
        prepare_upload("fake.pdf", b"hello")
    with pytest.raises(DocumentError, match="empty"):
        prepare_upload("empty.pdf", b"")
    app.config["DOCUMENT_MAX_BYTES"] = 1024
    with pytest.raises(DocumentError, match="larger than"):
        prepare_upload("big.pdf", b"%PDF-" + b"0" * 2048)
    app.config["DOCUMENT_MAX_BYTES"] = 25 * 1024 * 1024
    assert prepare_upload("site.png", PNG_1PX).media_type == "image/png"


def test_same_bytes_in_two_organizations_are_two_files(world):
    data = text_pdf("shared bytes")
    key_a, _ = storage.store_bytes(ORG, data, ".pdf")
    key_b, _ = storage.store_bytes(OTHER_ORG, data, ".pdf")
    assert key_a != key_b and key_a.startswith(ORG + "/") and key_b.startswith(OTHER_ORG + "/")


# ------------------------------------------------------------------ duplicates


def test_duplicates_found_only_inside_the_organization_and_link_it_here(world):
    data = text_pdf("COI for Acme")
    staff = Actor.of(world["staff"])
    doc = ingest.file_document(ORG, staff, blob=prepare_upload("coi.pdf", data),
                               context=ctx(CONTEXT_SUBCONTRACTOR, world["sub"].id))
    current, other = ingest.find_duplicates(ORG, storage.sha256_hex(data))
    assert [d.id for d in current] == [doc.id] and other == []
    assert ingest.find_duplicates(OTHER_ORG, storage.sha256_hex(data)) == ([], [])
    ingest.link_existing_here(doc, staff, ctx(CONTEXT_PROJECT, world["project"].id))
    assert Document.query.count() == 1
    kinds = {link.context_kind for link in DocumentLink.query.filter_by(document_id=doc.id, unlinked_at=None)}
    assert kinds == {CONTEXT_SUBCONTRACTOR, CONTEXT_PROJECT}
    assert "DUPLICATE_LINKED" in _events(doc)
    # Filing it as a separate document is still possible; the stored file is shared.
    second = ingest.file_document(ORG, staff, blob=prepare_upload("coi-copy.pdf", data),
                                  context=ctx(CONTEXT_COMPANY))
    assert second.current_version.storage_key == doc.current_version.storage_key


def test_link_cannot_end_the_last_link_and_needs_a_reason(world):
    staff = Actor.of(world["staff"])
    doc = file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "spec.pdf", "Spec")
    only = DocumentLink.query.filter_by(document_id=doc.id).one()
    with pytest.raises(DocumentError, match="must stay linked"):
        ingest.end_link(doc, staff, only, "wrong job")
    extra = ingest.add_link(doc, staff, ctx(CONTEXT_PROJECT, world["second"].id))
    db.session.commit()
    with pytest.raises(DocumentError):
        ingest.end_link(doc, staff, extra, "")
    ingest.end_link(doc, staff, extra, "Wrong job")
    assert extra.unlinked_at is not None and DocumentLink.query.count() == 2  # ended, not deleted


# ------------------------------------------------------------------ contexts


def test_contexts_resolve_inside_the_organization_only(world):
    with pytest.raises(DocumentNotFound):
        resolve_context(ORG, CONTEXT_PROJECT, world["other_project"].id)
    with pytest.raises(DocumentNotFound):
        resolve_context(ORG, CONTEXT_SUBCONTRACTOR, world["other_sub"].id)
    with pytest.raises(DocumentNotFound):
        resolve_context(ORG, CONTEXT_SUPPLIER, world["stranger"].id)  # shared table, but no account with them
    assert resolve_context(ORG, CONTEXT_SUPPLIER, world["supplier"].id).label.startswith("Valley")
    with pytest.raises(DocumentNotFound):
        resolve_context(OTHER_ORG, CONTEXT_SUPPLIER, world["supplier"].id)
    with pytest.raises(DocumentNotFound):
        resolve_context(ORG, "MATTER", 1)


def test_person_context_documents_default_to_people_sensitivity(world):
    from app.models.user import UserMembership

    membership = UserMembership.query.filter_by(user_id=world["staff"].id, organization_id=ORG).one()
    doc = file_pdf(world["owner"], CONTEXT_PERSON, membership.id, "working-at-heights-ticket.pdf", "Working at Heights")
    assert doc.sensitivity == SENSITIVITY_PEOPLE and doc.document_type == "CERTIFICATION"
    invoice = file_pdf(world["staff"], CONTEXT_PROJECT, world["project"].id, "invoice-1042.pdf", "Invoice")
    assert invoice.document_type == "INVOICE" and invoice.sensitivity == SENSITIVITY_FINANCIAL


# ------------------------------------------------------------------ classification


CLASSIFICATION_CASES = [
    ("WSIB_clearance_Acme.pdf", CONTEXT_SUBCONTRACTOR, "WSIB_CLEARANCE"),
    ("wsib-2027.pdf", CONTEXT_COMPANY, "WSIB_CLEARANCE"),
    ("Clearance Certificate.pdf", CONTEXT_SUBCONTRACTOR, "WSIB_CLEARANCE"),
    ("COI Acme Framing.pdf", CONTEXT_SUBCONTRACTOR, "INSURANCE_CERT"),
    ("certificate_of_insurance.pdf", CONTEXT_COMPANY, "INSURANCE_CERT"),
    ("liability insurance 2027.pdf", CONTEXT_SUPPLIER, "INSURANCE_CERT"),
    ("CGL policy wording.pdf", CONTEXT_SUBCONTRACTOR, "INSURANCE_CERT"),
    ("Tarion registration.pdf", CONTEXT_COMPANY, "LICENCE"),
    ("electrical licence.pdf", CONTEXT_SUBCONTRACTOR, "LICENCE"),
    ("building permit 24-118.pdf", CONTEXT_PROJECT, "PERMIT"),
    ("health and safety policy.pdf", CONTEXT_COMPANY, "POLICY"),
    ("employee handbook.pdf", CONTEXT_COMPANY, "POLICY"),
    ("lockout procedure.pdf", CONTEXT_COMPANY, "PROCEDURE"),
    ("hazard assessment.pdf", CONTEXT_PROJECT, "SAFETY"),
    ("toolbox talk week 12.pdf", CONTEXT_COMPANY, "SAFETY"),
    ("SDS concrete sealer.pdf", CONTEXT_PROJECT, "SAFETY"),
    ("Working at Heights ticket.pdf", CONTEXT_PERSON, "CERTIFICATION"),
    ("WHMIS 2026.pdf", CONTEXT_PERSON, "CERTIFICATION"),
    ("first aid cpr.pdf", CONTEXT_PERSON, "CERTIFICATION"),
    ("forklift certification.pdf", CONTEXT_PERSON, "CERTIFICATION"),
    ("offer letter.pdf", CONTEXT_PERSON, "EMPLOYMENT"),
    ("orientation record.pdf", CONTEXT_PERSON, "TRAINING_RECORD"),
    ("policy acknowledgement signed.pdf", CONTEXT_PERSON, "SIGNED_POLICY"),
    ("Kubota KX040 operator manual.pdf", CONTEXT_EQUIPMENT, "MANUAL"),
    ("annual inspection 2026.pdf", CONTEXT_EQUIPMENT, "INSPECTION"),
    ("CVIP truck 3.pdf", CONTEXT_EQUIPMENT, "INSPECTION"),
    ("trailer registration.pdf", CONTEXT_EQUIPMENT, "REGISTRATION"),
    ("service record oil change.pdf", CONTEXT_EQUIPMENT, "MAINTENANCE"),
    ("bill of sale.pdf", CONTEXT_EQUIPMENT, "PURCHASE"),
    ("A1 site plan.pdf", CONTEXT_PROJECT, "DRAWING"),
    ("elevations rev B.pdf", CONTEXT_PROJECT, "DRAWING"),
    ("deck specs.pdf", CONTEXT_PROJECT, "SPECIFICATION"),
    ("composite decking installation instructions.pdf", CONTEXT_PROJECT, "INSTRUCTION"),
    ("change order 3.pdf", CONTEXT_PROJECT, "CHANGE_ORDER"),
    ("purchase order 5512.pdf", CONTEXT_SUPPLIER, "PURCHASE_ORDER"),
    ("lumber quote.pdf", CONTEXT_SUPPLIER, "SUPPLIER_QUOTE"),
    ("subcontract framing.pdf", CONTEXT_SUBCONTRACTOR, "SUBCONTRACT"),
    ("roof membrane warranty.pdf", CONTEXT_PROJECT, "WARRANTY"),
    ("generator warranty.pdf", CONTEXT_EQUIPMENT, "WARRANTY"),
    ("credit application.pdf", CONTEXT_SUPPLIER, "AGREEMENT"),
    ("product data sheet.pdf", CONTEXT_SUPPLIER, "PRODUCT_INFO"),
    ("IMG_2041.jpg", CONTEXT_PROJECT, "PHOTO"),
    ("closeout package.pdf", CONTEXT_PROJECT, "CLOSEOUT"),
    ("invoice 1042.pdf", CONTEXT_PROJECT, "INVOICE"),
    ("random scan 0001.pdf", CONTEXT_PROJECT, "OTHER"),
    ("Working at Heights ticket.pdf", CONTEXT_PROJECT, "OTHER"),  # people types only in a person context
    ("wsib.pdf", CONTEXT_EQUIPMENT, "OTHER"),  # not offered for equipment
]


@pytest.mark.parametrize("filename,context,expected", CLASSIFICATION_CASES)
def test_classification_table(filename, context, expected):
    assert classify(filename, context)[0] == expected


def test_classification_uses_text_when_the_name_says_nothing():
    assert classify("scan0004.pdf", CONTEXT_SUBCONTRACTOR,
                    "This is to certify that the WSIB clearance certificate applies until June 2027")[0] == "WSIB_CLEARANCE"


# ------------------------------------------------------------------ extraction


def test_extraction_text_pdf_scanned_docx_corrupt_and_unsupported():
    assert extract_text(text_pdf("Hello inspection"), "application/pdf").status == "EXTRACTED"
    assert extract_text(blank_pdf(), "application/pdf").status == "NO_TEXT"
    docx = extract_text(docx_bytes("Warranty period ends 2030-01-15"),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert docx.status == "EXTRACTED" and "2030-01-15" in docx.body
    assert extract_text(b"%PDF-1.4 broken", "application/pdf").status == "FAILED"
    assert extract_text(PNG_1PX, "image/png").status == "UNSUPPORTED"
    assert extract_text("a,b\n1,2".encode(), "text/csv").status == "EXTRACTED"


def test_corrupt_pdf_still_files(world):
    doc = ingest.file_document(ORG, Actor.of(world["staff"]), blob=prepare_upload("broken.pdf", b"%PDF-1.4 broken"),
                               context=ctx(CONTEXT_COMPANY))
    assert DocumentText.query.filter_by(version_id=doc.current_version.id).one().status == "FAILED"


# ------------------------------------------------------------------ dates


DATE_CASES = [
    ("Policy period: January 1, 2026 to March 31, 2027", DATE_EXPIRES, date(2027, 3, 31)),
    ("Valid until 2027-06-30", DATE_EXPIRES, date(2027, 6, 30)),
    ("Expiry date: 30/06/2027", DATE_EXPIRES, date(2027, 6, 30)),
    ("This clearance is valid from 01 Nov 2026 to 31 Jan 2027", DATE_EXPIRES, date(2027, 1, 31)),
    ("Date of issue: Oct 15 2026", DATE_ISSUED, date(2026, 10, 15)),
    ("Effective date 2026-11-01", DATE_EFFECTIVE, date(2026, 11, 1)),
    ("Next inspection due 2027-04-12", DATE_INSPECTION_DUE, date(2027, 4, 12)),
    ("Renewal by May 1, 2027", DATE_RENEWAL_DUE, date(2027, 5, 1)),
    ("Warranty coverage ends December 31, 2036", DATE_WARRANTY_ENDS, date(2036, 12, 31)),
    ("Expires Sept 5th, 2027", DATE_EXPIRES, date(2027, 9, 5)),
]


@pytest.mark.parametrize("text,kind,expected", DATE_CASES)
def test_date_phrases(text, kind, expected):
    found = {(c.kind, c.value) for c in date_rules.find_dates(text, today=TODAY)}
    assert (kind, expected) in found


def test_ambiguous_day_month_is_proposed_both_ways():
    found = date_rules.find_dates("Expires 03/04/2027", today=TODAY)
    assert {c.value for c in found} == {date(2027, 4, 3), date(2027, 3, 4)}
    assert all(c.ambiguous for c in found)


def test_out_of_range_and_uncued_dates_are_dropped():
    assert date_rules.find_dates("Expires 2019-01-01. Expires 2090-01-01. Meeting on 2027-01-01.", today=TODAY) == []


def test_at_most_two_proposals_per_kind_latest_expiry_first():
    text = "Expires 2027-01-01. Expires 2027-02-01. Expires 2027-03-01."
    found = date_rules.find_dates(text, today=TODAY)
    assert [c.value for c in found] == [date(2027, 3, 1), date(2027, 2, 1)]


def test_confirm_change_reject_and_enter_dates_are_audited(world):
    actor = Actor.of(world["staff"])
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "insurance.pdf", "Policy expires 2027-03-31",
                   "Issued 2026-10-01")
    expiry = DocumentDate.query.filter_by(document_id=doc.id, date_kind=DATE_EXPIRES).one()
    issued = DocumentDate.query.filter_by(document_id=doc.id, date_kind=DATE_ISSUED).one()
    with pytest.raises(DocumentError, match="why"):
        ingest.confirm_date(doc, actor, expiry.id, value=date(2027, 4, 30))
    ingest.confirm_date(doc, actor, expiry.id, value=date(2027, 4, 30), reason="Broker letter extends it")
    assert expiry.status == DATE_CONFIRMED and expiry.value == date(2027, 4, 30)
    ingest.reject_date(doc, actor, issued.id)
    assert issued.status == DATE_REJECTED
    with pytest.raises(DocumentError, match="why"):
        ingest.enter_date(doc, actor, DATE_EXPIRES, date(2027, 5, 31))
    entered = ingest.enter_date(doc, actor, DATE_EXPIRES, date(2027, 5, 31), reason="Corrected certificate")
    assert entered.basis == "ENTERED" and entered.status == DATE_CONFIRMED
    assert expiry.status == DATE_REJECTED  # only one confirmed date per kind on a version
    types = _events(doc)
    for t in ("DATE_PROPOSED", "DATE_CHANGED", "DATE_CONFIRMED", "DATE_REJECTED", "DATE_ENTERED"):
        assert t in types
    with pytest.raises(sa.exc.IntegrityError):
        db.session.add(DocumentDate(organization_id=ORG, document_id=doc.id, version_id=entered.version_id,
                                    date_kind=DATE_EXPIRES, value=date(2027, 1, 1), basis="ENTERED",
                                    status=DATE_CONFIRMED, remind_days_before=30))
        db.session.flush()
    db.session.rollback()


def test_large_file_extraction_is_deferred_to_first_open(app, world):
    from app.services.documents import extract

    original = extract.MAX_SYNC_BYTES
    extract.MAX_SYNC_BYTES = 10
    try:
        doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "manual.pdf", "Next inspection due 2027-02-01")
        assert DocumentText.query.count() == 0
    finally:
        extract.MAX_SYNC_BYTES = original
    assert ingest.ensure_extracted(doc) is True
    assert DocumentDate.query.filter_by(document_id=doc.id, date_kind=DATE_INSPECTION_DUE).count() == 1
    assert ingest.ensure_extracted(doc) is False  # once only
