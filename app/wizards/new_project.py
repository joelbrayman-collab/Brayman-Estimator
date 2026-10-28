"""Wizard 1 — Start a New Project (brief §2; redesigned 27 Oct 2026, Project Creation UX; compact five-step modal
28 Oct 2026, Joel's approved "Open a New Project" mockup).

Five steps, shown as a compact modal with numbered steps across the top:

  1 Project    the project's name, number, what is being built, commercial type, status and description
  2 Customer   choose one, or add a new customer right here (no detour to the Clients pages)
  3 Details    the job site (or "Same as customer address"), the permit class and commercial settings, your role
               and the Project Lead; Continue creates the project (once)
  4 Plans      upload a plan PDF here (the Step-4 upload, unchanged), record that none are needed, or add them later
  5 Review     every answer by section, each with Edit; Finish shows Project Created

Project Created is the completion state (not a sixth step): Open Project, Start Guided Estimating, Create Another
Project. The work being done (Internal or Subcontracted) is chosen in Guided Estimating.

Steps 1 to 3 keep the answers in the run's draft until the project exists; Continue on step 3 posts them to the
existing New Project form handler (projects.create_project), which creates the project, its commercial context,
its location and its Project Lead exactly as the manual form does, claims the run once (a second press creates
nothing), and then starts the project's guided estimate with the chosen role. A new customer is created by the
existing customer rules (app/services/clients.py) and its exact id is kept in the run. No dimension, quantity or
specification is ever filled in by the wizard.
"""

from __future__ import annotations

from flask import request, url_for

from app.models.wizard import WIZARD_GUIDED_ESTIMATING, WIZARD_NEW_PROJECT
from app.wizards.framework import (
    DONE,
    INFO,
    NOT_NEEDED,
    TODO,
    Action,
    Item,
    Step,
    StepView,
    Wizard,
)

NEW_CUSTOMER_FIELDS = ("name", "company", "email", "phone", "street_address", "unit", "city", "province_state",
                       "postal_code", "country")
NEW_PREFIX = "new_customer_"
CUSTOMER_FIELDS = ("client_id", "customer_mode") + tuple(NEW_PREFIX + f for f in NEW_CUSTOMER_FIELDS)
PROJECT_FIELDS = ("name", "project_number", "description", "guided_project_type", "project_type", "status")
LOCATION_FIELDS = ("same_as_customer", "address", "street", "municipality", "province_state", "postal_zip",
                   "country", "permit_context_class", "pricing_posture", "execution_risk", "schedule_condition",
                   "site_condition", "estimate_stage", "delivery_model", "justification_reason",
                   "contractor_role", "project_lead_user_id")
DRAFT_FIELDS = CUSTOMER_FIELDS + PROJECT_FIELDS + LOCATION_FIELDS
# The manual form's own defaults (templates/projects/form.html), so the wizard and the form start the same way.
FORM_DEFAULTS = {"status": "Lead", "project_type": "New Build", "pricing_posture": "Competitive",
                 "execution_risk": "Normal", "schedule_condition": "Normal", "site_condition": "Normal",
                 "estimate_stage": "Preliminary", "delivery_model": "Self-Perform", "country": "Canada",
                 "province_state": "Ontario"}
PROJECT_STATUSES = ("Lead", "Estimating")
SAVING_ACTIONS = ("next", "save", "save_exit")


def _clients(ctx):
    from app.models import Client
    from app.services.time_entry import customer_clients_only

    query = Client.query.filter_by(organization_id=ctx.organization_id)
    return customer_clients_only(query, ctx.organization_id).order_by(Client.name.asc()).all()


def _chosen_client(ctx):
    """The customer this run chose, by its exact id only (never a list position, default or ordering)."""
    from app.models import Client

    if ctx.project is not None:
        return ctx.project.client
    raw = str(ctx.draft.get("client_id") or "").strip()
    if not raw.isdigit():
        return None
    return Client.query.filter_by(id=int(raw), organization_id=ctx.organization_id).first()


def _value(ctx, key):
    return ctx.draft.get(key) or FORM_DEFAULTS.get(key, "")


def _project_or_todo(ctx, headline="Create the project first (step 3, Details)."):
    if ctx.project is None:
        return StepView(TODO, headline, missing=[headline])
    return None


def _wizard_action(form) -> str:
    """The button pressed (autosave sends none: it only keeps what was typed)."""
    return (form.get("wizard_action") or "").strip()


# ------------------------------------------------------------------------------------------------ 2 customer
def _customer(ctx):
    from app.services.clients import form_options, missing_information

    if ctx.project is not None:
        client = ctx.project.client
        missing = missing_information(client) if client is not None else []
        return StepView(DONE, f"Customer: {client.name if client else '—'}"
                        + (f" (still to add: {', '.join(missing).lower()})" if missing else ""),
                        actions=[Action("Correct the customer", url_for("projects.correct_project_client_page",
                                                                        id=ctx.project.id), key="correct-client")],
                        note="The project exists. Its customer is changed on the project's own pages.")
    client = _chosen_client(ctx)
    mode = ctx.draft.get("customer_mode") or ("existing" if client is not None or _clients(ctx) else "new")
    values = {f: ctx.draft.get(NEW_PREFIX + f, "") for f in NEW_CUSTOMER_FIELDS}
    form_ctx = {"clients": _clients(ctx), "chosen_id": client.id if client is not None else None, "mode": mode,
                "new": values, **form_options()}
    if client is None:
        return StepView(TODO, "No customer chosen yet", missing=["Choose the customer, or add a new customer."],
                        form="np_customer.html", form_ctx=form_ctx)
    missing = missing_information(client)
    return StepView(DONE, f"Customer: {client.name}"
                    + (f" — still to add: {', '.join(missing).lower()}" if missing else ""),
                    form="np_customer.html", form_ctx=form_ctx)


def _save_customer(ctx, form):
    """Choose a customer, or create the new one (existing customer rules) and keep its exact id in the run."""
    from app import db
    from app.services import clients as C
    from app.wizards.service import WizardError, has_event, record, save_draft

    if ctx.project is not None:
        return "The project exists. Its customer is changed on the project's own pages."
    mode = "new" if form.get("customer_mode") == "new" else "existing"
    typed = {NEW_PREFIX + f: form.get(NEW_PREFIX + f, "") for f in NEW_CUSTOMER_FIELDS}
    if mode == "existing":
        client_id = (form.get("client_id") or "").strip()
        if client_id and not any(str(c.id) == client_id for c in _clients(ctx)):
            raise WizardError("Choose a customer of this company.")
        save_draft(ctx.run, {"client_id": client_id, "customer_mode": "existing"}, allowed=CUSTOMER_FIELDS,
                   step="customer", actor=ctx.actor, user_id=ctx.user_id,
                   event="DRAFT_SAVED" if _wizard_action(form) else None)
        return "Saved."
    # A new customer. Autosave only keeps what was typed; the customer is created by Save & Continue (or Save).
    if _wizard_action(form) not in SAVING_ACTIONS:
        save_draft(ctx.run, {**typed, "customer_mode": "new"}, allowed=CUSTOMER_FIELDS, step="customer",
                   actor=ctx.actor, user_id=ctx.user_id)
        return "Saved."
    values = {f: form.get(NEW_PREFIX + f, "") for f in NEW_CUSTOMER_FIELDS}
    name = " ".join((values.get("name") or "").split())
    if not name:
        save_draft(ctx.run, {**typed, "customer_mode": "new"}, allowed=CUSTOMER_FIELDS, step="customer",
                   actor=ctx.actor, user_id=ctx.user_id)
        if _wizard_action(form) == "save_exit":
            return "Saved."
        raise WizardError("Enter the new customer's name (email, phone and address can be added later).")
    # The same form sent twice (double press, or two windows): reuse the customer this run already created.
    previous = has_event(ctx.run, "CUSTOMER_CREATED", "customer")
    reused = None
    if previous is not None and (previous.detail or "").startswith("Client "):
        try:
            prior_id = int(previous.detail.split(":", 1)[0].split()[1])
        except (IndexError, ValueError):
            prior_id = None
        prior = next((c for c in _clients(ctx) if c.id == prior_id), None)
        if prior is not None and prior.name.strip().lower() == name.lower():
            reused = prior
    if reused is None:
        try:
            client = C.create_client(ctx.organization_id, values, commit=False)
        except C.ClientError as exc:
            db.session.rollback()
            save_draft(ctx.run, {**typed, "customer_mode": "new"}, allowed=CUSTOMER_FIELDS, step="customer",
                       actor=ctx.actor, user_id=ctx.user_id)
            raise WizardError(str(exc)) from exc
        record(ctx.run, "CUSTOMER_CREATED", actor=ctx.actor, step="customer",
               detail=f"Client {client.id}: {client.name}", user_id=ctx.user_id)
    else:
        client = reused
    # Exactly this customer from now on; the typed fields are cleared so nothing is created twice.
    cleared = {k: "" for k in typed}
    save_draft(ctx.run, {**cleared, "client_id": str(client.id), "customer_mode": "existing"},
               allowed=CUSTOMER_FIELDS, step="customer", actor=ctx.actor, user_id=ctx.user_id, event="DRAFT_SAVED")
    missing = C.missing_information(client)
    message = f"Customer {client.name} added" + (f" — still to add: {', '.join(missing).lower()} (listed under What "
                                                 "needs my attention)." if missing else ".")
    return message, None  # shown on the next task; the wizard moves straight on with this customer


# ------------------------------------------------------------------------------------------------ 1 project
def _type_options():
    from app.models.guided_estimating import PROJECT_TYPE_LABELS
    from app.services.commercial_context import PROJECT_TYPES
    from app.services.guided_estimating import COMMERCIAL_TYPE_HINT

    return {"guided_types": PROJECT_TYPE_LABELS, "commercial_types": PROJECT_TYPES, "hints": COMMERCIAL_TYPE_HINT,
            "statuses": PROJECT_STATUSES}


def _project_type(ctx):
    from app.models.guided_estimating import PROJECT_TYPE_LABELS

    if ctx.project is not None:
        guided_type = ctx.guided.project_type if ctx.guided is not None else ctx.draft.get("guided_project_type")
        commercial = ctx.project.current_commercial_context
        return StepView(DONE, f"{ctx.project.name} · {PROJECT_TYPE_LABELS.get(guided_type, 'type not chosen')}",
                        items=[Item("Project", DONE, ctx.project.name),
                               Item("What is being built", DONE if guided_type else TODO,
                                    PROJECT_TYPE_LABELS.get(guided_type, "Not chosen")),
                               Item("Commercial project type", DONE, commercial.project_type if commercial else "—")],
                        actions=[Action("Open the project", url_for("projects.view_project", id=ctx.project.id),
                                        key="open-project"),
                                 Action("Change the commercial project type",
                                        url_for("projects.edit_commercial_context", id=ctx.project.id),
                                        key="edit-context")])
    guided_type = ctx.draft.get("guided_project_type")
    missing = []
    if not (ctx.draft.get("name") or "").strip():
        missing.append("Name the project.")
    if guided_type not in PROJECT_TYPE_LABELS:
        missing.append("Choose what is being built.")
    headline = (f"{ctx.draft.get('name')} · {PROJECT_TYPE_LABELS[guided_type]}" if not missing
                else "Not named yet" if not (ctx.draft.get("name") or "").strip() else "Kind of job not chosen yet")
    return StepView(DONE if not missing else TODO, headline, missing=missing, form="np_project.html",
                    form_ctx={**_type_options(), "values": {**FORM_DEFAULTS, **ctx.draft}})


def _save_type(ctx, form):
    from app.models.guided_estimating import PROJECT_TYPE_LABELS
    from app.wizards.service import WizardError, save_draft

    if ctx.project is not None:
        return "The project exists. Its name and type are changed on the project's own pages."
    value = (form.get("guided_project_type") or "").strip()
    if value and value not in PROJECT_TYPE_LABELS:
        raise WizardError("Choose what is being built.")
    fields = {k: form.get(k, "") for k in PROJECT_FIELDS}
    if fields.get("status") not in PROJECT_STATUSES:
        fields["status"] = "Lead"
    save_draft(ctx.run, fields, allowed=PROJECT_FIELDS, step="project_type", actor=ctx.actor, user_id=ctx.user_id,
               event="DRAFT_SAVED" if _wizard_action(form) else None)
    return "Saved."


# ------------------------------------------------------------------------------------------------ 3 details
def _location_options():
    from app.models.project import DEFAULT_PERMIT_CONTEXT_CLASS, PERMIT_CONTEXT_CLASSES
    from app.services.clients import form_options
    from app.services.commercial_context import (
        DELIVERY_MODELS,
        ESTIMATE_STAGES,
        EXECUTION_RISKS,
        PRICING_POSTURES,
        SCHEDULE_CONDITIONS,
        SITE_CONDITIONS,
    )

    return {"permit_context_classes": PERMIT_CONTEXT_CLASSES, "default_permit": DEFAULT_PERMIT_CONTEXT_CLASS,
            "pricing_postures": PRICING_POSTURES, "execution_risks": EXECUTION_RISKS,
            "schedule_conditions": SCHEDULE_CONDITIONS, "site_conditions": SITE_CONDITIONS,
            "estimate_stages": ESTIMATE_STAGES, "delivery_models": DELIVERY_MODELS, **form_options()}


def _role_labels():
    from app.models.guided_estimating import CONTRACTOR_ROLE_LABELS, PROJECT_TYPE_LABELS

    return CONTRACTOR_ROLE_LABELS, PROJECT_TYPE_LABELS


def _location(ctx):
    """Step 3, Details: the job site, the project settings, your role and the Project Lead. Continue creates it."""
    from app.models.project import LOCATION_COMPLETE
    from app.services.clients import location_values
    from app.wizards.lead import lead_form_ctx

    roles, types = _role_labels()
    if ctx.project is not None:
        location = ctx.project.location
        complete = location is not None and location.completeness == LOCATION_COMPLETE
        address = ", ".join(x for x in ((location.street, location.municipality, location.province_state)
                                        if location else ()) if x) or (ctx.project.address or "")
        commercial = ctx.project.current_commercial_context
        from app.services.project_lead import lead_name

        items = [Item("Job location", DONE if complete else TODO,
                      "Complete" if complete else "Incomplete: street, city, province and country are needed for "
                                                  "the permit report"),
                 Item("Project settings", DONE, (f"{commercial.pricing_posture} pricing · {commercial.estimate_stage}"
                                                 f" · {commercial.delivery_model}") if commercial else "—"),
                 Item("Your role", DONE if ctx.guided is not None else TODO,
                      ctx.guided.contractor_role_label if ctx.guided is not None else "Not chosen yet"),
                 Item("Project Lead", DONE if ctx.project.project_lead_user_id else INFO, lead_name(ctx.project))]
        form_ctx = {**lead_form_ctx(ctx), "roles": roles, "types": types, "need_role": ctx.guided is None,
                    "chosen_type": ctx.draft.get("guided_project_type", ""),
                    "chosen_role": ctx.draft.get("contractor_role", "")}
        return StepView(DONE if ctx.guided is not None else TODO,
                        ("Job site: " + address) if address else "Project created — no job address yet",
                        items=items, missing=[] if ctx.guided is not None else ["Choose your role on this job."],
                        actions=[Action("Review the job location", url_for("projects.edit_project_location",
                                                                           id=ctx.project.id), key="edit-location"),
                                 Action("Change the project settings", url_for("projects.edit_commercial_context",
                                                                               id=ctx.project.id),
                                        key="edit-context"),
                                 Action("Permit report", url_for("projects.view_permit_report", id=ctx.project.id),
                                        key="permit-report")],
                        form="np_details_after.html", form_ctx=form_ctx,
                        note="The project was created once. A second press never makes another.")
    missing = []
    if not (ctx.draft.get("name") and ctx.draft.get("guided_project_type")):
        missing.append("Step 1: name the project and choose what is being built.")
    if _chosen_client(ctx) is None:
        missing.append("Step 2: choose the customer.")
    ready = not missing
    missing.append("Continue creates the project.")
    values = {**FORM_DEFAULTS, **ctx.draft}
    hidden = {k: values.get(k, "") for k in ("client_id", "name", "project_number", "description", "project_type",
                                              "status")}
    client = _chosen_client(ctx)
    return StepView(TODO, "Ready to create the project" if ready else "Steps 1 and 2 come first", missing=missing,
                    form="np_location.html",
                    form_ctx={**_location_options(), "values": values, "hidden": hidden, "ready": ready,
                              "continue_url": url_for("projects.create_project") if ready else None,
                              "customer_address": location_values(client),
                              "customer_name": client.name if client is not None else "",
                              "roles": roles, "lead_people": lead_form_ctx(ctx)["people"]})


def start_estimate_after_create(run, project, *, actor, user_id) -> str:
    """Called by projects.create_project once the wizard's project exists: start its guided estimate with the role
    chosen on Details (the project type chosen on Project). Returns a message; a refusal leaves the project as it is
    and the role is asked again on Details."""
    from app.services import guided_estimating as G
    from app.wizards.service import draft_fields

    draft = draft_fields(run)
    role = (draft.get("contractor_role") or "").strip()
    if not role or G.get_guided(project.organization_id, project.id) is not None:
        return ""
    try:
        G.start_guided_estimate(organization_id=project.organization_id, project_id=project.id,
                                project_type=draft.get("guided_project_type", ""), contractor_role=role,
                                actor=actor, user_id=user_id)
    except G.GuidedEstimatingError as exc:
        from app import db

        db.session.rollback()
        return f"Your role was not recorded: {exc} Choose it again on Details."
    return ""


def _save_location(ctx, form):
    from app.wizards.service import save_draft

    if ctx.project is not None:
        # After creation: your role (if not recorded yet) and the Project Lead, only on a real press (never autosave).
        if not _wizard_action(form):
            return "Saved."
        messages = []
        role = (form.get("contractor_role") or "").strip()
        if ctx.guided is None and role:
            from app.services import guided_estimating as G
            from app.wizards.service import WizardError

            try:
                G.start_guided_estimate(organization_id=ctx.organization_id, project_id=ctx.project.id,
                                        project_type=form.get("guided_project_type")
                                        or ctx.draft.get("guided_project_type", ""),
                                        contractor_role=role, actor=ctx.actor, user_id=ctx.user_id)
            except G.GuidedEstimatingError as exc:
                raise WizardError(str(exc)) from exc
            messages.append("Your role is recorded.")
        if form.get("project_lead_user_id") is not None:
            from app.wizards.lead import save_lead

            messages.append(save_lead(ctx, form, step="location"))
        return " ".join(messages) or "Saved."
    save_draft(ctx.run, {k: form.get(k, "") for k in LOCATION_FIELDS}, allowed=LOCATION_FIELDS, step="location",
               actor=ctx.actor, user_id=ctx.user_id, event="DRAFT_SAVED" if _wizard_action(form) else None)
    return "Saved."


# ------------------------------------------------------------------------------------------------ 4 plans and information
def _plan_facts(ctx):
    from app.plan_intelligence.models import DrawingPackage, DrawingRevision, PlanMeasurement, PlanSheet
    from app.services.project_work_package import project_plans

    documents = project_plans(ctx.organization_id, ctx.project.id)
    sheets = (PlanSheet.query.join(DrawingRevision, PlanSheet.drawing_revision_id == DrawingRevision.id)
              .join(DrawingPackage, DrawingRevision.package_id == DrawingPackage.id)
              .filter(DrawingPackage.project_id == ctx.project.id).all())
    ids = [s.id for s in sheets]
    measurements = 0
    if ids:
        measurements = PlanMeasurement.query.filter(PlanMeasurement.sheet_id.in_(ids),
                                                    PlanMeasurement.status != "void").count()
    return {"documents": documents, "sheets": len(sheets), "measurements": measurements}


PLAN_REVIEW_CHOICES = {
    "measured": "Measurements were taken on the drawings and checked.",
    "manual": "Drawing measurements are not available or not reliable: quantities will be entered and confirmed by hand.",
}


def _documents(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    from app.services.project_drawing_requirement import (
        DRAWING_STATE_NOT_REQUIRED,
        DRAWING_STATE_PRESENT,
        derive_drawing_state,
    )
    from app.wizards.service import has_event

    facts = _plan_facts(ctx)
    state = derive_drawing_state(ctx.project.drawing_requirement, bool(facts["documents"]))
    pid = ctx.project.id
    reviewed = has_event(ctx.run, "CONFIRMED", "view_plan")
    items = [Item(d.original_filename, DONE, "", url_for("plan_intelligence.view_plan", project_id=pid,
                                                         document_id=d.id)) for d in facts["documents"]]
    if reviewed:
        items.append(Item("Your review of the drawings", DONE, reviewed.detail))
    actions = [Action("Generate construction drawings", url_for("construction_drawings.index", project_id=pid),
                      key="generate-drawings"),
               Action("Site plans", url_for("site_plans.project", project_id=pid), key="site-plans")]
    if facts["documents"]:
        actions.insert(0, Action("Open the drawings", url_for("plan_intelligence.list_plans", project_id=pid),
                                 key="view-plan"))
    form_ctx = {"multipart": True, "has_drawings": bool(facts["documents"]), "measurements": facts["measurements"],
                "not_required": state == DRAWING_STATE_NOT_REQUIRED, "reviewed": bool(reviewed)}
    if state == DRAWING_STATE_PRESENT:
        n = len(facts["documents"])
        return StepView(DONE, f"{n} drawing{'s' if n != 1 else ''} on the project", items=items, actions=actions,
                        form="np_plans.html", form_ctx=form_ctx)
    if state == DRAWING_STATE_NOT_REQUIRED:
        return StepView(DONE, "No drawings needed for this project (recorded)", items=items, actions=actions,
                        form="np_plans.html", form_ctx=form_ctx)
    return StepView(TODO, "No drawings yet — add them now, or later from the project", items=items, actions=actions,
                    form="np_plans.html", form_ctx=form_ctx)


def _plan_already_on_project(ctx, upload):
    """The project's plan with exactly these bytes, if there is one. Leaves the upload ready to read again."""
    import hashlib

    from app.plan_intelligence.models import PlanDocument

    data = upload.stream.read()
    upload.stream.seek(0)
    if not data:
        return None
    digest = hashlib.sha256(data).hexdigest()
    return (PlanDocument.query.filter_by(project_id=ctx.project.id, sha256_hex=digest, archived_at=None)
            .order_by(PlanDocument.id).first())


def _save_documents(ctx, form):
    """Upload a plan PDF (the Plans page's own service), record that none are needed, or record the review."""
    from app import db
    from app.wizards.service import WizardError, confirm

    if ctx.project is None:
        raise WizardError("Create the project first.")
    messages = []
    upload = request.files.get("plan_file") if request.files else None
    if upload is not None and (upload.filename or "").strip():
        from app.plan_intelligence.services import PlanIntelligenceServiceError, upload_plan_pdf

        # The same PDF sent twice (a second Save & Continue while the first was still uploading, or Back and
        # Save & Continue again with the file still chosen) is kept once (Production defect, 28 Oct 2026).
        already = _plan_already_on_project(ctx, upload)
        if already is not None:
            messages.append(f"{already.original_filename} is already on the project (not added again).")
        else:
            try:
                document = upload_plan_pdf(ctx.project, upload, notes=(form.get("plan_notes") or "").strip())
            except PlanIntelligenceServiceError as exc:
                db.session.rollback()
                raise WizardError(str(exc)) from exc
            messages.append(f"{document.original_filename} added to the project.")
    if form.get("drawings_choice") == "none":
        from app.services.project_drawing_requirement import (
            ProjectDrawingRequirementError,
            set_project_drawing_requirement,
        )

        try:
            set_project_drawing_requirement(organization_id=ctx.organization_id, project_id=ctx.project.id,
                                            requirement="NOT_REQUIRED")
        except ProjectDrawingRequirementError as exc:
            raise WizardError(str(exc)) from exc
        messages.append("Recorded: this project needs no drawings.")
    choice = form.get("plan_review") or ""
    if choice in PLAN_REVIEW_CHOICES:
        if choice == "measured" and not _plan_facts(ctx)["measurements"]:
            raise WizardError("No measurement has been taken on these drawings yet. Measure on a sheet first, or "
                              "choose that quantities will be entered by hand.")
        note = " ".join((form.get("plan_note") or "").split())[:300]
        confirm(ctx.run, "view_plan", actor=ctx.actor, user_id=ctx.user_id,
                detail=PLAN_REVIEW_CHOICES[choice] + (f" Note: {note}" if note else ""))
        messages.append("Your review of the drawings is recorded.")
    text = " ".join(messages) or "Saved."
    # A PDF sent with Save & Continue: say on Step 5 what happened to it (added, or already there).
    return (text, None) if upload is not None and (upload.filename or "").strip() else text


# ------------------------------------------------------------------------------------------------ 5 review
def outstanding(ctx):
    """What is still missing on the project's setup (listed on the review and kept on the project)."""
    out = []
    if ctx.project is None:
        return ["The project is not created yet."]
    from app.models.project import LOCATION_COMPLETE
    from app.services.clients import missing_information

    client = ctx.project.client
    if client is not None:
        missing = missing_information(client)
        if missing:
            out.append(f"Customer information: {', '.join(missing).lower()} (listed under What needs my attention).")
    location = ctx.project.location
    if location is None or location.completeness != LOCATION_COMPLETE:
        out.append("The job location is incomplete.")
    if _documents(ctx).state != DONE:
        out.append("No drawings yet, and no record that none are needed.")
    if ctx.guided is None:
        out.append("Your role on the project is not chosen.")
    return out


def review_sections(ctx) -> list:
    """The review, by section, each with the step that edits it: [(title, edit_step_key, [(label, value)])]."""
    from app.models.appointment import APPOINTMENT_STATUS_ACTIVE, CompanyAppointment
    from app.models.guided_estimating import PROJECT_TYPE_LABELS
    from app.services.clients import location_values
    from app.services.commercial_context import delivery_model_label
    from app.services.project_lead import lead_name

    project = ctx.project
    commercial = project.current_commercial_context
    location = project.location
    address = ", ".join(x for x in ((location.street, location.municipality, location.province_state,
                                     location.postal_zip) if location else ()) if x) or (project.address or "—")
    guided_type = ctx.guided.project_type if ctx.guided is not None else ctx.draft.get("guided_project_type")
    client = project.client
    contact = location_values(client) if client is not None else {}
    customer_address = ", ".join(x for x in (contact.get("street"), contact.get("municipality"),
                                             contact.get("province_state"), contact.get("postal_zip")) if x)
    facts = _plan_facts(ctx)
    plans = ", ".join(d.original_filename for d in facts["documents"]) or (
        "Not needed (recorded)" if _documents(ctx).state == DONE else "None yet")
    appointments = (CompanyAppointment.query.filter_by(organization_id=ctx.organization_id, project_id=project.id,
                                                       status=APPOINTMENT_STATUS_ACTIVE)
                    .order_by(CompanyAppointment.appointment_date.asc()).all())
    visits = "; ".join(f"{a.appointment_date:%b %d, %Y} — {a.title}" for a in appointments[:4]) + (
        f" (+{len(appointments) - 4} more)" if len(appointments) > 4 else "")
    return [
        ("Project information", "project_type", [
            ("Name", project.name), ("Project #", project.project_number or "—"),
            ("What is being built", PROJECT_TYPE_LABELS.get(guided_type, "—")),
            ("Commercial type", commercial.project_type if commercial else "—"), ("Status", project.status),
            ("Description", project.description or "—")]),
        ("Customer", "customer", [
            ("Customer", client.name if client else "—"), ("Company", (client.company if client else "") or "—"),
            ("Phone", (client.phone if client else "") or "—"), ("Email", (client.email if client else "") or "—"),
            ("Address", customer_address or "—")]),
        ("Site and project details", "location", [
            ("Job site", address), ("Permit class", (project.current_permit_profile.permit_context_class
                                                     if project.current_permit_profile is not None else "—")),
            ("Pricing posture", commercial.pricing_posture if commercial else "—"),
            ("Execution risk", commercial.execution_risk if commercial else "—"),
            ("Schedule / site", f"{commercial.schedule_condition} / {commercial.site_condition}" if commercial else "—"),
            ("Estimate stage", commercial.estimate_stage if commercial else "—"),
            ("Delivery model", delivery_model_label(commercial.delivery_model) if commercial else "—")]),
        ("Your role and the Project Lead", "location", [
            ("Your role", ctx.guided.contractor_role_label if ctx.guided is not None else "Not chosen"),
            ("Project Lead", lead_name(project)),
            ("Visits and meetings", visits or "None yet (Company Calendar)")]),
        ("Plans and documents", "documents", [
            ("Plans", plans)]),
    ]


def _review(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    from app.wizards.service import has_event

    missing = outstanding(ctx)
    confirmed = has_event(ctx.run, "CONFIRMED", "review")
    return StepView(DONE if confirmed else INFO,
                    "Everything is in place" if not missing else f"{len(missing)} thing{'s' if len(missing) != 1 else ''}"
                    " still to add later",
                    items=[], form="np_review.html",
                    actions=[Action("Add a site visit or meeting to the Company Calendar",
                                    url_for("schedule.new_appointment", project_id=ctx.project.id, scope="company"),
                                    key="new-appointment")],
                    form_ctx={"sections": review_sections(ctx), "outstanding": missing, "custom_finish": True,
                              "can_estimate": ctx.guided is not None,
                              "finish_url": ctx.step_url("review", choice="finish")})


def _finish(ctx, form):
    """Finish the setup and show Project Created (Open Project, Start Guided Estimating, Create Another Project)."""
    from app.wizards import service as S

    if ctx.project is None:
        raise S.WizardError("Create the project first.")
    choice = form.get("choice") or request.args.get("choice") or ""
    if not ctx.run.is_active and choice:
        return "", url_for("wizards.project_created", run_id=ctx.run.id)  # Finish pressed twice: finished once
    if choice not in ("finish", "estimate", "later"):
        return "Saved."
    missing = outstanding(ctx)
    S.confirm(ctx.run, "review", actor=ctx.actor, user_id=ctx.user_id,
              detail="Project setup confirmed." + (f" Outstanding: {'; '.join(missing)}" if missing else ""))
    S.finish(ctx.run, actor=ctx.actor, user_id=ctx.user_id)
    if choice == "estimate" and ctx.guided is not None:
        run = S.start_contractor_run(WIZARD_GUIDED_ESTIMATING, organization_id=ctx.organization_id,
                                     actor=ctx.actor, user_id=ctx.user_id, project_id=ctx.project.id)
        return "Project set up. Guided Estimating is next.", url_for("wizards.resume", run_id=run.id)
    return "", url_for("wizards.project_created", run_id=ctx.run.id)


STEPS = (
    Step("project_type", "Project",
         "Key information about the project. You can change it later on the project's own pages.",
         "Name the project and choose what is being built. The commercial type and status are pre-filled.",
         "Next, the customer.",
         _project_type, handle=_save_type, draft=True,
         manual=lambda ctx: ("Project page", url_for("projects.view_project", id=ctx.project.id))
         if ctx.project else ("New Project form", url_for("projects.create_project"))),
    Step("customer", "Customer",
         "Select an existing customer or add a new one right here. Only the name is needed now.",
         "Choose the customer from the list, or press Add New Customer and enter their name (email, phone and "
         "address can be added later; CalibraytAI reminds you).",
         "Next, the site and project details.",
         _customer, handle=_save_customer, draft=True,
         manual=lambda ctx: ("New Project form", url_for("projects.create_project"))),
    Step("location", "Details",
         "The job site (for the permit report and the contract), the project settings, your role on the job and "
         "the Project Lead. Continue creates the project, once.",
         "Enter the job-site address (or use the customer's), check the pre-filled settings, choose your role, then "
         "Continue. The work itself is chosen later, in Guided Estimating.",
         "Next, the plans and drawings.",
         _location, handle=_save_location, draft=True,
         manual=lambda ctx: ("Job location", url_for("projects.edit_project_location", id=ctx.project.id))
         if ctx.project else ("New Project form", url_for("projects.create_project"))),
    Step("documents", "Plans",
         "Add the plan PDFs you have now, record that this job needs none, or carry on and add them later.",
         "Choose a PDF to add it, or choose No drawings needed. Nothing here stops you going on.",
         "Last, review the project.",
         _documents, required=False, handle=_save_documents, continue_form=True,
         manual=lambda ctx: ("Project plans", url_for("plan_intelligence.list_plans", project_id=ctx.project.id))
         if ctx.project else None),
    Step("review", "Review",
         "Everything the project has, by section, and anything still to add later.",
         "Check each section (Edit goes back to it), then press Finish.",
         "Project Created: open the project, start Guided Estimating, or create another project.",
         _review, required=False, handle=_finish, continue_form=True,
         manual=lambda ctx: ("Project setup", url_for("projects.project_setup", id=ctx.project.id))
         if ctx.project else None),
)


def _subject(ctx):
    if ctx.project is not None:
        client = ctx.project.client
        return ctx.project.name + (f" — {client.name}" if client is not None else "")
    client = _chosen_client(ctx)
    name = ctx.draft.get("name") or ""
    if client is not None or name:
        return " — ".join(x for x in (name or "New project", client.name if client is not None else "") if x)
    return "New project (not created yet)"


WIZARD = Wizard(
    key=WIZARD_NEW_PROJECT, side="CONTRACTOR", title="Start a New Project",
    short="Project, customer, details, plans and a review — five compact steps, then estimating.",
    audience="Contractors and office staff",
    steps=STEPS, manual_label="New Project form",
    manual_url=lambda ctx=None: url_for("projects.create_project"),
    subject=_subject, finish_label="Finish", compact=True,
)

_ = NOT_NEEDED
