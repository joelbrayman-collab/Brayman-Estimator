"""Change it on the fly (Joel, 2 Nov 2026): the Paulusse REV9 decision, with synthetic data.

The client answered the quote: the stone went to someone else (By others), their budget for soffit, fascia and
aluminum trim is $8,800 plus the lift billed at cost, and the siding stays as quoted. Per package on the working
version: By others (the existing exclusion), a client budget / fixed price, a pass-through at cost; a live P&L on
Review This Estimate; the summary PDF shows the scenario exactly; the budget is spread over the package's lines for
the customer price; approved and sent versions never change (each price sent is kept as REV1, REV2, ...).
"""

from __future__ import annotations

import json
import re
from decimal import Decimal as D

import pytest

from app import db
from app.models import EstimateVersion, Proposal
from app.models.documents import Document, DocumentLink
from app.models.estimate_approval import EstimateApproval
from app.services import guided_estimating as G
from app.services import internal_financial_summary as IFS
from app.services import package_scenario as PS
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.test_guided_tasks import _project, _template
from tests.test_internal_financial_summary import WORKER_A, WORKER_B, _add_employee, _approve_form, _pdf_text, env  # noqa: F401

# Joel's approved REV9 figures, held in the test itself so it needs no file outside the repository.
REV9_EXPECT = {"rev": "$40,693.52", "cost": "$28,192.12", "profit": "$12,501.40", "mat": "$14,944.60"}
# The reference's lines (synthetic copy of the REV9 structure: quantities x prices, person-hours, equipment).
HARDIE_MATERIALS = [("HardiePanel vertical siding", 61, "118.00"), ("HardieTrim batten", 121, "25.68"),
                    ("Siding nails", 3, "72.00"), ("Z flashing", 22, "18.00"), ("Sealant", 24, "9.00"),
                    ("Touch-up kit", 1, "52.00"), ("Delivery of materials", 1, "150.00")]
HARDIE_HOURS = ["8.80", "4.40", "8.80", "8.80", "68.33", "24.07", "13.20", "39.60"]  # 176.00 h
HARDIE_EQUIPMENT = [("Staging rental", "650.00"), ("Cutting blades & consumables", "200.00")]
ALUMINUM_MATERIALS = [("Corner trim", 14, "38.98"), ("Window trim", 19, "28.98"), ("Door / garage trim", 11, "27.87"),
                      ("Window drip cap", 8, "10.92"), ("Freeze boards", 12, "27.88"), ("Trim nails", 4, "17.98"),
                      ("Vented soffit", 28, "27.74"), ("Fascia", 29, "22.37"), ("Soffit J-channel", 29, "7.28"),
                      ("Soffit fasteners", 2, "38.00")]
ALUMINUM_HOURS = ["22.00", "6.33", "1.93", "4.59", "11.00", "5.78", "22.83"]  # 74.46 h


def _add(d, project, stage, **data):
    d.post(f"/projects/{project.id}/guided/stages/{stage.id}/add_cost", data=data)


def _paulusse(d):
    project = _project(d, "Synthetic 3 Kingfisher (Paulusse REV9 mirror)")
    d.post(f"/projects/{project.id}/guided/scope",
           data={"action": "add_work", "work": ["work_siding", "work_soffit_fascia", "work_painting"]})
    guided = G.get_guided(ORG, project.id)
    stages = {s.stage_key.replace("work_", ""): s for s in guided.top_stages}
    hardie, aluminum, stone = stages["siding"], stages["soffit_fascia"], stages["painting"]
    for name, qty, price in HARDIE_MATERIALS:
        _add(d, project, hardie, kind="material", description=name, quantity=str(qty), unit="ea", unit_cost=price)
    for i, hours in enumerate(HARDIE_HOURS, 1):
        _add(d, project, hardie, kind="labour", description=f"Siding activity {i}", quantity=hours)
    for name, cost in HARDIE_EQUIPMENT:
        _add(d, project, hardie, kind="equipment", description=name, quantity="1", unit="ls", unit_cost=cost)
    for name, qty, price in ALUMINUM_MATERIALS:
        _add(d, project, aluminum, kind="material", description=name, quantity=str(qty), unit="ea", unit_cost=price)
    for i, hours in enumerate(ALUMINUM_HOURS, 1):
        _add(d, project, aluminum, kind="labour", description=f"Aluminum activity {i}", quantity=hours)
    _add(d, project, stone, kind="material", description="Stone veneer and sills (synthetic)", quantity="1",
         unit="ls", unit_cost="4952.72")
    for stage in (hardie, aluminum, stone):
        d.post(f"/projects/{project.id}/guided/stages/{stage.id}/routing")
        d.post(f"/projects/{project.id}/guided/stages/{stage.id}/complete_next")
    db.session.expire_all()
    return project, G.get_guided(ORG, project.id), hardie, aluminum, stone


def _scenario(d, project, rows, reason="Client counter-offer (synthetic)"):
    data = {"reason": reason}
    for stage, by_others, budget, label in rows:
        data[f"present_{stage.id}"] = "1"
        if by_others:
            data[f"by_others_{stage.id}"] = "1"
            data[f"party_{stage.id}"] = "NAMED"
            data[f"party_name_{stage.id}"] = "Lockwood (synthetic)"
        data[f"budget_{stage.id}"] = budget
        data[f"budget_label_{stage.id}"] = label
    d.post(f"/projects/{project.id}/guided/scenario", data=data)


def _crew(d, project):
    a = _add_employee(d, WORKER_A)
    b = _add_employee(d, WORKER_B)
    d.post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id), str(b.id)]})
    return a, b


def test_the_paulusse_rev9_decision_reproduces_joels_figures(env):
    _app, c, _users = env
    d = c["owner"]
    project, guided, hardie, aluminum, stone = _paulusse(d)
    _crew(d, project)
    # The live preview before any decision: the aluminum package at its internal price.
    sc = PS.scenario_rows(G.current_version(guided), [{"loaded_rate": "55.77", "share": 1},
                                                      {"loaded_rate": "31.25", "share": 1}])
    alu = next(r for r in sc["rows"] if r["stage_id"] == aluminum.id)
    assert alu["internal_price"] == D("10203.06")  # 3,609.32 / 0.85 + 74.46 h x $80 (no lift yet)
    # Ben's decision.
    d.post(f"/projects/{project.id}/guided/passthrough",
           data={"stage_id": aluminum.id, "description": "Genie lift (synthetic)", "amount": "1500"})
    assert not [m for m in d.flashes() if "Not" in m]
    _scenario(d, project, [(hardie, False, "30393.52", "Nov 1 quote"), (aluminum, False, "8800", "client budget"),
                           (stone, True, "", "")])
    flashes = d.flashes()
    assert any("Scenario saved" in m for m in flashes), flashes
    db.session.expire_all()
    version = G.current_version(G.get_guided(ORG, project.id))
    assert PS.budgets(version) == {f"stage:{hardie.id}": D("30393.52"), f"stage:{aluminum.id}": D("8800.00")}
    # The live P&L: the aluminum internal price against the $10,300 budget, still $1,950.93 profit at real cost.
    page = d.get(f"/projects/{project.id}/guided/pricing")
    assert "data-live-pl" in page
    row = re.search(rf'<tr data-pl-row="stage:{aluminum.id}".*?</tr>', page, re.S).group(0)
    assert "$11,703.06" in row and "$10,300.00" in row and "$1,950.93" in row
    assert "$40,693.52" in page and "$12,501.40" in page
    # The summary reflects the scenario exactly.
    data = IFS.build_data(version)
    totals = IFS.totals(data)
    assert totals["revenue"] == D("40693.52")
    assert totals["cost"] == D("28192.12") and totals["profit"] == D("12501.40")
    assert totals["materials"] == D("14944.60") and totals["labour_cost"] == D("10897.52")
    assert totals["equipment"] == D("2350.00")
    labels = [r["label"] for p in data["packages"] for r in p["revenue"]]
    assert any("(client budget)" in l for l in labels) and any("(Nov 1 quote)" in l for l in labels)
    assert "Genie lift (synthetic) (billed at cost)" in labels
    assert data["excluded"] == [{"name": stone.display_name, "responsible": "Lockwood (synthetic)",
                                 "quoted": "5826.73"}]
    text = "\n".join(_pdf_text(IFS.render_pdf(data)))
    assert "EXCLUDED / BY OTHERS" in text and "we had quoted $5,826.73" in text and "$40,693.52" in text
    # The reference file's expected figures, for the record.
    expect = REV9_EXPECT
    assert (IFS.m(totals["revenue"]), IFS.m(totals["cost"]), IFS.m(totals["profit"]), IFS.m(totals["materials"])) == (
        expect["rev"], expect["cost"], expect["profit"], expect["mat"])


def test_a_budget_is_spread_over_its_lines_and_the_customer_price_agrees(env):
    _app, c, _users = env
    _template()
    d = c["owner"]
    project, guided, hardie, aluminum, stone = _paulusse(d)
    d.post(f"/projects/{project.id}/guided/passthrough",
           data={"stage_id": aluminum.id, "description": "Genie lift (synthetic)", "amount": "1500"})
    _scenario(d, project, [(hardie, False, "", ""), (aluminum, False, "8800", "client budget"), (stone, True, "", "")])
    values = _approve_form(d.get(f"/projects/{project.id}/guided/pricing"))
    d.post(f"/projects/{project.id}/guided/approve", data=values)
    db.session.expire_all()
    version = db.session.get(EstimateVersion, int(values["version_id"]))
    from app.services.work_packages import package_lines

    alu_lines = package_lines(aluminum, version)
    lift = [l for l in alu_lines if PS.is_passthrough(l)]
    assert len(lift) == 1 and lift[0].sell_price == D("1500.00")  # billed at cost
    assert sum(l.sell_price for l in alu_lines if not PS.is_passthrough(l)) == D("8800.00")
    assert all(l.sell_price == 0 for l in package_lines(stone, version))  # by others: out of the price
    snapshot = version.pricing_snapshot
    assert snapshot.pre_tax_selling_price == sum(l.sell_price for s in version.sections for l in s.line_items)
    proposal = Proposal.query.filter_by(estimate_version_id=version.id).one()
    assert proposal.subtotal == snapshot.pre_tax_selling_price
    # Gate 1 froze the scenario: the version is locked and a budget cannot be changed on it.
    with pytest.raises(PS.PackageScenarioError, match="never changes"):
        PS.set_budget(version, f"stage:{aluminum.id}", "9000", actor="Owner Synthetic")
    frozen = EstimateApproval.query.one().summary["internal_financial_summary"]
    assert any(p.get("budget") == "8800.00" for p in frozen["packages"])


def test_every_price_sent_is_kept_as_a_revision_and_the_next_revision_carries_the_decisions(env):
    from app.services.proposal_acceptance import send_proposal_to_client

    _app, c, users = env
    _template()
    d = c["owner"]
    project, guided, hardie, aluminum, stone = _paulusse(d)
    _scenario(d, project, [(aluminum, False, "8800", "client budget")])
    values = _approve_form(d.get(f"/projects/{project.id}/guided/pricing"))
    response = d.post(f"/projects/{project.id}/guided/approve", data=values)
    db.session.expire_all()
    v1 = db.session.get(EstimateVersion, int(values["version_id"]))
    proposal = Proposal.query.filter_by(estimate_version_id=v1.id).one()
    send_proposal_to_client(proposal, user=users["owner"], client_name="Client Synthetic",
                            client_email="client@example.invalid")
    revisions = IFS.quoted_revisions(v1.estimate)
    assert [(r["label"], r["version"].id) for r in revisions] == [("REV1", v1.id)]
    sent = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
            .filter(Document.document_type == "INTERNAL_FINANCIAL_SUMMARY", DocumentLink.record_kind == "PROPOSAL",
                    DocumentLink.record_id == proposal.id).one())
    assert "REV1 sent to client" in sent.title
    page = d.get(f"/projects/{project.id}/guided/pricing")
    assert "data-scenario-locked" in page and "REV1" in page and "data-save-scenario" not in page
    # The client counters: the next revision is the working copy; REV1 stays exactly as sent.
    rev1_total = v1.pricing_snapshot.customer_total
    G.start_revision(G.get_guided(ORG, project.id), reason="Client countered (synthetic)", actor="Owner Synthetic")
    db.session.expire_all()
    v2 = G.current_version(G.get_guided(ORG, project.id))
    assert v2.id != v1.id and PS.budgets(v2) == {f"stage:{aluminum.id}": D("8800.00")}
    PS.set_budget(v2, f"stage:{aluminum.id}", "9300", actor="Owner Synthetic", reason="Counter (synthetic)")
    db.session.expire_all()
    assert db.session.get(EstimateVersion, v1.id).pricing_snapshot.customer_total == rev1_total
    assert PS.budgets(db.session.get(EstimateVersion, v1.id)) == {f"stage:{aluminum.id}": D("8800.00")}


def test_budgets_need_the_labour_at_rate_method_and_refuse_bad_amounts(env):
    _app, c, _users = env
    d = c["owner"]
    project, guided, hardie, aluminum, stone = _paulusse(d)
    version = G.current_version(guided)
    with pytest.raises(PS.PackageScenarioError, match="negative"):
        PS.set_budget(version, f"stage:{aluminum.id}", "-1", actor="Owner Synthetic")
    version.pricing_method = "TRUE_GROSS_MARGIN"
    with pytest.raises(PS.PackageScenarioError, match="pricing method"):
        PS.set_budget(version, f"stage:{aluminum.id}", "8800", actor="Owner Synthetic")
    db.session.rollback()
    c["staff"].post(f"/projects/{project.id}/guided/scenario", data={f"present_{aluminum.id}": "1"}, status=403)
