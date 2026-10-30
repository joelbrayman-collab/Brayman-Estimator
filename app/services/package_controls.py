"""Cost and margin control, execution actuals and closeout by work package (Joel, 30 Oct 2026).

One view, by the same governed work packages that priced the job:
- estimate: direct cost, selling price and hours of the approved version (Gate 1);
- change: approved change-order items tied to the package;
- committed: approved subcontracts and placed purchase orders (Gate 3);
- actual: approved labour time on the work plan items built from the package (hours x the estimate's labour rate);
- forecast and margin.

Closeout compares estimated and actual hours and durations, and proposes calibration factors for the next estimate.
Proposals only: a person records the closeout (decision 3). Nothing changes an estimate or a rate by itself.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app import db

ZERO = Decimal("0")
CENT = Decimal("0.01")


def _q(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT)


def approved_version(project):
    """The project's latest approved (Gate 1) estimate version, or None."""
    from app.models import Estimate, EstimateApproval

    row = (EstimateApproval.query.join(Estimate, Estimate.id == EstimateApproval.estimate_id)
           .filter(Estimate.project_id == project.id).order_by(EstimateApproval.id.desc()).first())
    return row.estimate_version if row is not None else None


def _actual_hours_by_package(project) -> dict:
    from app.models import LabourTimeEntry, ProjectWorkElement
    from app.models.time_entry import TIME_STATUS_APPROVED

    element_package = {e.id: e.guided_stage_id
                       for e in ProjectWorkElement.query.filter_by(project_id=project.id,
                                                                   organization_id=project.organization_id)}
    hours: dict = {}
    dates: dict = {}
    for entry in LabourTimeEntry.query.filter_by(project_id=project.id, organization_id=project.organization_id,
                                                 status=TIME_STATUS_APPROVED):
        key = element_package.get(entry.project_work_element_id)
        hours[key] = hours.get(key, ZERO) + Decimal(str(entry.hours or 0))
        dates.setdefault(key, []).append(entry.work_date)
    return hours, dates


def _change_by_package(project) -> dict:
    from app.project_controls.models import ChangeOrder

    out: dict = {}
    for change in ChangeOrder.query.filter(ChangeOrder.project_id == project.id,
                                           ChangeOrder.status.in_(("Approved", "Invoiced"))):
        for item in change.items:
            key = getattr(item, "guided_stage_id", None)
            out[key] = out.get(key, ZERO) + Decimal(str(item.total or 0))
    return out


def package_cost_report(project) -> dict:
    from app.services import procurement_gate as PG
    from app.services import work_packages as WP
    from app.services.estimate_economics import economics
    from app.services.estimate_labour_hours import is_labour_line
    from app.services.guided_estimating import get_guided

    version = approved_version(project)
    if version is None:
        return {"version": None, "rows": [], "totals": None,
                "message": "Approve the estimate (Gate 1) to control cost against it."}
    e = economics(version)
    rate = Decimal(str(e.get("labour_rate") or 0))
    actual_hours, _dates = _actual_hours_by_package(project)
    committed = PG.committed_by_package(project)
    changes = _change_by_package(project)
    rows = []
    for package in WP.packages_in(get_guided(project.organization_id, project.id), version):
        if not WP.package_participates(package, version):
            continue
        lines = WP.package_lines(package, version)
        est_direct = sum((Decimal(str(l.extended_cost or 0)) for l in lines), ZERO)
        est_sell = sum((Decimal(str(l.sell_price or 0)) for l in lines), ZERO)
        est_hours = sum((Decimal(str(l.quantity or 0)) for l in lines if is_labour_line(l)), ZERO)
        est_labour = sum((Decimal(str(l.extended_cost or 0)) for l in lines if is_labour_line(l)), ZERO)
        act_hours = actual_hours.get(package.id, ZERO)
        act_labour = act_hours * rate
        com = committed.get(package.id, ZERO)
        change = changes.get(package.id, ZERO)
        # Forecast: the estimate's non-labour cost (or what is committed, if more), plus the labour still expected:
        # the larger of the estimate's labour and what has already been spent.
        non_labour = max(est_direct - est_labour, com)
        forecast = non_labour + max(est_labour, act_labour)
        revenue = est_sell + change
        rows.append({"package": package, "estimate_direct": _q(est_direct), "estimate_sell": _q(est_sell),
                     "estimate_hours": _q(est_hours), "change": _q(change), "committed": _q(com),
                     "actual_hours": _q(act_hours), "actual_labour": _q(act_labour), "forecast": _q(forecast),
                     "revenue": _q(revenue), "margin": _q(revenue - forecast),
                     "hours_variance": _q(act_hours - est_hours)})
    totals = {k: _q(sum((r[k] for r in rows), ZERO)) for k in
              ("estimate_direct", "estimate_sell", "estimate_hours", "change", "committed", "actual_hours",
               "actual_labour", "forecast", "revenue", "margin")}
    unlinked = {"actual_hours": _q(actual_hours.get(None, ZERO)), "committed": _q(committed.get(None, ZERO)),
                "change": _q(changes.get(None, ZERO))}
    return {"version": version, "rows": rows, "totals": totals, "unlinked": unlinked, "labour_rate": _q(rate),
            "message": None}


# ---------------------------------------------------------------------------------------------- closeout
def _working_days(start, end) -> int:
    from app.services.governed_schedule import is_working_day
    from datetime import timedelta

    if start is None or end is None:
        return 0
    days, current = 0, start
    while current <= end:
        if is_working_day(current):
            days += 1
        current += timedelta(days=1)
    return days


def closeout_report(project) -> dict:
    """Estimated against actual, by work package, with calibration factors proposed for the next estimate."""
    from app.models import WorkScheduleItem
    from app.models import ProjectWorkElement

    report = package_cost_report(project)
    _hours, dates = _actual_hours_by_package(project)
    planned: dict = {}
    for element in ProjectWorkElement.query.filter_by(project_id=project.id, organization_id=project.organization_id):
        if element.guided_stage_id is None:
            continue
        items = WorkScheduleItem.query.filter_by(project_work_element_id=element.id, status="ACTIVE").all()
        if items:
            planned[element.guided_stage_id] = _working_days(min(i.scheduled_start for i in items),
                                                             max(i.scheduled_end for i in items))
    rows = []
    for row in report["rows"]:
        package = row["package"]
        worked = sorted(dates.get(package.id, []))
        actual_days = _working_days(worked[0], worked[-1]) if worked else 0
        factor = (row["actual_hours"] / row["estimate_hours"]).quantize(Decimal("0.001")) \
            if row["estimate_hours"] and row["actual_hours"] else None
        rows.append({**row, "planned_days": planned.get(package.id, 0), "actual_days": actual_days,
                     "productivity_factor": factor})
    return {**report, "rows": rows}


def record_closeout(project, *, actor: str, note: str = "") -> "ProjectCloseoutRecord":
    """A person records the closeout. The calibration factors are kept as proposals for future estimates."""
    from app.models.closeout import ProjectCloseoutRecord

    name = " ".join((actor or "").split())[:160]
    if not name or name.lower() in {"system", "ai", "automatic", "calibraytai"}:
        raise ValueError("A person must record the closeout.")
    report = closeout_report(project)
    if report["version"] is None:
        raise ValueError(report["message"])
    payload = {
        "version_id": report["version"].id,
        "labour_rate": str(report["labour_rate"]),
        "totals": {k: str(v) for k, v in report["totals"].items()},
        "packages": [{"package_id": r["package"].id, "name": r["package"].display_name,
                      "estimate_hours": str(r["estimate_hours"]), "actual_hours": str(r["actual_hours"]),
                      "planned_days": r["planned_days"], "actual_days": r["actual_days"],
                      "productivity_factor": str(r["productivity_factor"]) if r["productivity_factor"] else None,
                      "estimate_direct": str(r["estimate_direct"]), "forecast": str(r["forecast"]),
                      "margin": str(r["margin"])} for r in report["rows"]],
    }
    record = ProjectCloseoutRecord(organization_id=project.organization_id, project_id=project.id,
                                   recorded_by_name=name, recorded_at=datetime.utcnow(),
                                   note=(note or "").strip() or None, report_json=json.dumps(payload, sort_keys=True))
    db.session.add(record)
    db.session.commit()
    return record


def calibration_proposals(organization_id: str, *, name: Optional[str] = None) -> list:
    """Productivity factors from recorded closeouts, by work-package name: a proposal to review, never applied."""
    from app.models.closeout import ProjectCloseoutRecord

    seen: dict = {}
    for record in ProjectCloseoutRecord.query.filter_by(organization_id=organization_id):
        for row in json.loads(record.report_json).get("packages", []):
            if row.get("productivity_factor") and (name is None or row["name"] == name):
                seen.setdefault(row["name"], []).append(Decimal(row["productivity_factor"]))
    return [{"name": key, "projects": len(values),
             "average_factor": (sum(values) / len(values)).quantize(Decimal("0.001"))}
            for key, values in sorted(seen.items())]
