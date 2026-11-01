"""Document search: FTS5 and LIKE fallback agree, permissions are applied in SQL, FTS syntax cannot be injected,
paging is stable, and every filter works. Synthetic data only."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import db
from app.models.documents import (
    CONTEXT_COMPANY,
    CONTEXT_EQUIPMENT,
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    CONTEXT_SUBCONTRACTOR,
    CONTEXT_SUPPLIER,
    DATE_EXPIRES,
    DocumentDate,
)
from app.models.user import UserMembership
from app.services.documents import fts, ingest
from app.services.documents.access import field_scope, office_scope
from app.services.documents.ingest import Actor
from app.services.documents.search import Filters, fts_match_expression, search
from app.services.equipment import create_equipment
from tests.documents_support import (  # noqa: F401  (fixtures)
    ORG,
    OTHER_ORG,
    TODAY,
    app,
    file_pdf,
    like_app,
    make_world,
)


def _fixture_set(world):
    staff = world["staff"]
    docs = {
        "wsib": file_pdf(staff, CONTEXT_SUBCONTRACTOR, world["sub"].id, "WSIB clearance Acme.pdf",
                         "Clearance certificate for framing crews"),
        "coi": file_pdf(staff, CONTEXT_SUPPLIER, world["supplier"].id, "certificate of insurance.pdf",
                        "General liability coverage for lumber deliveries"),
        "plan": file_pdf(staff, CONTEXT_PROJECT, world["project"].id, "deck framing plan.pdf",
                         "Joist layout and ledger detail"),
        "spec": file_pdf(staff, CONTEXT_PROJECT, world["second"].id, "garage spec.pdf", "Concrete slab thickness"),
        "policy": file_pdf(staff, CONTEXT_COMPANY, None, "safety policy.pdf", "Fall protection above three metres"),
        "invoice": file_pdf(staff, CONTEXT_PROJECT, world["project"].id, "invoice 1042.pdf", "Framing labour invoice"),
    }
    membership = UserMembership.query.filter_by(user_id=staff.id, organization_id=ORG).one()
    docs["ticket"] = file_pdf(world["owner"], CONTEXT_PERSON, membership.id, "working at heights ticket.pdf",
                              "Fall protection training for framing")
    equipment = create_equipment(ORG, staff, {"name": "Kubota KX040", "category": "HEAVY_EQUIPMENT"})
    docs["manual"] = file_pdf(staff, CONTEXT_EQUIPMENT, equipment.id, "operator manual.pdf", "Hydraulic framing grease")
    # Another organization with the same words: never visible.
    docs["other"] = file_pdf(world["other"], CONTEXT_PROJECT, world["other_project"].id, "deck framing plan.pdf",
                             "Joist layout framing", org=OTHER_ORG)
    return docs


QUERIES = ["framing", "fram", "insurance", "joist ledger", "acme", "lakeview", "kubota", "fall protection",
           "nothingmatches", "valley", "garage"]


def _ids(page):
    return sorted(r.document.public_id for r in page.rows)


def _run_all(app_instance):
    world = make_world(crew=False)
    docs = _fixture_set(world)
    owner = office_scope(world["owner"], ORG)
    staff = office_scope(world["staff"], ORG)
    out = {}
    for q in QUERIES:
        out[("owner", q)] = _ids(search(owner, Filters(q=q), today=TODAY))
        out[("staff", q)] = _ids(search(staff, Filters(q=q), today=TODAY))
    names = {d.public_id: k for k, d in docs.items()}
    return {k: sorted(names[i] for i in v) for k, v in out.items()}


def test_fts_is_used_when_available(app):
    assert fts.fts_enabled()
    world = make_world(crew=False)
    _fixture_set(world)
    page = search(office_scope(world["staff"], ORG), Filters(q="joist"), today=TODAY)
    assert page.mode == "fts" and page.total == 1
    assert "<mark>" in str(page.rows[0].snippet)


def test_like_fallback_used_without_fts(like_app):
    assert not fts.fts_enabled()
    world = make_world(crew=False)
    _fixture_set(world)
    page = search(office_scope(world["staff"], ORG), Filters(q="joist"), today=TODAY)
    assert page.mode == "like" and page.total == 1


def test_fts_and_like_return_the_same_documents():
    from tests.documents_support import make_app
    from app.services.organizations import ensure_default_organization

    results = []
    for config in ({}, {"DOCUMENTS_SEARCH_MODE": "like"}):
        application = make_app(**config)
        with application.app_context():
            db.create_all()
            ensure_default_organization()
            results.append(_run_all(application))
            db.session.remove()
            db.drop_all()
    fts_results, like_results = results
    assert fts_results == like_results
    assert fts_results[("staff", "framing")] == ["invoice", "manual", "plan", "wsib"]
    assert "ticket" in fts_results[("owner", "fall protection")]
    assert "ticket" not in fts_results[("staff", "fall protection")]  # PEOPLE: people administrators only
    assert fts_results[("staff", "lakeview")] == ["invoice", "plan"]  # project name (a context label)
    assert fts_results[("staff", "valley")] == ["coi"]  # supplier name
    assert fts_results[("staff", "nothingmatches")] == []
    assert "other" not in sum(fts_results.values(), [])  # other organization never appears


def test_financial_documents_follow_office_financial_access(app):
    world = make_world(crew=False)
    docs = _fixture_set(world)
    scope = office_scope(world["staff"], ORG)
    assert "FINANCIAL" in scope.sensitivities  # every active office member (has_office_financial_access)
    assert docs["invoice"].public_id in _ids(search(scope, Filters(q="invoice"), today=TODAY))


@pytest.mark.parametrize("raw", ['"', 'framing NEAR joist', '-framing', 'title:framing', 'fram*', '"unbalanced',
                                 "a OR b AND NOT c", "(framing", "^framing", "framing'; DROP TABLE documents; --"])
def test_fts_syntax_is_harmless(app, raw):
    world = make_world(crew=False)
    _fixture_set(world)
    page = search(office_scope(world["staff"], ORG), Filters(q=raw), today=TODAY)
    assert page.total >= 0
    assert all(c not in fts_match_expression(raw).replace('"', "").replace("*", "") for c in "():^-")


def test_counts_exclude_hidden_documents_and_paging_is_stable(app):
    world = make_world(crew=False)
    for i in range(7):
        file_pdf(world["staff"], CONTEXT_COMPANY, None, f"form {i:02d}.pdf", "framing form")
    membership = UserMembership.query.filter_by(user_id=world["staff"].id, organization_id=ORG).one()
    file_pdf(world["owner"], CONTEXT_PERSON, membership.id, "framing ticket.pdf", "framing form")
    staff = office_scope(world["staff"], ORG)
    first = search(staff, Filters(q="framing"), page=1, page_size=3, today=TODAY)
    assert first.total == 7 and first.pages == 3
    seen = []
    for page in (1, 2, 3):
        seen += _ids(search(staff, Filters(q="framing"), page=page, page_size=3, today=TODAY))
    assert len(seen) == 7 and len(set(seen)) == 7
    assert search(office_scope(world["owner"], ORG), Filters(q="framing"), today=TODAY).total == 8


def test_filters_type_context_status_dates_and_uploaded(app):
    world = make_world(crew=False)
    docs = _fixture_set(world)
    actor = Actor.of(world["staff"])
    scope = office_scope(world["staff"], ORG)
    ingest.enter_date(docs["wsib"], actor, DATE_EXPIRES, TODAY + timedelta(days=10))
    ingest.enter_date(docs["coi"], actor, DATE_EXPIRES, TODAY + timedelta(days=200))
    ingest.archive(docs["policy"], actor, "Replaced")

    def names(**kw):
        page = search(scope, Filters(**kw), today=TODAY)
        lookup = {d.public_id: k for k, d in docs.items()}
        return sorted(lookup[r.document.public_id] for r in page.rows)

    assert names(type_code="WSIB_CLEARANCE") == ["wsib"]
    assert names(family="Compliance") == ["coi", "wsib"]
    assert names(context_kind=CONTEXT_PROJECT, context_id=world["project"].id) == ["invoice", "plan"]
    assert names(context_kind=CONTEXT_SUBCONTRACTOR) == ["wsib"]
    assert names(context_kind=CONTEXT_SUPPLIER) == ["coi"]
    assert names(context_kind=CONTEXT_EQUIPMENT) == ["manual"]
    assert names(status="ARCHIVED") == ["policy"]
    assert "policy" not in names()
    assert names(expiring_within=30) == ["wsib"]
    assert names(expiring_within=365) == ["coi", "wsib"]
    from app.services.local_time import local_date

    filed_on = local_date(docs["wsib"].created_at)  # stored in UTC; the filter is on the office's calendar day
    assert names(uploaded_from=filed_on + timedelta(days=1)) == []
    assert len(names(uploaded_from=filed_on, uploaded_to=filed_on)) == 6  # active, visible to staff
    assert "wsib" not in names(dates="none")
    proposed = file_pdf(world["staff"], CONTEXT_COMPANY, None, "licence.pdf", "Licence expires 2027-05-01")
    assert [r.document.id for r in search(scope, Filters(dates="proposed"), today=TODAY).rows] == [proposed.id]


def test_uploaded_filters_use_the_office_calendar_day(app):
    """An upload at 9:30 pm Toronto on 31 Oct is stored as 01:30 UTC on 1 Nov; the "uploaded" filter is about
    the office's day, so it is a 31 Oct upload (My Week date fix follow-up, 1 Nov 2026)."""
    from datetime import datetime

    world = make_world(crew=False)
    docs = _fixture_set(world)
    scope = office_scope(world["staff"], ORG)
    docs["wsib"].created_at = datetime(2026, 11, 1, 1, 30)  # naive UTC
    for key in docs:
        if key != "wsib":
            docs[key].created_at = datetime(2026, 10, 20, 15, 0)
    db.session.commit()

    def names(**kw):
        page = search(scope, Filters(**kw), today=TODAY)
        lookup = {d.public_id: k for k, d in docs.items()}
        return sorted(lookup[r.document.public_id] for r in page.rows)

    assert names(uploaded_from=date(2026, 10, 31), uploaded_to=date(2026, 10, 31)) == ["wsib"]
    assert names(uploaded_from=date(2026, 11, 1)) == []
    assert "wsib" not in names(uploaded_to=date(2026, 10, 30))


def test_expired_filter_and_new_version_resets_dates(app):
    world = make_world(crew=False)
    actor = Actor.of(world["staff"])
    scope = office_scope(world["staff"], ORG)
    doc = file_pdf(world["staff"], CONTEXT_COMPANY, None, "insurance.pdf", "Insurance")
    ingest.enter_date(doc, actor, DATE_EXPIRES, TODAY - timedelta(days=3))
    assert search(scope, Filters(dates="expired"), today=TODAY).total == 1
    from app.services.documents.ingest import prepare_upload
    from tests.documents_support import text_pdf

    ingest.add_version(doc, actor, prepare_upload("insurance-2027.pdf", text_pdf("Insurance renewed")))
    assert search(scope, Filters(dates="expired"), today=TODAY).total == 0  # the old date belongs to the old version
    assert DocumentDate.query.filter_by(document_id=doc.id).count() == 1  # kept, nothing rewritten


def test_field_scope_only_their_jobs_and_crew_types(app):
    world = make_world(crew=True)
    staff = world["staff"]
    plan = file_pdf(staff, CONTEXT_PROJECT, world["project"].id, "deck plan.pdf", "framing")
    file_pdf(staff, CONTEXT_PROJECT, world["project"].id, "change order 2.pdf", "framing")  # not a crew type
    file_pdf(staff, CONTEXT_PROJECT, world["project"].id, "invoice 7.pdf", "framing")
    file_pdf(staff, CONTEXT_PROJECT, world["second"].id, "garage plan.pdf", "framing")  # not their job
    file_pdf(staff, CONTEXT_COMPANY, None, "safety policy.pdf", "framing")  # company, not a job document
    scope = field_scope(world["crew"], ORG)
    assert world["project"].id in scope.project_ids and world["second"].id not in scope.project_ids
    page = search(scope, Filters(q="framing"), today=TODAY)
    assert [r.document.id for r in page.rows] == [plan.id] and page.total == 1


def test_filters_from_the_address_bar():
    filters = Filters.from_args({"context": "project", "context_id": "50000", "expiring": "30", "status": "bogus",
                                 "from": "2026-13-40", "q": "x" * 500, "review": "1"})
    assert filters.context_kind == CONTEXT_PROJECT and filters.context_id == 50000  # any record id
    assert filters.expiring_within == 30 and filters.status == "ACTIVE" and filters.uploaded_from is None
    assert len(filters.q) == 200 and filters.review is True
    assert Filters.from_args({"context": "MATTER", "expiring": "99999"}).context_kind == ""
    assert Filters.from_args({"expiring": "99999"}).expiring_within is None
