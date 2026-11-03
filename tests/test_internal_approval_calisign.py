"""CaliSIGN internal approval (Joel, 3 Nov 2026): the sixth signable document class, INTERNAL_APPROVAL.

Lifecycle: the working Internal Project Financial Summary is frozen as REVn; sent for internal approval; the approver
gets the normal CaliSIGN one-time email link, opens it with no Calibrayt session, reviews the exact frozen PDF,
consents and signs; the request completes (approver only, the Financial Summary's rule); the signed copy is filed in
the project's Documents with the signing evidence. A signed REV never changes: a later change is the next REV, separate
and unsigned. Negative: the link reaches nothing but its own frozen document; a used, expired or guessed token
refuses; rate limited as the other classes. Synthetic data only; mail is captured locally.
"""

from __future__ import annotations

import glob
import hashlib
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal as D
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import create_app, db
from app.models.documents import Document, DocumentLink
from app.models.internal_summary import InternalSummaryRevision
from app.models.signing import (
    DOCUMENT_FAMILY_INTERNAL_APPROVAL,
    ROLE_APPROVER,
    STATUS_EXECUTED,
    STATUS_SIGNED,
    SigningEvent,
    SigningRequest,
)
from app.services import guided_estimating as G
from app.services import internal_approval as IA
from app.services import package_scenario as PS
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.guided_support import Driver, seed_company
from tests.test_internal_financial_summary import (
    CREW,
    OWNER,
    STAFF,
    WORKER_A,
    WORKER_B,
    _add_employee,
    _brayman_pricing,
    _job_with_labour,
    _membership,
)

APPROVER = ("Approver Synthetic", "approver@example.invalid")


@pytest.fixture()
def env(tmp_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k",
                              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": str(tmp_path / "mail")})
    context = application.app_context()
    context.push()
    db.create_all()
    ensure_default_organization()
    seed_company()
    _brayman_pricing()
    owner = ensure_office_user(email=OWNER[0], password=OWNER[1], display_name=OWNER[2])
    set_instance_owner(ORG, _membership(owner).id, owner.id)
    staff = ensure_office_user(email=STAFF[0], password=STAFF[1], display_name=STAFF[2])
    crew = ensure_office_user(email=CREW[0], password=CREW[1], display_name=CREW[2])
    from app.services.access_domains import set_field_only

    set_field_only(_membership(crew), True, owner)
    db.session.commit()
    clients = {}
    for key, (email, password, _name) in (("owner", OWNER), ("staff", STAFF), ("crew", CREW)):
        driver = Driver(application.test_client())
        login_office_user(driver.http, email=email, password=password)
        clients[key] = driver
    clients["public"] = Driver(application.test_client())  # the approver's laptop: no Calibrayt account
    yield application, clients, {"owner": owner, "staff": staff}
    db.session.remove()
    db.drop_all()
    context.pop()


def _mail(app):
    root = app.config["MAIL_CAPTURE_ROOT"]
    return [open(p, encoding="utf-8").read() for p in sorted(glob.glob(os.path.join(root, "*-SIGNING_INVITATION.txt")))]


def _link(text) -> str:
    match = re.search(r"Review and Sign Document: (\S+)", text)
    assert match, text
    return "/" + match.group(1).split("/", 3)[-1]


def _job(c):
    project, guided = _job_with_labour(c["owner"])
    a = _add_employee(c["owner"], WORKER_A)
    b = _add_employee(c["owner"], WORKER_B)
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id), str(b.id)]})
    return project, guided


def _freeze(c, project):
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions")
    flashes = c["owner"].flashes()
    assert any("frozen" in m for m in flashes), flashes
    db.session.expire_all()
    return InternalSummaryRevision.query.order_by(InternalSummaryRevision.id.desc()).first()


def _change_working_summary(c, project, guided, n):
    """A real change to the working summary: the siding package's client budget."""
    stage = G.get_guided(ORG, project.id).top_stages[0]
    version = G.current_version(G.get_guided(ORG, project.id))
    PS.set_budget(version, PS.package_key(stage), str(D("3000") + n), actor=OWNER[2], reason="Synthetic change")


def _pdf_text(data: bytes) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(BytesIO(data)).pages)


def test_the_full_internal_approval_lifecycle_rev10_signed_rev11_separate(env):
    app, c, users = env
    project, guided = _job(c)
    # REV1 ... REV9 from earlier working states; REV10 is the one approved.
    for n in range(9):
        _freeze(c, project)
        _change_working_summary(c, project, guided, n)
    rev10 = _freeze(c, project)
    assert rev10.label == "REV10" and rev10.origin == "FROZEN" and rev10.employee_detail
    artifact = IA.frozen_artifact(rev10)
    from app.services.signing import retrieve_frozen_artifact_bytes

    frozen_bytes = retrieve_frozen_artifact_bytes(artifact)
    assert hashlib.sha256(frozen_bytes).hexdigest() == rev10.pdf_sha256 == artifact.sha256
    assert "REV10" in _pdf_text(frozen_bytes) and "$55.77" in _pdf_text(frozen_bytes)
    # Send for internal approval: the approver gets the normal CaliSIGN email.
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev10.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    assert any("sent to approver@example.invalid" in m for m in c["owner"].flashes())
    request = SigningRequest.query.filter_by(document_family=DOCUMENT_FAMILY_INTERNAL_APPROVAL,
                                             source_record_id=rev10.id).one()
    assert request.client_id is None and not request.countersign_required and request.status == "SENT"
    assert [p.role for p in request.participants] == [ROLE_APPROVER]
    assert request.consent_version.version_code == IA.CONSENT_INTERNAL_APPROVAL_V1_CODE
    mails = _mail(app)
    assert len(mails) == 1 and APPROVER[1] in mails[0]
    assert "document for internal approval" in mails[0] and "Internal Project Financial Summary REV10" in mails[0]
    link = _link(mails[0])
    # The approver opens the link on a laptop with no Calibrayt account.
    page = c["public"].get(link)
    assert "Internal approval" in page and "Internal Project Financial Summary REV10" in page
    assert "you approve this internal document electronically" in page
    response = c["public"].http.get(link + "/document")
    assert response.status_code == 200 and response.data == frozen_bytes  # the exact frozen PDF
    assert hashlib.sha256(response.data).hexdigest() == rev10.pdf_sha256
    # Consent and sign.
    c["public"].post(link + "/sign", data={"consent_accepted": "yes", "confirmed_signer_name": APPROVER[0]},
                     status=200)
    db.session.expire_all()
    request = db.session.get(SigningRequest, request.id)
    assert request.status == STATUS_EXECUTED  # approver only: complete when the approver signs
    approver = request.participants[0]
    assert approver.confirmed_signer_name == APPROVER[0] and approver.signed_at and approver.consent_accepted_at
    assert approver.completion_ip and approver.token_consumed_at is not None
    events = [e.event_type for e in SigningEvent.query.filter_by(signing_request_id=request.id).order_by(SigningEvent.id)]
    assert events == ["REQUEST_CREATED", "APPROVED_FOR_SIGNATURE", "SENT", "VIEWED", "CONSENT_ACCEPTED", "SIGNED",
                      "EXECUTED"]
    assert all(e.artifact_sha256 for e in request.events)
    assert IA.status_of(rev10)["state"] == "approved" and IA.status_of(rev10)["signed_by"] == APPROVER[0]
    # The signed copy is filed against the project in Documents, with its signing record.
    doc = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
           .filter(DocumentLink.record_kind == "SIGNING_REQUEST", DocumentLink.record_id == request.id,
                   DocumentLink.project_id == project.id).one())
    assert doc.document_type == "INTERNAL_FINANCIAL_SUMMARY" and doc.sensitivity == "PEOPLE"
    from app.models.documents import DocumentVersion

    filed = DocumentVersion.query.filter_by(document_id=doc.id, is_current=True).one()
    assert filed.sha256 == request.executed_artifact.sha256  # the executed artifact itself
    signed_text = _pdf_text(c["owner"].http.get(
        f"/projects/{project.id}/guided/summary-revisions/{rev10.id}.pdf").data)
    assert "REV10" in signed_text and "Internal approval" in signed_text and APPROVER[0] in signed_text
    assert "Approver email" in signed_text and request.frozen_artifact.sha256 in signed_text
    # The working summary changes later: REV11 is separate and unsigned; REV10 is unchanged and signed.
    _change_working_summary(c, project, guided, 99)
    rev11 = _freeze(c, project)
    db.session.expire_all()
    rev10_again = db.session.get(InternalSummaryRevision, rev10.id)
    assert rev11.label == "REV11" and rev11.id != rev10.id and rev11.pdf_sha256 != rev10.pdf_sha256
    assert rev10_again.pdf_sha256 == rev10.pdf_sha256 and rev10_again.data_json == rev10.data_json
    assert retrieve_frozen_artifact_bytes(IA.frozen_artifact(rev10_again)) == frozen_bytes
    assert IA.status_of(rev10_again)["state"] == "approved" and IA.status_of(rev11)["state"] == "not_sent"
    assert IA.requests_for(rev11) == []
    with pytest.raises(ValueError, match="never changes"):
        rev10_again.data_json = "{}"
        db.session.commit()
    db.session.rollback()
    review = c["owner"].get(f"/projects/{project.id}/guided/pricing")
    assert 'data-summary-revision="REV10" data-revision-state="approved"' in review
    assert 'data-summary-revision="REV11" data-revision-state="not_sent"' in review


def test_the_link_reaches_only_its_own_frozen_document(env):
    app, c, _users = env
    project, guided = _job(c)
    rev = _freeze(c, project)
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    link = _link(_mail(app)[0])
    public = c["public"]
    assert public.http.get(link).status_code == 200
    for path in (f"/projects/{project.id}", f"/projects/{project.id}/documents", "/documents",
                 f"/projects/{project.id}/guided/pricing", f"/projects/{project.id}/guided/internal-financial-summary.pdf",
                 f"/projects/{project.id}/guided/summary-revisions/{rev.id}.pdf", "/settings/people/employees",
                 "/settings/people/employees/1", "/pricing-engine/", "/settings/people"):
        response = public.http.get(path)
        assert response.status_code in (302, 401, 403) and "/login" in response.headers.get("Location", "/login"), path
    page = public.get(link)
    for leak in ("Worker A", "$55.77", "$31.25", "hourly", "wage", "Employees"):
        assert leak not in page, leak  # the ceremony page itself shows no compensation detail
    # The credential does not open another document: a second project's REV has its own link only.
    other = _freeze_other_project(c)
    c["owner"].post(f"/projects/{other[0].id}/guided/summary-revisions/{other[1].id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": "second@example.invalid"})
    second_link = _link(_mail(app)[1])
    assert public.http.get(link + "/document").data != public.http.get(second_link + "/document").data
    lookup, secret = link.split("/")[-1].split(".")
    second_lookup, second_secret = second_link.split("/")[-1].split(".")
    assert public.http.get(f"/sign/{lookup}.{second_secret}").status_code == 404  # mixing credentials fails


def _freeze_other_project(c):
    from tests.test_guided_tasks import _priced_job

    project, _guided = _priced_job(c["owner"], "Second synthetic job")
    rev = _freeze(c, project)
    return project, rev


def test_a_used_expired_or_guessed_token_refuses_and_guessing_is_rate_limited(env):
    app, c, _users = env
    project, _guided = _job(c)
    rev = _freeze(c, project)
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    link = _link(_mail(app)[0])
    public = c["public"]
    public.post(link + "/sign", data={"consent_accepted": "yes", "confirmed_signer_name": APPROVER[0]}, status=200)
    assert public.http.post(link + "/sign", data={"consent_accepted": "yes",
                                                  "confirmed_signer_name": APPROVER[0]}).status_code == 409  # used
    # Expired: a fresh REV whose link has passed its expiry.
    _change_working_summary(c, project, None, 5)
    rev2 = _freeze(c, project)
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev2.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    link2 = _link(_mail(app)[1])
    request = IA.requests_for(rev2)[0]
    request.expires_at = datetime.utcnow() - timedelta(minutes=1)
    request.participants[0].token_expires_at = request.expires_at
    db.session.commit()
    assert public.http.get(link2).status_code == 410
    assert db.session.get(SigningRequest, request.id).status == "EXPIRED"
    # Guessing: the same per-address limit as every other class.
    from app.models.signing import SigningTokenAccessAttempt

    limit = app.config.get("SIGNING_TOKEN_FAIL_LIMIT", 8)
    already = SigningTokenAccessAttempt.query.filter_by(outcome="FAIL").count()  # the used and expired presentations
    lookup = link.split("/")[-1].split(".")[0]
    left = limit - already
    statuses = [public.http.get(f"/sign/{lookup}.{'x' * 30}{i}").status_code for i in range(left + 1)]
    assert statuses[:left] == [404] * left and statuses[-1] == 429
    assert public.http.get(link + "/document").status_code == 429  # even the real link, from that address


def test_only_project_economics_may_freeze_or_send_and_crew_rates_need_employee_cost(env, monkeypatch):
    app, c, _users = env
    project, _guided = _job(c)
    c["staff"].post(f"/projects/{project.id}/guided/summary-revisions", status=403)
    rev = _freeze(c, project)
    c["staff"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/send",
                    data={"approver_name": "X", "approver_email": "x@example.invalid"}, status=403)
    from app.services import financial_access

    monkeypatch.setattr(financial_access, "can_view_project_economics", lambda user, org: True)
    # Economics but not employee cost: REV with crew rates cannot be sent; a freeze gives the crew-total variant.
    c["staff"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/send",
                    data={"approver_name": "X", "approver_email": "x@example.invalid"})
    assert any("crew-total version" in m for m in c["staff"].flashes())
    assert IA.requests_for(rev) == []
    _change_working_summary(c, project, None, 7)
    c["staff"].post(f"/projects/{project.id}/guided/summary-revisions")
    db.session.expire_all()
    crew_total = InternalSummaryRevision.query.order_by(InternalSummaryRevision.id.desc()).first()
    assert not crew_total.employee_detail
    text = _pdf_text(__import__("app.services.signing", fromlist=["x"]).retrieve_frozen_artifact_bytes(
        IA.frozen_artifact(crew_total)))
    assert "$55.77" not in text and "Worker A" not in text and "Labour (crew)" in text
    c["staff"].post(f"/projects/{project.id}/guided/summary-revisions/{crew_total.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    assert IA.requests_for(crew_total)[0].status == "SENT"
    # Nothing changed since the latest REV: no duplicate REV.
    c["staff"].post(f"/projects/{project.id}/guided/summary-revisions")
    assert any("Nothing changed" in m for m in c["staff"].flashes())


def test_the_approver_plus_countersigner_rule(env, monkeypatch):
    app, c, users = env
    project, _guided = _job(c)
    monkeypatch.setitem(IA.GOVERNANCE, IA.DOCUMENT_TYPE_FINANCIAL_SUMMARY,
                        dict(IA.GOVERNANCE[IA.DOCUMENT_TYPE_FINANCIAL_SUMMARY],
                             signers=IA.SIGNERS_APPROVER_AND_COUNTERSIGNER))
    rev = _freeze(c, project)
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/send",
                    data={"approver_name": APPROVER[0], "approver_email": APPROVER[1]})
    request = IA.requests_for(rev)[0]
    assert request.countersign_required and [p.role for p in request.participants] == [ROLE_APPROVER,
                                                                                        "ORGANIZATION_COUNTERSIGN"]
    link = _link(_mail(app)[0])
    c["public"].post(link + "/sign", data={"consent_accepted": "yes", "confirmed_signer_name": APPROVER[0]}, status=200)
    db.session.expire_all()
    assert db.session.get(SigningRequest, request.id).status == STATUS_SIGNED
    assert IA.status_of(rev)["state"] == "awaiting_countersign" and IA.signed_document(request) is None
    c["owner"].post(f"/projects/{project.id}/guided/summary-revisions/{rev.id}/countersign")
    db.session.expire_all()
    request = db.session.get(SigningRequest, request.id)
    assert request.status == STATUS_EXECUTED and request.countersigned_by_user_id == users["owner"].id
    assert IA.signed_document(request) is not None
