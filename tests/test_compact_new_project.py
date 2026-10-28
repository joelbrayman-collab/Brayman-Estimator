"""Compact Open a New Project (Joel, 28 Oct 2026) — the brief's tests 1–24, server side. Synthetic data only.

Start a New Project is five steps in a dialog — Project, Customer, Details (creates the project; Joel's decision
"Option 2"), Plans, Review — then Project Created. Same workflow, same information, same functionality. The browser
side of the same list (the dialog, Tab kept inside, Escape, two columns at 1280, the narrow layout, a real plan PDF,
Finish double-pressed, Open Project) is tools/release/evidence_compact_new_project.mjs; the Linda walk and Step 4 are
tools/release/evidence_project_creation.mjs.
"""

from __future__ import annotations

import re
from io import BytesIO

from app import db
from app.models import Client, Project
from app.models.wizard import WizardRunEvent
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.test_guided_estimating import BEN, _login, env  # noqa: F401
from tests.test_project_creation_ux import _create, _draft, _marc, _new_customer, _post, _run
from tests.test_wizards import COMMERCIAL_DEFAULTS, _start

STEPS = ["project_type", "customer", "location", "documents", "review"]
JOB = "Compact deck (synthetic)"
CUSTOMER = "Compact customer (synthetic)"

# The inventory taken before the change (27 Oct 2026 seven-task wizard): every field the wizard posted, by the step
# that now holds it. Test 3 proves each one is still on the page of its new step.
INVENTORY = {
    "project_type": ["name", "project_number", "guided_project_type", "description", "project_type", "status"],
    "customer": ["customer_mode", "client_id", "new_customer_name", "new_customer_company", "new_customer_email",
                 "new_customer_phone", "new_customer_street_address", "new_customer_unit", "new_customer_city",
                 "new_customer_province_state", "new_customer_postal_code", "new_customer_country"],
    "location": ["same_as_customer", "street", "municipality", "province_state", "postal_zip", "country", "address",
                 "permit_context_class", "pricing_posture", "execution_risk", "schedule_condition", "site_condition",
                 "estimate_stage", "delivery_model", "justification_reason", "contractor_role",
                 "project_lead_user_id", "plan_start"],
    "documents": ["plan_file", "plan_notes", "drawings_choice"],
}


def _names(page):
    return set(re.findall(r'name="([a-z_]+)"', page))


def _through_customer(d, run_id, **project):
    _post(d, run_id, "project_type", name=JOB, guided_project_type="ADDITION_RENOVATION", project_type="Addition",
          status="Lead", **project)
    _post(d, run_id, "customer", **_new_customer(CUSTOMER, phone="613-555-0101"))


# ------------------------------------------------------------------------------------------ 1–3 launch and fields
def test_01_open_a_new_project_launches_as_a_dialog_on_project(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    assert _run(run_id).wizard_key == "NEW_PROJECT"
    page = d.get(f"/wizards/run/{run_id}/step/project_type")
    resume = d.http.get(f"/wizards/run/{run_id}")
    assert resume.headers["Location"].endswith(f"/wizards/run/{run_id}/step/project_type")
    assert 'role="dialog"' in page and 'aria-modal="true"' in page and 'aria-labelledby="wzc-dialog-title"' in page
    assert ">Start a New Project</h1>" in page and "Step 1 of 5" in page


def test_02_all_five_steps_are_reachable_in_order(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    page = d.get(f"/wizards/run/{run_id}/step/project_type")
    assert re.findall(r'data-step-link="(\w+)"', page) == STEPS
    assert [t.strip() for t in re.findall(r'class="wzc-step-name">([^<]+)<', page)] == [
        "Project", "Customer", "Details", "Plans", "Review"]
    for number, key in enumerate(STEPS, start=1):
        assert f"Step {number} of 5" in d.get(f"/wizards/run/{run_id}/step/{key}")


def test_03_every_existing_field_is_still_on_its_step(env):
    _app, d, _ben = env
    _marc()
    run_id = _start(d, "NEW_PROJECT")
    for key in ("project_type", "customer"):
        page = d.get(f"/wizards/run/{run_id}/step/{key}")
        missing = set(INVENTORY[key]) - _names(page)
        assert not missing, (key, missing)
    _through_customer(d, run_id)
    page = d.get(f"/wizards/run/{run_id}/step/location")
    assert not set(INVENTORY["location"]) - _names(page) - {"same_as_customer"}
    _create(d, run_id, street="5 Compact Rd", municipality="Kemptville", province_state="Ontario", postal_zip="",
            country="Canada")
    page = d.get(f"/wizards/run/{run_id}/step/documents")
    assert not set(INVENTORY["documents"]) - _names(page)
    # The two retired tasks' content: the role and Project Lead on Details, a site visit or meeting on Review.
    assert "data-project-lead-select" in d.get(f"/wizards/run/{run_id}/step/location")
    assert 'data-wizard-action="new-appointment"' in d.get(f"/wizards/run/{run_id}/step/review")


# ------------------------------------------------------------------------------------------ 4–5 validation
def test_04_required_answers_are_checked_on_their_own_step(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "project_type")
    assert _run(run_id).current_step == "project_type"
    assert any("Name the project" in m and "Choose what is being built" in m for m in d.flashes())
    _post(d, run_id, "project_type", name=JOB, guided_project_type="OTHER", project_type="New Build", status="Lead")
    _post(d, run_id, "customer")
    assert _run(run_id).current_step == "customer"
    assert any("Choose the customer" in m for m in d.flashes())
    _post(d, run_id, "customer", **_new_customer(CUSTOMER))
    refused = _create(d, run_id, street="", municipality="", province_state="", postal_zip="", country="",
                      contractor_role="")
    assert refused.headers["Location"].endswith(f"/wizards/run/{run_id}/step/location")
    assert any("Choose your role" in m for m in d.flashes())
    assert Project.query.filter_by(name=JOB).count() == 0


def test_05_optional_fields_stay_optional(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "project_type", name=JOB, guided_project_type="OTHER", project_type="New Build", status="Lead")
    _post(d, run_id, "customer", **_new_customer(CUSTOMER))  # the name only
    created = _create(d, run_id, street="", municipality="", province_state="", postal_zip="", country="Canada")
    assert created.headers["Location"].endswith(f"/wizards/run/{run_id}/step/documents")
    project = Project.query.filter_by(name=JOB).one()
    assert project.project_number is None and project.project_lead_user_id is None
    _post(d, run_id, "documents")  # no plans: Save & Continue still goes on
    assert _run(run_id).current_step == "review"


# ------------------------------------------------------------------------------------------ 6–11 values kept
def test_06_an_existing_customer_is_chosen_by_exact_id(env):
    _app, d, _ben = env
    marc = _marc()
    run_id = _start(d, "NEW_PROJECT")
    count = Client.query.count()
    _post(d, run_id, "customer", customer_mode="existing", client_id=str(marc.id))
    assert _draft(run_id)["client_id"] == str(marc.id) and Client.query.count() == count


def test_07_a_new_customer_is_created_once_in_place(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _through_customer(d, run_id)
    _post(d, run_id, "customer", **_new_customer(CUSTOMER, phone="613-555-0101"))  # sent twice
    assert Client.query.filter_by(name=CUSTOMER).count() == 1
    assert WizardRunEvent.query.filter_by(run_id=run_id, event="CUSTOMER_CREATED").count() == 1


def test_08_09_10_back_and_continue_keep_customer_project_and_details(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _through_customer(d, run_id, project_number="CNP-1", description="Rear deck (synthetic)")
    _post(d, run_id, "location", action="save", street="5 Compact Rd", municipality="Kemptville",
          province_state="Ontario", postal_zip="K0G 1J0", country="Canada", contractor_role="GENERAL_CONTRACTOR",
          permit_context_class="Other/unspecified", **dict(COMMERCIAL_DEFAULTS, pricing_posture="Premium"))
    _post(d, run_id, "location", action="back")
    _post(d, run_id, "customer", action="back")
    project_page = d.get(f"/wizards/run/{run_id}/step/project_type")
    assert f'value="{JOB}"' in project_page and 'value="CNP-1"' in project_page and "Rear deck (synthetic)" in project_page
    customer_page = d.get(f"/wizards/run/{run_id}/step/customer")
    client = Client.query.filter_by(name=CUSTOMER).one()
    assert f'<option value="{client.id}" selected>' in customer_page
    details = d.get(f"/wizards/run/{run_id}/step/location")
    assert 'value="5 Compact Rd"' in details and 'value="K0G 1J0"' in details
    assert '<option value="GENERAL_CONTRACTOR" selected>' in details
    assert re.search(r'<option value="Premium"\s+selected>', details)


def test_11_project_settings_reach_the_project_unchanged(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _through_customer(d, run_id)
    settings = dict(COMMERCIAL_DEFAULTS, pricing_posture="Premium", execution_risk="Low", estimate_stage="Tender",
                    justification_reason="Owner asked for premium finishes (synthetic)")
    fields = {k: v for k, v in _draft(run_id).items() if k in ("client_id", "name", "project_number", "description",
                                                              "project_type", "status")}
    fields.update(settings, permit_context_class="Other/unspecified", wizard_run=str(run_id), plan_start="later",
                  street="5 Compact Rd", municipality="Kemptville", province_state="Ontario", postal_zip="",
                  country="Canada", contractor_role="GENERAL_CONTRACTOR")
    d.post("/projects/new", data=fields)
    project = Project.query.filter_by(name=JOB).one()
    commercial = project.current_commercial_context
    assert (commercial.pricing_posture, commercial.execution_risk, commercial.estimate_stage) == (
        "Premium", "Low", "Tender")
    assert commercial.project_type == "Addition"
    assert project.current_permit_profile.permit_context_class == "Other/unspecified"


# ------------------------------------------------------------------------------------------ 12–14 plans
def test_12_13_14_plans_upload_and_survive_navigation(env):
    _app, d, _ben = env
    from app.services.project_work_package import project_plans
    from tests.test_plan_upload import _make_searchable_pdf_bytes

    run_id = _start(d, "NEW_PROJECT")
    _through_customer(d, run_id)
    _create(d, run_id, street="5 Compact Rd", municipality="Kemptville", province_state="Ontario", postal_zip="",
            country="Canada")
    project = Project.query.filter_by(name=JOB).one()
    page = d.get(f"/wizards/run/{run_id}/step/documents")
    # The proven Step-4 form, unchanged: one PDF at a time, the size limit, the busy state.
    assert 'accept="application/pdf,.pdf"' in page and 'data-max-bytes="' in page and "Uploading plans…" in page
    pdf = _make_searchable_pdf_bytes("Compact plan (synthetic)")
    for _ in range(2):  # sent twice: kept once
        d.http.post(f"/wizards/run/{run_id}/step/documents",
                    data={"wizard_action": "next", "plan_file": (BytesIO(pdf), "compact-plan.pdf")},
                    content_type="multipart/form-data")
    assert [p.original_filename for p in project_plans(ORG, project.id)] == ["compact-plan.pdf"]
    _post(d, run_id, "review", action="back")
    _post(d, run_id, "documents", action="back")
    _post(d, run_id, "location", action="next")
    assert "compact-plan.pdf" in d.get(f"/wizards/run/{run_id}/step/documents")
    assert "compact-plan.pdf" in d.get(f"/wizards/run/{run_id}/step/review")
    assert [p.original_filename for p in project_plans(ORG, project.id)] == ["compact-plan.pdf"]


# ------------------------------------------------------------------------------------------ 15–20 review and create
def _ready_for_review(d):
    run_id = _start(d, "NEW_PROJECT")
    _through_customer(d, run_id, project_number="CNP-2", description="Rear deck (synthetic)")
    _create(d, run_id, street="5 Compact Rd", municipality="Kemptville", province_state="Ontario",
            postal_zip="K0G 1J0", country="Canada")
    _post(d, run_id, "documents", drawings_choice="none")
    return run_id


def test_15_16_17_review_sections_edit_and_nothing_erased(env):
    _app, d, _ben = env
    run_id = _ready_for_review(d)
    page = d.get(f"/wizards/run/{run_id}/step/review")
    for text in (JOB, "CNP-2", "Rear deck (synthetic)", "Addition / Renovation", CUSTOMER, "613-555-0101",
                 "5 Compact Rd, Kemptville, Ontario, K0G 1J0", "Competitive", "General Contractor",
                 "Not needed (recorded)"):
        assert text in page, text
    links = re.findall(r'href="([^"]+)" data-review-edit="(\w+)"', page)
    assert len(links) == 5  # Project information, Customer, Site and settings, Role and lead, Plans
    edits = {key: href for href, key in links}
    assert {k: v.rsplit("/", 1)[1] for k, v in edits.items()} == {
        "project_type": "project_type", "customer": "customer", "location": "location", "documents": "documents"}
    for key in ("project_type", "customer", "location", "documents"):
        d.get(f"/wizards/run/{run_id}/step/{key}")
        _post(d, run_id, key, action="next")
    after = d.get(f"/wizards/run/{run_id}/step/review")
    for text in (JOB, "CNP-2", CUSTOMER, "5 Compact Rd", "General Contractor", "Not needed (recorded)"):
        assert text in after, text


def test_18_19_20_one_project_with_what_was_entered_and_open_project(env):
    _app, d, ben = env
    run_id = _ready_for_review(d)
    # Create pressed again, and Finish pressed twice: still one project, finished once.
    fields = {k: v for k, v in _draft(run_id).items() if not k.startswith("new_customer_")}
    d.post("/projects/new", data=dict(fields, wizard_run=str(run_id), plan_start="later"))
    for _ in range(2):
        response = d.post(f"/wizards/run/{run_id}/step/review?choice=finish", data={"wizard_action": "next"})
        assert response.headers["Location"].endswith(f"/wizards/run/{run_id}/created")
    assert Project.query.filter_by(name=JOB).count() == 1
    assert WizardRunEvent.query.filter_by(run_id=run_id, event="CONFIRMED").count() == 1
    project = Project.query.filter_by(name=JOB).one()
    db.session.refresh(project)
    assert project.project_number == "CNP-2" and project.description == "Rear deck (synthetic)"
    assert project.client.name == CUSTOMER and project.status == "Lead"
    assert project.location.street == "5 Compact Rd" and project.location.postal_zip == "K0G 1J0"
    from app.services import guided_estimating as G

    assert G.get_guided(ORG, project.id).contractor_role == "GENERAL_CONTRACTOR"
    created = d.get(f"/wizards/run/{run_id}/created")
    assert "Project Created Successfully" in created
    for text in (JOB, "CNP-2", CUSTOMER, "Lead"):
        assert text in created
    assert re.search(rf'href="/projects/{project.id}" data-open-project>Open Project<', created)
    assert JOB in d.get(f"/projects/{project.id}")


# ------------------------------------------------------------------------------------------ 21–24 close, a11y, narrow
def test_21_close_is_save_and_exit_and_keeps_everything(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    page = d.get(f"/wizards/run/{run_id}/step/project_type")
    close = re.search(r'<button type="submit" form="wz-nav-project_type" name="wizard_action" value="save_exit"[^>]*'
                      r'data-modal-close', page)
    assert close and "formnovalidate" in close.group(0)
    response = _post(d, run_id, "project_type", action="save_exit", name=JOB)
    assert response.headers["Location"].endswith("/")
    assert _draft(run_id)["name"] == JOB and "SAVED_AND_EXITED" in [
        e.event for e in WizardRunEvent.query.filter_by(run_id=run_id)]
    assert Project.query.filter_by(name=JOB).count() == 0


def test_22_validation_is_announced_and_required_is_not_colour_only(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "project_type")
    page = d.get(f"/wizards/run/{run_id}/step/project_type")
    flash = page[page.index("data-wizard-flash"):]
    assert 'class="alert alert-error" role="alert"' in flash[:400]
    assert page.index("data-wizard-flash") > page.index('role="dialog"')  # inside the dialog, never behind it
    _through_customer(d, run_id)
    details = d.get(f"/wizards/run/{run_id}/step/location")
    role = re.search(r'<label class="np-field">Your role on this job <span class="np-req" aria-hidden="true">\*</span>'
                     r'\s*<select name="contractor_role"[^>]*>', details)
    assert role and "required" in role.group(0) and 'aria-required="true"' in role.group(0)


def test_23_keyboard_labels_steps_and_focus(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _through_customer(d, run_id)
    page = d.get(f"/wizards/run/{run_id}/step/location")
    # Every control of the step is inside a <label> (the browser walk also checks each one is labelled).
    form = page[page.index("data-step-form"):page.index("data-autosave-status")]
    controls = re.findall(r"<(input|select|textarea)\b(?![^>]*type=\"hidden\")[^>]*>", form)
    assert controls and form.count("<label") >= len(controls) - 1
    assert 'aria-current="step"' in page and '<nav class="wzc-stepper-wrap" aria-label="Steps">' in page
    assert 'document.addEventListener("focusin"' in page and 'event.key === "Tab"' in page
    assert 'event.key !== "Escape"' in page


def test_24_narrow_layout_rules_exist(env):
    from pathlib import Path

    css = Path("app/static/css/wizards.css").read_text()
    narrow = css[css.index("Compact Open a New Project (28 Oct 2026)"):]
    for rule in (".np-cols, .np-review-grid { grid-template-columns: minmax(0, 1fr); }",
                 ".wzc-overlay { padding: 0; }", ".wzc-modal .cust-fields { grid-template-columns: minmax(0, 1fr); }"):
        assert rule in narrow, rule
