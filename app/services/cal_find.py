"""Cal Assistant, Phase 1 — Find It (Joel, 17 Oct 2026).

Cal finds records the signed-in office user can already open and returns links to them.
It reads only. It does not answer from outside knowledge, call an external AI provider,
change a record, send a message, place an order or move a schedule.

Authority: the existing records, the existing organization scoping
(``get_current_organization_id``), the existing navigation (``NAV_SECTIONS`` and its
access-domain rule) and the existing Help topics (``help_content``). Matching is plain
word matching; nothing is generated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from flask import url_for
from flask_login import current_user

from app.navigation import NAV_SECTIONS
from app.presentation import help_content

MAX_QUERY = 200
MAX_PER_GROUP = 8

# ---------------------------------------------------------------- what the user is asking for

DEST_PROJECTS = "projects"
DEST_DRAWINGS = "drawings"
DEST_ESTIMATES = "estimates"
DEST_PROPOSALS = "proposals"
DEST_CONTRACTS = "contracts"
DEST_QUOTES = "quotes"
DEST_ORDERS = "orders"
DEST_DELIVERIES = "deliveries"
DEST_CALENDAR = "calendar"

DEST_TITLES = {
    DEST_PROJECTS: "Projects",
    DEST_DRAWINGS: "Drawings and Project Plans",
    DEST_ESTIMATES: "Estimates",
    DEST_PROPOSALS: "Proposals",
    DEST_CONTRACTS: "Contracts",
    DEST_QUOTES: "Supplier quotations",
    DEST_ORDERS: "Purchase orders",
    DEST_DELIVERIES: "Delivery schedule",
    DEST_CALENDAR: "Company Calendar",
}

# Longest phrases first, so "delivery schedule" is not read as the calendar and
# "estimate request" (a supplier request) is not read as an estimate.
_INTENT_PHRASES = (
    ("supplier estimate request", DEST_QUOTES),
    ("estimate request", DEST_QUOTES),
    ("price request", DEST_QUOTES),
    ("pricing request", DEST_QUOTES),
    ("supplier request", DEST_QUOTES),
    ("supplier quote", DEST_QUOTES),
    ("concrete quote", DEST_QUOTES),
    ("concrete request", DEST_QUOTES),
    ("concrete order", DEST_QUOTES),
    ("purchase orders", DEST_ORDERS),
    ("purchase order", DEST_ORDERS),
    ("delivery schedule", DEST_DELIVERIES),
    ("delivery dates", DEST_DELIVERIES),
    ("delivery date", DEST_DELIVERIES),
    ("company calendar", DEST_CALENDAR),
    ("project plans", DEST_DRAWINGS),
    ("drawing set", DEST_DRAWINGS),
)
_INTENT_WORDS = {
    "drawing": DEST_DRAWINGS, "drawings": DEST_DRAWINGS, "plans": DEST_DRAWINGS, "plan": DEST_DRAWINGS,
    "sheets": DEST_DRAWINGS, "blueprint": DEST_DRAWINGS, "blueprints": DEST_DRAWINGS, "dxf": DEST_DRAWINGS,
    "estimate": DEST_ESTIMATES, "estimates": DEST_ESTIMATES,
    "proposal": DEST_PROPOSALS, "proposals": DEST_PROPOSALS,
    "contract": DEST_CONTRACTS, "contracts": DEST_CONTRACTS, "agreement": DEST_CONTRACTS,
    "quote": DEST_QUOTES, "quotes": DEST_QUOTES, "quotation": DEST_QUOTES, "quotations": DEST_QUOTES,
    "po": DEST_ORDERS, "pos": DEST_ORDERS, "order": DEST_ORDERS, "orders": DEST_ORDERS,
    "delivery": DEST_DELIVERIES, "deliveries": DEST_DELIVERIES, "delivered": DEST_DELIVERIES,
    "calendar": DEST_CALENDAR, "schedule": DEST_CALENDAR, "scheduled": DEST_CALENDAR,
    "project": DEST_PROJECTS, "projects": DEST_PROJECTS, "job": DEST_PROJECTS, "jobs": DEST_PROJECTS,
}
_STOPWORDS = frozenset(
    "a an the for of on at in to from with and or my our me i we you it its is are was be "
    "find show open get see go take where wheres what whats which who when how can do does "
    "please pull up look looking need want latest last recent current all any this that "
    "about there here use using today tomorrow week weeks month upcoming coming next soon"
    .split()
)
# Words that only steer the search and never name a project.
_HELP_WORDS = frozenset({"help", "how", "explain", "meaning", "mean"})
_REF_RE = re.compile(r"^(?=.*\d)[a-z0-9][a-z0-9\-_/]{1,29}$")


@dataclass
class Item:
    title: str
    url: str
    detail: str = ""
    kind: str = ""

    def as_dict(self) -> dict:
        return {"title": self.title, "url": self.url, "detail": self.detail, "kind": self.kind}


@dataclass
class Group:
    title: str
    items: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"title": self.title, "items": [i.as_dict() for i in self.items[:MAX_PER_GROUP]]}


@dataclass
class Parsed:
    raw: str
    intents: list
    words: list
    refs: list
    wants_help: bool


def _normalize(text: str) -> str:
    text = (text or "").lower().replace("’", "'")
    text = re.sub(r"'s\b", "", text)
    return " ".join(re.sub(r"[^a-z0-9\-_/ ]+", " ", text).split())


def parse_query(raw: str) -> Parsed:
    raw = (raw or "").strip()[:MAX_QUERY]
    text = f" {_normalize(raw)} "
    intents: list = []
    for phrase, dest in _INTENT_PHRASES:
        if f" {phrase} " in text:
            text = text.replace(f" {phrase} ", " ")
            if dest not in intents:
                intents.append(dest)
    words, refs, wants_help = [], [], False
    for token in text.split():
        if token in _HELP_WORDS:
            wants_help = True
            continue
        if token in _INTENT_WORDS:
            dest = _INTENT_WORDS[token]
            if dest not in intents:
                intents.append(dest)
            continue
        if token in _STOPWORDS or len(token) < 2:
            continue
        if _REF_RE.match(token):
            refs.append(token)
        words.append(token)
    # "project" only steers when nothing more specific was asked for.
    if len(intents) > 1 and DEST_PROJECTS in intents:
        intents.remove(DEST_PROJECTS)
    return Parsed(raw=raw, intents=intents, words=words, refs=refs, wants_help=wants_help)


# ---------------------------------------------------------------- authorized records

def _org_id() -> str:
    from app.services.organizations import get_current_organization_id

    return get_current_organization_id()


def _contains_all(haystack: str, words) -> bool:
    return all(w in haystack for w in words)


def _project_haystack(project) -> str:
    parts = [project.name or "", project.project_number or "", project.address or ""]
    client = getattr(project, "client", None)
    if client is not None:
        parts.append(client.name or "")
    location = getattr(project, "location", None)
    if location is not None and not isinstance(location, list):
        parts += [getattr(location, "street", "") or "", getattr(location, "municipality", "") or ""]
    return _normalize(" ".join(parts))


def match_projects(org_id: str, words) -> list:
    """Projects in this organization whose name, number, client or address contain every word."""
    from app.models import Project

    if not words:
        return []
    projects = Project.query.filter(Project.organization_id == org_id).order_by(Project.name.asc()).all()
    return [p for p in projects if _contains_all(_project_haystack(p), words)]


def _project_state(project) -> str:
    from app.models.project import OPERATING_STATE_CLOSED

    if getattr(project, "operating_state", None) == OPERATING_STATE_CLOSED:
        return "Closed"
    return project.status or ""


def project_item(project) -> Item:
    client = getattr(project, "client", None)
    detail = " · ".join(x for x in (client.name if client else "", project.address or "", _project_state(project)) if x)
    return Item(project.name, url_for("projects.view_project", id=project.id), detail, "project")


def _supplier_name(row) -> str:
    supplier = getattr(row, "supplier", None)
    return getattr(supplier, "legal_name", "") or ""


def _date(value) -> str:
    return value.strftime("%a %d %b %Y") if value else ""


def records_for_project(dest: str, project, org_id: str) -> list:
    """The records of one kind on one project, as links. Never writes."""
    pid = project.id
    items: list = []
    if dest == DEST_PROJECTS:
        return [project_item(project)]
    if dest == DEST_DRAWINGS:
        from app.models.construction_drawing import ConstructionDrawingSet
        from app.plan_intelligence.models import PlanDocument

        sets = (ConstructionDrawingSet.query.filter_by(organization_id=org_id, project_id=pid)
                .order_by(ConstructionDrawingSet.id.desc()).all())
        for s in sets:
            items.append(Item(f"Drawing set — model revision {s.model_revision_number}",
                              url_for("construction_drawings.preview", project_id=pid, set_id=s.id),
                              f"{project.name} · {s.status.title()} · PDF and DXF", "drawing"))
        plans = PlanDocument.query.filter_by(project_id=pid).order_by(PlanDocument.id.desc()).all()
        for doc in plans:
            items.append(Item(doc.original_filename,
                              url_for("plan_intelligence.view_plan", project_id=pid, document_id=doc.id),
                              f"{project.name} · Project Plans", "plan"))
    elif dest == DEST_ESTIMATES:
        from app.models import Estimate

        for e in (Estimate.query.filter_by(organization_id=org_id, project_id=pid)
                  .order_by(Estimate.updated_at.desc()).all()):
            items.append(Item(f"{e.estimate_number} — {e.title}", url_for("estimates.view_estimate", id=e.id),
                              f"{project.name} · {e.status}", "estimate"))
    elif dest == DEST_PROPOSALS:
        from app.models import Estimate, Proposal

        rows = (Proposal.query.join(Estimate, Proposal.estimate_id == Estimate.id)
                .filter(Proposal.organization_id == org_id, Estimate.project_id == pid)
                .order_by(Proposal.updated_at.desc()).all())
        for p in rows:
            items.append(Item(f"{p.proposal_number} — {p.title}", url_for("proposals.view_proposal", id=p.id),
                              f"{project.name} · {p.status}", "proposal"))
    elif dest == DEST_CONTRACTS:
        from app.models.project_contract import GeneratedProjectContract

        for c in (GeneratedProjectContract.query.filter_by(organization_id=org_id, project_id=pid)
                  .order_by(GeneratedProjectContract.id.desc()).all()):
            items.append(Item(f"Contract {c.contract_number}", url_for("projects.review_contract", id=pid),
                              f"{project.name} · {c.status.title()}", "contract"))
    elif dest == DEST_QUOTES:
        from app.models.supplier_portal import ConcreteRequest, SupplierRequestShare

        base = url_for("supplier_office.project_requests", project_id=pid)
        for s in (SupplierRequestShare.query.filter_by(organization_id=org_id, project_id=pid)
                  .order_by(SupplierRequestShare.sent_at.desc()).all()):
            items.append(Item(f"Supplier request {s.number}", f"{base}#share-{s.id}",
                              " · ".join(x for x in (_supplier_name(s), s.status.title(), project.name) if x), "quote"))
        for c in (ConcreteRequest.query.filter_by(organization_id=org_id, project_id=pid)
                  .order_by(ConcreteRequest.id.desc()).all()):
            items.append(Item(f"Concrete request {c.number}", f"{base}#concrete",
                              f"{project.name} · delivery {_date(c.delivery_date)}", "quote"))
    elif dest == DEST_ORDERS:
        from app.models.supplier_portal import SupplierPurchaseOrder

        base = url_for("supplier_office.project_requests", project_id=pid)
        for o in (SupplierPurchaseOrder.query.filter_by(organization_id=org_id, project_id=pid)
                  .order_by(SupplierPurchaseOrder.placed_at.desc()).all()):
            items.append(Item(f"Purchase order {o.number}", f"{base}#share-{o.share_id}",
                              " · ".join(x for x in (_supplier_name(o), o.status.title(), project.name) if x), "order"))
    elif dest == DEST_DELIVERIES:
        from app.services.supplier_hub import upcoming_deliveries

        base = url_for("supplier_office.project_requests", project_id=pid)
        for row in upcoming_deliveries(organization_id=org_id, project_id=pid):
            order, sched = row["order"], row["schedule"]
            when = _date(sched["date"]) or "date not set"
            items.append(Item(f"Delivery — {order.number}", f"{base}#share-{order.share_id}",
                              f"{when}{' · ' + sched['window'] if sched['window'] else ''} · {project.name}", "delivery"))
    elif dest == DEST_CALENDAR:
        items.append(Item(f"Company Calendar — {project.name}", url_for("schedule.company", project_id=pid),
                          "This project's scheduled work", "calendar"))
    return items


def company_wide(dest: str, org_id: str) -> list:
    """The most recent records of one kind across the organization, when no project was named."""
    from app.models import Estimate, Project, Proposal

    items: list = []
    if dest == DEST_PROJECTS:
        projects = (Project.query.filter(Project.organization_id == org_id)
                    .order_by(Project.id.desc()).limit(MAX_PER_GROUP).all())
        items = [project_item(p) for p in projects]
        items.append(Item("All projects", url_for("projects.list_projects"), "The Projects register", "tool"))
    elif dest == DEST_ESTIMATES:
        for e in (Estimate.query.filter_by(organization_id=org_id).order_by(Estimate.updated_at.desc())
                  .limit(MAX_PER_GROUP - 1).all()):
            items.append(Item(f"{e.estimate_number} — {e.title}", url_for("estimates.view_estimate", id=e.id),
                              f"{e.project.name if e.project else ''} · {e.status}", "estimate"))
        items.append(Item("All estimates", url_for("estimates.list_estimates"), "The Estimates register", "tool"))
    elif dest == DEST_PROPOSALS:
        for p in (Proposal.query.filter_by(organization_id=org_id).order_by(Proposal.updated_at.desc())
                  .limit(MAX_PER_GROUP - 1).all()):
            items.append(Item(f"{p.proposal_number} — {p.title}", url_for("proposals.view_proposal", id=p.id),
                              p.status, "proposal"))
        items.append(Item("All proposals", url_for("proposals.list_proposals"), "The Proposals register", "tool"))
    elif dest == DEST_DELIVERIES:
        from app.services.supplier_hub import upcoming_deliveries

        for row in upcoming_deliveries(organization_id=org_id)[: MAX_PER_GROUP - 1]:
            order, sched, project = row["order"], row["schedule"], row["project"]
            items.append(Item(f"Delivery — {order.number}",
                              url_for("supplier_office.project_requests", project_id=order.project_id) + f"#share-{order.share_id}",
                              f"{_date(sched['date']) or 'date not set'} · {project.name if project else ''}", "delivery"))
        items.append(Item("All deliveries", url_for("supplier_office.deliveries"), "Every upcoming delivery", "tool"))
    elif dest == DEST_CALENDAR:
        items.append(Item("Company Calendar", url_for("schedule.company"), "Every crew, every job, by day", "tool"))
    else:
        # Drawings, contracts, quotations and purchase orders live on a project.
        rows = []
        for p in Project.query.filter(Project.organization_id == org_id).order_by(Project.id.desc()).all():
            found = records_for_project(dest, p, org_id)
            rows += found
            if len(rows) >= MAX_PER_GROUP:
                break
        items = rows
    return items


def match_references(org_id: str, refs) -> list:
    """Exact record numbers: estimate, proposal, contract, supplier request, purchase order, project."""
    from sqlalchemy import func

    from app.models import Estimate, Project, Proposal
    from app.models.project_contract import GeneratedProjectContract
    from app.models.supplier_portal import ConcreteRequest, SupplierPurchaseOrder, SupplierRequestShare

    items: list = []
    for ref in refs:
        for p in Project.query.filter(Project.organization_id == org_id, func.lower(Project.project_number) == ref).all():
            items.append(project_item(p))
        for e in Estimate.query.filter(Estimate.organization_id == org_id, func.lower(Estimate.estimate_number) == ref).all():
            items.append(Item(f"{e.estimate_number} — {e.title}", url_for("estimates.view_estimate", id=e.id),
                              f"Estimate · {e.status}", "estimate"))
        for p in Proposal.query.filter(Proposal.organization_id == org_id, func.lower(Proposal.proposal_number) == ref).all():
            items.append(Item(f"{p.proposal_number} — {p.title}", url_for("proposals.view_proposal", id=p.id),
                              f"Proposal · {p.status}", "proposal"))
        for c in GeneratedProjectContract.query.filter(GeneratedProjectContract.organization_id == org_id,
                                                       func.lower(GeneratedProjectContract.contract_number) == ref).all():
            items.append(Item(f"Contract {c.contract_number}", url_for("projects.review_contract", id=c.project_id),
                              "Contract", "contract"))
        for s in SupplierRequestShare.query.filter(SupplierRequestShare.organization_id == org_id,
                                                   func.lower(SupplierRequestShare.number) == ref).all():
            items.append(Item(f"Supplier request {s.number}",
                              url_for("supplier_office.project_requests", project_id=s.project_id) + f"#share-{s.id}",
                              f"Supplier quotation · {s.status.title()}", "quote"))
        for o in SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.organization_id == org_id,
                                                    func.lower(SupplierPurchaseOrder.number) == ref).all():
            items.append(Item(f"Purchase order {o.number}",
                              url_for("supplier_office.project_requests", project_id=o.project_id) + f"#share-{o.share_id}",
                              f"Purchase order · {o.status.title()}", "order"))
        for c in ConcreteRequest.query.filter(ConcreteRequest.organization_id == org_id,
                                              func.lower(ConcreteRequest.number) == ref).all():
            items.append(Item(f"Concrete request {c.number}",
                              url_for("supplier_office.project_requests", project_id=c.project_id) + "#concrete",
                              "Concrete request", "quote"))
    return items


# ---------------------------------------------------------------- platform tools and Help

def _tool_visible(item) -> bool:
    from app.shell import _nav_item_visible

    return item.get("enabled", True) and bool(item.get("endpoint")) and _nav_item_visible(item, True)


def platform_tools() -> list:
    """Every menu destination this user can open, from the single navigation source."""
    tools = []
    for section in NAV_SECTIONS:
        for item in section["links"]:
            if not _tool_visible(item):
                continue
            try:
                url = url_for(item["endpoint"])
            except Exception:
                continue
            tools.append(Item(item["title"], url, section["title"] or "Menu", "tool"))
    return tools


def match_tools(words) -> list:
    generic = {"calculator", "calculators", "page", "screen", "tool", "tools"}
    useful = [w for w in words if w not in generic]
    if not useful:
        return []
    out = []
    for tool in platform_tools():
        hay = _normalize(f"{tool.title} {tool.detail}")
        if all(any(h.startswith(w) or w in h for h in hay.split()) for w in useful):
            out.append(tool)
    return out


# Help topics that belong to a page with no project in its address.
HELP_TOPIC_ENDPOINTS = {
    "dashboard": ("main.dashboard", {}),
    "clients": ("clients.list_clients", {}),
    "projects_current": ("projects.list_projects", {}),
    "projects_closed": ("projects.list_projects", {"view": "closed"}),
    "schedule": ("schedule.company", {}),
    "company_attention": ("company_attention.index", {}),
    "estimating": ("estimates.list_estimates", {}),
    "previous_estimates": ("historical_estimates.index", {}),
    "costs_and_pricing": ("costs_and_pricing.index", {}),
    "cost_library": ("cost_library.list_cost_items", {}),
    "reusable_work": ("assemblies.list_assemblies", {}),
    "how_we_price": ("pricing_engine.index", {}),
    "settings_brand_profile": ("settings.brand_profile", {}),
    "time_review": ("time_entry.review", {}),
    "change_orders": ("project_controls.list_change_orders", {}),
}


def _company_management_allowed() -> bool:
    from app.navigation import NAV_ITEMS

    for item in NAV_ITEMS:
        if item.get("endpoint") == "company_attention.index":
            return _tool_visible(item)
    return False


def match_help(words, wants_help: bool) -> list:
    """Existing Help topics whose title or text contains the words. Help text is shown as written."""
    if not words and not wants_help:
        return []
    out = []
    for key, (endpoint, args) in HELP_TOPIC_ENDPOINTS.items():
        topic = help_content.OFFICE_TOPICS.get(key)
        if topic is None or topic.future:
            continue
        if key == "company_attention" and not _company_management_allowed():
            continue
        title_hay = _normalize(topic.title)
        text_hay = _normalize(" ".join(x for x in (topic.what, topic.do or "", topic.next or "") if x))
        if not words or not all(w in text_hay or w in title_hay for w in words):
            continue
        rank = -sum(1 for w in words if w in title_hay)
        out.append((rank, Item(f"Help: {topic.title}", url_for(endpoint, **args) + f"#help-{topic.key}",
                               topic.what, "help")))
    out.sort(key=lambda t: t[0])
    return [i for _, i in out]


# ---------------------------------------------------------------- the answer

MSG_EMPTY = "Type what you are looking for, for example “Harbour Lane drawings” or “proposals”."
MSG_NONE = "Cal could not find anything that matches “{q}” in records you can open."
MSG_NONE_HINT = "Try a project name, a client name, an address or a record number such as an estimate number."
MSG_NO_PROJECT = "No project you can open matches “{words}”."
MSG_AMBIGUOUS = "More than one project matches “{words}”. Which one do you mean?"
MSG_PROJECT_EMPTY = "{project} has no {what} yet."


def find(raw_query: str) -> dict:
    """Answer one Find It query for the signed-in office user. Read-only."""
    parsed = parse_query(raw_query)
    if not parsed.raw or not (parsed.words or parsed.intents or parsed.wants_help):
        return {"query": parsed.raw, "status": "empty", "message": MSG_EMPTY, "groups": []}
    if not getattr(current_user, "is_authenticated", False):
        return {"query": parsed.raw, "status": "signed_out", "message": "Sign in to use Cal.", "groups": []}

    org_id = _org_id()
    groups: list = []
    message = ""
    status = "results"
    dest = next((d for d in parsed.intents if d != DEST_PROJECTS), parsed.intents[0] if parsed.intents else None)

    referenced = match_references(org_id, parsed.refs) if parsed.refs else []
    if referenced:
        groups.append(Group("Records", referenced))

    project_words = [w for w in parsed.words if w not in parsed.refs] if referenced else parsed.words
    projects = match_projects(org_id, project_words) if project_words else []
    tools = match_tools(parsed.words)
    help_items = match_help(parsed.words if not dest else [w for w in parsed.words], parsed.wants_help)

    if dest and dest != DEST_PROJECTS:
        what = DEST_TITLES[dest].lower()
        if not project_words:
            groups.append(Group(DEST_TITLES[dest], company_wide(dest, org_id)))
        elif len(projects) == 1:
            found = records_for_project(dest, projects[0], org_id)
            if found:
                groups.append(Group(f"{DEST_TITLES[dest]} — {projects[0].name}", found))
            else:
                message = MSG_PROJECT_EMPTY.format(project=projects[0].name, what=what)
                groups.append(Group("Project", [project_item(projects[0])]))
        elif len(projects) > 1:
            status = "ambiguous"
            message = MSG_AMBIGUOUS.format(words=" ".join(project_words))
            choices = []
            for p in projects[:MAX_PER_GROUP]:
                found = records_for_project(dest, p, org_id)
                item = project_item(p)
                if found:
                    item = Item(p.name, found[0].url if len(found) == 1 else item.url,
                                f"{item.detail} · {len(found)} {what}", "project")
                else:
                    item.detail = f"{item.detail} · no {what} yet"
                choices.append(item)
            groups.append(Group("Which project?", choices))
        elif not referenced and not tools:
            status = "none"
            message = MSG_NO_PROJECT.format(words=" ".join(project_words))
            groups.append(Group(DEST_TITLES[dest], company_wide(dest, org_id)[-1:]))
    else:
        if len(projects) > 1 and not referenced:
            status = "ambiguous"
            message = MSG_AMBIGUOUS.format(words=" ".join(project_words))
            groups.append(Group("Which project?", [project_item(p) for p in projects]))
        elif projects:
            groups.append(Group("Projects", [project_item(p) for p in projects]))
            if len(projects) == 1:
                shortcuts = []
                for d in (DEST_DRAWINGS, DEST_ESTIMATES, DEST_PROPOSALS, DEST_CONTRACTS, DEST_QUOTES, DEST_DELIVERIES):
                    found = records_for_project(d, projects[0], org_id)
                    if found:
                        shortcuts.append(Item(DEST_TITLES[d], found[0].url if len(found) == 1 else found[0].url,
                                              f"{len(found)} on {projects[0].name}", d))
                if shortcuts:
                    groups.append(Group("On this project", shortcuts))
        elif dest == DEST_PROJECTS and not project_words:
            groups.append(Group("Projects", company_wide(DEST_PROJECTS, org_id)))

    if tools:
        groups.append(Group("Tools", tools))
    if help_items:
        groups.append(Group("Help", help_items))

    groups = [g for g in groups if g.items]
    if not groups:
        status = "none"
        message = message or MSG_NONE.format(q=parsed.raw)
        return {"query": parsed.raw, "status": status, "message": message, "hint": MSG_NONE_HINT, "groups": []}
    return {"query": parsed.raw, "status": status, "message": message, "groups": [g.as_dict() for g in groups]}
