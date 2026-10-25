"""WHAT NEEDS MY ATTENTION? — Ben's one place for today's actions (Magnificent Seven, 25 Oct 2026).

Derived live from the real records every time it is shown; nothing is stored, so there is no second task list and a
resolved item simply stops being listed. Each item says what needs attention, the job or person, the current status,
the date or urgency, and links straight to the working screen where it is done (never to another dashboard).
One Click to Action never approves anything: the link opens the screen where the person decides.

Office members only (Field-only crew never see it). Receipts and QuickBooks items follow the /accounting rule
(has_office_financial_access). The labour-allowance and schedule facts of Company Attention are included for
members holding COMPANY_MANAGEMENT, as on that page.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

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

URGENCY_ORDER = {"overdue": 0, "today": 1, "soon": 2, "": 3}
MISSING_TIME_DAYS = 5


def _day(d: Optional[date]) -> str:
    if d is None:
        return ""
    return f"{d:%a %b} {d.day}"


def _item(kind, what, who, status, when, href, action, *, urgency="", sort_date=None):
    return {"kind": kind, "what": what, "who": who, "status": status, "when": when, "href": href, "action": action,
            "urgency": urgency, "sort_date": sort_date or date.max}


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


def _projects(org):
    return {p.id: p for p in Project.query.filter_by(organization_id=org).all()}


def _label(project) -> str:
    if project is None:
        return ""
    number = (project.project_number or "").strip()
    return f"{project.name}" + (f" ({number})" if number else "")


def working_days(org) -> set:
    from app.services.reminders import settings_for

    raw = settings_for(org).working_days or ""
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


def missing_time(org, *, today: date, include_today: bool = False) -> list:
    """(user_id, name, day, [project ids]) for scheduled people with no time at all entered for that day."""
    from app.models.user import UserMembership
    from app.services.daily_summaries import item_workers, scheduled_items

    days = working_days(org)
    out = []
    active = {m.user_id for m in UserMembership.query.filter_by(organization_id=org, is_active=True).all()}
    start = 0 if include_today else 1
    for back in range(start, MISSING_TIME_DAYS + 1):
        day = today - timedelta(days=back)
        if day.weekday() not in days:
            continue
        people = defaultdict(lambda: {"name": "", "projects": set()})
        for item in scheduled_items(org, None, day):
            for user_id, name in item_workers(item, day).items():
                if user_id in active:
                    people[user_id]["name"] = name
                    people[user_id]["projects"].add(item.project_id)
        if not people:
            continue
        entered = {row[0] for row in db.session.query(LabourTimeEntry.worker_user_id).filter(
            LabourTimeEntry.organization_id == org, LabourTimeEntry.work_date == day,
            LabourTimeEntry.status != TIME_STATUS_SUPERSEDED).all()}
        for user_id, row in people.items():
            if user_id not in entered:
                out.append((user_id, row["name"], day, sorted(row["projects"])))
    return out


def assemble(organization_id: str, viewer, *, today: Optional[date] = None, include_company_facts=None) -> dict:
    from app.services.access_domains import (
        ACCESS_DOMAIN_COMPANY_MANAGEMENT,
        has_office_financial_access,
        membership_has_access_domain,
        user_is_field_only,
    )

    org = organization_id
    today = today or local_today()
    if viewer is None or not getattr(viewer, "is_authenticated", True) or user_is_field_only(viewer, org):
        return {"items": [], "count": 0, "hidden": True}
    projects = _projects(org)
    items = []

    # ---- time
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
                           f"/time?status=SUBMITTED&worker_user_id={uid}", "Review time",
                           urgency="overdue" if oldest < today - timedelta(days=2) else "today", sort_date=oldest))
    for (uid, name), rows in returned.items():
        items.append(_item("time", f"{len(rows)} returned time entr{'y' if len(rows) == 1 else 'ies'} not fixed yet",
                           name, "Returned to the worker", _day(min(r.work_date for r in rows)),
                           f"/time?status=RETURNED&worker_user_id={uid}", "Open time",
                           sort_date=min(r.work_date for r in rows)))
    show_today = local_now().strftime("%H:%M") >= _reminder_time(org)
    for uid, name, day, project_ids in missing_time(org, today=today, include_today=show_today):
        jobs = ", ".join(_label(projects.get(pid)) for pid in project_ids)
        items.append(_item("time", "No time entered", f"{name} · {jobs}", "Scheduled, no time", _day(day),
                           f"/time?worker_user_id={uid}&from={day.isoformat()}&to={day.isoformat()}", "Check time",
                           urgency="overdue" if day < today else "today", sort_date=day))

    # ---- material requests
    for r in FieldMaterialRequest.query.filter(FieldMaterialRequest.organization_id == org,
                                               FieldMaterialRequest.status.in_((MR_SUBMITTED, MR_APPROVED))):
        status = "Waiting for your review" if r.status == MR_SUBMITTED else "Approved — choose the supplier"
        items.append(_item("materials", f"Material request: {r.description}", f"{_label(projects.get(r.project_id))} · "
                           f"{r.requested_by_name}", status,
                           ("Needed by " + _day(r.needed_by)) if r.needed_by else f"Asked {_day(local_date(r.requested_at))}",
                           f"/operations/material-requests/{r.id}", "Review request",
                           urgency=_urgency(r.needed_by, today) or "today", sort_date=r.needed_by or today))

    # ---- extra work and change orders
    from app.services import extra_work_reports as ew

    reported_activities = set()
    for r in ew.office_list(org, open_only=False):
        reported_activities.add(r.activity_id)
        if not ew.needs_office(r):
            continue
        co = ew.change_order(r)
        if co is not None:
            items.append(_item("extra_work", f"Change order {co.number} for extra work: {r.description[:80]}",
                               _label(projects.get(r.project_id)), f"Change order {co.status}",
                               _day(r.work_date), f"/project-controls/change-orders/{co.id}",
                               "Open the change order", sort_date=r.work_date))
        else:
            items.append(_item("extra_work", f"Extra work reported: {r.description[:80]}",
                               f"{_label(projects.get(r.project_id))} · {r.reported_by_name}",
                               "Answered — review it" if r.status == "ANSWERED" else "Waiting for your review",
                               _day(r.work_date), f"/operations/extra-work/{r.id}", "Review extra work",
                               urgency="today", sort_date=r.work_date))
    from app.models.work_structure import ProjectWorkActivity
    from app.services.work_scope import inherit_scope_lineage

    for activity in ProjectWorkActivity.query.filter_by(organization_id=org, scope_origin="EXTRA_WORK", status="ACTIVE"):
        if activity.id in reported_activities or activity.change_order_id:
            continue
        if inherit_scope_lineage(activity)["effective_origin"] != "EXTRA_WORK":
            continue
        project = projects.get(activity.element.project_id) if activity.element else None
        if project is None:
            continue
        items.append(_item("extra_work", f"Extra work not on a change order: {activity.display_name}",
                           _label(project), "No change order yet", "",
                           f"/work-structure/projects/{project.id}", "Review extra work"))
    from app.project_controls.models import ChangeOrder

    seen_co = {i["href"] for i in items}
    for co in ChangeOrder.query.filter(ChangeOrder.organization_id == org, ChangeOrder.status == "Pending Approval"):
        href = f"/project-controls/change-orders/{co.id}"
        if href in seen_co:
            continue
        items.append(_item("extra_work", f"Change order {co.number}: {co.title}", _label(projects.get(co.project_id)),
                           "Waiting for the customer's approval", _day(co.requested_date), href,
                           "Open the change order", sort_date=co.requested_date))

    # ---- supplier quotes, orders, deliveries
    from app.models.supplier_portal import (
        PO_PROBLEM,
        SHARE_OPENED,
        SHARE_RETURNED,
        SHARE_SENT,
        SupplierDeliveryChange,
        SupplierPurchaseOrder,
        SupplierRequestShare,
    )

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
        href = f"/projects/{share.project_id}/supplier-requests#share-{share.id}"
        if share.status == SHARE_RETURNED:
            items.append(_item("quotes", f"Price returned by {share.supplier.legal_name} ({share.number})",
                               _label(projects.get(share.project_id)), "Review the price and order",
                               ("Needed by " + _day(needed)) if needed else _day(local_date(share.returned_at)),
                               href, "Review and order", urgency=_urgency(needed, today) or "today",
                               sort_date=needed or today))
        else:
            items.append(_item("quotes", f"Waiting for a price from {share.supplier.legal_name} ({share.number})",
                               _label(projects.get(share.project_id)),
                               "Opened by the supplier" if share.status == SHARE_OPENED else "Sent to the supplier",
                               ("Needed by " + _day(needed)) if needed else f"Asked {_day(local_date(share.sent_at))}",
                               href, "Open the request", urgency=_urgency(needed, today),
                               sort_date=needed or date.max))
    for order in SupplierPurchaseOrder.query.filter_by(organization_id=org, status=PO_PROBLEM):
        items.append(_item("deliveries", f"{order.share.supplier.legal_name} reported a problem with {order.number}",
                           _label(projects.get(order.project_id)), "Supplier problem", "",
                           f"/projects/{order.project_id}/supplier-requests#share-{order.share_id}", "Open the order",
                           urgency="today"))
    for change in SupplierDeliveryChange.query.filter_by(status="PENDING", requested_by_side="SUPPLIER"):
        order = change.order
        if order is None or order.organization_id != org:
            continue
        items.append(_item("deliveries", f"{order.share.supplier.legal_name} asks to move {order.number} to "
                           f"{_day(change.new_date)}", _label(projects.get(order.project_id)),
                           "Delivery change waiting for your answer", _day(change.new_date),
                           f"/projects/{order.project_id}/supplier-requests#share-{order.share_id}", "Answer",
                           urgency=_urgency(change.new_date, today) or "today", sort_date=change.new_date))
    for row in DeliveryConfirmation.query.filter_by(organization_id=org, exception_status=EXCEPTION_OPEN):
        items.append(_item("deliveries", f"Delivery {row.outcome_label.lower()}: {row.order.number} "
                           f"({row.order.share.supplier.legal_name})", f"{_label(projects.get(row.project_id))} · "
                           f"{row.confirmed_by_name}", "Delivery problem to resolve", _day(local_date(row.confirmed_at)),
                           f"/operations/deliveries/{row.id}", "Resolve delivery", urgency="today",
                           sort_date=local_date(row.confirmed_at)))

    # ---- receipts and QuickBooks
    if has_office_financial_access(viewer, org):
        grouped = defaultdict(list)
        for r in FieldReceipt.query.filter(FieldReceipt.organization_id == org,
                                           FieldReceipt.status.in_((RECEIPT_NEW, RECEIPT_REVIEWED,
                                                                    RECEIPT_NEEDS_ATTENTION, RECEIPT_SYNC_FAILED))):
            if r.status in (RECEIPT_NEW, RECEIPT_REVIEWED):
                grouped[r.status].append(r)
                continue
            failed = r.status == RECEIPT_SYNC_FAILED
            items.append(_item("receipts", f"Receipt {r.number}: {'QuickBooks transfer failed' if failed else 'needs attention'}",
                               f"{_label(projects.get(r.project_id))} · {r.shown_supplier or 'supplier not entered'}",
                               r.status_label, _day(r.receipt_date or local_date(r.submitted_at)),
                               f"/accounting/receipts/{r.id}", "Open the receipt", urgency="today",
                               sort_date=r.receipt_date or local_date(r.submitted_at)))
        for status, rows in grouped.items():
            oldest = min(local_date(r.submitted_at) for r in rows)
            items.append(_item("receipts", f"{len(rows)} receipt{'s' if len(rows) != 1 else ''} "
                               + ("to review" if status == RECEIPT_NEW else "reviewed, waiting for approval"),
                               "Receipts Inbox", "New" if status == RECEIPT_NEW else "Reviewed", f"Since {_day(oldest)}",
                               f"/accounting/receipts?status={status}", "Open the Receipts Inbox", sort_date=oldest))
        from app.models.payroll_time import QBT_STATUS_FAILED, QBT_STATUS_NEEDS_SETUP, QuickBooksTimeTransfer

        qbt = QuickBooksTimeTransfer.query.filter(QuickBooksTimeTransfer.organization_id == org,
                                                  QuickBooksTimeTransfer.status.in_((QBT_STATUS_FAILED,
                                                                                     QBT_STATUS_NEEDS_SETUP))).count()
        if qbt:
            items.append(_item("quickbooks", f"{qbt} approved time entr{'y' if qbt == 1 else 'ies'} did not reach "
                               "QuickBooks Time", "Payroll", "Failed or needs a link", "", "/time/quickbooks-time",
                               "Fix and retry", urgency="today"))

    # ---- schedule conflicts, job updates, punch list, texts
    from app.services.schedule import list_schedule_conflicts

    try:
        conflicts = list_schedule_conflicts(org, window_start=today, window_end=today + timedelta(days=14))
    except Exception:  # never let one source hide the rest
        conflicts = []
    for c in conflicts:
        project = projects.get(c.get("project_id"))
        items.append(_item("schedule", c.get("summary") or "Schedule conflict", _label(project), c.get("label") or
                           "Schedule conflict", "Next two weeks", f"/projects/{project.id}#hub-schedule" if project else
                           "/schedule", "Open the schedule", urgency="soon"))
    for s in DailyJobSummary.query.filter_by(organization_id=org, problem_status=PROBLEM_OPEN):
        items.append(_item("tasks", f"Problem or delay reported: {(s.problems_text or '')[:80]}",
                           f"{_label(projects.get(s.project_id))} · {s.submitted_by_name}", "Job update — open",
                           _day(s.work_date), f"/operations/job-updates/{s.id}", "Open the job update",
                           urgency="today", sort_date=s.work_date))
    from app.models.punch_list import PUNCH_LIST_STATUS_OPEN, ProjectPunchListItem

    punch = defaultdict(int)
    for row in ProjectPunchListItem.query.filter_by(organization_id=org, status=PUNCH_LIST_STATUS_OPEN):
        punch[row.project_id] += 1
    for pid, n in punch.items():
        project = projects.get(pid)
        if project is None or project.operating_state != "ACTIVE":
            continue
        items.append(_item("tasks", f"{n} open punch list item{'s' if n != 1 else ''}", _label(project), "Open", "",
                           f"/projects/{pid}#hub-punch-list", "Open the punch list"))

    # ---- labour and schedule facts (Company Attention), for COMPANY_MANAGEMENT as on that page
    if include_company_facts is None:
        include_company_facts = membership_has_access_domain(viewer, org, ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    if include_company_facts:
        from app.services.company_attention import assemble_company_attention
        from app.services.project_performance import FACT_EXTRA_WORK_NEEDS_REVIEW

        for fact in assemble_company_attention(org, today=today).get("items") or []:
            if fact.get("fact_type") == FACT_EXTRA_WORK_NEEDS_REVIEW:
                continue  # listed above from the extra work itself
            dest = fact.get("destination") or {}
            items.append(_item("labour", fact.get("title") or "", (fact.get("project") or {}).get("name") or "",
                               fact.get("detail") or "", "", dest.get("href") or f"/projects/{fact.get('project_id')}",
                               "Open"))

    items.sort(key=lambda i: (URGENCY_ORDER.get(i["urgency"], 3), i["sort_date"], i["what"]))
    kinds = defaultdict(int)
    for i in items:
        kinds[i["kind"]] += 1
    return {"items": items, "count": len(items), "hidden": False, "kinds": dict(kinds)}


def _reminder_time(org) -> str:
    from app.services.reminders import settings_for

    return settings_for(org).reminder_time or "16:30"
