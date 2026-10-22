"""The single authoritative CalibraytAI workflow definition (Joel, 21 Oct 2026).

Every Workflow Map reads this module and nothing else: the contractor office Workflow Guide (/workflow), the
Supplier Hub Workflow Guide (/supplier/<id>/workflow), the Field workflow (/field/workflow) and the Training
& Acceptance Centre's Workflow map (/training/workflow). There is no second copy of the stages.

What it holds, per stage: identifier, number, label, title, description, the substeps with their real
application destinations (Flask endpoints and the context each needs), availability, role visibility,
training lessons (keys in app/training/contractor.py and supplier.py), acceptance-test (UAT) keys, the
loops back to earlier stages and the contractor-supplier hand-offs. tests/test_workflow_map.py checks that
every endpoint exists, every lesson and UAT key exists, every role is real and no stage is orphaned.

Rules kept here:
- A destination is a real CalibraytAI page. A step CalibraytAI does not do has no destination and says so
  (``NOT_YET``, ``OUTSIDE``, ``OTHER_PARTY``); it is never shown as a link.
- A destination that needs a project (or a supplier) and is opened without one goes to the page where the
  person chooses one (``fallback``), never to a dead end.
- ``requires`` says who may open the page; the map shows the reason instead of a link to anyone else.
- The map shows descriptions and links only. It never shows a record, and never the other party's records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.models.training import (
    ROLE_FIELD,
    ROLE_OFFICE,
    ROLE_OWNER,
    ROLE_PRO_DESK,
    ROLE_SUPPLIER_ADMIN,
    ROLE_SUPPLIER_OWNER,
)

DEFINITION_VERSION = "2026-10-22.2"  # .2: schedule texts (SMS notices, 22 Oct 2026)

# ------------------------------------------------------------------ vocabulary

SIDE_CONTRACTOR = "CONTRACTOR"
SIDE_SUPPLIER = "SUPPLIER"
SIDE_FIELD = "FIELD"

# Who may open a destination.
REQ_OFFICE = "office"                    # an office member of the contractor company (not field-only)
REQ_PEOPLE_ADMIN = "people_admin"        # the owner or a System Administrator
REQ_COMPANY_MANAGEMENT = "company_management"  # the Company management access domain
REQ_CONTRACTOR = "contractor"            # anyone in the contractor company, Field crew included
REQ_SUPPLIER = "supplier"                # a signed-in person of this supplier (Supplier Hub)
REQUIREMENTS = (REQ_OFFICE, REQ_PEOPLE_ADMIN, REQ_COMPANY_MANAGEMENT, REQ_CONTRACTOR, REQ_SUPPLIER)

REQUIREMENT_REASONS = {
    REQ_OFFICE: "Opened by the office. Field sign-ins see only Field.",
    REQ_PEOPLE_ADMIN: "Only the owner or a System Administrator can open this. Ask them.",
    REQ_COMPANY_MANAGEMENT: "Needs Company management access, which the owner gives in People & Access.",
    REQ_CONTRACTOR: "Opened by the contractor company in CalibraytAI.",
    REQ_SUPPLIER: "Opened in the supplier's own Supplier Hub.",
}

# Availability of a step in CalibraytAI.
AVAILABLE = "available"
OTHER_PARTY = "other_party"   # real, but done by someone else (the contractor's office, the customer)
OUTSIDE = "outside"           # done outside CalibraytAI
NOT_YET = "not_yet"           # not in CalibraytAI yet
AVAILABILITY_LABELS = {
    AVAILABLE: "In CalibraytAI",
    OTHER_PARTY: "Done by the other party",
    OUTSIDE: "Done outside CalibraytAI",
    NOT_YET: "Not in CalibraytAI yet",
}

CTX_PROJECT = "project"
CTX_SUPPLIER = "supplier"
CONTEXTS = (CTX_PROJECT, CTX_SUPPLIER)

CONTRACTOR_ROLES = (ROLE_OWNER, ROLE_OFFICE, ROLE_FIELD)
OFFICE_ROLES = (ROLE_OWNER, ROLE_OFFICE)
SUPPLIER_ROLES = (ROLE_SUPPLIER_OWNER, ROLE_SUPPLIER_ADMIN, ROLE_PRO_DESK)
SUPPLIER_DESK_ROLES = (ROLE_SUPPLIER_OWNER, ROLE_SUPPLIER_ADMIN)
ALL_ROLES = CONTRACTOR_ROLES + SUPPLIER_ROLES


@dataclass(frozen=True)
class Destination:
    """A real CalibraytAI page. ``path`` maps URL arguments to a context (("id", "project")); ``query`` adds
    optional query arguments from the context when known; ``fixed`` adds constant query arguments.
    Without a required context the link goes to ``fallback`` (where the person chooses one)."""

    endpoint: str
    label: str
    requires: str = REQ_OFFICE
    path: Tuple[Tuple[str, str], ...] = ()
    query: Tuple[Tuple[str, str], ...] = ()
    fixed: Tuple[Tuple[str, str], ...] = ()
    anchor: str = ""
    fallback: str = ""
    fallback_label: str = ""

    @property
    def needs(self) -> Tuple[str, ...]:
        return tuple(ctx for _arg, ctx in self.path)


@dataclass(frozen=True)
class Substep:
    key: str
    label: str
    dest: Optional[Destination] = None
    availability: str = AVAILABLE
    note: str = ""
    lesson: str = ""
    roles: Tuple[str, ...] = ()   # empty = everyone who sees the stage


@dataclass(frozen=True)
class Loop:
    target: str       # stage id
    label: str        # "Delivery change → BUILD"
    text: str
    action: str


@dataclass(frozen=True)
class Stage:
    id: str
    journey: str
    number: int
    label: str        # SET UP
    title: str        # Get the business ready
    summary: str      # one line on the overview card
    description: str
    substeps: Tuple[Substep, ...]
    primary: Optional[Destination] = None
    lessons: Tuple[str, ...] = ()
    uat: Tuple[str, ...] = ()
    loops: Tuple[Loop, ...] = ()
    handoffs: Tuple[int, ...] = ()
    roles: Tuple[str, ...] = ()
    # Project.status values (app/services/project_stage.py) at which a project is in this stage.
    project_statuses: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Branch:
    """A tool used at any stage (calculators, drawings, calendars, Cal)."""

    key: str
    label: str
    description: str
    dests: Tuple[Destination, ...] = ()
    lessons: Tuple[str, ...] = ()
    opens_cal: bool = False


@dataclass(frozen=True)
class Journey:
    key: str
    side: str
    letter: str
    title: str
    flow: str          # "SET UP → PLAN → …"
    summary: str
    stage_ids: Tuple[str, ...]
    roles: Tuple[str, ...]
    loop_note: str = ""


@dataclass(frozen=True)
class Handoff:
    """One step of the authorized contractor-supplier transaction, seen from both sides."""

    number: int
    title: str
    contractor: str
    supplier: str
    contractor_stage: str
    supplier_stage: str


@dataclass(frozen=True)
class WorkflowMap:
    key: str
    side: str
    title: str
    eyebrow: str
    intro: str
    journeys: Tuple[str, ...]
    branches: Tuple[Branch, ...]
    shows_handoffs: bool


def _d(endpoint, label, requires=REQ_OFFICE, **kw) -> Destination:
    for name in ("path", "query", "fixed"):
        if name in kw and isinstance(kw[name], dict):
            kw[name] = tuple(kw[name].items())
    return Destination(endpoint=endpoint, label=label, requires=requires, **kw)


def _project(endpoint, label, arg="project_id", anchor="", requires=REQ_OFFICE) -> Destination:
    """A page about one project; without a project, the Projects list to choose one."""
    return _d(endpoint, label, requires, path={arg: CTX_PROJECT}, anchor=anchor,
              fallback="projects.list_projects", fallback_label="Choose the project in Projects")


def _hub(label, anchor="") -> Destination:
    return _project("projects.view_project", label, arg="id", anchor=anchor)


def _sup(endpoint, label, anchor="", fixed=None) -> Destination:
    return _d(endpoint, label, REQ_SUPPLIER, path={"supplier_id": CTX_SUPPLIER}, anchor=anchor,
              fixed=fixed or {}, fallback="supplier_portal.home", fallback_label="Choose your store")


def _field(endpoint, label, project=False) -> Destination:
    if project:
        return _d(endpoint, label, REQ_CONTRACTOR, path={"project_id": CTX_PROJECT},
                  fallback="field.projects", fallback_label="Choose the job in Field → Projects")
    return _d(endpoint, label, REQ_CONTRACTOR)


S = Substep

# ------------------------------------------------------------------ destinations used more than once

D_DASHBOARD = _d("main.dashboard", "Open Home")
D_GETTING_STARTED = _d("getting_started.index", "Open Getting started")
D_PASSWORD = _d("auth.change_password", "Open Change password", REQ_CONTRACTOR)
D_BRAND = _d("settings.brand_profile", "Open Brand profile")
D_PEOPLE = _d("people_access.index", "Open People & Access", REQ_PEOPLE_ADMIN)
D_CREWS = _d("organization_crew.index", "Open Crews")
D_ACCOUNTING = _d("accounting.index", "Open Accounting")
D_RECONCILE = _d("accounting.reconcile", "Open Check QuickBooks")
D_INVOICES = _d("accounting.invoices", "Open Invoices")
D_MY_CAL = _d("schedule.company", "Open My Calendar", fixed={"scope": "mine"})
D_CO_CAL = _d("schedule.company", "Open Company Calendar", fixed={"scope": "company"})
D_CAL_FEED = _d("schedule.calendar_feed_settings", "Open Calendar on your phone")
D_SUPPLIERS = _d("supplier_office.suppliers", "Open Suppliers")
D_DELIVERIES = _d("supplier_office.deliveries", "Open Deliveries")
D_PRICING = _d("pricing_engine.index", "Open How we price")
D_COSTS = _d("cost_library.list_cost_items", "Open What we pay")
D_REUSABLE = _d("assemblies.list_assemblies", "Open Reusable work")
D_CLIENT_NEW = _d("clients.create_client", "Open New client")
D_PROJECT_NEW = _d("projects.create_project", "Open New project")
D_PROJECTS = _d("projects.list_projects", "Open Projects")
D_PAST_PROJECTS = _d("projects.list_projects", "Open Closed projects", fixed={"view": "closed"})
D_PAST_JOBS = _d("historical_estimates.index", "Open Past jobs")
D_ESTIMATES = _d("estimates.list_estimates", "Open Estimates")
D_ESTIMATE_NEW = _d("estimates.create_estimate_route", "Open New estimate", query={"project_id": CTX_PROJECT})
D_PROPOSALS = _d("proposals.list_proposals", "Open Proposals")
D_TEMPLATES = _d("proposal_templates.list_templates", "Open Proposal templates")
D_CHANGE_ORDERS = _d("project_controls.list_change_orders", "Open Change orders")
D_TIME = _d("time_entry.review", "Open Time review")
D_SCHEDULE_NEW = _d("schedule.new_item", "Open Schedule work")
D_CONCRETE = _d("calculators.concrete", "Open Concrete calculator")
D_ATTENTION = _d("company_attention.index", "Open Attention", REQ_COMPANY_MANAGEMENT)
D_FIELD_TODAY = _field("field.today", "Open Field Today")

D_HUB = _hub("Open the project page")
D_SUPPLIER_REQUESTS = _project("supplier_office.project_requests", "Open Supplier requests")
D_CONTRACT = _project("projects.review_contract", "Open Contract", arg="id")
D_DRAWINGS = _project("construction_drawings.index", "Open Construction Drawings")

D_INBOX = _sup("supplier_portal.inbox", "Open Requests")
D_SUP_DELIVERIES = _sup("supplier_portal.supplier_deliveries", "Open Deliveries")
D_SUP_DASHBOARD = _sup("supplier_portal.supplier_dashboard", "Open Dashboard")
D_SUP_DEMAND = _sup("supplier_portal.supplier_demand", "Open Material demand")
D_SUP_ACCOUNT = _d("supplier_portal.account", "Open Text settings", REQ_SUPPLIER)
D_PD_INDEX = _sup("supplier_pro_desk.index", "Open Walk-in quotations")
D_PD_NEW = _sup("supplier_pro_desk.new_quote", "Open New walk-in quotation")
D_PD_QUICK = _sup("supplier_pro_desk.quick", "Open Quick Quote")
D_PD_PRICES = _sup("supplier_pro_desk.prices", "Open Price file")
D_PD_SETTINGS = _sup("supplier_pro_desk.settings", "Open Quote settings")
D_PD_STANDARDS = _sup("supplier_pro_desk.standards", "Open Standard buildings and product matches")
D_PD_TIMING = _sup("supplier_pro_desk.timing", "Open Timing")

# A walk-in quotation's own page needs the quotation; the list is where it is opened.
D_PD_A_QUOTE = _sup("supplier_pro_desk.index", "Open the quotation from Walk-in quotations")
D_A_REQUEST = _sup("supplier_portal.inbox", "Open the request from Requests")

# ------------------------------------------------------------------ contractor journey

CONTRACTOR_STAGES: Tuple[Stage, ...] = (
    Stage(
        id="c-setup", journey="contractor", number=1, label="SET UP", title="Get the business ready",
        summary="Company, people, crews and phones, accounting, calendars, suppliers and pricing.",
        description="Done once and kept current. The company's name and brand, who may sign in and what each "
                    "person may do, the crews and their iPhones, the accounting files for QuickBooks, the "
                    "calendars, the suppliers and the way the company prices its work.",
        primary=D_GETTING_STARTED,
        substeps=(
            S("account", "Contractor account and first sign-in", D_PASSWORD, lesson="c01-sign-in"),
            S("brand", "Company information and branding", D_BRAND, lesson="c02-company-brand"),
            S("people", "Users, roles and permissions", D_PEOPLE, lesson="c02-people"),
            S("crews", "Crew invitations and iPhone setup", D_CREWS, lesson="c02-crews"),
            S("quickbooks", "Verified accounting workflow (QuickBooks files)", D_ACCOUNTING,
              note="CalibraytAI prepares QuickBooks import files and checks them against QuickBooks.",
              lesson="c04-quickbooks-setup"),
            S("quickbooks-live", "Direct QuickBooks Online connection", availability=NOT_YET,
              note="Prepared but not switched on. Use the files on the Accounting page."),
            S("calendars", "My Calendar and Company Calendar", D_MY_CAL, lesson="c05-calendars"),
            S("suppliers", "Supplier accounts and pricing", D_SUPPLIERS, lesson="c08-suppliers"),
            S("defaults", "Business estimating defaults (How we price, HST)", D_PRICING, lesson="c02-pricing-hst"),
            S("costs", "What we pay and Reusable work", D_COSTS, lesson="c09-cost-library"),
        ),
        lessons=("c01-welcome", "c01-sign-in", "c01-find-your-way", "c01-forgot-password", "c02-getting-started",
                 "c02-company-brand", "c02-pricing-hst", "c02-people", "c02-access", "c02-crews",
                 "c03-invite-worker", "c03-activate-phone", "c03-home-screen", "c03-field-first-look",
                 "c04-accounting-page", "c04-quickbooks-setup", "c05-calendars",
                 "c05-phone-calendar", "c08-suppliers", "c09-cost-library"),
        uat=("uat-c01-sign-in", "uat-c01-register", "uat-c02-people", "uat-c02-pricing", "uat-c02-office-no-people",
             "uat-c03-activate", "uat-c03-phones-step", "uat-c05-feed"),
        roles=OFFICE_ROLES,
    ),
    Stage(
        id="c-plan", journey="contractor", number=2, label="PLAN", title="Get the job organized",
        summary="Customer, project, job location, specifications, drawings, calculators and takeoffs.",
        description="Every job starts with a customer and a project. The project page (the hub) then holds the "
                    "job location, the construction information, the plans and drawings, the calculations and "
                    "the material takeoffs that the price is built from.",
        primary=D_PROJECTS,
        substeps=(
            S("customer", "Add a customer", D_CLIENT_NEW, lesson="c06-clients"),
            S("project", "Start a project", D_PROJECT_NEW, lesson="c06-existing-jobs"),
            S("location", "Enter job-location information",
              _project("projects.edit_project_location", "Open Job location", arg="id"), lesson="c06-project-setup"),
            S("specs", "Record construction specifications",
              _project("projects.construction_information", "Open Construction information", arg="id")),
            S("upload", "Upload drawings and documents",
              _project("plan_intelligence.upload_plan", "Open Upload Plan PDF"), lesson="c07-plans"),
            S("calculators", "Use construction calculators", D_CONCRETE, lesson="c07-concrete-calculator"),
            S("drawings", "Generate or review drawings", D_DRAWINGS, lesson="c07-deck-takeoff"),
            S("takeoff", "Prepare material takeoffs", _project("deck_takeoff.review", "Open Deck Takeoff"),
              lesson="c07-deck-takeoff"),
            S("scope", "Define scope and material requirements",
              _project("projects.scope_of_work", "Open Scope of work", arg="id")),
            S("engineered", "Engineered or permit-ready drawings", availability=OUTSIDE,
              note="CalibraytAI's drawings are construction and sales drawings. Engineering and permit "
                   "drawings come from a designer or engineer."),
        ),
        lessons=("c06-clients", "c06-project-hub", "c06-project-setup", "c06-existing-jobs", "c07-plans",
                 "c07-concrete-calculator", "c07-deck-takeoff"),
        uat=("uat-c06-project", "uat-c06-hub", "uat-c07-plan", "uat-c07-calculator"),
        roles=OFFICE_ROLES, project_statuses=("Lead",),
    ),
    Stage(
        id="c-price", journey="contractor", number=3, label="PRICE", title="Know what the job will cost",
        summary="Supplier quotations, approved material costs, labour, the estimate, margin and taxes.",
        description="Ask the suppliers for prices, compare and approve what they return, add the labour, and "
                    "build the estimate with the company's pricing and true gross margin. Costing waits until "
                    "each line says who supplies and who builds it.",
        primary=D_ESTIMATES,
        substeps=(
            S("select-suppliers", "Select suppliers", D_SUPPLIERS, lesson="c08-suppliers"),
            S("request", "Request material quotations", D_SUPPLIER_REQUESTS, lesson="c08-concrete-request"),
            S("compare", "Receive and compare supplier responses", D_SUPPLIER_REQUESTS, lesson="c08-approve-quote"),
            S("approve-costs", "Approve material costs", D_SUPPLIER_REQUESTS, lesson="c08-approve-quote"),
            S("labour", "Calculate labour requirements", _hub("Open the project page: Labour", "hub-labour")),
            S("estimate", "Build the estimate", D_ESTIMATE_NEW, lesson="c09-new-estimate"),
            S("margin", "Apply pricing and true gross margin", D_PRICING, lesson="c09-pricing"),
            S("taxes", "Review taxes and totals", D_ESTIMATES, lesson="c09-pricing"),
            S("finalize", "Finalize the estimate (scope delivery and costing approval)",
              _project("scope_delivery.review", "Open Scope Delivery Review"), lesson="c09-scope-delivery-costing"),
        ),
        lessons=("c08-concrete-request", "c08-approve-quote", "c09-new-estimate", "c09-scope-delivery-costing",
                 "c09-pricing"),
        uat=("uat-c08-quote", "uat-c09-estimate", "uat-c09-block"),
        handoffs=(1, 2, 3, 4), roles=OFFICE_ROLES, project_statuses=("Estimating",),
        loops=(Loop("c-plan", "Price → Plan", "A quotation or takeoff shows the scope or quantities need to change.",
                    "Go back to Plan"),),
    ),
    Stage(
        id="c-win", journey="contractor", number=4, label="WIN", title="Turn an estimate into a job",
        summary="The proposal, the customer's answer, the contract and signing.",
        description="The signed-off estimate becomes the customer proposal. It goes to the customer only "
                    "through CalibraytAI; the customer accepts or declines on their own link, and acceptance "
                    "leads to the contract, signed electronically, and the deposit invoice.",
        primary=D_PROPOSALS,
        substeps=(
            S("proposal", "Generate the customer proposal", D_PROPOSALS, lesson="c10-send-proposal"),
            S("review", "Review scope, exclusions and price", D_PROPOSALS, lesson="c10-send-proposal"),
            S("send", "Send the proposal", D_PROPOSALS, lesson="c10-send-proposal"),
            S("answer", "Customer acceptance or decline", availability=OTHER_PARTY,
              note="The customer answers on their own proposal link, by email or text.",
              lesson="c10-customer-acceptance"),
            S("contract", "Contract preparation", D_CONTRACT, lesson="c10-contract"),
            S("signing", "Electronic signing", D_CONTRACT, lesson="c10-contract"),
            S("authorize", "Project authorization", _hub("Open the project page: Contract", "hub-contract")),
            S("deposit", "Deposit invoice", D_INVOICES, lesson="c04-invoices"),
        ),
        lessons=("c10-proposal-template", "c10-send-proposal", "c10-customer-acceptance", "c10-contract",
                 "c04-invoices"),
        uat=("uat-c10-accept", "uat-c10-contract", "uat-c04-deposit"),
        roles=OFFICE_ROLES, project_statuses=("Proposal Sent",),
        loops=(Loop("c-price", "Win → Price", "The customer asks for a change before accepting.",
                    "Revise the estimate"),),
    ),
    Stage(
        id="c-build", journey="contractor", number=5, label="BUILD", title="Run the work",
        summary="Calendars, crews, Field, purchase orders, deliveries, field activity and change orders.",
        description="The work is scheduled on the calendars and assigned to crews, who see it on Field; when "
                    "their work moves, workers who agreed to texts get one text about it. "
                    "Purchase orders go to the suppliers, who confirm them; deliveries are scheduled and "
                    "changed together. Field notes, time and extra work come back to the office, and extra work "
                    "becomes an approved change order.",
        primary=_hub("Open the project page: Schedule", "hub-schedule"),
        substeps=(
            S("company-calendar", "Company Calendar", D_CO_CAL, lesson="c05-calendars"),
            S("my-calendar", "My Calendar", D_MY_CAL, lesson="c05-appointments"),
            S("schedule", "Schedule project activities",
              _project("work_structure.project_work_plan", "Open Project work"), lesson="c11-schedule-crew"),
            S("crews", "Assign crews", D_SCHEDULE_NEW, lesson="c11-schedule-crew"),
            S("text-notices", "Schedule texts to the crew (sent, delivered, failed, Retry)",
              _d("sms_notifications.office_notices", "Open Text notices")),
            S("field", "Field Today, Week and Month", D_FIELD_TODAY, lesson="c05-field-schedule"),
            S("orders", "Purchase orders", D_SUPPLIER_REQUESTS, lesson="c08-place-order"),
            S("confirmations", "Supplier confirmations", D_DELIVERIES, lesson="c08-place-order"),
            S("deliveries", "Delivery scheduling", D_DELIVERIES, lesson="c12-morning"),
            S("delivery-changes", "Delivery changes", D_DELIVERIES, lesson="c12-morning"),
            S("field-activity", "Field activity (notes, photos and time)", D_TIME, lesson="c11-office-review"),
            S("change-orders", "Change orders", D_CHANGE_ORDERS, lesson="c11-change-order"),
            S("progress", "Project progress", _hub("Open the project page: Build", "hub-build"),
              lesson="c11-office-review"),
        ),
        lessons=("c05-appointments", "c05-field-schedule", "c11-schedule-crew", "c08-place-order", "c11-field-today",
                 "c11-capture", "c11-extra-work", "c11-field-time", "c11-office-review", "c11-change-order",
                 "c12-morning", "c12-field-day", "c04-invoices", "c07-field-drawings"),
        uat=("uat-c05-appointments", "uat-c05-field-week", "uat-c08-order", "uat-c11-schedule", "uat-c11-field",
             "uat-c11-delivery-field", "uat-c11-change-order", "uat-c12-day", "uat-c12-field-day"),
        handoffs=(5, 6, 7, 8), roles=OFFICE_ROLES, project_statuses=("Contracted", "Active"),
        loops=(Loop("c-price", "Build → Price", "Extra work needs pricing before it becomes a change order.",
                    "Price the extra work"),
               Loop("c-build", "Delivery change", "Weather or the site moves a delivery: the change is asked, "
                    "answered and the new date shows on Field.", "Stay in Build")),
    ),
    Stage(
        id="c-close", journey="contractor", number=6, label="CLOSE", title="Finish the job properly",
        summary="Outstanding work and orders, final documents, job costs, completion and the record.",
        description="Before the job is closed: the punch list and open purchase orders are cleared, the final "
                    "documents are in place, the final invoice is sent and QuickBooks is checked. Closing keeps "
                    "the whole project as a historical record; it can be reopened.",
        primary=_project("projects.close_project", "Open Close the project", arg="id", requires=REQ_PEOPLE_ADMIN),
        substeps=(
            S("outstanding-work", "Outstanding work (punch list)",
              _hub("Open the project page: Punch list", "hub-punch-list")),
            S("outstanding-orders", "Outstanding purchase orders", D_SUPPLIER_REQUESTS, lesson="c12-morning"),
            S("documents", "Final documents",
              _project("projects.workflow_documents", "Open Workflow documents", arg="id")),
            S("job-costs", "Job costs and financial reconciliation", D_RECONCILE, lesson="c04-bills-and-check"),
            S("final-invoice", "Final invoice", D_INVOICES, lesson="c12-invoice-closeout"),
            S("complete", "Project completion",
              _project("projects.close_project", "Open Close the project", arg="id", requires=REQ_PEOPLE_ADMIN),
              lesson="c12-close-project"),
            S("history", "Historical project records", D_PAST_PROJECTS),
            S("past-jobs", "Past jobs (the company library)", D_PAST_JOBS),
        ),
        lessons=("c04-invoice-export", "c04-bills-and-check", "c12-invoice-closeout", "c12-getting-started-done",
                 "c12-close-project", "c12-final-acceptance"),
        uat=("uat-c04-export", "uat-c04-check", "uat-c12-close", "uat-c12-getting-started"),
        roles=OFFICE_ROLES, project_statuses=("Completed", "Archived"),
        loops=(Loop("c-plan", "Close → Plan", "The finished job becomes the starting point for the next one.",
                    "Start the next job"),),
    ),
)

# ------------------------------------------------------------------ Field journey (field crew)

FIELD_STAGES: Tuple[Stage, ...] = (
    Stage(
        id="f-start", journey="field", number=1, label="SIGN IN", title="Field on your iPhone",
        summary="Activate your account, sign in and put Field on the Home Screen.",
        description="Field is CalibraytAI on the crew's iPhone. Sign in once with the link the office sent, put "
                    "Field on the Home Screen and it opens on Today.",
        primary=D_FIELD_TODAY,
        substeps=(
            S("activate", "Activate your account from the email link", availability=OTHER_PARTY,
              note="The office sends the link from People & Access; you open it on your phone.",
              lesson="f01-activate"),
            S("password", "Change your password", D_PASSWORD, lesson="f01-password"),
            S("home-screen", "Put Field on the Home Screen", D_FIELD_TODAY, lesson="f01-home-screen"),
        ),
        lessons=("f01-start-training", "f01-activate", "f01-open-field", "f01-home-screen", "f01-useful-calculators",
                 "f01-password",
                 "f07-troubleshooting", "f08-field-uat"),
        uat=("uat-f01-sign-in", "uat-f01-field-only", "uat-f01-home-screen", "uat-f01-useful-calculators"),
        roles=CONTRACTOR_ROLES,
    ),
    Stage(
        id="f-today", journey="field", number=2, label="TODAY", title="See your day",
        summary="Today, This week, This month and Company today, with the day's deliveries.",
        description="Today shows the work you are on and the deliveries for your jobs. This week and This month "
                    "show what is coming; Company today shows what the whole company has on. Turn on schedule "
                    "texts (Texts, at the top of Field) to get a text when the office moves your work.",
        primary=D_FIELD_TODAY,
        substeps=(
            S("today", "Today", D_FIELD_TODAY, lesson="f02-my-work"),
            S("week", "This week", _field("field.week", "Open This week"), lesson="f03-week"),
            S("month", "This month", _field("field.month", "Open This month"), lesson="f03-month"),
            S("company", "Company today", _field("field.company_today", "Open Company today"),
              lesson="f02-company-today"),
            S("changes", "Schedule changes (the office moves dates)", _field("field.week", "Open This week"),
              lesson="f03-changes"),
            S("texts", "Schedule texts (a text when your work moves)",
              _field("field.text_messages", "Open Schedule texts"), lesson="f03-texts"),
        ),
        lessons=("f02-my-work", "f02-company-today", "f03-week", "f03-month", "f03-changes", "f03-texts",
                 "f07-refresh"),
        uat=("uat-f02-today", "uat-f03-week-month", "uat-f03-change", "uat-f03-texts"),
        roles=CONTRACTOR_ROLES,
    ),
    Stage(
        id="f-job", journey="field", number=3, label="ON THE JOB", title="Confirm the job you are on",
        summary="Choose the project, then its drawings and plans.",
        description="Confirm the job you are standing on. Its construction drawings and plan PDFs open read-only "
                    "on the phone.",
        primary=_field("field.projects", "Open Projects"),
        substeps=(
            S("projects", "Choose the job", _field("field.projects", "Open Projects"), lesson="f02-confirm-job"),
            S("drawings", "Drawings and plans", _field("field.drawings", "Open Drawings and plans", project=True),
              lesson="f04-drawings"),
        ),
        lessons=("f02-confirm-job", "f04-drawings", "f04-job-info"),
        uat=("uat-f02-confirm", "uat-f04-drawings"),
        roles=CONTRACTOR_ROLES,
    ),
    Stage(
        id="f-capture", journey="field", number=4, label="CAPTURE", title="Photos, notes and extra work",
        summary="Send photos and notes to the office; record extra work the customer asks for.",
        description="Photos and notes go straight to the project in the office. Extra work the customer asks "
                    "for is recorded here and becomes a change order in the office.",
        primary=_field("field.capture", "Open Capture", project=True),
        substeps=(
            S("capture", "Photos and notes", _field("field.capture", "Open Capture", project=True),
              lesson="f06-capture"),
            S("extra-work", "Extra work", _field("field.extra_work", "Open Extra work", project=True),
              lesson="f05-extra-work"),
        ),
        lessons=("f06-capture", "f06-voice-note", "f06-progress", "f05-extra-work", "f07-offline"),
        uat=("uat-f06-capture", "uat-f05-extra-work", "uat-f07-offline"),
        roles=CONTRACTOR_ROLES,
    ),
    Stage(
        id="f-time", journey="field", number=5, label="TIME", title="Send your time",
        summary="Record your hours on the job; the office reviews them.",
        description="At the end of the day send your time for the job. The office reviews it; you can see what "
                    "you sent on My time.",
        primary=_field("field.my_time", "Open My time"),
        substeps=(
            S("time", "Send time for the job", _field("field.time_entry", "Open Time", project=True),
              lesson="f05-send-time"),
            S("my-time", "My time", _field("field.my_time", "Open My time"), lesson="f05-my-time-review"),
            S("returned", "Fix time the office returned", _field("field.my_time", "Open My time"),
              lesson="f05-returned-time"),
            S("approved", "The office approves your time", availability=OTHER_PARTY,
              note="Ben reviews and approves your hours in the office; My time then shows Approved.",
              lesson="f05-approved"),
            S("company-time", "Shop and company time", _field("field.my_time", "Open My time"),
              lesson="f05-company-time"),
        ),
        lessons=("f05-send-time", "f05-my-time-review", "f05-returned-time", "f05-approved", "f05-company-time",
                 "f08-working-day"),
        uat=("uat-f05-time", "uat-f05-my-time", "uat-f05-returned", "uat-f05-approved", "uat-f05-company-time",
             "uat-f08-day"),
        roles=CONTRACTOR_ROLES,
        loops=(Loop("f-today", "Tomorrow → Today", "The next working day starts on Today again.", "Back to Today"),),
    ),
)

# ------------------------------------------------------------------ supplier journeys

SUPPLIER_STAGES: Tuple[Stage, ...] = (
    # Journey A — serving contractors
    Stage(
        id="sa-receive", journey="supplier-a", number=1, label="RECEIVE", title="A contractor's request arrives",
        summary="Material and concrete requests the contractor chose to send you.",
        description="A contractor sends a request only to suppliers it chose. It arrives in Requests with the "
                    "materials, quantities, the delivery town and the requested date. It never shows the "
                    "contractor's customer, prices or margins.",
        primary=D_INBOX,
        substeps=(
            S("authorized", "Contractor-authorized material requests", D_INBOX, lesson="s04-open-request"),
            S("inbox", "Supplier inbox (Requests)", D_INBOX, lesson="s03-store-page"),
            S("details", "Request details", D_A_REQUEST, lesson="s04-open-request"),
            S("lists", "Material lists and quantities", D_A_REQUEST, lesson="s04-open-request"),
            S("concrete", "Concrete requests (kept separate)", D_INBOX, lesson="s04-concrete-quote"),
            S("dates", "Requested delivery dates", D_A_REQUEST, lesson="s04-open-request"),
        ),
        lessons=("s03-store-page", "s04-open-request"),
        uat=("uat-s03-needs-attention", "uat-s04-privacy"),
        handoffs=(1, 2), roles=SUPPLIER_DESK_ROLES,
    ),
    Stage(
        id="sa-quote", journey="supplier-a", number=2, label="QUOTE", title="Price it and return the quote",
        summary="Match your SKUs, enter your selling prices and return the quotation.",
        description="Review what is needed, match your own SKUs (remembered from earlier quotes), enter your "
                    "selling prices and return the quotation, with the filled request PDF if you prefer.",
        primary=D_A_REQUEST,
        substeps=(
            S("review", "Review material requirements", D_A_REQUEST, lesson="s04-material-quote"),
            S("skus", "Match supplier SKUs", D_A_REQUEST, lesson="s07-sku-reuse"),
            S("prices", "Enter supplier selling prices", D_A_REQUEST, lesson="s04-material-quote"),
            S("return", "Prepare and return quotations", D_A_REQUEST, lesson="s04-material-quote"),
            S("attach", "Attach supporting documents (the filled request PDF)", D_A_REQUEST,
              lesson="s04-material-quote"),
            S("effort", "Record quotation effort", availability=NOT_YET,
              note="Timed for PRO Desk walk-in quotations only (Journey B); not yet for contractor requests."),
        ),
        lessons=("s04-material-quote", "s04-concrete-quote", "s07-sku-reuse"),
        uat=("uat-s04-material-quote", "uat-s04-concrete-quote", "uat-s07-sku-prefill"),
        handoffs=(3,), roles=SUPPLIER_DESK_ROLES,
    ),
    Stage(
        id="sa-confirm", journey="supplier-a", number=3, label="CONFIRM", title="The order arrives",
        summary="The contractor approves your quote and places the purchase order; you confirm it.",
        description="The contractor reviews your quotation in its own office. When it places the purchase "
                    "order you are told by email (and text, if set); the site address arrives with the order. "
                    "Confirm it, or report a problem with a note.",
        primary=D_INBOX,
        substeps=(
            S("review", "Contractor quotation review", availability=OTHER_PARTY,
              note="Done in the contractor's office. You see the purchase order when it is placed."),
            S("po", "Purchase order received", D_INBOX, lesson="s05-new-order"),
            S("accept", "Order acceptance or confirmation", D_A_REQUEST, lesson="s05-confirm"),
            S("details", "Order details and quantities", D_A_REQUEST, lesson="s05-new-order"),
            S("changes", "Required changes (report a problem)", D_A_REQUEST, lesson="s05-confirm"),
        ),
        lessons=("s05-new-order", "s05-confirm"),
        uat=("uat-s05-confirm", "uat-s05-problem-note", "uat-s05-address"),
        handoffs=(4, 5, 6), roles=SUPPLIER_DESK_ROLES,
        loops=(Loop("sa-quote", "Confirm → Quote", "The contractor asks for a revised quotation.",
                    "Back to Quote"),),
    ),
    Stage(
        id="sa-deliver", journey="supplier-a", number=4, label="DELIVER", title="Agree the delivery",
        summary="The delivery schedule, confirmations and changes from either side.",
        description="Deliveries lists every confirmed order by date. Either side can ask to move a delivery; "
                    "the other answers. For concrete, the store sells to the contractor and its ready-mix "
                    "supplier fulfils the pour (BMR Winchester sells; Tomlinson fulfils).",
        primary=D_SUP_DELIVERIES,
        substeps=(
            S("schedule", "Delivery schedule", D_SUP_DELIVERIES, lesson="s06-deliveries"),
            S("confirmations", "Delivery confirmations", D_A_REQUEST, lesson="s06-deliveries"),
            S("propose", "Proposed schedule changes", D_A_REQUEST, lesson="s06-ask-change"),
            S("responses", "Contractor responses (answer a change)", D_INBOX, lesson="s06-answer-change"),
            S("upstream", "Concrete fulfilment through the upstream supplier (e.g. Tomlinson)", availability=OUTSIDE,
              note="The store arranges the pour with its ready-mix supplier. That supplier is not a party in "
                   "CalibraytAI; the contractor deals with the store."),
        ),
        lessons=("s06-deliveries", "s06-ask-change", "s06-answer-change"),
        uat=("uat-s06-supplier-change", "uat-s06-answer-change"),
        handoffs=(7, 8), roles=SUPPLIER_DESK_ROLES,
        loops=(Loop("sa-deliver", "Delivery change", "Weather moves the pour: ask, answer, and the agreed date "
                    "replaces the old one.", "Stay in Deliver"),),
    ),
    Stage(
        id="sa-complete", journey="supplier-a", number=5, label="COMPLETE", title="Close the order",
        summary="Mark it delivered; the history and your reporting stay.",
        description="Mark the order delivered. The request keeps its full history of quotes, orders and "
                    "changes, and the Dashboard counts it.",
        primary=D_SUP_DASHBOARD,
        substeps=(
            S("status", "Final order status (mark delivered)", D_A_REQUEST, lesson="s06-delivered"),
            S("history", "Transaction history", D_A_REQUEST, lesson="s10-contractor-cycle"),
            S("reporting", "Relevant supplier reporting", D_SUP_DASHBOARD, lesson="s03-dashboard"),
            S("invoice", "Invoicing and payment", availability=OUTSIDE,
              note="The store invoices and is paid in its own system; CalibraytAI does not record sales."),
        ),
        lessons=("s06-delivered", "s10-contractor-cycle", "s10-acceptance"),
        uat=("uat-s06-delivered", "uat-s10-full-cycle"),
        roles=SUPPLIER_DESK_ROLES,
        loops=(Loop("sa-receive", "Complete → Receive", "The contractor's next request starts the cycle again.",
                    "Back to Receive"),),
    ),
    # Journey B — walk-in PRO Desk customers
    Stage(
        id="sb-customer", journey="supplier-b", number=1, label="CUSTOMER", title="The walk-in customer",
        summary="Create the store's own customer record with contact details and consent.",
        description="The customer belongs to the store, not to any contractor. Record who they are, how to "
                    "reach them and their consent to be contacted.",
        primary=D_PD_NEW,
        substeps=(
            S("create", "Create a supplier-owned walk-in customer", D_PD_NEW, lesson="s09-quick-quote"),
            S("consent", "Record contact details and consent", D_PD_NEW, lesson="s09-quick-quote"),
        ),
        lessons=("s09-quick-quote",),
        uat=("uat-s09-quick-quote",),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sb-sketch", journey="supplier-b", number=2, label="SKETCH", title="The customer's drawing",
        summary="Photograph or upload the sketch and review what it says.",
        description="Photograph the customer's sketch at the counter or upload it, then go through what it "
                    "shows with the customer.",
        primary=D_PD_QUICK,
        substeps=(
            S("photo", "Photograph or upload the customer's drawing", D_PD_QUICK, lesson="s09-quick-quote"),
            S("review", "Review the supplied information", D_PD_A_QUOTE, lesson="s09-quick-quote"),
        ),
        lessons=("s09-quick-quote",),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sb-configure", journey="supplier-b", number=3, label="CONFIGURE", title="The building",
        summary="Building type, dimensions and specifications, in Quick Quote.",
        description="Choose one of the store's standard buildings, enter the dimensions, doors, windows and "
                    "floor, and confirm the specifications. Nothing is filled in for you.",
        primary=D_PD_QUICK,
        substeps=(
            S("type", "Select the supported building type", D_PD_QUICK, lesson="s09-quick-quote"),
            S("dimensions", "Enter dimensions", D_PD_QUICK, lesson="s09-quick-quote"),
            S("specs", "Confirm required specifications", D_PD_A_QUOTE, lesson="s09-price-issue"),
            S("quick", "Use Quick Quote", D_PD_QUICK, lesson="s09-quick-quote"),
            S("standards", "The store's standard buildings", D_PD_STANDARDS, lesson="s08-standards-matches"),
        ),
        lessons=("s09-quick-quote", "s08-standards-matches"),
        uat=("uat-s09-quick-quote",),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sb-draw", journey="supplier-b", number=4, label="DRAW", title="Drawing and quantities",
        summary="A preliminary sales drawing and the material list, with technical-review items flagged.",
        description="CalibraytAI draws a preliminary sales drawing from the confirmed answers and works out the "
                    "material list. It is not engineered and not a permit drawing; structural items always go "
                    "to technical review.",
        primary=D_PD_A_QUOTE,
        substeps=(
            S("drawing", "Generate the preliminary drawing (not engineered, not for permit)", D_PD_A_QUOTE,
              lesson="s09-price-issue"),
            S("quantities", "Calculate material quantities", D_PD_A_QUOTE, lesson="s09-price-issue"),
            S("technical", "Identify technical review requirements", D_PD_A_QUOTE, lesson="s09-price-issue"),
            S("engineered", "Engineered or permit-ready drawings", availability=OUTSIDE,
              note="Not produced by CalibraytAI. The customer's designer or engineer provides them."),
        ),
        lessons=("s09-price-issue",),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sb-price", journey="supplier-b", number=5, label="PRICE", title="The store's prices",
        summary="Match products, apply the store's prices, find missing prices, taxes and delivery.",
        description="Each line is matched to the store's product and priced from the store's own price file. A "
                    "line without a current price is listed, never guessed. Tax and delivery are added.",
        primary=D_PD_PRICES,
        substeps=(
            S("match", "Match supplier products", D_PD_STANDARDS, lesson="s08-standards-matches"),
            S("prices", "Apply authorized store selling prices", D_PD_PRICES, lesson="s08-price-file"),
            S("missing", "Identify missing prices and exceptions", D_PD_A_QUOTE, lesson="s09-price-issue"),
            S("tax", "Calculate taxes and delivery", D_PD_A_QUOTE, lesson="s09-price-issue"),
        ),
        lessons=("s08-price-file", "s08-standards-matches", "s09-price-issue"),
        uat=("uat-s08-price-file", "uat-s08-bad-row"),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sb-quote", journey="supplier-b", number=6, label="QUOTE", title="Issue the quotation",
        summary="The materials-only quotation, reviewed and issued.",
        description="Review the drawing, quantities, prices and exclusions, then issue the materials-only "
                    "quotation in the store's name.",
        primary=D_PD_A_QUOTE,
        substeps=(
            S("generate", "Generate the materials-only quotation", D_PD_A_QUOTE, lesson="s09-price-issue"),
            S("review", "Review drawings, quantities, prices and exclusions", D_PD_A_QUOTE, lesson="s09-price-issue"),
            S("issue", "Issue the quotation", D_PD_A_QUOTE, lesson="s09-price-issue"),
        ),
        lessons=("s09-price-issue",),
        uat=("uat-s09-issue",),
        roles=SUPPLIER_ROLES,
        loops=(Loop("sb-configure", "Quote → Configure", "The customer changes the size or a door.",
                    "Back to Configure"),),
    ),
    Stage(
        id="sb-approve", journey="supplier-b", number=7, label="APPROVE", title="The customer's answer",
        summary="The customer accepts or declines; the history is kept.",
        description="Send the customer their link, or record the answer they give at the counter or by phone. "
                    "The quotation and its approval history are kept.",
        primary=D_PD_A_QUOTE,
        substeps=(
            S("customer", "Customer reviews and accepts or declines", availability=OTHER_PARTY,
              note="On the customer's own quotation link (email or text).", lesson="s09-customer-link"),
            S("record", "Record an answer given in person or by phone", D_PD_A_QUOTE, lesson="s09-customer-link"),
            S("history", "Preserve the quotation and approval history", D_PD_A_QUOTE, lesson="s09-customer-link"),
        ),
        lessons=("s09-customer-link",),
        uat=("uat-s09-customer-link",),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sb-order", journey="supplier-b", number=8, label="ORDER", title="Ready for the store's system",
        summary="The order-ready package, exported for the store's own sales system.",
        description="An accepted quotation becomes an order-ready material package and a file (CSV) for the "
                    "store's own sales system. CalibraytAI is not connected to the point-of-sale system.",
        primary=D_PD_A_QUOTE,
        substeps=(
            S("package", "Generate the order-ready material package", D_PD_A_QUOTE, lesson="s09-order"),
            S("export", "Export the information for the store's existing sales system", D_PD_A_QUOTE,
              lesson="s09-order"),
            S("pos", "Direct point-of-sale (POS) integration", availability=NOT_YET,
              note="Not in CalibraytAI. The exported order sheet is entered in the store's own system."),
        ),
        lessons=("s09-order", "s10-pro-desk-cycle"),
        uat=("uat-s09-order", "uat-s10-walk-in"),
        roles=SUPPLIER_ROLES,
        loops=(Loop("sb-customer", "Order → Customer", "The next walk-in starts a new quotation.",
                    "Next customer"),),
    ),
    # Journey C — store setup and management
    Stage(
        id="sc-setup", journey="supplier-c", number=1, label="SET UP", title="Set up the store",
        summary="Account and location, staff sign-ins, prices, quote settings, branding and texts.",
        description="The contractor's office opens the store's Supplier Hub account, gives the staff their "
                    "sign-ins and saves the store's branding. The store loads its own price file and sets its "
                    "quotation settings and text messages.",
        primary=D_PD_SETTINGS,
        substeps=(
            S("account", "Supplier account and location", availability=OTHER_PARTY,
              note="Opened by the contractor's office (Company → Suppliers)."),
            S("staff", "Staff users and permissions", availability=OTHER_PARTY,
              note="The contractor's office gives each person a Supplier Hub sign-in. Every store user has the "
                   "same access.", lesson="s02-users"),
            S("catalogue", "Catalogue and SKU management (standard buildings and product matches)", D_PD_STANDARDS,
              lesson="s08-standards-matches"),
            S("prices", "Supplier selling-price imports", D_PD_PRICES, lesson="s08-price-file"),
            S("settings", "Quotation settings", D_PD_SETTINGS, lesson="s08-settings"),
            S("branding", "Approved supplier branding", availability=OTHER_PARTY,
              note="Saved by the contractor's office from the store's own logo and colour.", lesson="s02-branding"),
            S("texts", "Text messages for orders and delivery changes", D_SUP_ACCOUNT, lesson="s02-texts"),
        ),
        lessons=("s01-sign-in", "s01-register", "s01-password", "s02-users", "s02-branding", "s02-texts",
                 "s08-what-exists", "s08-settings", "s08-price-file"),
        uat=("uat-s01-sign-in", "uat-s01-wrong-password", "uat-s01-password-link", "uat-s02-same-access",
             "uat-s02-removed", "uat-s02-texts", "uat-s08-settings"),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sc-manage", journey="supplier-c", number=2, label="MANAGE", title="Run the day",
        summary="Needs attention, the Dashboard and the deliveries.",
        description="The store's page shows what needs attention first; the Dashboard and Deliveries show the "
                    "rest.",
        primary=D_SUP_DASHBOARD,
        substeps=(
            S("attention", "Needs attention", D_INBOX, lesson="s03-store-page"),
            S("dashboard", "Supplier Dashboard", D_SUP_DASHBOARD, lesson="s03-dashboard"),
            S("deliveries", "Deliveries", D_SUP_DELIVERIES, lesson="s06-deliveries"),
        ),
        lessons=("s03-store-page", "s03-dashboard"),
        uat=("uat-s03-phone", "uat-s10-other-store"),
        roles=SUPPLIER_ROLES,
    ),
    Stage(
        id="sc-measure", journey="supplier-c", number=3, label="MEASURE", title="Know the numbers",
        summary="Material demand, quote-to-order conversion and quotation effort.",
        description="Every figure comes from the requests, quotes and orders CalibraytAI already keeps for your "
                    "store. Requested is not ordered, and ordered is not a sale.",
        primary=D_SUP_DEMAND,
        substeps=(
            S("demand", "Material-demand reporting", D_SUP_DEMAND, lesson="s07-demand"),
            S("conversion", "Quote-to-order conversion", D_SUP_DASHBOARD, lesson="s03-dashboard"),
            S("effort", "Quotation effort (PRO Desk timing)", D_PD_TIMING, lesson="s09-order"),
        ),
        lessons=("s03-dashboard", "s07-demand"),
        uat=("uat-s03-period", "uat-s07-demand"),
        roles=SUPPLIER_DESK_ROLES,
    ),
    Stage(
        id="sc-grow", journey="supplier-c", number=4, label="GROW", title="Grow with your contractors",
        summary="Product opportunities and contractor relationships.",
        description="Material demand lists possible assortment gaps; the Dashboard lists the contractors who "
                    "send you requests.",
        primary=D_SUP_DEMAND,
        substeps=(
            S("opportunities", "Product opportunities (possible assortment gaps)", D_SUP_DEMAND, lesson="s07-demand"),
            S("relationships", "Contractor relationships", D_SUP_DASHBOARD, lesson="s03-dashboard"),
            S("sponsored", "Supplier-sponsored contractor access", availability=NOT_YET,
              note="A store sponsoring a contractor's CalibraytAI access is a proposal, not a feature yet."),
        ),
        lessons=("s07-demand",),
        roles=SUPPLIER_DESK_ROLES,
        loops=(Loop("sc-setup", "Grow → Set up", "New products and prices go back into the price file.",
                    "Back to Set up"),),
    ),
)

STAGES: Tuple[Stage, ...] = CONTRACTOR_STAGES + FIELD_STAGES + SUPPLIER_STAGES
STAGES_BY_ID: Dict[str, Stage] = {s.id: s for s in STAGES}

JOURNEYS: Tuple[Journey, ...] = (
    Journey("contractor", SIDE_CONTRACTOR, "", "The contractor's journey", "SET UP → PLAN → PRICE → WIN → BUILD → CLOSE",
            "The real operating life of a construction business, from setting up to closing each job.",
            tuple(s.id for s in CONTRACTOR_STAGES), OFFICE_ROLES,
            loop_note="Each job loops back: closing one job starts the next."),
    Journey("field", SIDE_FIELD, "", "The Field crew's day", "SIGN IN → TODAY → ON THE JOB → CAPTURE → TIME",
            "Field on the crew's iPhone: the day's work, the job's drawings, photos and notes, extra work and time.",
            tuple(s.id for s in FIELD_STAGES), CONTRACTOR_ROLES,
            loop_note="Every working day starts again on Today."),
    Journey("supplier-a", SIDE_SUPPLIER, "A", "Serving contractors", "RECEIVE → QUOTE → CONFIRM → DELIVER → COMPLETE",
            "Requests contractors choose to send you, your quotation, their order, the delivery and the close.",
            tuple(s.id for s in SUPPLIER_STAGES if s.journey == "supplier-a"), SUPPLIER_ROLES,
            loop_note="Delivery changes loop until both sides agree."),
    Journey("supplier-b", SIDE_SUPPLIER, "B", "Walk-in PRO Desk customers",
            "CUSTOMER → SKETCH → CONFIGURE → DRAW → PRICE → QUOTE → APPROVE → ORDER",
            "The five-minute PRO Desk quotation: from the customer's sketch to an order-ready package.",
            tuple(s.id for s in SUPPLIER_STAGES if s.journey == "supplier-b"), SUPPLIER_ROLES,
            loop_note="A change from the customer goes back to Configure."),
    Journey("supplier-c", SIDE_SUPPLIER, "C", "Store setup and management", "SET UP → MANAGE → MEASURE → GROW",
            "The store's account, staff, prices and settings, and the figures that help it grow.",
            tuple(s.id for s in SUPPLIER_STAGES if s.journey == "supplier-c"), SUPPLIER_ROLES),
)
JOURNEYS_BY_KEY: Dict[str, Journey] = {j.key: j for j in JOURNEYS}

# ------------------------------------------------------------------ the contractor-supplier connection

HANDOFFS: Tuple[Handoff, ...] = (
    Handoff(1, "Request", "You send a material or concrete quotation request to the suppliers you choose.",
            "The request arrives in Requests: materials, quantities, delivery town and date. Never your customer "
            "or your prices.", "c-price", "sa-receive"),
    Handoff(2, "Received", "The request shows Sent, then Opened when the supplier reads it.",
            "Opening it marks it Opened for the contractor.", "c-price", "sa-receive"),
    Handoff(3, "Pricing returned", "The supplier's quotation comes back on the project's Supplier requests.",
            "You match your SKUs, enter your selling prices and return the quotation.", "c-price", "sa-quote"),
    Handoff(4, "Costs approved", "You compare and approve the material costs; they flow into the estimate.",
            "The contractor's approval is its own decision; you see the order when it is placed.",
            "c-price", "sa-confirm"),
    Handoff(5, "Purchase order", "You place the purchase order from the approved quotation.",
            "The order arrives by email (and text, if set) with the site address.", "c-build", "sa-confirm"),
    Handoff(6, "Order confirmed", "The order shows Confirmed, or the problem the supplier reported.",
            "You confirm the order or report a problem with a note.", "c-build", "sa-confirm"),
    Handoff(7, "Delivery", "The delivery is on Deliveries, the Calendar and the crew's Field Today.",
            "The delivery is on your Deliveries list by date.", "c-build", "sa-deliver"),
    Handoff(8, "Schedule changes", "Either side asks to move a delivery; the other answers; the agreed date "
            "replaces the old one.", "Either side asks to move a delivery; the other answers. For concrete the "
            "store sells and its ready-mix supplier (e.g. Tomlinson) fulfils.", "c-build", "sa-deliver"),
)

PRIVACY_NOTE = ("Suppliers see only what a contractor chose to share with them on a request or an order. "
                "The Workflow Map shows stage descriptions and links, never the other party's records.")

# ------------------------------------------------------------------ tools used at any stage (branches)

CONTRACTOR_BRANCHES: Tuple[Branch, ...] = (
    Branch("calculators", "Calculators", "Concrete, stairs, ICF walls, framing, footings, roofing, siding, "
           "drywall and flooring: use them on their own or for a project.",
           (D_CONCRETE, _d("calculators.stairs", "Open Stair calculator"),
            _d("calculators.wall_form", "Open ICF wall calculator"),
            _d("calculators.wall_framing", "Open Wall framing calculator")),
           lessons=("c07-concrete-calculator",)),
    Branch("drawings", "Drawings and plans", "The job's construction drawings and plan PDFs, from Plan to Close.",
           (D_DRAWINGS, _project("plan_intelligence.list_plans", "Open Drawings (plan PDFs)")),
           lessons=("c07-plans", "c07-deck-takeoff")),
    Branch("calendars", "Calendars", "My Calendar and Company Calendar, and your phone's own calendar.",
           (D_MY_CAL, D_CO_CAL, D_CAL_FEED), lessons=("c05-calendars", "c05-phone-calendar")),
    Branch("cal", "Cal Assistant", "Ask Cal where something is, where you are or what comes next. Cal finds and "
           "links; it never changes anything.", (), opens_cal=True),
    Branch("attention", "Attention and Getting started", "What needs attention across the company, and Ben's "
           "First Day checklist.", (D_ATTENTION, D_GETTING_STARTED), lessons=("c02-getting-started",)),
)

SUPPLIER_BRANCHES: Tuple[Branch, ...] = (
    Branch("requests", "Requests", "Your store's page: needs attention, requests and orders.", (D_INBOX,),
           lessons=("s03-store-page",)),
    Branch("pro-desk", "PRO Desk", "Walk-in quotations and Quick Quote at the counter.", (D_PD_INDEX, D_PD_QUICK),
           lessons=("s09-quick-quote",)),
    Branch("texts", "Text settings", "Who at the store gets a text for new orders and delivery changes.",
           (D_SUP_ACCOUNT,), lessons=("s02-texts",)),
)

FIELD_BRANCHES: Tuple[Branch, ...] = (
    Branch("week", "Your schedule", "This week and This month, any time.",
           (_field("field.week", "Open This week"), _field("field.month", "Open This month")),
           lessons=("f03-week", "f03-month")),
)

MAP_CONTRACTOR = "contractor"
MAP_SUPPLIER = "supplier"
MAP_FIELD = "field"

MAPS: Dict[str, WorkflowMap] = {
    MAP_CONTRACTOR: WorkflowMap(
        MAP_CONTRACTOR, SIDE_CONTRACTOR, "Contractor Workflow Map", "Workflow Guide",
        "How a construction business runs in CalibraytAI, from setting up to closing each job. Select a stage to "
        "see what happens there and go straight to the right screen.",
        ("contractor",), CONTRACTOR_BRANCHES, True),
    MAP_SUPPLIER: WorkflowMap(
        MAP_SUPPLIER, SIDE_SUPPLIER, "Supplier Workflow Map", "Workflow Guide",
        "Three connected journeys for a building supplier: serving contractors, walk-in PRO Desk customers, and "
        "setting up and managing the store. Select a stage to see what happens there and open the right screen.",
        ("supplier-a", "supplier-b", "supplier-c"), SUPPLIER_BRANCHES, True),
    MAP_FIELD: WorkflowMap(
        MAP_FIELD, SIDE_FIELD, "Field Workflow", "Workflow Guide",
        "Your working day on Field, step by step.",
        ("field",), FIELD_BRANCHES, False),
}


# ------------------------------------------------------------------ lookups


def stage(stage_id: str) -> Optional[Stage]:
    return STAGES_BY_ID.get(stage_id)


def map_stages(map_key: str) -> List[Stage]:
    """The stages of one map, in Back/Next order (journey A, then B, then C on the supplier map)."""
    out: List[Stage] = []
    for key in MAPS[map_key].journeys:
        out += [STAGES_BY_ID[sid] for sid in JOURNEYS_BY_KEY[key].stage_ids]
    return out


def stages_for_lesson(lesson_key: str) -> List[Stage]:
    return [s for s in STAGES if lesson_key in s.lessons or any(x.lesson == lesson_key for x in s.substeps)]


def stages_for_uat(uat_key: str) -> List[Stage]:
    return [s for s in STAGES if uat_key in s.uat]


def stage_for_project_status(status: str) -> Optional[str]:
    for s in CONTRACTOR_STAGES:
        if status in s.project_statuses:
            return s.id
    return None


def all_destinations():
    """Every destination in the definition, with where it is used (for tests and the export)."""
    for s in STAGES:
        if s.primary is not None:
            yield f"{s.id}:primary", s.primary
        for x in s.substeps:
            if x.dest is not None:
                yield f"{s.id}:{x.key}", x.dest
    for m in MAPS.values():
        for b in m.branches:
            for i, d in enumerate(b.dests):
                yield f"{m.key}:branch:{b.key}:{i}", d


def export() -> dict:
    """A versioned, plain-data copy of the whole definition (for a separately hosted site to validate against)."""
    from dataclasses import asdict

    return {"version": DEFINITION_VERSION, "stages": [asdict(s) for s in STAGES],
            "journeys": [asdict(j) for j in JOURNEYS], "handoffs": [asdict(h) for h in HANDOFFS],
            "maps": {k: asdict(m) for k, m in MAPS.items()}}
