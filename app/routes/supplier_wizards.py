"""Guided Workflow Wizards — the Supplier Hub pages (Supplier Pro Desk wizard, Joel 24 Oct 2026).

Registered on the Supplier Hub blueprint, so the Supplier Hub wall applies: supplier sign-in only, office users
refused. Every run is found under a supplier the signed-in person belongs to; anything else is Not found.
"""

from __future__ import annotations

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.wizard import SIDE_SUPPLIER, WIZARD_SUPPLIER_PRO_DESK
from app.routes.supplier_portal import _areas, _supplier, supplier_portal_bp
from app.wizards import service as S
from app.wizards import views as V
from app.wizards.context import WizardContext
from app.wizards.registry import supplier_wizards, wizard_for


def _actor():
    return (getattr(current_user, "display_name", None) or getattr(current_user, "email", None) or "").strip()


def _ctx(supplier_id, run_id) -> WizardContext:
    supplier = _supplier(supplier_id)
    try:
        run = S.supplier_run(supplier.id, run_id)
    except S.WizardError:
        abort(404)
    wizard = wizard_for(run.wizard_key)
    if wizard is None or wizard.side != SIDE_SUPPLIER:
        abort(404)
    return WizardContext(run, wizard, user=current_user._get_current_object(), supplier=supplier)


def supplier_summaries(supplier, *, limit=6):
    out = []
    for run in S.active_supplier_runs(supplier.id)[:limit]:
        wizard = wizard_for(run.wizard_key)
        ctx = WizardContext(run, wizard, user=current_user._get_current_object(), supplier=supplier)
        try:
            out.append(V.run_summary(ctx))
        except Exception:  # noqa: BLE001 - one unreadable run never breaks the dashboard
            continue
    return out


@supplier_portal_bp.app_context_processor
def _supplier_wizard_context():
    def supplier_wizard_return():
        try:
            return V.return_banner(SIDE_SUPPLIER)
        except RuntimeError:
            return None

    def supplier_wizard_summaries(supplier, limit=6):
        try:
            return supplier_summaries(supplier, limit=limit)
        except Exception:  # noqa: BLE001
            return []

    return {"supplier_wizard_return": supplier_wizard_return, "supplier_wizard_summaries": supplier_wizard_summaries,
            "supplier_wizard_list": supplier_wizards}


def _home(supplier):
    return url_for("supplier_portal.inbox", supplier_id=supplier.id)


@supplier_portal_bp.route("/<int:supplier_id>/wizards/")
def wizard_index(supplier_id):
    supplier = _supplier(supplier_id)
    return render_template("supplier/wizards_index.html", supplier=supplier, areas=_areas(),
                           wizards=supplier_wizards(), summaries=supplier_summaries(supplier, limit=30))


@supplier_portal_bp.route("/<int:supplier_id>/wizards/start", methods=["GET", "POST"])
def wizard_start(supplier_id):
    supplier = _supplier(supplier_id)
    share_id = request.values.get("share_id", type=int)
    quote_id = request.values.get("quote_id", type=int)
    try:
        if share_id:
            from app.services.supplier_hub import SupplierHubError, supplier_share

            try:
                supplier_share(supplier.id, share_id)
            except SupplierHubError:
                abort(404)
        if quote_id:
            from app.services.supplier_pro_desk import ProDeskError, supplier_quote

            try:
                supplier_quote(supplier.id, quote_id)
            except ProDeskError:
                abort(404)
        run = S.start_supplier_run(supplier_id=supplier.id, actor=_actor(), user_id=current_user.id,
                                   share_id=share_id, quote_id=quote_id)
    except S.WizardError as exc:
        flash(str(exc), "error")
        return redirect(url_for("supplier_portal.wizard_index", supplier_id=supplier.id))
    return redirect(url_for("supplier_portal.wizard_resume", supplier_id=supplier.id, run_id=run.id))


@supplier_portal_bp.route("/<int:supplier_id>/wizards/run/<int:run_id>")
def wizard_resume(supplier_id, run_id):
    ctx = _ctx(supplier_id, run_id)
    return redirect(ctx.step_url(V.resume_target(ctx)))


@supplier_portal_bp.route("/<int:supplier_id>/wizards/run/<int:run_id>/step/<step_key>", methods=["GET", "POST"])
def wizard_step(supplier_id, run_id, step_key):
    ctx = _ctx(supplier_id, run_id)
    if request.method == "POST":
        return V.post_step(ctx, step_key, home_url=_home(ctx.supplier))
    return V.render_step(ctx, step_key, "supplier/wizards_run.html", supplier=ctx.supplier, areas=_areas())


@supplier_portal_bp.route("/<int:supplier_id>/wizards/run/<int:run_id>/open/<step_key>")
def wizard_open(supplier_id, run_id, step_key):
    return V.open_page(_ctx(supplier_id, run_id), step_key)


@supplier_portal_bp.route("/<int:supplier_id>/wizards/run/<int:run_id>/manual/<step_key>")
def wizard_manual(supplier_id, run_id, step_key):
    return V.switch_to_manual(_ctx(supplier_id, run_id), step_key)


@supplier_portal_bp.route("/<int:supplier_id>/wizards/run/<int:run_id>/end", methods=["POST"])
def wizard_end(supplier_id, run_id):
    ctx = _ctx(supplier_id, run_id)
    return V.end_run(ctx, home_url=_home(ctx.supplier))


@supplier_portal_bp.route("/<int:supplier_id>/wizards/help", methods=["POST"])
def wizard_help(supplier_id):
    """Ask the Tutor on a supplier wizard step: the same bounded Help answer as the office (no change made)."""
    _supplier(supplier_id)
    from app.presentation.help_content import SURFACE_WIZARD, answer_help_question

    data = request.get_json(silent=True) or {}
    key = str(data.get("key") or "")
    if not key.startswith(WIZARD_SUPPLIER_PRO_DESK + "."):
        return jsonify({"answer": "Help isn't available for this screen.", "mutates": False})
    return jsonify(answer_help_question(SURFACE_WIZARD, key, str(data.get("question") or "")[:400]))
