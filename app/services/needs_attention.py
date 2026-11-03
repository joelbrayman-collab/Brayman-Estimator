"""WHAT NEEDS MY ATTENTION? — the ONE attention list (Magnificent Seven, 25 Oct 2026; Task-First UX, 31 Oct 2026).

Layer 1 of the Task-First model: "what requires me?". Derived live from the real records every time it is shown;
nothing is stored, so there is no second task list and a resolved item simply stops being listed. Each item says
what needs attention, the job or person, why it is waiting, the date or urgency, and links straight to the task
screen (or the exact anchor) where the decision is made. One Click to Action never approves anything: the link
opens the screen where the person decides.

A REGISTRY OF PROVIDERS (Task-First UX, 31 Oct 2026). Each provider is one kind of governed event. It returns
items and declares the permission scope of the people who may act on it; ``assemble`` runs only the providers the
viewer's existing permissions allow (no visual-only security: the target pages keep their own checks).

    Scope            Who sees it (existing permission model, app/services/access_domains.py, instance_authority.py)
    office           any office member (Field-only crew never see the list at all)
    financial        has_office_financial_access (receipts, QuickBooks: the /accounting rule)
    company          COMPANY_MANAGEMENT access domain, or the Instance Owner (Gate 3, company schedule changes)
    company_facts    COMPANY_MANAGEMENT access domain only (the labour and schedule facts of Company Attention)
    owner_admin      the Instance Owner or a System Administrator (closing a project)

Extension hook — ``extra_attention_providers``: another feature (e.g. Documents) registers its own provider without
editing this file::

    from app.services.needs_attention import AttentionProvider, register_attention_provider

    def _documents(ctx):          # ctx: AttentionContext (org, viewer, today, projects, link(), item())
        return [ctx.item("documents", "Drawing revision to review", "Smith deck", "New revision uploaded", "",
                         ctx.link("documents.project_documents", project_id=7), "Review the drawing",
                         project_id=7)]

    register_attention_provider(AttentionProvider("documents_review", "documents", "office", _documents), app=app)

Providers registered with ``app=`` live in ``app.extensions["extra_attention_providers"]`` (per application, so
tests stay isolated). An item keeps the original keys (kind, what, who, status, when, href, action, urgency) and adds
title (= what), why (= status), due (= when), severity, scope, provider, project_id and waiting_on ("you" or
"others": a customer, supplier or subcontractor has the next move).
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable, Optional

from flask import current_app, has_request_context, url_for

from app import db
from app.models import Project
from app.models.field_operations import (
    EXCEPTION_OPEN,
    MR_APPROVED,
    MR_SUBMITTED,
    PROBLEM_OPEN,
    RECEIPT_NEEDS_ATTENTION,
    RECEIPT_NEW,
    RECEIPT_REVIEWED,
    RECEIPT_SYNC_FAILED,
    DailyJobSummary,
    DeliveryConfirmation,
    FieldMaterialRequest,
    FieldReceipt,
)
from app.models.time_entry import TIME_STATUS_RETURNED, TIME_STATUS_SUBMITTED, TIME_STATUS_SUPERSEDED, LabourTimeEntry
from app.services.local_time import local_date, local_now, local_today

_log = logging.getLogger(__name__)

URGENCY_ORDER = {"overdue": 0, "today": 1, "soon": 2, "": 3}
MISSING_TIME_DAYS = 5
QUOTE_OVERDUE_DAYS = 7      # a subcontract quote asked for more than a week ago is overdue
PROPOSAL_QUIET_DAYS = 5     # a proposal sent this long ago with no answer is worth a call
SIGNING_EXPIRY_SOON_DAYS = 3

SCOPE_OFFICE = "office"
SCOPE_FINANCIAL = "financial"
SCOPE_COMPANY = "company"
SCOPE_COMPANY_FACTS = "company_facts"
SCOPE_OWNER_ADMIN = "owner_admin"
# The Supplier Hub (Slice C, 1 Nov 2026): providers for a store's own list. Never on the office list (scope_allows
# refuses it); run only by ``assemble_for_supplier`` for one store.
SCOPE_SUPPLIER = "supplier"
SCOPES = (SCOPE_OFFICE, SCOPE_FINANCIAL, SCOPE_COMPANY, SCOPE_COMPANY_FACTS, SCOPE_OWNER_ADMIN, SCOPE_SUPPLIER)

# Plain words for each kind (the filter chips on the attention list). Kind codes never show.
KIND_LABELS = {
    "estimates": "Estimates", "proposals": "Proposals", "customers": "Customers", "signing": "Signatures & contracts",
    "purchasing": "Purchasing", "quotes": "Supplier prices", "materials": "Material requests",
    "deliveries": "Deliveries", "planning": "Dates to decide", "schedule": "Schedule", "extra_work": "Changes & extra work",
    "time": "Time", "receipts": "Receipts", "quickbooks": "QuickBooks", "tasks": "Job problems & punch list",
    "closeout": "Closing jobs", "labour": "Labour hours", "texts": "Crew texts", "documents": "Documents",
}


def kind_label(kind: str) -> str:
    return KIND_LABELS.get(kind, (kind or "").replace("_", " ").capitalize())


WAITING_ON_YOU = "you"
WAITING_ON_OTHERS = "others"


def _day(d: Optional[date]) -> str:
    if d is None:
        return ""
    return f"{d:%a %b} {d.day}"


def _item(kind, what, who, status, when, href, action, *, urgency="", sort_date=None, project_id=None,
          waiting_on=WAITING_ON_YOU):
    return {"kind": kind, "what": what, "who": who, "status": status, "when": when, "href": href, "action": action,
            "urgency": urgency, "sort_date": sort_date or date.max,
            # Task-First names for the same facts (31 Oct 2026)
            "title": what, "why": status, "due": when, "severity": urgency or "info",
            "project_id": project_id, "waiting_on": waiting_on, "scope": SCOPE_OFFICE, "provider": ""}


def _urgency(d: Optional[date], today: date) -> str:
    if d is None:
        return ""
    if d < today:
        return "overdue"
    if d == today:
        return "today"
    if d <= today + timedelta(days=2):
        return "soon"
    return ""


def _link(endpoint: str, _anchor: Optional[str] = None, **values) -> str:
    """url_for, also outside a request (the reminder job reads the list from a command)."""
    if has_request_context():
        return url_for(endpoint, _anchor=_anchor, **values) if _anchor else url_for(endpoint, **values)
    adapter = current_app.url_map.bind("localhost")
    path = adapter.build(endpoint, values, force_external=False)
    return f"{path}#{_anchor}" if _anchor else path


def _projects(org):
    return {p.id: p for p in Project.query.filter_by(organization_id=org).all()}


def _label(project) -> str:
    if project is None:
        return ""
    number = (project.project_number or "").strip()
    return f"{project.name}" + (f" ({number})" if number else "")


def _open(project) -> bool:
    return project is not None and (project.operating_state or "ACTIVE") != "CLOSED"


# ================================================================================================= registry
@dataclass
class AttentionContext:
    """What every provider is given: the company, the person, today, the company's projects and helpers."""

    org: str
    viewer: object
    today: date
    projects: dict
    roles: dict = field(default_factory=dict)
    items_so_far: list = field(default_factory=list)
    # Review fix I2 (1 Nov 2026): the Project page's list. A provider may filter its query by this project (SQL);
    # assemble() still keeps only this project's items, so the result is the same either way.
    project_id: Optional[int] = None

    link = staticmethod(_link)
    item = staticmethod(_item)
    label = staticmethod(_label)
    day = staticmethod(_day)
    urgency = staticmethod(_urgency)

    def project(self, project_id):
        return self.projects.get(project_id)


@dataclass(frozen=True)
class AttentionProvider:
    key: str          # stable name, e.g. "estimate_ready_for_approval"
    kind: str         # the item kind (filters and counts), e.g. "estimates"
    scope: str        # one of SCOPES: who may act on it
    collect: Callable[[AttentionContext], list]
    title: str = ""   # what the provider surfaces, in plain words (documentation and tests)


PROVIDERS: list = []


def attention_provider(key, kind, scope=SCOPE_OFFICE, title=""):
    def wrap(fn):
        PROVIDERS.append(AttentionProvider(key, kind, scope, fn, title or (fn.__doc__ or "").strip().split("\n")[0]))
        return fn
    return wrap


def register_attention_provider(provider: AttentionProvider, *, app=None) -> AttentionProvider:
    """The ``extra_attention_providers`` hook: add a provider from another feature (see the module docstring)."""
    if provider.scope not in SCOPES:
        raise ValueError(f"Unknown attention scope {provider.scope!r}.")
    target = app or current_app
    target.extensions.setdefault("extra_attention_providers", []).append(provider)
    return provider


def extra_attention_providers() -> list:
    try:
        return list(current_app.extensions.get("extra_attention_providers", []))
    except RuntimeError:  # no application context
        return []


def all_providers() -> list:
    return PROVIDERS + extra_attention_providers()


def viewer_roles(viewer, org) -> dict:
    from app.services.access_domains import (
        ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        has_office_financial_access,
        membership_has_access_domain,
        user_is_field_only,
    )
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    if viewer is None or not getattr(viewer, "is_authenticated", True):
        return {"office": False}
    field_only = user_is_field_only(viewer, org)
    owner = is_instance_owner(viewer, org)
    admin = is_system_administrator(viewer, org)
    company = membership_has_access_domain(viewer, org, ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    return {"office": not field_only, "field_only": field_only, "financial": has_office_financial_access(viewer, org),
            "owner": owner, "admin": admin, "company_management": company}


def scope_allows(scope: str, roles: dict) -> bool:
    if not roles.get("office"):
        return False
    if scope == SCOPE_OFFICE:
        return True
    if scope == SCOPE_FINANCIAL:
        return bool(roles.get("financial"))
    if scope == SCOPE_COMPANY:
        return bool(roles.get("company_management") or roles.get("owner"))
    if scope == SCOPE_COMPANY_FACTS:
        return bool(roles.get("company_management"))
    if scope == SCOPE_OWNER_ADMIN:
        return bool(roles.get("owner") or roles.get("admin"))
    return False


def assemble(organization_id: str, viewer, *, today: Optional[date] = None, include_company_facts=None,
             project_id: Optional[int] = None) -> dict:
    """The attention list for one person. ``project_id`` narrows it to one job (the Project page)."""
    org = organization_id
    today = today or local_today()
    roles = viewer_roles(viewer, org)
    if not roles.get("office"):
        return {"items": [], "count": 0, "hidden": True, "kinds": {}, "waiting_on_you": [], "waiting_on_others": []}
    if include_company_facts is not None:
        roles = {**roles, "company_management_facts": include_company_facts}
    ctx = AttentionContext(org=org, viewer=viewer, today=today, projects=_projects(org), roles=roles,
                           project_id=project_id)
    items = []
    for provider in all_providers():
        if provider.scope == SCOPE_COMPANY_FACTS and include_company_facts is not None:
            if not include_company_facts:
                continue
        elif not scope_allows(provider.scope, roles):
            continue
        try:
            found = provider.collect(ctx) or []
        except Exception:  # never let one source hide the rest
            if current_app.testing:
                raise
            _log.exception("attention provider %s could not be read", provider.key)
            continue
        for row in found:
            row.setdefault("provider", provider.key)
            if not row.get("provider"):
                row["provider"] = provider.key
            row["scope"] = provider.scope
            items.append(row)
        ctx.items_so_far = items
    if project_id is not None:
        items = [i for i in items if i.get("project_id") == project_id]
    items.sort(key=lambda i: (i.get("waiting_on") == WAITING_ON_OTHERS, URGENCY_ORDER.get(i["urgency"], 3),
                              i["sort_date"], i["what"]))
    kinds = defaultdict(int)
    for i in items:
        kinds[i["kind"]] += 1
    mine = [i for i in items if i.get("waiting_on") != WAITING_ON_OTHERS]
    others = [i for i in items if i.get("waiting_on") == WAITING_ON_OTHERS]
    if project_id is None and include_company_facts is None and today == local_today():
        _remember_bell(org, viewer, len(mine))  # the same list the bell counts: the page's bell needs no second read
    return {"items": items, "count": len(items), "hidden": False, "kinds": dict(kinds),
            "waiting_on_you": mine, "waiting_on_others": others}


@dataclass
class SupplierAttentionContext:
    """What a Supplier Hub provider is given: the one store, today and the same helpers."""

    supplier_id: int
    today: date

    link = staticmethod(_link)
    item = staticmethod(_item)
    day = staticmethod(_day)


def assemble_for_supplier(supplier_id: int, *, today: Optional[date] = None) -> list:
    """The Supplier Hub's registry items for one store (scope ``supplier``), oldest first. The store's existing
    counts (quotes, orders, delivery changes, deliveries) stay in app/services/supplier_insights.attention."""
    ctx = SupplierAttentionContext(supplier_id=supplier_id, today=today or local_today())
    items = []
    for provider in all_providers():
        if provider.scope != SCOPE_SUPPLIER:
            continue
        try:
            found = provider.collect(ctx) or []
        except Exception:  # never let one source hide the rest
            if current_app.testing:
                raise
            _log.exception("supplier attention provider %s could not be read", provider.key)
            continue
        for row in found:
            row["provider"], row["scope"] = provider.key, SCOPE_SUPPLIER
            items.append(row)
    items.sort(key=lambda i: (i["sort_date"], i["what"]))
    return items


# Review fix I2 (1 Nov 2026): the header bell asks for its count on every page. It is a hint, so it is answered from a
# short per-person cache (per app process), filled by the bell itself or by any page that just assembled the same list
# (Home, the full list, Purchasing, Time & Money). The attention list itself is always assembled fresh.
BELL_CACHE_SECONDS = 60
_BELL_CACHE_MAX = 2000


def _now() -> float:
    return time.monotonic()


def _bell_key(organization_id, viewer):
    user_id = getattr(viewer, "id", None)
    if user_id is None:
        return None
    return (organization_id, int(user_id), local_today())


def _bell_cache() -> dict:
    return current_app.extensions.setdefault("attention_bell_cache", {})


def _remember_bell(organization_id, viewer, count: int) -> None:
    key = _bell_key(organization_id, viewer)
    if key is None:
        return
    cache = _bell_cache()
    if len(cache) >= _BELL_CACHE_MAX:
        cutoff = _now() - BELL_CACHE_SECONDS
        for stale in [k for k, (at, _n) in cache.items() if at < cutoff]:
            cache.pop(stale, None)
        if len(cache) >= _BELL_CACHE_MAX:
            cache.clear()
    cache[key] = (_now(), count)


def count_for(organization_id: str, viewer) -> int:
    """The header bell: how many items are waiting on this person (not on others). Cached for BELL_CACHE_SECONDS."""
    key = _bell_key(organization_id, viewer)
    hit = _bell_cache().get(key) if key is not None else None
    if hit is not None and _now() - hit[0] < BELL_CACHE_SECONDS:
        return hit[1]
    view = assemble(organization_id, viewer)
    count = len(view.get("waiting_on_you") or [])
    _remember_bell(organization_id, viewer, count)
    return count


# ================================================================================================= helpers
def working_days(org) -> set:
    from app.services.reminders import settings_for

    raw = settings_for(org).working_days or ""
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


def missing_time(org, *, today: date, include_today: bool = False) -> list:
    """(user_id, name, day, [project ids]) for scheduled people with no time at all entered for that day."""
    from sqlalchemy.orm import joinedload, selectinload

    from app.models.schedule import SCHEDULE_STATUS_ACTIVE, WorkScheduleAssignment, WorkScheduleItem
    from app.models.user import UserMembership
    from app.services.daily_summaries import item_workers

    days = working_days(org)
    out = []
    active = {m.user_id for m in UserMembership.query.filter_by(organization_id=org, is_active=True).all()}
    start = 0 if include_today else 1
    first, last = today - timedelta(days=MISSING_TIME_DAYS), today - timedelta(days=start)
    # Review fix I2 (1 Nov 2026): the window's scheduled work (with its people) and time entries in one query each,
    # instead of per day and per assignment; each day then sees exactly daily_summaries.scheduled_items(org, None, day).
    window_items = (WorkScheduleItem.query
                    .options(selectinload(WorkScheduleItem.assignments).joinedload(WorkScheduleAssignment.worker))
                    .filter(WorkScheduleItem.organization_id == org, WorkScheduleItem.status == SCHEDULE_STATUS_ACTIVE,
                            WorkScheduleItem.scheduled_start <= last, WorkScheduleItem.scheduled_end >= first)
                    .order_by(WorkScheduleItem.id).all())
    entered_on = defaultdict(set)
    if window_items:
        for user_id, work_date in db.session.query(LabourTimeEntry.worker_user_id, LabourTimeEntry.work_date).filter(
                LabourTimeEntry.organization_id == org, LabourTimeEntry.work_date >= first,
                LabourTimeEntry.work_date <= last, LabourTimeEntry.status != TIME_STATUS_SUPERSEDED).all():
            entered_on[work_date].add(user_id)
    for back in range(start, MISSING_TIME_DAYS + 1):
        day = today - timedelta(days=back)
        if day.weekday() not in days:
            continue
        people = defaultdict(lambda: {"name": "", "projects": set()})
        for item in window_items:
            if not (item.scheduled_start <= day <= item.scheduled_end):
                continue
            for user_id, name in item_workers(item, day).items():
                if user_id in active:
                    people[user_id]["name"] = name
                    people[user_id]["projects"].add(item.project_id)
        if not people:
            continue
        entered = entered_on.get(day, set())
        for user_id, row in people.items():
            if user_id not in entered:
                out.append((user_id, row["name"], day, sorted(row["projects"])))
    return out


def _reminder_time(org) -> str:
    from app.services.reminders import settings_for

    return settings_for(org).reminder_time or "16:30"


# ================================================================================================= providers
# ---- existing items (Magnificent Seven, 25 Oct 2026): same words, links now built with url_for
@attention_provider("time_to_approve", "time", title="Time entries to approve, returned time, missing time")
def _time(ctx):
    if ctx.project_id is not None:
        return []  # none of these items belongs to one project (the Project page never shows them)
    org, today, projects = ctx.org, ctx.today, ctx.projects
    items = []
    submitted = defaultdict(list)
    returned = defaultdict(list)
    for e in LabourTimeEntry.query.filter(LabourTimeEntry.organization_id == org,
                                          LabourTimeEntry.status.in_((TIME_STATUS_SUBMITTED, TIME_STATUS_RETURNED))):
        (submitted if e.status == TIME_STATUS_SUBMITTED else returned)[(e.worker_user_id, e.worker_display_name)].append(e)
    for (uid, name), rows in submitted.items():
        oldest = min(r.work_date for r in rows)
        hours = sum(float(r.hours) for r in rows)
        items.append(_item("time", f"{len(rows)} time entr{'y' if len(rows) == 1 else 'ies'} to approve "
                           f"({hours:g} h)", name, "Waiting for approval", f"Since {_day(oldest)}",
                           _link("time_entry.review", status="SUBMITTED", worker_user_id=uid), "Review time",
                           urgency="overdue" if oldest < today - timedelta(days=2) else "today", sort_date=oldest))
    for (uid, name), rows in returned.items():
        items.append(_item("time", f"{len(rows)} returned time entr{'y' if len(rows) == 1 else 'ies'} not fixed yet",
                           name, "Returned to the worker", _day(min(r.work_date for r in rows)),
                           _link("time_entry.review", status="RETURNED", worker_user_id=uid), "Open time",
                           sort_date=min(r.work_date for r in rows), waiting_on=WAITING_ON_OTHERS))
    show_today = local_now().strftime("%H:%M") >= _reminder_time(org)
    for uid, name, day, project_ids in missing_time(org, today=today, include_today=show_today):
        jobs = ", ".join(_label(projects.get(pid)) for pid in project_ids)
        items.append(_item("time", "No time entered", f"{name} · {jobs}", "Scheduled, no time", _day(day),
                           _link("time_entry.review", worker_user_id=uid, **{"from": day.isoformat(),
                                                                             "to": day.isoformat()}),
                           "Check time", urgency="overdue" if day < today else "today", sort_date=day))
    return items


@attention_provider("material_requests", "materials", title="Material requests to review or send to a supplier")
def _materials(ctx):
    items = []
    query = FieldMaterialRequest.query.filter(FieldMaterialRequest.organization_id == ctx.org,
                                              FieldMaterialRequest.status.in_((MR_SUBMITTED, MR_APPROVED)))
    if ctx.project_id is not None:
        query = query.filter(FieldMaterialRequest.project_id == ctx.project_id)
    for r in query:
        status = "Waiting for your review" if r.status == MR_SUBMITTED else "Approved — choose the supplier"
        items.append(_item("materials", f"Material request: {r.description}",
                           f"{_label(ctx.projects.get(r.project_id))} · {r.requested_by_name}", status,
                           ("Needed by " + _day(r.needed_by)) if r.needed_by else f"Asked {_day(local_date(r.requested_at))}",
                           _link("operations.material_request", request_id=r.id), "Review request",
                           urgency=_urgency(r.needed_by, ctx.today) or "today", sort_date=r.needed_by or ctx.today,
                           project_id=r.project_id))
    return items


@attention_provider("extra_work", "extra_work", title="Extra work reported, not on a change order, or awaiting approval")
def _extra_work(ctx):
    from app.models.work_structure import ProjectWorkActivity
    from app.project_controls.models import ChangeOrder
    from app.services import extra_work_reports as ew
    from app.services.work_scope import inherit_scope_lineage

    projects = ctx.projects
    items = []
    reported_activities = set()
    for r in ew.office_list(ctx.org, open_only=False):
        reported_activities.add(r.activity_id)
        if not ew.needs_office(r):
            continue
        co = ew.change_order(r)
        if co is not None:
            items.append(_item("extra_work", f"Change order {co.number} for extra work: {r.description[:80]}",
                               _label(projects.get(r.project_id)), f"Change order {co.status}",
                               _day(r.work_date), _link("project_controls.view_change_order", id=co.id),
                               "Open the change order", sort_date=r.work_date, project_id=r.project_id))
        else:
            items.append(_item("extra_work", f"Extra work reported: {r.description[:80]}",
                               f"{_label(projects.get(r.project_id))} · {r.reported_by_name}",
                               "Answered — review it" if r.status == "ANSWERED" else "Waiting for your review",
                               _day(r.work_date), _link("operations.extra_work_report", report_id=r.id),
                               "Review extra work", urgency="today", sort_date=r.work_date, project_id=r.project_id))
    for activity in ProjectWorkActivity.query.filter_by(organization_id=ctx.org, scope_origin="EXTRA_WORK",
                                                        status="ACTIVE"):
        if activity.id in reported_activities or activity.change_order_id:
            continue
        if inherit_scope_lineage(activity)["effective_origin"] != "EXTRA_WORK":
            continue
        project = projects.get(activity.element.project_id) if activity.element else None
        if project is None:
            continue
        # The work plan is where this work is put on a change order (its "Add change order work item" action).
        items.append(_item("extra_work", f"Extra work not on a change order: {activity.display_name}",
                           _label(project), "No change order yet", "",
                           _link("work_structure.project_work_plan", project_id=project.id),
                           "Review extra work", project_id=project.id))
    seen_co = {i["href"] for i in items}
    for co in ChangeOrder.query.filter(ChangeOrder.organization_id == ctx.org, ChangeOrder.status == "Pending Approval"):
        href = _link("project_controls.view_change_order", id=co.id)
        if href in seen_co:
            continue
        items.append(_item("extra_work", f"Change order {co.number}: {co.title}", _label(projects.get(co.project_id)),
                           "Waiting for the customer's approval", _day(co.requested_date), href,
                           "Open the change order", sort_date=co.requested_date, project_id=co.project_id,
                           waiting_on=WAITING_ON_OTHERS))
    return items


@attention_provider("supplier_quotes_and_orders", "quotes", title="Supplier prices returned or awaited; PO problems; delivery changes")
def _suppliers(ctx):
    from app.models.supplier_portal import (
        PO_PROBLEM,
        SHARE_OPENED,
        SHARE_RETURNED,
        SHARE_SENT,
        SupplierDeliveryChange,
        SupplierPurchaseOrder,
        SupplierRequestShare,
    )

    org, today, projects = ctx.org, ctx.today, ctx.projects
    items = []
    ordered = {row[0] for row in db.session.query(SupplierPurchaseOrder.share_id).filter(
        SupplierPurchaseOrder.organization_id == org).all()}
    for share in SupplierRequestShare.query.filter(SupplierRequestShare.organization_id == org,
                                                   SupplierRequestShare.status.in_((SHARE_SENT, SHARE_OPENED,
                                                                                    SHARE_RETURNED))):
        if share.id in ordered:
            continue
        needed = None
        try:
            raw = (share.shared_json or {}).get("needed_by")
            needed = date.fromisoformat(raw) if raw else None
        except (TypeError, ValueError):
            needed = None
        href = _link("supplier_office.project_requests", project_id=share.project_id, _anchor=f"share-{share.id}")
        if share.status == SHARE_RETURNED:
            items.append(_item("quotes", f"Price returned by {share.supplier.legal_name} ({share.number})",
                               _label(projects.get(share.project_id)), "Review the price and order",
                               ("Needed by " + _day(needed)) if needed else _day(local_date(share.returned_at)),
                               href, "Review and order", urgency=_urgency(needed, today) or "today",
                               sort_date=needed or today, project_id=share.project_id))
        else:
            items.append(_item("quotes", f"Waiting for a price from {share.supplier.legal_name} ({share.number})",
                               _label(projects.get(share.project_id)),
                               "Opened by the supplier" if share.status == SHARE_OPENED else "Sent to the supplier",
                               ("Needed by " + _day(needed)) if needed else f"Asked {_day(local_date(share.sent_at))}",
                               href, "Open the request", urgency=_urgency(needed, today),
                               sort_date=needed or date.max, project_id=share.project_id,
                               waiting_on=WAITING_ON_OTHERS))
    for order in SupplierPurchaseOrder.query.filter_by(organization_id=org, status=PO_PROBLEM):
        items.append(_item("deliveries", f"{order.share.supplier.legal_name} reported a problem with {order.number}",
                           _label(projects.get(order.project_id)), "Supplier problem", "",
                           _link("supplier_office.project_requests", project_id=order.project_id,
                                 _anchor=f"share-{order.share_id}"), "Open the order",
                           urgency="today", project_id=order.project_id))
    for change in SupplierDeliveryChange.query.filter_by(status="PENDING", requested_by_side="SUPPLIER"):
        order = change.order
        if order is None or order.organization_id != org:
            continue
        items.append(_item("deliveries", f"{order.share.supplier.legal_name} asks to move {order.number} to "
                           f"{_day(change.new_date)}", _label(projects.get(order.project_id)),
                           "Delivery change waiting for your answer", _day(change.new_date),
                           _link("supplier_office.project_requests", project_id=order.project_id,
                                 _anchor=f"share-{order.share_id}"), "Answer",
                           urgency=_urgency(change.new_date, today) or "today", sort_date=change.new_date,
                           project_id=order.project_id))
    return items


@attention_provider("delivery_exceptions", "deliveries", title="Deliveries the crew reported short or damaged")
def _delivery_exceptions(ctx):
    items = []
    query = DeliveryConfirmation.query.filter_by(organization_id=ctx.org, exception_status=EXCEPTION_OPEN)
    if ctx.project_id is not None:
        query = query.filter(DeliveryConfirmation.project_id == ctx.project_id)
    for row in query:
        items.append(_item("deliveries", f"Delivery {row.outcome_label.lower()}: {row.order.number} "
                           f"({row.order.share.supplier.legal_name})", f"{_label(ctx.projects.get(row.project_id))} · "
                           f"{row.confirmed_by_name}", "Delivery problem to resolve", _day(local_date(row.confirmed_at)),
                           _link("operations.delivery", confirmation_id=row.id), "Resolve delivery", urgency="today",
                           sort_date=local_date(row.confirmed_at), project_id=row.project_id))
    return items


@attention_provider("receipts", "receipts", SCOPE_FINANCIAL, title="Receipts to review, approve or retry")
def _receipts(ctx):
    items = []
    grouped = defaultdict(list)
    for r in FieldReceipt.query.filter(FieldReceipt.organization_id == ctx.org,
                                       FieldReceipt.status.in_((RECEIPT_NEW, RECEIPT_REVIEWED,
                                                                RECEIPT_NEEDS_ATTENTION, RECEIPT_SYNC_FAILED))):
        if r.status in (RECEIPT_NEW, RECEIPT_REVIEWED):
            grouped[r.status].append(r)
            continue
        failed = r.status == RECEIPT_SYNC_FAILED
        items.append(_item("receipts", f"Receipt {r.number}: {'QuickBooks transfer failed' if failed else 'needs attention'}",
                           f"{_label(ctx.projects.get(r.project_id))} · {r.shown_supplier or 'supplier not entered'}",
                           r.status_label, _day(r.receipt_date or local_date(r.submitted_at)),
                           _link("accounting.receipt_detail", receipt_id=r.id), "Open the receipt", urgency="today",
                           sort_date=r.receipt_date or local_date(r.submitted_at), project_id=r.project_id))
    for status, rows in grouped.items():
        oldest = min(local_date(r.submitted_at) for r in rows)
        items.append(_item("receipts", f"{len(rows)} receipt{'s' if len(rows) != 1 else ''} "
                           + ("to review" if status == RECEIPT_NEW else "reviewed, waiting for approval"),
                           "Receipts Inbox", "New" if status == RECEIPT_NEW else "Reviewed", f"Since {_day(oldest)}",
                           _link("accounting.receipts_inbox", status=status), "Open the Receipts Inbox",
                           sort_date=oldest))
    return items


@attention_provider("quickbooks", "quickbooks", SCOPE_FINANCIAL, title="QuickBooks transfers and project syncs to fix")
def _quickbooks(ctx):
    from app.models.payroll_time import QBT_STATUS_FAILED, QBT_STATUS_NEEDS_SETUP, QuickBooksTimeTransfer
    from app.services.accounting_project_sync import problems as project_sync_problems

    items = []
    qbt = QuickBooksTimeTransfer.query.filter(QuickBooksTimeTransfer.organization_id == ctx.org,
                                              QuickBooksTimeTransfer.status.in_((QBT_STATUS_FAILED,
                                                                                 QBT_STATUS_NEEDS_SETUP))).count()
    if qbt:
        items.append(_item("quickbooks", f"{qbt} approved time entr{'y' if qbt == 1 else 'ies'} did not reach "
                           "QuickBooks Time", "Payroll", "Failed or needs a link", "",
                           _link("payroll_time.quickbooks_time"), "Fix and retry", urgency="today"))
    # Projects in QuickBooks Online / QuickBooks Time: a match to confirm, a failure or an unknown outcome.
    for link in project_sync_problems(ctx.org):
        states = {link.qbo_status, link.qbt_status}
        what = ("QuickBooks: confirm the existing job" if "NEEDS_CONFIRM" in states else
                "QuickBooks project sync failed" if "FAILED" in states else "QuickBooks project sync not confirmed")
        items.append(_item("quickbooks", what, _label(ctx.projects.get(link.project_id)),
                           link.qbo_last_error or link.qbt_last_error or "", "",
                           _link("accounting.quickbooks_projects", _anchor=f"project-{link.project_id}"),
                           "Confirm or retry", urgency="today", project_id=link.project_id))
    return items


@attention_provider("schedule_conflicts", "schedule", title="Schedule conflicts in the next two weeks")
def _schedule_conflicts(ctx):
    from app.services.schedule import list_schedule_conflicts

    try:
        conflicts = list_schedule_conflicts(ctx.org, window_start=ctx.today, window_end=ctx.today + timedelta(days=14))
    except Exception:  # never let one source hide the rest
        conflicts = []
    items = []
    for c in conflicts:
        project = ctx.projects.get(c.get("project_id"))
        items.append(_item("schedule", c.get("summary") or "Schedule conflict", _label(project), c.get("label") or
                           "Schedule conflict", "Next two weeks",
                           _link("projects.view_project", id=project.id, _anchor="hub-schedule") if project else
                           _link("schedule.company"), "Open the schedule", urgency="soon",
                           project_id=project.id if project else None))
    return items


@attention_provider("job_updates", "tasks", title="Problems or delays reported in a job update")
def _job_updates(ctx):
    items = []
    query = DailyJobSummary.query.filter_by(organization_id=ctx.org, problem_status=PROBLEM_OPEN)
    if ctx.project_id is not None:
        query = query.filter(DailyJobSummary.project_id == ctx.project_id)
    for s in query:
        items.append(_item("tasks", f"Problem or delay reported: {(s.problems_text or '')[:80]}",
                           f"{_label(ctx.projects.get(s.project_id))} · {s.submitted_by_name}", "Job update — open",
                           _day(s.work_date), _link("operations.job_update", summary_id=s.id), "Open the job update",
                           urgency="today", sort_date=s.work_date, project_id=s.project_id))
    return items


@attention_provider("punch_list", "tasks", title="Open punch list items on active jobs")
def _punch(ctx):
    from app.models.punch_list import PUNCH_LIST_STATUS_OPEN, ProjectPunchListItem

    punch = defaultdict(int)
    query = ProjectPunchListItem.query.filter_by(organization_id=ctx.org, status=PUNCH_LIST_STATUS_OPEN)
    if ctx.project_id is not None:
        query = query.filter(ProjectPunchListItem.project_id == ctx.project_id)
    for row in query:
        punch[row.project_id] += 1
    items = []
    for pid, n in punch.items():
        project = ctx.projects.get(pid)
        if project is None or project.operating_state != "ACTIVE":
            continue
        items.append(_item("tasks", f"{n} open punch list item{'s' if n != 1 else ''}", _label(project), "Open", "",
                           _link("projects.view_project", id=pid, _anchor="hub-punch-list"), "Open the punch list",
                           project_id=pid))
    return items


@attention_provider("documents", "documents",
                    title="Document dates due (expiry, inspection, renewal, warranty) and documents to review")
def _documents(ctx):
    """Documents (RDIMS, 31 Oct 2026): confirmed dates in the reminder window or past, plus the two roll-ups.
    The documents service applies the viewer's document permissions; no compliance rules are inferred."""
    from app.services.documents.attention import document_attention_items

    if ctx.project_id is not None:
        return []  # document items are not tied to one project (the Project page never shows them)
    rows = []
    for row in document_attention_items(ctx.org, ctx.viewer, ctx.today):
        row.setdefault("why", row.get("status") or "")
        row.setdefault("due", row.get("when") or "")
        row.setdefault("project_id", None)
        row.setdefault("waiting_on", WAITING_ON_YOU)
        rows.append(row)
    return rows


@attention_provider("customers_incomplete", "customers", title="Customers with information still to add")
def _customers(ctx):
    return incomplete_customers(ctx.org, ctx.projects)


@attention_provider("company_facts", "labour", SCOPE_COMPANY_FACTS,
                    title="Labour allowance and schedule facts (Company Attention)")
def _company_facts(ctx):
    from app.services.company_attention import assemble_company_attention
    from app.services.project_performance import FACT_EXTRA_WORK_NEEDS_REVIEW

    items = []
    for fact in assemble_company_attention(ctx.org, today=ctx.today).get("items") or []:
        if fact.get("fact_type") == FACT_EXTRA_WORK_NEEDS_REVIEW:
            continue  # listed above from the extra work itself
        dest = fact.get("destination") or {}
        items.append(_item("labour", fact.get("title") or "", (fact.get("project") or {}).get("name") or "",
                           fact.get("detail") or "", "",
                           dest.get("href") or _link("projects.view_project", id=fact.get("project_id")),
                           "Open", project_id=fact.get("project_id")))
    return items


@attention_provider("schedule_texts_failed", "texts", title="Schedule texts to workers that were not delivered")
def _failed_texts(ctx):
    """The Home banner of failed schedule texts, now one attention item (audit 5.3 #21)."""
    from app.services.access_domains import has_office_scheduling_authority
    from app.services.crew_notices import attention_count

    if ctx.project_id is not None or not has_office_scheduling_authority(ctx.viewer, ctx.org):
        return []  # (not tied to one project)
    n = attention_count(ctx.org)
    if not n:
        return []
    return [_item("texts", f"{n} schedule text{'' if n == 1 else 's'} to workers not delivered", "Crew texts",
                  "Check and retry", "", _link("sms_notifications.office_notices"), "Check and retry",
                  urgency="today")]


# ---- governed events added by the Task-First UX (31 Oct 2026; audit section 5.3)
def _guided_estimates(ctx):
    from app.models.guided_estimating import GuidedEstimate

    query = GuidedEstimate.query.filter_by(organization_id=ctx.org)
    if ctx.project_id is not None:
        query = query.filter(GuidedEstimate.project_id == ctx.project_id)
    for guided in query.all():
        project = ctx.projects.get(guided.project_id)
        if _open(project):
            yield guided, project


@attention_provider("estimate_ready_for_approval", "estimates", title="Estimate priced and ready for approval (Gate 1)")
def _estimate_ready(ctx):
    from app.models.guided_estimating import STATUS_COMPLETE, STATUS_EXCLUDED
    from app.services import guided_estimating as G
    from app.services.estimate_approval import is_approved

    items = []
    for guided, project in _guided_estimates(ctx):
        version = G.current_version(guided)
        if version is None or version.is_locked or is_approved(version):
            continue
        work = [s for s in guided.top_stages if (s.commercial_status or "INCLUDED") != "EXCLUDED"]
        if not work or any(s.status not in (STATUS_COMPLETE, STATUS_EXCLUDED) for s in work):
            continue
        if all(s.status == STATUS_EXCLUDED for s in work):
            continue
        items.append(_item("estimates", f"{project.name} estimate is ready for your approval", _label(project),
                           "Every work item is priced; approving locks this estimate", "",
                           _link("guided.pricing", project_id=project.id), "Review This Estimate",
                           urgency="today", project_id=project.id))
    return items


@attention_provider("calculator_results_not_on_estimate", "estimates",
                    title="Calculator results not yet on the estimate")
def _calculator_results(ctx):
    from app.models.calculation_estimate_mapping import STATUS_OPEN, CalculationQuantityReview, CalculationResultIntake
    from app.models.estimate import EstimateVersion
    from app.models.project_calculation import ProjectCalculation

    items = []
    waiting = defaultdict(list)
    calcs_query = ProjectCalculation.query.filter_by(organization_id=ctx.org, review_status="AWAITING_REVIEW")
    if ctx.project_id is not None:
        calcs_query = calcs_query.filter(ProjectCalculation.project_id == ctx.project_id)
    for calc in calcs_query.all():
        if calc.payload and _open(ctx.projects.get(calc.project_id)):
            waiting[calc.project_id].append(calc)
    for pid, calcs in waiting.items():
        project = ctx.projects[pid]
        n = len(calcs)
        href = (_link("guided.calculation", project_id=pid, calculation_id=calcs[0].id) if n == 1 else
                _link("projects.view_project", id=pid, _anchor="calculations"))
        items.append(_item("estimates", f"{n} calculator result{'' if n == 1 else 's'} waiting to go on the estimate",
                           _label(project), "Calculated, not reviewed for the estimate yet", "", href,
                           "Review for the estimate", project_id=pid))
    intakes_query = (db.session.query(CalculationResultIntake)
                     .join(CalculationQuantityReview, CalculationQuantityReview.intake_id == CalculationResultIntake.id)
                     .filter(CalculationResultIntake.organization_id == ctx.org,
                             CalculationQuantityReview.status == STATUS_OPEN))
    if ctx.project_id is not None:
        intakes_query = intakes_query.filter(CalculationResultIntake.project_id == ctx.project_id)
    open_intakes = intakes_query.distinct().all()
    for intake in open_intakes:
        project = ctx.projects.get(intake.project_id)
        version = db.session.get(EstimateVersion, intake.estimate_version_id)
        if not _open(project) or version is None or version.is_locked:
            continue
        items.append(_item("estimates", "Calculated quantities waiting to go on the estimate", _label(project),
                           "Quantities to confirm on the estimate lines", "",
                           _link("estimates.calculation_review", id=intake.estimate_id,
                                 version_id=intake.estimate_version_id, intake_id=intake.id),
                           "Confirm quantities", project_id=intake.project_id))
    return items


@attention_provider("subcontract_quotes", "estimates", title="Subcontract quotes waiting, or received and not chosen")
def _subcontract_quotes(ctx):
    from app.models.estimate import EstimateLineItem, EstimateVersion
    from app.models.guided_estimating import STATUS_WAITING_FOR_QUOTE
    from app.models.subcontractor import QUOTE_STATUS_RECEIVED, QUOTE_STATUS_SELECTED, SubcontractQuoteEvidence

    items = []
    guided_projects = set()
    for guided, project in _guided_estimates(ctx):
        guided_projects.add(project.id)
        for stage in guided.stages:
            if stage.status != STATUS_WAITING_FOR_QUOTE:
                continue
            asked = local_date(stage.quote_requested_at) if stage.quote_requested_at else None
            overdue = asked is not None and asked < ctx.today - timedelta(days=QUOTE_OVERDUE_DAYS)
            items.append(_item("estimates", f"Waiting for a subcontract quote: {stage.display_name}", _label(project),
                               "Quote asked for, not received yet" + (" — follow up" if overdue else ""),
                               f"Asked {_day(asked)}" if asked else "",
                               _link("guided.stage", project_id=project.id, stage_id=stage.id), "Open the work item",
                               urgency="overdue" if overdue else "", sort_date=asked, project_id=project.id,
                               waiting_on=WAITING_ON_YOU if overdue else WAITING_ON_OTHERS))
    received = defaultdict(list)
    selected_lines = set()
    quotes_query = SubcontractQuoteEvidence.query.filter(SubcontractQuoteEvidence.organization_id == ctx.org,
                                                         SubcontractQuoteEvidence.selection_status.in_(
                                                             (QUOTE_STATUS_RECEIVED, QUOTE_STATUS_SELECTED)))
    if ctx.project_id is not None:
        quotes_query = quotes_query.filter(SubcontractQuoteEvidence.project_id == ctx.project_id)
    for q in quotes_query.all():
        if q.selection_status == QUOTE_STATUS_SELECTED:
            selected_lines.add(q.estimate_line_item_id)
        else:
            received[q.estimate_line_item_id].append(q)
    # One query each for the versions and lines involved (was one get per received line).
    wanted = {line_id: quotes[0] for line_id, quotes in received.items() if line_id not in selected_lines}
    versions = {v.id: v for v in EstimateVersion.query.filter(
        EstimateVersion.id.in_({q.estimate_version_id for q in wanted.values()} or {-1})).all()}
    lines = {li.id: li for li in EstimateLineItem.query.filter(EstimateLineItem.id.in_(set(wanted) or {-1})).all()}
    for line_id, quotes in received.items():
        if line_id in selected_lines:
            continue
        q = quotes[0]
        project = ctx.projects.get(q.project_id)
        version = versions.get(q.estimate_version_id)
        if not _open(project) or version is None or version.is_locked:
            continue
        line = lines.get(line_id)
        what = line.description if line is not None else "subcontract work"
        n = len(quotes)
        href = (_link("guided.compare", project_id=project.id) if project.id in guided_projects
                else _link("scope_delivery.review", project_id=project.id))
        items.append(_item("estimates", f"{n} subcontract quote{'' if n == 1 else 's'} received for {what}: choose one",
                           _label(project), "Received, not chosen for the estimate", _day(q.quote_date),
                           href, "Compare and choose", urgency="today", sort_date=q.quote_date,
                           project_id=project.id))
    return items


@attention_provider("supplier_prices_missing", "estimates", title="Estimate material lines still without a price")
def _supplier_prices_missing(ctx):
    """Review fix I2 (1 Nov 2026): one aggregate query for the unpriced material lines of every draft estimate (was
    every section, line and cost item loaded one by one). Same rule: a "Cost Item" line of a Material cost item with
    no unit cost (empty or 0) and no costing override reason (empty)."""
    from sqlalchemy import func, or_
    from sqlalchemy.orm import joinedload

    from app.models import Estimate
    from app.models.cost_item import CostItem
    from app.models.estimate import EstimateLineItem, EstimateSection

    query = Estimate.query.options(joinedload(Estimate.current_version)).filter_by(organization_id=ctx.org)
    if ctx.project_id is not None:
        query = query.filter(Estimate.project_id == ctx.project_id)
    drafts = []
    for estimate in query.all():
        project = ctx.projects.get(estimate.project_id)
        version = estimate.current_version
        if not _open(project) or version is None or version.is_locked or (version.status or "Draft") != "Draft":
            continue
        drafts.append((estimate, project, version))
    if not drafts:
        return []
    missing_by_version = dict(
        db.session.query(EstimateSection.estimate_version_id, func.count(EstimateLineItem.id))
        .join(EstimateLineItem, EstimateLineItem.estimate_section_id == EstimateSection.id)
        .join(CostItem, CostItem.id == EstimateLineItem.cost_item_id)
        .filter(EstimateSection.estimate_version_id.in_({v.id for _e, _p, v in drafts}),
                EstimateLineItem.line_type == "Cost Item", CostItem.category == "Material",
                or_(EstimateLineItem.unit_cost.is_(None), EstimateLineItem.unit_cost == 0),
                or_(EstimateLineItem.costing_override_reason.is_(None), EstimateLineItem.costing_override_reason == ""))
        .group_by(EstimateSection.estimate_version_id).all())
    items = []
    for estimate, project, version in drafts:
        missing = missing_by_version.get(version.id, 0)
        if not missing:
            continue
        items.append(_item("estimates", f"{missing} material line{'' if missing == 1 else 's'} still need a price",
                           f"{_label(project)} · {estimate.estimate_number}", "No price on the estimate yet",
                           "", _link("estimates.view_version", id=estimate.id, version_id=version.id),
                           "Add the prices", project_id=project.id))
    return items


def _proposal_project(proposal, ctx):
    estimate = proposal.estimate
    return ctx.projects.get(estimate.project_id) if estimate is not None else None


@attention_provider("proposal_awaiting_customer", "proposals", title="Proposal sent, customer has not answered")
def _proposals_waiting(ctx):
    from app.models import Proposal

    items = []
    for proposal in Proposal.query.filter_by(organization_id=ctx.org, status="Issued").all():
        project = _proposal_project(proposal, ctx)
        if not _open(project):
            continue
        sent = local_date(proposal.issued_at) if proposal.issued_at else None
        quiet = sent is not None and sent <= ctx.today - timedelta(days=PROPOSAL_QUIET_DAYS)
        expires = proposal.valid_until
        items.append(_item("proposals", f"Proposal {proposal.proposal_number} sent: no answer yet", _label(project),
                           ("Sent " + (f"{(ctx.today - sent).days} days ago" if sent else "") +
                            (" — give the customer a call" if quiet else "")).strip(),
                           ("Expires " + _day(expires)) if expires else (f"Sent {_day(sent)}" if sent else ""),
                           _link("proposals.view_proposal", id=proposal.id), "Open the proposal",
                           urgency=_urgency(expires, ctx.today) if expires else "", sort_date=expires or sent,
                           project_id=project.id, waiting_on=WAITING_ON_YOU if quiet else WAITING_ON_OTHERS))
    return items


@attention_provider("calisign", "signing", title="CaliSIGN: awaiting signature, countersignature, expiring or declined")
def _calisign(ctx):
    from app.models.signing import (
        DOCUMENT_FAMILY_CHANGE_ORDER,
        DOCUMENT_FAMILY_CONTRACT,
        DOCUMENT_FAMILY_SUBCONTRACT,
        DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE,
        DOCUMENT_FAMILY_SUPPLIER_ORDER,
        STATUS_APPROVED_FOR_SIGNATURE,
        STATUS_DECLINED,
        STATUS_EXPIRED,
        STATUS_SENT,
        STATUS_SIGNED,
        SigningRequest,
    )

    names = {DOCUMENT_FAMILY_CONTRACT: "Contract", DOCUMENT_FAMILY_CHANGE_ORDER: "Change order",
             DOCUMENT_FAMILY_SUPPLIER_ORDER: "Purchase order", DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE: "Delivery change",
             DOCUMENT_FAMILY_SUBCONTRACT: "Subcontract", "INTERNAL_APPROVAL": "Internal approval"}

    def href(req):
        if req.document_family == DOCUMENT_FAMILY_CONTRACT:
            return _link("projects.review_contract", id=req.project_id)
        if req.document_family == DOCUMENT_FAMILY_CHANGE_ORDER:
            return _link("project_controls.view_change_order", id=req.source_record_id)
        if req.document_family == "INTERNAL_APPROVAL":
            return _link("guided.pricing", project_id=req.project_id, _anchor="ts-review-scenario")
        if req.document_family == DOCUMENT_FAMILY_SUBCONTRACT:
            return _link("supplier_office.commitments", project_id=req.project_id, _anchor="subcontracts")
        return _link("supplier_office.project_requests", project_id=req.project_id)

    items = []
    query = SigningRequest.query.filter(SigningRequest.organization_id == ctx.org, SigningRequest.status.in_(
        (STATUS_APPROVED_FOR_SIGNATURE, STATUS_SENT, STATUS_SIGNED, STATUS_DECLINED, STATUS_EXPIRED)))
    if ctx.project_id is not None:
        query = query.filter(SigningRequest.project_id == ctx.project_id)
    for req in query.all():
        project = ctx.projects.get(req.project_id)
        if not _open(project):
            continue
        doc = names.get(req.document_family, "Document")
        expires = local_date(req.expires_at) if req.expires_at else None
        common = dict(project_id=req.project_id)
        if req.status == STATUS_SIGNED and req.countersign_required:
            items.append(_item("signing", f"{doc} {req.request_number} signed: your countersignature is needed",
                               _label(project), "Signed by the other party", "", href(req), "Review and sign",
                               urgency="today", **common))
        elif req.status == STATUS_APPROVED_FOR_SIGNATURE:
            items.append(_item("signing", f"{doc} {req.request_number} approved, not sent for signature yet",
                               _label(project), "Ready to send", "", href(req), "Send for e-signature", **common))
        elif req.status == STATUS_SENT:
            soon = expires is not None and expires <= ctx.today + timedelta(days=SIGNING_EXPIRY_SOON_DAYS)
            items.append(_item("signing", f"{doc} {req.request_number} waiting for signature"
                               + (" — expires soon" if soon else ""), _label(project),
                               "Sent for e-signature", ("Expires " + _day(expires)) if expires else "", href(req),
                               "Open", urgency=_urgency(expires, ctx.today) if soon else "", sort_date=expires,
                               waiting_on=WAITING_ON_YOU if soon else WAITING_ON_OTHERS, **common))
        elif req.status == STATUS_DECLINED:
            items.append(_item("signing", f"{doc} {req.request_number} was declined", _label(project),
                               "Declined by the signer: decide what to do next",
                               _day(local_date(req.declined_at)) if req.declined_at else "", href(req), "Open",
                               urgency="today", **common))
        elif req.status == STATUS_EXPIRED:
            items.append(_item("signing", f"{doc} {req.request_number} expired before it was signed", _label(project),
                               "Expired: send it again or withdraw it", _day(expires), href(req), "Open", **common))
    return items


@attention_provider("supplier_calisign_awaiting", "signing", SCOPE_SUPPLIER,
                    title="Supplier Hub: purchase orders and delivery changes waiting for the store's CaliSIGN signature")
def _supplier_calisign(ctx):
    """The store's own documents open on CaliSIGN (sent, not yet signed by the store), from the signing records.
    No rule is invented: a SENT request whose store participant has not signed is waiting for the store."""
    from app.models.signing import (
        DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE,
        DOCUMENT_FAMILY_SUPPLIER_ORDER,
        ROLE_CONTRACTOR,
        ROLE_SUPPLIER,
        STATUS_SENT,
        SigningRequest,
    )
    from app.models.supplier_portal import SupplierDeliveryChange, SupplierPurchaseOrder

    orders = {o.id: o for o in SupplierPurchaseOrder.query.filter_by(supplier_id=ctx.supplier_id).all()}
    if not orders:
        return []
    changes = {c.id: c for c in SupplierDeliveryChange.query.filter(
        SupplierDeliveryChange.order_id.in_(list(orders))).all()}
    sources = [(DOCUMENT_FAMILY_SUPPLIER_ORDER, list(orders))]
    if changes:
        sources.append((DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE, list(changes)))
    items = []
    for family, ids in sources:
        for req in SigningRequest.query.filter(SigningRequest.document_family == family,
                                               SigningRequest.source_record_id.in_(ids),
                                               SigningRequest.status == STATUS_SENT).all():
            change = changes.get(req.source_record_id) if family == DOCUMENT_FAMILY_SUPPLIER_DELIVERY_CHANGE else None
            order = change.order if change is not None else orders.get(req.source_record_id)
            if order is None or order.supplier_id != ctx.supplier_id or order.organization_id != req.organization_id:
                continue
            store = next((p for p in req.participants if p.role == ROLE_SUPPLIER), None)
            if store is None or store.signed_at is not None or store.confirmed_signer_name:
                continue
            contractor = next((p.invited_name for p in req.participants if p.role == ROLE_CONTRACTOR), "")
            sent = local_date(req.created_at) if req.created_at else None
            doc = f"Purchase order {order.number}" if change is None else f"Delivery change on {order.number}"
            href = _link("supplier_portal.request_detail", supplier_id=ctx.supplier_id, share_id=order.share_id,
                         **({"_anchor": "delivery"} if change is not None else {}))
            items.append(_item("signing", f"{doc} waiting for your signature", contractor,
                               "Sent for e-signature", f"Sent {_day(sent)}" if sent else "", href, "Review and Sign",
                               urgency="today", sort_date=sent))
    return items


@attention_provider("contract_not_generated", "signing", title="Customer accepted, contract not generated yet")
def _contract_not_generated(ctx):
    from app.models import Proposal
    from app.models.project_contract import GeneratedProjectContract

    with_contract = {row[0] for row in db.session.query(GeneratedProjectContract.project_id).filter(
        GeneratedProjectContract.organization_id == ctx.org).all()}
    items = []
    seen = set()
    for proposal in Proposal.query.filter_by(organization_id=ctx.org, status="Accepted").all():
        project = _proposal_project(proposal, ctx)
        if not _open(project) or project.id in with_contract or project.id in seen:
            continue
        seen.add(project.id)
        items.append(_item("signing", "Customer accepted: contract not generated yet", _label(project),
                           f"Proposal {proposal.proposal_number} accepted", "",
                           _link("projects.review_contract", id=project.id, _anchor="contract-generate"),
                           "Generate the contract", urgency="today", project_id=project.id))
    return items


@attention_provider("subcontract_awaiting_gate3", "purchasing", SCOPE_COMPANY,
                    title="Subcontract commitment awaiting approval (Gate 3)")
def _gate3(ctx):
    from app.models.procurement_governance import COMMITMENT_PROPOSED, SubcontractCommitment

    items = []
    for c in SubcontractCommitment.query.filter_by(organization_id=ctx.org, status=COMMITMENT_PROPOSED).all():
        project = ctx.projects.get(c.project_id)
        if not _open(project):
            continue
        items.append(_item("purchasing", f"Approve the {c.subcontractor_name} subcontract (${float(c.amount):,.2f})",
                           _label(project), f"Proposed by {c.proposed_by_name}", _day(local_date(c.proposed_at)),
                           _link("supplier_office.commitments", project_id=c.project_id, _anchor=f"commitment-{c.id}"),
                           "Review and approve", urgency="today", sort_date=local_date(c.proposed_at),
                           project_id=c.project_id))
    return items


@attention_provider("early_order_not_placed", "purchasing", title="Early order approved, not placed yet")
def _early_order(ctx):
    from app.models.procurement_governance import EXCEPTION_APPROVED, EarlyProcurementException

    items = []
    for e in EarlyProcurementException.query.filter_by(organization_id=ctx.org, status=EXCEPTION_APPROVED).all():
        project = ctx.projects.get(e.project_id)
        if not _open(project) or e.resulting_order_id:
            continue
        href = (_link("supplier_office.project_requests", project_id=e.project_id, _anchor=f"share-{e.share_id}")
                if e.share_id else _link("supplier_office.commitments", project_id=e.project_id, _anchor="early-orders"))
        items.append(_item("purchasing", "Order approved before the customer signed: not placed yet", _label(project),
                           f"Approved by {e.approved_by_name}: {e.proposed_commitment[:80]}",
                           _day(local_date(e.approved_at)), href, "Place the order",
                           sort_date=local_date(e.approved_at), project_id=e.project_id))
    return items


@attention_provider("company_schedule_change_requests", "planning", SCOPE_COMPANY,
                    title="Requested date changes that affect other jobs (Company Schedule Change Requests)")
def _schedule_change_requests(ctx):
    from app.models.schedule_governance import CSCR_PROPOSED, CompanyScheduleChangeRequest

    items = []
    for r in CompanyScheduleChangeRequest.query.filter_by(organization_id=ctx.org, status=CSCR_PROPOSED).all():
        project = ctx.projects.get(r.project_id)
        if not _open(project):
            continue
        items.append(_item("planning", f"{r.requested_by_name} asks to move work to {_day(r.proposed_start)}",
                           _label(project), "Other jobs are affected: approve or reject the date change",
                           _day(r.proposed_start),
                           _link("schedule.planning", project_id=r.project_id, _anchor=f"change-request-{r.id}"),
                           "Decide", urgency=_urgency(r.proposed_start, ctx.today) or "today",
                           sort_date=r.proposed_start, project_id=r.project_id))
    return items


@attention_provider("delivery_notices_to_send", "planning", title="Supplier delivery notices drafted, waiting to be sent")
def _delivery_notices(ctx):
    from app.models.schedule_governance import DRAFT_PENDING, ScheduleExternalDraft

    per_project = defaultdict(list)
    for d in ScheduleExternalDraft.query.filter_by(organization_id=ctx.org, status=DRAFT_PENDING).all():
        if _open(ctx.projects.get(d.project_id)):
            per_project[d.project_id].append(d)
    items = []
    for pid, drafts in per_project.items():
        n = len(drafts)
        first = min(d.new_start for d in drafts)
        items.append(_item("planning", f"{n} supplier delivery notice{'' if n == 1 else 's'} drafted: send?",
                           _label(ctx.projects[pid]), "The work moved; the supplier has not been told yet",
                           _day(first), _link("schedule.planning", project_id=pid, _anchor="delivery-drafts"),
                           "Review and send", urgency=_urgency(first, ctx.today), sort_date=first, project_id=pid))
    return items


@attention_provider("accepted_work_not_scheduled", "planning", title="Accepted work not on the schedule yet")
def _unscheduled(ctx):
    from app.services.procurement_gate import gate_2_passed
    from app.services.schedule import list_unscheduled_elements

    per_project = defaultdict(int)
    for element in list_unscheduled_elements(organization_id=ctx.org):
        per_project[element.project_id] += 1
    items = []
    for pid, n in per_project.items():
        project = ctx.projects.get(pid)
        if not _open(project) or not gate_2_passed(project):
            continue
        items.append(_item("planning", f"{n} accepted work item{'' if n == 1 else 's'} not on the schedule",
                           _label(project), "The customer accepted; no dates yet", "",
                           _link("schedule.planning", project_id=pid), "Schedule this project", project_id=pid))
    return items


@attention_provider("change_order_drafts", "extra_work", title="Change orders drafted, not sent to the customer")
def _change_order_drafts(ctx):
    from app.project_controls.models import ChangeOrder

    items = []
    query = ChangeOrder.query.filter_by(organization_id=ctx.org, status="Draft")
    if ctx.project_id is not None:
        query = query.filter(ChangeOrder.project_id == ctx.project_id)
    for co in query.all():
        project = ctx.projects.get(co.project_id)
        if not _open(project):
            continue
        items.append(_item("extra_work", f"Change order {co.number} drafted, not sent: {co.title}", _label(project),
                           "Draft: price it and send it to the customer", _day(co.requested_date),
                           _link("project_controls.view_change_order", id=co.id), "Open the change order",
                           sort_date=co.requested_date, project_id=co.project_id))
    return items


@attention_provider("walkthrough_returned", "closeout", title="Customer returned the final walkthrough")
def _walkthrough_returned(ctx):
    from app.models.final_walkthrough import (
        WALKTHROUGH_REVIEW_PENDING,
        WALKTHROUGH_STATUS_RESPONDED,
        ProjectFinalWalkthroughInvitation,
        ProjectFinalWalkthroughItem,
    )

    items = []
    for inv in ProjectFinalWalkthroughInvitation.query.filter_by(organization_id=ctx.org,
                                                                 status=WALKTHROUGH_STATUS_RESPONDED).all():
        project = ctx.projects.get(inv.project_id)
        if not _open(project):
            continue
        pending = ProjectFinalWalkthroughItem.query.filter_by(invitation_id=inv.id,
                                                              review_status=WALKTHROUGH_REVIEW_PENDING).count()
        if not pending:
            continue
        items.append(_item("closeout", f"Customer returned the walkthrough: {pending} item{'' if pending == 1 else 's'}",
                           _label(project), "Review each item: add it to the punch list or mark it done",
                           _day(local_date(inv.responded_at)) if inv.responded_at else "",
                           _link("projects.view_project", id=project.id, _anchor="hub-final-walkthrough"),
                           "Review the walkthrough", urgency="today", project_id=project.id))
    return items


@attention_provider("ready_to_close", "closeout", SCOPE_OWNER_ADMIN, title="Job looks ready to close")
def _ready_to_close(ctx):
    from app.models.final_walkthrough import (
        WALKTHROUGH_REVIEW_PENDING,
        WALKTHROUGH_STATUS_RESPONDED,
        ProjectFinalWalkthroughInvitation,
        ProjectFinalWalkthroughItem,
    )
    from app.models.punch_list import PUNCH_LIST_STATUS_OPEN, ProjectPunchListItem
    from app.models.supplier_portal import PO_CONFIRMED, PO_PLACED, PO_PROBLEM, SupplierPurchaseOrder

    items = []
    for inv in ProjectFinalWalkthroughInvitation.query.filter_by(organization_id=ctx.org,
                                                                 status=WALKTHROUGH_STATUS_RESPONDED).all():
        project = ctx.projects.get(inv.project_id)
        if not _open(project) or any(i.get("project_id") == project.id and i["provider"] == "ready_to_close"
                                     for i in items):
            continue
        if ProjectFinalWalkthroughItem.query.filter_by(invitation_id=inv.id,
                                                       review_status=WALKTHROUGH_REVIEW_PENDING).count():
            continue
        if ProjectPunchListItem.query.filter_by(project_id=project.id, status=PUNCH_LIST_STATUS_OPEN).count():
            continue
        if SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.project_id == project.id,
                                              SupplierPurchaseOrder.status.in_((PO_PLACED, PO_CONFIRMED,
                                                                                PO_PROBLEM))).count():
            continue
        row = _item("closeout", f"{project.name} looks ready to close", _label(project),
                    "Walkthrough answered, punch list done, no open orders", "",
                    _link("projects.close_project", id=project.id), "Close this project", project_id=project.id)
        row["provider"] = "ready_to_close"
        items.append(row)
    return items


# ================================================================================================= customers
def incomplete_customers(org, projects=None, *, client_id=None) -> list:
    """One item per customer whose email, phone or address is still missing (never two for the same customer).

    Derived from the customer record itself, like every other item: the moment the information is saved the item
    is gone. The customer may be saved without them (a contractor often gets the email or phone later); this keeps
    the gap in front of the office instead of in someone's memory. A customer whose jobs are all closed is left out;
    a customer with no job yet (just added) is included."""
    from app.models import Client
    from app.services.clients import missing_information
    from app.services.time_entry import customer_clients_only

    projects = projects if projects is not None else _projects(org)
    by_client = defaultdict(list)
    for p in projects.values():
        if p.client_id:
            by_client[p.client_id].append(p)
    query = customer_clients_only(Client.query.filter_by(organization_id=org), org)
    if client_id is not None:
        query = query.filter(Client.id == client_id)
    out = []
    for client in query.order_by(Client.name.asc()).all():
        missing = missing_information(client)
        if not missing:
            continue
        theirs = by_client.get(client.id, [])
        open_jobs = [p for p in theirs if (p.operating_state or "ACTIVE") != "CLOSED"]
        if theirs and not open_jobs:
            continue  # every job for this customer is closed: nothing left to chase
        jobs = ", ".join(_label(p) for p in sorted(open_jobs, key=lambda x: x.id)[:2])
        row = _item("customers", f"{client.name} — Customer information incomplete", jobs,
                    "Missing: " + ", ".join(missing), "", _link("clients.edit_client", client_id=client.id,
                                                                return_to="/"),
                    "Complete information", project_id=open_jobs[0].id if len(open_jobs) == 1 else None)
        out.append(row)
    return out
