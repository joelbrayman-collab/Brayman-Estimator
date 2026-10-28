"""Test-only helpers for Guided Estimating (23 Oct 2026): the synthetic company, its costs and an HTTP driver.

Everything goes through the real pages and services. Nothing here sets a cost, approves a quote or completes a
stage behind the application's back; the helpers press the same buttons a person presses.
"""

from __future__ import annotations

import re
from decimal import Decimal

from app import db
from app.models import Client, CostItem, Project
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

# The brief's required acceptance example: New Home / General Contractor, these 14 responsibilities exactly.
NEW_HOME_SCOPE = {
    "site_prep": "SUBCONTRACTED",
    "excavation": "SUBCONTRACTED",
    "footings_foundation": "INTERNAL",
    "framing": "INTERNAL",
    "roofing": "SUBCONTRACTED",
    "windows_doors": "INTERNAL",
    "siding": "SUBCONTRACTED",
    "electrical": "SUBCONTRACTED",
    "plumbing": "SUBCONTRACTED",
    "hvac": "SUBCONTRACTED",
    "insulation": "SUBCONTRACTED",
    "drywall": "SUBCONTRACTED",
    "interior_finishes": "INTERNAL",
    "final_cleanup": "INTERNAL",
}
NEW_HOME_NAMES = ["Site preparation", "Excavation", "Footings & foundation", "Framing", "Roofing",
                  "Windows & exterior doors", "Siding & exterior finishes", "Electrical", "Plumbing", "HVAC",
                  "Insulation", "Drywall", "Interior finishes", "Final cleanup"]

COMMERCIAL = {"project_type": "New Build", "pricing_posture": "Fair Market", "execution_risk": "Normal",
              "schedule_condition": "Normal", "site_condition": "Normal", "estimate_stage": "Preliminary",
              "delivery_model": "Mixed"}

COST_ITEMS = (
    # code, name, unit, unit cost: synthetic company costs (what we pay), matched by unit in the estimate review
    ("SYN-CONC-YD3", "Ready-mix concrete 25 MPa (synthetic)", "yd3", "210.00"),
    ("SYN-CONC-M3", "Ready-mix concrete 25 MPa per m3 (synthetic)", "m3", "275.00"),
    ("SYN-STUD-EA", "2x6 stud 92-5/8 in (synthetic)", "ea", "7.25"),
    ("SYN-FLOOR-FT2", "Engineered flooring (synthetic)", "ft2", "4.10"),
)


def seed_company():
    """The synthetic company's cost library, labour rate and pricing policy (as Getting Started leaves them)."""
    from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
    from tests.proposal_issue_support import ensure_default_pricing_policy

    ensure_org_001_direct_labour_cost_rate_standard()
    for code, name, unit, cost in COST_ITEMS:
        if CostItem.query.filter_by(organization_id=ORG, code=code).first() is None:
            db.session.add(CostItem(code=code, name=name, category="Material", unit=unit, unit_cost=Decimal(cost),
                                    default_markup_percent=Decimal("0"), organization_id=ORG, is_active=True))
    db.session.commit()
    ensure_default_pricing_policy(ORG)


def client(name="Jordan Avery (synthetic)"):
    row = Client.query.filter_by(organization_id=ORG, name=name).first()
    if row is None:
        row = Client(name=name, organization_id=ORG, email="jordan.avery@example.invalid")
        db.session.add(row)
        db.session.commit()
    return row


def cost_item(code):
    return CostItem.query.filter_by(organization_id=ORG, code=code).one()


class _FreshClient:
    """The test client, with the signed-in person looked up afresh on every request.

    The tests keep one application context open (to read the database between requests), and Flask reuses it
    for each request, so Flask-Login's cached user would otherwise follow from one person's client to another's.
    """

    def __init__(self, client):
        self._client = client

    def _fresh(self):
        from flask import g

        for key in ("_login_user", "organization_id", "field_only"):
            g.pop(key, None)

    def get(self, *args, **kwargs):
        self._fresh()
        return self._client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._fresh()
        return self._client.post(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._client, name)


class Driver:
    """Press the guided-estimating buttons through the HTTP client."""

    def __init__(self, http):
        self.http = _FreshClient(http)

    def get(self, url, status=200):
        response = self.http.get(url)
        assert response.status_code == status, (url, response.status_code, response.get_data(as_text=True)[-1500:])
        return response.get_data(as_text=True)

    def post(self, url, data=None, json=None, status=302):
        response = self.http.post(url, data=data, json=json)
        assert response.status_code == status, (url, response.status_code, response.get_data(as_text=True)[-1500:])
        return response

    def flashes(self):
        with self.http.session_transaction() as session:
            return [m for _c, m in session.get("_flashes", [])]

    # -- project and scope
    def new_project(self, name, project_type, role, *, carry=None, client_row=None, legacy=True):
        """A project and its scope. ``legacy`` (the default for the v1rel9 acceptance tests): the stage-template
        scope every estimate had before 28 Oct 2026, made directly by the engine as a fixture for estimates that
        already exist — the product starts every new scope as selected work (tests/test_selected_work.py)."""
        data = dict(COMMERCIAL, name=name, client_id=(client_row or client()).id, guided_project_type=project_type,
                    contractor_role=role)
        if not legacy:
            data["start_guided"] = "1"
        if carry:
            data["carry"] = carry
        response = self.post("/projects/new", data=data)
        project = Project.query.filter_by(organization_id=ORG, name=name).one()
        if legacy:
            from app.services.guided_estimating import get_guided, start_guided_estimate

            if get_guided(ORG, project.id) is None:
                start_guided_estimate(organization_id=ORG, project_id=project.id, project_type=project_type,
                                      contractor_role=role, actor="Ben Brayman (synthetic)", legacy_stages=True)
            return project, f"/projects/{project.id}/guided/scope"
        return project, response.headers["Location"]

    def scope(self, project, decisions, *, split=(), action="save", na_reasons=None, status=302):
        from app.services.guided_estimating import get_guided

        guided = get_guided(ORG, project.id)
        data = {"action": action}
        by_key = {s.stage_key: s for s in guided.stages}
        for key, value in decisions.items():
            data[f"resp_{by_key[key].id}"] = value
        for key, reason in (na_reasons or {}).items():
            data[f"na_reason_{by_key[key].id}"] = reason
        data["split"] = [str(by_key[k].id) for k in split]
        return self.post(f"/projects/{project.id}/guided/scope", data=data, status=status)

    def stage(self, project, key):
        from app.services.guided_estimating import get_guided

        guided = get_guided(ORG, project.id)
        return next(s for s in guided.stages if s.stage_key == key)

    def action(self, project, stage, action, data=None, status=302):
        return self.post(f"/projects/{project.id}/guided/stages/{stage.id}/{action}", data=data or {}, status=status)

    # -- Option B through the calculator page and the estimate review
    def calculator_result(self, slug, form):
        """POST a server calculator and return its Contract V1 payload (as the page carries it)."""
        html = self.post(f"/calculators/{slug}", data=form, status=200).get_data(as_text=True)
        match = re.search(r'<script type="application/json" data-calculator-contract>(.*?)</script>', html, re.S)
        assert match, f"{slug}: no Contract V1 result on the page"
        import json

        return json.loads(match.group(1)), html

    def link(self, project, calculator, payload, *, stage=None, summary=None, status=200):
        body = {"calculator": calculator, "project_id": project.id, "summary": summary or f"{calculator} result",
                "entered": [{"label": i["code"], "value": f"{i['value']} {i['unit_code']}"} for i in payload["inputs"]],
                "result_text": "\n".join(f"{q['code']} {q['quantity']} {q['unit_code']}" for q in payload["quantities"]),
                "payload": payload, "stage_id": stage.id if stage is not None else None}
        response = self.http.post("/calculators/link-project", json=body)
        assert response.status_code == status, response.get_data(as_text=True)
        return response.get_json()

    def send_to_review(self, project, calculation_id, stage=None):
        data = {"stage_id": stage.id} if stage is not None else {}
        response = self.post(f"/projects/{project.id}/calculations/{calculation_id}/send", data=data)
        return response.headers["Location"]

    def confirm_quantities(self, review_url, code_to_cost_item, section_id):
        """In the estimate review, confirm the chosen quantities against company costs (a person's choices)."""
        from app.models.calculation_estimate_mapping import CalculationQuantityReview

        match = re.search(r"/estimates/(\d+)/versions/(\d+)/calculations/(\d+)", review_url)
        estimate_id, version_id, intake_id = map(int, match.groups())
        page = self.get(review_url)
        assert "Add to this estimate" in page
        done = 0
        for review in CalculationQuantityReview.query.filter_by(intake_id=intake_id).all():
            code = code_to_cost_item.get(review.quantity_code)
            if code is None:
                continue
            self.post(f"/estimates/{estimate_id}/versions/{version_id}/calculations/quantities/{review.id}/confirm",
                      data={"intake_id": intake_id, "section_id": section_id, "target": f"cost_item:{cost_item(code).id}",
                            "confirmed_quantity": review.quantity_text, "return_to": "/projects/1/guided"})
            done += 1
        return done
