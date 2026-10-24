"""Local office for the roles and isolation browser checks (tools/release/evidence_roles.mjs, 20 Oct 2026).

Temporary database, synthetic data only, clearly labelled. Seeds what exists before the walk starts:

* Organization A (the default organization): the Instance Owner (office@example.com), an ordinary office
  user (Sam Staff), a crew member (Kevin Field) on a crew, and the Ontario Brayman V1 contract package.
* Organization B: its own office user, client and project, which nobody in A may see.
* A project with a priced estimate whose line carries the company's internal cost, markup and an
  internal provenance note. Its proposal is sent to the customer (the link the walk opens), and a second
  proposal whose first link was replaced and whose current link has expired.
* An accepted proposal whose contract was generated and sent for signature, an expired contract
  invitation, and two approved change orders sent for signature (one to sign, one to decline).
* Supplier PRO Desk: a synthetic store and a rival store, each with a sign-in; three issued quotations
  with customer links (one to accept, one to decline, one replaced by a newer link).

The walk itself (sign-in, refusals, signing, accepting, declining, links) happens in the browser.
The idle clock: ``session_timeout._now`` reads an offset in seconds from the file named in the facts
(``clock_file``), so the walk can move this office's clock 31 minutes forward without waiting.
It never reads the hosted database.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401  (models load before app.services)
from app.services.local_time import local_today  # noqa: E402  (the office's date, as the app uses)

OWNER = ("office@example.com", "office-test-password", "Office Test User")
STAFF = ("sam.staff@example.invalid", "Synthetic-staff-pass-1", "Sam Staff (synthetic office)")
KEVIN = ("kevin.field@example.invalid", "field-test-password", "Kevin Field (synthetic crew)")
ORG_B = ("ORG-RB2", "Rival Builders B (synthetic)")
BEA = ("bea.orgb@example.invalid", "Synthetic-orgb-pass-1", "Bea OrgB (synthetic office)")
ORG_B_CLIENT = "OrgB Hidden Client Quillfeather (synthetic)"
ORG_B_PROJECT = "OrgB Hidden Project Larkspur (synthetic)"
CUSTOMER = ("Pat Synthetic Owner", "pat.owner@example.invalid")
OTHER_CUSTOMER = ("Morgan Other Customer (synthetic)", "morgan.other@example.invalid")
# Company figures a customer must never see: the cost item's code and name, its unit cost and markup,
# an internal provenance note (written the way the approved-cost hand-off writes it) and an internal
# project note.
INTERNAL = {
    "code": "INT-ZEPHYR",
    "name": "Zephyr crew allowance (synthetic)",
    "unit_cost": "8765.43",
    "markup": "41.25",
    "note": "Approved contractor cost #7; quantity confirmed by Ben Synthetic.",
    "project_note": "INTERNAL ONLY: margin is thin on this job (synthetic)",
    "co_internal_cost": "4321.09",
}
CUSTOMER_LINE = "Deck framing, supplied and installed (synthetic)"
STORE = ("pro.desk@example.invalid", "Synthetic-pro-desk-pass-1")
RIVAL = ("rival.store@example.invalid", "Synthetic-rival-pass-1")
QUOTE_CUSTOMERS = ("Synthetic Farmer Accept", "Synthetic Farmer Decline", "Synthetic Farmer Replaced")


def _credential(path: str) -> str:
    return path.rsplit("/", 1)[1]


def _users():
    from app.models.user import UserMembership
    from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package
    from app.services.instance_authority import set_instance_owner
    from app.services.jurisdiction import ensure_jurisdiction_seed
    from app.services.organization_crew import add_crew_member, create_crew
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
    from app.models.organization import Organization
    from tests.auth_fixtures import ensure_office_user

    ensure_default_organization()
    ensure_jurisdiction_seed(commit=True)
    owner = ensure_office_user()
    membership = UserMembership.query.filter_by(user_id=owner.id, organization_id=ORG).one()
    set_instance_owner(ORG, membership.id, owner.id)
    staff = ensure_office_user(email=STAFF[0], password=STAFF[1], display_name=STAFF[2])
    kevin = ensure_office_user(email=KEVIN[0], password=KEVIN[1], display_name=KEVIN[2])
    crew = create_crew(name="North Crew (synthetic)", organization_id=ORG)
    add_crew_member(crew.id, user_id=kevin.id, effective_from=(local_today() - timedelta(days=30)).isoformat(),
                    organization_id=ORG)
    ensure_brayman_v1_interim_ontario_package()
    db.session.add(Organization(id=ORG_B[0], legal_name=ORG_B[1], display_name=ORG_B[1], is_active=True))
    db.session.commit()
    bea = ensure_office_user(email=BEA[0], password=BEA[1], display_name=BEA[2], organization_id=ORG_B[0])
    db.session.commit()
    return {"owner": owner, "staff": staff, "kevin": kevin, "bea": bea, "crew_id": crew.id}


def _org_b_project():
    from app.models import Client, Project

    client = Client(name=ORG_B_CLIENT, organization_id=ORG_B[0])
    db.session.add(client)
    db.session.flush()
    project = Project(name=ORG_B_PROJECT, client_id=client.id, organization_id=ORG_B[0], status="Estimating",
                      address="9 Hidden Lane (synthetic)")
    db.session.add(project)
    db.session.commit()
    return project


def _priced_version(project, number):
    from app.models import CostItem
    from app.models.estimate import EstimateSection
    from app.services.estimate_builder import add_cost_item_line
    from app.services.estimates import create_estimate
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from tests.proposal_issue_support import approve_for_issue

    item = CostItem.query.filter_by(organization_id=ORG, code=INTERNAL["code"]).first()
    if item is None:
        item = CostItem(organization_id=ORG, code=INTERNAL["code"], name=INTERNAL["name"], category="Labour", unit="ls",
                        unit_cost=Decimal(INTERNAL["unit_cost"]), default_markup_percent=Decimal(INTERNAL["markup"]))
        db.session.add(item)
        db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number=number, title="Deck (synthetic)", organization_id=ORG)
    version = estimate.current_version
    section = EstimateSection(estimate_version_id=version.id, name="Deck", sort_order=1, subtotal=Decimal("0"))
    db.session.add(section)
    db.session.commit()
    line = add_cost_item_line(section, cost_item_id=item.id, quantity=1, notes=INTERNAL["note"], organization_id=ORG)
    line.description = CUSTOMER_LINE
    db.session.commit()
    approve_for_issue(version)
    return version


def _proposals(users):
    from app.models.proposal_acceptance import ProposalClientLink
    from app.services import proposal_acceptance as PA
    from app.services.proposals import create_proposal_template
    from tests.test_brayman_v1_interim_contract import _ottawa_project

    owner = users["owner"]
    create_proposal_template(name="Synthetic template", is_active=True, is_default=True, default_intro_text="Thank you.",
                             default_payment_terms="As stated on this proposal")
    facts = {}
    # 1. The link the customer opens, views, downloads and accepts in the walk.
    project = _ottawa_project(name="Roles walk deck (synthetic)")
    project.description = INTERNAL["project_note"]
    db.session.commit()
    version = _priced_version(project, "EST-ROLES-1")
    proposal = PA.sign_off_estimate(version, user=owner)
    sent = PA.send_proposal_to_client(proposal, user=owner, client_name=CUSTOMER[0], client_email=CUSTOMER[1])
    facts.update(project_id=project.id, proposal_id=proposal.id, proposal_link=sent.path,
                 proposal_number=proposal.proposal_number, estimate_id=version.estimate_id, version_id=version.id)
    # 2. Another customer's proposal: its first link was replaced, its current link has expired.
    other = _ottawa_project(name="Other customer job (synthetic)")
    other_version = _priced_version(other, "EST-ROLES-2")
    other_proposal = PA.sign_off_estimate(other_version, user=owner)
    first = PA.send_proposal_to_client(other_proposal, user=owner, client_name=OTHER_CUSTOMER[0], client_email=OTHER_CUSTOMER[1])
    second = PA.send_proposal_to_client(other_proposal, user=owner, client_name=OTHER_CUSTOMER[0], client_email=OTHER_CUSTOMER[1])
    link = db.session.get(ProposalClientLink, second.link.id)
    link.expires_at = datetime.utcnow() - timedelta(minutes=5)
    db.session.commit()
    facts.update(other_project_id=other.id, replaced_proposal_link=first.path, expired_proposal_link=second.path)
    # 3. An accepted proposal: its contract is generated and sent; change orders follow.
    signed = _ottawa_project(name="Contract and change order job (synthetic)")
    signed_version = _priced_version(signed, "EST-ROLES-3")
    signed_proposal = PA.sign_off_estimate(signed_version, user=owner)
    signed_sent = PA.send_proposal_to_client(signed_proposal, user=owner, client_name=CUSTOMER[0], client_email=CUSTOMER[1])
    acceptance = PA.accept_via_link(_credential(signed_sent.path), confirmed_name=CUSTOMER[0], accepted=True,
                                    client_ip=None, user_agent=None)
    assert acceptance.contract_id is not None, acceptance.contract_block_code
    facts.update(signed_project_id=signed.id, contract_id=acceptance.contract_id, used_proposal_link=signed_sent.path)
    return facts


def _scheduled_work(project_id):
    """One scheduled work item, so the walk can prove a field user cannot move it (G7, 21 Oct 2026)."""
    from datetime import date

    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.services.schedule import create_schedule_item
    from app.services.work_structure import add_project_element, ensure_baseline_work_catalog

    ensure_baseline_work_catalog()
    element = add_project_element(project_id=project_id, display_name="Deck framing (synthetic)", organization_id=ORG)
    today = local_today()
    item = create_schedule_item(project_id=project_id, project_work_element_id=element.id,
                                scheduled_start=today, scheduled_end=today, organization_id=ORG)
    return {"schedule_item_id": item.id, "schedule_item_start": today.isoformat()}


def _signing(users, facts):
    from app.models.signing import SigningRequest
    from app.project_controls.models import ChangeOrderItem
    from app.project_controls.services import create_change_order
    from app.services import signing as S
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.models import Project

    owner = users["owner"]
    issue = S.office_send_contract_for_signature(
        facts["contract_id"], organization_id=ORG, actor_user_id=owner.id, actor_identifier=owner.email,
        invited_name=CUSTOMER[0], invited_email=CUSTOMER[1], countersign_required=True,
        expires_at=datetime.utcnow() + timedelta(days=7))
    facts["contract_sign_link"] = issue.path
    project = db.session.get(Project, facts["signed_project_id"])
    for key, title in (("co_sign_link", "Synthetic extra footing step"), ("co_decline_link", "Synthetic railing upgrade"),
                       ("co_expired_link", "Synthetic late gate")):
        change_order = create_change_order(project=project, title=title, tax_percent=13)
        db.session.add(ChangeOrderItem(change_order_id=change_order.id, description=f"{title}, supplied and installed",
                                       quantity=Decimal("1"), unit="ls", unit_price=Decimal("600")))
        change_order.status = "Approved"
        change_order.approved_internal_direct_cost = Decimal(INTERNAL["co_internal_cost"])
        db.session.commit()
        co_issue = S.office_send_change_order_for_signature(
            change_order.id, organization_id=ORG, actor_user_id=owner.id, actor_identifier=owner.email,
            invited_name=CUSTOMER[0], invited_email=CUSTOMER[1], countersign_required=True,
            expires_at=datetime.utcnow() + timedelta(days=7))
        facts[key] = co_issue.path
        if key == "co_expired_link":
            request = db.session.get(SigningRequest, co_issue.request.id)
            request.expires_at = datetime.utcnow() - timedelta(minutes=5)
            for participant in request.participants:
                participant.token_expires_at = request.expires_at
            db.session.commit()
    return facts


def _pro_desk(application):
    """Three issued quotations with customer links, made through the store's own pages."""
    from app.models.supplier_quote import SupplierQuote
    from tests.pro_desk_page_server import QUICK_FORM, seed

    with application.app_context():
        store_facts = seed()
    sid = store_facts["supplier_id"]
    store = application.test_client()
    assert store.post("/supplier/login", data={"email": STORE[0], "password": STORE[1]}).status_code == 302
    links = []
    for name in QUOTE_CUSTOMERS:
        form = {"customer_name": name, "customer_phone": "613-555-0100", "customer_town": "Winchester",
                "demo_synthetic": "yes", "assembly_id": str(store_facts["standard_id"]), **QUICK_FORM}
        made = store.post(f"/supplier/{sid}/pro-desk/quick", data=form)
        assert made.status_code == 302, made.data[:400]
        with application.app_context():
            quote = SupplierQuote.query.order_by(SupplierQuote.id.desc()).first()
            quote_id, number = quote.id, quote.number
        base = f"/supplier/{sid}/pro-desk/{quote_id}"
        with application.app_context():
            from app.services import supplier_pro_desk as P

            for row in P.price_quote(db.session.get(SupplierQuote, quote_id))["rows"]:
                if row["code"].startswith("CAL-OB-TRUSS"):
                    store.post(f"{base}/line", data={"code": row["code"], "exclude_reason": "Truss quote to follow"})
        issued = store.post(f"{base}/issue")
        assert issued.status_code == 302, issued.data[:400]
        made_link = store.post(f"{base}/link")
        credential = re.search(r"link=([^#&]+)", made_link.headers["Location"]).group(1)
        if name == QUOTE_CUSTOMERS[2]:
            # A newer link replaces this one.
            store.post(f"{base}/link")
        with application.app_context():
            total = str(db.session.get(SupplierQuote, quote_id).total)
        links.append({"customer": name, "link": f"/quote/{credential}", "number": number, "quote_id": quote_id,
                      "total": total})
    return {"store_supplier_id": sid, "rival_supplier_id": store_facts["rival_id"], "quotes": links,
            "store": list(STORE), "rival": list(RIVAL)}


def _install_clock(clock_file: str):
    from app.services import session_timeout

    real = session_timeout._now

    def shifted():
        try:
            return real() + float(Path(clock_file).read_text() or 0)
        except (OSError, ValueError):
            return real()

    session_timeout._now = shifted


def main():
    workdir = tempfile.mkdtemp(prefix="roles-office-")
    mail = os.path.join(workdir, "mail")
    clock = os.path.join(workdir, "clock_offset")
    Path(clock).write_text("0")
    uri = f"sqlite:///{workdir}/roles.db"
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri, "SECRET_KEY": "roles-secret-key",
              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": mail, "WTF_CSRF_ENABLED": False,
              "CONTRACT_ARTIFACT_ROOT": os.path.join(workdir, "contracts"),
              "SIGNING_ARTIFACT_ROOT": os.path.join(workdir, "signing"),
              "BRAND_LOGO_ROOT": os.path.join(workdir, "logos")}
    application = create_app(config)
    with application.app_context():
        db.create_all()
        users = _users()
        org_b = _org_b_project()
        facts = _proposals(users)
        facts = _signing(users, facts)
        facts.update(crew_id=users["crew_id"], org_b_project_id=org_b.id, staff_user_id=users["staff"].id,
                     kevin_user_id=users["kevin"].id)
        facts.update(_scheduled_work(facts["project_id"]))
    facts.update(_pro_desk(application))
    application.config["WTF_CSRF_ENABLED"] = True  # seed only; the browser walk runs with CSRF on
    _install_clock(clock)
    facts.update({"owner": list(OWNER[:2]), "staff": list(STAFF), "kevin": list(KEVIN), "bea": list(BEA),
                  "org_b": list(ORG_B), "org_b_client": ORG_B_CLIENT, "org_b_project": ORG_B_PROJECT,
                  "customer": list(CUSTOMER), "other_customer": list(OTHER_CUSTOMER), "internal": INTERNAL,
                  "customer_line": CUSTOMER_LINE, "mail_dir": mail, "clock_file": clock, "database_uri": uri,
                  "workdir": workdir})
    port = int(os.environ["ROLES_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
