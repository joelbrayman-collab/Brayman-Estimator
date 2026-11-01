"""Attention list: review fixes I2 (cost of the bell and the project page) and M5 (owner reminder counts),
1 Nov 2026. Synthetic data only.

I2  The header bell asks /attention/count on every page; it is now answered from a short per-person cache (primed by
    the pages that already assembled the list), while the attention list itself is always assembled fresh. The
    project page's narrowed list is assembled with the project in the context, so the providers that can filter by
    project do so in SQL, with exactly the same result. "Material lines still need a price" no longer loads every
    section and line of every estimate (one aggregate query; the statement count does not grow with line items).
M5  The owner's end-of-day reminder counts "extra work or change order" exactly as before the Task-First list: a
    change order drafted in the office (the new change_order_drafts provider) is on the attention list but is not
    counted in the owner's text/email.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date

import pytest
from sqlalchemy import event

from app import create_app, db
from app.models import Client, Project
from app.models.user import UserMembership
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import ensure_office_user

TODAY = date(2026, 11, 2)


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "attention-review-fixes", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def _owner():
    from app.models.organization import Organization

    user = ensure_office_user()
    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()
    db.session.get(Organization, ORG).instance_owner_membership_id = membership.id
    db.session.commit()
    return user


def _project(name):
    client = Client(name=f"{name} customer", organization_id=ORG, email="c@example.com", phone="555-0100",
                    address="1 Synthetic Rd")
    db.session.add(client)
    db.session.flush()
    project = Project(name=name, client_id=client.id, organization_id=ORG, status="Estimating")
    db.session.add(project)
    db.session.commit()
    return project


def _change_order(project, number, status):
    from app.project_controls.models import ChangeOrder

    db.session.add(ChangeOrder(organization_id=ORG, project_id=project.id, number=number, title=f"{number} work",
                               status=status))
    db.session.commit()


@contextmanager
def _statements():
    seen = []

    def count(conn, cursor, statement, parameters, context, executemany):
        seen.append(statement)

    engine = db.engine
    event.listen(engine, "before_cursor_execute", count)
    try:
        yield seen
    finally:
        event.remove(engine, "before_cursor_execute", count)


def _priced_world(lines_per_estimate):
    """Three jobs, each with a draft estimate whose material lines have no price yet."""
    from app.models.cost_item import CostItem
    from app.services.estimate_builder import add_cost_item_line_uncommitted, create_section
    from app.services.estimates import create_estimate

    item = CostItem(organization_id=ORG, code="LUM-2X6", name="2x6 SPF (synthetic)", category="Material", unit="ea",
                    unit_cost=0, is_active=True)
    db.session.add(item)
    db.session.commit()
    projects = []
    for n in range(3):
        project = _project(f"Priced job {n}")
        estimate = create_estimate(project_id=project.id, estimate_number=f"EST-P-{n}", title=f"Estimate {n}")
        for s in range(2):
            section = create_section(estimate.current_version, name=f"Section {s}")
            for _ in range(lines_per_estimate // 2):
                add_cost_item_line_uncommitted(section, cost_item_id=item.id, quantity=3, organization_id=ORG)
        db.session.commit()
        projects.append(project)
    return projects


# ------------------------------------------------------------------ M5


def test_the_owner_reminder_counts_extra_work_as_before_the_task_first_list(app):
    from app.services.needs_attention import assemble
    from app.services.reminders import owner_items

    owner = _owner()
    project = _project("Reminder job")
    _change_order(project, "CO-R-1", "Draft")              # new on the list (change_order_drafts), not in the text
    _change_order(project, "CO-R-2", "Pending Approval")   # counted before and still counted
    with app.test_request_context("/"):
        providers = [i["provider"] for i in assemble(ORG, owner, today=TODAY)["items"] if i["kind"] == "extra_work"]
        reminder = owner_items(ORG, owner, TODAY)
    assert sorted(providers) == ["change_order_drafts", "extra_work"]  # the draft stays on the attention list
    extra = [r for r in reminder if r["key"] == "extra_work"]
    assert [r["text"] for r in extra] == ["1 extra work or change order"]


def test_a_draft_change_order_alone_adds_nothing_to_the_owner_reminder(app):
    from app.services.reminders import owner_items

    owner = _owner()
    _change_order(_project("Draft only"), "CO-R-3", "Draft")
    with app.test_request_context("/"):
        assert [r for r in owner_items(ORG, owner, TODAY) if r["key"] == "extra_work"] == []


# ------------------------------------------------------------------ I2 (c): no N+1 over estimate lines


def _assemble_statements(app, owner, **kw):
    """Statements one assemble() runs in a fresh session, as in a new request."""
    from app.models.user import User
    from app.services.needs_attention import assemble

    owner_id = owner.id
    db.session.remove()
    owner = db.session.get(User, owner_id)
    with app.test_request_context("/"):
        with _statements() as seen:
            view = assemble(ORG, owner, today=TODAY, **kw)
    return len(seen), view


def test_assemble_statement_count_does_not_grow_with_line_items(app):
    owner = _owner()
    _priced_world(lines_per_estimate=2)
    few, view_few = _assemble_statements(app, owner)
    from app.models import Estimate
    from app.models.cost_item import CostItem
    from app.services.estimate_builder import add_cost_item_line_uncommitted, create_section

    # More sections, more lines, each line its own cost item: nothing per line or per section may be loaded.
    n = 0
    for estimate in Estimate.query.all():
        for s in range(2):
            section = create_section(estimate.current_version, name=f"More {s}")
            for _ in range(5):
                n += 1
                item = CostItem(organization_id=ORG, code=f"MAT-{n}", name=f"Material {n} (synthetic)",
                                category="Material", unit="ea", unit_cost=0, is_active=True)
                db.session.add(item)
                db.session.flush()
                add_cost_item_line_uncommitted(section, cost_item_id=item.id, quantity=1, organization_id=ORG)
    db.session.commit()
    many, view_many = _assemble_statements(app, owner)
    assert many == few, (few, many)
    missing = sorted(i["what"] for i in view_many["items"] if i["provider"] == "supplier_prices_missing")
    assert missing == ["12 material lines still need a price"] * 3
    assert sorted(i["what"] for i in view_few["items"] if i["provider"] == "supplier_prices_missing") == \
        ["2 material lines still need a price"] * 3


def test_prices_missing_counts_only_unpriced_unexplained_material_lines(app):
    from app.models.estimate import EstimateLineItem

    owner = _owner()
    _priced_world(lines_per_estimate=4)
    lines = EstimateLineItem.query.order_by(EstimateLineItem.id).all()
    lines[0].unit_cost = 5               # priced
    lines[1].costing_override_reason = "Owner supplies it"  # explained
    lines[2].costing_override_reason = ""                   # empty reason still counts as missing
    db.session.commit()
    _n, view = _assemble_statements(app, owner)
    found = sorted(i["what"] for i in view["items"] if i["provider"] == "supplier_prices_missing")
    assert found == ["2 material lines still need a price", "4 material lines still need a price",
                     "4 material lines still need a price"]


# ------------------------------------------------------------------ I2 (b): the project page


def test_the_project_list_is_identical_and_cheaper_with_the_project_in_the_context(app, monkeypatch):
    import app.services.needs_attention as NA

    owner = _owner()
    projects = _priced_world(lines_per_estimate=2)
    _change_order(projects[0], "CO-P-1", "Draft")
    _change_order(projects[1], "CO-P-2", "Draft")
    target = projects[0].id
    full_n, full = _assemble_statements(app, owner)
    narrowed_n, narrowed = _assemble_statements(app, owner, project_id=target)
    expected = [i for i in full["items"] if i.get("project_id") == target]
    assert narrowed["items"] == expected and narrowed["count"] == len(expected)
    assert narrowed_n < full_n
    # The providers see the project (so they can filter in SQL).
    seen = []
    monkeypatch.setattr(NA, "PROVIDERS", NA.PROVIDERS + [NA.AttentionProvider(
        "probe", "tasks", NA.SCOPE_OFFICE, lambda ctx: seen.append(ctx.project_id) or [])])
    _assemble_statements(app, owner, project_id=target)
    assert seen == [target]


# ------------------------------------------------------------------ I2 (a): the bell


def test_the_bell_count_is_cached_briefly_per_person_and_the_list_stays_fresh(app, monkeypatch):
    import app.services.needs_attention as NA

    owner = _owner()
    project = _project("Bell job")
    _change_order(project, "CO-B-1", "Draft")
    calls = []
    real = NA.assemble

    def counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(NA, "assemble", counting)
    clock = [1000.0]
    monkeypatch.setattr(NA, "_now", lambda: clock[0])
    with app.test_request_context("/"):
        assert NA.count_for(ORG, owner) == 1
        _change_order(project, "CO-B-2", "Draft")
        assert NA.count_for(ORG, owner) == 1  # cached: the bell is a hint
        assert len(calls) == 1
        assert real(ORG, owner)["count"] == 2  # the list itself is always fresh
        clock[0] += NA.BELL_CACHE_SECONDS + 1
        assert NA.count_for(ORG, owner) == 2
        assert len(calls) == 2


def test_the_bell_cache_is_per_person_and_primed_by_a_page_that_assembled(app, monkeypatch):
    import app.services.needs_attention as NA
    from tests.auth_fixtures import create_membership, create_user

    owner = _owner()
    staff = create_user(email="bell.staff@example.com", password="staff-password-1", display_name="Bell Staff")
    create_membership(staff, ORG)
    db.session.commit()
    _change_order(_project("Bell job 2"), "CO-B-3", "Draft")
    with app.test_request_context("/"):
        NA.assemble(ORG, owner)  # e.g. Home: primes the bell for this person
        calls = []
        monkeypatch.setattr(NA, "assemble", lambda *a, **k: calls.append(1) or {"waiting_on_you": []})
        assert NA.count_for(ORG, owner) == 1 and calls == []
        assert NA.count_for(ORG, staff) == 0 and calls == [1]  # another person: not shared


def test_a_narrowed_or_backdated_list_never_primes_the_bell(app, monkeypatch):
    import app.services.needs_attention as NA

    owner = _owner()
    project = _project("Bell job 3")
    _change_order(project, "CO-B-4", "Draft")
    with app.test_request_context("/"):
        NA.assemble(ORG, owner, project_id=project.id + 999)
        NA.assemble(ORG, owner, today=date(2020, 1, 1))
        assert NA.count_for(ORG, owner) == 1
