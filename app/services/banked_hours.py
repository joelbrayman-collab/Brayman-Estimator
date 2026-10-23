"""Banked hours under the company's own hours policy (Joel, 22 Oct 2026).

Nothing is hard-coded. The owner enters the policy (Getting Started → "Hours and banked time", later
Company → Hours policy): the normal work week, the weekly hours after which extra hours are banked (or paid
as overtime), the bank rate, whether shop / company work counts, and the week's first day. Until a policy is
saved nothing accrues. Each saved change is a new version with who, when, old → new and an effective date;
a version governs the weeks whose first day is on or after its effective date, so earlier weeks keep the
rules they were earned under.

The ledger is append-only. Approved time (FG-035) is the only source of worked hours: when time is approved
or an approved entry is corrected, the week is worked out again and only the difference is added as a new
EARNED row. Time off taken and management adjustments are their own rows with a reason. Hours only: no
wage, rate or money is read or shown here.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import func

from app import db
from app.models.payroll_time import (
    BANKED_KIND_ADJUSTMENT,
    BANKED_KIND_EARNED,
    BANKED_KIND_USED,
    EXTRA_HOURS_BANK,
    EXTRA_HOURS_PAY,
    EXTRA_HOURS_TREATMENTS,
    BankedHoursLedgerEntry,
    BankedHoursPolicy,
)
from app.models.time_entry import TIME_STATUS_APPROVED, LabourTimeEntry
from app.models.user import User, UserMembership

Q = Decimal("0.01")
DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
POLICY_FIELDS = (
    ("normal_week_hours", "Normal work week (hours)"),
    ("extra_after_hours", "Extra hours start after (hours in a week)"),
    ("extra_hours_treatment", "Extra hours are"),
    ("bank_rate", "Banked hours for each extra hour"),
    ("counts_company_time", "Shop / company work counts"),
    ("week_start_day", "Week starts on"),
    ("effective_from", "Effective from"),
)
TREATMENT_LABELS = {EXTRA_HOURS_BANK: "banked", EXTRA_HOURS_PAY: "paid as overtime (not banked)"}


class BankedHoursError(ValueError):
    pass


def _q(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Q, rounding=ROUND_HALF_UP)


def _actor_name(user) -> str:
    return ((getattr(user, "display_name", None) or getattr(user, "email", None) or "Office").strip())[:150]


# ------------------------------------------------------------------ policy


def policy_versions(organization_id: str):
    return (BankedHoursPolicy.query.filter_by(organization_id=organization_id)
            .order_by(BankedHoursPolicy.version.desc()).all())


def latest_policy(organization_id: str) -> Optional[BankedHoursPolicy]:
    return (BankedHoursPolicy.query.filter_by(organization_id=organization_id)
            .order_by(BankedHoursPolicy.version.desc()).first())


def policy_in_force(organization_id: str, on: date) -> Optional[BankedHoursPolicy]:
    """The newest version whose effective date is on or before ``on``."""
    return (BankedHoursPolicy.query.filter(BankedHoursPolicy.organization_id == organization_id,
                                           BankedHoursPolicy.effective_from <= on)
            .order_by(BankedHoursPolicy.effective_from.desc(), BankedHoursPolicy.version.desc()).first())


def week_start_for(day: date, week_start_day: int) -> date:
    return day - timedelta(days=(day.weekday() - int(week_start_day)) % 7)


def policy_for_week_containing(organization_id: str, day: date):
    """(policy, week_start) governing the week that contains ``day``; (None, None) before any policy.

    The week's boundaries come from the version in force on ``day``; that week is then governed by the
    version in force on its first day (a change takes effect from the first full week on or after it)."""
    probe = policy_in_force(organization_id, day)
    if probe is None:
        return None, None
    start = week_start_for(day, probe.week_start_day)
    governing = policy_in_force(organization_id, start)
    if governing is None:
        return None, start
    return governing, week_start_for(day, governing.week_start_day)


def _decimal_field(raw, label, *, allow_zero=False, maximum=Decimal("168")) -> Decimal:
    text = (str(raw) if raw is not None else "").strip()
    if not text:
        raise BankedHoursError(f"Enter {label.lower()}.")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        raise BankedHoursError(f"Enter a number for {label.lower()}.")
    if value < 0 or (value == 0 and not allow_zero) or value > maximum:
        raise BankedHoursError(f"Check {label.lower()}.")
    return value


def parse_policy_form(form, *, today: Optional[date] = None, current: Optional[BankedHoursPolicy] = None) -> dict:
    """Every value must be entered by the owner: no defaults are filled in."""
    today = today or date.today()
    normal = _decimal_field(form.get("normal_week_hours"), "the normal work week (hours)")
    after = _decimal_field(form.get("extra_after_hours"), "the weekly hours after which extra hours start")
    if after < normal:
        raise BankedHoursError("Extra hours cannot start before the normal work week is complete.")
    treatment = (form.get("extra_hours_treatment") or "").strip().upper()
    if treatment not in EXTRA_HOURS_TREATMENTS:
        raise BankedHoursError("Choose whether extra hours are banked or paid as overtime.")
    if treatment == EXTRA_HOURS_BANK:
        rate = _decimal_field(form.get("bank_rate"), "the banked hours for each extra hour", maximum=Decimal("5"))
    else:
        raw_rate = (form.get("bank_rate") or "").strip()
        rate = _decimal_field(raw_rate, "the banked hours for each extra hour", allow_zero=True,
                              maximum=Decimal("5")) if raw_rate else Decimal("0")
    counts = (form.get("counts_company_time") or "").strip().lower()
    if counts not in ("yes", "no"):
        raise BankedHoursError("Say whether shop / company work counts toward the week.")
    day_raw = (form.get("week_start_day") or "").strip()
    if day_raw not in {str(i) for i in range(7)}:
        raise BankedHoursError("Choose the day the work week starts.")
    day = int(day_raw)
    eff_raw = (form.get("effective_from") or "").strip()
    if not eff_raw:
        raise BankedHoursError("Enter the date this policy takes effect.")
    try:
        effective = date.fromisoformat(eff_raw)
    except ValueError:
        raise BankedHoursError("Enter a valid effective date.")
    earliest = week_start_for(today, day)
    if effective < earliest:
        raise BankedHoursError(
            f"The effective date cannot be before {earliest.strftime('%a %b %d, %Y')} (the start of this week): "
            "earlier weeks keep the rules they were worked under.")
    if current is not None and effective < current.effective_from:
        raise BankedHoursError("The effective date cannot be before the current policy's effective date.")
    return {"normal_week_hours": normal.quantize(Q), "extra_after_hours": after.quantize(Q),
            "extra_hours_treatment": treatment, "bank_rate": rate.quantize(Decimal("0.001")),
            "counts_company_time": counts == "yes", "week_start_day": day, "effective_from": effective,
            "change_note": " ".join((form.get("change_note") or "").split())[:500] or None}


def _display(field: str, value) -> str:
    if value is None:
        return ""
    if field == "extra_hours_treatment":
        return TREATMENT_LABELS.get(value, value)
    if field == "counts_company_time":
        return "yes" if value else "no"
    if field == "week_start_day":
        return DAY_NAMES[int(value)]
    if field == "effective_from":
        return value.strftime("%b %d, %Y")
    if field == "bank_rate":
        return f"{Decimal(str(value)).normalize():f}"
    return f"{_q(value)}"


def save_policy(organization_id: str, user, form, *, today: Optional[date] = None) -> BankedHoursPolicy:
    current = latest_policy(organization_id)
    values = parse_policy_form(form, today=today, current=current)
    changes = []
    for field, _label in POLICY_FIELDS:
        old = getattr(current, field) if current is not None else None
        new = values[field]
        if current is None or _display(field, old) != _display(field, new):
            changes.append({"field": field, "old": _display(field, old) if current is not None else "",
                            "new": _display(field, new)})
    if current is not None and not [c for c in changes if c["field"] != "effective_from"]:
        raise BankedHoursError("Nothing changed.")
    row = BankedHoursPolicy(organization_id=organization_id, version=(current.version + 1) if current else 1,
                            changes_json=changes, recorded_by_user_id=getattr(user, "id", None),
                            recorded_by_name=_actor_name(user), recorded_at=datetime.utcnow(), **values)
    db.session.add(row)
    db.session.flush()
    # Weeks on or after the effective date that already have approved time are worked out under the new
    # version (difference rows only). Earlier weeks are not touched.
    for user_id in _workers_with_time_since(organization_id, row.effective_from):
        recalculate_from(organization_id, user_id, row.effective_from, actor=user,
                         reason=f"Hours policy version {row.version} in effect")
    db.session.commit()
    return row


def policy_summary(policy: Optional[BankedHoursPolicy]) -> str:
    """The configured policy in plain words, for every screen that shows a balance."""
    if policy is None:
        return "No hours policy has been entered yet, so no hours are banked."
    week = f"{DAY_NAMES[policy.week_start_day]} to {DAY_NAMES[(policy.week_start_day + 6) % 7]}"
    text = (f"Normal work week: {_q(policy.normal_week_hours)} hours ({week}). "
            f"Hours after {_q(policy.extra_after_hours)} in a week are ")
    if policy.extra_hours_treatment == EXTRA_HOURS_BANK:
        text += f"banked: {_display('bank_rate', policy.bank_rate)} banked hour for each extra hour. "
    else:
        text += "paid as overtime, not banked. "
    text += "Shop / Company Work counts." if policy.counts_company_time else "Shop / Company Work does not count."
    return text


# ------------------------------------------------------------------ worked hours and earning


def _company_project_id(organization_id: str):
    from app.services.time_entry import get_company_time_project

    project = get_company_time_project(organization_id)
    return project.id if project is not None else None


def worked_hours(organization_id: str, user_id: int, week_start: date, policy: BankedHoursPolicy) -> Decimal:
    query = LabourTimeEntry.query.filter(
        LabourTimeEntry.organization_id == organization_id,
        LabourTimeEntry.worker_user_id == user_id,
        LabourTimeEntry.status == TIME_STATUS_APPROVED,
        LabourTimeEntry.work_date >= week_start,
        LabourTimeEntry.work_date <= week_start + timedelta(days=6),
    )
    if not policy.counts_company_time:
        company_id = _company_project_id(organization_id)
        if company_id is not None:
            query = query.filter(LabourTimeEntry.project_id != company_id)
    total = query.with_entities(func.coalesce(func.sum(LabourTimeEntry.hours), 0)).scalar()
    return _q(total)


def week_figures(organization_id: str, user_id: int, week_start: date, policy: BankedHoursPolicy) -> dict:
    worked = worked_hours(organization_id, user_id, week_start, policy)
    normal = Decimal(str(policy.normal_week_hours))
    after = Decimal(str(policy.extra_after_hours))
    regular = min(worked, normal)
    extra = max(Decimal("0"), worked - after)
    earned = _q(extra * Decimal(str(policy.bank_rate))) if policy.extra_hours_treatment == EXTRA_HOURS_BANK else Decimal("0.00")
    return {"week_start": week_start, "week_end": week_start + timedelta(days=6), "worked": _q(worked),
            "regular": _q(regular), "extra": _q(extra), "earned_target": earned,
            "overtime_paid": _q(extra) if policy.extra_hours_treatment == EXTRA_HOURS_PAY else Decimal("0.00")}


def _earned_so_far(organization_id: str, user_id: int, week_start: date) -> Decimal:
    total = (BankedHoursLedgerEntry.query.filter_by(organization_id=organization_id, user_id=user_id,
                                                    kind=BANKED_KIND_EARNED, week_start=week_start)
             .with_entities(func.coalesce(func.sum(BankedHoursLedgerEntry.hours), 0)).scalar())
    return _q(total)


def recalculate_week(organization_id: str, user_id: int, day: date, *, actor=None, source_entry_id=None,
                     reason: str = "Approved time") -> Optional[BankedHoursLedgerEntry]:
    """Bring the week containing ``day`` up to date. Adds one difference row, or nothing. No commit."""
    policy, week_start = policy_for_week_containing(organization_id, day)
    if policy is None:
        return None
    figures = week_figures(organization_id, user_id, week_start, policy)
    delta = figures["earned_target"] - _earned_so_far(organization_id, user_id, week_start)
    if delta == 0:
        return None
    worker = db.session.get(User, user_id)
    row = BankedHoursLedgerEntry(
        organization_id=organization_id, user_id=user_id,
        worker_display_name=(getattr(worker, "display_name", None) or "Worker")[:150], kind=BANKED_KIND_EARNED,
        hours=delta, week_start=week_start, worked_hours=figures["worked"], regular_hours=figures["regular"],
        extra_hours=figures["extra"], policy_id=policy.id, source_time_entry_id=source_entry_id,
        reason=reason[:500], actor_user_id=getattr(actor, "id", None),
        actor_name=_actor_name(actor) if actor is not None else "CalibraytAI", created_at=datetime.utcnow())
    db.session.add(row)
    return row


def recalculate_from(organization_id: str, user_id: int, start: date, *, actor=None, reason: str):
    """Every week from ``start`` to today that has approved time. Difference rows only. No commit."""
    days = sorted({row[0] for row in db.session.query(LabourTimeEntry.work_date).filter(
        LabourTimeEntry.organization_id == organization_id, LabourTimeEntry.worker_user_id == user_id,
        LabourTimeEntry.work_date >= start).distinct().all()})
    seen = set()
    for day in days:
        _policy, week_start = policy_for_week_containing(organization_id, day)
        if week_start is None or week_start in seen:
            continue
        seen.add(week_start)
        recalculate_week(organization_id, user_id, day, actor=actor, reason=reason)


def _workers_with_time_since(organization_id: str, start: date):
    return sorted({row[0] for row in db.session.query(LabourTimeEntry.worker_user_id).filter(
        LabourTimeEntry.organization_id == organization_id, LabourTimeEntry.work_date >= start).distinct().all()})


def after_time_approved(entry, *, actor=None, previous_entry=None) -> None:
    """Called inside the approval / correction transaction (no commit)."""
    reason = "Approved time" if previous_entry is None else "Approved time corrected"
    recalculate_week(entry.organization_id, entry.worker_user_id, entry.work_date, actor=actor,
                     source_entry_id=entry.id, reason=reason)
    if previous_entry is not None and previous_entry.work_date != entry.work_date:
        recalculate_week(entry.organization_id, entry.worker_user_id, previous_entry.work_date, actor=actor,
                         source_entry_id=entry.id, reason=reason)


# ------------------------------------------------------------------ balances, time off, adjustments


def balance(organization_id: str, user_id: int) -> Decimal:
    total = (BankedHoursLedgerEntry.query.filter_by(organization_id=organization_id, user_id=user_id)
             .with_entities(func.coalesce(func.sum(BankedHoursLedgerEntry.hours), 0)).scalar())
    return _q(total)


def ledger(organization_id: str, user_id: int, limit: int = 200):
    return (BankedHoursLedgerEntry.query.filter_by(organization_id=organization_id, user_id=user_id)
            .order_by(BankedHoursLedgerEntry.id.desc()).limit(limit).all())


def _require_member(organization_id: str, user_id: int) -> User:
    worker = db.session.get(User, int(user_id))
    if worker is None or UserMembership.query.filter_by(user_id=worker.id, organization_id=organization_id).first() is None:
        raise BankedHoursError("Worker not found.")
    return worker


def _require_manager(organization_id: str, actor, worker: User):
    from app.services.access_domains import has_office_financial_access

    if actor is None or not has_office_financial_access(actor, organization_id):
        raise BankedHoursError("Only the office can change banked hours.")
    if actor.id == worker.id:
        raise BankedHoursError("You cannot change your own banked hours.")


def record_time_off(organization_id: str, user_id: int, *, hours, on_date, reason, actor) -> BankedHoursLedgerEntry:
    worker = _require_member(organization_id, user_id)
    _require_manager(organization_id, actor, worker)
    amount = _decimal_field(hours, "the hours taken off", maximum=Decimal("200")).quantize(Q)
    try:
        day = on_date if isinstance(on_date, date) else date.fromisoformat((on_date or "").strip())
    except ValueError:
        raise BankedHoursError("Enter the day taken off.")
    note = " ".join((reason or "").split())
    if not note:
        raise BankedHoursError("Say what the time off was for.")
    if amount > balance(organization_id, worker.id):
        raise BankedHoursError(f"{worker.display_name} has only {balance(organization_id, worker.id)} banked hours.")
    policy = policy_in_force(organization_id, day) or latest_policy(organization_id)
    row = BankedHoursLedgerEntry(organization_id=organization_id, user_id=worker.id,
                                 worker_display_name=worker.display_name[:150], kind=BANKED_KIND_USED, hours=-amount,
                                 on_date=day, week_start=week_start_for(day, policy.week_start_day) if policy else None,
                                 policy_id=policy.id if policy else None, reason=note[:500], actor_user_id=actor.id,
                                 actor_name=_actor_name(actor))
    db.session.add(row)
    db.session.commit()
    return row


def adjust(organization_id: str, user_id: int, *, hours, reason, actor) -> BankedHoursLedgerEntry:
    worker = _require_member(organization_id, user_id)
    _require_manager(organization_id, actor, worker)
    text = (str(hours) if hours is not None else "").strip()
    try:
        amount = Decimal(text).quantize(Q)
    except (InvalidOperation, ValueError):
        raise BankedHoursError("Enter the hours to add (for example 2) or remove (for example -2).")
    if amount == 0 or abs(amount) > 200:
        raise BankedHoursError("Enter the hours to add (for example 2) or remove (for example -2).")
    note = " ".join((reason or "").split())
    if not note:
        raise BankedHoursError("Say why the banked hours are being adjusted.")
    if balance(organization_id, worker.id) + amount < 0:
        raise BankedHoursError("That would make the balance less than zero.")
    row = BankedHoursLedgerEntry(organization_id=organization_id, user_id=worker.id,
                                 worker_display_name=worker.display_name[:150], kind=BANKED_KIND_ADJUSTMENT,
                                 hours=amount, reason=note[:500], actor_user_id=actor.id, actor_name=_actor_name(actor))
    db.session.add(row)
    db.session.commit()
    return row


KIND_LABELS = {BANKED_KIND_EARNED: "Earned", BANKED_KIND_USED: "Time off taken", BANKED_KIND_ADJUSTMENT: "Adjustment"}


def worker_summary(organization_id: str, user_id: int, *, today: Optional[date] = None) -> dict:
    """What a worker (and the office) sees: balance, this week, recent movements, the policy in words."""
    today = today or date.today()
    policy, week_start = policy_for_week_containing(organization_id, today)
    shown_policy = policy or latest_policy(organization_id)
    week = week_figures(organization_id, user_id, week_start, policy) if policy is not None else None
    if week is not None:
        week["earned"] = _earned_so_far(organization_id, user_id, week_start)
    used_total = (BankedHoursLedgerEntry.query.filter_by(organization_id=organization_id, user_id=user_id,
                                                         kind=BANKED_KIND_USED)
                  .with_entities(func.coalesce(func.sum(BankedHoursLedgerEntry.hours), 0)).scalar())
    return {"balance": balance(organization_id, user_id), "week": week, "policy": shown_policy,
            "policy_in_force": policy, "policy_text": policy_summary(shown_policy),
            "used_total": _q(-Decimal(str(used_total or 0))), "rows": ledger(organization_id, user_id, limit=50),
            "kind_label": KIND_LABELS, "pending_policy": shown_policy is not None and policy is None}


def organization_balances(organization_id: str):
    rows = (db.session.query(BankedHoursLedgerEntry.user_id, func.sum(BankedHoursLedgerEntry.hours))
            .filter(BankedHoursLedgerEntry.organization_id == organization_id)
            .group_by(BankedHoursLedgerEntry.user_id).all())
    balances = {uid: _q(total) for uid, total in rows}
    from app.services.time_entry import org_time_workers

    out = []
    for worker in org_time_workers(organization_id):
        out.append({"worker": worker, "balance": balances.get(worker.id, Decimal("0.00"))})
    return out


def onboarding_done(organization_id: str, _user=None) -> bool:
    return latest_policy(organization_id) is not None


__all__ = ["BankedHoursError", "EXTRA_HOURS_BANK", "EXTRA_HOURS_PAY"]
