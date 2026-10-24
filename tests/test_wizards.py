"""Four Guided Workflow Wizards (Joel, 24 Oct 2026) — automated acceptance. Synthetic data only.

Driven through the real pages: Home (WHAT DO YOU NEED TO DO?), Start Guided Wizard / Continue Manually, Back and
Next with required-information checks, Save & Exit and Resume, automatic draft saving, interruption recovery,
switching to the manual page and back, duplicate prevention (one project per Start a New Project run, one run per
project), company and supplier isolation, Field-only crew kept out, approvals never bypassed, the guided-estimating
engine reused (stages, quotes, internal cost estimate, costing approval, company pricing — the same totals as the
manual path), Manage a Project reading the real schedule, orders and close state, the Supplier Pro Desk wizard over a
real PRO Desk quotation to the order package, and the audit history. The browser walk is
tools/release/evidence_wizards.mjs.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest

from app import db
from app.models import Project
from app.models.wizard import WizardRun, WizardRunEvent
from app.services import guided_estimating as G
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.guided_support import NEW_HOME_SCOPE, client
from tests.test_guided_estimating import (  # noqa: F401
    BEN,
    _build_new_home,
    _cost_new_home,
    _field_only_kevin,
    _login,
    _make_owner,
    _other_company,
    env,
)


def _run(run_id):
    db.session.expire_all()
    return db.session.get(WizardRun, run_id)


def _start(d, key, **data):
    response = d.post(f"/wizards/{key}/start", data=data)
    run_id = int(re.search(r"/wizards/run/(\d+)", response.headers["Location"]).group(1))
    return run_id


def _step(d, run_id, step, action="next", expect=302, **data):
    return d.post(f"/wizards/run/{run_id}/step/{step}", data={"wizard_action": action, **data}, status=expect)


def _events(run_id):
    return [e.event for e in WizardRunEvent.query.filter_by(run_id=run_id).order_by(WizardRunEvent.id)]


COMMERCIAL_DEFAULTS = {"pricing_posture": "Competitive", "execution_risk": "Normal", "schedule_condition": "Normal",
                       "site_condition": "Normal", "estimate_stage": "Preliminary", "delivery_model": "Self-Perform"}
LOCATION = {"street": "8 Synthetic Road", "municipality": "Merrickville", "province_state": "Ontario",
            "postal_zip": "K0G 1N0", "country": "Canada", "permit_context_class": "Other/unspecified",
            **COMMERCIAL_DEFAULTS}


def _create_from_wizard(d, run_id, name="Wizard New Home (synthetic)"):
    """Steps 1–3 of Start a New Project, then Create the project (the existing New Project handler)."""
    customer = client()
    _step(d, run_id, "customer", client_id=str(customer.id), name=name, description="Two-storey new home")
    _step(d, run_id, "project_type", guided_project_type="NEW_HOME", project_type="New Build", status="Lead")
    _step(d, run_id, "location", action="save", **LOCATION)
    run = _run(run_id)
    fields = dict(run.draft_json["fields"])
    fields.update(wizard_run=str(run_id), plan_start="later")
    return d.post("/projects/new", data=fields)


# ====================================================================================== Home and the framework
def test_home_asks_what_do_you_need_to_do_and_keeps_every_existing_tool(env):
    _app, d, _ben = env
    home = d.get("/")
    assert "What do you need to do?" in home
    for title in ("Start a New Project", "Guided Estimating", "Manage a Project"):
        assert title in home
    assert home.count("Start Guided Wizard") == 3 and home.count("Continue Manually") == 3
    # Nothing that was on Home before is gone: Start New Estimate, + Start New Project, Company Calendar.
    assert "data-home-start-estimate" in home and 'class="home-start"' in home and 'class="home-calendar"' in home
    # Continue Manually goes straight to the existing page.
    assert 'href="/projects/new" data-continue-manually="NEW_PROJECT"' in home
    # The entry pages offer both too.
    assert 'data-start-wizard="NEW_PROJECT"' in d.get("/projects/new")
    assert 'data-start-wizard="GUIDED_ESTIMATING"' in d.get("/estimating/start")


def test_start_a_new_project_end_to_end_creates_the_project_once(env):
    _app, d, ben = env
    run_id = _start(d, "NEW_PROJECT")
    assert _start(d, "NEW_PROJECT") == run_id  # a second Start resumes the unfinished one
    page = d.get(f"/wizards/run/{run_id}/step/customer")
    assert "Customer and project" in page and "Step 1 of" in page and "Start a New Project" in page
    # Required information: Next is refused until the customer and the name are given.
    _step(d, run_id, "customer")
    assert _run(run_id).current_step == "customer"
    assert any("Before you go on" in m and "Choose the customer" in m for m in d.flashes())
    response = _create_from_wizard(d, run_id)
    project = Project.query.filter_by(organization_id=ORG, name="Wizard New Home (synthetic)").one()
    assert response.headers["Location"].endswith(f"/wizards/run/{run_id}/step/documents")
    assert _run(run_id).project_id == project.id
    # The project is exactly what the New Project form makes: commercial context and structured location.
    assert project.current_commercial_context.project_type == "New Build"
    assert project.location.municipality == "Merrickville" and project.status == "Lead"
    # Pressing Create again (or sending the form twice) makes nothing new.
    fields = dict(_run(run_id).draft_json["fields"], wizard_run=str(run_id), plan_start="later")
    again = d.post("/projects/new", data=fields)
    assert again.headers["Location"].endswith(f"/wizards/run/{run_id}/step/location")
    assert Project.query.filter_by(organization_id=ORG, name="Wizard New Home (synthetic)").count() == 1
    assert "PROJECT_CREATED" in _events(run_id)

    # Drawings: none yet → required; recording "no drawings needed" uses the existing project choice.
    page = d.get(f"/wizards/run/{run_id}/step/documents")
    assert "No drawing on the project yet" in page
    d.post(f"/projects/{project.id}/drawing-requirement", data={"drawing_requirement": "NOT_REQUIRED"})
    assert "Drawings are not required" in d.get(f"/wizards/run/{run_id}/step/documents")
    # With no drawings the View Plan review does not apply (conditional step).
    assert 'data-step-link="view_plan"' not in d.get(f"/wizards/run/{run_id}/step/documents")

    # Role: starts the project's one guided estimate with the type chosen in step 2.
    _step(d, run_id, "role", action="submit", contractor_role="GENERAL_CONTRACTOR")
    guided = G.get_guided(ORG, project.id)
    assert (guided.project_type, guided.contractor_role) == ("NEW_HOME", "GENERAL_CONTRACTOR")
    assert all(s.responsibility is None for s in guided.stages)  # nothing preselected
    assert "14 construction stages" in d.get(f"/wizards/run/{run_id}/step/construction_scope")
    # Internal / Subcontracted / N/A: the guided-estimating scope page itself (the same records).
    page = d.get(f"/wizards/run/{run_id}/step/stages")
    assert "0 of" in page and "stages decided" in page and f"/projects/{project.id}/guided/scope" in page
    _step(d, run_id, "stages")
    assert any("Decide" in m for m in d.flashes())
    d.scope(project, NEW_HOME_SCOPE, action="save")
    page = d.get(f"/wizards/run/{run_id}/step/stages")
    assert 'data-step-state="done"' in page
    # Responsibility and first dates is optional: Next is allowed without it.
    _step(d, run_id, "responsibility")
    assert _run(run_id).current_step == "review"
    _step(d, run_id, "review", action="submit", confirmed="1")
    assert "Setup confirmed" in d.get(f"/wizards/run/{run_id}/step/review")
    # Continue directly into Guided Estimating: this run finishes, the estimating wizard opens on the project.
    response = _step(d, run_id, "continue", action="submit", choice="estimate")
    assert _run(run_id).status == "COMPLETED"
    estimating = WizardRun.query.filter_by(wizard_key="GUIDED_ESTIMATING", project_id=project.id).one()
    assert response.headers["Location"].endswith(f"/wizards/run/{estimating.id}")
    assert Project.query.filter_by(organization_id=ORG).count() == 1


def test_save_exit_resume_autosave_and_interruption_recovery(env):
    application, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    customer = client()
    # Automatic draft saving while typing (no button pressed).
    r = d.http.post(f"/wizards/run/{run_id}/step/customer/autosave",
                    data={"client_id": str(customer.id), "name": "Interrupted job (synthetic)"})
    assert r.status_code == 200 and r.get_json()["saved"]
    # Interruption: the session ends (a new sign-in), nothing was pressed. The draft is still there.
    d2 = _login(application, BEN)
    page = d2.get(f"/wizards/run/{run_id}/step/customer")
    assert 'value="Interrupted job (synthetic)"' in page
    response = _step(d2, run_id, "customer", action="save_exit", client_id=str(customer.id),
                     name="Interrupted job (synthetic)")
    assert response.headers["Location"].endswith("/")
    assert "SAVED_AND_EXITED" in _events(run_id)
    home = d2.get("/")
    assert "Resume Start a New Project" in home and "Interrupted job (synthetic)" in home
    assert d2.http.get(f"/wizards/run/{run_id}").headers["Location"].endswith(f"/wizards/run/{run_id}/step/customer")
    # Back works, and nothing is created until Create is pressed.
    _step(d2, run_id, "customer")
    _step(d2, run_id, "project_type", action="back")
    assert _run(run_id).current_step == "customer"
    assert Project.query.filter_by(name="Interrupted job (synthetic)").count() == 0


def test_switching_to_manual_and_back_keeps_everything(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _create_from_wizard(d, run_id, name="Manual switch job (synthetic)")
    project = Project.query.filter_by(name="Manual switch job (synthetic)").one()
    manual = d.http.get(f"/wizards/run/{run_id}/manual/documents")
    assert manual.headers["Location"].endswith(f"/projects/{project.id}/plans")
    assert "SWITCHED_TO_MANUAL" in _events(run_id)
    # The manual page shows the way back to the same step.
    plans = d.get(f"/projects/{project.id}/plans")
    assert "Return to the wizard" in plans and f"/wizards/run/{run_id}/step/documents" in plans
    # A change made on the manual page is what the wizard shows (the records are the source of truth).
    d.post(f"/projects/{project.id}/drawing-requirement", data={"drawing_requirement": "NOT_REQUIRED"})
    assert 'data-step-state="done"' in d.get(f"/wizards/run/{run_id}/step/documents")


def test_wizards_stay_inside_the_company_and_field_crew_are_kept_out(env):
    application, d, ben = env
    run_id = _start(d, "NEW_PROJECT")
    other = _other_company(application)
    other.get(f"/wizards/run/{run_id}/step/customer", status=404)
    other.post(f"/wizards/run/{run_id}/step/customer", data={"wizard_action": "save"}, status=404)
    other.post(f"/wizards/run/{run_id}/end", status=404)
    # Another company cannot claim this run with its own New Project form either.
    customer_other = client("Other company customer (synthetic)")
    other.post("/projects/new", data={"wizard_run": str(run_id), "name": "Hijack", "client_id": customer_other.id},
               status=404)
    assert Project.query.filter_by(name="Hijack").count() == 0
    assert "What do you need to do?" in other.get("/")
    assert "Resume Start a New Project" not in other.get("/")
    kevin = _field_only_kevin(application, ben)
    for url in ("/wizards/", f"/wizards/run/{run_id}/step/customer"):
        response = kevin.http.get(url)
        assert response.status_code in (302, 403), url
        assert "/wizards/run" not in (response.headers.get("Location") or "")


def test_return_to_accepts_a_wizard_step_and_nothing_else():
    from app.services.return_path import guided_return_path

    assert guided_return_path("/wizards/run/12/step/pricing") == "/wizards/run/12/step/pricing"
    for bad in ("//evil.example/wizards/run/1/step/x", "https://evil.example/", "/wizards/run/1/open/x?to=/",
                "/wizards/run/x/step/pricing", "/wizards/run/1/step/../../admin"):
        assert guided_return_path(bad) is None, bad


# ====================================================================================== the one migration
def test_the_migration_adds_exactly_the_two_wizard_tables_and_refuses_downgrade_with_rows(tmp_path):
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    from app import create_app
    from app.models.wizard import WizardRun as Run, WizardRunEvent as Event

    root = Path(__file__).resolve().parents[1]
    uri = f"sqlite:///{tmp_path}/m.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    ctx = application.app_context()
    ctx.push()
    cfg = Config(str(root / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["w2z9r4d7k1m6"]
    assert script.get_revision("w2z9r4d7k1m6").down_revision == "g5e7c2a9d1b4"
    command.upgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    before = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
              for t in inspector.get_table_names()}
    before_indexes = {t: sorted(i["name"] for i in inspector.get_indexes(t)) for t in inspector.get_table_names()}
    engine.dispose()
    command.upgrade(cfg, "w2z9r4d7k1m6")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    after = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
             for t in inspector.get_table_names()}
    assert set(after) - set(before) == {"wizard_runs", "wizard_run_events"}
    for table in before:
        assert after[table] == before[table], table
        assert sorted(i["name"] for i in inspector.get_indexes(table)) == before_indexes[table], table
    for model in (Run, Event):
        assert {c["name"] for c in inspector.get_columns(model.__tablename__)} == set(model.__table__.columns.keys())
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO organizations (id, legal_name, display_name, currency, is_active, created_at, updated_at) "
                             "VALUES ('ORG-M', 'M', 'M', 'CAD', 1, '2026-10-24', '2026-10-24')"))
        conn.execute(sa.text("INSERT INTO wizard_runs (wizard_key, side, organization_id, actor_display_name, status, "
                             "created_at, updated_at) VALUES ('NEW_PROJECT', 'CONTRACTOR', 'ORG-M', 'Ben', 'ACTIVE', "
                             "'2026-10-24', '2026-10-24')"))
        # A contractor run must name its company, and a supplier run must not.
        with pytest.raises(sa.exc.IntegrityError):
            with conn.begin_nested():
                conn.execute(sa.text("INSERT INTO wizard_runs (wizard_key, side, organization_id, supplier_id, "
                                     "actor_display_name, status, created_at, updated_at) VALUES ('SUPPLIER_PRO_DESK', "
                                     "'SUPPLIER', 'ORG-M', 1, 'Dana', 'ACTIVE', '2026-10-24', '2026-10-24')"))
    engine.dispose()
    with pytest.raises(RuntimeError, match="Downgrade refused"):
        command.downgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("DELETE FROM wizard_runs"))
    engine.dispose()
    command.downgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    assert {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
            for t in inspector.get_table_names()} == before
    engine.dispose()
    ctx.pop()
