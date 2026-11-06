"""Employer statutory payroll rates, versioned by year (Joel, 2 Nov 2026: employee cost profiles).

One place for the employer's share of CPP, CPP2 and EI, the default WSIB rate and Ontario Employer Health Tax. A new
year is a new entry; a cost profile records the year it was calculated with, so last year's figures never change when
this year's rates are added. Amounts are dollars; rates are fractions (0.0595 is 5.95 %).

Sources (2026):
* CPP / CPP2: Canada Revenue Agency, "CPP contribution rates, maximums and exemptions" (2026): employer rate 5.95 % on
  pensionable earnings up to the YMPE $74,600 less the $3,500 basic exemption; CPP2 employer rate 4 % on earnings
  between the YMPE $74,600 and the YAMPE $85,000.
* EI: Canada Revenue Agency, "EI premium rates and maximums" (2026): employee rate 1.63 % on insurable earnings up to
  $68,900; the employer pays 1.4 times the employee premium.
* WSIB: wsib.ca 2026 premium rates, rate group G3 (building exterior construction): $3.55 per $100 of insurable
  earnings. A company setting (each company enters its own class rate), with a per-employee override.
* Ontario Employer Health Tax: exempt when total Ontario payroll is under the $1 million exemption, so 0 here.
"""

from __future__ import annotations

from decimal import Decimal

D = Decimal

STATUTORY = {
    2026: {
        "cpp_rate": D("0.0595"),
        "cpp_ympe": D("74600"),
        "cpp_basic_exemption": D("3500"),
        "cpp2_rate": D("0.04"),
        "cpp2_yampe": D("85000"),
        "ei_employee_rate": D("0.0163"),
        "ei_employer_multiplier": D("1.4"),
        "ei_max_insurable": D("68900"),
        "wsib_default_per_100": D("3.55"),
        "wsib_default_class": "G3 (building exterior construction)",
        "ontario_eht_rate": D("0"),
    },
}

CURRENT_YEAR = 2026


class StatutoryYearError(LookupError):
    pass


def rates(year: int = CURRENT_YEAR) -> dict:
    try:
        return STATUTORY[int(year)]
    except (KeyError, TypeError, ValueError):
        raise StatutoryYearError(f"No statutory payroll rates are set for {year}.") from None
