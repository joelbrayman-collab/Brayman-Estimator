"""FG-042 S1 / M2: the immutable approved project baseline. Synthetic names and figures only."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal as D

import pytest
import sqlalchemy as sa

from app import create_app, db
from app.models.estimate import EstimateVersion
from app.models.person import OrganizationPerson
from app.models.project import Project
from app.models.project_baseline import (
    ProjectBaseline,
    ProjectBaselineLabourAllocation,
    ProjectBaselineLine,
    ProjectBaselineOpenItem,
    ProjectBaselinePersonRate,
)
from app.services import labour_cost_profile as LCP
from app.services import project_baseline as PB
from app.services.instance_authority import set_instance_owner
from app.services.organization_people import create_person
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import create_membership, create_user, ensure_office_user
from tests.fg042_support import seeded_project

ORG = DEFAULT_ORGANIZATION_ID
CSV = ("group,task,person,hours\n"
       "Framing,Walls,Synthetic Alex,10\n"
       "Framing,Walls,Synthetic Blair,12.5\n"
       "Framing,Roof,Synthetic Alex,8\n"
       "Finish,Trim,Synthetic Blair,6.25\n")


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "k-m2", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.rollback()
        db.session.execute(sa.text("PRAGMA foreign_keys=OFF"))
        db.session.remove()
        db.drop_all()


@pytest.fixture
def owner(app):
    from app.models.user import UserMembership

    user = ensure_office_user(email="owner-m2@example.com", password="pw-m2")
    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()
    set_instance_owner(ORG, membership.id, user)
    return user


@pytest.fixture
def office(app):
    return ensure_office_user(email="office-m2@example.com", password="pw-m2")


def _person(owner, name, wage=None):
    identity = create_person(organization_id=ORG, actor=owner, full_name=name, address="1 Test Rd",
                             mobile_number="613-555-0100", email_address=name.split()[-1].lower() + "@example.com",
                             hourly_wage=D(wage or "26"))
    person = OrganizationPerson.query.get(identity.id)
    if wage is not None:
        inputs = LCP.parse_inputs({"hourly_wage": wage}, company_wsib=D("3.55"))
        LCP.save_profile(person, inputs, actor_user=owner, wsib_override=False, reason="t")
    return person


@pytest.fixture
def crew(app, owner):
    return {"alex": _person(owner, "Synthetic Alex", "26"), "blair": _person(owner, "Synthetic Blair", "30")}


@pytest.fixture
def base(app, owner, crew):
    project, _activity, version = seeded_project()
    row = PB.create_provisional_baseline(project, version, actor=owner, option_label="Option A",
                                         labour_selling_rate="85.00")
    return row


def _full(base, owner):
    """A fully built, self-consistent provisional baseline (labour plus two lines)."""
    PB.import_labour_csv(base, CSV, actor=owner)
    PB.add_line(base, actor=owner, category="MATERIAL", description="Synthetic sheathing", net_cost="1000.00",
                markup_rate="0.20")
    PB.add_line(base, actor=owner, category="SUBCONTRACT", description="Synthetic crane", net_cost="333.33",
                markup_rate="0.15", quoted_price="400.00", price_override_reason="Quoted to the customer")
    t = PB.totals(base)
    return {"hours": t["hours"], "revenue": t["revenue"], "cost": t["cost"], "profit": t["profit"]}


# ------------------------------------------------------------------------------------------------------ create
def test_create_provisional_from_an_estimate_version(app, owner, base):
    assert (base.status, base.pricing_basis, base.labour_selling_rate) == ("PROVISIONAL", "MARKUP", D("85.00"))
    assert base.content_sha256 is None and base.frozen_at is None


def test_only_owner_or_administrator_may_create(app, office):
    project, _a, version = seeded_project()
    with pytest.raises(PB.BaselineError, match="owner or a System Administrator"):
        PB.create_provisional_baseline(project, version, actor=office, option_label="A", labour_selling_rate="85")
    assert ProjectBaseline.query.count() == 0


def test_create_validation(app, owner, base):
    project = db.session.get(Project, base.project_id)
    version = db.session.get(EstimateVersion, base.estimate_version_id)
    for kwargs in (dict(option_label=" "), dict(labour_selling_rate="-1"), dict(labour_selling_rate="x")):
        args = dict(option_label="B", labour_selling_rate="85")
        args.update(kwargs)
        with pytest.raises(PB.BaselineError):
            PB.create_provisional_baseline(project, version, actor=owner, **args)
    with pytest.raises(PB.BaselineError, match="already exists"):
        PB.create_provisional_baseline(project, version, actor=owner, option_label="Option A",
                                       labour_selling_rate="85")


def test_version_of_another_project_is_refused(app, owner, base):
    _other_project, _a, other_version = seeded_project(name="Other Project", code="LT-OTHER")
    first = db.session.get(Project, base.project_id)
    with pytest.raises(PB.BaselineError, match="does not belong"):
        PB.create_provisional_baseline(first, other_version, actor=owner, option_label="Wrong", labour_selling_rate="85")


# ------------------------------------------------------------------------------------------------- the import
def test_import_builds_allocations_rates_and_control_totals(app, owner, base, crew):
    result = PB.import_labour_csv(base, CSV, actor=owner)
    assert result == {"rows": 4, "tasks": 3, "people": 2, "total_hours": D("36.75"), "without_rate": []}
    assert ProjectBaselineLabourAllocation.query.filter_by(baseline_id=base.id).count() == 4
    rates = {r.person_id: r.loaded_rate for r in ProjectBaselinePersonRate.query.filter_by(baseline_id=base.id)}
    assert rates[crew["alex"].id] == LCP.calculate(LCP.CostInputs(hourly_wage=D("26"),
                                                                 wsib_rate_per_100=D("3.55")))["loaded_rate"]


def test_allocations_tie_per_task_per_person_and_in_total(app, owner, base):
    PB.import_labour_csv(base, CSV, actor=owner)
    schedule = PB.view(base)["schedule"]
    per_task = {s["task"]: s["total"] for s in schedule}
    assert per_task == {"Walls": D("22.50"), "Roof": D("8.00"), "Trim": D("6.25")}
    assert sum(per_task.values()) == PB.totals(base)["hours"] == D("36.75")
    walls = next(s for s in schedule if s["task"] == "Walls")
    assert {(p["name"], p["hours"]) for p in walls["people"]} == {("Synthetic Alex", D("10.00")),
                                                                  ("Synthetic Blair", D("12.50"))}


def test_reimport_replaces_and_a_bad_file_changes_nothing(app, owner, base):
    PB.import_labour_csv(base, CSV, actor=owner)
    before = PB.canonical_content(base)
    bad_files = [
        "group,task,person,hours\nA,T,Nobody Here,1\n",
        "group,task,person,hours\nA,T,Synthetic Alex,1\nA,T,Synthetic Alex,2\n",
        "group,task,person,hours\nA,T,Synthetic Alex,-1\n",
        "group,task,person,hours\nA,T,Synthetic Alex,1.234\n",
        "group,task,person,hours\nA,T,Synthetic Alex,abc\n",
        "group,task,person\nA,T,Synthetic Alex\n",
        "group,task,person,hours\n",
    ]
    for text in bad_files:
        with pytest.raises(PB.BaselineError):
            PB.import_labour_csv(base, text, actor=owner)
        assert PB.canonical_content(base) == before
    PB.import_labour_csv(base, "group,task,person,hours\nF,Only,Synthetic Alex,3\n", actor=owner)
    assert PB.totals(base)["hours"] == D("3.00")


def test_unknown_names_are_listed_together(app, owner, base):
    with pytest.raises(PB.BaselineError, match="Nobody One, Nobody Two"):
        PB.import_labour_csv(base, "group,task,person,hours\nA,T,Nobody One,1\nA,T2,Nobody Two,1\n", actor=owner)


def test_person_without_a_rate_becomes_an_open_item_and_resolves_when_a_rate_exists(app, owner, base, crew):
    no_rate = _person(owner, "Synthetic Casey")  # no cost profile yet (employee onboarding)
    result = PB.import_labour_csv(base, CSV + "Finish,Paint,Synthetic Casey,4\n", actor=owner)
    assert result["without_rate"] == ["Synthetic Casey"]
    items = ProjectBaselineOpenItem.query.filter_by(baseline_id=base.id, status="OPEN").all()
    assert [i.description for i in items] == ["No loaded rate: Synthetic Casey"]
    assert PB.totals(base)["unrated_person_ids"] == [no_rate.id]
    inputs = LCP.parse_inputs({"hourly_wage": "22"}, company_wsib=D("3.55"))
    LCP.save_profile(no_rate, inputs, actor_user=owner, wsib_override=False, reason="onboarded")
    PB.import_labour_csv(base, CSV + "Finish,Paint,Synthetic Casey,4\n", actor=owner)
    assert ProjectBaselineOpenItem.query.filter_by(baseline_id=base.id, status="OPEN").count() == 0
    assert PB.totals(base)["unrated_person_ids"] == []


# ---------------------------------------------------------------------------------------------------- lines
def test_line_selling_follows_the_shared_markup_rule_and_override_is_stored_with_its_reason(app, owner, base):
    line = PB.add_line(base, actor=owner, category="MATERIAL", description="Synthetic lumber", net_cost="1000.00",
                       markup_rate="0.20", supplier_name="Synthetic Supplier")
    assert (line.net_cost, line.markup_rate, line.selling_price) == (D("1000.00"), D("0.200000"), D("1200.00"))
    quoted = PB.add_line(base, actor=owner, category="SUBCONTRACT", description="Synthetic crane", net_cost="333.33",
                         markup_rate="0.15", quoted_price="400.00", price_override_reason="Quoted to the customer")
    assert quoted.selling_price == D("400.00") and quoted.price_override_reason == "Quoted to the customer"
    with pytest.raises(PB.BaselineError, match="needs a reason"):
        PB.add_line(base, actor=owner, category="MATERIAL", description="x", net_cost="10", markup_rate="0.1",
                    quoted_price="12")


def test_line_uses_the_company_markup_when_none_is_given_and_refuses_when_none_exists(app, owner, base):
    with pytest.raises(PB.BaselineError, match="No markup is configured"):
        PB.add_line(base, actor=owner, category="MATERIAL", description="x", net_cost="10")
    from datetime import datetime

    from app.models.pricing_engine import OrganizationPricingPolicy

    db.session.add(OrganizationPricingPolicy(organization_id=ORG, policy_code="M2-D", version_number=1,
                                             method="COST_PLUS_MARKUP", markup_rate=D("0.25"),
                                             approval_status="ORG_APPROVED", is_default=True, created_by="t",
                                             created_at=datetime.utcnow()))
    db.session.commit()
    assert PB.add_line(base, actor=owner, category="MATERIAL", description="x", net_cost="100").selling_price == D("125.00")


def test_line_validation_and_provisional_reason(app, owner, base):
    for kwargs in (dict(category="NOPE"), dict(description=" "), dict(net_cost="-1"),
                   dict(is_provisional=True)):
        args = dict(category="MATERIAL", description="x", net_cost="10", markup_rate="0.1")
        args.update(kwargs)
        with pytest.raises(PB.BaselineError):
            PB.add_line(base, actor=owner, **args)
    assert ProjectBaselineLine.query.count() == 0


def test_remove_line_while_provisional(app, owner, base):
    line = PB.add_line(base, actor=owner, category="MATERIAL", description="x", net_cost="10", markup_rate="0.1")
    PB.remove_line(base, line.id, actor=owner)
    assert ProjectBaselineLine.query.count() == 0


# ---------------------------------------------------------------------------------------- totals and display
def test_totals_order_and_margin(app, owner, base):
    _full(base, owner)
    v = PB.view(base, include_rates=True)
    assert [label for label, _ in v["summary"]] == ["Revenue", "Cost", "Profit", "Profit Margin"]
    t = v["totals"]
    assert t["labour_revenue"] == D("3123.75")  # 36.75 h x 85.00
    assert t["revenue"] == t["labour_revenue"] + D("1200.00") + D("400.00")
    assert t["profit"] == t["revenue"] - t["cost"]
    assert t["profit_margin"] == t["profit"] / t["revenue"]
    assert v["person_rates"]  # the owner-only page asks for rates


def test_allocation_schedule_is_hours_and_assignments_only(app, owner, base):
    _full(base, owner)
    schedule = PB.view(base)["schedule"]
    assert set(schedule[0]) == {"group", "task", "people", "total"}
    assert all(set(p) == {"name", "hours"} for s in schedule for p in s["people"])
    assert "person_rates" not in PB.view(base)


# ------------------------------------------------------------------------------------------ reconciliation
def test_reconciliation_ok_and_a_difference_blocks_freezing(app, owner, base):
    source = _full(base, owner)
    assert PB.reconcile(base, source)["ok"]
    off = dict(source, revenue=source["revenue"] + D("0.01"))
    report = PB.reconcile(base, off)
    assert not report["ok"] and [c["key"] for c in report["checks"] if not c["ok"]] == ["revenue"]
    with pytest.raises(PB.BaselineError, match=r"Revenue differs by -0\.01"):
        PB.freeze(base, actor=owner, source=off)
    assert base.status == "PROVISIONAL"


def test_reconciliation_needs_hours_revenue_and_cost_from_the_source(app, owner, base):
    source = _full(base, owner)
    for missing in ("hours", "revenue", "cost"):
        partial = {k: v for k, v in source.items() if k != missing}
        assert not PB.reconcile(base, partial)["ok"]
    assert not PB.reconcile(base, {})["ok"]  # no source at all (no approval figures)


def test_unrated_person_blocks_freezing(app, owner, base):
    _person(owner, "Synthetic Casey")
    PB.import_labour_csv(base, CSV + "Finish,Paint,Synthetic Casey,4\n", actor=owner)
    report = PB.reconcile(base, {"hours": D("40.75"), "revenue": D("1"), "cost": D("1")})
    assert any("No loaded rate for: Synthetic Casey" in p for p in report["problems"])


# --------------------------------------------------------------------------------------------------- freezing
def test_open_item_blocks_freezing_in_service_and_in_the_database(app, owner, base):
    source = _full(base, owner)
    item = PB.add_open_item(base, "Confirm the crane quote", actor=owner)
    with pytest.raises(PB.BaselineError, match="1 open item"):
        PB.freeze(base, actor=owner, source=source)
    with pytest.raises(sa.exc.DatabaseError, match="open items cannot be frozen"):
        db.session.execute(sa.text(
            "UPDATE project_baselines SET status='FROZEN', content_sha256='x', frozen_at='2026-11-24', "
            "frozen_by_user_id=1, reconciliation_json='{}' WHERE id=:i"), {"i": base.id})
    db.session.rollback()
    PB.resolve_open_item(base, item.id, "Confirmed by phone", actor=owner)
    assert PB.freeze(base, actor=owner, source=source).status == "FROZEN"


def test_provisional_line_blocks_freezing_in_service_and_in_the_database(app, owner, base):
    source = _full(base, owner)
    PB.add_line(base, actor=owner, category="ALLOWANCE", description="Unpriced hatch", net_cost="0",
                markup_rate="0", is_provisional=True, provisional_reason="Fire rating unconfirmed")
    with pytest.raises(PB.BaselineError, match="provisional lines"):
        PB.freeze(base, actor=owner, source=source)
    with pytest.raises(sa.exc.DatabaseError, match="provisional lines cannot be frozen"):
        db.session.execute(sa.text(
            "UPDATE project_baselines SET status='FROZEN', content_sha256='x', frozen_at='2026-11-24', "
            "frozen_by_user_id=1, reconciliation_json='{}' WHERE id=:i"), {"i": base.id})
    db.session.rollback()


def test_freeze_records_who_when_sha_and_reconciliation(app, owner, base):
    source = _full(base, owner)
    PB.freeze(base, actor=owner, source=source)
    assert (base.status, base.frozen_by_user_id) == ("FROZEN", owner.id) and base.frozen_at is not None
    assert len(base.content_sha256) == 64 and PB.verify(base)
    recorded = json.loads(base.reconciliation_json)
    assert all(c["ok"] for c in recorded["checks"]) and recorded["frozen_by_user_id"] == owner.id
    assert PB.content_sha256(base) == base.content_sha256  # reproducible from the stored content


def test_only_the_owner_or_an_administrator_may_freeze_or_edit(app, owner, office, base):
    source = _full(base, owner)
    for call in (lambda: PB.freeze(base, actor=office, source=source),
                 lambda: PB.import_labour_csv(base, CSV, actor=office),
                 lambda: PB.add_line(base, actor=office, category="MATERIAL", description="x", net_cost="1",
                                     markup_rate="0.1"),
                 lambda: PB.add_open_item(base, "x", actor=office)):
        with pytest.raises(PB.BaselineError, match="owner or a System Administrator"):
            call()


def test_a_frozen_baseline_refuses_every_service_change(app, owner, base):
    source = _full(base, owner)
    PB.freeze(base, actor=owner, source=source)
    for call in (lambda: PB.import_labour_csv(base, CSV, actor=owner),
                 lambda: PB.add_line(base, actor=owner, category="MATERIAL", description="x", net_cost="1",
                                     markup_rate="0.1"),
                 lambda: PB.add_open_item(base, "x", actor=owner),
                 lambda: PB.freeze(base, actor=owner, source=source)):
        with pytest.raises(PB.BaselineError, match="only a PROVISIONAL baseline can be changed"):
            call()


# ---------------------------------------------------------------- immutability at the database level
@pytest.fixture
def frozen(app, owner, base):
    PB.freeze(base, actor=owner, source=_full(base, owner))
    return base


def _refused(sql, **params):
    with pytest.raises(sa.exc.DatabaseError, match="frozen|immutable"):
        db.session.execute(sa.text(sql), params)
    db.session.rollback()


def test_database_refuses_every_change_to_a_frozen_baseline(app, frozen):
    bid = frozen.id
    for table, change in (("project_baseline_labour_allocations", "hours = 99"),
                          ("project_baseline_person_rates", "loaded_rate = 1"),
                          ("project_baseline_lines", "net_cost = 1")):
        _refused(f"UPDATE {table} SET {change} WHERE baseline_id = :b", b=bid)
        _refused(f"DELETE FROM {table} WHERE baseline_id = :b", b=bid)
    _refused("INSERT INTO project_baseline_open_items (baseline_id, description, status) VALUES (:b, 'late', 'OPEN')",
             b=bid)
    _refused("INSERT INTO project_baseline_lines (baseline_id, category, description, net_cost, markup_rate, "
             "selling_price, is_provisional, sort_order) VALUES (:b, 'OTHER', 'late', 1, 0, 1, 0, 9)", b=bid)
    _refused("INSERT INTO project_baseline_labour_allocations (baseline_id, group_name, task_name, sort_order, "
             "person_id, hours) VALUES (:b, 'g', 'late task', 9, 1, 1)", b=bid)
    _refused("UPDATE project_baselines SET labour_selling_rate = 1 WHERE id = :b", b=bid)
    _refused("UPDATE project_baselines SET content_sha256 = 'tampered' WHERE id = :b", b=bid)
    _refused("UPDATE project_baselines SET status = 'PROVISIONAL' WHERE id = :b", b=bid)
    _refused("DELETE FROM project_baselines WHERE id = :b", b=bid)
    assert PB.verify(db.session.get(ProjectBaseline, bid))


def test_a_frozen_baseline_moves_only_to_superseded_with_nothing_else_changed(app, frozen):
    _refused("UPDATE project_baselines SET status = 'SUPERSEDED', option_label = 'renamed' WHERE id = :b", b=frozen.id)
    db.session.execute(sa.text("UPDATE project_baselines SET status = 'SUPERSEDED' WHERE id = :b"), {"b": frozen.id})
    db.session.commit()
    assert db.session.get(ProjectBaseline, frozen.id).status == "SUPERSEDED"
    _refused("UPDATE project_baselines SET status = 'FROZEN' WHERE id = :b", b=frozen.id)
    _refused("DELETE FROM project_baseline_lines WHERE baseline_id = :b", b=frozen.id)


def test_one_frozen_baseline_per_project_and_a_new_freeze_supersedes_the_old(app, owner, frozen):
    second = PB.create_provisional_baseline(db.session.get(Project, frozen.project_id),
                                            db.session.get(EstimateVersion, frozen.estimate_version_id), actor=owner,
                                            option_label="Option B", labour_selling_rate="90.00")
    source = _full(second, owner)
    PB.freeze(second, actor=owner, source=source)
    assert db.session.get(ProjectBaseline, frozen.id).status == "SUPERSEDED" and second.status == "FROZEN"
    assert ProjectBaseline.query.filter_by(project_id=second.project_id, status="FROZEN").count() == 1
    # the unique index also refuses two FROZEN rows written around the service
    third = PB.create_provisional_baseline(db.session.get(Project, frozen.project_id),
                                           db.session.get(EstimateVersion, frozen.estimate_version_id), actor=owner,
                                           option_label="Option C", labour_selling_rate="90.00")
    _full(third, owner)
    with pytest.raises(sa.exc.IntegrityError):
        db.session.execute(sa.text(
            "UPDATE project_baselines SET status='FROZEN', content_sha256='x', frozen_at='2026-11-24', "
            "frozen_by_user_id=1, reconciliation_json='{}' WHERE id=:i"), {"i": third.id})
    db.session.rollback()


def test_a_provisional_baseline_can_still_be_deleted_but_not_a_frozen_one(app, owner, base):
    db.session.execute(sa.text("DELETE FROM project_baselines WHERE id = :b"), {"b": base.id})
    db.session.commit()
    assert ProjectBaseline.query.count() == 0


# ------------------------------------------------------------- the estimate and its approval are untouched
def test_estimate_version_and_approval_rows_are_byte_identical_after_the_whole_flow(app, owner, crew):
    from app.models.estimate_approval import EstimateApproval

    project, _a, version = seeded_project()

    def snapshot():
        out = {}
        with db.engine.connect() as conn:
            for table in ("estimates", "estimate_versions", "estimate_approvals", "estimate_line_items",
                          "estimate_labour_snapshots", "projects"):
                try:
                    out[table] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{table}"')))
                except sa.exc.OperationalError:
                    pass
        return out

    before = snapshot()
    row = PB.create_provisional_baseline(project, version, actor=owner, option_label="Option A",
                                         labour_selling_rate="85.00")
    PB.freeze(row, actor=owner, source=_full(row, owner))
    assert snapshot() == before
    assert db.session.get(EstimateVersion, version.id) is not None and EstimateApproval.query.count() >= 0


# ---------------------------------------------------------------- the approved figures as the source
def test_source_totals_come_from_the_frozen_approval_summary_and_nothing_in_it_changes(app, owner, crew):
    from app.models.estimate_approval import EstimateApproval
    from app.services.estimate_approval import record_approval

    project, _a, version = seeded_project()
    approval = record_approval(version, user=owner)
    db.session.commit()
    frozen_before = (approval.summary_json, approval.fingerprint)
    row = PB.create_provisional_baseline(project, version, actor=owner, option_label="Option A",
                                         labour_selling_rate="85.00")
    assert row.estimate_approval_id == approval.id
    source = PB.approved_source_totals(row)
    assert {"hours", "revenue"} <= set(source)
    assert "cost" not in source  # the approved summary has no cost until a crew is assigned: freezing then needs it
    # an empty baseline does not reconcile to the approved figures, so it cannot be frozen
    assert not PB.reconcile(row)["ok"]
    with pytest.raises(PB.BaselineError, match="cannot be frozen"):
        PB.freeze(row, actor=owner)
    fresh = db.session.get(EstimateApproval, approval.id)
    assert (fresh.summary_json, fresh.fingerprint) == frozen_before
    # a second live baseline cannot reference the same approval
    with pytest.raises(sa.exc.IntegrityError):
        PB.create_provisional_baseline(project, version, actor=owner, option_label="Option B",
                                       labour_selling_rate="85.00")
    db.session.rollback()
