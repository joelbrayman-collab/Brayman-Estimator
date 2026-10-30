"""Project Creation UX (27 Oct 2026) — Start a New Project as one continuous guided workflow. Synthetic data only.

The Linda Bushel Production failure is reproduced first (a new customer added from the wizard must be the customer
the wizard carries on with, by its exact id, with no detour through the Clients pages), then: choosing an existing
customer, a customer saved with information still missing (WHAT NEEDS MY ATTENTION? lists it once and forgets it
the moment it is completed), the customer's mailing address versus the job-site address and "Same as customer
address", the structured address keeping older one-line addresses untouched, the seven-step structure and the
compact presentation, and the client_structured_address migration. The browser walk (desktop and phone) is
tools/release/evidence_project_creation.mjs.
"""

from __future__ import annotations

import re

from app import db
from app.models import Client, Project
from app.models.wizard import WizardRun, WizardRunEvent
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.test_guided_estimating import BEN, _login, env  # noqa: F401
from tests.test_wizards import COMMERCIAL_DEFAULTS, _start

LINDA = "Linda Bushel (synthetic)"
MARC = "Marc Bouliion (synthetic)"
STEP_KEYS = ["project_type", "customer", "location", "documents", "review"]


def _run(run_id):
    db.session.expire_all()
    return db.session.get(WizardRun, run_id)


def _draft(run_id):
    return dict((_run(run_id).draft_json or {}).get("fields") or {})


def _post(d, run_id, step, action="next", expect=302, **data):
    return d.post(f"/wizards/run/{run_id}/step/{step}", data={"wizard_action": action, **data}, status=expect)


def _new_customer(name, **extra):
    data = {"customer_mode": "new", "new_customer_name": name}
    data.update({f"new_customer_{k}": v for k, v in extra.items()})
    return data


def _marc():
    """The customer already in Production before Linda (P27's customer), with nothing else to choose from."""
    row = Client(organization_id=ORG, name=MARC, company="Solid Steel Management (synthetic)")
    db.session.add(row)
    db.session.commit()
    return row


def _selected_customer(page):
    match = re.search(r'<option value="(\d+)" selected>', page)
    return int(match.group(1)) if match else None


# ====================================================================================== the Linda failure
def test_linda_new_customer_is_carried_by_its_exact_id_with_no_detour_and_never_marc(env):
    application, d, _ben = env
    marc = _marc()
    run_id = _start(d, "NEW_PROJECT")
    # 1–2. Start a New Project; no customer is selected (never the first in the list).
    page = d.get(f"/wizards/run/{run_id}/step/customer")
    assert _selected_customer(page) is None and "Choose the customer" in page
    refused = _post(d, run_id, "customer", client_id="")
    assert refused.headers["Location"].endswith(f"/wizards/run/{run_id}/step/customer")
    assert any("Choose the customer" in m for m in d.flashes())
    # 3–5. Add a new customer right in the step (no email or phone yet) and Save & Continue.
    response = _post(d, run_id, "customer", **_new_customer(LINDA, street_address="12 Synthetic Lane", city="Kemptville",
                                                            province_state="Ontario", postal_code="k0g1j0",
                                                            country="Canada"))
    linda = Client.query.filter_by(organization_id=ORG, name=LINDA).one()
    # 6. Her exact id is in the run, and recorded as created by this run.
    assert _draft(run_id)["client_id"] == str(linda.id)
    created = WizardRunEvent.query.filter_by(run_id=run_id, event="CUSTOMER_CREATED").one()
    assert created.detail == f"Client {linda.id}: {LINDA}"
    # 7. No detour through the Clients pages: straight on to the next task (9. automatic progression).
    assert "/clients" not in response.headers["Location"]
    assert response.headers["Location"].endswith(f"/wizards/run/{run_id}/step/location")
    assert _run(run_id).current_step == "location"
    page = d.get(f"/wizards/run/{run_id}/step/location")
    assert "Details" in page and LINDA in page and MARC not in page
    # 8. Marc (or anyone else) is never the customer.
    assert _draft(run_id)["client_id"] != str(marc.id)
    # 10. Back keeps Linda selected.
    _post(d, run_id, "location", action="back")
    page = d.get(f"/wizards/run/{run_id}/step/customer")
    assert _selected_customer(page) == linda.id
    # The same form sent twice (double press) never makes a second Linda.
    _post(d, run_id, "customer", **_new_customer(LINDA))
    assert Client.query.filter_by(organization_id=ORG, name=LINDA).count() == 1
    assert _draft(run_id)["client_id"] == str(linda.id)
    # 11. Forward keeps Linda.
    _post(d, run_id, "customer", customer_mode="existing", client_id=str(linda.id))
    assert _run(run_id).current_step == "location" and _draft(run_id)["client_id"] == str(linda.id)
    # 12. Save & Exit keeps Linda.
    exit_response = _post(d, run_id, "project_type", action="save_exit", name="Bushel deck (synthetic)",
                          guided_project_type="OTHER", project_type="New Build", status="Lead")
    assert exit_response.headers["Location"].endswith("/")
    assert _draft(run_id)["client_id"] == str(linda.id)
    # 13. Resume (a new sign-in) keeps Linda, on the step where Joel stopped.
    d2 = _login(application, BEN)
    home = d2.get("/")
    assert "Bushel deck (synthetic) — " + LINDA in home
    resume = d2.http.get(f"/wizards/run/{run_id}")
    assert resume.headers["Location"].endswith(f"/wizards/run/{run_id}/step/project_type")
    assert _selected_customer(d2.get(f"/wizards/run/{run_id}/step/customer")) == linda.id
    # And the project is created for Linda, never Marc.
    _post(d2, run_id, "project_type", name="Bushel deck (synthetic)", guided_project_type="OTHER",
          project_type="New Build", status="Lead")
    created = _create(d2, run_id, same_as_customer="on")
    assert created.headers["Location"].endswith(f"/wizards/run/{run_id}/step/documents")
    project = Project.query.filter_by(organization_id=ORG, name="Bushel deck (synthetic)").one()
    assert project.client_id == linda.id
    assert Project.query.filter_by(client_id=marc.id).count() == 0


def _create(d, run_id, **location):
    """Create Project & Continue on Details (step 3): the fields the step's form posts to the New Project handler."""
    fields = {k: v for k, v in _draft(run_id).items() if k in ("client_id", "name", "client_project_number", "description",
                                                             "project_type", "status")}
    location.setdefault("contractor_role", "GENERAL_CONTRACTOR")  # Details: your role is chosen with the site
    fields.update(COMMERCIAL_DEFAULTS, permit_context_class="Other/unspecified", wizard_run=str(run_id),
                  plan_start="later", **location)
    return d.post("/projects/new", data=fields)


# ====================================================================================== choosing and completing
def test_choosing_an_existing_customer_and_nothing_is_created(env):
    _app, d, _ben = env
    marc = _marc()
    run_id = _start(d, "NEW_PROJECT")
    count = Client.query.count()
    response = _post(d, run_id, "customer", customer_mode="existing", client_id=str(marc.id))
    assert response.headers["Location"].endswith(f"/wizards/run/{run_id}/step/location")
    assert _draft(run_id)["client_id"] == str(marc.id) and Client.query.count() == count
    # A customer of another company cannot be chosen.
    from tests.test_guided_estimating import _other_company

    other = Client(organization_id=ORG, name="placeholder")
    db.session.add(other)
    db.session.commit()
    _post(d, run_id, "customer", customer_mode="existing", client_id="999999")
    assert any("Choose a customer of this company" in m for m in d.flashes())
    _ = _other_company


def test_a_new_customer_needs_only_a_name_and_the_typed_fields_wait_in_the_draft(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    # Autosave keeps what was typed for a new customer but never creates one.
    r = d.http.post(f"/wizards/run/{run_id}/step/customer/autosave",
                    data=_new_customer("Typed only (synthetic)", phone="613-555-0100"))
    assert r.status_code == 200 and r.get_json()["saved"]
    assert Client.query.filter_by(name="Typed only (synthetic)").count() == 0
    page = d.get(f"/wizards/run/{run_id}/step/customer")
    assert 'value="Typed only (synthetic)"' in page and 'value="613-555-0100"' in page
    # Save & Continue without a name is refused (and nothing is made).
    _post(d, run_id, "customer", **_new_customer(""))
    assert any("Enter the new customer's name" in m for m in d.flashes())
    # A bad email is refused with the reason; the customer is not created half-way.
    _post(d, run_id, "customer", **_new_customer("Bad email (synthetic)", email="not-an-email"))
    assert any("email address does not look right" in m for m in d.flashes())
    assert Client.query.filter_by(name="Bad email (synthetic)").count() == 0


def test_missing_customer_information_is_one_attention_item_until_completed(env):
    _app, d, _ben = env
    from app.services.needs_attention import incomplete_customers

    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "customer", **_new_customer(LINDA))
    linda = Client.query.filter_by(name=LINDA).one()
    items = [i for i in incomplete_customers(ORG) if LINDA in i["what"]]
    assert len(items) == 1
    item = items[0]
    assert item["what"] == f"{LINDA} — Customer information incomplete"
    assert item["status"] == "Missing: Email, Phone, Address"
    assert item["href"] == f"/clients/{linda.id}?return_to=/" and item["action"] == "Complete information"
    # On Home (WHAT NEEDS MY ATTENTION?), once.
    home = d.get("/")
    assert home.count(f"{LINDA} — Customer information incomplete") == 1
    # Two projects for her still make one item.
    _post(d, run_id, "project_type", name="Bushel deck (synthetic)", guided_project_type="OTHER",
          project_type="New Build", status="Lead")
    _create(d, run_id, street="12 Synthetic Lane", municipality="Kemptville", province_state="Ontario",
            postal_zip="K0G 1J0", country="Canada")
    project = Project.query.filter_by(name="Bushel deck (synthetic)").one()
    assert len([i for i in incomplete_customers(ORG) if LINDA in i["what"]]) == 1
    # In the project's context.
    page = d.get(f"/projects/{project.id}")
    assert "Customer information incomplete — missing email, phone, address" in page
    assert f"/clients/{linda.id}?return_to=/projects/{project.id}" in page.replace("&amp;", "&")
    # On the customer's own page.
    assert "Customer information incomplete." in d.get(f"/clients/{linda.id}")
    # Completing part of it narrows the item; completing all of it resolves it automatically.
    form = {"name": LINDA, "email": "linda.bushel@example.invalid", "phone": "", "street_address": "",
            "province_state": "", "country": "Canada"}
    d.post(f"/clients/{linda.id}", data={**form, "return_to": "/"})
    assert [i["status"] for i in incomplete_customers(ORG) if LINDA in i["what"]] == ["Missing: Phone, Address"]
    done = d.post(f"/clients/{linda.id}", data={**form, "phone": "613-555-0142", "street_address": "12 Synthetic Lane",
                                               "city": "Kemptville", "province_state": "Ontario",
                                               "postal_code": "K0G 1J0", "return_to": "/"})
    assert done.headers["Location"].endswith("/")  # back where "Complete information" was pressed
    assert [i for i in incomplete_customers(ORG) if LINDA in i["what"]] == []
    assert f"{LINDA} — Customer information incomplete" not in d.get("/")
    assert "Customer information incomplete" not in d.get(f"/projects/{project.id}")
    # return_to only ever goes back to this site's own pages.
    evil = d.post(f"/clients/{linda.id}", data={**form, "return_to": "https://evil.example/"})
    assert evil.headers["Location"].endswith("/clients/")


# ====================================================================================== addresses
def test_job_site_can_differ_from_the_customer_address_or_be_the_same(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "customer", **_new_customer(LINDA, street_address="12 Synthetic Lane", unit="2",
                                                 city="Kemptville", province_state="Ontario", postal_code="K0G 1J0",
                                                 country="Canada"))
    linda = Client.query.filter_by(name=LINDA).one()
    assert linda.address == "12 Synthetic Lane, Unit 2, Kemptville, Ontario K0G 1J0, Canada"
    _post(d, run_id, "project_type", name="Cottage deck (synthetic)", guided_project_type="OTHER",
          project_type="New Build", status="Lead")
    page = d.get(f"/wizards/run/{run_id}/step/location")
    assert "Same as Linda Bushel (synthetic)&#39;s address" in page or "Same as Linda Bushel (synthetic)'s address" in page
    # A different job site: the job address is its own, the customer's address is untouched.
    _create(d, run_id, street="77 Lakeshore Road", municipality="Merrickville", province_state="Ontario",
            postal_zip="K0G 1N0", country="Canada")
    project = Project.query.filter_by(name="Cottage deck (synthetic)").one()
    assert (project.location.street, project.location.municipality) == ("77 Lakeshore Road", "Merrickville")
    db.session.refresh(linda)
    assert linda.street_address == "12 Synthetic Lane" and linda.city == "Kemptville"

    # "Same as customer address": an empty job address is taken from the customer's.
    run2 = _start(d, "NEW_PROJECT")
    _post(d, run2, "customer", customer_mode="existing", client_id=str(linda.id))
    _post(d, run2, "project_type", name="Home deck (synthetic)", guided_project_type="OTHER", project_type="New Build",
          status="Lead")
    _create(d, run2, same_as_customer="on", street="", municipality="", province_state="", postal_zip="", country="")
    same = Project.query.filter_by(name="Home deck (synthetic)").one()
    loc = same.location
    assert (loc.street, loc.municipality, loc.province_state, loc.postal_zip, loc.country) == (
        "12 Synthetic Lane, 2", "Kemptville", "Ontario", "K0G 1J0", "Canada")
    assert loc.completeness == "LOCATION_COMPLETE"


def test_structured_address_keeps_older_one_line_addresses_exactly(env):
    _app, d, _ben = env
    old = Client(organization_id=ORG, name="Older customer (synthetic)", address="RR 2, Lot 14 Con 3, North Gower")
    db.session.add(old)
    db.session.commit()
    page = d.get(f"/clients/{old.id}")
    assert "Address on record: <strong>RR 2, Lot 14 Con 3, North Gower</strong>" in page
    # Saving other details leaves the one-line address exactly as it was typed (nothing parsed or guessed).
    d.post(f"/clients/{old.id}", data={"name": "Older customer (synthetic)", "phone": "613-555-0101",
                                       "address": "RR 2, Lot 14 Con 3, North Gower", "province_state": "Ontario",
                                       "country": "Canada"})
    db.session.refresh(old)
    assert old.address == "RR 2, Lot 14 Con 3, North Gower" and old.street_address is None and old.city is None
    # Entering the structured fields replaces it with the composed address.
    d.post(f"/clients/{old.id}", data={"name": "Older customer (synthetic)", "phone": "613-555-0101",
                                       "address": "RR 2, Lot 14 Con 3, North Gower", "street_address": "2562 Church St",
                                       "city": "North Gower", "province_state": "Ontario", "postal_code": "k0a2t0",
                                       "country": "Canada"})
    db.session.refresh(old)
    assert old.address == "2562 Church St, North Gower, Ontario K0A 2T0, Canada" and old.postal_code == "K0A 2T0"
    # Province is a controlled choice: a value from another country's list is refused.
    d.post(f"/clients/{old.id}", data={"name": "Older customer (synthetic)", "street_address": "1 Main",
                                       "city": "Ottawa", "province_state": "Texas", "country": "Canada"}, status=200)
    db.session.refresh(old)
    assert old.province_state == "Ontario"


def test_the_clients_page_creates_with_only_a_name_and_lists_what_is_missing(env):
    _app, d, _ben = env
    response = d.post("/clients/new", data={"name": "Name only (synthetic)", "province_state": "Ontario",
                                            "country": "Canada"})
    assert response.headers["Location"].endswith("/clients/")
    row = Client.query.filter_by(name="Name only (synthetic)").one()
    assert row.address == "" and row.street_address is None and row.country is None
    assert any("Still to add: email, phone, address" in m for m in d.flashes())
    form = d.get("/clients/new")
    for label in ("Street address", "Unit / suite", "City / town", "Province / state", "Postal code / ZIP", "Country"):
        assert label in form


# ====================================================================================== structure and presentation
def test_five_compact_steps_in_a_dialog(env):
    _app, d, _ben = env
    from app.wizards.new_project import WIZARD

    assert [s.key for s in WIZARD.steps] == STEP_KEYS
    assert [s.title for s in WIZARD.steps] == ["Project", "Customer", "Details", "Plans", "Review"]
    run_id = _start(d, "NEW_PROJECT")
    page = d.get(f"/wizards/run/{run_id}/step/project_type")
    assert "data-compact-wizard" in page and 'role="dialog"' in page and 'aria-modal="true"' in page
    assert "Step 1 of 5" in page and "data-stepper" in page and 'aria-current="step"' in page
    assert "data-modal-close" in page  # × is Save & Exit
    assert 'class="wz-steps"' not in page  # no permanent roadmap column
    assert "Save &amp; Continue →" in page and "Save &amp; Exit" in page
    assert "Come back here when it is saved" not in page and 'href="/clients/new"' not in page
    # Messages are shown inside the dialog, never behind the backdrop.
    _post(d, run_id, "project_type")
    page = d.get(f"/wizards/run/{run_id}/step/project_type")
    assert "data-wizard-flash" in page and page.index("data-wizard-flash") > page.index('role="dialog"')
    # Details: the site, the settings, your role (required) and the Project Lead; Continue creates the project.
    _post(d, run_id, "project_type", name="Dialog deck (synthetic)", guided_project_type="OTHER",
          project_type="New Build", status="Lead")
    _post(d, run_id, "customer", **_new_customer(LINDA))
    page = d.get(f"/wizards/run/{run_id}/step/location")
    for hook in ('name="street"', 'name="permit_context_class"', 'name="pricing_posture"', 'name="contractor_role"',
                 'name="project_lead_user_id"', 'name="justification_reason"', 'name="address"', "data-create-project"):
        assert hook in page, hook
    assert "Create Project &amp; Continue" in page
    # The other wizards keep their existing presentation.
    est = _start(d, "GUIDED_ESTIMATING")
    assert "data-compact-wizard" not in d.get(f"/wizards/run/{est}/step/project")


def test_plans_step_uploads_here_and_never_blocks(env):
    _app, d, _ben = env
    from io import BytesIO

    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "customer", **_new_customer(LINDA))
    _post(d, run_id, "project_type", name="Plans deck (synthetic)", guided_project_type="OTHER",
          project_type="New Build", status="Lead")
    _create(d, run_id, street="1 Plan St", municipality="Kemptville", province_state="Ontario", postal_zip="",
            country="Canada")
    project = Project.query.filter_by(name="Plans deck (synthetic)").one()
    page = d.get(f"/wizards/run/{run_id}/step/documents")
    assert 'enctype="multipart/form-data"' in page and 'name="plan_file"' in page
    # No drawings yet: Save & Continue still goes on (optional step); the review lists it to add later.
    _post(d, run_id, "documents")
    assert _run(run_id).current_step == "review"
    # A PDF chosen here is added through the Plans page's own service, and the step is done.
    from tests.test_plan_upload import _make_searchable_pdf_bytes

    pdf = _make_searchable_pdf_bytes("Deck framing plan (synthetic)")
    d.http.post(f"/wizards/run/{run_id}/step/documents", data={"wizard_action": "next",
                                                               "plan_file": (BytesIO(pdf), "deck-plan.pdf")},
                content_type="multipart/form-data")
    from app.services.project_work_package import project_plans

    assert [p.original_filename for p in project_plans(ORG, project.id)] == ["deck-plan.pdf"]
    assert 'data-step-state="done"' in d.get(f"/wizards/run/{run_id}/step/documents")


def test_plans_step_sent_twice_keeps_one_plan_and_says_what_is_happening(env):
    """Production, 28 Oct 2026: Save & Continue on Plans showed nothing while the PDF uploaded; a second press sent the
    same PDF again. The page now says what is happening and holds its buttons; the same PDF sent twice is kept once,
    and Step 5 follows both times."""
    _app, d, _ben = env
    from io import BytesIO

    from app.services.project_work_package import project_plans
    from tests.test_plan_upload import _make_searchable_pdf_bytes

    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "customer", **_new_customer(LINDA))
    _post(d, run_id, "project_type", name="Twice deck (synthetic)", guided_project_type="OTHER",
          project_type="New Build", status="Lead")
    _create(d, run_id, street="2 Twice Rd", municipality="Kemptville", province_state="Ontario", postal_zip="",
            country="Canada")
    project = Project.query.filter_by(name="Twice deck (synthetic)").one()
    page = d.get(f"/wizards/run/{run_id}/step/documents")
    assert "data-submit-status" in page and 'data-max-bytes="' in page and "Uploading plans…" in page
    pdf = _make_searchable_pdf_bytes("Deck plan sent twice (synthetic)")
    for _ in range(2):
        r = d.http.post(f"/wizards/run/{run_id}/step/documents",
                        data={"wizard_action": "next", "plan_file": (BytesIO(pdf), "deck-plan.pdf")},
                        content_type="multipart/form-data")
        assert r.status_code == 302 and r.headers["Location"].endswith(f"/wizards/run/{run_id}/step/review")
    assert [p.original_filename for p in project_plans(ORG, project.id)] == ["deck-plan.pdf"]
    assert any("already on the project" in m for m in d.flashes())
    # A different PDF is still added; a file that is not a PDF stays on Plans with the reason.
    other = _make_searchable_pdf_bytes("Second sheet (synthetic)")
    d.http.post(f"/wizards/run/{run_id}/step/documents",
                data={"wizard_action": "next", "plan_file": (BytesIO(other), "sheet-2.pdf")},
                content_type="multipart/form-data")
    assert [p.original_filename for p in project_plans(ORG, project.id)] == ["deck-plan.pdf", "sheet-2.pdf"]
    r = d.http.post(f"/wizards/run/{run_id}/step/documents",
                    data={"wizard_action": "next", "plan_file": (BytesIO(b"not a pdf"), "notes.txt")},
                    content_type="multipart/form-data")
    assert r.headers["Location"].endswith(f"/wizards/run/{run_id}/step/documents")
    assert any("Only PDF files are allowed" in m for m in d.flashes())
    assert len(project_plans(ORG, project.id)) == 2


def test_review_sections_edit_and_finish_shows_project_created(env):
    _app, d, _ben = env
    run_id = _start(d, "NEW_PROJECT")
    _post(d, run_id, "project_type", name="Finish deck (synthetic)", guided_project_type="OTHER",
          project_type="New Build", status="Lead")
    _post(d, run_id, "customer", **_new_customer(LINDA))
    _create(d, run_id, street="9 Done Rd", municipality="Kemptville", province_state="Ontario", postal_zip="",
            country="Canada")
    project = Project.query.filter_by(name="Finish deck (synthetic)").one()
    from app.services import guided_estimating as G

    guided = G.get_guided(ORG, project.id)
    assert (guided.project_type, guided.contractor_role) == ("OTHER", "GENERAL_CONTRACTOR")
    assert all(s.responsibility is None for s in guided.stages)  # who does each stage is Guided Estimating's step
    _post(d, run_id, "documents", drawings_choice="none")
    page = d.get(f"/wizards/run/{run_id}/step/review")
    assert LINDA in page and "9 Done Rd" in page and "General Contractor" in page.replace("general contractor", "General Contractor")
    for title in ("Project information", "Customer", "Site and project details", "Plans and documents"):
        assert title in page
    assert "Customer information: email, phone, address" in page
    # Edit goes back to the step; going back and forward keeps everything.
    edit = re.search(r'href="([^"]+)" data-review-edit="location"', page).group(1)
    assert edit.endswith(f"/wizards/run/{run_id}/step/location")
    assert "9 Done Rd" in d.get(edit)
    # Finish (pressed twice) finishes once and shows Project Created; nothing new is made.
    for _ in range(2):
        response = d.post(f"/wizards/run/{run_id}/step/review?choice=finish", data={"wizard_action": "next"})
    assert _run(run_id).status == "COMPLETED"
    assert WizardRunEvent.query.filter_by(run_id=run_id, event="CONFIRMED").count() == 1
    assert Project.query.filter_by(name="Finish deck (synthetic)").count() == 1
    created = d.get(f"/wizards/run/{run_id}/created")
    assert "Project Created Successfully" in created and LINDA in created
    assert created.index("data-open-project") < created.index("data-create-another")
    # Create Another Project starts a fresh run.
    another = d.post("/wizards/NEW_PROJECT/start")
    new_id = int(re.search(r"/wizards/run/(\d+)", another.headers["Location"]).group(1))
    assert new_id != run_id and _run(new_id).status == "ACTIVE"
    # The completion page belongs to a finished run of this company only.
    d.get(f"/wizards/run/{new_id}/created", status=404)


# ====================================================================================== migration
def test_the_migration_adds_six_empty_customer_address_columns_and_changes_nothing_else(tmp_path):
    """q4c7l2n8t3a6: six nullable columns on clients, added in place. Every existing table, column, index and row is
    unchanged (the customers' existing addresses included). Downgrade refuses once a structured address exists."""
    from pathlib import Path

    import pytest
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from app import create_app

    root = Path(__file__).resolve().parents[1]
    uri = f"sqlite:///{tmp_path}/m.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    ctx = application.app_context()
    ctx.push()
    cfg = Config(str(root / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["s6f7a8b9c0d1"]
    assert script.get_revision("q4c7l2n8t3a6").down_revision == "e5d1v4r7y2k9"
    command.upgrade(cfg, "e5d1v4r7y2k9")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO organizations (id, legal_name, display_name, currency, is_active, created_at, "
                             "updated_at) VALUES ('ORG-M', 'M', 'M', 'CAD', 1, '2026-10-27', '2026-10-27')"))
        conn.execute(sa.text("INSERT INTO clients (organization_id, name, email, address, created_at) VALUES "
                             "('ORG-M', 'Legacy (synthetic)', 'l@example.invalid', 'RR 2, Lot 14', '2026-10-27')"))
    inspector = sa.inspect(engine)
    before = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
              for t in inspector.get_table_names()}
    before_indexes = {t: sorted(i["name"] for i in inspector.get_indexes(t)) for t in before}
    with engine.connect() as conn:
        rows = {t: conn.execute(sa.text(f'SELECT * FROM "{t}" ORDER BY rowid')).fetchall() for t in before
                if t != "alembic_version"}
    engine.dispose()
    command.upgrade(cfg, "q4c7l2n8t3a6")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    after = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
             for t in inspector.get_table_names()}
    assert set(after) == set(before)
    added = [c for c in after["clients"] if c not in before["clients"]]
    assert [c[0] for c in added] == ["street_address", "unit", "city", "province_state", "postal_code", "country"]
    assert all(c[2] for c in added)  # nullable
    assert after["clients"][:len(before["clients"])] == before["clients"]
    for table in before:
        if table != "clients":
            assert after[table] == before[table], table
        assert sorted(i["name"] for i in inspector.get_indexes(table)) == before_indexes[table], table
    with engine.connect() as conn:
        for table, old_rows in rows.items():
            columns = ", ".join(f'"{c[0]}"' for c in before[table])
            new_rows = conn.execute(sa.text(f'SELECT {columns} FROM "{table}" ORDER BY rowid')).fetchall()
            assert new_rows == old_rows, table
        assert conn.execute(sa.text("SELECT street_address, city, country FROM clients")).fetchall() == [(None, None, None)]
    with engine.begin() as conn:
        conn.execute(sa.text("UPDATE clients SET city='Kemptville'"))
    engine.dispose()
    with pytest.raises(RuntimeError, match="Downgrade refused"):
        command.downgrade(cfg, "e5d1v4r7y2k9")
    ctx.pop()


def test_production_sequence_a_draft_already_holding_marc_never_survives_adding_linda(env):
    """The exact Production record of 27 Oct 2026 (run 2): the step-1 draft was autosaved with Marc's id and no name
    at 11:38:54, before Linda existed (11:48:51). The old wizard then sent the office to the Clients page, and
    nothing ever replaced that draft, so step 1 showed Marc. Now the new customer replaces it, by exact id."""
    application, d, _ben = env
    marc = _marc()
    run_id = _start(d, "NEW_PROJECT")
    r = d.http.post(f"/wizards/run/{run_id}/step/customer/autosave",
                    data={"customer_mode": "existing", "client_id": str(marc.id)})
    assert r.status_code == 200 and _draft(run_id)["client_id"] == str(marc.id)  # the Production state
    _post(d, run_id, "customer", **_new_customer(LINDA))
    linda = Client.query.filter_by(organization_id=ORG, name=LINDA).one()
    assert _draft(run_id)["client_id"] == str(linda.id) != str(marc.id)
    assert _run(run_id).current_step == "location"
    page = d.get(f"/wizards/run/{run_id}/step/customer")
    assert _selected_customer(page) == linda.id
