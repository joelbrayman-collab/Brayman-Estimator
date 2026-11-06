"""Employee cost profiles and the Loaded Labour Rate (Joel, 2 Nov 2026).

Every employee of the company has a cost profile; Calibrayt calculates the employee's Loaded Labour Rate (LLR): what
one hour actually worked really costs the company.

Inputs per employee: hourly wage; paid hours a year (2,080); vacation weeks (2) and paid public holidays (9), which
give the working hours (paid hours less vacation and holidays: 1,928 by default); company truck and fuel a month;
the yearly tool allowance (paid as taxable pay); the company RRSP contribution as a percentage of wages; the health &
dental premium a month (not taxable pay: no CPP, EI or WSIB on it); and the WSIB rate per $100 (the company's rate,
which an employee may override).

    wages        = hourly wage x paid hours
    earnings     = wages + tool allowance                    (pensionable and insurable)
    CPP          = 5.95 % x (min(earnings, YMPE) - basic exemption), never below 0
    CPP2         = 4 % x (min(earnings, YAMPE) - YMPE), when earnings are above the YMPE
    EI           = 1.4 x 1.63 % x min(earnings, maximum insurable)
    WSIB         = rate / 100 x earnings
    RRSP         = RRSP % x wages
    annual cost  = wages + CPP + CPP2 + EI + WSIB + RRSP + tool allowance + 12 x (truck + fuel + premium)
    LLR          = annual cost / working hours

Every amount is rounded half-up to the cent once, where it is calculated (the same rule as the pricing engine).
Statutory rates come from ``payroll_statutory`` for the profile's year. A profile is never edited: a change is a new
profile (the history is kept), like the wage events.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import List, Optional

from app.services.payroll_statutory import CURRENT_YEAR, rates

CENT = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")
WEEKS_PER_YEAR = Decimal("52")
DAYS_PER_WEEK = Decimal("5")

DEFAULTS = {
    "paid_hours_per_year": Decimal("2080"),
    "vacation_weeks": Decimal("2"),
    "paid_holidays": Decimal("9"),
    "truck_monthly": ZERO,
    "fuel_monthly": ZERO,
    "tool_allowance_annual": ZERO,
    "rrsp_percent": ZERO,
    "health_premium_monthly": ZERO,
}


class CostProfileError(ValueError):
    """A plain-language refusal shown to the person."""


def q(value) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _money(value) -> str:
    return f"${q(value):,.2f}"


def _num(value, *, name, minimum=ZERO, maximum=None, allow_blank_default=None) -> Decimal:
    text = ("" if value is None else str(value)).strip().replace("$", "").replace(",", "").replace("%", "")
    if text == "":
        if allow_blank_default is not None:
            return allow_blank_default
        raise CostProfileError(f"{name} is required.")
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise CostProfileError(f"{name} must be a number (you entered “{value}”).") from None
    if not number.is_finite() or number < minimum:
        raise CostProfileError(f"{name} cannot be less than {minimum}.")
    if maximum is not None and number > maximum:
        raise CostProfileError(f"{name} cannot be more than {maximum}.")
    return number


@dataclass(frozen=True)
class CostInputs:
    hourly_wage: Decimal
    paid_hours_per_year: Decimal = DEFAULTS["paid_hours_per_year"]
    vacation_weeks: Decimal = DEFAULTS["vacation_weeks"]
    paid_holidays: Decimal = DEFAULTS["paid_holidays"]
    truck_monthly: Decimal = ZERO
    fuel_monthly: Decimal = ZERO
    tool_allowance_annual: Decimal = ZERO
    rrsp_percent: Decimal = ZERO  # a percentage: 2 is 2 %
    health_premium_monthly: Decimal = ZERO
    wsib_rate_per_100: Decimal = Decimal("3.55")
    statutory_year: int = CURRENT_YEAR


def parse_inputs(form: dict, *, company_wsib: Decimal, year: int = CURRENT_YEAR) -> CostInputs:
    """Read a submitted form (strings). Blank optional amounts are 0; blank hours use the defaults."""
    wage = _num(form.get("hourly_wage"), name="Hourly wage", minimum=Decimal("0.01"), maximum=Decimal("1000"))
    paid = _num(form.get("paid_hours_per_year"), name="Paid hours a year", minimum=Decimal("1"),
                maximum=Decimal("8784"), allow_blank_default=DEFAULTS["paid_hours_per_year"])
    override = (form.get("wsib_rate_per_100") or "").strip()
    inputs = CostInputs(
        hourly_wage=q(wage),
        paid_hours_per_year=paid,
        vacation_weeks=_num(form.get("vacation_weeks"), name="Vacation weeks", maximum=Decimal("52"),
                            allow_blank_default=DEFAULTS["vacation_weeks"]),
        paid_holidays=_num(form.get("paid_holidays"), name="Paid public holidays", maximum=Decimal("60"),
                           allow_blank_default=DEFAULTS["paid_holidays"]),
        truck_monthly=q(_num(form.get("truck_monthly"), name="Company truck a month", allow_blank_default=ZERO)),
        fuel_monthly=q(_num(form.get("fuel_monthly"), name="Fuel a month", allow_blank_default=ZERO)),
        tool_allowance_annual=q(_num(form.get("tool_allowance_annual"), name="Tool allowance a year",
                                     allow_blank_default=ZERO)),
        rrsp_percent=_num(form.get("rrsp_percent"), name="Company RRSP", maximum=HUNDRED, allow_blank_default=ZERO),
        health_premium_monthly=q(_num(form.get("health_premium_monthly"), name="Health & dental premium a month",
                                      allow_blank_default=ZERO)),
        wsib_rate_per_100=_num(override, name="WSIB rate per $100", maximum=HUNDRED) if override else company_wsib,
        statutory_year=year,
    )
    if working_hours(inputs) <= 0:
        raise CostProfileError("Vacation and holidays leave no working hours. Check the hours.")
    return inputs


def working_hours(inputs: CostInputs) -> Decimal:
    per_week = inputs.paid_hours_per_year / WEEKS_PER_YEAR
    per_day = per_week / DAYS_PER_WEEK
    return inputs.paid_hours_per_year - inputs.vacation_weeks * per_week - inputs.paid_holidays * per_day


def calculate(inputs: CostInputs) -> dict:
    """The loaded cost of one employee for a year, line by line, with the LLR. Pure function."""
    r = rates(inputs.statutory_year)
    wages = q(inputs.hourly_wage * inputs.paid_hours_per_year)
    tools = q(inputs.tool_allowance_annual)
    earnings = wages + tools  # pensionable and insurable: wages plus the taxable tool allowance
    cpp = q(max(ZERO, r["cpp_rate"] * (min(earnings, r["cpp_ympe"]) - r["cpp_basic_exemption"])))
    cpp2 = q(r["cpp2_rate"] * (min(earnings, r["cpp2_yampe"]) - r["cpp_ympe"])) if earnings > r["cpp_ympe"] else ZERO
    ei = q(r["ei_employer_multiplier"] * r["ei_employee_rate"] * min(earnings, r["ei_max_insurable"]))
    wsib = q(inputs.wsib_rate_per_100 / HUNDRED * earnings)
    rrsp = q(inputs.rrsp_percent / HUNDRED * wages)
    truck = q(inputs.truck_monthly * 12)
    fuel = q(inputs.fuel_monthly * 12)
    premium = q(inputs.health_premium_monthly * 12)
    eht = q(r["ontario_eht_rate"] * earnings)
    work = working_hours(inputs)
    paid = inputs.paid_hours_per_year
    per_week = paid / WEEKS_PER_YEAR
    wage_text = f"${q(inputs.hourly_wage):,.2f} x {paid:,.0f} paid hours"
    if inputs.vacation_weeks or inputs.paid_holidays:
        wage_text += (f" (includes {inputs.vacation_weeks.normalize():f} weeks' vacation and "
                      f"{inputs.paid_holidays.normalize():f} public holidays)")
    rows = [
        ("wages", "Wages", wage_text, wages),
        ("cpp", "CPP (employer)",
         (f"{r['cpp_rate'] * 100:.2f}% of earnings up to ${r['cpp_ympe']:,.0f}, less the "
          f"${r['cpp_basic_exemption']:,.0f} exemption" if earnings >= r["cpp_ympe"] else
          f"{r['cpp_rate'] * 100:.2f}% of earnings, less the ${r['cpp_basic_exemption']:,.0f} exemption "
          f"(below the ${r['cpp_ympe']:,.0f} maximum)"), cpp),
        ("cpp2", "CPP2 (employer)",
         (f"{r['cpp2_rate'] * 100:.0f}% of earnings above ${r['cpp_ympe']:,.0f} (wages + tool allowance)"
          if cpp2 else f"None: earnings below ${r['cpp_ympe']:,.0f}"), cpp2),
        ("ei", "EI (employer)",
         f"{r['ei_employer_multiplier']} x the {r['ei_employee_rate'] * 100:.2f}% employee rate, "
         + (f"on insurable earnings up to ${r['ei_max_insurable']:,.0f}" if earnings >= r["ei_max_insurable"]
            else f"on all earnings (below the ${r['ei_max_insurable']:,.0f} maximum)"), ei),
        ("wsib", "WSIB", f"${inputs.wsib_rate_per_100:.2f} per $100 of payroll", wsib),
        ("rrsp", f"RRSP (company {inputs.rrsp_percent.normalize():f}%)" if inputs.rrsp_percent else "RRSP (company)",
         f"{inputs.rrsp_percent.normalize():f}% of wages" if inputs.rrsp_percent else "None", rrsp),
        ("tools", "Tool allowance", f"{_money(tools)} per year, paid as taxable pay" if tools else "None", tools),
        ("truck", "Company truck", f"{_money(inputs.truck_monthly)} per month" if truck else "None", truck),
        ("fuel", "Fuel", f"{_money(inputs.fuel_monthly)} per month" if fuel else "None", fuel),
        ("premium", "Health & dental premium",
         f"{_money(inputs.health_premium_monthly)} per month (no CPP, EI or WSIB on it)" if premium else "None",
         premium),
    ]
    if eht:
        rows.append(("eht", "Ontario Employer Health Tax", "", eht))
    total = sum((row[3] for row in rows), ZERO)
    llr = q(total / work)
    return {
        "statutory_year": inputs.statutory_year,
        "paid_hours": paid,
        "working_hours": work,
        "vacation_hours": inputs.vacation_weeks * per_week,
        "holiday_hours": inputs.paid_holidays * per_week / DAYS_PER_WEEK,
        "earnings": earnings,
        "rows": [{"key": key, "label": label, "basis": basis, "per_year": amount,
                  "per_paid_hour": q(amount / paid), "per_working_hour": q(amount / work)}
                 for key, label, basis, amount in rows],
        "annual_cost": q(total),
        "per_paid_hour": q(total / paid),
        "loaded_rate": llr,
        "wage_per_working_hour": q(wages / work),
    }


def breakdown_json(result: dict) -> str:
    return json.dumps({"rows": [{k: (str(v) if isinstance(v, Decimal) else v) for k, v in row.items()}
                                for row in result["rows"]],
                       "working_hours": str(result["working_hours"]), "paid_hours": str(result["paid_hours"])},
                      sort_keys=True)


# ---------------------------------------------------------------------------------------------- company setting
def company_wsib(organization_id: str) -> dict:
    """The company's WSIB rate per $100 (its newest setting), or the year's default class rate."""
    from app.models.person import OrganizationLabourCostSetting

    row = (OrganizationLabourCostSetting.query.filter_by(organization_id=organization_id)
           .order_by(OrganizationLabourCostSetting.id.desc()).first())
    r = rates(CURRENT_YEAR)
    if row is None:
        return {"rate": r["wsib_default_per_100"], "label": r["wsib_default_class"], "is_default": True, "row": None}
    return {"rate": Decimal(str(row.wsib_rate_per_100)), "label": row.wsib_class_label or "", "is_default": False,
            "row": row}


def set_company_wsib(organization_id: str, *, rate, label: str, actor_user) -> object:
    from app import db
    from app.models.person import OrganizationLabourCostSetting

    value = _num(rate, name="WSIB rate per $100", maximum=HUNDRED)
    row = OrganizationLabourCostSetting(organization_id=organization_id, wsib_rate_per_100=value,
                                        wsib_class_label=(label or "").strip()[:120] or None,
                                        created_at=datetime.utcnow(), actor_user_id=actor_user.id,
                                        actor_name=_actor_name(actor_user))
    db.session.add(row)
    db.session.commit()
    return row


def _actor_name(user) -> str:
    return ((getattr(user, "display_name", None) or getattr(user, "email", None) or "Unknown").strip())[:150]


# ---------------------------------------------------------------------------------------------- profiles
def current_profile(person_id: int):
    from app.models.person import OrganizationPersonCostProfile

    return (OrganizationPersonCostProfile.query.filter_by(person_id=person_id)
            .order_by(OrganizationPersonCostProfile.id.desc()).first())


def profile_history(person_id: int) -> list:
    from app.models.person import OrganizationPersonCostProfile

    return (OrganizationPersonCostProfile.query.filter_by(person_id=person_id)
            .order_by(OrganizationPersonCostProfile.id.desc()).all())


def is_complete(profile, person=None) -> bool:
    """Complete: a saved profile exists and its wage is the employee's current wage."""
    if profile is None:
        return False
    if person is not None and Decimal(str(person.hourly_wage)).quantize(CENT) != Decimal(
            str(profile.hourly_wage)).quantize(CENT):
        return False
    return profile.loaded_rate is not None and Decimal(str(profile.loaded_rate)) > 0


def inputs_of(profile) -> CostInputs:
    return CostInputs(
        hourly_wage=Decimal(str(profile.hourly_wage)), paid_hours_per_year=Decimal(str(profile.paid_hours_per_year)),
        vacation_weeks=Decimal(str(profile.vacation_weeks)), paid_holidays=Decimal(str(profile.paid_holidays)),
        truck_monthly=Decimal(str(profile.truck_monthly)), fuel_monthly=Decimal(str(profile.fuel_monthly)),
        tool_allowance_annual=Decimal(str(profile.tool_allowance_annual)),
        rrsp_percent=Decimal(str(profile.rrsp_percent)),
        health_premium_monthly=Decimal(str(profile.health_premium_monthly)),
        wsib_rate_per_100=Decimal(str(profile.wsib_rate_per_100)), statutory_year=int(profile.statutory_year))


def save_profile(person, inputs: CostInputs, *, actor_user, wsib_override: bool, reason: str = ""):
    """Append a new cost profile (and, when the wage changed, the wage and an append-only wage event)."""
    from app import db
    from app.models.person import OrganizationPersonCostProfile, OrganizationPersonWageEvent

    result = calculate(inputs)
    now = datetime.utcnow()
    previous_wage = Decimal(str(person.hourly_wage)).quantize(CENT)
    if previous_wage != inputs.hourly_wage:
        db.session.add(OrganizationPersonWageEvent(organization_id=person.organization_id, person_id=person.id,
                                                   previous_hourly_wage=previous_wage,
                                                   hourly_wage=inputs.hourly_wage, created_at=now,
                                                   actor_user_id=actor_user.id))
        person.hourly_wage = inputs.hourly_wage
        person.updated_at = now
        person.updated_by_user_id = actor_user.id
    profile = OrganizationPersonCostProfile(
        organization_id=person.organization_id, person_id=person.id, hourly_wage=inputs.hourly_wage,
        paid_hours_per_year=inputs.paid_hours_per_year, vacation_weeks=inputs.vacation_weeks,
        paid_holidays=inputs.paid_holidays, truck_monthly=inputs.truck_monthly, fuel_monthly=inputs.fuel_monthly,
        tool_allowance_annual=inputs.tool_allowance_annual, rrsp_percent=inputs.rrsp_percent,
        health_premium_monthly=inputs.health_premium_monthly, wsib_rate_per_100=inputs.wsib_rate_per_100,
        wsib_is_override=bool(wsib_override), statutory_year=inputs.statutory_year,
        working_hours=result["working_hours"].quantize(CENT), annual_cost=result["annual_cost"],
        loaded_rate=result["loaded_rate"], breakdown_json=breakdown_json(result),
        reason=(reason or "").strip()[:300] or None, created_at=now, actor_user_id=actor_user.id,
        actor_name=_actor_name(actor_user))
    db.session.add(profile)
    db.session.commit()
    return profile, result


def employees(organization_id: str) -> List[dict]:
    """Every employee of the company with their cost-profile state (active first, then by name)."""
    from app.models.person import OrganizationPerson

    out = []
    for person in OrganizationPerson.query.filter_by(organization_id=organization_id).all():
        profile = current_profile(person.id)
        out.append({"person": person, "profile": profile, "complete": is_complete(profile, person),
                    "loaded_rate": Decimal(str(profile.loaded_rate)) if profile is not None else None})
    out.sort(key=lambda row: (not row["person"].is_active, row["person"].full_name.lower()))
    return out


def assignable_employees(organization_id: str) -> List[dict]:
    """Active employees with a complete cost profile: the only ones that may be put on an estimate crew."""
    return [row for row in employees(organization_id) if row["person"].is_active and row["complete"]]


def loaded_rate_for(person) -> Optional[Decimal]:
    profile = current_profile(person.id)
    if not is_complete(profile, person):
        return None
    return Decimal(str(profile.loaded_rate)).quantize(CENT)
