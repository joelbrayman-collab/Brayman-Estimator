"""FG-042 M3 (c2a5b8d1e4f6) and the shared materials markup calculation. Synthetic data only."""

from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal as D

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models.pricing_engine import OrganizationPricingPolicy, PricingMarkupOverride
from app.models.supplier_catalogue import Supplier
from app.services import markup as M
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import ensure_office_user
from tests.fg042_support import seeded_project

REVISION = "c2a5b8d1e4f6"
PRIOR = "b1f4a9c2d7e3"
ORG = DEFAULT_ORGANIZATION_ID


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "k-m3", "WTF_CSRF_ENABLED": False})
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

    user = ensure_office_user(email="owner-m3@example.com", password="pw-m3")
    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()
    set_instance_owner(ORG, membership.id, user)
    return user


# ------------------------------------------------------------------------------------------- the calculation
def test_selling_profit_and_margin():
    line = M.price_line("100.00", "0.25")
    assert (line.selling, line.profit) == (D("125.00"), D("25.00"))
    assert line.margin == D("0.2")
    assert (line.discount, line.quoted) == (D("0.00"), False)


def test_rounding_is_half_up_per_line_and_totals_are_sums_of_lines():
    lines = [M.price_line("10.01", "0.15"), M.price_line("3.33", "0.15"), M.price_line("7.50", "0.15")]
    assert [l.selling for l in lines] == [D("11.51"), D("3.83"), D("8.63")]  # 11.5115, 3.8295, 8.625
    totals = M.total(lines)
    assert totals.selling == sum(l.selling for l in lines) == D("23.97")
    assert totals.net_cost == D("20.84")
    assert totals.profit == totals.selling - totals.net_cost


def test_line_package_project_reconcile():
    pkg_a = M.total([M.price_line("100.00", "0.2"), M.price_line("55.55", "0.2")])
    pkg_b = M.total([M.price_line("9.99", "0.2")])
    project = M.total_packages([pkg_a, pkg_b])
    assert project.net_cost == pkg_a.net_cost + pkg_b.net_cost
    assert project.selling == pkg_a.selling + pkg_b.selling
    assert project.profit == project.selling - project.net_cost
    assert project.line_count == 3


def test_zero_revenue_has_no_margin():
    assert M.total([]).margin is None
    assert M.price_line("0.00", "0.3").margin is None


def test_quoted_price_needs_a_reason_and_shows_the_discount():
    with pytest.raises(M.MarkupError, match="needs a reason"):
        M.price_line("100.00", "0.25", quoted_price="120.00")
    line = M.price_line("100.00", "0.25", quoted_price="120.00", override_reason="Customer package price")
    assert (line.calculated_selling, line.selling, line.discount, line.profit) == (
        D("125.00"), D("120.00"), D("5.00"), D("20.00"))
    assert line.quoted and line.override_reason == "Customer package price"
    assert M.total([line]).discount == D("5.00")


def test_a_premium_is_a_negative_discount():
    assert M.price_line("100.00", "0.10", quoted_price="115.00", override_reason="Rush order").discount == D("-5.00")


def test_invalid_inputs_are_refused():
    for args in (("-1", "0.1"), ("10", "-0.1"), ("abc", "0.1"), ("10", "x")):
        with pytest.raises(M.MarkupError):
            M.price_line(*args)
    with pytest.raises(M.MarkupError):
        M.price_line("10", "0.1", quoted_price="-5", override_reason="r")


def test_legacy_pricing_methods_are_untouched():
    from app.services.pricing_engine import cost_plus_markup_pre_tax

    assert cost_plus_markup_pre_tax("10.01", "0.15") == M.price_line("10.01", "0.15").selling


# ------------------------------------------------------------------------------------------ which markup applies
def _supplier(code="SUP-M3"):
    s = Supplier(code=code, legal_name="Synthetic Lumber Ltd.")
    db.session.add(s)
    db.session.commit()
    return s


def _company_default(rate):
    policy = OrganizationPricingPolicy(organization_id=ORG, policy_code="M3-DEFAULT", version_number=1,
                                       method="COST_PLUS_MARKUP", markup_rate=D(rate), approval_status="ORG_APPROVED",
                                       is_default=True, created_by="test", created_at=datetime.utcnow())
    db.session.add(policy)
    db.session.commit()


def test_no_markup_configured_is_reported_not_defaulted(app):
    assert M.resolve_markup(ORG) == (None, None, None)


def test_precedence_project_then_supplier_then_company(app, owner):
    project, _, _ = seeded_project()
    supplier = _supplier()
    _company_default("0.20")
    assert M.resolve_markup(ORG, project_id=project.id, supplier_id=supplier.id) == (D("0.20"), M.SOURCE_COMPANY, None)
    M.record_markup_override(ORG, scope="SUPPLIER", target_id=supplier.id, markup_rate="0.12",
                             reason="Contract pricing", actor=owner, effective_from=date(2026, 1, 1))
    assert M.resolve_markup(ORG, project_id=project.id, supplier_id=supplier.id)[:2] == (D("0.12"), M.SOURCE_SUPPLIER)
    M.record_markup_override(ORG, scope="PROJECT", target_id=project.id, markup_rate="0.08",
                             reason="Negotiated for this job", actor=owner, effective_from=date(2026, 1, 1))
    rate, source, reason = M.resolve_markup(ORG, project_id=project.id, supplier_id=supplier.id)
    assert (rate, source, reason) == (D("0.08"), M.SOURCE_PROJECT, "Negotiated for this job")


def test_newest_row_in_force_wins_and_future_rows_wait(app, owner):
    project, _, _ = seeded_project()
    for rate, day in (("0.10", date(2026, 1, 1)), ("0.14", date(2026, 6, 1)), ("0.30", date(2027, 1, 1))):
        M.record_markup_override(ORG, scope="PROJECT", target_id=project.id, markup_rate=rate, reason="r",
                                 actor=owner, effective_from=day)
    assert M.resolve_markup(ORG, project_id=project.id, on_day=date(2026, 3, 1))[0] == D("0.10")
    assert M.resolve_markup(ORG, project_id=project.id, on_day=date(2026, 11, 24))[0] == D("0.14")
    assert M.resolve_markup(ORG, project_id=project.id, on_day=date(2027, 2, 1))[0] == D("0.30")


def test_override_needs_reason_nonnegative_rate_and_the_owner(app, owner):
    project, _, _ = seeded_project()
    other = ensure_office_user(email="office-m3@example.com", password="pw-m3")
    with pytest.raises(M.MarkupError, match="owner or a System Administrator"):
        M.record_markup_override(ORG, scope="PROJECT", target_id=project.id, markup_rate="0.1", reason="r", actor=other)
    for kwargs in (dict(reason=" "), dict(markup_rate="-0.1"), dict(scope="COMPANY"), dict(reason="x" * 301)):
        base = dict(scope="PROJECT", target_id=project.id, markup_rate="0.1", reason="r", actor=owner)
        base.update(kwargs)
        with pytest.raises(M.MarkupError):
            M.record_markup_override(ORG, **base)
    assert PricingMarkupOverride.query.count() == 0


# ---------------------------------------------------------------------------------------------- the migration
def _config(db_path):
    cfg = Config("migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def test_revision_follows_m1():
    script = ScriptDirectory.from_config(_config(":memory:"))
    assert script.get_revision(REVISION).down_revision == PRIOR


def test_upgrade_adds_one_table_touches_nothing_else_and_downgrade_is_guarded(tmp_path):
    db_path = tmp_path / "m3.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        before_tables = set(sa.inspect(engine).get_table_names())
        before = {}
        with engine.connect() as conn:
            for t in sorted(before_tables - {"alembic_version"}):
                before[t] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"')))
        command.upgrade(cfg, REVISION)
        after_tables = set(sa.inspect(engine).get_table_names())
        assert after_tables - before_tables == {"pricing_markup_overrides"}
        with engine.connect() as conn:
            for t, rows in before.items():
                assert sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"'))) == rows, t
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            triggers = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))}
            assert {"pricing_markup_overrides_no_update", "pricing_markup_overrides_no_delete"} <= triggers
        with engine.begin() as conn:
            conn.execute(sa.text(
                "INSERT OR IGNORE INTO organizations (id, legal_name, display_name, currency, is_active, created_at, updated_at)"
                " VALUES ('ORG-001','S','S','CAD',1,'2026-11-24','2026-11-24')"))
            conn.execute(sa.text(
                "INSERT INTO users (email, display_name, password_hash, is_active, created_at, updated_at) VALUES "
                "('o@example.invalid','O','x',1,'2026-11-24','2026-11-24')"))
        # the table's own check constraints refuse a project row with no project, a negative rate, an empty reason
        bad = ("INSERT INTO pricing_markup_overrides (organization_id, scope, project_id, markup_rate, reason, "
               "effective_from, created_at, actor_user_id, actor_name) VALUES ('ORG-001','PROJECT',{p},{r},'{why}',"
               "'2026-11-24','2026-11-24',1,'O')")
        for sql in (bad.format(p="NULL", r="0.1", why="x"), bad.format(p="1", r="-0.1", why="x"),
                    bad.format(p="1", r="0.1", why=" ")):
            with pytest.raises(sa.exc.IntegrityError):
                with engine.begin() as conn:
                    conn.execute(sa.text(sql))
        command.downgrade(cfg, PRIOR)  # empty table: a clean rollback
        assert set(sa.inspect(engine).get_table_names()) == before_tables
        command.upgrade(cfg, REVISION)
        with engine.begin() as conn:
            conn.execute(sa.text("INSERT INTO suppliers (code, legal_name, status, demo_synthetic, created_at) VALUES "
                                 "('S1', 'Synthetic', 'ACTIVE', 1, '2026-11-24')"))
            conn.execute(sa.text(
                "INSERT INTO pricing_markup_overrides (organization_id, scope, supplier_id, markup_rate, reason, "
                "effective_from, created_at, actor_user_id, actor_name) VALUES ('ORG-001','SUPPLIER',1,0.1,'r',"
                "'2026-11-24','2026-11-24',1,'O')"))
        for sql in ("UPDATE pricing_markup_overrides SET markup_rate = 0.5", "DELETE FROM pricing_markup_overrides"):
            with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
                with engine.begin() as conn:
                    conn.execute(sa.text(sql))
        with pytest.raises(RuntimeError, match="pre-migration backup"):
            command.downgrade(cfg, PRIOR)
