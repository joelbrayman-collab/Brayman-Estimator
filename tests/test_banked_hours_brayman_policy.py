"""Brayman Construction's approved banked-hours policy (Ben, confirmed 25 Oct 2026). Synthetic data only.

40-hour week; every hour over 40 in a week is banked at 1 hour for 1 hour; banked, never also paid as
overtime. Checked with 40-, 45- and 50-hour weeks, the weekly reset, the balance carried forward, approved
use of banked time, what the worker sees, and the audit trail. The policy itself is entered by the owner on
the existing Hours policy screen (these are its form fields), no code default.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from app.models.payroll_time import BankedHoursLedgerEntry, BankedHoursPolicy
from app.services import banked_hours as banked
from app.services.local_time import local_today
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.time_entry import approve_time, submit_time
from tests.test_field_time_labour_2026_10_22 import BEN, KEVIN, _client, _setup
from tests.test_work_time_fg035 import app  # noqa: F401

TODAY = local_today()
THIS_MONDAY = TODAY - timedelta(days=TODAY.weekday())
WEEK_40 = THIS_MONDAY - timedelta(days=21)
WEEK_45 = THIS_MONDAY - timedelta(days=14)
WEEK_50 = THIS_MONDAY - timedelta(days=7)

# Exactly what the owner enters on Company → Hours policy.
BRAYMAN_POLICY = {"normal_week_hours": "40", "extra_after_hours": "40", "extra_hours_treatment": "BANK",
                  "bank_rate": "1", "counts_company_time": "yes", "week_start_day": "0",
                  "effective_from": WEEK_40.isoformat(), "change_note": "Brayman policy confirmed by Ben"}


def _week(project, activity, kevin, ben, monday, hours_per_day):
    for day in range(5):  # Monday to Friday
        entry = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours=hours_per_day,
                            work_date=monday + timedelta(days=day), worker_user_id=kevin.id)
        approve_time(time_entry_id=entry.id, reviewer_user_id=ben.id)


@pytest.fixture
def brayman(app):
    ben, kevin, project, activity = _setup()
    policy = banked.save_policy(ORG, ben, BRAYMAN_POLICY, today=WEEK_40)
    return ben, kevin, project, activity, policy


def test_the_policy_is_saved_as_entered_with_who_and_when(brayman):
    ben, _kevin, _p, _a, policy = brayman
    assert (policy.normal_week_hours, policy.extra_after_hours, policy.extra_hours_treatment, policy.bank_rate,
            policy.week_start_day) == (Decimal("40.00"), Decimal("40.00"), "BANK", Decimal("1.00"), 0)
    assert policy.version == 1 and BankedHoursPolicy.query.count() == 1
    text = banked.policy_summary(policy)
    assert "40" in text and "banked" in text and "paid as overtime" not in text


def test_40_45_and_50_hour_weeks_and_the_weekly_reset(brayman):
    ben, kevin, project, activity, policy = brayman
    expected = []
    for monday, per_day, worked, banked_hours in ((WEEK_40, "8", "40", "0"), (WEEK_45, "9", "45", "5"),
                                                  (WEEK_50, "10", "50", "10")):
        _week(project, activity, kevin, ben, monday, per_day)
        f = banked.week_figures(ORG, kevin.id, monday, policy)
        # Paid regular hours stop at 40; the extra is banked and nothing is paid as overtime.
        assert f["worked"] == Decimal(worked) and f["regular"] == Decimal("40.00")
        assert f["extra"] == Decimal(banked_hours) and f["earned_target"] == Decimal(banked_hours)
        assert f["overtime_paid"] == Decimal("0.00")
        assert f["regular"] + f["earned_target"] == f["worked"]  # each hour is paid OR banked, never both
        expected.append(Decimal(banked_hours))
    # Weekly reset: each week is measured on its own Monday-to-Sunday hours (no carry-over of the 40).
    earned = [sum(r.hours for r in BankedHoursLedgerEntry.query.filter_by(user_id=kevin.id, kind="EARNED",
                                                                       week_start=m))
              for m in (WEEK_40, WEEK_45, WEEK_50)]
    assert earned == expected == [Decimal("0"), Decimal("5"), Decimal("10")]
    # Balance carries forward across weeks.
    assert banked.balance(ORG, kevin.id) == Decimal("15.00")


def test_approved_use_carries_the_remaining_balance_forward_and_is_audited(app, brayman):
    ben, kevin, project, activity, _policy = brayman
    _week(project, activity, kevin, ben, WEEK_45, "9")
    _week(project, activity, kevin, ben, WEEK_50, "10")
    office = _client(app, BEN)
    r = office.post(f"/time/banked-hours/{kevin.id}/time-off",
                    data={"hours": "16", "on_date": TODAY.isoformat(), "reason": "Too much"}, follow_redirects=True)
    assert "only 15.00 banked hours" in r.get_data(as_text=True)  # cannot use more than is banked
    office.post(f"/time/banked-hours/{kevin.id}/time-off",
                data={"hours": "8", "on_date": TODAY.isoformat(), "reason": "Friday off (approved)"})
    summary = banked.worker_summary(ORG, kevin.id)
    assert (summary["earned_total"], summary["used_total"], summary["balance"]) == (
        Decimal("15.00"), Decimal("8.00"), Decimal("7.00"))
    used = BankedHoursLedgerEntry.query.filter_by(user_id=kevin.id, kind="USED").one()
    assert used.hours == Decimal("-8.00") and used.reason == "Friday off (approved)" and used.actor_user_id == ben.id
    # Kevin sees earned, used and remaining on his phone, and no pay or rates.
    page = _client(app, KEVIN).get("/field/banked-hours").get_data(as_text=True)
    assert "Earned 15.00 · Used 8.00 · Remaining 7.00 hours" in page
    assert "$" not in page.split("data-banked-totals", 1)[1].split("</p>", 1)[0]


def test_a_correction_adds_a_difference_row_and_never_rewrites_the_audit_trail(brayman):
    from app.models.time_entry import LabourTimeEntry
    from app.services.time_entry import correct_approved_time

    ben, kevin, project, activity, _policy = brayman
    _week(project, activity, kevin, ben, WEEK_50, "10")
    before = [(r.id, r.hours) for r in BankedHoursLedgerEntry.query.order_by(BankedHoursLedgerEntry.id)]
    friday = LabourTimeEntry.query.filter_by(worker_user_id=kevin.id, work_date=WEEK_50 + timedelta(days=4)).one()
    correct_approved_time(time_entry_id=friday.id, hours="7", reason="Left early", reviewer_user_id=ben.id)
    after = [(r.id, r.hours) for r in BankedHoursLedgerEntry.query.order_by(BankedHoursLedgerEntry.id)]
    assert after[:len(before)] == before and after[-1][1] == Decimal("-3.00")
    assert banked.balance(ORG, kevin.id) == Decimal("7.00")  # 47 worked: 40 regular, 7 banked
