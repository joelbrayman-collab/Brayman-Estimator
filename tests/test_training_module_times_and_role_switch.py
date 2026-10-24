"""Training module times and one office trainee on two pathways (Joel, 23 Oct 2026). Synthetic data only.

1. Every Contractor, Field Crew and Supplier module shows how long it takes to sit: "About 35 minutes", or Session 1
   / Session 2 between lessons when it would run past about 45 minutes (app/training/estimates.py). No lesson or
   acceptance-test key changes, so saved progress and results are untouched.
2. One office (not Field-only) training account takes the Contractor pathway as Office staff, changes role to
   Field (Change my role), and back. Each pathway's lesson progress and acceptance results stay separate and
   intact, and the administrator's dashboard shows both."""

from __future__ import annotations

import re

import pytest
from flask import g

from app import create_app, db
from app.models.training import TrainingLessonProgress, TrainingTrainee, TrainingUatResult
from app.training import content as C
from app.training import environment
from app.training import estimates as E

pytestmark = pytest.mark.no_office_auth
PW = {k: f"Synthetic-{k}-times-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")}
TRACKS = ((C.PATHWAY_CONTRACTOR, "OWNER"), (C.PATHWAY_CONTRACTOR, "OFFICE"), (C.PATHWAY_FIELD_CREW, "FIELD"),
          (C.PATHWAY_SUPPLIER, "SUPPLIER_OWNER"), (C.PATHWAY_SUPPLIER, "PRO_DESK"))


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                              "WTF_CSRF_ENABLED": False, "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        db.create_all()
        environment.build(application, PW)
        yield application
        db.session.remove()
        db.drop_all()


def _email(key):
    return next(e for k, _n, e, *_ in environment.OFFICE_PEOPLE if k == key)


def _client(app, key):
    g.pop("_login_user", None)
    client = app.test_client()
    assert client.post("/login", data={"email": _email(key), "password": PW[key]}).status_code == 302, key
    return client


def _get(client, path):
    g.pop("_login_user", None)
    return client.get(path)


def _post(client, path, **kw):
    g.pop("_login_user", None)
    return client.post(path, **kw)


# ------------------------------------------------------------------ 1. module times


def test_every_module_is_one_sitting_of_30_to_45_minutes_or_sessions_cut_between_lessons():
    for pathway, role in TRACKS:
        cases = C.uat_for(pathway, role)
        for module, est in E.for_track(pathway, role):
            # The sessions cover the module's lessons exactly, in order: no lesson moves or changes key.
            keys = [key for s in est.sessions for key in s.lesson_keys]
            assert keys == [lesson.key for lesson in module.lessons], module.key
            assert [s.number for s in est.sessions] == list(range(1, len(est.sessions) + 1))
            for s in est.sessions:
                assert s.minutes % 5 == 0 and s.minutes >= E.SITTING_MIN, (module.key, s)
                # Over 45 only when one lesson is longer than a sitting on its own (none today).
                assert s.minutes <= E.SITTING_MAX or len(s.lesson_keys) == 1, (module.key, s)
            tests = sum(1 for c in cases if c.module_key == module.key)
            raw = sum(E.lesson_minutes(lesson) for lesson in module.lessons) + E.MINUTES_PER_TEST * tests
            assert est.raw_minutes == raw
            assert est.split == (int(5 * round(raw / 5)) > E.SITTING_MAX), module.key
            if not est.split:
                assert est.label == f"About {est.sessions[0].minutes} minutes"


def test_the_rule_on_known_modules():
    times = {m.key: e for m, e in E.for_track(C.PATHWAY_CONTRACTOR, "OWNER")}
    # c06: 4 lessons, 11 steps, 2 tests -> 16 + 22 + 6 = 44 -> About 45 minutes, one sitting.
    assert times["c06"].raw_minutes == 44 and times["c06"].label == "About 45 minutes"
    # c04 (QuickBooks): 11 lessons, 34 steps, 8 tests -> 136 minutes -> four sessions.
    assert times["c04"].raw_minutes == 136 and len(times["c04"].sessions) == 4
    field = {m.key: e for m, e in E.for_track(C.PATHWAY_FIELD_CREW, "FIELD")}
    assert field["f02"].label == "About 35 minutes"
    assert [len(s.lesson_keys) for s in field["f01"].sessions] == [1, 3, 2]
    supplier = {m.key: e for m, e in E.for_track(C.PATHWAY_SUPPLIER, "SUPPLIER_OWNER")}
    assert supplier["s07"].raw_minutes == 26 and supplier["s07"].label == "About 30 minutes"  # never under 30


def test_the_training_home_and_the_administrator_show_the_times(app):
    olivia = _client(app, "olivia")
    assert _post(olivia, "/training/register", data={"role": "OFFICE"}).status_code == 302
    html = _get(olivia, "/training").get_data(as_text=True)
    office = dict(E.for_track(C.PATHWAY_CONTRACTOR, "OFFICE"))
    shown = re.findall(r'data-module="(c\d\d)".*?data-module-time="(\d+)"', html, re.S)
    assert [k for k, _ in shown] == [m.key for m in office]
    for module, est in office.items():
        assert (module.key, str(est.minutes)) in shown
    c04 = next(e for m, e in office.items() if m.key == "c04")
    assert c04.split and "Session 1: about" in html and 'data-session-start="2"' in html
    assert "About 45 minutes" in html  # c06
    ben = _client(app, "ben")
    admin = _get(ben, "/training/admin").get_data(as_text=True)
    assert "data-admin-module-times" in admin and "Module times" in admin
    for pathway, role in ((C.PATHWAY_CONTRACTOR, "OWNER"), (C.PATHWAY_FIELD_CREW, "FIELD"),
                          (C.PATHWAY_SUPPLIER, "SUPPLIER_OWNER")):
        for module, est in E.for_track(pathway, role):
            assert f'data-module-time-row="{module.key}"' in admin and est.label in admin


# ------------------------------------------------------------------ 2. one office trainee, two pathways


def _do_lesson(client, key):
    lesson = C.find_lesson(key)[1]
    for i in range(len(lesson.steps)):
        assert _post(client, f"/training/lessons/{key}/check", data={"step": i, "done": "1"}).status_code == 302
    assert _post(client, f"/training/lessons/{key}/complete", data={"exercise_done": "1"}).status_code == 302


def _snapshot(trainee_id, keys):
    progress = {p.lesson_key: (p.step_reached, sorted(p.steps_done or []), p.exercise_done, p.completed_at)
                for p in TrainingLessonProgress.query.filter_by(trainee_id=trainee_id).all() if p.lesson_key in keys}
    results = sorted((r.case_key, r.attempt, r.status, r.notes, r.issue)
                     for r in TrainingUatResult.query.filter_by(trainee_id=trainee_id).all() if r.case_key in keys)
    return progress, results


def test_an_office_trainee_takes_contractor_then_field_and_back_with_both_records_kept(app):
    office_lesson = C.lessons_for(C.PATHWAY_CONTRACTOR, "OFFICE")[0][1].key
    office_case = C.uat_for(C.PATHWAY_CONTRACTOR, "OFFICE")[0].key
    field_lesson = C.lessons_for(C.PATHWAY_FIELD_CREW, "FIELD")[0][1].key
    field_case = C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")[0].key
    contractor_keys = ({lesson.key for _m, lesson in C.lessons_for(C.PATHWAY_CONTRACTOR, "OWNER")}
                       | {c.key for c in C.uat_for(C.PATHWAY_CONTRACTOR, "OWNER")})
    field_keys = ({lesson.key for _m, lesson in C.lessons_for(C.PATHWAY_FIELD_CREW, "FIELD")}
                  | {c.key for c in C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")})
    assert not contractor_keys & field_keys  # separate records by construction

    olivia = _client(app, "olivia")
    assert _post(olivia, "/training/register", data={"role": "OFFICE"}).status_code == 302
    _do_lesson(olivia, office_lesson)
    assert _post(olivia, f"/training/uat/{office_case}", data={"status": "PASS", "notes": "office ok"}).status_code == 302
    trainee = next(t for t in TrainingTrainee.query.all() if t.display_name.startswith("Olivia"))
    contractor_before = _snapshot(trainee.id, contractor_keys)
    assert contractor_before[0][office_lesson][3] is not None and contractor_before[1][0][2] == "PASS"
    home = _get(olivia, "/training").get_data(as_text=True)
    assert "Change my role" in home and 'value="FIELD"' in home

    # Change my role -> Field: the Field Crew lessons, none done; the Contractor record is untouched.
    assert _post(olivia, "/training/register", data={"role": "FIELD"}).status_code == 302
    db.session.expire_all()
    assert trainee.track == C.PATHWAY_FIELD_CREW and trainee.role == "FIELD"
    home = _get(olivia, "/training").get_data(as_text=True)
    assert f'data-lesson="{field_lesson}"' in home and f'data-lesson="{office_lesson}"' not in home
    assert "0 of 31 lessons done" in home
    assert _get(olivia, f"/training/lessons/{office_lesson}").status_code == 404  # not in this pathway now
    _do_lesson(olivia, field_lesson)
    assert _post(olivia, f"/training/uat/{field_case}",
                 data={"status": "FAIL", "issue": "synthetic: the button was greyed out"}).status_code == 302
    assert _snapshot(trainee.id, contractor_keys) == contractor_before
    field_before = _snapshot(trainee.id, field_keys)
    assert field_before[0][field_lesson][3] is not None and field_before[1][0][2] == "FAIL"

    # And back to Office: the Contractor lesson is still done, the Field record is untouched.
    assert _post(olivia, "/training/register", data={"role": "OFFICE"}).status_code == 302
    db.session.expire_all()
    home = _get(olivia, "/training").get_data(as_text=True)
    assert re.search(rf'data-lesson-row="{office_lesson}" data-lesson-status="completed"[^>]*class="tc-lesson tc-done', home)
    total = len(C.lessons_for(C.PATHWAY_CONTRACTOR, "OFFICE"))
    assert f"1 of {total} lessons done" in home and "Acceptance tests: 1 passed, 0 failed" in home
    assert _snapshot(trainee.id, contractor_keys) == contractor_before
    assert _snapshot(trainee.id, field_keys) == field_before

    # The administrator sees both: Contractor (current) and Field Crew (kept), each with its own counts.
    ben = _client(app, "ben")
    admin = _get(ben, "/training/admin").get_data(as_text=True)
    rows = re.findall(r'<tr data-admin-trainee="Olivia[^"]*" data-admin-track="([A-Z_]+)"( data-admin-current)?>'
                      r'(.*?)</tr>', admin, re.S)
    by_track = {track: (bool(current), re.sub(r"<[^>]+>", " ", body)) for track, current, body in rows}
    assert set(by_track) == {C.PATHWAY_CONTRACTOR, C.PATHWAY_FIELD_CREW}
    assert by_track[C.PATHWAY_CONTRACTOR][0] and not by_track[C.PATHWAY_FIELD_CREW][0]
    assert f"1/{total}" in by_track[C.PATHWAY_CONTRACTOR][1] and "1 pass · 0 fail" in by_track[C.PATHWAY_CONTRACTOR][1]
    assert "1/31" in by_track[C.PATHWAY_FIELD_CREW][1] and "0 pass · 1 fail" in by_track[C.PATHWAY_FIELD_CREW][1]
    crew = re.search(r'data-admin-crew-member="Olivia[^"]*" data-admin-other-track>(.*?)</article>', admin, re.S)
    assert crew and "Lessons: 1 of 31 done" in crew.group(1) and "synthetic: the button was greyed out" in crew.group(1)
    assert "Field Crew training" in admin and "synthetic: the button was greyed out" in admin  # outstanding issue


def test_a_field_only_crew_member_still_cannot_take_the_contractor_pathway(app):
    kevin = _client(app, "kevin")
    assert _post(kevin, "/training/register", data={"role": "FIELD"}).status_code == 302
    assert _post(kevin, "/training/register", data={"role": "OFFICE"}).status_code == 302
    trainee = next(t for t in TrainingTrainee.query.all() if t.display_name.startswith("Kevin"))
    assert trainee.role == "FIELD"
    assert "Change my role" not in _get(kevin, "/training").get_data(as_text=True)
