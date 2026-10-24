"""Guided Workflow Wizards — the contractor office pages (Joel, 24 Oct 2026).

Office pages: the office sign-in and company wall apply, and the Field-only wall keeps crew out (these endpoints
are not on its allow-list). Every run is found in the signed-in person's company only; another company's run is
Not found. The wizard pages read the records and open the existing pages; see app/wizards/.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.wizard import SIDE_CONTRACTOR
from app.services.organizations import get_current_organization_id
from app.wizards import service as S
from app.wizards import views as V
from app.wizards.context import WizardContext
from app.wizards.registry import contractor_wizards, require, wizard_for

wizards_bp = Blueprint("wizards", __name__, url_prefix="/wizards")


def _ctx(run_id) -> WizardContext:
    org = get_current_organization_id()
    try:
        run = S.contractor_run(org, run_id)
    except S.WizardError:
        abort(404)
    wizard = wizard_for(run.wizard_key)
    if wizard is None or wizard.side != SIDE_CONTRACTOR:
        abort(404)
    return WizardContext(run, wizard, user=current_user._get_current_object(), organization_id=org)


def _home():
    return url_for("main.dashboard")


def contractor_summaries(organization_id, *, limit=6, project_id=None):
    """The company's unfinished wizards, newest first, each with its next required action."""
    out = []
    for run in S.active_contractor_runs(organization_id, project_id=project_id)[:limit]:
        wizard = wizard_for(run.wizard_key)
        if wizard is None:
            continue
        ctx = WizardContext(run, wizard, user=current_user._get_current_object(), organization_id=organization_id)
        try:
            out.append(V.run_summary(ctx))
        except Exception:  # noqa: BLE001 - one unreadable run must never break Home; it is still listed
            out.append({"run": run, "wizard": wizard, "subject": "", "progress": {"done": 0, "total": 0, "percent": 0},
                        "current": None, "next": None, "record_url": None, "next_url": None,
                        "resume_url": url_for("wizards.resume", run_id=run.id)})
    return out


@wizards_bp.app_context_processor
def _wizard_context():
    def wizard_return():
        try:
            return V.return_banner(SIDE_CONTRACTOR)
        except RuntimeError:
            return None

    def office_wizard_summaries(limit=6, project_id=None):
        try:
            return contractor_summaries(get_current_organization_id(), limit=limit, project_id=project_id)
        except Exception:  # noqa: BLE001 - outside an office request there is nothing to show
            return []

    def project_wizard_entry(project):
        """The wizard that fits the project now: Manage a Project once a proposal is accepted, else estimating."""
        try:
            org = get_current_organization_id()
            from app.models import Estimate, Proposal
            from app.models.wizard import WIZARD_GUIDED_ESTIMATING, WIZARD_MANAGE_PROJECT

            accepted = (Proposal.query.join(Estimate, Proposal.estimate_id == Estimate.id)
                        .filter(Estimate.project_id == project.id, Estimate.organization_id == org,
                                Proposal.status == "Accepted").first())
            key = WIZARD_MANAGE_PROJECT if accepted is not None else WIZARD_GUIDED_ESTIMATING
            resume = bool(S.active_contractor_runs(org, wizard_key=key, project_id=project.id))
            if key == WIZARD_MANAGE_PROJECT:
                return {"key": key, "title": "Manage a Project:", "resume": resume,
                        "text": "schedule, crews, purchasing, deliveries, costs, changes and closing, step by step."}
            return {"key": key, "title": "Guided Estimating:", "resume": resume,
                    "text": "every stage to the proposal and the customer's acceptance, step by step."}
        except Exception:  # noqa: BLE001 - the project page never fails because of the wizard bar
            return None

    return {"wizard_return": wizard_return, "office_wizards": contractor_wizards,
            "office_wizard_summaries": office_wizard_summaries, "project_wizard_entry": project_wizard_entry}


@wizards_bp.route("/")
def index():
    org = get_current_organization_id()
    return render_template("wizards/index.html", wizards=contractor_wizards(),
                           summaries=contractor_summaries(org, limit=30))


@wizards_bp.route("/<wizard_key>/start", methods=["GET", "POST"])
def start(wizard_key):
    wizard = require(wizard_key, SIDE_CONTRACTOR)
    if wizard is None:
        abort(404)
    org = get_current_organization_id()
    from app.services.auth import current_actor_display_name

    try:
        run = S.start_contractor_run(wizard.key, organization_id=org, actor=current_actor_display_name(),
                                     user_id=current_user.id,
                                     project_id=request.values.get("project_id", type=int))
    except S.WizardError as exc:
        flash(str(exc), "error")
        return redirect(url_for("wizards.index"))
    return redirect(url_for("wizards.resume", run_id=run.id))


@wizards_bp.route("/run/<int:run_id>")
def resume(run_id):
    ctx = _ctx(run_id)
    return redirect(ctx.step_url(V.resume_target(ctx)))


@wizards_bp.route("/run/<int:run_id>/step/<step_key>", methods=["GET", "POST"])
def step(run_id, step_key):
    ctx = _ctx(run_id)
    if request.method == "POST":
        return V.post_step(ctx, step_key, home_url=_home())
    return V.render_step(ctx, step_key, "wizards/run.html")


@wizards_bp.route("/run/<int:run_id>/step/<step_key>/autosave", methods=["POST"])
def autosave(run_id, step_key):
    ctx = _ctx(run_id)
    payload, status = V.autosave(ctx, step_key)
    return jsonify(payload), status


@wizards_bp.route("/run/<int:run_id>/open/<step_key>")
def open_page(run_id, step_key):
    return V.open_page(_ctx(run_id), step_key)


@wizards_bp.route("/run/<int:run_id>/manual/<step_key>")
def manual(run_id, step_key):
    return V.switch_to_manual(_ctx(run_id), step_key)


@wizards_bp.route("/run/<int:run_id>/end", methods=["POST"])
def end(run_id):
    return V.end_run(_ctx(run_id), home_url=_home())
