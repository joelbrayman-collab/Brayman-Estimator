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


SIGN = {"sign_consent": "yes", "signer_name": "Test Signer"}  # supplier Native Signing (FG-041): every order, confirmation and change asked on screen is signed


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


def _create_from_wizard(d, run_id, name="Wizard New Home (synthetic)", role="GENERAL_CONTRACTOR"):
    """Steps 1–3 of Start a New Project (Project, Customer, Details), then Create Project & Continue on Details (the
    existing New Project handler creates the project and starts its guided estimate with the role chosen there)."""
    customer = client()
    _step(d, run_id, "project_type", name=name, description="Two-storey new home", guided_project_type="NEW_HOME",
          project_type="New Build", status="Lead")
    _step(d, run_id, "customer", customer_mode="existing", client_id=str(customer.id))
    _step(d, run_id, "location", action="save", contractor_role=role, **LOCATION)
    run = _run(run_id)
    fields = {k: v for k, v in run.draft_json["fields"].items() if not k.startswith("new_customer_")}
    fields.update(wizard_run=str(run_id), plan_start="later")
    return d.post("/projects/new", data=fields)


# ====================================================================================== Home and the framework
def test_home_asks_what_do_you_need_to_do_and_keeps_every_existing_tool(env):
    _app, d, _ben = env
    home = d.get("/")
    # Home starts each guided wizard from one compact band (Project Creation UX, 27 Oct 2026): Start (primary) and
    # Continue manually, and the Company Calendar; no second set of start buttons.
    assert "Guided Wizards" in home and "What are Wizards?" in home
    for label in ("Start a New Project", "Estimate a Project", "Manage a Project"):
        assert label in home
    assert home.count("data-start-wizard=") == 3 and home.count(">Continue manually</a>") == 3
    for key in ("NEW_PROJECT", "GUIDED_ESTIMATING", "MANAGE_PROJECT"):
        assert f'href="/wizards/{key}/start" data-start-wizard="{key}">' in home
    # Nothing that was on Home before is gone: the New Project form, the estimate form, Company Calendar.
    assert home.count("data-home-start-estimate") == 1 and home.count('class="home-start') == 1
    assert home.count('class="home-calendar') == 1
    assert "+ Start New Project" not in home and "Start New Estimate" not in home  # the duplicates are gone
    # Continue Manually goes straight to the existing page.
    assert 'class="home-start hc-manual" href="/projects/new" data-continue-manually="NEW_PROJECT"' in home
    assert 'href="/estimating/start" data-continue-manually="GUIDED_ESTIMATING" data-home-start-estimate' in home
    # The entry pages offer both too.
    assert 'data-start-wizard="NEW_PROJECT"' in d.get("/projects/new")
    assert 'data-start-wizard="GUIDED_ESTIMATING"' in d.get("/estimating/start")


def test_start_a_new_project_end_to_end_creates_the_project_once(env):
    _app, d, ben = env
    run_id = _start(d, "NEW_PROJECT")
    assert _start(d, "NEW_PROJECT") == run_id  # a second Start resumes the unfinished one
    page = d.get(f"/wizards/run/{run_id}/step/project_type")
    assert "Step 1 of 5" in page and "Start a New Project" in page and 'role="dialog"' in page
    # The five steps across the top, in order (Compact Open a New Project, 28 Oct 2026).
    assert re.findall(r'data-step-link="(\w+)"', page) == ["project_type", "customer", "location", "documents",
                                                          "review"]
    # Required information: Save & Continue is refused until the project is named, then the customer is chosen.
    _step(d, run_id, "project_type")
    assert _run(run_id).current_step == "project_type"
    assert any("Before you go on" in m and "Name the project" in m for m in d.flashes())
    _step(d, run_id, "project_type", name="Wizard New Home (synthetic)", guided_project_type="NEW_HOME",
          project_type="New Build", status="Lead")
    assert _run(run_id).current_step == "customer"
    _step(d, run_id, "customer")
    assert _run(run_id).current_step == "customer"
    assert any("Before you go on" in m and "Choose the customer" in m for m in d.flashes())
    # Details refuses to create the project without your role; everything typed is kept.
    _step(d, run_id, "customer", customer_mode="existing", client_id=str(client().id))
    assert _run(run_id).current_step == "location"
    _step(d, run_id, "location", action="save", **LOCATION)
    fields = {k: v for k, v in _run(run_id).draft_json["fields"].items() if not k.startswith("new_customer_")}
    refused = d.post("/projects/new", data=dict(fields, wizard_run=str(run_id), plan_start="later"))
    assert refused.headers["Location"].endswith(f"/wizards/run/{run_id}/step/location")
    assert any("Choose your role" in m for m in d.flashes())
    assert Project.query.filter_by(organization_id=ORG, name="Wizard New Home (synthetic)").count() == 0
    assert _run(run_id).draft_json["fields"]["municipality"] == "Merrickville"
    response = _create_from_wizard(d, run_id)
    project = Project.query.filter_by(organization_id=ORG, name="Wizard New Home (synthetic)").one()
    assert response.headers["Location"].endswith(f"/wizards/run/{run_id}/step/documents")
    assert _run(run_id).project_id == project.id
    # The project is exactly what the New Project form makes: commercial context and structured location.
    assert project.current_commercial_context.project_type == "New Build"
    assert project.location.municipality == "Merrickville" and project.status == "Lead"
    # The role chosen on Details starts the project's one guided estimate, with the type chosen on Project.
    guided = G.get_guided(ORG, project.id)
    assert (guided.project_type, guided.contractor_role) == ("NEW_HOME", "GENERAL_CONTRACTOR")
    # Since 28 Oct 2026 the scope is the selected work: no stage list is made here.
    assert guided.stages == []
    # Pressing Create Project & Continue again (or sending the form twice) makes nothing new.
    fields = {k: v for k, v in _run(run_id).draft_json["fields"].items() if not k.startswith("new_customer_")}
    again = d.post("/projects/new", data=dict(fields, wizard_run=str(run_id), plan_start="later"))
    assert again.headers["Location"].endswith(f"/wizards/run/{run_id}/step/location")
    assert Project.query.filter_by(organization_id=ORG, name="Wizard New Home (synthetic)").count() == 1
    assert "PROJECT_CREATED" in _events(run_id)
    assert G.GuidedEstimate.query.filter_by(project_id=project.id).count() == 1

    # Plans: none yet; recording "no drawings needed" uses the existing project choice. Never blocking.
    page = d.get(f"/wizards/run/{run_id}/step/documents")
    assert "No drawings yet" in page
    d.post(f"/projects/{project.id}/drawing-requirement", data={"drawing_requirement": "NOT_REQUIRED"})
    assert "No drawings needed for this project" in d.get(f"/wizards/run/{run_id}/step/documents")
    _step(d, run_id, "documents")
    assert _run(run_id).current_step == "review"
    for retired in ("role", "responsibility", "construction_scope", "applicable", "stages", "view_plan", "continue"):
        assert f'data-step-link="{retired}"' not in page
    # Review: every section with Edit, then Finish (never "Create Project": it was created on Details).
    page = d.get(f"/wizards/run/{run_id}/step/review")
    assert "Wizard New Home (synthetic)" in page and "Create Project" not in page.split("data-step-form")[1]
    for key in ("project_type", "customer", "location", "documents"):
        assert f'data-review-edit="{key}"' in page
    assert "data-finish-project" in page
    # Finish: this run finishes and Project Created is shown (Open Project, Start Guided Estimating, Create Another).
    response = d.post(f"/wizards/run/{run_id}/step/review?choice=finish", data={"wizard_action": "next"})
    assert _run(run_id).status == "COMPLETED"
    assert "CONFIRMED" in _events(run_id)
    assert response.headers["Location"].endswith(f"/wizards/run/{run_id}/created")
    created = d.get(f"/wizards/run/{run_id}/created")
    assert "Project Created Successfully" in created and "Wizard New Home (synthetic)" in created
    assert f'href="/projects/{project.id}" data-open-project' in created
    assert "data-start-estimating" in created and "data-create-another" in created
    assert Project.query.filter_by(organization_id=ORG).count() == 1
    # Start Guided Estimating from there opens the estimating wizard on the project.
    started = d.post("/wizards/GUIDED_ESTIMATING/start", data={"project_id": str(project.id)})
    estimating = WizardRun.query.filter_by(wizard_key="GUIDED_ESTIMATING", project_id=project.id).one()
    assert started.headers["Location"].endswith(f"/wizards/run/{estimating.id}")


def test_save_exit_resume_autosave_and_interruption_recovery(env):
    application, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    customer = client()
    _step(d, run_id, "customer", customer_mode="existing", client_id=str(customer.id))
    # Automatic draft saving while typing (no button pressed).
    r = d.http.post(f"/wizards/run/{run_id}/step/project_type/autosave",
                    data={"name": "Interrupted job (synthetic)"})
    assert r.status_code == 200 and r.get_json()["saved"]
    # Interruption: the session ends (a new sign-in), nothing was pressed. The draft is still there.
    d2 = _login(application, BEN)
    page = d2.get(f"/wizards/run/{run_id}/step/project_type")
    assert 'value="Interrupted job (synthetic)"' in page
    response = _step(d2, run_id, "project_type", action="save_exit", name="Interrupted job (synthetic)")
    assert response.headers["Location"].endswith("/")
    assert "SAVED_AND_EXITED" in _events(run_id)
    home = d2.get("/")
    assert "Resume Start a New Project" in home and "Interrupted job (synthetic)" in home
    assert d2.http.get(f"/wizards/run/{run_id}").headers["Location"].endswith(f"/wizards/run/{run_id}/step/project_type")
    # Back works, and nothing is created until Create Project & Continue on Details.
    back = _step(d2, run_id, "customer", action="back")
    assert back.headers["Location"].endswith(f"/wizards/run/{run_id}/step/project_type")
    d2.get(f"/wizards/run/{run_id}/step/customer")
    assert _run(run_id).current_step == "customer"
    assert 'value="Interrupted job (synthetic)"' in d2.get(f"/wizards/run/{run_id}/step/project_type")
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
    assert "Guided Wizards" in other.get("/")
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
def test_the_migration_adds_exactly_the_two_wizard_tables_and_the_project_lead_column(tmp_path):
    """w2z9r4d7k1m6 is the release's only migration: wizard_runs, wizard_run_events and the one nullable column
    projects.project_lead_user_id (decision 1). Every existing table's other columns, indexes and rows are unchanged.
    Downgrade refuses while a wizard table holds a row or any project has a Project Lead."""
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    from app import create_app
    from app.models.project import Project as ProjectModel
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
    assert script.get_heads() == ["r5e6f7a8b9c0"]
    assert script.get_revision("w2z9r4d7k1m6").down_revision == "g5e7c2a9d1b4"
    command.upgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    # Existing records before the migration: a company, a user, a client and a project.
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO organizations (id, legal_name, display_name, currency, is_active, created_at, "
                             "updated_at) VALUES ('ORG-M', 'M', 'M', 'CAD', 1, '2026-10-24', '2026-10-24')"))
        conn.execute(sa.text("INSERT INTO users (id, email, display_name, password_hash, is_active, created_at, updated_at) "
                             "VALUES (7, 'lead@example.invalid', 'Lee Lead', 'x', 1, '2026-10-24', '2026-10-24')"))
        conn.execute(sa.text("INSERT INTO clients (id, name, organization_id, created_at) "
                             "VALUES (3, 'Synthetic Client', 'ORG-M', '2026-10-24')"))
        conn.execute(sa.text("INSERT INTO projects (id, organization_id, name, status, client_id, created_at, "
                             "operating_state, operating_state_changed_at, drawing_requirement) VALUES (5, 'ORG-M', "
                             "'Existing Job (synthetic)', 'Lead', 3, '2026-10-24', 'ACTIVE', '2026-10-24', 'UNKNOWN')"))
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    before = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)] for t in tables}
    before_indexes = {t: sorted(i["name"] for i in inspector.get_indexes(t)) for t in tables}
    with engine.connect() as conn:
        before_rows = {t: conn.execute(sa.text(f'SELECT * FROM "{t}" ORDER BY rowid')).fetchall() for t in tables
                       if t != "alembic_version"}
    engine.dispose()
    command.upgrade(cfg, "w2z9r4d7k1m6")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    after = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
             for t in inspector.get_table_names()}
    assert set(after) - set(before) == {"wizard_runs", "wizard_run_events"}
    for table in before:
        if table == "projects":
            # Exactly one new column, nullable, at the end; every other column as it was.
            assert after[table][:-1] == before[table]
            assert after[table][-1] == ("project_lead_user_id", "INTEGER", True)
            assert sorted(i["name"] for i in inspector.get_indexes(table)) == sorted(
                before_indexes[table] + ["ix_projects_project_lead_user_id"])
            fks = [fk for fk in inspector.get_foreign_keys(table) if fk["constrained_columns"] == ["project_lead_user_id"]]
            assert len(fks) == 1 and fks[0]["referred_table"] == "users" and fks[0]["referred_columns"] == ["id"]
            continue
        assert after[table] == before[table], table
        assert sorted(i["name"] for i in inspector.get_indexes(table)) == before_indexes[table], table
    for model in (Run, Event, ProjectModel):
        assert {c["name"] for c in inspector.get_columns(model.__tablename__)} == set(model.__table__.columns.keys())
    with engine.connect() as conn:
        for table, rows in before_rows.items():
            if table == "projects":
                columns = ", ".join(c[0] for c in before["projects"])
                assert conn.execute(sa.text(f"SELECT {columns} FROM projects ORDER BY rowid")).fetchall() == rows
                # The existing project starts unassigned.
                assert conn.execute(sa.text("SELECT project_lead_user_id FROM projects")).fetchall() == [(None,)]
            else:
                assert conn.execute(sa.text(f'SELECT * FROM "{table}" ORDER BY rowid')).fetchall() == rows, table
    with engine.begin() as conn:
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
    with pytest.raises(RuntimeError, match="Downgrade refused: wizard_runs holds rows"):
        command.downgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("DELETE FROM wizard_runs"))
        conn.execute(sa.text("UPDATE projects SET project_lead_user_id = 7 WHERE id = 5"))
    engine.dispose()
    with pytest.raises(RuntimeError, match="Downgrade refused: a project has a Project Lead"):
        command.downgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("UPDATE projects SET project_lead_user_id = NULL"))
    engine.dispose()
    command.downgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    assert {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
            for t in inspector.get_table_names()} == before
    assert sorted(i["name"] for i in inspector.get_indexes("projects")) == before_indexes["projects"]
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT * FROM projects ORDER BY rowid")).fetchall() == before_rows["projects"]
    engine.dispose()
    ctx.pop()


# ====================================================================================== Guided Estimating
def _state(d, run_id, step):
    page = d.get(f"/wizards/run/{run_id}/step/{step}")
    return re.search(r'data-step-state="(\w+)"', page).group(1), page


def _accept_and_build(d, project):
    """The customer accepts through the existing proposal services; the work plan is seeded from the estimate."""
    from app.services.estimates import lock_version
    from app.services.proposals import create_proposal, create_proposal_template, update_proposal_status
    from app.services.work_structure import seed_project_work_structure

    version = G.current_version(G.get_guided(ORG, project.id))
    template = create_proposal_template(name="Synthetic standard", organization_id=ORG, is_default=True)
    proposal = create_proposal(estimate=version.estimate, version=version, template=template, organization_id=ORG)
    update_proposal_status(proposal, "Issued")
    update_proposal_status(proposal, "Accepted")
    lock_version(version)
    seed_project_work_structure(project_id=project.id, estimate_version_id=version.id, seeded_by=BEN[2],
                                organization_id=ORG)
    return proposal


def test_guided_estimating_wizard_walks_the_v1rel9_engine_and_prices_like_the_manual_path(env):
    _app, d, ben = env
    project = _build_new_home(d)  # New Project and the 14-stage scope, finalized on the scope page
    run_id = _start(d, "GUIDED_ESTIMATING", project_id=str(project.id))
    assert _start(d, "GUIDED_ESTIMATING", project_id=str(project.id)) == run_id  # one run per project
    assert WizardRun.query.filter_by(wizard_key="GUIDED_ESTIMATING", project_id=project.id).count() == 1
    assert _state(d, run_id, "project")[0] == "done"
    assert _state(d, run_id, "type_role")[0] == "done"
    state, page = _state(d, run_id, "scope")
    assert state == "done" and "5 internal, 9 subcontracted, 0 N/A" in page
    state, page = _state(d, run_id, "internal")
    assert state == "todo" and "0 of 5 internal stages complete" in page
    # "Open existing calculators automatically": the next stage's calculator opens with project and stage chosen.
    assert "Footing calculator for Footings" in page and f"to=/calculators/footing?project%3D{project.id}%26stage%3D" in page
    state, page = _state(d, run_id, "select_quotes")
    assert state == "todo" and "0 of 9 subcontracted stages complete" in page
    # A required step that is not done holds Next and says why.
    r = _step(d, run_id, "internal")
    assert r.headers["Location"].endswith(f"/wizards/run/{run_id}/step/internal")
    assert any("Before you go on" in m and "Complete each internal stage" in m for m in d.flashes())
    # The pricing step offers no approval while stages are unresolved (no approval bypass).
    state, page = _state(d, run_id, "pricing")
    assert state == "todo" and 'data-wizard-action="approve-costing"' not in page

    _cost_new_home(d, project)  # Ben costs every stage on the stage pages (the engine itself)
    for step in ("quantities", "internal", "request_quotes", "select_quotes", "internal_cost"):
        assert _state(d, run_id, step)[0] == "done", step
    state, page = _state(d, run_id, "costs")
    assert state == "info" and "Subcontractors" in page and "Allowances" in page
    guided = G.get_guided(ORG, project.id)
    doc = G.internal_cost_document(guided)
    assert f"${doc['direct_cost']:,.2f}" in _state(d, run_id, "internal_cost")[1]

    # Approve the costing and apply the company pricing from the wizard: the existing endpoints, back to the step.
    version = G.current_version(guided)
    back = f"/wizards/run/{run_id}/step/pricing"
    r = d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/approve-all-costing", data={"return_to": back})
    assert r.headers["Location"].endswith(back)
    assert 'data-wizard-action="apply-pricing"' in d.get(back)
    r = d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/apply-org-pricing", data={"return_to": back})
    assert r.headers["Location"].endswith(back)
    db.session.expire_all()
    snapshot = G.current_version(G.get_guided(ORG, project.id)).pricing_snapshot
    # The same price the manual path gives (true gross margin 15 %, HST 13 %), from the same records.
    expected_sell = (doc["direct_cost"] / Decimal("0.85")).quantize(Decimal("0.01"))
    assert snapshot.direct_cost_basis == doc["direct_cost"]
    assert abs(snapshot.pre_tax_selling_price - expected_sell) <= Decimal("0.01")
    state, page = _state(d, run_id, "pricing")
    assert state == "done" and "15.0%" in page and f"${snapshot.customer_total:,.2f}" in page

    assert _state(d, run_id, "proposal")[0] == "todo"
    assert _state(d, run_id, "acceptance")[0] == "todo"
    proposal = _accept_and_build(d, project)
    state, page = _state(d, run_id, "proposal")
    assert state == "done" and proposal.proposal_number in page
    state, page = _state(d, run_id, "acceptance")
    assert state == "done" and "5 work items" in page
    # Finish into Manage a Project.
    response = _step(d, run_id, "acceptance", action="submit", choice="manage")
    manage = WizardRun.query.filter_by(wizard_key="MANAGE_PROJECT", project_id=project.id).one()
    assert response.headers["Location"].endswith(f"/wizards/run/{manage.id}")
    assert _run(run_id).status == "COMPLETED"


# ====================================================================================== Manage a Project
def test_manage_a_project_reads_the_real_schedule_people_orders_changes_and_close(env):
    application, d, ben = env
    project = _build_new_home(d)
    _cost_new_home(d, project)
    guided = G.get_guided(ORG, project.id)
    version = G.current_version(guided)
    d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/approve-all-costing", data={})
    d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/apply-org-pricing", data={})
    # Only accepted projects are offered.
    run_id = _start(d, "MANAGE_PROJECT")
    assert project.name not in _state(d, run_id, "project")[1]
    _accept_and_build(d, project)
    assert project.name in _state(d, run_id, "project")[1]
    _step(d, run_id, "project", action="submit", project_id=str(project.id))
    assert _run(run_id).project_id == project.id
    state, page = _state(d, run_id, "scope_contract")
    assert state == "todo" and "no contract yet" in page
    state, page = _state(d, run_id, "schedule")
    assert state == "todo" and "0 of 5 work items scheduled" in page
    # Schedule one work item on the existing work schedule: the wizard counts it.
    from datetime import timedelta

    from app.services.local_time import local_today
    from app.services.schedule import assign_user, create_schedule_item
    from app.services.work_structure import list_project_work_elements

    elements = list_project_work_elements(project.id, organization_id=ORG)
    start = local_today() + timedelta(days=7)
    item = create_schedule_item(project_id=project.id, project_work_element_id=elements[0].id,
                                scheduled_start=start, scheduled_end=start + timedelta(days=2), organization_id=ORG)
    assert "1 of 5 work items scheduled" in _state(d, run_id, "schedule")[1]
    state, page = _state(d, run_id, "people")
    assert state == "todo" and "0 of 1 scheduled item assigned" in page
    assert "Schedule-change texts to workers" in page  # the real switch, not assumed on
    assign_user(item.id, worker_user_id=ben.id, organization_id=ORG)
    state, page = _state(d, run_id, "people")
    assert state == "done", re.findall(r"data-item-state=\"(\w+)\".{0,400}", page, re.S)
    # Features not switched on show their real status.
    page = _state(d, run_id, "progress")[1]
    assert "QuickBooks Time" in page and "Not switched on" in page
    # No supplier request yet on a job with lines the company buys: the step says so (no invented order).
    state, page = _state(d, run_id, "orders")
    assert "No supplier request on this project" in page
    # Changes: none open.
    state, page = _state(d, run_id, "changes")
    assert state == "done", re.search(r"data-step-headline>(.*?)</div>", page, re.S).group(1)
    # Close: only the owner or a System Administrator gets the button; the close route itself enforces it.
    state, page = _state(d, run_id, "close")
    assert 'data-wizard-action="close-project"' not in page and "Only the owner" in page
    _make_owner(ben)
    assert 'data-wizard-action="close-project"' in _state(d, run_id, "close")[1]
    d.post(f"/projects/{project.id}/close", data={})
    db.session.expire_all()
    assert db.session.get(Project, project.id).operating_state == "CLOSED"
    state, page = _state(d, run_id, "close")
    assert state == "done" and "records are kept" in page


def test_multiple_active_projects_each_keep_their_own_wizard(env):
    _app, d, _ben = env
    first = _build_new_home(d)
    second, _loc = d.new_project("Second synthetic home", "GARAGE_OUTBUILDING", "GENERAL_CONTRACTOR")
    a = _start(d, "GUIDED_ESTIMATING", project_id=str(first.id))
    b = _start(d, "GUIDED_ESTIMATING", project_id=str(second.id))
    assert a != b
    _step(d, a, "scope", action="save_exit")
    _step(d, b, "type_role", action="save_exit")
    home = d.get("/")
    assert "Avery New Home (synthetic)" in home and "Second synthetic home" in home
    assert _run(a).current_step == "scope" and _run(b).current_step == "type_role"
    # Choosing a project that already has an open wizard resumes it instead of making a second one.
    c = _start(d, "GUIDED_ESTIMATING")
    r = _step(d, c, "project", action="submit", project_id=str(first.id))
    assert r.headers["Location"].endswith(f"/wizards/run/{a}") and _run(c).status == "ENDED"
    assert WizardRun.query.filter_by(wizard_key="GUIDED_ESTIMATING", project_id=first.id, status="ACTIVE").count() == 1


# ====================================================================================== Supplier Pro Desk
@pytest.fixture()
def hub(tmp_path):
    """The Darcy Supplier Hub seed (tests/supplier_hub_page_server.py): BMR (synthetic), a rival supplier, two deck
    projects, and an earlier request Darcy quoted and the office recorded."""
    from app import create_app
    from tests import supplier_hub_page_server as S

    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/hub.db",
                              "SECRET_KEY": "k", "TRANSACTIONAL_EMAIL_PROVIDER": "local", "WTF_CSRF_ENABLED": False,
                              "DECK_TAKEOFF_ROOT": f"{tmp_path}/deck_takeoff"})
    with application.app_context():
        db.create_all()
        facts = S.seed_records()
    facts.update(S.seed_flow(application, facts))
    application.config["WTF_CSRF_ENABLED"] = False
    ctx = application.app_context()
    ctx.push()
    yield application, facts, S
    db.session.remove()
    ctx.pop()


def _supplier_login(application, email, password):
    from tests.guided_support import Driver

    d = Driver(application.test_client())
    d.post("/supplier/login", data={"email": email, "password": password})
    return d


def _office_login(application):
    from tests.guided_support import Driver

    d = Driver(application.test_client())
    d.post("/login", data={"email": "office@example.com", "password": "office-test-password"})
    return d


def _sstate(d, sid, run_id, step):
    page = d.get(f"/supplier/{sid}/wizards/run/{run_id}/step/{step}")
    return re.search(r'data-step-state="(\w+)"', page).group(1), page


def test_supplier_pro_desk_wizard_follows_a_contractor_request_to_delivery(hub):
    application, facts, S = hub
    from app.models.supplier_portal import SupplierPurchaseOrder, SupplierRequestShare
    from app.services.local_time import local_today
    from datetime import timedelta

    sid, share_id = facts["bmr_id"], facts["earlier_share_id"]
    darcy = _supplier_login(application, S.DARCY[1], S.DARCY[2])
    inbox = darcy.get(f"/supplier/{sid}/")
    assert "What do you need to do?" in inbox and 'data-start-wizard="SUPPLIER_PRO_DESK"' in inbox
    r = darcy.post(f"/supplier/{sid}/wizards/start", data={"share_id": share_id})
    run_id = int(re.search(r"/wizards/run/(\d+)", r.headers["Location"]).group(1))
    assert darcy.post(f"/supplier/{sid}/wizards/start", data={"share_id": share_id}).headers["Location"] == r.headers["Location"]
    state, page = _sstate(darcy, sid, run_id, "who")
    assert state == "done" and "delivery town" in page.lower()
    # The contractor's internal figures never reach the supplier's wizard.
    for step in ("who", "documents", "quantities", "pricing", "send", "responses", "order", "delivery", "close"):
        page = _sstate(darcy, sid, run_id, step)[1]
        for secret in (S.INTERNAL_COST[1], S.INTERNAL_COST[2], "8,765.43", S.PROJECT, S.CLIENT):
            assert secret not in page, (step, secret)
    assert _sstate(darcy, sid, run_id, "send")[0] == "done"           # Darcy returned the quote
    assert _sstate(darcy, sid, run_id, "availability")[0] == "na"     # not part of the contractor request form
    state, page = _sstate(darcy, sid, run_id, "order")
    assert state == "waiting" and "Only the contractor places the order" in page
    # The office approves and orders on its own page (the supplier cannot).
    office = _office_login(application)
    share = db.session.get(SupplierRequestShare, share_id)
    from app.services.deck_takeoff import storage

    follow = next(x for x in storage.list_responses(ORG, share.project_id) if x.get("records_response") == share.response_ref)
    for result in follow["results"]:
        if result.get("recorded"):
            office.post(f"/projects/{share.project_id}/deck-takeoff/responses/{share.response_ref}/approve",
                        data={"canonical_material_id": result["canonical_material_id"], "status": "APPROVED"})
    office.post(f"/projects/{share.project_id}/supplier-requests/{share_id}/order",
                data={**SIGN, "delivery_date": (local_today() + timedelta(days=12)).isoformat(), "site_contact": "Ben"})
    order = SupplierPurchaseOrder.query.filter_by(share_id=share_id).first()
    assert order is not None, office.flashes()
    state, page = _sstate(darcy, sid, run_id, "order")
    assert state == "todo" and order.number in page and 'data-wizard-action="confirm-order"' in page
    darcy.post(f"/supplier/{sid}/orders/{order.id}/confirm",
               data={**SIGN, "action": "confirm", "expected_delivery": (local_today() + timedelta(days=12)).isoformat()})
    assert _sstate(darcy, sid, run_id, "order")[0] == "done"
    assert _sstate(darcy, sid, run_id, "delivery")[0] == "waiting"
    assert _sstate(darcy, sid, run_id, "close")[0] == "todo"
    darcy.post(f"/supplier/{sid}/orders/{order.id}/delivered", data={"delivered_on": local_today().isoformat()})
    state, page = _sstate(darcy, sid, run_id, "close")
    assert state == "done" and "history are kept" in page
    finish = darcy.post(f"/supplier/{sid}/wizards/run/{run_id}/step/close", data={"wizard_action": "finish"})
    assert finish.headers["Location"].endswith(f"/supplier/{sid}/")
    assert db.session.get(WizardRun, run_id).status == "COMPLETED"


def test_supplier_wizards_are_isolated_from_other_suppliers_and_the_office(hub):
    application, facts, S = hub
    sid, rival_id = facts["bmr_id"], facts["rival_id"]
    darcy = _supplier_login(application, S.DARCY[1], S.DARCY[2])
    r = darcy.post(f"/supplier/{sid}/wizards/start", data={"share_id": facts["earlier_share_id"]})
    run_id = int(re.search(r"/wizards/run/(\d+)", r.headers["Location"]).group(1))
    rival = _supplier_login(application, S.RIVAL[1], S.RIVAL[2])
    # Another supplier: not its area, not its run, and it cannot start a run on Darcy's request.
    rival.get(f"/supplier/{sid}/wizards/run/{run_id}/step/who", status=404)
    rival.get(f"/supplier/{rival_id}/wizards/run/{run_id}/step/who", status=404)
    rival.post(f"/supplier/{rival_id}/wizards/start", data={"share_id": facts["earlier_share_id"]}, status=404)
    # Darcy cannot pick the rival's request in the wizard either.
    mine = darcy.post(f"/supplier/{sid}/wizards/start", data={})
    blank = int(re.search(r"/wizards/run/(\d+)", mine.headers["Location"]).group(1))
    page = darcy.get(f"/supplier/{sid}/wizards/run/{blank}/step/open")
    assert facts["rival_number"] not in page
    darcy.post(f"/supplier/{sid}/wizards/run/{blank}/step/open",
               data={"wizard_action": "submit", "record": f"share:{facts['rival_share_id']}"})
    assert db.session.get(WizardRun, blank).supplier_share_id is None
    assert any("Not found" in m for m in darcy.flashes())
    # The office cannot open supplier wizard pages, and a supplier is sent away from the office wizards.
    office = _office_login(application)
    assert office.http.get(f"/supplier/{sid}/wizards/run/{run_id}/step/who").status_code == 403
    assert darcy.http.get("/wizards/").status_code == 302
    # Ask the Tutor from a supplier step answers from the step's own Help and changes nothing.
    answer = darcy.http.post(f"/supplier/{sid}/wizards/help", json={"key": "SUPPLIER_PRO_DESK.pricing",
                                                                    "question": "What do I do here?"}).get_json()
    assert answer["mutates"] is False and "price" in answer["answer"].lower()
    refused = darcy.http.post(f"/supplier/{sid}/wizards/help", json={"key": "NEW_PROJECT.customer", "question": "x"})
    assert "isn't available" in refused.get_json()["answer"]


@pytest.fixture()
def pro_desk(tmp_path):
    from app import create_app
    from tests.pro_desk_page_server import seed

    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/pd.db",
                              "SECRET_KEY": "k", "TRANSACTIONAL_EMAIL_PROVIDER": "local", "WTF_CSRF_ENABLED": False})
    ctx = application.app_context()
    ctx.push()
    db.create_all()
    facts = seed()
    yield application, facts
    db.session.remove()
    ctx.pop()


def test_supplier_pro_desk_wizard_quick_quote_to_order_package(pro_desk):
    application, store_facts = pro_desk
    from app.models.supplier_quote import SupplierQuote
    from app.services import supplier_pro_desk as P
    from tests.pro_desk_page_server import QUICK_FORM, STORE

    sid = store_facts["supplier_id"]
    store = _supplier_login(application, *STORE)
    r = store.post(f"/supplier/{sid}/wizards/start", data={})
    run_id = int(re.search(r"/wizards/run/(\d+)", r.headers["Location"]).group(1))
    state, page = _sstate(store, sid, run_id, "open")
    assert state == "todo" and 'data-wizard-action="quick-quote"' in page
    made = store.post(f"/supplier/{sid}/pro-desk/quick", data={
        "customer_name": "Pat Walk-in (synthetic)", "customer_phone": "613-555-0100", "customer_town": "Winchester",
        "demo_synthetic": "yes", "assembly_id": str(store_facts["standard_id"]), **QUICK_FORM})
    assert made.status_code == 302
    quote = SupplierQuote.query.filter_by(supplier_id=sid).order_by(SupplierQuote.id.desc()).first()
    assert quote.number in store.get(f"/supplier/{sid}/wizards/run/{run_id}/step/open")
    store.post(f"/supplier/{sid}/wizards/run/{run_id}/step/open", data={"wizard_action": "submit", "record": f"quote:{quote.id}"})
    assert db.session.get(WizardRun, run_id).supplier_quote_id == quote.id
    state, page = _sstate(store, sid, run_id, "availability")
    # From the price file's availability column (decision 3): the supplier's own statement, never a quantity.
    assert "priced lines have availability from your price file" in page
    assert "In stock (supplier-reported)" in page
    for row in P.price_quote(quote)["rows"]:
        if row["code"].startswith("CAL-OB-TRUSS"):
            store.post(f"/supplier/{sid}/pro-desk/{quote.id}/line", data={"code": row["code"], "exclude_reason": "Truss quote to follow"})
    assert _sstate(store, sid, run_id, "pricing")[0] == "done"
    assert "left out" in _sstate(store, sid, run_id, "substitutions")[1]
    assert _sstate(store, sid, run_id, "send")[0] == "todo"
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/issue")
    assert _sstate(store, sid, run_id, "send")[0] == "done"
    assert _sstate(store, sid, run_id, "responses")[0] == "waiting"
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/accept", data={"method": "in_person", "customer_name": "Pat Walk-in"})
    assert _sstate(store, sid, run_id, "responses")[0] == "done"
    state, page = _sstate(store, sid, run_id, "order")
    assert state == "todo" and 'data-wizard-action="order-ready"' in page
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/order-ready")
    assert _sstate(store, sid, run_id, "order")[0] == "done"
    assert "Arranged in the store&#39;s own system" in _sstate(store, sid, run_id, "delivery")[1]
    # Decision 2: a walk-in order is completed in the store's own system; never shown as picked up or delivered.
    state, page = _sstate(store, sid, run_id, "close")
    assert state == "info" and "pickup or delivery not confirmed in CalibraytAI" in page
    # The order package is the PRO Desk's own (no point-of-sale, inventory or rewards assumption).
    page = _sstate(store, sid, run_id, "pricing")[1]
    assert "No rewards or Pro Account points program" in page


# ====================================================================================== training
def test_wizard_training_adds_modules_without_touching_any_existing_key():
    from app.training import contractor, content as C, supplier
    from app.training.wizards_lessons import UAT_CASES

    keys = [lesson.key for m in C.modules() for lesson in m.lessons]
    assert len(keys) == len(set(keys))
    for module in contractor.MODULES + supplier.MODULES:
        for lesson in module.lessons:
            assert lesson.key in keys
    c15 = next(m for m in C.modules() if m.key == "c15")
    s11 = next(m for m in C.modules() if m.key == "s11")
    assert set(c15.roles) == {"OWNER", "OFFICE"} and s11.pathway == "SUPPLIER"
    # The owner's lesson is the owner's only; the Field crew get none of it.
    assert [l.key for _m, l in C.lessons_for("CONTRACTOR", "OWNER") if l.key == "c15-owner-decisions"]
    assert not [l.key for _m, l in C.lessons_for("CONTRACTOR", "OFFICE") if l.key == "c15-owner-decisions"]
    assert not any(l.key.startswith("c15") for _m, l in C.lessons_for("FIELD_CREW", "FIELD"))
    assert {c.key for c in UAT_CASES} <= {c.key for c in C.uat_cases()}
