"""Wizard 1 — Start a New Project (brief §2).

Steps 1 to 3 keep the answers in the run's draft until the project exists; "Create the project" posts them to the
existing New Project form handler (projects.create_project), which creates the project, its commercial context and
its location exactly as the manual form does, and claims the run once (a second press creates nothing). From then
on every step reads and changes the project's own records through the existing pages and services.
No dimension, quantity or specification is ever filled in by the wizard.
"""

from __future__ import annotations

from flask import url_for

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

CUSTOMER_FIELDS = ("client_id", "name", "project_number", "description")
TYPE_FIELDS = ("guided_project_type", "project_type", "status")
LOCATION_FIELDS = ("address", "street", "municipality", "province_state", "postal_zip", "country",
                   "permit_context_class", "pricing_posture", "execution_risk", "schedule_condition",
                   "site_condition", "estimate_stage", "delivery_model", "justification_reason")
DRAFT_FIELDS = CUSTOMER_FIELDS + TYPE_FIELDS + LOCATION_FIELDS + ("contractor_role",)
# The manual form's own defaults (templates/projects/form.html), so the wizard and the form start the same way.
FORM_DEFAULTS = {"status": "Lead", "project_type": "New Build", "pricing_posture": "Competitive",
                 "execution_risk": "Normal", "schedule_condition": "Normal", "site_condition": "Normal",
                 "estimate_stage": "Preliminary", "delivery_model": "Self-Perform", "country": "Canada"}
PROJECT_STATUSES = ("Lead", "Estimating")


def _clients(ctx):
    from app.models import Client
    from app.services.time_entry import customer_clients_only

    query = Client.query.filter_by(organization_id=ctx.organization_id)
    return customer_clients_only(query, ctx.organization_id).order_by(Client.name.asc()).all()


def _value(ctx, key):
    return ctx.draft.get(key) or FORM_DEFAULTS.get(key, "")


def _project_or_todo(ctx, headline="Create the project first (step 3)."):
    if ctx.project is None:
        return StepView(TODO, headline, missing=[headline])
    return None


# ------------------------------------------------------------------------------------------------ 1 customer
def _customer(ctx):
    if ctx.project is not None:
        client = ctx.project.client
        return StepView(DONE, f"Customer {client.name if client else '—'} · project {ctx.project.name}",
                        items=[Item("Customer", DONE, client.name if client else "Not in this company"),
                               Item("Project", DONE, ctx.project.name)],
                        actions=[Action("Correct the customer", url_for("projects.correct_project_client_page",
                                                                        id=ctx.project.id), key="correct-client"),
                                 Action("Open the project", url_for("projects.view_project", id=ctx.project.id),
                                        key="open-project")],
                        note="The project exists. Its name, customer and details are changed on the project's own pages.")
    clients = _clients(ctx)
    missing = []
    chosen = next((c for c in clients if str(c.id) == str(ctx.draft.get("client_id"))), None)
    if chosen is None:
        missing.append("Choose the customer (or add a new customer first).")
    if not (ctx.draft.get("name") or "").strip():
        missing.append("Name the project.")
    view = StepView(DONE if not missing else TODO,
                    f"Customer {chosen.name} · project {ctx.draft.get('name')}" if not missing
                    else "Who is the customer, and what is the job called?",
                    missing=missing, form="new_project_customer.html",
                    form_ctx={"clients": clients, "values": ctx.draft},
                    actions=[Action("Add a new customer", url_for("clients.create_client"), key="add-client",
                                    note="Opens the customer form. Come back here when it is saved.")])
    return view


def _save_customer(ctx, form):
    from app.wizards.service import WizardError, save_draft

    client_id = (form.get("client_id") or "").strip()
    if client_id and not any(str(c.id) == client_id for c in _clients(ctx)):
        raise WizardError("Choose a customer of this company.")
    save_draft(ctx.run, {k: form.get(k, "") for k in CUSTOMER_FIELDS}, allowed=CUSTOMER_FIELDS, step="customer",
               actor=ctx.actor, user_id=ctx.user_id, event="DRAFT_SAVED")
    return "Saved."


# ------------------------------------------------------------------------------------------------ 2 project type
def _type_options():
    from app.models.guided_estimating import PROJECT_TYPE_LABELS
    from app.services.commercial_context import PROJECT_TYPES
    from app.services.guided_estimating import COMMERCIAL_TYPE_HINT

    return {"guided_types": PROJECT_TYPE_LABELS, "commercial_types": PROJECT_TYPES, "hints": COMMERCIAL_TYPE_HINT,
            "statuses": PROJECT_STATUSES}


def _project_type(ctx):
    from app.models.guided_estimating import PROJECT_TYPE_LABELS

    guided_type = ctx.guided.project_type if ctx.guided is not None else ctx.draft.get("guided_project_type")
    commercial = ctx.project.current_commercial_context if ctx.project is not None else None
    if ctx.project is not None:
        items = [Item("What is being built", DONE if guided_type else TODO,
                      PROJECT_TYPE_LABELS.get(guided_type, "Choose it in step 6")),
                 Item("Commercial project type", DONE, commercial.project_type if commercial else "—")]
        actions = [Action("Change the commercial project type", url_for("projects.edit_commercial_context",
                                                                        id=ctx.project.id), key="edit-context")]
        return StepView(DONE if guided_type else TODO,
                        PROJECT_TYPE_LABELS.get(guided_type, "Project type not chosen yet"),
                        items=items, actions=actions,
                        missing=[] if guided_type else ["Choose what is being built."],
                        form=None if ctx.guided is not None else "new_project_type.html",
                        form_ctx={**_type_options(), "values": {**FORM_DEFAULTS, **ctx.draft}, "locked": True})
    missing = [] if guided_type in PROJECT_TYPE_LABELS else ["Choose what is being built."]
    return StepView(DONE if not missing else TODO,
                    PROJECT_TYPE_LABELS.get(guided_type, "What is being built?"), missing=missing,
                    form="new_project_type.html", form_ctx={**_type_options(),
                                                            "values": {**FORM_DEFAULTS, **ctx.draft}, "locked": False})


def _save_type(ctx, form):
    from app.models.guided_estimating import PROJECT_TYPE_LABELS
    from app.wizards.service import WizardError, save_draft

    value = (form.get("guided_project_type") or "").strip()
    if value and value not in PROJECT_TYPE_LABELS:
        raise WizardError("Choose what is being built.")
    if ctx.project is not None:
        # The project exists but its guided estimate does not yet: the type waits in the run for step 6.
        run = ctx.run
        draft = dict((run.draft_json or {}).get("fields") or {})
        draft["guided_project_type"] = value
        run.draft_json = {"fields": draft}
        from app import db
        from app.wizards.service import record

        record(run, "DRAFT_SAVED", actor=ctx.actor, step="project_type", user_id=ctx.user_id)
        db.session.commit()
        return "Saved."
    fields = {k: form.get(k, "") for k in TYPE_FIELDS}
    if fields.get("status") not in PROJECT_STATUSES:
        fields["status"] = "Lead"
    save_draft(ctx.run, fields, allowed=TYPE_FIELDS, step="project_type", actor=ctx.actor, user_id=ctx.user_id,
               event="DRAFT_SAVED")
    return "Saved."


# ------------------------------------------------------------------------------------------------ 3 location
def _location_options():
    from app.models.project import DEFAULT_PERMIT_CONTEXT_CLASS, PERMIT_CONTEXT_CLASSES
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
            "estimate_stages": ESTIMATE_STAGES, "delivery_models": DELIVERY_MODELS}


def _location(ctx):
    from app.models.project import LOCATION_COMPLETE

    if ctx.project is not None:
        location = ctx.project.location
        complete = location is not None and location.completeness == LOCATION_COMPLETE
        address = ", ".join(x for x in ((location.street, location.municipality, location.province_state)
                                        if location else ()) if x) or (ctx.project.address or "")
        items = [Item("Job location", DONE if complete else TODO,
                      address or "No address yet" if complete else (address or "Incomplete") + " — incomplete"),
                 Item("Commercial decision gate", DONE, "Recorded with the project (versioned)")]
        return StepView(DONE, "Project created" + ("" if complete else " — the job location is not complete yet"),
                        items=items,
                        actions=[Action("Review the job location", url_for("projects.edit_project_location",
                                                                           id=ctx.project.id), key="edit-location"),
                                 Action("Permit report", url_for("projects.view_permit_report", id=ctx.project.id),
                                        key="permit-report")],
                        note="The project was created once. A second press of Create never makes another.")
    missing = []
    if not (ctx.draft.get("client_id") and ctx.draft.get("name")):
        missing.append("Step 1: choose the customer and name the project.")
    if not ctx.draft.get("guided_project_type"):
        missing.append("Step 2: choose what is being built.")
    missing.append("Create the project.")
    values = {**FORM_DEFAULTS, **ctx.draft}
    hidden = {k: values.get(k, "") for k in CUSTOMER_FIELDS + ("project_type", "status")}
    return StepView(TODO, "Where is the job? Then create the project.", missing=missing,
                    form="new_project_location.html",
                    form_ctx={**_location_options(), "values": values, "hidden": hidden,
                              "ready": len(missing) == 1, "create_url": url_for("projects.create_project"),
                              "run_id": ctx.run.id})


def _save_location(ctx, form):
    from app.wizards.service import save_draft

    save_draft(ctx.run, {k: form.get(k, "") for k in LOCATION_FIELDS}, allowed=LOCATION_FIELDS, step="location",
               actor=ctx.actor, user_id=ctx.user_id, event="DRAFT_SAVED")
    return "Saved."


# ------------------------------------------------------------------------------------------------ 4 documents
def _plan_facts(ctx):
    from app.plan_intelligence.models import DrawingPackage, DrawingRevision, PlanMeasurement, PlanScaleCalibration, PlanSheet
    from app.services.project_work_package import project_plans

    documents = project_plans(ctx.organization_id, ctx.project.id)
    sheets = (PlanSheet.query.join(DrawingRevision, PlanSheet.drawing_revision_id == DrawingRevision.id)
              .join(DrawingPackage, DrawingRevision.package_id == DrawingPackage.id)
              .filter(DrawingPackage.project_id == ctx.project.id).all())
    ids = [s.id for s in sheets]
    measurements = calibrations = 0
    if ids:
        measurements = PlanMeasurement.query.filter(PlanMeasurement.sheet_id.in_(ids),
                                                    PlanMeasurement.status != "void").count()
        calibrations = PlanScaleCalibration.query.filter(PlanScaleCalibration.sheet_id.in_(ids),
                                                         PlanScaleCalibration.calibration_status != "void").count()
    return {"documents": documents, "sheets": len(sheets), "measurements": measurements, "calibrations": calibrations}


def _documents(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    from app.services.project_drawing_requirement import (
        DRAWING_STATE_NOT_REQUIRED,
        DRAWING_STATE_PRESENT,
        derive_drawing_state,
    )

    facts = _plan_facts(ctx)
    state = derive_drawing_state(ctx.project.drawing_requirement, bool(facts["documents"]))
    pid = ctx.project.id
    actions = [Action("Upload a plan PDF", url_for("plan_intelligence.upload_plan", project_id=pid), primary=True,
                      key="upload-plan", note="CAD exports, plans, specifications: one PDF at a time."),
               Action("Generate construction drawings", url_for("construction_drawings.index", project_id=pid),
                      key="generate-drawings"),
               Action("Site plans", url_for("site_plans.project", project_id=pid), key="site-plans")]
    if state != DRAWING_STATE_PRESENT:
        actions.append(Action("This project needs no drawings", url_for("projects.set_project_drawing_requirement_choice",
                                                                        id=pid), method="post",
                              fields={"drawing_requirement": "NOT_REQUIRED"}, key="no-drawings"))
    items = [Item(d.original_filename, DONE, f"{d.page_count or ''} pages".strip() if getattr(d, "page_count", None) else "",
                  url_for("plan_intelligence.view_plan", project_id=pid, document_id=d.id)) for d in facts["documents"]]
    if state == DRAWING_STATE_PRESENT:
        n = len(facts["documents"])
        return StepView(DONE, f"{n} drawing{'s' if n != 1 else ''} on the project", items=items, actions=actions)
    if state == DRAWING_STATE_NOT_REQUIRED:
        return StepView(DONE, "Drawings are not required for this project (recorded).", actions=actions)
    return StepView(TODO, "No drawing on the project yet", items=items, actions=actions,
                    missing=["Upload the drawings, generate them, or record that this project needs none."])


# ------------------------------------------------------------------------------------------------ 5 view plan
def _has_drawings(ctx):
    if ctx.project is None:
        return True  # shown (not yet available) until the project exists
    from app.services.project_work_package import project_plans

    return bool(project_plans(ctx.organization_id, ctx.project.id))


def _view_plan(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    from app.services.project_plan_link import office_plan_link
    from app.wizards.service import has_event

    facts = _plan_facts(ctx)
    link = office_plan_link(ctx.project)
    confirmed = has_event(ctx.run, "CONFIRMED", "view_plan")
    items = [Item("Drawings", DONE, f"{len(facts['documents'])} document(s), {facts['sheets']} sheet(s)"),
             Item("Scale calibrations", DONE if facts["calibrations"] else TODO, str(facts["calibrations"])),
             Item("Measurements taken on the drawings", DONE if facts["measurements"] else TODO,
                  str(facts["measurements"]))]
    actions = [Action("View the project plan", link["url"] if link else url_for("plan_intelligence.list_plans",
                                                                              project_id=ctx.project.id),
                      primary=True, key="view-plan"),
               Action("Sheets and measuring", url_for("plan_intelligence.project_sheets", project_id=ctx.project.id),
                      key="sheets")]
    if confirmed:
        items.append(Item("Your review", DONE, f"{confirmed.actor_display_name}: {confirmed.detail}"))
        return StepView(DONE, "Drawings reviewed", items=items, actions=actions)
    return StepView(TODO, "Review the drawings and say what can be measured from them", items=items, actions=actions,
                    missing=["Confirm your review of the drawings."], form="new_project_plan_review.html",
                    form_ctx={"measurements": facts["measurements"]},
                    note="CalibraytAI does not read dimensions off a drawing by itself. Where a measurement is not "
                         "on the drawing or cannot be read reliably, the quantity is entered and confirmed by a "
                         "person at the estimating stage.")


PLAN_REVIEW_CHOICES = {
    "measured": "Measurements were taken on the drawings and checked.",
    "manual": "Drawing measurements are not available or not reliable: quantities will be entered and confirmed by hand.",
}


def _confirm_plan(ctx, form):
    from app.wizards.service import WizardError, confirm

    choice = form.get("plan_review") or ""
    if choice not in PLAN_REVIEW_CHOICES:
        raise WizardError("Choose what the drawings give you.")
    if choice == "measured" and not _plan_facts(ctx)["measurements"]:
        raise WizardError("No measurement has been taken on these drawings yet. Measure on a sheet first, or "
                          "choose that quantities will be entered by hand.")
    note = " ".join((form.get("plan_note") or "").split())[:300]
    confirm(ctx.run, "view_plan", actor=ctx.actor, user_id=ctx.user_id,
            detail=PLAN_REVIEW_CHOICES[choice] + (f" Note: {note}" if note else ""))
    return "Your review of the drawings is recorded."


# ------------------------------------------------------------------------------------------------ 6 role & scope
def _role_scope(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    from app.models.guided_estimating import CONTRACTOR_ROLE_LABELS, PROJECT_TYPE_LABELS

    if ctx.guided is not None:
        return StepView(DONE, f"{ctx.guided.contractor_role_label} · {ctx.guided.project_type_label}",
                        items=[Item("Your role", DONE, ctx.guided.contractor_role_label),
                               Item("What is being built", DONE, ctx.guided.project_type_label),
                               Item("Project description", INFO, (ctx.project.description or "—")[:200])],
                        note="These chose the construction stages of the project's guided estimate.")
    return StepView(TODO, "What is your role on this project?", missing=["Choose your role."],
                    form="new_project_role.html",
                    form_ctx={"roles": CONTRACTOR_ROLE_LABELS, "types": PROJECT_TYPE_LABELS,
                              "chosen_type": ctx.draft.get("guided_project_type", ""),
                              "chosen_role": ctx.draft.get("contractor_role", "")})


def _save_role(ctx, form):
    from app.services import guided_estimating as G
    from app.wizards.service import WizardError

    if ctx.project is None:
        raise WizardError("Create the project first.")
    if ctx.guided is not None:
        return "Your role is already recorded."
    try:
        G.start_guided_estimate(organization_id=ctx.organization_id, project_id=ctx.project.id,
                                project_type=form.get("guided_project_type") or ctx.draft.get("guided_project_type", ""),
                                contractor_role=form.get("contractor_role", ""), actor=ctx.actor, user_id=ctx.user_id)
    except G.GuidedEstimatingError as exc:
        raise WizardError(str(exc)) from exc
    return "Your role and the project's construction stages are set."


# ------------------------------------------------------------------------------------------------ 9 internal / subcontracted / N/A
def _stages(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    if ctx.guided is None:
        return StepView(TODO, "Choose your role first (step 6).", missing=["Choose your role first (step 6)."])
    from app.services import guided_estimating as G

    rows = G.leaf_stages(ctx.guided)
    undecided = [r for r in rows if r.responsibility is None]
    items = [Item(r.section_name, DONE if r.responsibility else TODO,
                  r.responsibility_label + (f" — {r.na_reason}" if r.na_reason else "")) for r in rows]
    decided = len(rows) - len(undecided)
    excluded = sum(1 for r in rows if r.responsibility == "NA")
    action = Action("Choose Internal, Subcontracted or N/A for each stage",
                    url_for("guided.scope", project_id=ctx.project.id), primary=True, key="open-scope")
    headline = f"{decided} of {len(rows)} stages decided" + (f" ({excluded} excluded)" if excluded else "")
    if undecided:
        return StepView(TODO, headline, items=items, actions=[action],
                        missing=[f"Decide {len(undecided)} more stage{'s' if len(undecided) != 1 else ''}: "
                                 + ", ".join(r.section_name for r in undecided[:6])
                                 + ("…" if len(undecided) > 6 else "")],
                        note="Nothing is preselected. An exclusion (N/A) keeps its reason.")
    return StepView(DONE, headline, items=items, actions=[action])


# ------------------------------------------------------------------------------------------------ 7 construction scope
def _construction_scope(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    if ctx.guided is None:
        return StepView(TODO, "Choose your role first (step 6).", missing=["Choose your role first (step 6)."])
    top = ctx.guided.top_stages
    added = sum(1 for s in top if s.is_custom)
    items = [Item(s.display_name, INFO, (s.explanation or "")[:140]) for s in top]
    return StepView(DONE, f"{len(top)} construction stages for {ctx.guided.project_type_label}"
                    + (f" ({added} added by you)" if added else ""), items=items,
                    actions=[Action("Add a stage the job needs", url_for("guided.scope", project_id=ctx.project.id)
                                    + "#stages", key="open-scope")],
                    note="The stages come from the project type. Add any stage this job needs that is not listed.")


# ------------------------------------------------------------------------------------------------ 8 stages that apply
def _applicable(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    if ctx.guided is None:
        return StepView(TODO, "Choose your role first (step 6).", missing=["Choose your role first (step 6)."])
    from app.services import guided_estimating as G

    rows = G.leaf_stages(ctx.guided)
    excluded = [r for r in rows if r.responsibility == "NA"]
    items = [Item(r.section_name, NOT_NEEDED if r.responsibility == "NA" else INFO,
                  ("N/A — " + (r.na_reason or "no reason given")) if r.responsibility == "NA" else
                  (r.responsibility_label if r.responsibility else "in the job (who does it: next step)")) for r in rows]
    return StepView(INFO, f"{len(rows) - len(excluded)} stage(s) in the job, {len(excluded)} excluded",
                    items=items, actions=[Action("Mark stages N/A (with the reason)",
                                                 url_for("guided.scope", project_id=ctx.project.id),
                                                 primary=True, key="open-scope")],
                    note="An excluded stage is N/A with its reason; it shows on the proposal's exclusions.")


# ------------------------------------------------------------------------------------------------ 10 responsibility & first dates
def _responsibility(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    from app.models.appointment import APPOINTMENT_STATUS_ACTIVE, APPOINTMENT_TYPE_LABELS, CompanyAppointment
    from app.models.user import User

    rows = (CompanyAppointment.query.filter_by(organization_id=ctx.organization_id, project_id=ctx.project.id,
                                               status=APPOINTMENT_STATUS_ACTIVE)
            .order_by(CompanyAppointment.appointment_date.asc()).all())
    items = []
    for appt in rows:
        person = User.query.get(appt.assigned_user_id) if appt.assigned_user_id else None
        items.append(Item(f"{appt.appointment_date:%b %d, %Y} — {appt.title}", DONE,
                          f"{APPOINTMENT_TYPE_LABELS.get(appt.appointment_type, appt.appointment_type)}; "
                          f"responsible: {person.display_name if person else 'not assigned'}",
                          url_for("schedule.edit_appointment", appointment_id=appt.id)))
    action = Action("Add a site visit or meeting to the Company Calendar",
                    url_for("schedule.new_appointment", project_id=ctx.project.id, scope="company"),
                    primary=True, key="new-appointment",
                    note="Choose the person responsible and the first date. Construction work is scheduled from "
                         "the work plan once the customer accepts.")
    if rows:
        return StepView(DONE, f"{len(rows)} appointment{'s' if len(rows) != 1 else ''} on the Company Calendar",
                        items=items, actions=[action])
    return StepView(TODO, "No one is booked on this project yet", actions=[action],
                    note="Optional. The construction schedule comes later, from the accepted estimate.")


# ------------------------------------------------------------------------------------------------ 9 review
def outstanding(ctx):
    """What is still missing on the project's setup, from the existing setup resolver and the steps."""
    out = []
    if ctx.project is None:
        return ["The project is not created yet."]
    from app.models.project import LOCATION_COMPLETE

    location = ctx.project.location
    if location is None or location.completeness != LOCATION_COMPLETE:
        out.append("The job location is incomplete.")
    if _documents(ctx).state != DONE:
        out.append("No drawings, and no record that none are needed.")
    elif _has_drawings(ctx) and _view_plan(ctx).state != DONE:
        out.append("The drawings are not reviewed yet.")
    if ctx.guided is None:
        out.append("Your role on the project is not chosen.")
    else:
        stages = _stages(ctx)
        if stages.state != DONE:
            out.append(stages.headline)
    return out


def _review(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    from app.services.project_setup import describe_setup
    from app.services.start_project_walk import resolve_start_project_walk
    from app.wizards.service import has_event

    setup = describe_setup(resolve_start_project_walk(ctx.organization_id, ctx.project.id))
    missing = outstanding(ctx)
    items = [Item(text, DONE) for text in setup.ready] + [Item(text, TODO) for text in missing]
    confirmed = has_event(ctx.run, "CONFIRMED", "review")
    actions = [Action("Open the project", url_for("projects.view_project", id=ctx.project.id), key="open-project")]
    if confirmed:
        return StepView(DONE, f"Setup confirmed by {confirmed.actor_display_name}", items=items, actions=actions,
                        note=("Still outstanding: " + "; ".join(missing)) if missing else "")
    return StepView(TODO, "Check the setup and confirm it", items=items, actions=actions,
                    missing=["Confirm the project setup."], form="confirm.html",
                    form_ctx={"label": "Confirm the project setup", "outstanding": missing,
                              "text": "I checked the customer, project type, location, drawings, role and stages."})


def _confirm_review(ctx, form):
    from app.wizards.service import WizardError, confirm

    if not form.get("confirmed"):
        raise WizardError("Tick the box to confirm the setup.")
    missing = outstanding(ctx)
    confirm(ctx.run, "review", actor=ctx.actor, user_id=ctx.user_id,
            detail="Project setup confirmed." + (f" Outstanding: {'; '.join(missing)}" if missing else ""))
    return "Project setup confirmed."


# ------------------------------------------------------------------------------------------------ 10 continue
def _continue(ctx):
    blocked = _project_or_todo(ctx)
    if blocked:
        return blocked
    return StepView(INFO, "Continue into Guided Estimating now, or save the project for later",
                    form="new_project_continue.html", form_ctx={},
                    actions=[Action("Open the project", url_for("projects.view_project", id=ctx.project.id),
                                    key="open-project")])


def _continue_handle(ctx, form):
    from app.wizards import service as S

    if ctx.project is None:
        raise S.WizardError("Create the project first.")
    if form.get("choice") == "estimate":
        S.finish(ctx.run, actor=ctx.actor, user_id=ctx.user_id)
        run = S.start_contractor_run(WIZARD_GUIDED_ESTIMATING, organization_id=ctx.organization_id,
                                     actor=ctx.actor, user_id=ctx.user_id, project_id=ctx.project.id)
        return "Project set up. Guided Estimating is next.", url_for("wizards.resume", run_id=run.id)
    S.finish(ctx.run, actor=ctx.actor, user_id=ctx.user_id)
    return ("Project saved. Start Guided Estimating from Home or the project page when you are ready.",
            url_for("projects.view_project", id=ctx.project.id))


STEPS = (
    Step("customer", "Customer and project",
         "Who the job is for and what it is called.",
         "Choose the customer (add one first if they are new), name the project and describe it in a line.",
         "Next, choose what is being built.",
         _customer, handle=_save_customer, draft=True,
         manual=lambda ctx: ("New Project form", url_for("projects.create_project"))),
    Step("project_type", "Project type",
         "What is being built: a new home, a garage, an addition or renovation, a foundation, or another job.",
         "Choose the type. It picks the construction stages for the estimate; the commercial project type is "
         "pre-filled from it and can be changed.",
         "Next, the job location and the basic commercial requirements.",
         _project_type, handle=_save_type, draft=True,
         manual=lambda ctx: ("Project page", url_for("projects.view_project", id=ctx.project.id))
         if ctx.project else ("New Project form", url_for("projects.create_project"))),
    Step("location", "Location and basic requirements",
         "The job address (for permits and the contract) and the commercial decision gate kept with every estimate.",
         "Enter the civic address, check the commercial choices, then press Create the project. It is created once.",
         "Next, add the drawings, specifications and documents.",
         _location, handle=_save_location, draft=True,
         manual=lambda ctx: ("Job location", url_for("projects.edit_project_location", id=ctx.project.id))
         if ctx.project else ("New Project form", url_for("projects.create_project"))),
    Step("documents", "Drawings and documents",
         "The plans everyone works from: CAD exports and plan PDFs, specifications and supporting documents.",
         "Upload each PDF, generate construction drawings, or record that this job needs no drawings.",
         "Next, review the drawings in View Plan.",
         _documents,
         manual=lambda ctx: ("Project plans", url_for("plan_intelligence.list_plans", project_id=ctx.project.id))
         if ctx.project else None),
    Step("view_plan", "Review the drawings",
         "Look through the drawings with View Plan before estimating.",
         "Open the plan, check the sheets, measure where the drawing allows, and record what the drawings give you.",
         "Next, your role on the project.",
         _view_plan, applies=_has_drawings, handle=_confirm_plan,
         manual=lambda ctx: ("Plan sheets", url_for("plan_intelligence.project_sheets", project_id=ctx.project.id))
         if ctx.project else None),
    Step("role", "Your role", "Whether you are the general contractor, do selected portions, or are a subcontractor "
         "for a defined scope.",
         "Choose your role. With the project type it sets the construction stages.",
         "Next, the construction scope.",
         _role_scope, handle=_save_role,
         manual=lambda ctx: ("Start New Estimate", url_for("guided.start"))),
    Step("construction_scope", "Construction scope", "The construction stages of this job, in building order.",
         "Read the stages. Add any stage the job needs that is not listed.",
         "Next, the stages that apply and the exclusions.",
         _construction_scope,
         manual=lambda ctx: ("Construction scope", url_for("guided.scope", project_id=ctx.project.id))
         if ctx.project else None),
    Step("applicable", "Stages that apply and exclusions", "Which stages are part of this job and which are not.",
         "Mark a stage N/A (with the reason) if it is not in this job.",
         "Next, who does each stage.",
         _applicable,
         manual=lambda ctx: ("Construction scope", url_for("guided.scope", project_id=ctx.project.id))
         if ctx.project else None),
    Step("stages", "Internal, Subcontracted or N/A",
         "Who does each stage: your crew (Internal), a subcontractor, or not in this job (N/A).",
         "Choose for every stage on the construction scope. Nothing is preselected.",
         "Next, who is responsible and the first dates.",
         _stages,
         manual=lambda ctx: ("Construction scope", url_for("guided.scope", project_id=ctx.project.id))
         if ctx.project else None),
    Step("responsibility", "Responsibility and first dates",
         "Who looks after the job at first, and the first visit or meeting on the Company Calendar.",
         "Add a site visit, estimate consultation or customer meeting with the person responsible.",
         "Next, review and confirm the setup.",
         _responsibility, required=False,
         manual=lambda ctx: ("Company Calendar", url_for("schedule.company"))),
    Step("review", "Review and confirm",
         "Everything the project has, and anything still missing.",
         "Check the list. Confirm it; anything outstanding stays listed on the project.",
         "Last, continue into Guided Estimating or save for later.",
         _review, handle=_confirm_review,
         manual=lambda ctx: ("Project setup", url_for("projects.project_setup", id=ctx.project.id))
         if ctx.project else None),
    Step("continue", "Continue",
         "Start estimating now with Guided Estimating, or stop here and come back later.",
         "Choose Continue into Guided Estimating, or Save for later.",
         "Guided Estimating walks each stage with its calculator or quotation.",
         _continue, handle=_continue_handle,
         manual=lambda ctx: ("Project page", url_for("projects.view_project", id=ctx.project.id))
         if ctx.project else None),
)


def _subject(ctx):
    if ctx.project is not None:
        return ctx.project.name
    return ctx.draft.get("name") or "New project (not created yet)"


WIZARD = Wizard(
    key=WIZARD_NEW_PROJECT, side="CONTRACTOR", title="Start a New Project",
    short="Customer, project type, location, drawings, your role and the construction stages — then estimating.",
    audience="Contractors and office staff",
    steps=STEPS, manual_label="New Project form",
    manual_url=lambda ctx=None: url_for("projects.create_project"),
    subject=_subject, finish_label="Finish",
)

_ = NOT_NEEDED
