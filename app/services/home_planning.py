"""Desktop Home planning presentation.

Reads existing Schedule, Project, Estimate, Proposal, and Company Attention
authority. Does not persist calendar state. Does not invent day-off, payday,
holiday, capacity, or readiness facts.
"""

from __future__ import annotations

from datetime import date, timedelta
from app.services.local_time import local_today
from typing import Optional

from flask_login import current_user

from app.models import Estimate, Project, Proposal
from app.models.proposal import ProposalTemplate
from app.presentation import contractor_copy
from app.project_controls.models import OPEN_CHANGE_ORDER_STATUSES, ChangeOrder
from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    membership_has_access_domain,
)
from app.services.company_attention import assemble_company_attention
from app.services.schedule import (
    assemble_schedule,
    calendar_month_bounds,
    list_unscheduled_elements,
)
from app.services.shared_api import list_current_operating_projects

VISIBLE_LANES = 4
OUTSTANDING_ESTIMATE_STATUSES = ("Draft", "In Review")
OUTSTANDING_PROPOSAL_STATUSES = ("Draft", "Ready", "Issued")
CREW_ACCENT = ("a", "b", "c")


def month_grid_bounds(year: int, month: int) -> tuple[date, date]:
    first, last = calendar_month_bounds(year, month)
    grid_start = first - timedelta(days=first.weekday())
    grid_end = last + timedelta(days=(6 - last.weekday()))
    return grid_start, grid_end


def _shift_month(year: int, month: int, months: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + months
    return index // 12, index % 12 + 1


def scroll_month_bounds(year: int, month: int, before: int = 0, after: int = 0) -> tuple[date, date]:
    """Weeks for a scrolling month view (Joel, 20 Oct 2026): from the first week of ``before`` months
    earlier to the last week of ``after`` months later. 0 and 0 is the single month grid."""
    grid_start, _ = month_grid_bounds(*_shift_month(year, month, -before))
    _, grid_end = month_grid_bounds(*_shift_month(year, month, after))
    return grid_start, grid_end


def _clip(start: date, end: date, window_start: date, window_end: date):
    clipped_start = max(start, window_start)
    clipped_end = min(end, window_end)
    if clipped_end < clipped_start:
        return None
    return clipped_start, clipped_end


def _crew_from_assignments(assignments) -> dict:
    crews = [row for row in assignments if row.get("kind") == "CREW"]
    if not crews:
        return {"letter": None, "name": None, "accent": None, "crew_id": None}
    row = crews[0]
    name = (row.get("name") or contractor_copy.SCHEDULE_CREW).strip()
    letter = name[:1].upper() if name else None
    crew_id = row.get("crew_id")
    accent = None
    if crew_id is not None:
        accent = CREW_ACCENT[int(crew_id) % len(CREW_ACCENT)]
    return {
        "letter": letter,
        "name": name,
        "accent": accent,
        "crew_id": crew_id,
    }


def _lane_pack(segments: list[dict]) -> list[dict]:
    lanes: list[list[tuple[date, date]]] = []
    packed = []
    ordered = sorted(
        segments,
        key=lambda row: (row["start"], row["end"], row["item_id"]),
    )
    for row in ordered:
        placed = None
        for index, occupied in enumerate(lanes):
            if all(row["end"] < start or row["start"] > end for start, end in occupied):
                occupied.append((row["start"], row["end"]))
                placed = index
                break
        if placed is None:
            lanes.append([(row["start"], row["end"])])
            placed = len(lanes) - 1
        packed.append({**row, "lane": placed})
    return packed


def _week_rows(grid_start: date, grid_end: date, bands: list[dict], selected: date, visible_lanes: int = VISIBLE_LANES):
    weeks = []
    cursor = grid_start
    week_number = 1
    while cursor <= grid_end:
        week_end = cursor + timedelta(days=6)
        days = []
        for offset in range(7):
            day = cursor + timedelta(days=offset)
            months_from_selected = (day.year - selected.year) * 12 + day.month - selected.month
            days.append(
                {
                    "date": day,
                    "iso": day.isoformat(),
                    "number": day.day,
                    "in_month": day.month == selected.month and day.year == selected.year,
                    # Scrolling month view: every other month is shaded, the selected month is not.
                    "alt_month": months_from_selected % 2 == 1,
                    "month_start": day.day == 1,
                    "month_short": day.strftime("%b"),
                    "weekend": day.weekday() >= 5,
                    "selected": day == selected,
                    "today": False,
                }
            )
        week_bands = [
            band
            for band in bands
            if band["week_start"] == cursor and band["lane"] < visible_lanes
        ]
        overflow_by_day = {}
        count_by_day = {}
        for band in bands:
            if band["week_start"] != cursor:
                continue
            current = band["start"]
            while current <= band["end"]:
                count_by_day[current] = count_by_day.get(current, 0) + 1
                if band["lane"] >= visible_lanes:
                    overflow_by_day[current] = overflow_by_day.get(current, 0) + 1
                current += timedelta(days=1)
        for day in days:
            hidden = overflow_by_day.get(day["date"], 0)
            day["overflow"] = hidden
            day["count"] = count_by_day.get(day["date"], 0)
        # Mon–Fri view (Joel, 23 Oct 2026): what a hidden Saturday or Sunday holds, so it is never missed.
        weekend = [
            {"date": d["date"], "label": d["date"].strftime("%a"), "count": d["count"]}
            for d in days
            if d["weekend"] and d["count"]
        ]
        first_of_month = next((d["date"] for d in days if d["date"].day == 1), None)
        thursday = cursor + timedelta(days=3)  # the week belongs to the month of its Thursday
        weeks.append(
            {
                "label": f"Wk {week_number}",
                "month_anchor": first_of_month.strftime("%Y-%m") if first_of_month else "",
                "month_title": thursday.strftime("%B %Y"),
                "month_short": first_of_month.strftime("%b") if first_of_month else "",
                # The in-calendar month heading (Joel, 20 Oct 2026), above the week holding the 1st.
                "month_heading": first_of_month.strftime("%B %Y") if first_of_month else "",
                "start": cursor,
                "end": week_end,
                "days": days,
                "bands": week_bands,
                "weekend": weekend,
            }
        )
        cursor += timedelta(days=7)
        week_number += 1
    return weeks


def _selected_detail(selected: date, items: list[dict], conflicts: list[dict]) -> dict:
    work = [
        row
        for row in items
        if row["scheduled_start"] <= selected <= row["scheduled_end"]
    ]
    people = []
    seen_people = set()
    for row in work:
        for name in row["people"]:
            if name not in seen_people:
                seen_people.add(name)
                people.append(name)
    attention = []
    seen_attn = set()
    work_ids = {row["item_id"] for row in work}
    for fact in conflicts:
        item_ids = set(fact.get("item_ids") or [])
        if item_ids & work_ids:
            summary = fact.get("summary") or fact.get("label")
            if summary and summary not in seen_attn:
                seen_attn.add(summary)
                attention.append(summary)
    return {
        "date": selected,
        "title": selected.strftime("%A") + " · " + selected.strftime("%B") + " " + str(selected.day),
        "work": [
            {
                "label": f"{row['project_name']} — {row['element_name']}",
                "project_id": row["project_id"],
            }
            for row in work
        ],
        "people": people,
        "attention": attention,
    }


def _home_briefing(today: date, item_rows: list[dict], attention_items: list[dict], can_attention: bool) -> dict:
    """Project Today, attention, and the next seven days from rows already read."""

    def covering(day: date) -> list[dict]:
        return [
            row
            for row in item_rows
            if row["scheduled_start"] <= day <= row["scheduled_end"]
        ]

    def work_line(row: dict) -> dict:
        return {
            "label": f"{row['project_name']} — {row['element_name']}",
            "project_id": row["project_id"],
        }

    today_work = [work_line(row) for row in covering(today)]
    coming = []
    for offset in range(1, 8):
        day = today + timedelta(days=offset)
        rows = covering(day)
        if not rows:
            continue
        coming.append(
            {
                "label": day.strftime("%A") + " " + str(day.day) + " " + day.strftime("%B"),
                "work": [work_line(row) for row in rows],
            }
        )
    attention = []
    if can_attention:
        for item in attention_items[:8]:
            project = item.get("project") or {}
            destination = item.get("destination") or {}
            attention.append(
                {
                    "title": item.get("title") or "",
                    "project_name": project.get("name") or "",
                    "href": destination.get("href") or f"/projects/{item.get('project_id')}",
                }
            )
    return {
        "today_label": today.strftime("%A") + " " + str(today.day) + " " + today.strftime("%B"),
        "today_work": today_work,
        "today_empty": not today_work,
        "attention": attention,
        "attention_empty": can_attention and not attention,
        "attention_hidden": not can_attention,
        "coming": coming,
        "coming_empty": not coming,
    }


def _delivery_rows(organization_id: str, start: date, end: date) -> list[dict]:
    """Supplier deliveries on the Company Calendar (Joel, 17 Oct 2026). Read-only."""
    from app.services.supplier_hub import upcoming_deliveries

    rows = []
    for row in upcoming_deliveries(organization_id=organization_id):
        day = row["schedule"]["date"]
        if day is None or not (start <= day <= end):
            continue
        order = row["order"]
        kind = "Concrete" if order.share.request_kind == "CONCRETE" else "Delivery"
        window = row["schedule"]["window"]
        rows.append({
            "order_id": order.id,
            "project_id": order.project_id,
            "date": day,
            "pending": row["pending"] is not None,
            "label": f"{kind} · {order.share.supplier.legal_name} · {row['project'].name}" + (f" · {window}" if window else ""),
            "href": f"/projects/{order.project_id}/supplier-requests#share-{order.share_id}",
            "status": ("Change requested" if row["pending"] is not None else ("Agreed" if row["schedule"]["agreed"] else "Waiting for supplier")),
        })
    return rows


def _assigned_in_window(item, user_id: int, start: date, end: date, organization_id: str) -> bool:
    """True when the person is on this work on any day it falls in the window (crews by their dates)."""
    from app.services.schedule import worker_assigned_on_date

    if any(a.worker_user_id == user_id for a in item.assignments):
        return True
    if not any(a.crew_id is not None for a in item.assignments):
        return False
    day = max(item.scheduled_start, start)
    last = min(item.scheduled_end, end)
    while day <= last:
        if worker_assigned_on_date(item, user_id, day, organization_id=organization_id):
            return True
        day += timedelta(days=1)
    return False


def _calendar_sources(organization_id: str, start: date, end: date, *, project_id: Optional[int] = None,
                      mine_user_id: Optional[int] = None):
    """Scheduled work and supplier deliveries between ``start`` and ``end`` for the calendar, with the
    calendar's own filters (project; My Calendar = work assigned to that person and those projects'
    deliveries). Shared by the calendar page and its printout so both always show the same entries."""
    from app.presentation.schedule_categories import activity_category

    schedule = assemble_schedule(
        organization_id,
        window_start=start,
        window_end=end,
        include_activities=False,
        include_conflicts=True,
    )

    item_rows = []
    for project_row in schedule["projects"]:
        project = project_row["project"]
        if project_id is not None and project.id != project_id:
            continue
        for bar in project_row["bars"]:
            item = bar["item"]
            if mine_user_id is not None and not _assigned_in_window(item, mine_user_id, start, end, organization_id):
                continue
            assignments = bar.get("assignments") or []
            crew = _crew_from_assignments(assignments)
            people = [row["name"] for row in assignments if row.get("name")]
            element = item.element
            element_name = element.display_name if element is not None else contractor_copy.SCHEDULE_HEADING
            item_rows.append(
                {
                    "item_id": item.id,
                    "project_id": project.id,
                    "project_name": project.name,
                    "element_name": element_name,
                    "scheduled_start": item.scheduled_start,
                    "scheduled_end": item.scheduled_end,
                    "crew": crew,
                    "people": people,
                    "conflict": False,
                    "category": activity_category(element),
                }
            )

    conflict_ids = set()
    for fact in schedule.get("conflicts") or []:
        for item_id in fact.get("item_ids") or []:
            conflict_ids.add(item_id)
    for row in item_rows:
        row["conflict"] = row["item_id"] in conflict_ids

    delivery_rows = _delivery_rows(organization_id, start, end)
    if project_id is not None:
        delivery_rows = [row for row in delivery_rows if row["project_id"] == project_id]
    if mine_user_id is not None:
        my_projects = {row["project_id"] for row in item_rows}
        delivery_rows = [row for row in delivery_rows if row["project_id"] in my_projects]
    return schedule, item_rows, delivery_rows


def _entries_for(day: date, item_rows: list[dict], delivery_rows: list[dict], appointments) -> list[dict]:
    """One day's calendar entries in calendar order: all-day appointments, work, deliveries, timed appointments."""
    work = [
        {
            "kind": "work",
            "project_id": row["project_id"],
            "label": row["element_name"],
            "project_name": row["project_name"],
            "category": row["category"],
            "crew_letter": row["crew"]["letter"],
            "crew_name": row["crew"]["name"],
            "people": row["people"],
            "conflict": row["conflict"],
            "href": f"/projects/{row['project_id']}#hub-schedule",
            "edit_href": f"/schedule/items/{row['item_id']}",
        }
        for row in item_rows
        if row["scheduled_start"] <= day <= row["scheduled_end"]
    ]
    deliveries = [
        {
            "kind": "delivery",
            "label": row["label"],
            "project_name": "",
            "category": "delivery-pending" if row["pending"] else "delivery",
            "status": row["status"],
            "href": row["href"],
        }
        for row in delivery_rows
        if row["date"] == day
    ]
    booked = sorted(
        (dict(row, kind="appointment") for row in appointments or () if row["date"] == day),
        key=lambda r: (not r["all_day"], r["start_min"], r["id"]),
    )
    return [r for r in booked if r["all_day"]] + work + deliveries + [r for r in booked if not r["all_day"]]


def calendar_print_days(organization_id: str, start: date, end: date, *, appointments=None,
                        project_id: Optional[int] = None, mine_user_id: Optional[int] = None) -> list[dict]:
    """Calendar printout (Joel, 23 Oct 2026): every day from ``start`` to ``end`` (both included) with the
    same entries the calendar shows for the same filters. ``appointments`` come from
    ``app.services.appointments.calendar_rows`` for the same range and viewer."""
    _schedule, item_rows, delivery_rows = _calendar_sources(
        organization_id, start, end, project_id=project_id, mine_user_id=mine_user_id
    )
    days = []
    day = start
    while day <= end:
        days.append({"date": day, "entries": _entries_for(day, item_rows, delivery_rows, appointments)})
        day += timedelta(days=1)
    return days


def assemble_home_planning(
    organization_id: str,
    *,
    year: Optional[int] = None,
    month: Optional[int] = None,
    selected_day: Optional[int] = None,
    today: Optional[date] = None,
    viewer=None,
    project_id: Optional[int] = None,
    appointments: Optional[list] = None,
    mine_user_id: Optional[int] = None,
    months_before: int = 0,
    months_after: int = 0,
    visible_lanes: int = VISIBLE_LANES,
) -> dict:
    """Month planning data. ``project_id`` (Company Calendar filter) limits the bars, the selected
    day and the week/day lists to one project; Home never passes it. ``appointments`` (Company
    Calendar only, from ``app.services.appointments.calendar_rows``) adds business appointments to
    the month, the selected day and the week/day lists; Home never passes them. ``mine_user_id``
    (My Calendar) keeps only work assigned to that person, directly or through a crew they are on
    at the time, and deliveries for those projects. ``months_before`` / ``months_after`` (Calendar
    month view) extend the weeks so the month view scrolls through several months."""
    today = today or local_today()
    year = int(year or today.year)
    month = int(month or today.month)
    if month < 1 or month > 12:
        year, month = today.year, today.month
    month_start, month_end = calendar_month_bounds(year, month)
    if selected_day is None:
        selected = today if month_start <= today <= month_end else month_start
    else:
        last = month_end.day
        day_number = max(1, min(int(selected_day), last))
        selected = date(year, month, day_number)

    grid_start, grid_end = scroll_month_bounds(year, month, months_before, months_after)
    schedule, item_rows, delivery_rows = _calendar_sources(
        organization_id, grid_start, grid_end, project_id=project_id, mine_user_id=mine_user_id
    )

    segments = []
    cursor = grid_start
    while cursor <= grid_end:
        week_end = cursor + timedelta(days=6)
        for row in item_rows:
            clipped = _clip(
                row["scheduled_start"], row["scheduled_end"], cursor, week_end
            )
            if clipped is None:
                continue
            start, end = clipped
            col_start = start.weekday() + 1
            col_end = end.weekday() + 2
            segments.append(
                {
                    "item_id": row["item_id"],
                    "week_start": cursor,
                    "start": start,
                    "end": end,
                    "col_start": col_start,
                    "col_end": col_end,
                    "label": f"{row['project_name']} · {row['element_name']}",
                    "short_label": f"{row['element_name']} · {row['project_name']}",
                    "category": row["category"],
                    "crew_letter": row["crew"]["letter"],
                    "accent": row["crew"]["accent"] or "none",
                    "conflict": row["conflict"],
                    "project_id": row["project_id"],
                }
            )
        for row in delivery_rows:
            if cursor <= row["date"] <= week_end:
                segments.append(
                    {
                        "item_id": -row["order_id"],
                        "week_start": cursor,
                        "start": row["date"],
                        "end": row["date"],
                        "col_start": row["date"].weekday() + 1,
                        "col_end": row["date"].weekday() + 2,
                        "label": row["label"],
                        "short_label": row["label"],
                        "category": "delivery",
                        "crew_letter": "",
                        "accent": "delivery-pending" if row["pending"] else "delivery",
                        "conflict": False,
                        "project_id": row["project_id"],
                        "href": row["href"],
                    }
                )
        for row in appointments or ():
            if cursor <= row["date"] <= week_end:
                segments.append(
                    {
                        "item_id": -1_000_000_000 + row["start_min"] * 100_000 + row["id"],
                        "week_start": cursor,
                        "start": row["date"],
                        "end": row["date"],
                        "col_start": row["date"].weekday() + 1,
                        "col_end": row["date"].weekday() + 2,
                        "label": f"{row['time_label']} · {row['title']}",
                        "short_label": row["label"],
                        "category": "appointment",
                        "crew_letter": "",
                        "accent": "appointment",
                        "appt_type": row.get("type", "GENERAL"),
                        "conflict": False,
                        "project_id": row["project_id"],
                        "href": row["href"],
                    }
                )
        cursor += timedelta(days=7)

    packed = []
    by_week = {}
    for row in segments:
        by_week.setdefault(row["week_start"], []).append(row)
    for week_start, rows in by_week.items():
        packed.extend(_lane_pack(rows))

    weeks = _week_rows(grid_start, grid_end, packed, selected, visible_lanes)
    for week in weeks:
        for day in week["days"]:
            day["today"] = day["date"] == today

    projects = list_current_operating_projects(organization_id)
    outstanding_estimates = (
        Estimate.query.join(Project, Estimate.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Estimate.status.in_(OUTSTANDING_ESTIMATE_STATUSES),
        )
        .count()
    )
    outstanding_proposals = (
        Proposal.query.join(
            ProposalTemplate, Proposal.proposal_template_id == ProposalTemplate.id
        )
        .filter(
            ProposalTemplate.organization_id == organization_id,
            Proposal.status.in_(OUTSTANDING_PROPOSAL_STATUSES),
        )
        .count()
    )
    open_change_orders = (
        ChangeOrder.query.join(Project, ChangeOrder.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            ChangeOrder.status.in_(tuple(OPEN_CHANGE_ORDER_STATUSES)),
        )
        .count()
    )

    user = viewer if viewer is not None else current_user
    can_attention = False
    attention_count = None
    if getattr(user, "is_authenticated", False):
        can_attention = membership_has_access_domain(
            user, organization_id, ACCESS_DOMAIN_COMPANY_MANAGEMENT
        )
    attention_items = []
    if can_attention:
        attention_items = (
            assemble_company_attention(organization_id, today=today).get("items") or []
        )
        attention_count = len(attention_items)

    pulse = [
        {
            "value": len(projects),
            "label": contractor_copy.HOME_PULSE_PROJECTS,
            "href": "/projects/",
        },
        {
            "value": outstanding_estimates,
            "label": contractor_copy.HOME_PULSE_ESTIMATES,
            "href": "/estimates/",
        },
        {
            "value": outstanding_proposals,
            "label": contractor_copy.HOME_PULSE_PROPOSALS,
            "href": "/proposals/",
        },
        {
            "value": open_change_orders,
            "label": contractor_copy.HOME_PULSE_CHANGE_ORDERS,
            "href": "/project-controls/change-orders/",
        },
    ]
    if can_attention:
        pulse.append(
            {
                "value": attention_count,
                "label": contractor_copy.HOME_PULSE_ATTENTION,
                "href": "/company-attention",
            }
        )

    unscheduled = list_unscheduled_elements(organization_id=organization_id)
    unscheduled_rows = [
        {
            "project_id": element.project_id,
            "project_name": element.project.name if element.project is not None else "",
            "element_name": element.display_name,
        }
        for element in unscheduled[:8]
    ]

    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    next_month = (month_end + timedelta(days=1)).replace(day=1)
    display_name = ""
    if getattr(user, "is_authenticated", False):
        display_name = getattr(user, "display_name", "") or ""
    first_name = display_name.split()[0] if display_name else ""

    current_ids = {project.id for project in projects}
    briefing = _home_briefing(
        today,
        [row for row in item_rows if row["project_id"] in current_ids],
        attention_items,
        can_attention,
    )

    def entries_for(day: date) -> list[dict]:
        return _entries_for(day, item_rows, delivery_rows, appointments)

    week_start = selected - timedelta(days=selected.weekday())
    week_days = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        week_days.append({
            "date": day,
            "label": day.strftime("%a") + " " + str(day.day),
            "long_label": day.strftime("%A") + " " + str(day.day) + " " + day.strftime("%B"),
            "today": day == today,
            "selected": day == selected,
            "entries": entries_for(day),
        })

    return {
        "today": today,
        "briefing": briefing,
        "week_days": week_days,
        "week_label": (week_start.strftime("%b") + " " + str(week_start.day) + " – "
                       + (week_start + timedelta(days=6)).strftime("%b") + " " + str((week_start + timedelta(days=6)).day)),
        "day_entries": entries_for(selected),
        "nav_dates": {
            "prev_week": selected - timedelta(days=7), "next_week": selected + timedelta(days=7),
            "prev_day": selected - timedelta(days=1), "next_day": selected + timedelta(days=1),
        },
        "year": year,
        "month": month,
        "month_label": month_start.strftime("%B %Y"),
        "selected": selected,
        "weeks": weeks,
        "detail": dict(_selected_detail(selected, item_rows, schedule.get("conflicts") or []),
                       deliveries=[row for row in delivery_rows if row["date"] == selected],
                       appointments=[row for row in appointments or () if row["date"] == selected]),
        "pulse": pulse,
        "unscheduled": unscheduled_rows,
        "unscheduled_more": max(len(unscheduled) - len(unscheduled_rows), 0),
        "can_attention": can_attention,
        "attention_count": attention_count,
        "prev": {"year": prev_month.year, "month": prev_month.month},
        "next": {"year": next_month.year, "month": next_month.month},
        "first_name": first_name,
        "has_scheduled_work": bool(item_rows) or bool(appointments),
        "week_dates": [week_start + timedelta(days=offset) for offset in range(7)],
    }
