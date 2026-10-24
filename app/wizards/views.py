"""The wizard pages, shared by the contractor office (app/routes/wizards.py) and the Supplier Hub
(app/routes/supplier_wizards.py). The two route modules only find the run in their own scope (company or
supplier) and build the context; everything here is the same for both sides."""

from __future__ import annotations

from flask import flash, redirect, render_template, request, session, url_for

from app.wizards import framework as F
from app.wizards import service as S

RETURN_KEY = "wizard_return"


def _safe_local(path: str):
    text = (path or "").strip()
    if not text.startswith("/") or text.startswith("//") or "\\" in text or "://" in text:
        return None
    return text


# ------------------------------------------------------------------------------------------------ "Return to the wizard"
def remember_return(ctx, step):
    session[RETURN_KEY] = {"side": ctx.run.side, "run": ctx.run.id, "url": ctx.step_url(step.key),
                           "label": f"{ctx.wizard.title}: {step.title}"}


def clear_return(run_id=None):
    data = session.get(RETURN_KEY)
    if data and (run_id is None or data.get("run") == run_id):
        session.pop(RETURN_KEY, None)


def return_banner(side: str):
    """The way back to the wizard on the page the wizard opened (only on that side's pages)."""
    data = session.get(RETURN_KEY)
    if not data or data.get("side") != side:
        return None
    endpoint = request.endpoint or ""
    if endpoint.startswith("wizards.") or ".wizard_" in endpoint:
        return None
    return data


# ------------------------------------------------------------------------------------------------ one step
def _rows(ctx):
    return F.evaluate_all(ctx.wizard, ctx)


def resume_target(ctx):
    rows = _rows(ctx)
    keys = [r["step"].key for r in rows]
    if ctx.run.current_step in keys:
        return ctx.run.current_step
    first = F.first_open_step(rows)
    return first.key if first is not None else (keys[0] if keys else None)


def render_step(ctx, step_key, template, **extra):
    rows = _rows(ctx)
    row = next((r for r in rows if r["step"].key == step_key), None)
    if row is None:
        target = resume_target(ctx)
        return redirect(ctx.step_url(target)) if target and target != step_key else ("Not found", 404)
    step, view = row["step"], row["view"]
    if ctx.run.is_active:
        remember_return(ctx, step)  # any page opened from here shows "Return to the wizard" until Save & Exit
    else:
        clear_return(ctx.run.id)
    if ctx.run.is_active and ctx.run.current_step != step.key:
        S.set_step(ctx.run, step.key, actor=ctx.actor or "Signed-in user", user_id=ctx.user_id)
    previous = F.neighbour(rows, step.key, -1)
    following = F.neighbour(rows, step.key, +1)
    first_open = F.first_open_step(rows)
    manual = step.manual(ctx) if step.manual is not None else None
    from app.presentation.help_content import wizard_topic

    return render_template(
        template, ctx=ctx, wizard=ctx.wizard, run=ctx.run, rows=rows, row=row, step=step, view=view,
        previous=previous, following=following, progress=F.progress(rows), first_open=first_open,
        manual=manual, subject=ctx.wizard.subject(ctx), help_topic=wizard_topic(ctx.wizard.key, step.key),
        blockers=F.can_leave(step, view), history=S.history(ctx.run, 12), state_labels=F.STATE_LABELS, **extra)


def _form_values():
    return request.form


def post_step(ctx, step_key, *, home_url):
    rows = _rows(ctx)
    row = next((r for r in rows if r["step"].key == step_key), None)
    if row is None:
        return redirect(ctx.step_url(resume_target(ctx)))
    step = row["step"]
    action = request.form.get("wizard_action", "save")
    actor = ctx.actor
    try:
        if not ctx.run.is_active and action not in ("back", "next", "goto"):
            raise S.WizardError("This guided wizard is finished. Its records are kept; start it again from Home.")
        # A step's own form: the draft answers (saved by Save, Next and Save & Exit) or a small form that calls
        # an existing service (its own Submit button).
        if action == "submit" or (step.draft and step.handle and action in ("save", "next", "save_exit")
                                  and row["view"].form):
            if step.handle is None:
                raise S.WizardError("Nothing to save on this step.")
            result = step.handle(ctx, _form_values())
            message, target = (result if isinstance(result, tuple) else (result, None))
            if action == "submit":
                if message:
                    flash(message, "success")
                return redirect(target or ctx.step_url(step.key))
        if action == "back":
            previous = F.neighbour(rows, step.key, -1)
            return redirect(ctx.step_url(previous.key if previous else step.key))
        if action == "goto":
            target = request.form.get("goto_step", "")
            if any(r["step"].key == target for r in rows):
                return redirect(ctx.step_url(target))
            return redirect(ctx.step_url(step.key))
        if action == "save":
            S.set_step(ctx.run, step.key, actor=actor, user_id=ctx.user_id, event="SAVED")
            flash("Saved.", "success")
            return redirect(ctx.step_url(step.key))
        if action == "save_exit":
            S.set_step(ctx.run, step.key, actor=actor, user_id=ctx.user_id, event="SAVED_AND_EXITED")
            clear_return(ctx.run.id)
            flash(f"Saved. Resume {ctx.wizard.title} at “{step.title}” from Home any time.", "success")
            return redirect(home_url)
        if action == "next":
            fresh = F.safe_evaluate(step, type(ctx)(ctx.run, ctx.wizard, user=ctx.user,
                                                     organization_id=ctx.organization_id, supplier=ctx.supplier))
            blockers = F.can_leave(step, fresh)
            if blockers:
                flash("Before you go on: " + " · ".join(blockers), "error")
                return redirect(ctx.step_url(step.key))
            following = F.neighbour(rows, step.key, +1)
            if following is None:
                return redirect(ctx.step_url(step.key))
            S.set_step(ctx.run, following.key, actor=actor, user_id=ctx.user_id)
            return redirect(ctx.step_url(following.key))
        if action == "finish":
            fresh_ctx = type(ctx)(ctx.run, ctx.wizard, user=ctx.user, organization_id=ctx.organization_id,
                                  supplier=ctx.supplier)
            fresh_rows = F.evaluate_all(ctx.wizard, fresh_ctx)
            open_step = F.first_open_step(fresh_rows)
            if open_step is not None:
                waiting = [r for r in fresh_rows if r["step"].required and r["view"].state == F.WAITING]
                flash(f"Not finished yet: “{open_step.title}” still needs doing.", "error")
                return redirect(ctx.step_url(open_step.key))
            if any(r["step"].required and r["view"].state == F.WAITING for r in fresh_rows):
                flash("Some steps are still waiting for someone else. Save & Exit and come back when they answer.",
                      "error")
                return redirect(ctx.step_url(step.key))
            S.finish(ctx.run, actor=actor, user_id=ctx.user_id)
            clear_return(ctx.run.id)
            flash(f"{ctx.wizard.title} finished. Every record stays on its own page.", "success")
            target = ctx.wizard.after_finish(ctx) if ctx.wizard.after_finish else None
            return redirect(target or home_url)
    except S.WizardError as exc:
        from app import db

        db.session.rollback()
        flash(str(exc), "error")
        return redirect(ctx.step_url(step.key))
    return redirect(ctx.step_url(step.key))


def autosave(ctx, step_key):
    """Automatic draft saving (Start a New Project, steps 1–3): the answers typed so far, nothing else."""
    step = ctx.wizard.step(step_key)
    if step is None or not step.draft or step.handle is None:
        return {"saved": False, "reason": "This step has nothing to save automatically."}, 400
    try:
        step.handle(ctx, _form_values())
    except S.WizardError as exc:
        from app import db

        db.session.rollback()
        return {"saved": False, "reason": str(exc)}, 400
    return {"saved": True}, 200


def open_page(ctx, step_key):
    """Leave the wizard for an existing page, with a "Return to the wizard" bar shown there."""
    step = ctx.wizard.step(step_key)
    target = _safe_local(request.args.get("to", ""))
    if step is None or target is None:
        return redirect(ctx.step_url(resume_target(ctx)))
    remember_return(ctx, step)
    return redirect(target)


def switch_to_manual(ctx, step_key):
    """Continue Manually: the step's existing page. The wizard keeps its place and can be resumed."""
    step = ctx.wizard.step(step_key)
    manual = step.manual(ctx) if step is not None and step.manual is not None else None
    if manual is None:
        url = ctx.wizard.manual_url(ctx)
    else:
        url = manual[1]
    if ctx.run.is_active:
        S.set_step(ctx.run, step_key, actor=ctx.actor, user_id=ctx.user_id, event="SWITCHED_TO_MANUAL",
                   detail=manual[0] if manual else ctx.wizard.manual_label)
    remember_return(ctx, step or ctx.wizard.steps[0])
    return redirect(url)


def end_run(ctx, *, home_url):
    try:
        S.end(ctx.run, actor=ctx.actor, user_id=ctx.user_id, reason=request.form.get("reason", ""))
    except S.WizardError as exc:
        flash(str(exc), "error")
        return redirect(ctx.step_url(resume_target(ctx)))
    clear_return(ctx.run.id)
    flash(f"{ctx.wizard.title} closed. Nothing on the project or quotation was changed.", "success")
    return redirect(home_url)


# ------------------------------------------------------------------------------------------------ lists
def run_summary(ctx) -> dict:
    """For Home and the supplier dashboard: what the run is about, where it is and the next required action."""
    rows = _rows(ctx)
    first_open = F.first_open_step(rows)
    current = next((r for r in rows if r["step"].key == ctx.run.current_step), None)
    next_row = next((r for r in rows if first_open is not None and r["step"].key == first_open.key), None)
    record_url = None
    if getattr(ctx, "project", None) is not None:
        record_url = url_for("projects.view_project", id=ctx.project.id)
    elif ctx.is_supplier and ctx.share is not None:
        record_url = url_for("supplier_portal.request_detail", supplier_id=ctx.supplier.id, share_id=ctx.share.id)
    elif ctx.is_supplier and ctx.quote is not None:
        from app.wizards.supplier_pro_desk import current_quote

        record_url = url_for("supplier_pro_desk.quote", supplier_id=ctx.supplier.id, quote_id=current_quote(ctx).id)
    return {"run": ctx.run, "wizard": ctx.wizard, "subject": ctx.wizard.subject(ctx),
            "progress": F.progress(rows), "current": current, "next": next_row,
            "resume_url": ctx.step_url(ctx.run.current_step or (rows[0]["step"].key if rows else "")),
            "next_url": ctx.step_url(first_open.key) if first_open is not None else None,
            "record_url": record_url}
