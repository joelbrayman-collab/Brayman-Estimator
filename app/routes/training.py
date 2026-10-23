"""Training & Acceptance Centre pages (Joel, 21 Oct 2026). Only on the training site (TRAINING_ENVIRONMENT=1);
everywhere else every page answers 404.

/training                         register (role) or the trainee's home: progress, Continue, modules, tests
/training/lessons/<key>           one lesson, one step at a time (?step=N), screenshot beside the instructions
/training/uat                     the trainee's acceptance tests; /training/uat/<key> one test (Pass/Fail/Blocked)
/training/workflow                the Workflow map: each stage with its lessons and acceptance tests
/training/admin                   the administrator's dashboard (Instance Owner or System Administrator)
/training/review                  owner review of the Workflow Maps (administrators; no trainee registration):
/training/review/<map>            contractor, supplier or field map; lessons and tests open read-only
/training/review/field-crew       the Field Crew pathway's modules, lessons and tests, read-only (22 Oct 2026)

Three groups (22 Oct 2026): contractor owners and office staff, the Field crew (role Field worker: the Field Crew
pathway, app/training/field_crew.py) and supplier owners and PRO Desk staff. A Field-only person is offered
only the Field Crew training.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user

from app.models.training import ROLE_FIELD, ROLE_LABELS, UAT_STATUSES
from app.training import content as C
from app.training import service as svc
from app.training.links import links_for_lesson

training_bp = Blueprint("training", __name__, url_prefix="/training")


@training_bp.before_request
def _guard():
    if not svc.enabled():
        abort(404)
    session.pop("tc_return", None)  # back in the Training Centre: the 'Back to the lesson step' bar is done
    if not current_user.is_authenticated and request.endpoint != "training.signin":
        return redirect(url_for("training.signin"))
    return None


def _trainee_or_register():
    trainee = svc.trainee_for(current_user)
    if trainee is None:
        return None, redirect(url_for("training.home"))
    return trainee, None


@training_bp.context_processor
def _review_nav():
    """Training administrators see Owner review in the Training Centre menu (21 Oct 2026)."""
    if not current_user.is_authenticated:
        return {"training_admin": False}
    return {"training_admin": svc.is_admin(current_user._get_current_object()) is not None}


@training_bp.route("/signin")
def signin():
    if current_user.is_authenticated:
        return redirect(url_for("training.home"))
    from app.services.transactional_email import email_delivery_configured

    return render_template("training/signin.html", next=request.args.get("next") or url_for("training.home"),
                           email_ready=email_delivery_configured())


@training_bp.route("")
def home():
    trainee = svc.trainee_for(current_user)
    roles = svc.allowed_roles(current_user)
    if trainee is None:
        if not roles:
            abort(403)
        pathway = svc.principal(current_user)[0]
        return render_template("training/register.html", roles=roles, labels=ROLE_LABELS, pathway=pathway,
                               field_crew_only=roles == (ROLE_FIELD,))
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
                           progress=progress, notes=svc.feedback(trainee, key),
                           workflow_stages=_workflow_stages(trainee, key),
                           step_links=links_for_lesson(key, trainee))


def _workflow_stages(trainee, lesson_key):
    """The Workflow map stages this lesson belongs to, on the trainee's own map (link back to the map)."""
    from app.workflow_map import definition as WD
    from app.workflow_map.pages import training_viewer

    map_key, _viewer = training_viewer(trainee)
    on_map = {s.id for s in WD.map_stages(map_key)}
    return [s for s in WD.stages_for_lesson(lesson_key) if s.id in on_map]


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
    if action == "exit":
        # Resume where the trainee really is (22 Oct 2026): the first step not ticked once any step is ticked,
        # so Continue where I left off never sends them back to a step already done.
        ticked = set(svc.steps_ticked(trainee, key))
        if ticked:
            step = next((i for i in range(len(item.steps)) if i not in ticked), len(item.steps) - 1)
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


_BACK_LABELS = (("/training/lessons/", "the lesson"), ("/training/uat", "the acceptance test"),
                ("/training/review", "the owner review"), ("/training/workflow", "the Workflow map"))


def _map_back():
    """Where the Back button above a Workflow map goes (23 Oct 2026): the page the map was opened from, passed as
    ``?back=`` (same-site /training pages only), or the Training Centre home when the map is opened directly."""
    raw = (request.args.get("back") or "").strip()
    ok = (raw.startswith("/training") and not raw.startswith("//") and "\\" not in raw and "://" not in raw
          and "\n" not in raw and "\r" not in raw and len(raw) <= 300 and not raw.startswith("/training/workflow"))
    if not ok:
        return {"raw": "", "href": url_for("training.home"), "label": "← Back to the Training Centre"}
    label = next((txt for prefix, txt in _BACK_LABELS if raw.startswith(prefix)), "the Training Centre")
    return {"raw": raw, "href": raw, "label": "← Back to " + label}


@training_bp.route("/workflow")
def workflow_map():
    """The Workflow map in the Training Centre (Joel, 21 Oct 2026): the trainee's side of the governed workflow
    definition, each stage with its lessons and acceptance tests and the trainee's own progress."""
    trainee = svc.trainee_for(current_user)
    if trainee is None:
        # An administrator reviews the maps without registering (21 Oct 2026); others register first.
        if svc.is_admin(current_user) is not None:
            return redirect(url_for("training.review_map", map_key="contractor", stage=request.args.get("stage")))
        return redirect(url_for("training.home"))
    from app.workflow_map.build import build as build_map
    from app.workflow_map.pages import training_viewer

    map_key, viewer = training_viewer(trainee)
    back = _map_back()
    wf = build_map(map_key, viewer, current=request.args.get("stage"), stage_endpoint="training.workflow_map",
                   stage_args={"back": back["raw"]} if back["raw"] else {})
    return render_template("training/workflow.html", trainee=trainee, wf=wf, map_back=back)


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
        nxt = svc.next_uat_after(trainee, key)  # the next test with no result yet, or the list after the last
        return redirect(url_for("training.uat_case", key=nxt) if nxt else url_for("training.uat"))
    svc.save_uat_position(trainee, key)
    attempts = svc.uat_history(trainee).get(key, [])
    module = next((m for m in C.modules() if m.key == case.module_key), None)
    from app.workflow_map import definition as WD
    from app.workflow_map.pages import training_viewer

    on_map = {s.id for s in WD.map_stages(training_viewer(trainee)[0])}
    return render_template("training/uat_case.html", trainee=trainee, case=case, attempts=attempts, module=module,
                           statuses=UAT_STATUSES, tutor_mode="uat",
                           workflow_stages=[s for s in WD.stages_for_uat(key) if s.id in on_map])


@training_bp.route("/admin")
def admin():
    org = svc.is_admin(current_user)
    if org is None:
        abort(403)
    return render_template("training/admin.html", report=svc.admin_report(org), labels=ROLE_LABELS)


# ------------------------------------------------------------------ owner review (21 Oct 2026)
# The owner reviews the Workflow Maps, lessons and acceptance tests without registering as a trainee.
# Read-only: nothing here saves progress or results. Training administrators only.

REVIEW_MAPS = ("contractor", "supplier", "field")


def _review_guard():
    if svc.is_admin(current_user) is None:
        abort(403)


def _review_map_key(raw):
    from app.workflow_map import definition as WD

    key = (raw or "").strip().lower()
    return key if key in REVIEW_MAPS and key in WD.MAPS else None


@training_bp.route("/review")
def review():
    _review_guard()
    from app.workflow_map import definition as WD

    maps = [{"key": k, "title": WD.MAPS[k].title, "intro": WD.MAPS[k].intro,
             "href": url_for("training.review_map", map_key=k)} for k in REVIEW_MAPS]
    return render_template("training/review.html", maps=maps)


@training_bp.route("/review/field-crew")
def review_field_crew():
    """The owner previews the whole Field Crew pathway (Joel, 22 Oct 2026): its eight modules, lessons and
    acceptance tests, read-only. Nothing is saved; the owner is not registered as crew."""
    _review_guard()
    modules = C.modules_for(C.PATHWAY_FIELD_CREW, ROLE_FIELD)
    return render_template("training/review_pathway.html", map_key="field-crew", modules=modules,
                           lesson_count=sum(len(m.lessons) for m in modules),
                           cases=C.uat_for(C.PATHWAY_FIELD_CREW, ROLE_FIELD))


@training_bp.route("/review/<map_key>")
def review_map(map_key):
    _review_guard()
    key = _review_map_key(map_key)
    if key is None:
        abort(404)
    from app.workflow_map.build import KIND_FIELD, KIND_OFFICE, KIND_SUPPLIER, Viewer
    from app.workflow_map.build import build as build_map

    kind = {"contractor": KIND_OFFICE, "supplier": KIND_SUPPLIER, "field": KIND_FIELD}[key]
    org = svc.is_admin(current_user)
    from app.workflow_map.pages import _office_access

    people_admin, company_management = _office_access(org) if kind == KIND_OFFICE else (False, False)
    viewer = Viewer(kind=kind, people_admin=people_admin, company_management=company_management, training=True,
                    trainee=None, role=None, projects=None, review_map=key)
    back = _map_back()
    wf = build_map(key, viewer, current=request.args.get("stage"), stage_endpoint="training.review_map",
                   stage_args={"map_key": key, **({"back": back["raw"]} if back["raw"] else {})})
    return render_template("training/review_map.html", wf=wf, map_key=key, maps=REVIEW_MAPS, map_back=back)


def _review_back(key):
    map_key = _review_map_key(request.args.get("map")) or "contractor"
    stage = (request.args.get("stage") or "").strip()
    return url_for("training.review_map", map_key=map_key, stage=stage or None) + "#workflow-stage", map_key


@training_bp.route("/review/lessons/<key>")
def review_lesson(key):
    _review_guard()
    found = C.find_lesson(key)
    if found is None:
        abort(404)
    module, item = found
    back, map_key = _review_back(key)
    return render_template("training/review_lesson.html", module=module, lesson=item, back=back, map_key=map_key)


@training_bp.route("/review/uat/<key>")
def review_uat(key):
    _review_guard()
    case = C.find_uat(key)
    if case is None:
        abort(404)
    module = next((m for m in C.modules() if m.key == case.module_key), None)
    back, map_key = _review_back(key)
    return render_template("training/review_uat.html", case=case, module=module, back=back, map_key=map_key)
