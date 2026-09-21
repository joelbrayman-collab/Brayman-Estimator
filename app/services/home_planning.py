"""Desktop Home planning presentation.

Reads existing Schedule, Project, Estimate, Proposal, and Company Attention
authority. Does not persist calendar state. Does not invent day-off, payday,
holiday, capacity, or readiness facts.
"""

from __future__ import annotations

from datetime import date, timedelta
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


def _week_rows(grid_start: date, grid_end: date, bands: list[dict], selected: date):
    weeks = []
    cursor = grid_start
    week_number = 1
    while cursor <= grid_end:
        week_end = cursor + timedelta(days=6)
        days = []
        for offset in range(7):
            day = cursor + timedelta(days=offset)
            days.append(
                {
                    "date": day,
                    "iso": day.isoformat(),
                    "number": day.day,
                    "in_month": day.month == selected.month and day.year == selected.year,
                    "weekend": day.weekday() >= 5,
                    "selected": day == selected,
                    "today": False,
                }
            )
        week_bands = [
            band
            for band in bands
            if band["week_start"] == cursor and band["lane"] < VISIBLE_LANES
        ]
        overflow_by_day = {}
        for band in bands:
            if band["week_start"] != cursor or band["lane"] < VISIBLE_LANES:
                continue
            current = band["start"]
            while current <= band["end"]:
                overflow_by_day[current] = overflow_by_day.get(current, 0) + 1
                current += timedelta(days=1)
        for day in days:
            hidden = overflow_by_day.get(day["date"], 0)
            day["overflow"] = hidden
        weeks.append(
            {
                "label": f"Wk {week_number}",
                "start": cursor,
                "end": week_end,
                "days": days,
                "bands": week_bands,
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


def assemble_home_planning(
    organization_id: str,
    *,
    year: Optional[int] = None,
    month: Optional[int] = None,
    selected_day: Optional[int] = None,
    today: Optional[date] = None,
    viewer=None,
) -> dict:
    today = today or date.today()
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

    grid_start, grid_end = month_grid_bounds(year, month)
    schedule = assemble_schedule(
        organization_id,
        window_start=grid_start,
        window_end=grid_end,
        include_activities=False,
        include_conflicts=True,
    )

    item_rows = []
    for project_row in schedule["projects"]:
        project = project_row["project"]
        for bar in project_row["bars"]:
            item = bar["item"]
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
                }
            )

    conflict_ids = set()
    for fact in schedule.get("conflicts") or []:
        for item_id in fact.get("item_ids") or []:
            conflict_ids.add(item_id)
    for row in item_rows:
        row["conflict"] = row["item_id"] in conflict_ids

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
                    "crew_letter": row["crew"]["letter"],
                    "accent": row["crew"]["accent"] or "none",
                    "conflict": row["conflict"],
                    "project_id": row["project_id"],
                }
            )
        cursor += timedelta(days=7)

    packed = []
    by_week = {}
    for row in segments:
        by_week.setdefault(row["week_start"], []).append(row)
    for week_start, rows in by_week.items():
        packed.extend(_lane_pack(rows))

    weeks = _week_rows(grid_start, grid_end, packed, selected)
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
    if can_attention:
        attention_count = len(
            assemble_company_attention(organization_id, today=today).get("items")
            or []
        )

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

    return {
        "today": today,
        "year": year,
        "month": month,
        "month_label": month_start.strftime("%B %Y"),
        "selected": selected,
        "weeks": weeks,
        "detail": _selected_detail(selected, item_rows, schedule.get("conflicts") or []),
        "pulse": pulse,
        "unscheduled": unscheduled_rows,
        "unscheduled_more": max(len(unscheduled) - len(unscheduled_rows), 0),
        "can_attention": can_attention,
        "attention_count": attention_count,
        "prev": {"year": prev_month.year, "month": prev_month.month},
        "next": {"year": next_month.year, "month": next_month.month},
        "first_name": first_name,
        "has_scheduled_work": bool(item_rows),
    }
