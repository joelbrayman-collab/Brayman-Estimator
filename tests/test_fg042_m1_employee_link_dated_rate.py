"""FG-042 M1 / S2: Person-to-User link, dated loaded rate, other employment cost (Joel, 24 Nov 2026).

Synthetic names only."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal as D

import pytest
import sqlalchemy as sa

from app import create_app, db
from app.models.person import OrganizationPerson, OrganizationPersonCostProfile
from app.services import labour_cost_profile as LCP
from app.services.employee_rates import (
    BASIS_IN_FORCE,
    BASIS_PREDATES_FIRST_PROFILE,
    EmployeeLinkError,
    UserRateBook,
    link_person_to_user,
    loaded_rate_on,
)
from app.services.instance_authority import set_instance_owner
from app.services.organization_people import create_person
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.auth_fixtures import create_membership, create_user, ensure_office_user


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "k-fg042-m1", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        from app.services.organizations import ensure_default_organization

        ensure_default_organization()
        yield application
        db.session.rollback()
        db.session.execute(sa.text("PRAGMA foreign_keys=OFF"))
        db.session.remove()
        db.drop_all()


def _owner():
    from app.models.user import UserMembership

    user = ensure_office_user()
    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=DEFAULT_ORGANIZATION_ID).one()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, user)
    return user


def _worker_user(email="crew-a@example.com"):
    user = create_user(email=email, password="pw-crew-a", display_name="Crew A", is_active=True)
    create_membership(user, DEFAULT_ORGANIZATION_ID, is_active=True)
    db.session.commit()
    return user


def _person(owner, name="Synthetic Worker A", wage="26"):
    identity = create_person(organization_id=DEFAULT_ORGANIZATION_ID, actor=owner, full_name=name,
                             address="1 Test Rd", mobile_number="613-555-0100",
                             email_address=f"{name.split()[-1].lower()}@example.com", hourly_wage=D(wage))
    return OrganizationPerson.query.get(identity.id)


def _profile(person, owner, wage, *, effective_from=None, **extra):
    form = {"hourly_wage": str(wage), **extra}
    inputs = LCP.parse_inputs(form, company_wsib=D("3.55"))
    profile, _ = LCP.save_profile(person, inputs, actor_user=owner, wsib_override=False, reason="t",
                                  effective_from=effective_from)
    return profile


# ----------------------------------------------------------------------------------------- other employment cost
def test_other_cost_is_zero_by_default_and_changes_nothing(app):
    base = LCP.calculate(LCP.CostInputs(hourly_wage=D("26"), wsib_rate_per_100=D("3.55")))
    assert base["loaded_rate"] == D("31.25")
    assert not any(r["key"] == "other" for r in base["rows"])


def test_other_cost_is_added_as_a_plain_annual_cost(app):
    inputs = LCP.parse_inputs({"hourly_wage": "26", "other_employment_cost_annual": "1928",
                               "other_employment_cost_note": "Safety boot programme"}, company_wsib=D("3.55"))
    result = LCP.calculate(inputs)
    row = next(r for r in result["rows"] if r["key"] == "other")
    assert row["per_year"] == D("1928.00")
    assert result["annual_cost"] - D("60243.46") == D("1928.00")
    assert result["loaded_rate"] == D("32.25")  # 31.25 + 1,928 / 1,928 working hours


def test_other_cost_needs_a_note(app):
    with pytest.raises(LCP.CostProfileError, match="needs a note"):
        LCP.parse_inputs({"hourly_wage": "26", "other_employment_cost_annual": "500"}, company_wsib=D("3.55"))


@pytest.mark.parametrize("note", ["Truck allowance", "Fuel card", "RRSP match", "Health and dental", "Tool money",
                                  "WSIB top-up", "Vacation pay", "CPP", "EI", "Employer health tax", "Holiday pay"])
def test_other_cost_refuses_what_the_profile_already_counts(app, note):
    with pytest.raises(LCP.CostProfileError, match="already counts"):
        LCP.parse_inputs({"hourly_wage": "26", "other_employment_cost_annual": "500",
                          "other_employment_cost_note": note}, company_wsib=D("3.55"))


def test_other_cost_accepts_a_genuinely_different_cost_and_a_blank_note_with_no_amount(app):
    LCP.parse_inputs({"hourly_wage": "26", "other_employment_cost_annual": "500",
                      "other_employment_cost_note": "Training course fees"}, company_wsib=D("3.55"))
    LCP.parse_inputs({"hourly_wage": "26", "other_employment_cost_note": "ignored"}, company_wsib=D("3.55"))


def test_other_cost_is_stored_and_round_trips(app):
    owner = _owner()
    person = _person(owner)
    profile = _profile(person, owner, 26, other_employment_cost_annual="500",
                       other_employment_cost_note="Training course fees")
    assert profile.other_employment_cost_annual == D("500.00")
    assert profile.other_employment_cost_note == "Training course fees"
    assert LCP.inputs_of(profile).other_employment_cost_annual == D("500.00")


# ------------------------------------------------------------------------------------------------- the link
def test_link_requires_owner_or_system_administrator(app):
    owner = _owner()
    person = _person(owner)
    worker = _worker_user()
    with pytest.raises(EmployeeLinkError):
        link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, worker.id, actor=worker)
    link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, worker.id, actor=owner)
    assert OrganizationPerson.query.get(person.id).user_id == worker.id


def test_one_user_per_employee_and_one_employee_per_user(app):
    owner = _owner()
    a, b = _person(owner, "Synthetic Worker A"), _person(owner, "Synthetic Worker B")
    worker = _worker_user()
    link_person_to_user(DEFAULT_ORGANIZATION_ID, a.id, worker.id, actor=owner)
    with pytest.raises(EmployeeLinkError, match="already linked"):
        link_person_to_user(DEFAULT_ORGANIZATION_ID, b.id, worker.id, actor=owner)
    # the database enforces it too
    b = OrganizationPerson.query.get(b.id)
    b.user_id = worker.id
    with pytest.raises(sa.exc.IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_link_refuses_a_user_outside_the_organization(app):
    owner = _owner()
    person = _person(owner)
    stranger = create_user(email="stranger@example.com", password="pw-stranger", display_name="S", is_active=True)
    db.session.commit()
    with pytest.raises(EmployeeLinkError, match="not an active member"):
        link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, stranger.id, actor=owner)


def _approved_time(worker, reviewer, project, activity, hours, day):
    from app.services.time_entry import approve_time, submit_time

    entry = submit_time(project_id=project.id, project_work_activity_id=activity.id, hours=str(hours),
                        work_date=day, worker_user_id=worker.id)
    approve_time(time_entry_id=entry.id, reviewer_user_id=reviewer.id)
    return entry


def test_unlink_is_refused_once_the_user_has_time_entries(app):
    from tests.fg042_support import seeded_project

    owner = _owner()
    person = _person(owner)
    worker = _worker_user()
    link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, worker.id, actor=owner)
    link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, None, actor=owner)  # no time yet: allowed
    link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, worker.id, actor=owner)
    project, activity, _ = seeded_project()
    _approved_time(worker, owner, project, activity, 8, date(2026, 11, 2))
    with pytest.raises(EmployeeLinkError, match="time entries"):
        link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, None, actor=owner)


# ------------------------------------------------------------------------------------------------ dated rate
def test_rate_on_a_date_uses_the_profile_in_force_that_day(app):
    owner = _owner()
    person = _person(owner)
    first = _profile(person, owner, 26, effective_from=date(2026, 1, 1))
    second = _profile(person, owner, 30, effective_from=date(2026, 7, 1))
    before = loaded_rate_on(person.id, date(2026, 6, 30))
    on = loaded_rate_on(person.id, date(2026, 7, 1))
    after = loaded_rate_on(person.id, date(2026, 12, 1))
    assert (before.cost_profile_id, before.basis) == (first.id, BASIS_IN_FORCE)
    assert before.loaded_rate == D(str(first.loaded_rate))
    assert on.cost_profile_id == second.id and after.cost_profile_id == second.id
    assert on.loaded_rate > before.loaded_rate


def test_a_later_profile_never_changes_an_earlier_date(app):
    owner = _owner()
    person = _person(owner)
    _profile(person, owner, 26, effective_from=date(2026, 1, 1))
    snapshot = loaded_rate_on(person.id, date(2026, 3, 1))
    _profile(person, owner, 40, effective_from=date(2026, 9, 1))
    assert loaded_rate_on(person.id, date(2026, 3, 1)) == snapshot


def test_same_effective_date_newest_saved_wins(app):
    owner = _owner()
    person = _person(owner)
    _profile(person, owner, 26, effective_from=date(2026, 5, 1))
    newer = _profile(person, owner, 28, effective_from=date(2026, 5, 1))
    assert loaded_rate_on(person.id, date(2026, 5, 1)).cost_profile_id == newer.id


def test_a_profile_with_no_effective_date_applies_from_the_day_it_was_saved(app):
    owner = _owner()
    person = _person(owner)
    profile = _profile(person, owner, 26)
    saved_day = profile.created_at.date()
    assert loaded_rate_on(person.id, saved_day).basis == BASIS_IN_FORCE
    early = loaded_rate_on(person.id, saved_day - timedelta(days=30))
    assert early.basis == BASIS_PREDATES_FIRST_PROFILE and early.cost_profile_id == profile.id


def test_no_usable_profile_means_no_rate(app):
    owner = _owner()
    person = _person(owner)
    assert loaded_rate_on(person.id, date(2026, 11, 1)) is None


def test_user_rate_book_returns_none_for_an_unlinked_user(app):
    owner = _owner()
    worker = _worker_user()
    assert UserRateBook(DEFAULT_ORGANIZATION_ID).on(worker.id, date(2026, 11, 1)) is None
    person = _person(owner)
    _profile(person, owner, 26, effective_from=date(2026, 1, 1))
    link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, worker.id, actor=owner)
    assert UserRateBook(DEFAULT_ORGANIZATION_ID).on(worker.id, date(2026, 11, 1)).loaded_rate == D("31.25")


def test_existing_profile_rows_stay_insert_only(app):
    owner = _owner()
    person = _person(owner)
    profile = _profile(person, owner, 26)
    assert profile.id is not None
    cols = {c.name for c in OrganizationPersonCostProfile.__table__.columns}
    assert {"effective_from", "other_employment_cost_annual", "other_employment_cost_note"} <= cols


# --------------------------------------------------------------------------- project labour cost (S2 consumer)
def test_project_labour_cost_prices_linked_time_at_the_employee_rate_and_labels_the_rest(app):
    from app.services.project_performance import assemble_project_labour_cost
    from tests.fg042_support import seeded_project

    owner = _owner()
    project, activity, _ = seeded_project()
    linked_user, other_user = _worker_user("linked@example.com"), _worker_user("unlinked@example.com")
    person = _person(owner)
    _profile(person, owner, 26, effective_from=date(2026, 1, 1))
    link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, linked_user.id, actor=owner)
    _approved_time(linked_user, owner, project, activity, 8, date(2026, 11, 2))
    _approved_time(other_user, owner, project, activity, 4, date(2026, 11, 2))
    cost = assemble_project_labour_cost(DEFAULT_ORGANIZATION_ID, project.id, today=date(2026, 11, 24))
    total = cost["total"]
    assert total["person_rated_hours"] == D("8.00")
    # the unlinked 4 h keep the company rate (or are shown as unrated when there is none): never the employee's
    assert total["company_rated_hours"] + total["unrated_hours"] == D("4.00")
    assert total["actual_cost"] >= D("8") * D("31.25")


def test_project_labour_cost_is_unchanged_when_nobody_is_linked(app):
    from app.services.project_performance import assemble_project_labour_cost
    from tests.fg042_support import seeded_project

    owner = _owner()
    project, activity, _ = seeded_project()
    worker = _worker_user()
    _approved_time(worker, owner, project, activity, 5, date(2026, 11, 2))
    total = assemble_project_labour_cost(DEFAULT_ORGANIZATION_ID, project.id, today=date(2026, 11, 24))["total"]
    assert total["person_rated_hours"] == D("0.00")
    assert total["company_rated_hours"] + total["unrated_hours"] == D("5.00")


def test_a_rate_change_does_not_reprice_earlier_approved_time(app):
    from app.services.project_performance import assemble_project_labour_cost
    from tests.fg042_support import seeded_project

    owner = _owner()
    project, activity, _ = seeded_project()
    worker = _worker_user()
    person = _person(owner)
    _profile(person, owner, 26, effective_from=date(2026, 1, 1))
    link_person_to_user(DEFAULT_ORGANIZATION_ID, person.id, worker.id, actor=owner)
    _approved_time(worker, owner, project, activity, 10, date(2026, 3, 2))
    before = assemble_project_labour_cost(DEFAULT_ORGANIZATION_ID, project.id, today=date(2026, 11, 24))["total"]
    _profile(person, owner, 45, effective_from=date(2026, 9, 1))
    after = assemble_project_labour_cost(DEFAULT_ORGANIZATION_ID, project.id, today=date(2026, 11, 24))["total"]
    assert after["actual_cost"] == before["actual_cost"] == D("312.50")
