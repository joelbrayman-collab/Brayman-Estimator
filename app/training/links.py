"""Buttons that take a trainee from a lesson step to the page or calculator the step is about (23 Oct 2026).

Joel: "Anywhere CalibraytAI says 'fill something in' the appropriate calculator needs to be readily accessible with
a button that says 'complete this page' or something to that effect."

The table below is explicit (lesson key, step number from 1) so every button can be reviewed. A button is shown only
when the page it points to can be found for this trainee on the training site (for example the Harbour Lane job in
their own company, or the supplier request that was sent to their own store). Otherwise the step shows no button and
nothing is invented. The buttons open in a new tab on the same training site, so the lesson, the ticks and the
trainee's place stay where they are.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from flask import url_for

JOB_NAME = "Harbour Lane Pool Deck (training)"


@dataclass(frozen=True)
class Link:
    label: str
    kind: str            # route | project | supplier | share | quote | estimate
    endpoint: str
    arg: str = "project_id"   # the URL argument the project id fills (kind == project)
    fragment: str = ""
    focus: str = "first"      # the field to put the cursor in: a field name or id, or "first" (first field on the page)


CALC = Link("Open the concrete calculator", "route", "calculators.concrete", focus="length")
CALC_PICK = Link("Open the concrete calculator", "route", "calculators.concrete", focus="variant")


def _page(endpoint, label="Complete this page"):
    return Link(label, "route", endpoint)


def _job(endpoint, label="Complete this page", arg="project_id", fragment=""):
    return Link(label, "project", endpoint, arg, fragment)


def _sup(endpoint, label="Complete this page"):
    return Link(label, "supplier", endpoint)


def _share(label="Complete this quote page"):
    return Link(label, "share", "supplier_portal.request_detail")


# (lesson key, step number) -> buttons, in the order shown.
STEP_LINKS: Dict[Tuple[str, int], Tuple[Link, ...]] = {
    # ---- Contractor
    ("c02-company-brand", 2): (_page("settings.brand_profile", "Complete the brand profile"),),
    ("c02-pricing-hst", 2): (_page("pricing_engine.create_policy", "Complete the pricing draft"),),
    ("c02-people", 2): (_page("people_access.new", "Complete the Add a person page"),),
    ("c02-crews", 2): (_page("organization_crew.new", "Complete the Add crew page"),),
    ("c04-invoices", 3): (_job("accounting.new_invoice", "Complete the invoice page"),),
    ("c04-bills-and-check", 3): (_page("accounting.reconcile", "Open Check QuickBooks"),),
    ("c05-appointments", 2): (_page("schedule.new_appointment", "Complete the appointment page"),),
    ("c05-appointments", 4): (_page("schedule.new_appointment", "Complete the appointment page"),),
    ("c06-clients", 2): (_page("clients.create_client", "Complete the New Client page"),),
    ("c06-project-setup", 2): (_job("projects.edit_project_location", "Complete the job location", arg="id"),),
    ("c06-existing-jobs", 1): (_page("projects.create_project", "Complete the New Project page"),),
    ("c06-existing-jobs", 2): (_page("projects.create_project", "Complete the New Project page"),),
    ("c07-plans", 2): (_job("plan_intelligence.upload_plan", "Complete the plan upload page"),),
    ("c07-concrete-calculator", 1): (CALC_PICK,),
    ("c07-concrete-calculator", 2): (CALC,),
    ("c07-deck-takeoff", 2): (_job("deck_takeoff.review", "Complete the product facts page"),),
    ("c08-suppliers", 2): (_page("supplier_office.suppliers", "Complete the Suppliers page"),),
    ("c08-suppliers", 3): (_page("supplier_office.suppliers", "Complete the Suppliers page"),),
    ("c08-concrete-request", 2): (CALC, Link("Complete the concrete request", "project", "supplier_office.project_requests",
                                             fragment="concrete", focus="volume_m3")),
    ("c08-place-order", 1): (_job("supplier_office.project_requests", "Complete the order page"),),
    ("c09-new-estimate", 2): (_page("estimates.create_estimate_route", "Complete the New Estimate page"),),
    ("c09-new-estimate", 4): (Link("Complete the estimate page", "estimate", "estimates.view_version"),),
    ("c09-new-estimate", 5): (Link("Complete the estimate page", "estimate", "estimates.view_version"),),
    ("c09-scope-delivery-costing", 2): (_job("scope_delivery.review", "Complete the Scope Delivery Review"),),
    ("c10-proposal-template", 2): (_page("proposal_templates.create_template", "Complete the template page"),),
    ("c11-schedule-crew", 2): (_job("work_structure.project_work_plan", "Complete the project work page"),),
    ("c11-schedule-crew", 3): (_job("work_structure.project_work_plan", "Complete the project work page"),),
    ("c11-schedule-crew", 5): (_page("schedule.new_item", "Complete the Set dates page"),),
    ("c11-capture", 1): (_job("field.capture", "Open Capture"),),
    ("c11-extra-work", 1): (_job("field.extra_work", "Complete the Extra work page"),),
    ("c11-field-time", 1): (_job("field.time_entry", "Complete the time page"),),
    ("c11-office-review", 4): (_job("supplier_office.project_requests", "Open the concrete request"),),
    ("c11-change-order", 2): (_page("project_controls.create_change_order_route", "Complete the New Change Order page"),),
    ("c12-invoice-closeout", 2): (_job("accounting.new_invoice", "Complete the invoice page"),),
    # ---- Field Crew
    ("f05-send-time", 1): (_job("field.time_entry", "Complete the time page"),),
    ("f05-send-time", 3): (_job("field.time_entry", "Complete the time page"),),
    ("f05-extra-work", 2): (_job("field.extra_work", "Complete the Extra work page"),),
    ("f06-capture", 2): (_job("field.capture", "Open Capture"),),
    ("f06-capture", 3): (_job("field.capture", "Open Capture"),),
    # ---- Supplier
    ("s02-texts", 2): (_page("supplier_portal.account", "Complete the text settings"),),
    ("s02-texts", 3): (_page("supplier_portal.account", "Complete the text settings"),),
    ("s04-material-quote", 1): (_share(),),
    ("s04-material-quote", 2): (_share(),),
    ("s04-material-quote", 3): (_share(),),
    ("s04-concrete-quote", 3): (_share(),),
    ("s05-confirm", 1): (_share("Complete the order page"),),
    ("s05-confirm", 3): (_share("Complete the order page"),),
    ("s06-ask-change", 1): (_share("Complete the delivery change"),),
    ("s06-delivered", 1): (_share("Complete the delivery page"),),
    ("s07-sku-reuse", 3): (_share(),),
    ("s08-what-exists", 1): (_share(),),
    ("s08-settings", 1): (_sup("supplier_pro_desk.settings", "Complete the Quote settings page"),),
    ("s08-price-file", 2): (_sup("supplier_pro_desk.prices", "Complete the price file page"),),
    ("s08-standards-matches", 1): (_sup("supplier_pro_desk.standards", "Complete the standard building page"),),
    ("s08-standards-matches", 3): (Link("Complete the quotation page", "quote", "supplier_pro_desk.quote"),),
    ("s09-quick-quote", 3): (_sup("supplier_pro_desk.quick", "Complete the Quick Quote page"),),
    ("s09-quick-quote", 4): (_sup("supplier_pro_desk.quick", "Complete the Quick Quote page"),),
    ("s09-quick-quote", 6): (_sup("supplier_pro_desk.new_quote", "Complete the Detailed quotation page"),),
    ("s09-price-issue", 3): (Link("Complete the quotation page", "quote", "supplier_pro_desk.quote"),),
    ("s10-pro-desk-cycle", 1): (_sup("supplier_pro_desk.quick", "Complete the Quick Quote page"),),
}


def _project_id(trainee) -> Optional[int]:
    if not trainee.organization_id:
        return None
    from app.models.project import Project

    row = (Project.query.filter_by(organization_id=trainee.organization_id, name=JOB_NAME)
           .order_by(Project.id.asc()).first())
    return row.id if row else None


def _resolve(link: Link, trainee, cache: dict) -> Optional[str]:
    try:
        if link.kind == "route":
            return url_for(link.endpoint)
        if link.kind == "project":
            if "project" not in cache:
                cache["project"] = _project_id(trainee)
            if not cache["project"]:
                return None
            url = url_for(link.endpoint, **{link.arg: cache["project"]})
            return url + ("#" + link.fragment if link.fragment else "")
        if link.kind == "supplier":
            return url_for(link.endpoint, supplier_id=trainee.supplier_id) if trainee.supplier_id else None
        if link.kind == "share":
            if not trainee.supplier_id:
                return None
            from app.models.supplier_portal import SupplierRequestShare

            row = (SupplierRequestShare.query.filter_by(supplier_id=trainee.supplier_id)
                   .order_by(SupplierRequestShare.id.desc()).first())
            return url_for(link.endpoint, supplier_id=trainee.supplier_id, share_id=row.id) if row else None
        if link.kind == "quote":
            if not trainee.supplier_id:
                return None
            from app.models.supplier_quote import SupplierQuote

            row = SupplierQuote.query.filter_by(supplier_id=trainee.supplier_id).order_by(SupplierQuote.id.desc()).first()
            return url_for(link.endpoint, supplier_id=trainee.supplier_id, quote_id=row.id) if row else None
        if link.kind == "estimate":
            if "project" not in cache:
                cache["project"] = _project_id(trainee)
            if not cache["project"]:
                return None
            from app.models.estimate import Estimate, EstimateVersion

            est = (Estimate.query.filter_by(organization_id=trainee.organization_id, project_id=cache["project"])
                   .order_by(Estimate.id.desc()).first())
            ver = (EstimateVersion.query.filter_by(estimate_id=est.id).order_by(EstimateVersion.id.desc()).first()
                   if est else None)
            return url_for(link.endpoint, id=est.id, version_id=ver.id) if ver else None
    except Exception:  # a link that cannot be built is simply not shown
        return None
    return None


def _with_return(url: str, lesson_key: str, number: int, focus: str) -> str:
    """Add the way back to this lesson step and the field to put the cursor in. The page, wherever it is on the
    training site, then shows a one-click 'Back to the lesson step' (see training/_site_bar.html)."""
    from urllib.parse import quote

    base, _hash, fragment = url.partition("#")
    back = quote(f"/training/lessons/{lesson_key}?step={number - 1}#step-{number}", safe="")
    sep = "&" if "?" in base else "?"
    out = f"{base}{sep}tc_back={back}&tc_focus={quote(focus, safe='')}"
    return out + ("#" + fragment if fragment else "")


def links_for_lesson(lesson_key: str, trainee) -> Dict[int, List[Tuple[str, str]]]:
    """{zero-based step index: [(label, url), ...]} for the buttons that can be built for this trainee."""
    out: Dict[int, List[Tuple[str, str]]] = {}
    cache: dict = {}
    for (key, number), links in STEP_LINKS.items():
        if key != lesson_key:
            continue
        built = []
        for link in links:
            url = _resolve(link, trainee, cache)
            if url:
                built.append((link.label, _with_return(url, lesson_key, number, link.focus)))
        if built:
            out[number - 1] = built
    return out
