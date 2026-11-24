"""The approved project baseline (FG-042 S1). Owner or System Administrator only.

Build a PROVISIONAL baseline from an estimate version, import the Labour Calculation Detail by Person, add itemized
cost lines, record open commercial items, reconcile against the approved figures, then freeze. A frozen baseline never
changes (database triggers); a change is a new baseline. Nothing here writes to the estimate, its approval or any
frozen summary."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from app import db
from app.models.person import OrganizationPerson
from app.models.project_baseline import (
    LINE_CATEGORIES,
    ProjectBaseline,
    ProjectBaselineLabourAllocation,
    ProjectBaselineLine,
    ProjectBaselineOpenItem,
    ProjectBaselinePersonRate,
)
from app.services import markup as M

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
RATE_OPEN_PREFIX = "No loaded rate: "


class BaselineError(ValueError):
    """The baseline action is refused (not permitted, not allowed in this status, or the input is invalid)."""


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _require_admin(actor, organization_id: str) -> None:
    from app.services.documents.access import is_people_admin

    if not is_people_admin(actor, organization_id):
        raise BaselineError("Only the owner or a System Administrator may work with a project baseline.")


def _provisional(baseline: ProjectBaseline) -> None:
    if baseline.status != "PROVISIONAL":
        raise BaselineError(f"This baseline is {baseline.status}; only a PROVISIONAL baseline can be changed. "
                            "A change is a new baseline.")


def get_baseline(organization_id: str, baseline_id: int) -> Optional[ProjectBaseline]:
    return ProjectBaseline.query.filter_by(id=baseline_id, organization_id=organization_id).first()


def baselines_for_project(organization_id: str, project_id: int):
    return (ProjectBaseline.query.filter_by(organization_id=organization_id, project_id=project_id)
            .order_by(ProjectBaseline.id.desc()).all())


# ------------------------------------------------------------------------------------------------------ create
def create_provisional_baseline(project, version, *, actor, option_label: str, labour_selling_rate,
                                approval=None) -> ProjectBaseline:
    org = project.organization_id
    _require_admin(actor, org)
    label = (option_label or "").strip()
    if not label:
        raise BaselineError("Name the option this baseline is for (for example, the accepted roof option).")
    if version.estimate is None or version.estimate.project_id != project.id or version.estimate.organization_id != org:
        raise BaselineError("That estimate version does not belong to this project.")
    try:
        rate = _money(labour_selling_rate)
    except Exception as exc:  # noqa: BLE001
        raise BaselineError("The labour selling rate is not a valid number.") from exc
    if rate < 0:
        raise BaselineError("The labour selling rate cannot be negative.")
    if approval is None:
        from app.services.estimate_approval import approval_for

        approval = approval_for(version)
    if approval is not None and approval.estimate_version_id != version.id:
        raise BaselineError("That approval is not for this estimate version.")
    if ProjectBaseline.query.filter_by(project_id=project.id, option_label=label, status="PROVISIONAL").first():
        raise BaselineError(f"A provisional baseline for '{label}' already exists on this project.")
    row = ProjectBaseline(
        organization_id=org, project_id=project.id, estimate_id=version.estimate_id, estimate_version_id=version.id,
        estimate_approval_id=approval.id if approval is not None else None, option_label=label, status="PROVISIONAL",
        labour_selling_rate=rate, pricing_basis="MARKUP", created_at=datetime.utcnow(), created_by_user_id=actor.id)
    db.session.add(row)
    db.session.commit()
    return row


# ------------------------------------------------------------------------------------------------ labour import
def _parse_hours(raw: str, where: str) -> Decimal:
    try:
        value = Decimal((raw or "").strip())
    except Exception as exc:  # noqa: BLE001
        raise BaselineError(f"{where}: hours '{raw}' is not a number.") from exc
    if value < 0:
        raise BaselineError(f"{where}: hours cannot be negative.")
    if value != value.quantize(CENT):
        raise BaselineError(f"{where}: hours '{raw}' has more than two decimal places.")
    return value.quantize(CENT)


def import_labour_csv(baseline: ProjectBaseline, content, *, actor, on_day: Optional[date] = None) -> dict:
    """Replace the labour allocations from the Labour Calculation Detail by Person: columns ``group,task,person,hours``
    (one row per task per person). All-or-nothing: a bad file changes nothing. Returns the control totals."""
    from app.services.employee_rates import loaded_rate_on

    _require_admin(actor, baseline.organization_id)
    _provisional(baseline)
    text = content.decode("utf-8-sig") if isinstance(content, (bytes, bytearray)) else str(content)
    reader = csv.DictReader(io.StringIO(text))
    fields = {(f or "").strip().lower(): f for f in (reader.fieldnames or [])}
    missing = [c for c in ("group", "task", "person", "hours") if c not in fields]
    if missing:
        raise BaselineError("The file needs the columns group, task, person, hours (missing: " + ", ".join(missing) + ").")
    people = {}
    for p in OrganizationPerson.query.filter_by(organization_id=baseline.organization_id).all():
        people.setdefault(p.full_name.strip().lower(), []).append(p)
    rows, unknown, seen, problems = [], [], set(), []
    for number, raw in enumerate(reader, start=2):
        group, task = (raw[fields["group"]] or "").strip(), (raw[fields["task"]] or "").strip()
        name = (raw[fields["person"]] or "").strip()
        if not (group or task or name):
            continue
        where = f"Row {number}"
        if not task or not name:
            problems.append(f"{where}: a task and a person are required.")
            continue
        matches = people.get(name.lower(), [])
        if len(matches) != 1:
            (unknown if not matches else problems).append(
                name if not matches else f"{where}: '{name}' matches more than one employee.")
            continue
        person = matches[0]
        key = (task, person.id)
        if key in seen:
            problems.append(f"{where}: '{task}' lists {name} twice.")
            continue
        seen.add(key)
        rows.append((group, task, person, _parse_hours(raw[fields["hours"]], where)))
    if unknown:
        problems.append("Not in the employee register: " + ", ".join(sorted(set(unknown))) + ".")
    if problems:
        raise BaselineError(" ".join(problems))
    if not rows:
        raise BaselineError("The file has no labour rows.")

    for existing in ProjectBaselineLabourAllocation.query.filter_by(baseline_id=baseline.id).all():
        db.session.delete(existing)
    for existing in ProjectBaselinePersonRate.query.filter_by(baseline_id=baseline.id).all():
        db.session.delete(existing)
    db.session.flush()
    order, task_order = 0, {}
    for group, task, person, hours in rows:
        task_order.setdefault(task, len(task_order))
        db.session.add(ProjectBaselineLabourAllocation(
            baseline_id=baseline.id, group_name=group or "Labour", task_name=task, sort_order=task_order[task],
            person_id=person.id, hours=hours))
    day = on_day or date.today()
    persons = {person.id: person for _g, _t, person, _h in rows}
    without_rate = []
    for person in persons.values():
        dated = loaded_rate_on(person.id, day)
        if dated is None:
            without_rate.append(person.full_name)
            continue
        db.session.add(ProjectBaselinePersonRate(baseline_id=baseline.id, person_id=person.id,
                                                 cost_profile_id=dated.cost_profile_id, loaded_rate=dated.loaded_rate))
    _sync_rate_open_items(baseline, without_rate, actor)
    db.session.commit()
    return {"rows": len(rows), "tasks": len(task_order), "people": len(persons),
            "total_hours": sum((r[3] for r in rows), ZERO), "without_rate": sorted(without_rate)}


def _sync_rate_open_items(baseline, without_rate, actor) -> None:
    wanted = {RATE_OPEN_PREFIX + name for name in without_rate}
    now = datetime.utcnow()
    current = ProjectBaselineOpenItem.query.filter(
        ProjectBaselineOpenItem.baseline_id == baseline.id,
        ProjectBaselineOpenItem.description.like(RATE_OPEN_PREFIX + "%")).all()
    have = set()
    for item in current:
        if item.status == "OPEN" and item.description not in wanted:
            item.status, item.resolved_by_user_id, item.resolved_at = "RESOLVED", actor.id, now
            item.resolution_note = "A loaded rate now exists."
        if item.status == "OPEN":
            have.add(item.description)
    for description in sorted(wanted - have):
        db.session.add(ProjectBaselineOpenItem(baseline_id=baseline.id, description=description, status="OPEN"))


# ------------------------------------------------------------------------------------------------------- lines
def add_line(baseline: ProjectBaseline, *, actor, category: str, description: str, net_cost, supplier_id=None,
             markup_rate=None, quoted_price=None, price_override_reason=None, is_provisional: bool = False,
             provisional_reason=None, source_ref=None, supplier_name=None, sku=None, quantity=None, uom=None,
             list_unit_price=None, discount_amount=None, sort_order: Optional[int] = None) -> ProjectBaselineLine:
    _require_admin(actor, baseline.organization_id)
    _provisional(baseline)
    if category not in LINE_CATEGORIES:
        raise BaselineError("Choose a valid cost category.")
    if not (description or "").strip():
        raise BaselineError("A line needs a description.")
    if is_provisional and not (provisional_reason or "").strip():
        raise BaselineError("A provisional line needs the reason it is provisional.")
    rate = markup_rate
    if rate is None or rate == "":
        rate, _source, _why = M.resolve_markup(baseline.organization_id, project_id=baseline.project_id,
                                               supplier_id=supplier_id)
        if rate is None:
            raise BaselineError("No markup is configured. Enter the markup for this line.")
    try:
        priced = M.price_line(net_cost, rate, quoted_price=quoted_price, override_reason=price_override_reason)
    except M.MarkupError as exc:
        raise BaselineError(str(exc)) from exc
    if sort_order is None:
        sort_order = ProjectBaselineLine.query.filter_by(baseline_id=baseline.id).count()
    line = ProjectBaselineLine(
        baseline_id=baseline.id, category=category, source_ref=source_ref, supplier_name=supplier_name, sku=sku,
        description=description.strip()[:300], quantity=quantity, uom=uom, list_unit_price=list_unit_price,
        discount_amount=discount_amount, net_cost=priced.net_cost, markup_rate=priced.markup_rate,
        selling_price=priced.selling, price_override_reason=priced.override_reason,
        is_provisional=bool(is_provisional), provisional_reason=(provisional_reason or None), sort_order=sort_order)
    db.session.add(line)
    db.session.commit()
    return line


def remove_line(baseline: ProjectBaseline, line_id: int, *, actor) -> None:
    _require_admin(actor, baseline.organization_id)
    _provisional(baseline)
    line = ProjectBaselineLine.query.filter_by(id=line_id, baseline_id=baseline.id).first()
    if line is None:
        raise BaselineError("That line is not on this baseline.")
    db.session.delete(line)
    db.session.commit()


def add_open_item(baseline: ProjectBaseline, description: str, *, actor) -> ProjectBaselineOpenItem:
    _require_admin(actor, baseline.organization_id)
    _provisional(baseline)
    text = (description or "").strip()
    if not text:
        raise BaselineError("Describe the open item.")
    item = ProjectBaselineOpenItem(baseline_id=baseline.id, description=text[:300], status="OPEN")
    db.session.add(item)
    db.session.commit()
    return item


def resolve_open_item(baseline: ProjectBaseline, item_id: int, note: str, *, actor) -> ProjectBaselineOpenItem:
    _require_admin(actor, baseline.organization_id)
    _provisional(baseline)
    item = ProjectBaselineOpenItem.query.filter_by(id=item_id, baseline_id=baseline.id).first()
    if item is None:
        raise BaselineError("That open item is not on this baseline.")
    if item.status != "OPEN":
        raise BaselineError("That open item is already resolved.")
    if not (note or "").strip():
        raise BaselineError("Say how the open item was resolved.")
    item.status, item.resolved_by_user_id, item.resolved_at = "RESOLVED", actor.id, datetime.utcnow()
    item.resolution_note = note.strip()[:300]
    db.session.commit()
    return item


# ------------------------------------------------------------------------------------------------------ totals
def totals(baseline: ProjectBaseline) -> dict:
    """Revenue, Cost, Profit, Profit Margin (in that order) with the pieces that make them. Labour revenue is
    total hours x the labour selling rate, rounded once; labour cost is each person's hours x their loaded rate,
    rounded per person and summed; lines are the sums of their own rounded amounts."""
    rate = Decimal(str(baseline.labour_selling_rate))
    hours_by_person = {}
    for row in ProjectBaselineLabourAllocation.query.filter_by(baseline_id=baseline.id).all():
        hours_by_person[row.person_id] = hours_by_person.get(row.person_id, ZERO) + Decimal(str(row.hours))
    rates = {r.person_id: Decimal(str(r.loaded_rate))
             for r in ProjectBaselinePersonRate.query.filter_by(baseline_id=baseline.id).all()}
    hours = sum(hours_by_person.values(), ZERO)
    labour_revenue = _money(hours * rate)
    unrated = sorted(pid for pid in hours_by_person if pid not in rates)
    labour_cost = sum((_money(h * rates[pid]) for pid, h in hours_by_person.items() if pid in rates), ZERO)
    by_category = {}
    lines = ProjectBaselineLine.query.filter_by(baseline_id=baseline.id).all()
    for line in lines:
        bucket = by_category.setdefault(line.category, {"net_cost": ZERO, "selling": ZERO})
        bucket["net_cost"] += Decimal(str(line.net_cost))
        bucket["selling"] += Decimal(str(line.selling_price))
    material_net = sum((b["net_cost"] for b in by_category.values()), ZERO)
    material_selling = sum((b["selling"] for b in by_category.values()), ZERO)
    revenue = labour_revenue + material_selling
    cost = labour_cost + material_net
    profit = revenue - cost
    return {"revenue": revenue, "cost": cost, "profit": profit,
            "profit_margin": None if revenue == 0 else profit / revenue,
            "hours": hours, "labour_revenue": labour_revenue, "labour_cost": labour_cost,
            "line_net_cost": material_net, "line_selling": material_selling, "by_category": by_category,
            "unrated_person_ids": unrated, "line_count": len(lines)}


# --------------------------------------------------------------------------------------------- reconciliation
SOURCE_KEYS = ("hours", "revenue", "cost", "profit", "labour_cost", "labour_value", "materials",
               "materials_with_margin")
REQUIRED_SOURCE_KEYS = ("hours", "revenue", "cost")


def approved_source_totals(baseline: ProjectBaseline) -> dict:
    """The approved figures, read from the approval's frozen summary when the baseline references one."""
    from app.models.estimate_approval import EstimateApproval
    from app.services.internal_financial_summary import frozen_data
    from app.services.internal_financial_summary import totals as summary_totals

    approval = EstimateApproval.query.get(baseline.estimate_approval_id) if baseline.estimate_approval_id else None
    data = frozen_data(approval) if approval is not None else None
    if not data:
        return {}
    figures = summary_totals(data)
    out = {}
    for key in SOURCE_KEYS:
        if figures.get(key) is not None:
            out[key] = _money(figures[key])
    return out


def reconcile(baseline: ProjectBaseline, source: Optional[dict] = None) -> dict:
    """Source against baseline, figure by figure, with the difference. Anything that is not exact to the cent, a missing
    source figure, a person without a loaded rate, or an unaccounted-for status makes ``ok`` false."""
    src = {k: _money(v) for k, v in (source if source is not None else approved_source_totals(baseline)).items()
           if k in SOURCE_KEYS and v is not None}
    t = totals(baseline)
    mine = {"hours": t["hours"], "revenue": t["revenue"], "cost": t["cost"], "profit": t["profit"],
            "labour_cost": t["labour_cost"], "labour_value": t["labour_revenue"],
            "materials": t["line_net_cost"], "materials_with_margin": t["line_selling"]}
    labels = {"hours": "Labour hours", "revenue": "Revenue", "cost": "Cost", "profit": "Profit",
              "labour_cost": "Labour cost", "labour_value": "Labour at the selling rate",
              "materials": "Materials and other cost at net", "materials_with_margin": "Materials and other at selling"}
    checks = []
    for key in SOURCE_KEYS:
        if key in src:
            diff = _money(mine[key]) - src[key]
            checks.append({"key": key, "label": labels[key], "source": str(src[key]),
                           "baseline": str(_money(mine[key])), "difference": str(diff), "ok": diff == 0})
    problems = []
    for key in REQUIRED_SOURCE_KEYS:
        if key not in src:
            problems.append(f"No source figure for {labels[key].lower()} to reconcile against.")
    if t["unrated_person_ids"]:
        names = [p.full_name for p in OrganizationPerson.query.filter(
            OrganizationPerson.id.in_(t["unrated_person_ids"])).all()]
        problems.append("No loaded rate for: " + ", ".join(sorted(names)) + ".")
    if t["hours"] == 0 and t["line_count"] == 0:
        problems.append("The baseline has no labour and no lines.")
    ok = bool(checks) and all(c["ok"] for c in checks) and not problems
    return {"ok": ok, "checks": checks, "problems": problems,
            "totals": {k: str(v) for k, v in t.items() if isinstance(v, Decimal)}}


# --------------------------------------------------------------------------------------------------- freezing
def canonical_content(baseline: ProjectBaseline) -> dict:
    allocs = (ProjectBaselineLabourAllocation.query.filter_by(baseline_id=baseline.id)
              .order_by(ProjectBaselineLabourAllocation.sort_order, ProjectBaselineLabourAllocation.task_name,
                        ProjectBaselineLabourAllocation.person_id).all())
    rates = ProjectBaselinePersonRate.query.filter_by(baseline_id=baseline.id).order_by(
        ProjectBaselinePersonRate.person_id).all()
    lines = ProjectBaselineLine.query.filter_by(baseline_id=baseline.id).order_by(
        ProjectBaselineLine.sort_order, ProjectBaselineLine.id).all()
    items = ProjectBaselineOpenItem.query.filter_by(baseline_id=baseline.id).order_by(ProjectBaselineOpenItem.id).all()

    def d(value):
        return None if value is None else str(Decimal(str(value)))

    return {
        "project_id": baseline.project_id, "estimate_id": baseline.estimate_id,
        "estimate_version_id": baseline.estimate_version_id, "estimate_approval_id": baseline.estimate_approval_id,
        "option_label": baseline.option_label, "labour_selling_rate": d(baseline.labour_selling_rate),
        "pricing_basis": baseline.pricing_basis,
        "allocations": [[a.group_name, a.task_name, a.sort_order, a.person_id, d(a.hours)] for a in allocs],
        "person_rates": [[r.person_id, r.cost_profile_id, d(r.loaded_rate)] for r in rates],
        "lines": [[l.category, l.source_ref, l.supplier_name, l.sku, l.description, d(l.quantity), l.uom,
                   d(l.list_unit_price), d(l.discount_amount), d(l.net_cost), d(l.markup_rate), d(l.selling_price),
                   l.price_override_reason, bool(l.is_provisional), l.provisional_reason, l.sort_order]
                  for l in lines],
        "open_items": [[i.description, i.status, i.resolution_note] for i in items],
    }


def content_sha256(baseline: ProjectBaseline) -> str:
    blob = json.dumps(canonical_content(baseline), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("ascii")).hexdigest()


def verify(baseline: ProjectBaseline) -> bool:
    return bool(baseline.content_sha256) and baseline.content_sha256 == content_sha256(baseline)


def freeze(baseline: ProjectBaseline, *, actor, source: Optional[dict] = None) -> ProjectBaseline:
    _require_admin(actor, baseline.organization_id)
    _provisional(baseline)
    open_items = ProjectBaselineOpenItem.query.filter_by(baseline_id=baseline.id, status="OPEN").count()
    if open_items:
        raise BaselineError(f"This baseline has {open_items} open item(s). Resolve them before freezing.")
    if ProjectBaselineLine.query.filter_by(baseline_id=baseline.id, is_provisional=True).count():
        raise BaselineError("This baseline still has provisional lines. Replace them with confirmed figures first.")
    report = reconcile(baseline, source)
    if not report["ok"]:
        reasons = report["problems"] + [f"{c['label']} differs by {c['difference']}" for c in report["checks"]
                                        if not c["ok"]]
        raise BaselineError("The baseline does not reconcile to the approved figures, so it cannot be frozen: "
                            + " ".join(reasons))
    now = datetime.utcnow()
    prior = ProjectBaseline.query.filter_by(project_id=baseline.project_id, status="FROZEN").first()
    sha = content_sha256(baseline)
    try:
        if prior is not None:
            prior.status = "SUPERSEDED"
            db.session.flush()
        baseline.content_sha256 = sha
        baseline.reconciliation_json = json.dumps(
            {"source": {k: str(_money(v)) for k, v in (source if source is not None
                                                      else approved_source_totals(baseline)).items()},
             "checks": report["checks"], "totals": report["totals"], "frozen_by_user_id": actor.id,
             "frozen_at": now.isoformat(timespec="seconds"), "supersedes_baseline_id": prior.id if prior else None},
            sort_keys=True)
        baseline.frozen_at, baseline.frozen_by_user_id = now, actor.id
        baseline.status = "FROZEN"
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return baseline


# ------------------------------------------------------------------------------------------------ presentation
def view(baseline: ProjectBaseline, *, include_rates: bool = False) -> dict:
    """What the page shows. The allocation schedule carries hours and assignments only. Financial summaries order
    Revenue, Cost, Profit, Profit Margin. Loaded rates appear only when asked for (owner-only page)."""
    t = totals(baseline)
    people = {p.id: p.full_name for p in OrganizationPerson.query.filter(
        OrganizationPerson.id.in_({a.person_id for a in baseline.allocations})).all()}
    schedule, current = [], None
    for a in baseline.allocations.order_by(ProjectBaselineLabourAllocation.sort_order,
                                           ProjectBaselineLabourAllocation.person_id):
        if current is None or current["task"] != a.task_name:
            current = {"group": a.group_name, "task": a.task_name, "people": [], "total": ZERO}
            schedule.append(current)
        current["people"].append({"name": people.get(a.person_id, "?"), "hours": Decimal(str(a.hours))})
        current["total"] += Decimal(str(a.hours))
    summary = [("Revenue", t["revenue"]), ("Cost", t["cost"]), ("Profit", t["profit"]),
               ("Profit Margin", t["profit_margin"])]
    data = {"schedule": schedule, "summary": summary, "totals": t,
            "lines": baseline.lines.order_by(ProjectBaselineLine.sort_order, ProjectBaselineLine.id).all(),
            "open_items": baseline.open_items.order_by(ProjectBaselineOpenItem.id).all(),
            "reconciliation": reconcile(baseline) if baseline.status == "PROVISIONAL" else
            json.loads(baseline.reconciliation_json or "{}"),
            "sha_verified": verify(baseline) if baseline.status != "PROVISIONAL" else None}
    if include_rates:
        data["person_rates"] = [(people.get(r.person_id, "?"), Decimal(str(r.loaded_rate)))
                                for r in baseline.person_rates]
    return data
