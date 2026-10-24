"""Training & Acceptance Centre: registration, saved progress, acceptance tests, feedback, the
administrator's report and the Training Tutor (Joel, 21 Oct 2026).

Equivalent to the AiRIA Training Centre's register (which lives on its own ChatGPT site, so there is no AiRIA
code to copy): training progress and UAT results are separate records with separate resume points; a
retest is a new attempt and earlier results are kept. Here they are kept on the server, per signed-in
person, so progress follows the trainee between the office computer and the phone.

The Centre is switched on only on the separate training site (TRAINING_ENVIRONMENT=1). It reads and writes
only its own four tables; lessons send the trainee to the real training-site pages to practise.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask import current_app

from app import db
from app.models.training import (
    CONTRACTOR_ROLES,
    PATHWAY_CONTRACTOR,
    PATHWAY_FIELD_CREW,
    PATHWAY_SUPPLIER,
    ROLE_FIELD,
    ROLE_LABELS,
    SUPPLIER_ROLES,
    UAT_BLOCKED,
    UAT_FAIL,
    UAT_PASS,
    UAT_STATUSES,
    TrainingFeedback,
    TrainingLessonProgress,
    TrainingTrainee,
    TrainingUatResult,
)
from app.training import content as C


class TrainingError(ValueError):
    pass


def enabled(app=None) -> bool:
    app = app or current_app
    return bool(app.config.get("TRAINING_ENVIRONMENT")) or os.environ.get("TRAINING_ENVIRONMENT") == "1"


def release_label() -> str:
    sha = os.environ.get("RENDER_GIT_COMMIT") or current_app.config.get("RELEASE_COMMIT") or ""
    return sha[:12] or "development"


# ------------------------------------------------------------------ who the person is


def principal(user) -> Tuple[Optional[str], Optional[str], Optional[int], bool]:
    """(pathway, organization_id, supplier_id, field_only) for a signed-in person, or (None, ...) when
    they belong to neither side or to both (fail closed)."""
    from app.models.user import UserMembership
    from app.services.access_domains import user_is_field_only
    from app.services.supplier_hub import active_supplier_memberships, principal_class

    kind = principal_class(user)
    if kind == "SUPPLIER":
        memberships = active_supplier_memberships(user)
        return PATHWAY_SUPPLIER, None, memberships[0].supplier_id, False
    if kind == "CONTRACTOR":
        rows = UserMembership.query.filter_by(user_id=user.id, is_active=True).all()
        if len(rows) != 1:
            return None, None, None, False
        org = rows[0].organization_id
        return PATHWAY_CONTRACTOR, org, None, user_is_field_only(user, org)
    return None, None, None, False


def allowed_roles(user) -> Tuple[str, ...]:
    pathway, _org, _sup, field_only = principal(user)
    if pathway == PATHWAY_CONTRACTOR:
        if field_only:
            return (ROLE_FIELD,)
        # Training administrators also take the Supplier pathway from their own sign-in (Joel, 24 Oct 2026); its
        # Supplier Hub practice uses their synthetic supplier practice login (app/training/practice.py).
        if enabled() and is_admin(user) is not None:
            return CONTRACTOR_ROLES + SUPPLIER_ROLES
        return CONTRACTOR_ROLES
    if pathway == PATHWAY_SUPPLIER:
        return SUPPLIER_ROLES
    return ()


def trainee_for(user) -> Optional[TrainingTrainee]:
    return TrainingTrainee.query.filter_by(user_id=user.id).first()


def register(user, role: str) -> TrainingTrainee:
    pathway, org, supplier_id, _field = principal(user)
    if pathway is None:
        raise TrainingError("This sign-in is not part of a contractor company or a supplier on the training site.")
    if role not in allowed_roles(user):
        raise TrainingError("Choose one of the roles shown.")
    trainee = trainee_for(user)
    if trainee is None:
        trainee = TrainingTrainee(user_id=user.id, display_name=(user.display_name or user.email)[:160],
                                  pathway=pathway, role=role, organization_id=org, supplier_id=supplier_id,
                                  release=release_label())
        db.session.add(trainee)
    else:
        trainee.role = role  # changing role keeps all progress and results
    db.session.commit()
    return trainee


# ------------------------------------------------------------------ training progress


def _progress(trainee) -> Dict[str, TrainingLessonProgress]:
    return {p.lesson_key: p for p in TrainingLessonProgress.query.filter_by(trainee_id=trainee.id).all()}


def overview(trainee) -> dict:
    """The trainee's modules and lessons with their state, and where to resume."""
    return _overview(trainee, trainee.track, trainee.role)


def _overview(trainee, track: str, role: str) -> dict:
    from app.training import estimates as E

    progress = _progress(trainee)
    times = {m.key: e for m, e in E.for_track(track, role)}
    rows, done, total = [], 0, 0
    for module in C.modules_for(track, role):
        lessons = []
        for lesson in module.lessons:
            p = progress.get(lesson.key)
            ticked = len(set(p.steps_done or [])) if p else 0
            state = "done" if p and p.completed_at else ("started" if p and (ticked or p.step_reached) else "new")
            lessons.append({"lesson": lesson, "state": state, "step": p.step_reached if p else 0,
                            "ticked": min(ticked, len(lesson.steps)), "steps": len(lesson.steps)})
            total += 1
            done += state == "done"
        time = times.get(module.key)
        starts = time.session_starts() if time else {}
        for x in lessons:
            x["session_start"] = starts.get(x["lesson"].key)
        rows.append({"module": module, "lessons": lessons, "time": time,
                     "done": sum(1 for x in lessons if x["state"] == "done"), "total": len(lessons)})
    nxt = None
    if trainee.training_resume and track == trainee.track:
        key, _, step = trainee.training_resume.partition(":")
        if any(x["lesson"].key == key and x["state"] != "done" for r in rows for x in r["lessons"]):
            nxt = (key, int(step or 0))
    if nxt is None:
        first = next((x for r in rows for x in r["lessons"] if x["state"] != "done"), None)
        nxt = (first["lesson"].key, first["step"]) if first else None
    return {"modules": rows, "done": done, "total": total, "percent": int(round(100 * done / total)) if total else 0,
            "resume": nxt}


def lesson_for_trainee(trainee, key: str):
    allowed = {lesson.key: (m, lesson) for m, lesson in C.lessons_for(trainee.track, trainee.role)}
    if key not in allowed:
        raise TrainingError("That lesson is not in your training.")
    return allowed[key]


def neighbours(trainee, key: str) -> Tuple[Optional[str], Optional[str]]:
    keys = [lesson.key for _m, lesson in C.lessons_for(trainee.track, trainee.role)]
    i = keys.index(key)
    return (keys[i - 1] if i > 0 else None), (keys[i + 1] if i + 1 < len(keys) else None)


def save_step(trainee, key: str, step: int) -> TrainingLessonProgress:
    _module, lesson = lesson_for_trainee(trainee, key)
    step = max(0, min(int(step), len(lesson.steps) - 1))
    p = TrainingLessonProgress.query.filter_by(trainee_id=trainee.id, lesson_key=key).first()
    if p is None:
        p = TrainingLessonProgress(trainee_id=trainee.id, lesson_key=key, step_reached=step, steps_done=[],
                                   exercise_done=False, release=release_label())
        db.session.add(p)
    p.step_reached = max(p.step_reached, step)
    trainee.training_resume = f"{key}:{step}"
    db.session.commit()
    return p


def check_step(trainee, key: str, index: int, done: bool) -> TrainingLessonProgress:
    """Tick (or untick) one step as done. Saved at once; the trainee resumes at the first step not ticked."""
    _module, lesson = lesson_for_trainee(trainee, key)
    index = int(index)
    if not 0 <= index < len(lesson.steps):
        raise TrainingError("That step is not in this lesson.")
    p = save_step(trainee, key, index)
    ticked = set(p.steps_done or [])
    if done:
        ticked.add(index)
    else:
        ticked.discard(index)
    p.steps_done = sorted(ticked)
    nxt = next((i for i in range(len(lesson.steps)) if i not in ticked), len(lesson.steps) - 1)
    p.step_reached = max(p.step_reached, nxt)
    trainee.training_resume = f"{key}:{nxt}"
    db.session.commit()
    return p


def steps_ticked(trainee, key: str) -> List[int]:
    p = TrainingLessonProgress.query.filter_by(trainee_id=trainee.id, lesson_key=key).first()
    return sorted(set(p.steps_done or [])) if p else []


def complete_lesson(trainee, key: str, exercise_done: bool) -> TrainingLessonProgress:
    _module, lesson = lesson_for_trainee(trainee, key)
    missing = [i + 1 for i in range(len(lesson.steps)) if i not in set(steps_ticked(trainee, key))]
    if missing:
        raise TrainingError("Tick each step as you do it first. Not ticked yet: step " + ", ".join(map(str, missing)) + ".")
    if not exercise_done:
        raise TrainingError("Tick “I did the practice exercise” first: the lesson is complete when you have done it.")
    p = save_step(trainee, key, len(lesson.steps) - 1)
    p.exercise_done = True
    p.completed_at = p.completed_at or datetime.utcnow()
    p.release = release_label()
    _prev, nxt = neighbours(trainee, key)
    trainee.training_resume = f"{nxt}:0" if nxt else None
    db.session.commit()
    return p


def set_tutor(trainee, minimized: bool) -> None:
    trainee.tutor_minimized = bool(minimized)
    db.session.commit()


def add_feedback(trainee, key: str, body: str) -> TrainingFeedback:
    lesson_for_trainee(trainee, key)
    body = (body or "").strip()
    if not body:
        raise TrainingError("Write your note or feedback first.")
    row = TrainingFeedback(trainee_id=trainee.id, lesson_key=key, body=body[:4000])
    db.session.add(row)
    db.session.commit()
    return row


def feedback(trainee, key: Optional[str] = None) -> List[TrainingFeedback]:
    q = TrainingFeedback.query.filter_by(trainee_id=trainee.id)
    if key:
        q = q.filter_by(lesson_key=key)
    return q.order_by(TrainingFeedback.id.desc()).all()


# ------------------------------------------------------------------ acceptance tests (UAT)


def uat_history(trainee) -> Dict[str, List[TrainingUatResult]]:
    out: Dict[str, List[TrainingUatResult]] = {}
    for r in TrainingUatResult.query.filter_by(trainee_id=trainee.id).order_by(TrainingUatResult.attempt).all():
        out.setdefault(r.case_key, []).append(r)
    return out


def uat_overview(trainee, track: Optional[str] = None, role: Optional[str] = None) -> dict:
    track, role = track or trainee.track, role or trainee.role
    history = uat_history(trainee)
    rows = []
    for case in C.uat_for(track, role):
        attempts = history.get(case.key, [])
        latest = attempts[-1] if attempts else None
        rows.append({"case": case, "latest": latest, "attempts": attempts,
                     "retest": bool(latest and latest.status != UAT_PASS)})
    counts = {s: sum(1 for r in rows if r["latest"] and r["latest"].status == s) for s in UAT_STATUSES}
    counts["NOT_TESTED"] = sum(1 for r in rows if r["latest"] is None)
    # Continue testing opens only a test with no result yet (22 Oct 2026): the one the trainee had open, else
    # the next untested one after it in the list. A retest of a failed or blocked test is an explicit action
    # (its Retest link), never Continue.
    resume = _next_untested(rows, trainee.uat_resume if track == trainee.track else None, include_self=True)
    return {"rows": rows, "counts": counts, "total": len(rows), "resume": resume}


def _next_untested(rows, key: Optional[str], include_self: bool = False) -> Optional[str]:
    """The next test in list order with no result, starting after ``key`` (or at it, with include_self) and
    wrapping round to the top; None when every test has a result."""
    keys = [r["case"].key for r in rows]
    untested = {r["case"].key for r in rows if r["latest"] is None}
    start = keys.index(key) if key in keys else -1
    if start >= 0 and include_self and key in untested:
        return key
    order = keys[start + 1:] + keys[:start + 1] if start >= 0 else keys
    return next((k for k in order if k in untested), None)


def next_uat_after(trainee, key: str) -> Optional[str]:
    """Where the trainee goes after saving a result for ``key``: the next untested test, or None (the list)."""
    return _next_untested(uat_overview(trainee)["rows"], key)


def uat_case_for_trainee(trainee, key: str) -> C.UatCase:
    case = C.find_uat(key)
    if case is None or case.pathway != trainee.track or trainee.role not in case.roles:
        raise TrainingError("That acceptance test is not in your list.")
    return case


def record_uat(trainee, key: str, status: str, notes: str = "", issue: str = "") -> TrainingUatResult:
    uat_case_for_trainee(trainee, key)
    if status not in UAT_STATUSES:
        raise TrainingError("Choose Pass, Fail or Blocked.")
    notes, issue = (notes or "").strip(), (issue or "").strip()
    if status in (UAT_FAIL, UAT_BLOCKED) and not issue:
        raise TrainingError("Say what went wrong, so it can be fixed and retested.")
    last = TrainingUatResult.query.filter_by(trainee_id=trainee.id, case_key=key) \
        .order_by(TrainingUatResult.attempt.desc()).first()
    row = TrainingUatResult(trainee_id=trainee.id, case_key=key, attempt=(last.attempt + 1) if last else 1,
                            status=status, notes=notes[:4000] or None, issue=issue[:4000] or None,
                            release=release_label())
    db.session.add(row)
    trainee.uat_resume = key
    db.session.commit()
    return row


def save_uat_position(trainee, key: str) -> None:
    uat_case_for_trainee(trainee, key)
    trainee.uat_resume = key
    db.session.commit()


# ------------------------------------------------------------------ administrator


def is_admin(user) -> Optional[str]:
    """The organization a training administrator looks after: its Instance Owner or a System
    Administrator. None for everyone else."""
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    pathway, org, _sup, field_only = principal(user)
    if pathway != PATHWAY_CONTRACTOR or field_only:
        return None
    return org if (is_instance_owner(user, org) or is_system_administrator(user, org)) else None


def visible_trainees(org: str) -> List[TrainingTrainee]:
    """The organization's own trainees and those of the suppliers it works with."""
    from app.models.supplier_catalogue import ContractorSupplierAccount

    supplier_ids = [a.supplier_id for a in ContractorSupplierAccount.query.filter_by(organization_id=org).all()]
    q = TrainingTrainee.query.filter(db.or_(TrainingTrainee.organization_id == org,
                                            TrainingTrainee.supplier_id.in_(supplier_ids or [-1])))
    return q.order_by(TrainingTrainee.pathway, TrainingTrainee.display_name).all()


TRACK_LABELS = {PATHWAY_CONTRACTOR: "Contractor training", PATHWAY_SUPPLIER: "Supplier training",
                PATHWAY_FIELD_CREW: "Field Crew training"}


def tracks_taken(trainee) -> List[Tuple[str, str, bool]]:
    """[(track, role, current)]: the trainee's current training first, then (Joel, 23 Oct 2026) the other contractor
    training when an office trainee has changed role to Field, or back, and has lessons or acceptance results in it.

    Progress and results are kept per lesson key and test key, so each training's record is separate and intact.
    The role shown for a Contractor training the trainee is not on now: Contractor owner when any of their records
    is in the owner-only lessons or tests, otherwise Office staff."""
    out = [(trainee.track, trainee.role, True)]
    if trainee.pathway != PATHWAY_CONTRACTOR:
        return out
    keys = {p.lesson_key for p in TrainingLessonProgress.query.filter_by(trainee_id=trainee.id).all()}
    keys |= {r.case_key for r in TrainingUatResult.query.filter_by(trainee_id=trainee.id).all()}

    def _keys(track, role):
        return ({lesson.key for _m, lesson in C.lessons_for(track, role)} | {c.key for c in C.uat_for(track, role)})

    from app.models.training import ROLE_OFFICE, ROLE_OWNER, ROLE_PRO_DESK, ROLE_SUPPLIER_OWNER

    if trainee.track != PATHWAY_CONTRACTOR:
        owner, office = _keys(PATHWAY_CONTRACTOR, ROLE_OWNER), _keys(PATHWAY_CONTRACTOR, ROLE_OFFICE)
        if keys & owner:
            out.append((PATHWAY_CONTRACTOR, ROLE_OWNER if keys & (owner - office) else ROLE_OFFICE, False))
    if trainee.track != PATHWAY_FIELD_CREW and keys & _keys(PATHWAY_FIELD_CREW, ROLE_FIELD):
        out.append((PATHWAY_FIELD_CREW, ROLE_FIELD, False))
    # A training administrator's Supplier pathway (24 Oct 2026): kept on the same record, shown as its own training.
    if trainee.track != PATHWAY_SUPPLIER:
        supplier, desk = _keys(PATHWAY_SUPPLIER, ROLE_SUPPLIER_OWNER), _keys(PATHWAY_SUPPLIER, ROLE_PRO_DESK)
        if keys & supplier:
            out.append((PATHWAY_SUPPLIER, ROLE_SUPPLIER_OWNER if keys & (supplier - desk) else ROLE_PRO_DESK, False))
    return out


def admin_report(org: str) -> dict:
    rows = []
    for t in visible_trainees(org):
        for track, role, current in tracks_taken(t):
            ov, uat = _overview(t, track, role), uat_overview(t, track, role)
            failing = [r for r in uat["rows"] if r["latest"] and r["latest"].status in (UAT_FAIL, UAT_BLOCKED)]
            retested = [r for r in uat["rows"] if len(r["attempts"]) > 1]
            ready = ov["done"] == ov["total"] and uat["counts"][UAT_PASS] == uat["total"] and uat["total"] > 0
            lesson_keys = {x["lesson"].key for m in ov["modules"] for x in m["lessons"]}
            notes = sum(1 for f in feedback(t) if f.lesson_key in lesson_keys)
            rows.append({"trainee": t, "role": ROLE_LABELS.get(role, role), "track": track, "current": current,
                         "track_label": TRACK_LABELS.get(track, track), "overview": ov, "uat": uat,
                         "failing": failing, "retested": retested, "feedback": notes,
                         "readiness": "Ready" if ready else ("Issues to fix" if failing else "In training")})
    issues = [(r["trainee"], x, r["track_label"]) for r in rows for x in r["failing"]]
    # The crew (Field Crew training) are shown in their own section of the dashboard, with each acceptance
    # test's latest result so a failing or blocked Field test stands out (Joel, 22 Oct 2026).
    crew = [r for r in rows if r["track"] == PATHWAY_FIELD_CREW]
    crew_cases = C.uat_for(PATHWAY_FIELD_CREW, ROLE_FIELD)
    from app.models.training import ROLE_OWNER, ROLE_SUPPLIER_OWNER
    from app.training import estimates as E

    times = [(TRACK_LABELS[PATHWAY_CONTRACTOR] + " (owner)", E.for_track(PATHWAY_CONTRACTOR, ROLE_OWNER)),
             (TRACK_LABELS[PATHWAY_FIELD_CREW], E.for_track(PATHWAY_FIELD_CREW, ROLE_FIELD)),
             (TRACK_LABELS[PATHWAY_SUPPLIER] + " (owner)", E.for_track(PATHWAY_SUPPLIER, ROLE_SUPPLIER_OWNER))]
    return {"rows": rows, "issues": issues, "crew": crew, "crew_cases": crew_cases, "times": times,
            "others": [r for r in rows if r["track"] != PATHWAY_FIELD_CREW]}


# ------------------------------------------------------------------ Training Tutor


_WORDS = re.compile(r"[a-z0-9']+")
_STOP = {"the", "a", "an", "i", "to", "do", "how", "what", "where", "is", "it", "my", "on", "in", "of", "and", "can",
         "you", "me", "this", "that", "for", "with", "be", "does", "did", "find", "go", "get", "at", "or"}

GENERAL_HELP = (
    ("save", "Every step you tick (the green check) is saved at once, and so is Save and exit. Come back to Training any time "
             "(computer or phone) and press Continue where I left off."),
    ("resume continue later exit", "Press Save and exit. Next time, open Training and press Continue where I left off."),
    ("phone iphone mobile", "The training pages work on the iPhone too. Field lessons are written for the phone."),
    ("screenshot picture image bigger enlarge", "Press a picture to see it full size. Press it again, or Close, to "
                                               "go back to the lesson."),
    ("mistake wrong undo broke", "Nothing you do on the training site touches real customers or real money. Read "
                                 "“If something goes wrong” under the step, or ask Joel."),
    ("test uat acceptance pass fail blocked", "Acceptance tests are separate from lessons. Open Acceptance tests, do "
                                             "what the test says, then choose Pass, Fail or Blocked. A Fail or Blocked "
                                             "needs a short description of what went wrong."),
    ("password sign login", "Sign in with the email and password from your training invitation. If you forgot it, "
                            "use Forgot password on the sign-in page."),
)


GENERAL_HELP = GENERAL_HELP + (
    ("next comes after then", "Do the step, press I did this step (it turns green), and the lesson moves you to the next "
                              "step. After the last step, do the practice exercise and press Finish this lesson."),
    ("fail blocked retest again", "Fail: it did something different from the expected result; say what you saw. "
                                  "Blocked: you could not get as far as the test; say what stopped you. After a fix, press "
                                  "Retest beside it in Acceptance tests and record the new result; your earlier results "
                                  "stay."),
    ("role job lessons missing", "Your lessons follow the job you chose. Change it at the bottom of your training home "
                                 "(your progress is kept). Field crew get the Field Crew training: Field lessons only."),
    ("field open app today", "On your training home press Open Field: CalibraytAI Field opens at Today. On Field, the "
                             "Training site bar at the top has Back to my training."),
    ("text texts sms message messages notification notifications stop", "Schedule texts: the first time you open Field it "
     "asks Get a text when your schedule changes? Tap Yes, text me or Not now. Later: on Field tap Texts (top of "
     "the page), type your mobile number, tick the box and tap Turn on schedule texts. When the office moves your "
     "work, puts you on a job or takes you off one, you get one text with the old and new dates and a link to Field. "
     "Stop them with Stop schedule texts or by replying STOP. The office sees each text on Calendar → Text notices "
     "(sent, delivered or failed, with Retry). The training site never sends a real text."),
)

# Guided Estimating (23 Oct 2026): the workflow, the stage rules and the calculators' three choices.
GENERAL_HELP = GENERAL_HELP + (
    ("guided estimate start new estimating workflow stages stage", "Guided Estimating: Home → Start New Estimate. "
     "Choose the project (or a new one), what is being built and your role. On Construction scope choose Internal, "
     "Subcontracted or N/A for every stage and press Finalize scope & build the workflow. Then open any stage, in any "
     "order: each one brings its calculator or its quote tools. Back, Save, Save & Exit and Complete & Next are at the "
     "bottom of every stage; Resume estimating is on the project page."),
    ("internal subcontracted n/a na scope responsibility mixed parts split", "Internal: your own crew. Subcontracted: an "
     "outside contractor. N/A: deliberately not part of this job (it shows as excluded). Nothing is chosen for you; "
     "a draft may have undecided stages, but Finalize needs every one. For mixed work open Parts of this stage and "
     "tick Decide this stage part by part (for example your materials, the subcontractor's installation)."),
    ("complete completed cost missing allowance zero refused incomplete", "A stage is Complete only with confirmed "
     "costs, an approved allowance (Allowance or no-cost decision → Approve the allowance, with the reason) or a "
     "no-cost decision, which only the owner or a System Administrator can authorize. Pressing Complete & Next "
     "alone never completes it: the page lists what is missing, and the proposal waits until every stage is "
     "resolved."),
    ("quote quotes subcontractor waiting suggested select compare", "Subcontracted stage: set up the subcontract, send "
     "the Printable quote request sheet and press I have sent the quote request (the stage shows Waiting for Quote; "
     "carry on with other stages). Record each quote, press Select this quote, then Use this cost on the line. A "
     "selected quote only suggests the cost; Undo puts the line back."),
    ("calculator result project existing new only choices carry cancel duplicate", "After any calculator result: Use "
     "Result Only (nothing saved), Add to Existing Project (choose the project and stage; it is kept with everything "
     "you entered and pressing it twice never doubles it) or Create New Project (the result waits on the new project; "
     "Cancel returns to the calculator with the same result). A calculation reaches the estimate only when you send "
     "it to the estimate review and confirm each quantity."),
    ("internal cost document pdf customer distribution", "Estimating workflow → Internal cost estimate: every stage's "
     "materials, labour, subcontracts and allowances with their sources, marked INTERNAL — NOT FOR CUSTOMER "
     "DISTRIBUTION. Download PDF or Print. The customer gets the proposal, never this."),
)

# Supplier training for administrators (Joel, 24 Oct 2026): the pathway switch and the supplier practice login.
GENERAL_HELP = GENERAL_HELP + (
    ("supplier practice administrator pathway store hub bmr password", "Training administrators take the Supplier "
     "pathway from their own sign-in: Pathway (top of the page) → Supplier owner, Supplier administrator or PRO Desk. "
     "Your lessons and test results stay on your own training record, apart from your Contractor and Field ones. For "
     "the Supplier Hub steps press Open the supplier practice site as <your name> (supplier practice): it opens BMR "
     "Winchester (training) as your practice login, with training records only and no supplier password. Press Back "
     "to the Training Centre as <your name> at the top of the page to come back signed in as yourself."),
)

_WHERE = {"where", "find", "menu", "button", "press", "click", "open", "locate"}
_SEE = {"see", "expect", "result", "happen", "look", "appear"}
_WRONG = {"wrong", "error", "problem", "stuck", "doesn't", "didn't", "work", "broken", "refused", "can't", "cannot"}
_TYPE = {"type", "enter", "fill", "write", "put"}
_WHY = {"why", "matter", "reason", "point"}
_NEXT = {"next", "after", "then"}


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def tutor_answer(lesson: Optional[C.Lesson], step_index: int, question: str, *, case: Optional[C.UatCase] = None) -> str:
    """Answer from the trainee's current lesson and step (or acceptance test) first, then the training guide.
    Only the trainee's own lessons are ever passed in (the route checks), nothing from anyone's records is read,
    and no outside service is called."""
    q = set(_WORDS.findall((question or "").lower()))
    words = {w for w in q if w not in _STOP}
    if not q:
        return "Ask in your own words, for example “where is the button?” or “what should I see?”."
    candidates: List[Tuple[int, str]] = []
    if lesson is not None:
        i = max(0, min(step_index, len(lesson.steps) - 1))
        step = lesson.steps[i]
        if q & _WHERE:
            candidates.append((100, f"Open {step.app}. Go to {step.where}. Then {_lower_first(step.do)}."))
        if q & _SEE:
            candidates.append((100, f"You should see: {step.expect}"))
        if q & _WRONG:
            candidates.append((110, f"If it did not work: {step.if_wrong} Check you are on {step.where} in "
                                    f"{step.app}. Nothing on the training site affects real customers, so you can try "
                                    "again. If it still does not work, write a note under My notes and feedback."))
        if q & _TYPE:
            candidates.append((95, f"Enter: {step.enter}" if step.enter else "Nothing needs typing in this step: "
                                                                                 f"{_lower_first(step.do)}."))
        if q & _WHY:
            candidates.append((95, step.why or lesson.why))
        if q & _NEXT:
            nxt = (f"Next is step {i + 2}: {lesson.steps[i + 1].title}. Press I did this step first."
                   if i + 1 < len(lesson.steps) else
                   "This is the last step. Then do the practice exercise below and press Finish this lesson.")
            candidates.append((90, nxt))
        for n, s in enumerate(lesson.steps):
            text = " ".join((s.title, s.where, s.do, s.enter, s.expect))
            score = len(words & set(_WORDS.findall(text.lower())))
            if score:
                candidates.append((10 * score, f"Step {n + 1}, “{s.title}”: go to {s.where}. {s.do}. You should see: "
                                               f"{s.expect}"))
    if q & {"fail", "blocked", "retest", "again"}:
        candidates.append((120, "Fail: it did something different from the expected result; say what you saw. Blocked: "
                                "you could not get as far as the test (for example a page would not open); say what "
                                "stopped you. After a fix, open the same test and record the new result; your earlier "
                                "results stay."))
    if case is not None:
        if q & (_WHERE | {"start"}):
            candidates.append((100, f"Start here: {case.start}"))
        if q & (_SEE | {"pass", "expected"}):
            candidates.append((100, f"It is a Pass when: {case.expected}"))
        if q & {"do", "action", "how"} and not q & {"retest", "fail", "blocked"}:
            candidates.append((80, f"Do this: {case.action}"))
    for keys, answer in GENERAL_HELP:
        score = len(words & set(keys.split()))
        if score:
            candidates.append((20 * score, answer))
    if not candidates:
        return ("I can help with this lesson: ask where something is, what to type, what you should see, what comes "
                "next, or what to do if it went wrong. For anything else, ask Joel.")
    return max(candidates, key=lambda c: c[0])[1]
