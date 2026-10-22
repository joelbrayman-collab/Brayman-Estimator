"""Useful Calculators: one collection of every existing calculator (Joel, 22 Oct 2026).

"ONE APPROVED ICON. ONE CALCULATOR COLLECTION. NO DUPLICATE ENGINES."

This module is only a catalogue. It names the calculators CalibraytAI already has, says who may open each one
and where, and never calculates anything itself. The calculators keep their own routes, engines and tests:

- Standalone quantity calculators (app/routes/calculators.py, listed in the office menu's Calculators section,
  app/navigation.py). They take measurements and give quantities; no project, estimate, cost, price, rate or
  company record is read or written. The Useful Calculators blueprint (app/routes/useful_calculators.py) serves
  the very same view functions under /useful-calculators/ with a phone layout, so the Home Screen app stays in
  its own scope. These are the calculators a Field-only worker may use.
- Office calculators that show company business numbers or need the office (Employment vs Entrepreneurship,
  the Supplier economic model): office members only, opened in the office.
- Project and estimate calculators (Add from calculation, labour hours, deck takeoff, construction information,
  construction drawings): they belong to one project or estimate and can show company costs, supplier prices
  or customer records, so they open only in the office, after choosing the project.

Public set (Joel, 22 Oct 2026: keep what is established): Concrete, Stairs and Employment vs Entrepreneurship,
already public on the website (calibraytai.com) from the same preserved engine packages. Signed out, the dashboard
links to those website pages; every other calculator needs a sign-in. No platform page was made public.

A Field-only worker sees the office entries named, with the reason they are not available, and nothing else:
no project, customer, cost or price ever appears on the dashboard for them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

PUBLIC_SITE = "https://calibraytai.com"

AUDIENCE_CREW = "crew"      # signed-in office members and Field-only workers
AUDIENCE_OFFICE = "office"  # signed-in office members only

FIELD_ONLY_REASON = ("Office only. It works with the company's own business numbers or job records, so it opens "
                     "in the office. Ask the office if you need a figure from it.")
PROJECT_REASON = ("Office only. These calculators belong to one job's office records and takeoff and can show "
                  "company and supplier numbers, so they open in the office after you choose the job.")


@dataclass(frozen=True)
class Calculator:
    key: str
    title: str
    description: str
    group: str                 # "Concrete and foundations", "Framing and stairs", ...
    audience: str              # AUDIENCE_CREW or AUDIENCE_OFFICE
    office_endpoint: str       # the existing route (also the office menu entry where there is one)
    phone_endpoint: str = ""   # the same view under /useful-calculators/ (crew calculators only)
    units: str = ""            # "Imperial or metric" where the calculator already offers both
    public_url: str = ""       # the same engine on the public website, for signed-out visitors


GROUP_CONCRETE = "Concrete and foundations"
GROUP_FRAMING = "Framing and stairs"
GROUP_FINISHES = "Roofing, siding and interiors"
GROUP_BUSINESS = "Business"

# Every calculator in the office menu (app/navigation.py "Calculators"), plus the office business tools.
# tests/test_useful_calculators.py checks this list covers every menu calculator and every calculators.* route.
CALCULATORS: Tuple[Calculator, ...] = (
    Calculator("concrete", "Concrete calculator", "Concrete for a standard slab or a slab with a thickened edge.",
               GROUP_CONCRETE, AUDIENCE_CREW, "calculators.concrete", "useful_calculators.concrete",
               "Imperial or metric", PUBLIC_SITE + "/useful-tools/concrete/"),
    Calculator("footing", "Footing calculator", "Concrete for rectangular footings, with waste.",
               GROUP_CONCRETE, AUDIENCE_CREW, "calculators.footing", "useful_calculators.footing",
               "Imperial or metric"),
    Calculator("wall-form", "ICF wall calculator", "Insulated concrete forms, corners and core concrete for a wall.",
               GROUP_CONCRETE, AUDIENCE_CREW, "calculators.wall_form", "useful_calculators.wall_form"),
    Calculator("stairs", "Stair calculator", "Ontario residential straight stair: risers, treads and stringer.",
               GROUP_FRAMING, AUDIENCE_CREW, "calculators.stairs", "useful_calculators.stairs",
               "Imperial or metric", PUBLIC_SITE + "/useful-tools/stairs/"),
    Calculator("wall-framing", "Wall framing calculator", "Studs, plates, openings and corners for one straight wall.",
               GROUP_FRAMING, AUDIENCE_CREW, "calculators.wall_framing", "useful_calculators.wall_framing"),
    Calculator("roofing", "Roofing calculator", "Roof area from plan size and pitch; shingle bundles and underlayment.",
               GROUP_FINISHES, AUDIENCE_CREW, "calculators.roofing", "useful_calculators.roofing",
               "Imperial or metric"),
    Calculator("siding", "Siding calculator", "Net wall area for siding, less openings, with gables.",
               GROUP_FINISHES, AUDIENCE_CREW, "calculators.siding", "useful_calculators.siding",
               "Imperial or metric"),
    Calculator("drywall", "Drywall calculator", "Board area and sheet count for walls and ceilings.",
               GROUP_FINISHES, AUDIENCE_CREW, "calculators.drywall", "useful_calculators.drywall",
               "Imperial or metric"),
    Calculator("flooring", "Flooring calculator", "Floor area and boxes for rooms.",
               GROUP_FINISHES, AUDIENCE_CREW, "calculators.flooring", "useful_calculators.flooring",
               "Imperial or metric"),
    Calculator("employment", "Employment vs Entrepreneurship",
               "Compare a job's pay with running your own business.",
               GROUP_BUSINESS, AUDIENCE_OFFICE, "calculators.employment_vs_entrepreneurship",
               public_url=PUBLIC_SITE + "/employment-vs-entrepreneurship/"),
    Calculator("supplier-model", "Supplier economic model",
               "The supplier program's numbers, for a discussion with a building supplier.",
               GROUP_BUSINESS, AUDIENCE_OFFICE, "supplier_program.economic_model"),
)
CALCULATOR_BY_KEY = {c.key: c for c in CALCULATORS}
GROUPS = (GROUP_CONCRETE, GROUP_FRAMING, GROUP_FINISHES, GROUP_BUSINESS)


@dataclass(frozen=True)
class ProjectTool:
    key: str
    title: str
    description: str
    scope: str        # "estimate" (needs an estimate version) or "project"
    endpoint: str
    id_arg: str = ""  # the URL argument naming the project ("project_id" or "id")


# The calculators that belong to one project or estimate (office only, opened in the office).
PROJECT_TOOLS: Tuple[ProjectTool, ...] = (
    ProjectTool("add-from-calculation", "Add from calculation",
                "ICF wall quantities, footing concrete and wall framing for this estimate.", "estimate",
                "estimates.calculation_list"),
    ProjectTool("icf-estimate", "ICF wall quantities", "The ICF wall calculator, sent to this estimate's review.",
                "estimate", "estimates.wall_form_quantities"),
    ProjectTool("footing-estimate", "Footing concrete", "The footing calculator, sent to this estimate's review.",
                "estimate", "estimates.footing_quantities"),
    ProjectTool("framing-estimate", "Wall framing", "The wall framing calculator, sent to this estimate's review.",
                "estimate", "estimates.framing_quantities"),
    ProjectTool("labour-hours", "Labour hours", "Labour hours for this estimate.", "estimate", "estimate_labour.hours"),
    ProjectTool("construction", "Construction information",
                "Levels, members and footings for the job; feeds the takeoff and drawings.", "project",
                "projects.construction_information", "id"),
    ProjectTool("deck-takeoff", "Deck takeoff", "The pool-deck material takeoff and supplier request.", "project",
                "deck_takeoff.review", "project_id"),
    ProjectTool("drawings", "Construction drawings", "Drawing sets generated from the construction information.",
                "project", "construction_drawings.index", "project_id"),
)


def viewer_kind(user, organization_id: Optional[str]) -> str:
    """"signed_out", "office", "field_only" or "other" (a supplier login, or no contractor membership)."""
    if user is None or not getattr(user, "is_authenticated", False):
        return "signed_out"
    from app.services.supplier_hub import principal_class

    if principal_class(user) != "CONTRACTOR" or not organization_id:
        return "other"
    from app.services.access_domains import user_is_field_only

    return "field_only" if user_is_field_only(user, organization_id) else "office"


def may_open(calculator: Calculator, kind: str) -> bool:
    if kind == "office":
        return True
    if kind == "field_only":
        return calculator.audience == AUDIENCE_CREW
    return False


def dashboard(kind: str) -> List[dict]:
    """The dashboard's groups for one kind of viewer. Signed-out visitors get the public calculators."""
    out = []
    for group in GROUPS:
        items = []
        for calc in (c for c in CALCULATORS if c.group == group):
            entry = {"calc": calc, "state": "open", "reason": ""}
            if kind in ("office", "field_only"):
                if not may_open(calc, kind):
                    entry.update(state="restricted", reason=FIELD_ONLY_REASON)
                elif calc.audience == AUDIENCE_OFFICE:
                    entry["state"] = "office"  # opens in the office, in a new tab
            elif calc.public_url:
                entry["state"] = "public"  # the public website's page (the same preserved engine)
            else:
                entry.update(state="sign_in")
            items.append(entry)
        out.append({"title": group, "items": items})
    return out


def project_tool_links(organization_id: str):
    """For the office: each current job with the project and estimate calculators that apply to it. Names
    only: no amounts. Estimate tools use the estimate's current version (or its latest)."""
    from flask import url_for

    from app.models.estimate import Estimate, EstimateVersion
    from app.services.shared_api import list_current_operating_projects

    rows = []
    for project in list_current_operating_projects(organization_id):
        project_links = [{"tool": t, "url": url_for(t.endpoint, **{t.id_arg: project.id})}
                         for t in PROJECT_TOOLS if t.scope == "project"]
        estimates = []
        for estimate in (Estimate.query.filter_by(organization_id=organization_id, project_id=project.id)
                         .order_by(Estimate.id.desc()).all()):
            version = None
            if estimate.current_version_id:
                version = EstimateVersion.query.filter_by(id=estimate.current_version_id,
                                                          estimate_id=estimate.id).first()
            if version is None:
                version = (EstimateVersion.query.filter_by(estimate_id=estimate.id)
                           .order_by(EstimateVersion.version_number.desc()).first())
            if version is None:
                continue
            estimates.append({
                "estimate": estimate, "version": version,
                "links": [{"tool": t, "url": url_for(t.endpoint, id=estimate.id, version_id=version.id)}
                          for t in PROJECT_TOOLS if t.scope == "estimate"],
            })
        rows.append({"project": project, "links": project_links, "estimates": estimates})
    return rows
