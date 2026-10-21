"""Training & Acceptance Centre pages (Joel, 21 Oct 2026). Only on the training site (TRAINING_ENVIRONMENT=1);
everywhere else every page answers 404.

/training                         register (role) or the trainee's home: progress, Continue, modules, tests
/training/lessons/<key>           one lesson, one step at a time (?step=N), screenshot beside the instructions
/training/uat                     the trainee's acceptance tests; /training/uat/<key> one test (Pass/Fail/Blocked)
/training/admin                   the administrator's dashboard (Instance Owner or System Administrator)
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.training import ROLE_LABELS, UAT_STATUSES
from app.training import content as C
from app.training import service as svc

training_bp = Blueprint("training", __name__, url_prefix="/training")


@training_bp.before_request
def _guard():
    if not svc.enabled():
        abort(404)
    if not current_user.is_authenticated and request.endpoint != "training.signin":
        return redirect(url_for("training.signin"))
    return None


def _trainee_or_register():
    trainee = svc.trainee_for(current_user)
    if trainee is None:
        return None, redirect(url_for("training.home"))
    return trainee, None


@training_bp.route("/signin")
def signin():
    if current_user.is_authenticated:
        return redirect(url_for("training.home"))
    return render_template("training/signin.html", next=request.args.get("next") or url_for("training.home"))


@training_bp.route("")
def home():
    trainee = svc.trainee_for(current_user)
    roles = svc.allowed_roles(current_user)
    if trainee is None:
        if not roles:
            abort(403)
        pathway = svc.principal(current_user)[0]
        return render_template("training/register.html", roles=roles, labels=ROLE_LABELS, pathway=pathway)
    return render_template("training/home.html", trainee=trainee, ov=svc.overview(trainee),
                           uat=svc.uat_overview(trainee), roles=roles, labels=ROLE_LABELS,
                           admin=svc.is_admin(current_user) is not None)


@training_bp.route("/register", methods=["POST"])
def register():
    try:
        svc.register(current_user, request.form.get("role", ""))
    except svc.TrainingError as exc:
        flash(str(exc), "error")
    return redirect(url_for("training.home"))


@training_bp.route("/lessons/<key>")
def lesson(key):
    trainee, back = _trainee_or_register()
    if back:
        return back
    try:
        module, item = svc.lesson_for_trainee(trainee, key)
    except svc.TrainingError:
        abort(404)
    step = max(0, min(request.args.get("step", default=0, type=int), len(item.steps) - 1))
    progress = svc.save_step(trainee, key, step)
    prev_key, next_key = svc.neighbours(trainee, key)
    ticked = set(svc.steps_ticked(trainee, key))
    return render_template("training/lesson.html", trainee=trainee, module=module, lesson=item, step=step,
                           current=item.steps[step], prev_key=prev_key, next_key=next_key, ticked=ticked,
                           progress=progress, notes=svc.feedback(trainee, key))


@training_bp.route("/lessons/<key>/check", methods=["POST"])
def check(key):
    """Tick or untick one step (the green check). Saved at once; works without JavaScript too."""
    trainee, back = _trainee_or_register()
    if back:
        return back
    index = request.form.get("step", default=-1, type=int)
    done = request.form.get("done") == "1"
    try:
        p = svc.check_step(trainee, key, index, done)
        _m, item = svc.lesson_for_trainee(trainee, key)
    except svc.TrainingError as exc:
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"error": str(exc)}), 400
        abort(404)
    ticked = sorted(set(p.steps_done or []))
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"step": index, "done": index in ticked, "ticked": len(ticked), "total": len(item.steps)})
    nxt = next((i for i in range(len(item.steps)) if i not in ticked), len(item.steps) - 1)
    return redirect(url_for("training.lesson", key=key, step=nxt) + f"#step-{nxt + 1}")


@training_bp.route("/lessons/<key>/move", methods=["POST"])
def move(key):
    trainee, back = _trainee_or_register()
    if back:
        return back
    try:
        _module, item = svc.lesson_for_trainee(trainee, key)
    except svc.TrainingError:
        abort(404)
    step = request.form.get("step", default=0, type=int)
    action = request.form.get("action", "next")
    target = step + 1 if action == "next" else step - 1 if action == "back" else step
    target = max(0, min(target, len(item.steps) - 1))
    svc.save_step(trainee, key, target if action != "exit" else step)
    if action == "exit":
        flash("Saved. Press Continue where I left off when you come back.", "success")
        return redirect(url_for("training.home"))
    return redirect(url_for("training.lesson", key=key, step=target))


@training_bp.route("/lessons/<key>/complete", methods=["POST"])
def complete(key):
    trainee, back = _trainee_or_register()
    if back:
        return back
    try:
        svc.complete_lesson(trainee, key, request.form.get("exercise_done") == "1")
    except svc.TrainingError as exc:
        flash(str(exc), "error")
        _m, item = svc.lesson_for_trainee(trainee, key)
        return redirect(url_for("training.lesson", key=key, step=len(item.steps) - 1))
    _prev, nxt = svc.neighbours(trainee, key)
    flash("Lesson complete.", "success")
    return redirect(url_for("training.lesson", key=nxt) if nxt else url_for("training.home"))


@training_bp.route("/lessons/<key>/feedback", methods=["POST"])
def add_feedback(key):
    trainee, back = _trainee_or_register()
    if back:
        return back
    step = request.form.get("step", default=0, type=int)
    try:
        svc.add_feedback(trainee, key, request.form.get("body", ""))
        flash("Your note is saved.", "success")
    except svc.TrainingError as exc:
        flash(str(exc), "error")
    return redirect(url_for("training.lesson", key=key, step=step))


@training_bp.route("/tutor", methods=["POST"])
def tutor_state():
    trainee, back = _trainee_or_register()
    if back:
        return back
    svc.set_tutor(trainee, request.form.get("minimized") == "1")
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"minimized": trainee.tutor_minimized})
    return redirect(request.form.get("back") or url_for("training.home"))


@training_bp.route("/tutor/ask", methods=["POST"])
def tutor_ask():
    trainee, back = _trainee_or_register()
    if back:
        return jsonify({"answer": "Register for training first."}), 400
    data = request.get_json(silent=True) or request.form
    item = None
    if data.get("lesson"):
        try:
            item = svc.lesson_for_trainee(trainee, data.get("lesson"))[1]
        except svc.TrainingError:
            item = None
    case = None
    if data.get("case"):
        try:
            case = svc.uat_case_for_trainee(trainee, data.get("case"))  # only the trainee's own tests
        except svc.TrainingError:
            case = None
    try:
        step = int(data.get("step") or 0)
    except (TypeError, ValueError):
        step = 0
    answer = svc.tutor_answer(item, step, str(data.get("question") or "")[:500], case=case)
    if request.headers.get("X-Requested-With") == "fetch" or request.is_json:
        return jsonify({"answer": answer})
    flash(answer, "tutor")
    if item:
        return redirect(url_for("training.lesson", key=data.get("lesson"), step=step))
    return redirect(url_for("training.uat_case", key=case.key) if case else url_for("training.home"))


@training_bp.route("/uat")
def uat():
    trainee, back = _trainee_or_register()
    if back:
        return back
    return render_template("training/uat.html", trainee=trainee, uat=svc.uat_overview(trainee))


@training_bp.route("/uat/<key>", methods=["GET", "POST"])
def uat_case(key):
    trainee, back = _trainee_or_register()
    if back:
        return back
    try:
        case = svc.uat_case_for_trainee(trainee, key)
    except svc.TrainingError:
        abort(404)
    if request.method == "POST":
        try:
            svc.record_uat(trainee, key, request.form.get("status", ""), request.form.get("notes", ""),
                           request.form.get("issue", ""))
        except svc.TrainingError as exc:
            flash(str(exc), "error")
            return redirect(url_for("training.uat_case", key=key))
        flash("Result saved.", "success")
        nxt = svc.uat_overview(trainee)["resume"]
        return redirect(url_for("training.uat_case", key=nxt) if nxt and nxt != key else url_for("training.uat"))
    svc.save_uat_position(trainee, key)
    attempts = svc.uat_history(trainee).get(key, [])
    module = next((m for m in C.modules() if m.key == case.module_key), None)
    return render_template("training/uat_case.html", trainee=trainee, case=case, attempts=attempts, module=module,
                           statuses=UAT_STATUSES, tutor_mode="uat")


@training_bp.route("/admin")
def admin():
    org = svc.is_admin(current_user)
    if org is None:
        abort(403)
    return render_template("training/admin.html", report=svc.admin_report(org), labels=ROLE_LABELS)
