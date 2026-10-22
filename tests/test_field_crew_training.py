"""Field Crew training (Joel, 22 Oct 2026): the third pathway of the Training & Acceptance Centre, for the crew
on the iPhone. Registration straight into it for a Field-only worker, only Field Crew lessons and tests, saved
progress and resume, Field acceptance tests (Pass / Fail / Blocked, notes, retest) kept apart from the lessons,
Ben's administrator view of his crew, the owner's read-only preview, the Workflow Map's Field section, the
Tutor, and never a price, cost, margin, supplier pricing or office page. Synthetic data only."""

from __future__ import annotations

import re
import struct
from pathlib import Path

import pytest
from flask import g

from app import create_app, db
from app.models.training import TrainingLessonProgress, TrainingTrainee, TrainingUatResult
from app.training import content as C
from app.training import environment

pytestmark = pytest.mark.no_office_auth
PW = {k: f"Synthetic-{k}-crew-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")}
MODULE_TITLES = (
    "First sign-in and iPhone setup",
    "Today's assigned work",
    "Weekly schedule and schedule changes",
    "Drawings and job information",
    "Recording field work",
    "Photos, notes and progress updates",
    "Offline use, refresh and troubleshooting",
    "Complete working-day exercise and Field UAT",
)
# Never on a Field Crew page or lesson: money, the contractor's or the supplier's commercial words.
MONEY = re.compile(r"\$\s?\d|\bprice|\bpricing|\bcost|margin|markup|estimate|invoice|\bquote|accounting", re.I)
# The only places a Field Crew page may link to.
ALLOWED = ("/training", "/field", "/account/password", "/static/", "#", "/logout", "/forgot-password", "/login",
           "/help/")


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
    return next(e for k, _n, e, *_ in environment.OFFICE_PEOPLE + environment.SUPPLIER_PEOPLE if k == key)


def _client(app, key):
    g.pop("_login_user", None)
    client = app.test_client()
    if key in ("darcy", "pat"):
        r = client.post("/supplier/login", data={"email": _email(key), "password": PW[key], "next": "/training"})
    else:
        r = client.post("/login", data={"email": _email(key), "password": PW[key]})
    assert r.status_code == 302, key
    return client


def _get(client, path, **kw):
    g.pop("_login_user", None)
    return client.get(path, **kw)


def _post(client, path, **kw):
    g.pop("_login_user", None)
    return client.post(path, **kw)


def _kevin(app):
    kevin = _client(app, "kevin")
    assert _post(kevin, "/training/register", data={"role": "FIELD"}).status_code == 302
    return kevin


def _main(html):
    """The page between <main> and </main> (the lesson, test or map), without the shared site chrome."""
    m = re.search(r"<main[^>]*>(.*)</main>", html, re.S)
    return m.group(1) if m else html


def _text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)))


def _hrefs(html):
    return re.findall(r'href="([^"]*)"', html)


def _field_lessons():
    return C.lessons_for(C.PATHWAY_FIELD_CREW, "FIELD")


# ------------------------------------------------------------------ the content


def test_eight_practical_modules_every_step_complete_for_a_worker_on_a_phone(app):
    modules = C.modules_for(C.PATHWAY_FIELD_CREW, "FIELD")
    assert [m.key for m in modules] == [f"f0{n}" for n in range(1, 9)]
    assert tuple(m.title for m in modules) == MODULE_TITLES
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    for module, lesson in _field_lessons():
        assert lesson.what and lesson.why and lesson.exercise and lesson.steps, lesson.key
        assert C.lesson_roles(module, lesson) == ("FIELD",), lesson.key
        for step in lesson.steps:
            assert step.title and step.app in C.APPS and step.where and step.do and step.expect and step.if_wrong
            if step.endpoint:
                assert step.endpoint in endpoints, (lesson.key, step.endpoint)
            assert not step.endpoint or step.endpoint.startswith(("field.", "training.", "auth.")), step.endpoint
    cases = C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")
    assert len(cases) >= 8 and {c.module_key for c in cases} <= {m.key for m in modules}
    assert all(c.start and c.action and c.expected and c.roles == ("FIELD",) for c in cases)


def test_every_field_crew_screenshot_exists_and_is_iphone_sized(app):
    shots = Path(app.static_folder) / "training" / "shots"
    named = {step.shot for _m, lesson in _field_lessons() for step in lesson.steps if step.shot}
    assert len(named) >= 30
    for name in named:
        path = shots / name
        assert path.is_file(), name
        with path.open("rb") as fh:
            head = fh.read(24)
        assert head[:8] == b"\x89PNG\r\n\x1a\n", name
        width, height = struct.unpack(">II", head[16:24])
        assert width in (375, 390) and height in (812, 844), (name, width, height)  # pictured at iPhone size
    # The Field pictures come from the real Field pages (f..-*.png from tools/training/capture_field_crew_shots.mjs).
    assert all(n.startswith("f0") or n == "c11-field-delivery.png" for n in named)


def test_no_money_or_office_words_anywhere_in_the_field_crew_content():
    for module, lesson in _field_lessons():
        parts = [module.title, module.summary, lesson.title, lesson.what, lesson.why, lesson.exercise]
        for s in lesson.steps:
            parts += [s.title, s.where, s.do, s.enter, s.expect, s.if_wrong, s.why]
        found = MONEY.findall(" ".join(parts))
        assert not found, (lesson.key, found)
    for case in C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD"):
        assert not MONEY.findall(" ".join((case.title, case.start, case.action, case.expected))), case.key


def test_the_contractor_pathway_keeps_no_crew_lessons():
    assert C.track("CONTRACTOR", "FIELD") == C.PATHWAY_FIELD_CREW
    assert C.track("CONTRACTOR", "OWNER") == "CONTRACTOR" and C.track("SUPPLIER", "PRO_DESK") == "SUPPLIER"
    assert C.lessons_for("CONTRACTOR", "FIELD") == [] and C.uat_for("CONTRACTOR", "FIELD") == []
    assert C.lessons_for(C.PATHWAY_FIELD_CREW, "OWNER") == []


# ------------------------------------------------------------------ registration and what the crew see


def test_signin_page_names_the_three_groups(app):
    page = app.test_client().get("/training/signin").get_data(as_text=True)
    assert 'data-signin="field"' in page and "I work on a crew (Field)" in page
    assert "I work for a contractor" in page and "I work for a building supplier" in page


def test_kevin_registers_straight_into_field_crew_and_sees_only_it(app):
    kevin = _client(app, "kevin")
    page = _get(kevin, "/training").get_data(as_text=True)
    assert 'data-register-pathway="FIELD_CREW"' in page and "Start my Field Crew training" in page
    assert "Contractor owner" not in page and "Office staff" not in page and "Supplier" not in _main(page)
    assert _post(kevin, "/training/register", data={"role": "OWNER"}).status_code == 302
    assert TrainingTrainee.query.count() == 0, "a Field-only person cannot take the owner's pathway"
    _post(kevin, "/training/register", data={"role": "FIELD"})
    t = TrainingTrainee.query.one()
    assert (t.pathway, t.role, t.track) == ("CONTRACTOR", "FIELD", "FIELD_CREW")
    home = _get(kevin, "/training").get_data(as_text=True)
    assert "Field Crew training · Field worker" in home
    assert re.findall(r'data-module="([^"]+)"', home) == [f"f0{n}" for n in range(1, 9)]
    assert 'href="/field/today" data-open-field' in home
    assert "Change my role" not in home
    for key in ("c01-welcome", "c09-new-estimate", "c11-field-today", "s09-quick-quote"):
        assert _get(kevin, f"/training/lessons/{key}").status_code == 404, key
    for key in ("uat-c08-quote", "uat-c11-field", "uat-s09-quick-quote"):
        assert _get(kevin, f"/training/uat/{key}").status_code == 404, key
    assert _get(kevin, "/training/admin").status_code == 403
    assert _get(kevin, "/training/review/field-crew").status_code == 403


def test_every_field_crew_page_has_no_money_and_no_office_link(app):
    kevin = _kevin(app)
    pages = ["/training", "/training/uat", "/training/workflow"]
    pages += [f"/training/lessons/{lesson.key}" for _m, lesson in _field_lessons()]
    pages += [f"/training/uat/{c.key}" for c in C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")]
    for path in pages:
        r = _get(kevin, path)
        assert r.status_code == 200, path
        html = r.get_data(as_text=True)
        text = _text(_main(html))
        assert not MONEY.findall(text), (path, MONEY.findall(text))
        for href in _hrefs(html):
            if href.startswith(("https://fonts.googleapis.com", "https://fonts.gstatic.com")):
                continue  # the Training Centre's typeface
            assert href.startswith(ALLOWED), (path, href)


def test_owner_previews_field_crew_but_office_staff_and_crew_cannot(app):
    ben = _client(app, "ben")
    page = _get(ben, "/training/review/field-crew").get_data(as_text=True)
    for _m, lesson in _field_lessons():
        assert f"/training/review/lessons/{lesson.key}" in page
        assert _get(ben, f"/training/review/lessons/{lesson.key}?map=field").status_code == 200
    assert "/training/review/field-crew" in _get(ben, "/training/review").get_data(as_text=True)
    assert "Field worker" in _get(ben, "/training").get_data(as_text=True)  # the owner may also take it himself
    assert TrainingTrainee.query.count() == 0, "previewing registers no one"
    olivia = _client(app, "olivia")
    assert _get(olivia, "/training/review/field-crew").status_code == 403


# ------------------------------------------------------------------ saved progress, resume, Back / Next / Save / Exit


def test_progress_is_saved_and_resumed_with_back_next_save_and_exit(app):
    kevin = _kevin(app)
    first, second = _field_lessons()[0][1], _field_lessons()[1][1]
    home = _get(kevin, "/training").get_data(as_text=True)
    assert f"/training/lessons/{first.key}?step=0" in home and "Continue where I left off" in home
    for i in range(2):
        r = _post(kevin, f"/training/lessons/{first.key}/check", data={"step": i, "done": "1"},
                  headers={"X-Requested-With": "fetch"})
        assert r.get_json()["done"] is True
    r = _post(kevin, f"/training/lessons/{first.key}/move", data={"step": 2, "action": "next"})
    assert r.headers["Location"].endswith(f"/training/lessons/{first.key}?step=3")
    r = _post(kevin, f"/training/lessons/{first.key}/move", data={"step": 3, "action": "back"})
    assert r.headers["Location"].endswith(f"/training/lessons/{first.key}?step=2")
    # Save and exit from a page opened at step 1: the place saved is still the first step not ticked (step 3).
    r = _post(kevin, f"/training/lessons/{first.key}/move", data={"step": 0, "action": "exit"})
    assert r.headers["Location"].endswith("/training")
    # A new sign-in (another device) resumes at the first step not ticked, with the ticks kept.
    kevin = _client(app, "kevin")
    home = _get(kevin, "/training").get_data(as_text=True)
    assert f"/training/lessons/{first.key}?step=2" in home
    page = _get(kevin, f"/training/lessons/{first.key}?step=2").get_data(as_text=True)
    assert page.count('class="tc-step-card is-done') == 2 and "<span data-ticked>2</span>" in page
    assert f'href="/training/lessons/{second.key}" data-next-lesson' in page and "data-exit" in page
    for i in range(len(first.steps)):
        _post(kevin, f"/training/lessons/{first.key}/check", data={"step": i, "done": "1"})
    r = _post(kevin, f"/training/lessons/{first.key}/complete", data={"exercise_done": "1"})
    assert r.headers["Location"].endswith(f"/training/lessons/{second.key}")
    assert TrainingLessonProgress.query.filter(TrainingLessonProgress.completed_at.isnot(None)).count() == 1
    assert f"1 of {len(_field_lessons())} lessons done" in _get(kevin, "/training").get_data(as_text=True)


# ------------------------------------------------------------------ Field acceptance tests, apart from training


def test_field_uat_pass_fail_blocked_notes_and_retest_kept_apart_from_lessons(app):
    kevin = _kevin(app)
    cases = C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")
    a, b = cases[0], cases[1]
    page = _get(kevin, f"/training/uat/{a.key}").get_data(as_text=True)
    assert a.start in page and a.expected in page and 'data-tutor-mode="uat"' in page
    refused = _post(kevin, f"/training/uat/{a.key}", data={"status": "FAIL"}, follow_redirects=True)
    assert "Say what went wrong" in refused.get_data(as_text=True)
    _post(kevin, f"/training/uat/{a.key}", data={"status": "FAIL", "issue": "Training opened, not Field (synthetic)",
                                                 "notes": "On Safari (synthetic)"})
    _post(kevin, f"/training/uat/{b.key}", data={"status": "BLOCKED", "issue": "No signal on site (synthetic)"})
    lessons_before = TrainingLessonProgress.query.count()
    # Retest after the fix: a new attempt; the failed one stays.
    _post(kevin, f"/training/uat/{a.key}", data={"status": "PASS", "notes": "Retested after the fix (synthetic)"})
    rows = TrainingUatResult.query.filter_by(case_key=a.key).order_by(TrainingUatResult.attempt).all()
    assert [(r.attempt, r.status) for r in rows] == [(1, "FAIL"), (2, "PASS")]
    assert rows[0].issue == "Training opened, not Field (synthetic)" and rows[0].notes == "On Safari (synthetic)"
    assert TrainingLessonProgress.query.count() == lessons_before == 0, "acceptance tests are not lessons"
    page = _get(kevin, f"/training/uat/{a.key}").get_data(as_text=True)
    assert page.count("data-attempt=") == 2 and "Training opened, not Field" in page
    uat = _get(kevin, "/training/uat").get_data(as_text=True)
    assert f"1 passed · 0 failed · 1 blocked · {len(cases) - 2} not tested, of {len(cases)}" in uat
    home = _get(kevin, "/training").get_data(as_text=True)
    assert "0 of" in home and "1 passed, 0 failed, 1 blocked" in home  # lessons and tests counted apart
    for key in ("uat-c11-field", "uat-c01-sign-in"):
        assert _post(kevin, f"/training/uat/{key}", data={"status": "PASS"}).status_code == 404


def test_ben_sees_his_crew_with_failing_and_blocked_tests_flagged(app):
    kevin = _kevin(app)
    cases = C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")
    lesson = _field_lessons()[0][1]
    for i in range(len(lesson.steps)):
        _post(kevin, f"/training/lessons/{lesson.key}/check", data={"step": i, "done": "1"})
    _post(kevin, f"/training/lessons/{lesson.key}/complete", data={"exercise_done": "1"})
    _post(kevin, f"/training/uat/{cases[0].key}", data={"status": "FAIL", "issue": "Directions opened the wrong town (synthetic)"})
    _post(kevin, f"/training/uat/{cases[1].key}", data={"status": "BLOCKED", "issue": "No signal on site (synthetic)"})
    _post(kevin, f"/training/uat/{cases[2].key}", data={"status": "PASS"})
    ben = _client(app, "ben")
    html = _get(ben, "/training/admin").get_data(as_text=True)
    crew = re.search(r'data-admin-crew-member="Kevin Field \(training crew\)".*?</article>', html, re.S).group(0)
    assert f"Lessons: 1 of {len(_field_lessons())} done" in crew
    assert f"1 pass · 1 fail · 1 blocked · {len(cases) - 3} to do" in crew
    flagged = re.findall(r'data-crew-case="([^"]+)" class="tc-flag" data-flag', crew)
    assert flagged == [cases[0].key, cases[1].key]
    assert "Directions opened the wrong town" in crew and "Issues to fix" in crew
    assert 'data-admin-track="FIELD_CREW"' in html and "Field Crew training · Field worker" in html
    assert "Liam Field" not in html, "only crew who registered are listed"
    # After the fix and a passing retest, the flag goes.
    _post(kevin, f"/training/uat/{cases[0].key}", data={"status": "PASS", "notes": "Retest (synthetic)"})
    html = _get(ben, "/training/admin").get_data(as_text=True)
    crew = re.search(r'data-admin-crew-member="Kevin Field \(training crew\)".*?</article>', html, re.S).group(0)
    assert re.findall(r'data-crew-case="([^"]+)" class="tc-flag"', crew) == [cases[1].key]
    assert "1 retested" in crew
    for who in ("olivia", "kevin"):
        assert _get(_client(app, who), "/training/admin").status_code == 403


# ------------------------------------------------------------------ the Tutor and the Workflow Map


def test_tutor_answers_from_the_field_crew_lesson_and_minimizes(app):
    kevin = _kevin(app)
    module, lesson = next((m, l) for m, l in _field_lessons() if l.key == "f05-send-time")

    def ask(**data):
        return _post(kevin, "/training/tutor/ask", data=data, headers={"X-Requested-With": "fetch"}).get_json()["answer"]

    step = lesson.steps[1]
    assert step.if_wrong in ask(lesson=lesson.key, step=1, question="It didn't work")
    assert step.where in ask(lesson=lesson.key, step=1, question="Where is it?")
    assert step.enter in ask(lesson=lesson.key, step=1, question="What do I type?")
    assert lesson.steps[2].title in ask(lesson=lesson.key, step=1, question="What comes next?")
    office = C.find_lesson("c09-new-estimate")[1]
    assert office.steps[0].where not in ask(lesson="c09-new-estimate", step=0, question="Where is it?")
    page = _get(kevin, f"/training/lessons/{lesson.key}").get_data(as_text=True)
    assert 'data-tutor-mode="lesson"' in page and 'class="tc-tutor"' in page
    _post(kevin, "/training/tutor", data={"minimized": "1"}, headers={"X-Requested-With": "fetch"})
    assert 'class="tc-tutor is-min"' in _get(kevin, f"/training/lessons/{lesson.key}").get_data(as_text=True)
    assert "Open the Tutor" in _get(kevin, "/training").get_data(as_text=True)
    _post(kevin, "/training/tutor", data={"minimized": "0"}, headers={"X-Requested-With": "fetch"})
    page = _get(kevin, f"/training/lessons/{lesson.key}").get_data(as_text=True)
    assert 'class="tc-tutor"' in page and 'class="tc-tutor is-min"' not in page


def test_field_crew_lessons_are_on_the_workflow_maps_field_section(app):
    from app.workflow_map import definition as D

    on_field = {k for s in D.map_stages(D.MAP_FIELD) for k in s.lessons}
    assert {lesson.key for _m, lesson in _field_lessons()} <= on_field
    assert {c.key for c in C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")} <= {k for s in D.map_stages(D.MAP_FIELD) for k in s.uat}
    kevin = _kevin(app)
    html = _get(kevin, "/training/workflow").get_data(as_text=True)
    for label in ("SIGN IN", "TODAY", "ON THE JOB", "CAPTURE", "TIME"):
        assert label in html
    assert "/training/lessons/f01-start-training" in html and "/training/uat/uat-f01-sign-in" in html
    assert "/training/lessons/c" not in html and "/training/lessons/s" not in html
    page = _get(kevin, "/training/lessons/f04-drawings").get_data(as_text=True)
    assert "/training/workflow?stage=f-job" in page
    assert "/training/workflow?stage=f-start" in _get(kevin, "/training/uat/uat-f01-sign-in").get_data(as_text=True)
    field_map = _get(kevin, "/field/workflow").get_data(as_text=True)
    assert "/training/lessons/f06-capture" in field_map and "/training/lessons/c11-capture" not in field_map
    # The owner reviewing the Field map sees the crew's lessons, read-only.
    ben = _client(app, "ben")
    review = _get(ben, "/training/review/field").get_data(as_text=True)
    assert "/training/review/lessons/f06-capture?map=field" in review
