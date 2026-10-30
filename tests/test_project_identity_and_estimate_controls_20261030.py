"""Project identity + universal estimate controls (Joel, 30 Oct 2026).

Brayman Project # (BC-YYYY-NNNN, automatic, permanent, never reused), Client Project # (the client's own reference,
text, edited with history), and each estimate's labour rate and target gross margin (company defaults captured,
project overrides with a reason, one calculation feeding the internal and customer documents). Paulusse is the
acceptance case. Synthetic data only.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, EstimateLineItem, Organization, Project, ProjectIdentityEvent, ProjectNumberSequence
from app.models.pricing_engine import PricingAuditEvent
from app.services import estimate_labour_hours as labour
from app.services.estimate_builder import add_manual_line, create_section
from app.services.estimate_economics import (
    EstimateEconomicsError,
    economics,
    project_values,
    set_company_default_margin,
    set_company_labour_rate,
    set_project_pricing,
)
from app.services.estimates import clone_current_version, create_estimate
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard, promote_direct_labour_cost_rate
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from app.services.pricing_engine import create_pricing_policy
from app.services.project_identity import (
    ProjectIdentityError,
    correct_brayman_project_number,
    reference_line,
    set_client_project_number,
)
from tests.proposal_issue_support import approve_for_issue

JOEL = "Joel Brayman"
YEAR = datetime.utcnow().year
ROOT = Path(__file__).resolve().parents[1]
BC = re.compile(rf"^BC-{YEAR}-\d{{4}}$")


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_org_001_direct_labour_cost_rate_standard()  # v1 $65, as the migrations seed it
        promote_direct_labour_cost_rate("75", approved_by=JOEL, reason="Brayman $75 (30 Oct 2026)", organization_id=ORG)
        create_pricing_policy(policy_code="ORG-001-TRUE-GM-15", method="TRUE_GROSS_MARGIN", actor=JOEL,
                              target_gross_margin=Decimal("0.15"), tax_jurisdiction="CA-ON", tax_percent=Decimal("13"),
                              overhead_treatment="UNSPECIFIED", profit_treatment="UNSPECIFIED",
                              contingency_visibility="UNSPECIFIED", provenance="docs/pricing-policy.md", is_default=True)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


def _client(name="Lockwood Brothers (synthetic)"):
    row = Client(name=name, organization_id=ORG)
    db.session.add(row)
    db.session.flush()
    return row


def _project(name="Job (synthetic)", client=None, **kw):
    project = Project(name=name, client_id=(client or _client()).id, organization_id=ORG, status="Estimating", **kw)
    db.session.add(project)
    db.session.commit()
    return project


# ============================================================================================ Brayman Project #
def test_numbers_are_assigned_automatically_in_order_for_the_year_and_recorded(app):
    client = _client()
    numbers = [_project(f"P{i}", client).project_number for i in range(3)]
    assert numbers == [f"BC-{YEAR}-0001", f"BC-{YEAR}-0002", f"BC-{YEAR}-0003"]
    assert ProjectNumberSequence.query.filter_by(organization_id=ORG, year=YEAR).one().last_value == 3
    events = ProjectIdentityEvent.query.filter_by(field="BRAYMAN_PROJECT_NUMBER").all()
    assert [e.new_value for e in events] == numbers and all(e.previous_value is None for e in events)


def test_the_year_is_the_creation_year_and_restarts_the_count(app):
    _project("this year")
    later = _project("next year", created_at=datetime(YEAR + 1, 1, 2, 9, 0))
    assert later.project_number == f"BC-{YEAR + 1}-0001"


def test_a_number_is_never_reused_and_a_number_already_taken_is_skipped(app):
    client = _client()
    first, second = _project("a", client), _project("b", client)
    db.session.delete(second)
    db.session.commit()
    third = _project("c", client)
    assert third.project_number == f"BC-{YEAR}-0003"  # 0002 is gone for good (gaps are fine)
    _project("typed by hand", client, project_number=f"BC-{YEAR}-0004")  # an existing legitimate number is kept
    assert _project("d", client).project_number == f"BC-{YEAR}-0005"
    assert first.project_number == f"BC-{YEAR}-0001"


def test_another_company_uses_its_own_prefix(app):
    db.session.add(Organization(id="ORG-SYN2", legal_name="Other Co (synthetic)", display_name="Other Co",
                                primary_address="1 Main St", default_region="Ottawa", currency="CAD",
                                tax_jurisdiction="Ontario (HST 13%)", is_active=True))
    db.session.commit()
    other = Client(name="Other client", organization_id="ORG-SYN2")
    db.session.add(other)
    db.session.flush()
    project = Project(name="Other job", client_id=other.id, organization_id="ORG-SYN2", status="Lead")
    db.session.add(project)
    db.session.commit()
    assert project.project_number == f"ORG-SYN2-{YEAR}-0001"
    assert _project("ours").project_number == f"BC-{YEAR}-0001"


def test_the_number_is_permanent_through_every_other_change_and_corrections_are_recorded(app):
    project = _project("Original name")
    number = project.project_number
    project.name, project.address, project.status = "Renamed", "1 New St", "Active"
    project.client_id = _client("Another client").id
    db.session.commit()
    assert project.project_number == number
    project.project_number = f"BC-{YEAR}-0099"
    with pytest.raises(ProjectIdentityError, match="permanent"):
        db.session.commit()
    db.session.rollback()
    with pytest.raises(ProjectIdentityError, match="reason"):
        correct_brayman_project_number(project, f"BC-{YEAR}-0099", actor=JOEL, reason="")
    correct_brayman_project_number(project, f"BC-{YEAR}-0099", actor=JOEL, reason="Entered twice by mistake (synthetic)")
    db.session.commit()
    assert project.project_number == f"BC-{YEAR}-0099"
    event = ProjectIdentityEvent.query.filter_by(project_id=project.id, actor_identifier=JOEL).one()
    assert (event.previous_value, event.new_value, event.reason) == (number, f"BC-{YEAR}-0099",
                                                                     "Entered twice by mistake (synthetic)")


def test_two_writers_at_once_never_get_the_same_number(tmp_path):
    path = tmp_path / "concurrency.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}", "SECRET_KEY": "t",
                              "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"timeout": 30}}})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        client = Client(name="Race client", organization_id=ORG)
        db.session.add(client)
        db.session.commit()
        client_id = client.id
    errors = []

    def writer(tag):
        try:
            with application.app_context():
                for i in range(8):
                    db.session.add(Project(name=f"{tag}-{i}", client_id=client_id, organization_id=ORG, status="Lead"))
                    db.session.commit()
                db.session.remove()
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))

    threads = [threading.Thread(target=writer, args=(t,)) for t in ("a", "b", "c")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    with application.app_context():
        numbers = [p.project_number for p in Project.query.all()]
        assert len(numbers) == 24 and len(set(numbers)) == 24 and all(BC.match(n) for n in numbers)
        assert ProjectNumberSequence.query.filter_by(organization_id=ORG, year=YEAR).one().last_value == 24


def test_the_company_work_record_keeps_its_own_reference_and_is_not_a_numbered_job(app):
    from app.services.time_entry import company_time_project_number, ensure_company_time_project

    company = ensure_company_time_project(ORG)
    db.session.commit()
    assert company.project_number == company_time_project_number(ORG)
    assert reference_line(company) == ""


# ============================================================================================ Client Project #
def test_client_project_number_is_text_optional_and_kept_exactly(app):
    project = _project()
    assert project.client_project_number is None and reference_line(project) == f"Brayman Project # {project.project_number}"
    for value in ("0042", "L-2291/B.7", "007 A"):
        set_client_project_number(project, value, actor=JOEL)
        db.session.commit()
        assert project.client_project_number == value
    with pytest.raises(ProjectIdentityError):
        set_client_project_number(project, "<script>", actor=JOEL)
    with pytest.raises(ProjectIdentityError):
        set_client_project_number(project, "9" * 81, actor=JOEL)
    set_client_project_number(project, "  ", actor=JOEL)
    db.session.commit()
    assert project.client_project_number is None


def test_client_number_changes_are_recorded_and_a_duplicate_for_the_client_is_a_warning(app):
    client = _client()
    first, second = _project("first", client), _project("second", client)
    set_client_project_number(first, "LB-38", actor=JOEL)
    done = set_client_project_number(second, "lb-38", actor="Ben Brayman", reason="Lockwood's email (synthetic)")
    db.session.commit()
    assert done["changed"] and [p.id for p in done["duplicates"]] == [first.id]
    assert second.client_project_number == "lb-38"
    event = ProjectIdentityEvent.query.filter_by(project_id=second.id, field="CLIENT_PROJECT_NUMBER").one()
    assert (event.previous_value, event.new_value, event.actor_identifier, event.reason) == (
        None, "lb-38", "Ben Brayman", "Lockwood's email (synthetic)")


def _office(app):
    from tests.auth_fixtures import ensure_office_user, login_office_user

    ensure_office_user()
    db.session.commit()
    client = app.test_client()
    login_office_user(client)
    return client


def test_office_pages_create_show_search_and_edit_the_numbers(app):
    browser = _office(app)
    client = _client("Lockwood Brothers (synthetic)")
    response = browser.post("/projects/new", data={
        "name": "Kingfisher cladding (synthetic)", "client_id": client.id, "client_project_number": "LB-0712",
        "project_type": "Addition", "pricing_posture": "Competitive", "execution_risk": "Normal",
        "schedule_condition": "Normal", "site_condition": "Normal", "estimate_stage": "Preliminary",
        "delivery_model": "Self-Perform", "permit_context_class": "Other/unspecified", "status": "Estimating",
        "street": "3 Kingfisher Cres", "municipality": "North Grenville", "province_state": "Ontario",
        "postal_zip": "K0G 1J0", "country": "Canada"})
    assert response.status_code == 302
    project = Project.query.filter_by(name="Kingfisher cladding (synthetic)").one()
    assert BC.match(project.project_number) and project.client_project_number == "LB-0712"
    hub = browser.get(f"/projects/{project.id}").get_data(as_text=True)
    assert project.project_number in hub and "Client Project # LB-0712" in hub
    listing = browser.get(f"/projects/?q={project.project_number[-4:]}").get_data(as_text=True)
    assert "Kingfisher cladding (synthetic)" in listing and project.project_number in listing
    assert "Kingfisher cladding (synthetic)" in browser.get("/projects/?q=lb-0712").get_data(as_text=True)
    assert "No project matches" in browser.get("/projects/?q=nothing-like-it").get_data(as_text=True)
    browser.post(f"/projects/{project.id}/client-project-number", data={"client_project_number": "LB-0712-R1",
                                                                       "reason": "Revised tender (synthetic)"})
    db.session.refresh(project)
    assert project.client_project_number == "LB-0712-R1"
    from app.services.cal_find import match_references

    with app.test_request_context():
        found = match_references(ORG, ["lb-0712-r1"])
    assert any("Kingfisher cladding" in item.title for item in found)


# ============================================================================================ estimate controls
def _paulusse(number="EST-PAUL-1", hours="272"):
    """Paulusse in the engine: $19,547.32 of material, equipment and disposal and 272 labour hours."""
    project = _project("Paulusse & Bonokoski (synthetic)")
    estimate = create_estimate(project_id=project.id, estimate_number=number, title="Exterior cladding")
    version = estimate.current_version
    section = create_section(version, name="Exterior cladding")
    package = add_manual_line(section, line_type="Custom", description="Materials, equipment and disposal",
                              quantity=1, unit="ls", unit_cost=Decimal("19547.32"))
    labour.save_hours(version, organization_id=ORG, hours_by_item={package.id: hours}, actor=JOEL)
    db.session.commit()
    return project, estimate, version


def _figures(version):
    e = economics(version)
    return (e["labour_cost"], e["direct_cost"], e["selling_price"], e["gross_profit"], e["true_gross_margin_percent"],
            e["tax"], e["customer_total"])


def test_a_new_estimate_captures_the_company_defaults(app):
    _project_, _estimate, version = _paulusse()
    values = project_values(version)
    assert (version.labour_rate, version.target_gross_margin) == (Decimal("75.00"), Decimal("0.150000"))
    assert not values["labour_rate_is_override"] and not values["margin_is_override"]


def test_paulusse_baseline_reproduces_through_the_engine_and_the_proposal(app):
    from app.services.proposals import create_proposal
    from tests.test_estimate_output_consistency import _template

    _project_, estimate, version = _paulusse()
    approve_for_issue(version, actor=JOEL)
    m = Decimal
    assert _figures(version) == (m("20400.00"), m("39947.32"), m("46996.85"), m("7049.53"), m("15.00"), m("6109.59"),
                                 m("53106.44"))
    assert economics(version)["applied"]
    proposal = create_proposal(estimate=estimate, version=version, template=_template())
    assert (proposal.subtotal, proposal.tax_amount, proposal.total) == (m("46996.85"), m("6109.59"), m("53106.44"))


def test_override_a_labour_rate_80(app):
    _project_, _estimate, version = _paulusse()
    approve_for_issue(version, actor=JOEL)
    with pytest.raises(EstimateEconomicsError, match="reason"):
        set_project_pricing(version, actor=JOEL, labour_rate="80")
    done = set_project_pricing(version, actor=JOEL, labour_rate="80.00", reason="Union crew (synthetic)")
    db.session.commit()
    assert done == {"changed": True, "rerated": 1, "reapproved": True, "repriced": True}
    lab = EstimateLineItem.query.filter(EstimateLineItem.code.like("LAB-%")).one()
    assert lab.quantity == Decimal("272") and lab.unit_cost == Decimal("80.00")  # hours unchanged
    m = Decimal
    assert _figures(version) == (m("21760.00"), m("41307.32"), m("48596.85"), m("7289.53"), m("15.00"), m("6317.59"),
                                 m("54914.44"))
    assert version.pricing_snapshot.customer_total == m("54914.44")
    values = project_values(version)
    assert values["labour_rate_is_override"] and values["labour_rate_default"] == m("75.00")
    audit = PricingAuditEvent.query.filter_by(event_type="estimate_labour_rate_change").one()
    assert audit.actor == JOEL and "75.00 -> 80.00" in audit.detail and "Union crew" in audit.detail


def test_override_b_margin_20_leaves_costs_alone(app):
    _project_, _estimate, version = _paulusse()
    approve_for_issue(version, actor=JOEL)
    done = set_project_pricing(version, actor=JOEL, margin_percent="20", reason="Tight schedule (synthetic)")
    db.session.commit()
    assert done == {"changed": True, "rerated": 0, "reapproved": False, "repriced": True}
    m = Decimal
    assert _figures(version) == (m("20400.00"), m("39947.32"), m("49934.15"), m("9986.83"), m("20.00"), m("6491.44"),
                                 m("56425.59"))
    assert version.pricing_snapshot.target_gross_margin == m("0.2")
    audit = PricingAuditEvent.query.filter_by(event_type="estimate_target_margin_change").one()
    assert "15.00% -> 20.00%" in audit.detail


def test_override_c_both_at_once_is_the_authoritative_58346_59(app):
    _project_, _estimate, version = _paulusse()
    approve_for_issue(version, actor=JOEL)
    set_project_pricing(version, actor=JOEL, labour_rate="80", margin_percent="20", reason="Both (synthetic)")
    db.session.commit()
    m = Decimal
    assert _figures(version) == (m("21760.00"), m("41307.32"), m("51634.15"), m("10326.83"), m("20.00"), m("6712.44"),
                                 m("58346.59"))
    # Back to the company defaults needs no reason and shows no override.
    set_project_pricing(version, actor=JOEL, labour_rate="75", margin_percent="15")
    db.session.commit()
    values = project_values(version)
    assert not values["labour_rate_is_override"] and not values["margin_is_override"]
    assert economics(version)["customer_total"] == m("53106.44")


def test_invalid_values_are_refused(app):
    _project_, _estimate, version = _paulusse()
    for rate in ("0", "-5", "abc", "75.001", ""):
        if rate == "":
            assert not set_project_pricing(version, actor=JOEL, labour_rate=rate)["changed"]
            continue
        with pytest.raises(EstimateEconomicsError):
            set_project_pricing(version, actor=JOEL, labour_rate=rate, reason="x")
    for margin in ("100", "-1", "101", "fifteen"):
        with pytest.raises(EstimateEconomicsError):
            set_project_pricing(version, actor=JOEL, margin_percent=margin, reason="x")
    with pytest.raises(EstimateEconomicsError):
        set_project_pricing(version, actor="AI", margin_percent="20", reason="x")
    assert set_project_pricing(version, actor=JOEL, margin_percent="0", reason="At cost (synthetic)")["changed"]


def test_company_default_changes_reach_new_estimates_only_and_revisions_keep_the_project_values(app):
    _project_, estimate, version = _paulusse()
    set_project_pricing(version, actor=JOEL, labour_rate="82", reason="Remote site (synthetic)")
    db.session.commit()
    set_company_labour_rate("78", actor=JOEL, reason="2027 wages (synthetic)", organization_id=ORG)
    set_company_default_margin("18", actor=JOEL, reason="Market (synthetic)", organization_id=ORG)
    db.session.commit()
    assert (version.labour_rate, version.target_gross_margin) == (Decimal("82.00"), Decimal("0.150000"))
    revision = clone_current_version(estimate, version_label="Rev 1")
    assert (revision.labour_rate, revision.labour_rate_reason) == (Decimal("82.00"), "Remote site (synthetic)")
    assert revision.target_gross_margin == Decimal("0.150000")
    _p2, _e2, fresh = _paulusse("EST-PAUL-2")
    assert (fresh.labour_rate, fresh.target_gross_margin) == (Decimal("78.00"), Decimal("0.180000"))


def test_an_estimate_from_before_keeps_resolving_as_it_did(app):
    _project_, _estimate, version = _paulusse()
    version.labour_rate = version.target_gross_margin = None  # a version created before 30 Oct 2026
    db.session.commit()
    values = project_values(version)
    assert values["labour_rate"] == Decimal("75.00") and values["target_gross_margin"] == Decimal("0.15")


def test_project_pricing_page_and_route_with_permissions(app):
    _project_, estimate, version = _paulusse()
    url = f"/estimates/{estimate.id}/versions/{version.id}/project-pricing"
    anonymous = app.test_client()
    assert anonymous.post(url, data={"labour_rate": "90", "reason": "x"}).status_code in (302, 401, 403)
    db.session.refresh(version)
    assert version.labour_rate == Decimal("75.00")
    browser = _office(app)
    page = browser.get(f"/estimates/{estimate.id}/versions/{version.id}").get_data(as_text=True)
    assert "Project pricing" in page and 'value="75.00"' in page and 'value="15.00"' in page
    browser.post(url, data={"labour_rate": "80", "margin_percent": "20", "reason": "Synthetic override"})
    db.session.refresh(version)
    assert (version.labour_rate, version.target_gross_margin) == (Decimal("80.00"), Decimal("0.200000"))
    page = browser.get(f"/estimates/{estimate.id}/versions/{version.id}").get_data(as_text=True)
    assert "Project override · Company default $75.00" in page and "Project override · Company default 15.00%" in page
    assert "$51,634.15" in page  # (19,547.32 + 272 x 80) / 0.8, the same figure everywhere


# ============================================================================================ documents
def _pdf_text(data: bytes) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)


def test_identifiers_reach_the_proposal_change_order_and_supplier_documents(app):
    from app.services.proposal_pdf import generate_proposal_pdf
    from app.services.proposals import create_proposal
    from app.services.supplier_hub import _project_reference
    from app.services.supplier_pricing_request_form import project_label
    from tests.test_estimate_output_consistency import _template

    project, estimate, version = _paulusse()
    set_client_project_number(project, "LB-0712", actor=JOEL)
    approve_for_issue(version, actor=JOEL)
    proposal = create_proposal(estimate=estimate, version=version, template=_template())
    db.session.commit()
    text = _pdf_text(generate_proposal_pdf(proposal).getvalue())
    assert f"Brayman Project # {project.project_number}" in text and "Client Project # LB-0712" in text
    assert _project_reference(project) == f"Brayman Project # {project.project_number}"  # never the job name
    # The form's PROJECT box holds 52 characters: the Client # is added only when it fits (by design).
    assert project_label(project) == f"{project.name} · {project.project_number}"
    project.name = "Paulusse"
    assert project_label(project) == f"Paulusse · {project.project_number} · Client # LB-0712"
    from app.services.guided_internal_cost_pdf import render_internal_cost_pdf  # noqa: F401 - imported for the doc

    browser = _office(app)
    preview = browser.get(f"/proposals/{proposal.id}/preview").get_data(as_text=True)
    assert project.project_number in preview and "LB-0712" in preview
    breakdown = browser.get(f"/estimates/{estimate.id}/versions/{version.id}/internal-breakdown").get_data(as_text=True)
    assert project.project_number in breakdown and "Project pricing" in breakdown and "$46,996.85" in breakdown


# ============================================================================================ migration
def _config(db_path):
    cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def test_migration_numbers_existing_projects_in_creation_order_and_keeps_existing_numbers(tmp_path):
    path = tmp_path / "prior.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    with application.app_context():
        command.upgrade(_config(path), "a4d5e6f7a8b9")
    con = sqlite3.connect(path)
    con.execute("INSERT OR IGNORE INTO organizations (id, legal_name, display_name, primary_address, default_region, "
                "currency, tax_jurisdiction, is_active, created_at, updated_at) VALUES ('ORG-001', 'B', 'B', 'a', 'r', "
                "'CAD', 'ON', 1, '2026-08-28 00:00:00', '2026-08-28 00:00:00')")
    con.execute("INSERT INTO clients (id, name, organization_id, created_at) VALUES (1, 'C', 'ORG-001', '2026-09-01 00:00:00')")
    rows = [(27, "Slab", None, "2026-09-12 20:24:27"), (28, "Paulusse", None, "2026-10-28 07:51:16"),
            (29, "Typed", "JOB-7", "2026-10-01 00:00:00"), (30, "Shop", "COMPANY-TIME-ORG-001", "2026-10-02 00:00:00"),
            (31, "Old", None, "2025-12-30 00:00:00")]
    for pid, name, number, created in rows:
        con.execute("INSERT INTO projects (id, name, project_number, address, status, client_id, created_at, "
                    "organization_id, operating_state, operating_state_changed_at, drawing_requirement) VALUES "
                    "(?, ?, ?, '', 'Estimating', 1, ?, 'ORG-001', 'ACTIVE', ?, 'UNKNOWN')", (pid, name, number, created, created))
    con.commit()
    con.close()
    with application.app_context():
        command.upgrade(_config(path), "r5e6f7a8b9c0")
    con = sqlite3.connect(path)
    got = dict(con.execute("SELECT id, project_number FROM projects").fetchall())
    assert got == {27: "BC-2026-0001", 28: "BC-2026-0002", 29: "JOB-7", 30: "COMPANY-TIME-ORG-001", 31: "BC-2025-0001"}
    assert sorted(con.execute("SELECT organization_id, year, last_value FROM project_number_sequences").fetchall()) == [
        ("ORG-001", 2025, 1), ("ORG-001", 2026, 2)]
    assert con.execute("SELECT COUNT(*) FROM project_identity_events").fetchone()[0] == 3
    assert con.execute("SELECT COUNT(*) FROM projects WHERE client_project_number IS NOT NULL").fetchone()[0] == 0
    con.close()
