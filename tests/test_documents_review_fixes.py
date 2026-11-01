"""Company documents: review fixes I1, I3, M2, M3 (1 Nov 2026). Synthetic data only.

I1  A STANDARD document linked into a person's page ("Link it here", or "Link to" on the document page) becomes a
    PEOPLE document (an audit event records why); any document with an active person link is hidden from viewers who
    are not people administrators (lists, search, opening, ending links), and person names are never shown to them.
I3  Opening a document never extracts a file larger than MAX_SYNC_BYTES in the request (left to
    ``flask documents reindex``), and a concurrent first open that already stored the text does not fail.
M2  A document type must be one offered for the filing context; changing the type recomputes who may see it, never
    below PEOPLE while a person link is active.
M3  A new subcontractor's generated code fits the 30-character column even with a "-N" suffix.
"""

from __future__ import annotations

import io

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.documents import (
    CONTEXT_COMPANY,
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    CONTEXT_SUBCONTRACTOR,
    SENSITIVITY_FINANCIAL,
    SENSITIVITY_PEOPLE,
    SENSITIVITY_STANDARD,
    Document,
    DocumentEvent,
    DocumentLink,
    DocumentText,
)
from app.models.subcontractor import Subcontractor
from app.models.user import UserMembership
from app.services.documents import extract, ingest
from app.services.documents.access import office_scope
from app.services.documents.ingest import Actor
from app.services.documents.search import Filters, search
from tests.documents_support import (  # noqa: F401  (fixture)
    ORG,
    OWNER,
    STAFF,
    TODAY,
    app,
    ctx,
    file_pdf,
    like_app,
    make_world,
    signed_in,
    text_pdf,
)

pytestmark = pytest.mark.no_office_auth


@pytest.fixture
def world(app):
    return make_world(crew=False)


def _membership(user):
    return UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()


def _upload(client, context, context_id, filename, data):
    form = {"context": context, "file": (io.BytesIO(data), filename)}
    if context_id is not None:
        form["context_id"] = str(context_id)
    return client.post("/documents/upload", data=form, content_type="multipart/form-data")


# ------------------------------------------------------------------ I1


def _person_world(app, world):
    """A company document Sam Staff can see; the owner links it into Sam's person page with "Link it here"."""
    person = _membership(world["staff"])
    data = text_pdf("Driver abstract", "Kowalczyk")
    doc = ingest.file_document(ORG, Actor.of(world["staff"]), blob=ingest.prepare_upload("abstract.pdf", data),
                               context=ctx(CONTEXT_COMPANY), today=TODAY)
    assert doc.sensitivity == SENSITIVITY_STANDARD
    owner = signed_in(app, OWNER)
    review = _upload(owner, CONTEXT_PERSON, person.id, "abstract.pdf", data)
    assert review.status_code == 200 and doc.public_id.encode() in review.data  # the duplicate prompt
    linked = owner.post("/documents/upload/link", data={"context": CONTEXT_PERSON, "context_id": str(person.id),
                                                        "public_id": doc.public_id})
    assert linked.status_code == 302
    db.session.expire_all()
    return person, db.session.get(Document, doc.id), owner


def test_link_it_here_from_a_person_page_makes_the_document_a_people_document(app, world):
    person, doc, _owner = _person_world(app, world)
    assert doc.sensitivity == SENSITIVITY_PEOPLE
    event = DocumentEvent.query.filter_by(document_id=doc.id, event_type="FIELD_CORRECTED",
                                          field_name="sensitivity").one()
    assert (event.previous_value, event.new_value) == (SENSITIVITY_STANDARD, SENSITIVITY_PEOPLE)
    assert "person" in event.reason.lower()


def test_after_link_it_here_a_non_admin_cannot_see_search_or_end_the_person_link(app, world):
    person, doc, owner = _person_world(app, world)
    staff = signed_in(app, STAFF)
    assert staff.get(f"/documents/{doc.public_id}").status_code == 404
    assert doc.public_id.encode() not in staff.get("/documents").data
    assert doc.public_id.encode() not in staff.get("/documents?q=abstract").data
    assert doc.public_id.encode() not in staff.get("/documents?q=Staff").data  # the person's name
    link = DocumentLink.query.filter_by(document_id=doc.id, context_kind=CONTEXT_PERSON).one()
    ended = staff.post(f"/documents/{doc.public_id}/links/{link.id}/end", data={"reason": "not hers"})
    assert ended.status_code == 404
    db.session.expire_all()
    assert db.session.get(DocumentLink, link.id).unlinked_at is None
    # The people administrator still sees it, with the person's name.
    page = owner.get(f"/documents/{doc.public_id}")
    assert page.status_code == 200 and b"Sam Staff" in page.data
    assert doc.public_id.encode() in owner.get("/documents?q=abstract").data


def test_linking_from_the_document_page_into_a_person_also_raises_sensitivity(app, world):
    person = _membership(world["staff"])
    doc = file_pdf(world["owner"], CONTEXT_COMPANY, None, "policy.pdf", "Safety policy")
    owner = signed_in(app, OWNER)
    owner.post(f"/documents/{doc.public_id}/links", data={"context": CONTEXT_PERSON, "context_id": str(person.id)})
    db.session.expire_all()
    assert db.session.get(Document, doc.id).sensitivity == SENSITIVITY_PEOPLE


def test_scope_hides_any_document_with_an_active_person_link_even_if_standard(app, world):
    """Defence in depth: a STANDARD row with a person link (e.g. written before this fix) is hidden from non-admins,
    in the browse, FTS and LIKE paths, and its person label is not shown."""
    person = _membership(world["staff"])
    doc = file_pdf(world["owner"], CONTEXT_COMPANY, None, "abstract.pdf", "Driver abstract")
    ingest.add_link(doc, Actor.of(world["owner"]), ctx(CONTEXT_PERSON, person.id))
    doc.sensitivity = SENSITIVITY_STANDARD  # simulate a row from before the fix
    db.session.commit()
    staff_scope = office_scope(world["staff"], ORG)
    owner_scope = office_scope(world["owner"], ORG)
    for mode in (None, "like"):
        for q in ("", "abstract", "Staff"):
            ids = [r.document.id for r in search(staff_scope, Filters(q=q), today=TODAY, mode=mode).rows]
            assert doc.id not in ids, (mode, q)
        assert doc.id in [r.document.id for r in search(owner_scope, Filters(q="abstract"), today=TODAY,
                                                        mode=mode).rows]


def test_person_labels_are_hidden_from_viewers_who_are_not_people_admins(app, world):
    from app.services.documents.contexts import labels_for_documents

    person = _membership(world["staff"])
    doc = file_pdf(world["owner"], CONTEXT_PROJECT, world["project"].id, "plan.pdf", "plan")
    ingest.add_link(doc, Actor.of(world["owner"]), ctx(CONTEXT_PERSON, person.id))
    db.session.commit()
    kinds = [k for k, *_ in labels_for_documents(ORG, [doc.id], include_people=False)[doc.id]]
    assert CONTEXT_PERSON not in kinds and CONTEXT_PROJECT in kinds
    assert CONTEXT_PERSON in [k for k, *_ in labels_for_documents(ORG, [doc.id])[doc.id]]


def test_the_search_index_labels_never_reach_a_non_admin(app, world):
    """The FTS labels column holds the person's name; a non-admin search by that name finds nothing."""
    person = _membership(world["staff"])
    doc = file_pdf(world["owner"], CONTEXT_PERSON, person.id, "ticket.pdf", "First aid")
    staff_scope = office_scope(world["staff"], ORG)
    assert search(staff_scope, Filters(q="Sam"), today=TODAY).total == 0
    assert doc.id in [r.document.id for r in search(office_scope(world["owner"], ORG), Filters(q="Sam"),
                                                    today=TODAY).rows]


# ------------------------------------------------------------------ I3


def _connected_without_text(world, data, filename="big.pdf"):
    """A filed document whose text was not extracted at filing (as for a connected record or a large file)."""
    doc = file_pdf(world["owner"], CONTEXT_COMPANY, None, filename, "x")
    version = doc.current_version
    DocumentText.query.filter_by(version_id=version.id).delete()
    db.session.commit()
    return doc, version


def test_opening_a_large_document_does_not_extract_it_in_the_request(app, world, monkeypatch):
    doc, version = _connected_without_text(world, None)
    monkeypatch.setattr(extract, "MAX_SYNC_BYTES", 10)  # this small file now counts as large
    called = []
    monkeypatch.setattr(extract, "extract_text", lambda *a, **k: called.append(1))
    assert ingest.ensure_extracted(doc, Actor.of(world["owner"])) is False
    assert called == []
    assert DocumentText.query.filter_by(version_id=version.id).first() is None
    owner = signed_in(app, OWNER)
    page = owner.get(f"/documents/{doc.public_id}")
    assert page.status_code == 200 and b"not indexed yet" in page.data


def test_a_concurrent_first_open_that_already_stored_the_text_does_not_fail(app, world, monkeypatch):
    doc, version = _connected_without_text(world, None)
    real_flush = db.session.flush
    state = {"raised": False}

    def store_twice(document, version_, extraction, actor, **kw):
        # Another request stored this version's text between our check and our insert.
        if not state["raised"]:
            state["raised"] = True
            raise IntegrityError("INSERT INTO document_text", {}, Exception("UNIQUE constraint failed"))
        return None

    monkeypatch.setattr(ingest, "store_text", store_twice)
    assert ingest.ensure_extracted(doc, Actor.of(world["owner"])) is False
    assert state["raised"]
    db.session.flush = real_flush
    # The session is usable afterwards and the page opens.
    owner = signed_in(app, OWNER)
    assert owner.get(f"/documents/{doc.public_id}").status_code == 200


# ------------------------------------------------------------------ M2


def test_a_type_not_offered_for_the_context_is_refused(app, world):
    with pytest.raises(ingest.DocumentError, match="can't be filed"):
        file_pdf(world["owner"], CONTEXT_PROJECT, world["project"].id, "x.pdf", "x", type_code="CERTIFICATION")
    assert Document.query.count() == 0


def test_a_people_type_cannot_be_filed_into_the_company_library(app, world):
    from app.services.documents.types import REGISTRY, types_for_context

    offered = {t.code for t in types_for_context(CONTEXT_COMPANY)}
    people_only = [t.code for t in REGISTRY if t.sensitivity == SENSITIVITY_PEOPLE and t.code not in offered]
    assert people_only
    with pytest.raises(ingest.DocumentError):
        file_pdf(world["owner"], CONTEXT_COMPANY, None, "x.pdf", "x", type_code=people_only[0])


def test_changing_the_type_recomputes_sensitivity(app, world):
    from app.services.documents.types import REGISTRY

    financial = next(t.code for t in REGISTRY if t.sensitivity == SENSITIVITY_FINANCIAL)
    doc = file_pdf(world["owner"], CONTEXT_PROJECT, world["project"].id, "x.pdf", "x")
    assert doc.sensitivity == SENSITIVITY_STANDARD
    ingest.correct_field(doc, Actor.of(world["owner"]), "document_type", financial, "It is an invoice")
    assert doc.sensitivity == SENSITIVITY_FINANCIAL
    event = DocumentEvent.query.filter_by(document_id=doc.id, field_name="sensitivity").one()
    assert (event.previous_value, event.new_value) == (SENSITIVITY_STANDARD, SENSITIVITY_FINANCIAL)
    ingest.correct_field(doc, Actor.of(world["owner"]), "document_type", "OTHER", "Not an invoice after all")
    assert doc.sensitivity == SENSITIVITY_STANDARD


def test_changing_the_type_never_lowers_a_person_document_below_people(app, world):
    from app.services.documents.types import REGISTRY

    financial = next(t.code for t in REGISTRY if t.sensitivity == SENSITIVITY_FINANCIAL)
    person = _membership(world["staff"])
    doc = file_pdf(world["owner"], CONTEXT_PERSON, person.id, "ticket.pdf", "First aid")
    assert doc.sensitivity == SENSITIVITY_PEOPLE
    ingest.correct_field(doc, Actor.of(world["owner"]), "document_type", "OTHER", "Unclear")
    assert doc.sensitivity == SENSITIVITY_PEOPLE
    ingest.correct_field(doc, Actor.of(world["owner"]), "document_type", financial, "Expense claim")
    assert doc.sensitivity == SENSITIVITY_PEOPLE


def test_an_administrator_choice_of_sensitivity_is_kept_when_the_type_does_not_change_it(app, world):
    """Only the type's own default moves; a type change that keeps the default leaves an explicit choice alone."""
    doc = file_pdf(world["owner"], CONTEXT_PROJECT, world["project"].id, "x.pdf", "x")
    ingest.correct_field(doc, Actor.of(world["owner"]), "sensitivity", SENSITIVITY_FINANCIAL, "Pricing inside",
                         allow_sensitivity=True)
    ingest.correct_field(doc, Actor.of(world["owner"]), "document_type", "OTHER", "Retype")
    assert doc.sensitivity == SENSITIVITY_FINANCIAL


# ------------------------------------------------------------------ M3


def test_a_long_subcontractor_name_gets_a_code_that_fits_with_its_suffix(app, world):
    owner = signed_in(app, OWNER)
    name = "Northern Ontario Precision Concrete Forming and Finishing Ltd"
    for _ in range(3):
        assert owner.post("/subcontractors", data={"legal_name": name}).status_code == 302
    codes = sorted(s.code for s in Subcontractor.query.filter_by(organization_id=ORG, legal_name=name))
    assert len(codes) == 3 and len(set(codes)) == 3
    assert all(len(c) <= 30 for c in codes), codes
    assert any(c.endswith("-2") for c in codes) and any(c.endswith("-3") for c in codes)


def test_reindex_extracts_the_text_a_page_open_left_for_it(app, world, monkeypatch):
    doc, version = _connected_without_text(world, None)
    monkeypatch.setattr(extract, "MAX_SYNC_BYTES", 10)
    assert ingest.ensure_extracted(doc, Actor.of(world["owner"])) is False
    result = app.test_cli_runner().invoke(args=["documents", "reindex"])
    assert result.exit_code == 0, result.output
    assert "TEXT_EXTRACTED=1" in result.output
    assert DocumentText.query.filter_by(version_id=version.id).count() == 1
