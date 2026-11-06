"""Independent review of f98ec33d (3 Nov 2026): one regression test per finding. Synthetic data only.

B1 the generic CaliSIGN office routes act on an INTERNAL_APPROVAL only for someone who may freeze and send its
   document type, checked before anything changes;
B2 Internal Project Financial Summary copies in Documents need project economics (and employee cost when they show
   the crew's loaded rates), never plain FINANCIAL office access;
S1 a filed copy is created at its final sensitivity, before it is indexed or committed;
S2 a version's recorded pricing method is always honoured when the company default changes;
M1 a sent-to-client REV records employee detail by the same rule filing uses;
M2 the migration's description counts its new columns correctly.
"""

from __future__ import annotations

import importlib.util
import os
import re
from decimal import Decimal as D

import pytest
from sqlalchemy import text

from app import db
from app.models import Proposal
from app.models.documents import Document
from app.models.internal_summary import InternalSummaryRevision
from app.services import internal_approval as IA
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.test_customer_estimate_approval import BEN, _freeze as _freeze_estimate, _rev10_job, _send as _send_estimate
from tests.test_internal_approval_calisign import APPROVER, _freeze, _job, _link, _mail, env  # noqa: F401

SIGNING_TABLES = ("signing_requests", "signing_participants", "signing_events", "signing_executed_artifacts",
                  "signing_frozen_artifacts", "transactional_messages", "documents")


def _state():
    return {t: db.session.execute(text(f"SELECT * FROM {t} ORDER BY id")).fetchall() for t in SIGNING_TABLES}


def _office_actions(request_id):
    base = f"/signing-requests/{request_id}"
    return [("post", base + "/invite"), ("post", base + "/resend"), ("post", base + "/void"),
            ("post", base + "/countersign"), ("post", base + "/approve"), ("post", base + "/execute"),
            ("get", base + "/executed")]


def _refused_everywhere(driver, request_id, allowed=(403,)):
    before = _state()
    for method, path in _office_actions(request_id):
        response = getattr(driver.http, method)(path, data={"void_reason": "Synthetic"} if method == "post" else None)
        assert response.status_code in allowed, (path, response.status_code)
        db.session.expire_all()
        assert _state() == before, path  # nothing changed, not even an event or an email


# ================================================================================================ B1
def test_b1_generic_signing_routes_refuse_internal_approvals_to_those_without_the_document_permission(env, monkeypatch):
    app, c, _users = env
    project, _guided = _job(c)
    rev = _freeze(c, project)  # shows the crew's loaded rates
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    request = IA.requests_for(rev)[0]
    assert request.status == "SENT"
    # An ordinary office member: refused on every generic route, before anything changes.
    _refused_everywhere(c["staff"], request.id)
    # Project economics without employee cost: still refused for a REV that shows the crew's loaded rates.
    from app.services import financial_access

    monkeypatch.setattr(financial_access, "can_view_project_economics", lambda user, org: True)
    _refused_everywhere(c["staff"], request.id)
    monkeypatch.undo()
    # Signed: the executed copy cannot be downloaded or voided by them either.
    c["public"].post(_link(_mail(app)[0]) + "/sign", data={"consent_accepted": "yes",
                                                          "confirmed_signer_name": APPROVER[0]}, status=200)
    db.session.expire_all()
    assert db.session.get(type(request), request.id).status == "EXECUTED"
    _refused_everywhere(c["staff"], request.id)
    # The person who may (the owner) still can, and lands on the internal approval, not a 404.
    response = c["owner"].http.get(f"/signing-requests/{request.id}/executed")
    assert response.status_code == 200 and response.mimetype == "application/pdf"
    response = c["owner"].http.post(f"/signing-requests/{request.id}/void", data={"void_reason": "Synthetic"})
    assert response.status_code == 302 and "/guided/pricing" in response.headers["Location"]


def test_b1_the_customer_estimate_follows_the_estimate_sending_rule_on_the_generic_routes(env):
    app, c, _users = env
    _project, _guided, proposal = _rev10_job(c, "Synthetic B1 estimate job")
    rev = _freeze_estimate(c, proposal)
    _send_estimate(c, proposal, rev)
    request = IA.requests_for(rev)[0]
    # Field crew (no estimate access): refused everywhere, nothing changes.
    _refused_everywhere(c["crew"], request.id, allowed=(302, 403))
    # An ordinary office member may send the estimate to the client today, so they may manage its approval too.
    response = c["staff"].http.post(f"/signing-requests/{request.id}/resend")
    assert response.status_code == 302 and f"/proposals/{proposal.id}" in response.headers["Location"]
    from app.models.signing import SigningEvent

    assert SigningEvent.query.filter_by(signing_request_id=request.id, event_type="RESENT").count() == 1


def test_b1_other_signing_families_are_unchanged(env):
    _app, c, _users = env
    # A request that does not exist (any family) behaves as before: the route's own refusal.
    response = c["staff"].http.post("/signing-requests/999999/void", data={"void_reason": "Synthetic"})
    assert response.status_code == 404


# ================================================================================================ B2
def _economics_documents():
    return Document.query.filter_by(document_type="INTERNAL_FINANCIAL_SUMMARY").all()


def _office_sees(driver, project_id, documents):
    seen = set()
    pages = [driver.http.get("/documents").get_data(as_text=True),
             driver.http.get("/documents?q=financial+summary").get_data(as_text=True),
             driver.http.get("/documents?q=Internal").get_data(as_text=True),
             driver.http.get(f"/projects/{project_id}/documents").get_data(as_text=True)]
    for doc in documents:
        if any(doc.public_id in page for page in pages):
            seen.add(doc.public_id)
        if driver.http.get(f"/documents/{doc.public_id}").status_code == 200:
            seen.add(doc.public_id)
        if driver.http.get(f"/documents/{doc.public_id}/file?download=1").status_code == 200:
            seen.add(doc.public_id)
        if driver.http.get(f"/documents/{doc.public_id}/file").status_code == 200:
            seen.add(doc.public_id)
    return seen


def test_b2_financial_summary_copies_need_project_economics_and_wage_copies_employee_cost(env, monkeypatch):
    app, c, users = env
    from app.services import financial_access
    from tests.test_guided_tasks import _template
    from tests.test_guided_tasks import _priced_job
    from tests.test_internal_financial_summary import _approve_form

    _template()
    # An approved summary without a crew, then that price sent to the client (a sent REV).
    project, _guided = _priced_job(c["owner"], "Synthetic no-crew B2 job")
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    proposal = Proposal.query.order_by(Proposal.id.desc()).first()
    c["owner"].post(f"/proposals/{proposal.id}/send-to-client",
                    data={"client_name": "Casey Synthetic", "client_email": "casey@example.invalid"})
    # A signed crew-total REV (frozen by someone with economics but not employee cost) and a signed wage REV.
    other, _g = _job(c)
    monkeypatch.setattr(financial_access, "can_view_project_economics",
                        lambda user, org: getattr(user, "id", None) in (users["owner"].id, users["staff"].id))
    c["staff"].post(f"/projects/{other.id}/guided/summary-revisions")
    db.session.expire_all()
    crew_total = InternalSummaryRevision.query.order_by(InternalSummaryRevision.id.desc()).first()
    assert not crew_total.employee_detail
    c["staff"].post(f"/projects/{other.id}/guided/summary-revisions/{crew_total.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    c["public"].post(_link(_mail(app)[-1]) + "/sign", data={"consent_accepted": "yes",
                                                           "confirmed_signer_name": APPROVER[0]}, status=200)
    monkeypatch.undo()
    db.session.expire_all()
    documents = _economics_documents()
    by_level = {}
    for doc in documents:
        by_level.setdefault(doc.sensitivity, []).append(doc)
    assert set(by_level) == {"ECONOMICS"} and len(documents) == 3, [(d.title, d.sensitivity) for d in documents]
    wage = _freeze(c, other)
    c["owner"].post(f"/projects/{other.id}/guided/summary-revisions/{wage.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": "second@example.invalid"})
    c["public"].post(_link(_mail(app)[-1]) + "/sign", data={"consent_accepted": "yes",
                                                           "confirmed_signer_name": APPROVER[0]}, status=200)
    db.session.expire_all()
    documents = _economics_documents()
    wage_docs = [d for d in documents if d.sensitivity == "EMPLOYEE_COST"]
    assert len(wage_docs) == 1 and len(documents) == 4
    # An ordinary office member (FINANCIAL office access) sees none of them: list, search, preview or download.
    from app.services.access_domains import has_office_financial_access

    assert has_office_financial_access(users["staff"], ORG)
    for pid in (project.id, other.id):
        assert _office_sees(c["staff"], pid, documents) == set()
    # A future project-performance grant (economics without wages) reaches the economics copies only.
    monkeypatch.setattr(financial_access, "can_view_project_economics",
                        lambda user, org: getattr(user, "id", None) in (users["owner"].id, users["staff"].id))
    seen = _office_sees(c["staff"], other.id, documents) | _office_sees(c["staff"], project.id, documents)
    assert seen == {d.public_id for d in documents if d.sensitivity == "ECONOMICS"}
    monkeypatch.undo()
    # The owner (economics and employee cost) sees all four.
    seen = _office_sees(c["owner"], other.id, documents) | _office_sees(c["owner"], project.id, documents)
    assert seen == {d.public_id for d in documents}


def test_b2_the_customer_estimate_approval_copy_is_at_normal_estimate_access(env):
    app, c, _users = env
    project, _guided, proposal = _rev10_job(c, "Synthetic B2 estimate job")
    rev = _freeze_estimate(c, proposal)
    _send_estimate(c, proposal, rev)
    c["public"].post(_link(_mail(app)[0]) + "/sign", data={"consent_accepted": "yes", "confirmed_signer_name": BEN[0]},
                     status=200)
    db.session.expire_all()
    estimates = Document.query.filter_by(document_type="ESTIMATE").all()
    assert len(estimates) == 2 and {d.sensitivity for d in estimates} == {"STANDARD"}
    assert _office_sees(c["staff"], project.id, estimates) == {d.public_id for d in estimates}


# ================================================================================================ S1
def test_s1_a_wage_copy_is_never_readable_at_a_weaker_level_even_if_a_later_step_fails(env, monkeypatch):
    _app, c, _users = env
    from app.services.documents import fts, ingest
    from tests.test_guided_tasks import _template
    from tests.test_internal_financial_summary import _approve_form

    _template()
    project, _guided = _job(c)
    indexed = []
    original_index = fts.index_document
    monkeypatch.setattr(fts, "index_document", lambda document: (indexed.append(
        (document.document_type, document.sensitivity)), original_index(document))[1])
    commits = []
    original_commit = db.session.commit

    def commit():
        for doc in db.session.new | db.session.dirty:
            if isinstance(doc, Document):
                commits.append((doc.document_type, doc.sensitivity))
        return original_commit()

    monkeypatch.setattr(db.session, "commit", commit)

    def broken_post_step(*args, **kwargs):  # the old "raise it to PEOPLE afterwards" step failing
        raise RuntimeError("synthetic failure after filing")

    monkeypatch.setattr(ingest, "correct_field", broken_post_step)
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    monkeypatch.undo()
    db.session.expire_all()
    doc = Document.query.filter_by(document_type="INTERNAL_FINANCIAL_SUMMARY").one()
    assert doc.sensitivity == "EMPLOYEE_COST"
    summary_levels = {s for t, s in indexed + commits if t == "INTERNAL_FINANCIAL_SUMMARY"}
    assert summary_levels == {"EMPLOYEE_COST"}, summary_levels  # indexed and committed at the final level only
    from app.models.documents import DocumentEvent

    created = DocumentEvent.query.filter_by(document_id=doc.id, event_type="CREATED").one()
    assert created.detail_json["sensitivity"] == "EMPLOYEE_COST"


# ================================================================================================ S2
METHOD_POLICIES = {
    "TRUE_GROSS_MARGIN": dict(target_gross_margin=D("0.20")),
    "COST_PLUS_MARKUP": dict(markup_rate=D("0.18")),
    "COST_PLUS_MARKUP_STACK": dict(stack_overhead_percent=D("10"), stack_profit_percent=D("8")),
    "LABOUR_AT_RATE_MATERIAL_MARGIN": dict(target_gross_margin=D("0.15")),
}


def _default_policy(method, code):
    from app.services.pricing_engine import approve_pricing_policy, create_pricing_policy, set_default_pricing_policy
    from tests.test_pricing_labour_material_margin import JOEL

    policy = create_pricing_policy(policy_code=code, method=method, actor=JOEL, tax_jurisdiction="CA-ON",
                                   tax_percent=D("13"), contingency_visibility="UNSPECIFIED",
                                   **METHOD_POLICIES[method])
    approve_pricing_policy(policy.id, actor=JOEL, organization_id=ORG)
    set_default_pricing_policy(policy.id, actor=JOEL, organization_id=ORG)
    db.session.commit()
    return policy


@pytest.mark.parametrize("method", sorted(METHOD_POLICIES))
def test_s2_a_company_method_change_never_changes_a_recorded_versions_method_or_figures(app, method):
    from app.services.pricing_engine import apply_resolved_pricing_to_version
    from tests.proposal_issue_support import approve_for_issue
    from tests.test_pricing_labour_material_margin import JOEL, _estimate

    _default_policy(method, f"S2-{method}")
    _estimate_row, version = _estimate(f"EST-S2-{method[:12]}")
    assert version.pricing_method == method
    approve_for_issue(version, actor=JOEL)
    before = (version.pricing_snapshot.method, version.pricing_snapshot.pre_tax_selling_price,
              version.pricing_snapshot.customer_total, version.subtotal, version.total)
    for other in sorted(METHOD_POLICIES):
        if other == method:
            continue
        _default_policy(other, f"S2-{method}-THEN-{other}")
        apply_resolved_pricing_to_version(version, actor=JOEL, organization_id=ORG)
        db.session.commit()
        db.session.expire_all()
        version = db.session.get(type(version), version.id)
        after = (version.pricing_snapshot.method, version.pricing_snapshot.pre_tax_selling_price,
                 version.pricing_snapshot.customer_total, version.subtotal, version.total)
        assert version.pricing_method == method and after == before, (method, other, before, after)


from tests.test_pricing_labour_material_margin import app  # noqa: E402,F401 - the S2 fixture


# ================================================================================================ M1
def test_m1_a_sent_rev_without_a_crew_records_no_employee_detail(env):
    _app, c, _users = env
    from tests.test_guided_tasks import _template
    from tests.test_internal_financial_summary import _approve_form, _job_with_labour

    _template()
    project, _guided = _job_with_labour(c["owner"])  # no crew assigned
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    proposal = Proposal.query.order_by(Proposal.id.desc()).first()
    c["owner"].post(f"/proposals/{proposal.id}/send-to-client",
                    data={"client_name": "Casey Synthetic", "client_email": "casey@example.invalid"})
    db.session.expire_all()
    sent = InternalSummaryRevision.query.filter_by(origin="SENT_TO_CLIENT").one()
    assert sent.employee_detail is False
    doc = Document.query.filter_by(document_type="INTERNAL_FINANCIAL_SUMMARY").all()
    assert {d.sensitivity for d in doc} == {"ECONOMICS"}  # the same rule decided the filing


# ================================================================================================ M2
def test_m2_the_migration_description_counts_its_new_columns():
    path = os.path.join(os.path.dirname(__file__), "..", "migrations", "versions",
                        "u8b9c0d1e2f3_cost_profiles_and_pricing_method.py")
    spec = importlib.util.spec_from_file_location("u8b9_for_count", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    words = {"eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
    match = re.search(r"(\w+) new nullable columns", module.__doc__)
    assert match and words[match.group(1)] == len(module.NEW_COLUMNS)
    match = re.search(r"(\w+) new tables", module.__doc__)
    assert match and {"four": 4, "five": 5}[match.group(1)] == len(module.NEW_TABLES)
