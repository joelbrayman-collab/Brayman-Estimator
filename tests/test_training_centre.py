"""Training & Acceptance Centre (Joel, 21 Oct 2026): registration, role-specific lessons, saved progress,
Back/Next, Save and exit, Tutor, training/UAT separation, Pass/Fail/Blocked with retests, notes,
administrator report, organization isolation, and the site switch. Synthetic data only."""

from __future__ import annotations

import pytest
from flask import g

from app import create_app, db
from app.models.training import TrainingLessonProgress, TrainingTrainee, TrainingUatResult
from app.training import content as C
from app.training import environment, service

pytestmark = pytest.mark.no_office_auth
PW = {k: f"Synthetic-{k}-training-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")}


def _app(enabled=True):
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
                       "WTF_CSRF_ENABLED": False, "TRAINING_ENVIRONMENT": enabled})


@pytest.fixture
def app():
    application = _app()
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


def test_switched_off_everywhere_but_the_training_site():
    application = _app(enabled=False)
    with application.app_context():
        db.create_all()
        assert application.test_client().get("/training").status_code == 404
        assert application.test_client().get("/training/admin").status_code == 404
        with pytest.raises(environment.TrainingEnvironmentError):
            environment.build(application)
        db.drop_all()


def test_signed_out_goes_to_the_training_sign_in(app):
    r = app.test_client().get("/training/lessons/c01-sign-in")
    assert r.status_code == 302 and r.headers["Location"].endswith("/training/signin")
    page = app.test_client().get("/training/signin").get_data(as_text=True)
    assert "I work for a contractor" in page and "I work for a building supplier" in page
    assert "I work on a crew (Field)" in page  # the third group: the Field crew (22 Oct 2026)


def test_registration_offers_the_roles_each_person_may_take(app):
    ben, kevin, darcy = _client(app, "ben"), _client(app, "kevin"), _client(app, "darcy")
    page = _get(ben, "/training").get_data(as_text=True)
    assert "Contractor owner" in page and "Office staff" in page and "Field worker" in page
    kev = _get(kevin, "/training").get_data(as_text=True)
    # Field-only crew register straight into the Field Crew training (22 Oct 2026), offered nothing else
    assert "Start my Field Crew training" in kev and "Contractor owner" not in kev and "Office staff" not in kev
    assert _post(kevin, "/training/register", data={"role": "OWNER"}).status_code == 302
    assert TrainingTrainee.query.count() == 0
    dar = _get(darcy, "/training").get_data(as_text=True)
    assert "Supplier owner" in dar and "PRO Desk staff" in dar and "Contractor owner" not in dar
    _post(darcy, "/training/register", data={"role": "SUPPLIER_ADMIN"})
    t = TrainingTrainee.query.one()
    assert t.pathway == "SUPPLIER" and t.supplier_id is not None and t.organization_id is None


def test_field_workers_get_only_field_lessons():
    # Field workers follow their own Field Crew pathway (22 Oct 2026); the contractor pathway has no crew lessons.
    assert C.track("CONTRACTOR", "FIELD") == "FIELD_CREW"
    assert C.lessons_for("FIELD_CREW", "FIELD")
    for module, lesson in C.lessons_for("FIELD_CREW", "FIELD"):
        assert "FIELD" in C.lesson_roles(module, lesson) and module.pathway == "FIELD_CREW"
    assert C.lessons_for("CONTRACTOR", "FIELD") == []
    office_only = [lesson.key for m in C.modules() for lesson in m.lessons if m.pathway == "CONTRACTOR"]
    field_keys = {lesson.key for _m, lesson in C.lessons_for("FIELD_CREW", "FIELD")}
    assert not field_keys & set(office_only)


def test_lessons_save_resume_back_next_and_complete(app):
    ben = _client(app, "ben")
    _post(ben, "/training/register", data={"role": "OWNER"})
    module, lesson = C.lessons_for("CONTRACTOR", "OWNER")[0]
    page = _get(ben, f"/training/lessons/{lesson.key}").get_data(as_text=True)
    assert all(st.title in page for st in lesson.steps) and f"<span data-ticked>0</span> of {len(lesson.steps)} steps done" in page
    r = _post(ben, f"/training/lessons/{lesson.key}/move", data={"step": 0, "action": "next"})
    assert r.headers["Location"].endswith(f"/training/lessons/{lesson.key}?step=1")
    _post(ben, f"/training/lessons/{lesson.key}/move", data={"step": 1, "action": "back"})
    r = _post(ben, f"/training/lessons/{lesson.key}/move", data={"step": 1, "action": "exit"})
    assert r.headers["Location"].endswith("/training")
    home = _get(ben, "/training").get_data(as_text=True)
    assert f"/training/lessons/{lesson.key}?step=1" in home and "Continue where I left off" in home
    last = len(lesson.steps) - 1
    refused = _post(ben, f"/training/lessons/{lesson.key}/complete", data={"exercise_done": "1"}, follow_redirects=True)
    assert "Tick each step as you do it first" in refused.get_data(as_text=True)
    # Tick each step (the green check); unticking and ticking again keeps one tick.
    for i in range(len(lesson.steps)):
        r = _post(ben, f"/training/lessons/{lesson.key}/check", data={"step": i, "done": "1"},
                  headers={"X-Requested-With": "fetch"})
        assert r.get_json()["done"] is True and r.get_json()["ticked"] == i + 1
    _post(ben, f"/training/lessons/{lesson.key}/check", data={"step": 0, "done": "0"}, headers={"X-Requested-With": "fetch"})
    assert TrainingLessonProgress.query.one().steps_done == list(range(1, len(lesson.steps)))
    page = _get(ben, f"/training/lessons/{lesson.key}").get_data(as_text=True)
    assert page.count('class="tc-step-card is-done') == len(lesson.steps) - 1
    _post(ben, f"/training/lessons/{lesson.key}/check", data={"step": 0, "done": "1"})
    assert _post(ben, f"/training/lessons/{lesson.key}/check", data={"step": 99, "done": "1"}).status_code == 404
    refused = _post(ben, f"/training/lessons/{lesson.key}/complete", data={}, follow_redirects=True)
    assert "I did the practice exercise" in refused.get_data(as_text=True)
    assert TrainingLessonProgress.query.one().completed_at is None
    _post(ben, f"/training/lessons/{lesson.key}/complete", data={"exercise_done": "1"})
    p = TrainingLessonProgress.query.one()
    assert p.completed_at is not None and p.exercise_done and p.step_reached == last
    home = _get(ben, "/training").get_data(as_text=True)
    assert "1 of" in home and ">Completed<" in home and "Review again" in home
    # A lesson outside the person's pathway is not theirs.
    supplier_lesson = C.lessons_for("SUPPLIER", "PRO_DESK")[0][1]
    assert _get(ben, f"/training/lessons/{supplier_lesson.key}").status_code == 404


def test_tutor_minimize_restore_and_answers(app):
    ben = _client(app, "ben")
    _post(ben, "/training/register", data={"role": "OWNER"})
    _m, lesson = C.lessons_for("CONTRACTOR", "OWNER")[0]
    _post(ben, "/training/tutor", data={"minimized": "1"}, headers={"X-Requested-With": "fetch"})
    assert TrainingTrainee.query.one().tutor_minimized is True
    assert "is-min" in _get(ben, f"/training/lessons/{lesson.key}").get_data(as_text=True)
    _post(ben, "/training/tutor", data={"minimized": "0"}, headers={"X-Requested-With": "fetch"})
    assert TrainingTrainee.query.one().tutor_minimized is False
    answer = _post(ben, "/training/tutor/ask", json={"lesson": lesson.key, "step": 0, "question": "Where is the button?"})
    assert lesson.steps[0].where in answer.get_json()["answer"]
    saved = _post(ben, "/training/tutor/ask", json={"lesson": lesson.key, "step": 0, "question": "how do I save and continue later"})
    assert "Continue where I left off" in saved.get_json()["answer"]
    # The tutor's answer does not move or lose the lesson position.
    assert TrainingTrainee.query.one().training_resume == f"{lesson.key}:0"


def test_uat_is_separate_with_pass_fail_blocked_and_retests(app):
    ben = _client(app, "ben")
    _post(ben, "/training/register", data={"role": "OWNER"})
    case = C.uat_for("CONTRACTOR", "OWNER")[0]
    refused = _post(ben, f"/training/uat/{case.key}", data={"status": "FAIL"}, follow_redirects=True)
    assert "Say what went wrong" in refused.get_data(as_text=True) and TrainingUatResult.query.count() == 0
    _post(ben, f"/training/uat/{case.key}", data={"status": "FAIL", "issue": "Password page error (synthetic)"})
    _post(ben, f"/training/uat/{case.key}", data={"status": "BLOCKED", "issue": "Waiting for the fix (synthetic)"})
    _post(ben, f"/training/uat/{case.key}", data={"status": "PASS", "notes": "Retested after the fix"})
    attempts = TrainingUatResult.query.order_by(TrainingUatResult.attempt).all()
    assert [(a.attempt, a.status) for a in attempts] == [(1, "FAIL"), (2, "BLOCKED"), (3, "PASS")]
    page = _get(ben, f"/training/uat/{case.key}").get_data(as_text=True)
    assert "Attempt 1" in page and "Password page error" in page
    assert TrainingLessonProgress.query.count() == 0  # UAT never counts as training
    assert _post(ben, f"/training/uat/{case.key}", data={"status": "MAYBE"}).status_code == 302
    assert TrainingUatResult.query.count() == 3
    other = C.uat_for("SUPPLIER", "PRO_DESK")[0]
    assert _get(ben, f"/training/uat/{other.key}").status_code == 404


def test_notes_and_feedback_persist(app):
    ben = _client(app, "ben")
    _post(ben, "/training/register", data={"role": "OWNER"})
    _m, lesson = C.lessons_for("CONTRACTOR", "OWNER")[0]
    _post(ben, f"/training/lessons/{lesson.key}/feedback", data={"body": "The key button is small (synthetic)", "step": 0})
    assert "The key button is small" in _get(ben, f"/training/lessons/{lesson.key}").get_data(as_text=True)


def test_admin_dashboard_access_and_isolation(app):
    from app.models import Organization
    from app.models.supplier_catalogue import Supplier
    from app.models.supplier_portal import MEMBERSHIP_ACTIVE, SupplierUserMembership
    from app.models.user import User, UserMembership
    from app.services.auth import hash_password

    ben, olivia, kevin, darcy = (_client(app, k) for k in ("ben", "olivia", "kevin", "darcy"))
    _post(olivia, "/training/register", data={"role": "OFFICE"})
    _post(kevin, "/training/register", data={"role": "FIELD"})
    _post(darcy, "/training/register", data={"role": "SUPPLIER_OWNER"})
    case = C.uat_for("FIELD_CREW", "FIELD")[0]
    _post(kevin, f"/training/uat/{case.key}", data={"status": "BLOCKED", "issue": "No signal on site (synthetic)"})
    # Another company and an unrelated supplier, each with a trainee.
    db.session.add(Organization(id="ORG-OTHER", legal_name="Other Co (synthetic)", display_name="Other Co", is_active=True))
    other = User(email="other@example.invalid", display_name="Other Person", password_hash=hash_password("x-pass-1234567"), is_active=True)
    stranger = User(email="stranger@example.invalid", display_name="Stranger Supplier", password_hash=hash_password("x-pass-1234567"), is_active=True)
    db.session.add_all([other, stranger])
    db.session.flush()
    db.session.add(UserMembership(user_id=other.id, organization_id="ORG-OTHER", is_active=True))
    lone = Supplier(code="LONE-SUPPLY", legal_name="Lone Supply (synthetic)", status="ACTIVE", demo_synthetic=True)
    db.session.add(lone)
    db.session.flush()
    db.session.add(SupplierUserMembership(user_id=stranger.id, supplier_id=lone.id, status=MEMBERSHIP_ACTIVE,
                                          created_by_name="test", created_by_organization_id="ORG-OTHER"))
    db.session.commit()
    service.register(other, "OWNER")
    service.register(stranger, "PRO_DESK")
    page = _get(ben, "/training/admin")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert "Olivia Office" in text and "Kevin Field" in text and "Darcy" in text
    assert "Other Person" not in text and "Stranger Supplier" not in text
    assert "No signal on site" in text  # outstanding issue listed
    for c in (olivia, kevin, darcy):
        assert _get(c, "/training/admin").status_code == 403


def test_environment_build_is_repeatable_and_synthetic(app):
    again = environment.build(app)
    assert all(row["password"] is None for k, row in again.items() if not k.startswith("_"))
    from app.models import Client, Project

    assert Client.query.filter_by(name=environment.CUSTOMER).count() == 1
    assert Project.query.filter_by(name=environment.JOB).count() == 1


def test_content_points_only_at_real_pages_and_screenshots(app):
    from pathlib import Path

    shots = Path(app.static_folder) / "training" / "shots"
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    keys = set()
    for module in C.modules():
        assert module.lessons, module.key
        for lesson in module.lessons:
            assert lesson.key not in keys, lesson.key
            keys.add(lesson.key)
            assert lesson.steps and lesson.exercise and lesson.what and lesson.why, lesson.key
            for step in lesson.steps:
                assert step.app in C.APPS, (lesson.key, step.title)
                assert step.where and step.do and step.expect and step.if_wrong, (lesson.key, step.title)
                if step.endpoint:
                    assert step.endpoint in endpoints, (lesson.key, step.endpoint)
                if step.shot:
                    assert (shots / step.shot).is_file(), (lesson.key, step.shot)
    module_keys = {m.key for m in C.modules()}
    case_keys = [c.key for c in C.uat_cases()]
    assert len(case_keys) == len(set(case_keys))
    for case in C.uat_cases():
        assert case.module_key in module_keys and case.start and case.action and case.expected and case.roles


def test_signing_in_on_the_training_site_lands_in_training(app):
    g.pop("_login_user", None)
    r = app.test_client().post("/login", data={"email": _email("ben"), "password": PW["ben"]})
    assert r.headers["Location"].endswith("/training")
    g.pop("_login_user", None)
    r = app.test_client().post("/supplier/login", data={"email": _email("darcy"), "password": PW["darcy"]})
    assert r.headers["Location"].endswith("/training")


def _ask(client, **data):
    return _post(client, "/training/tutor/ask", data=data, headers={"X-Requested-With": "fetch"}).get_json()["answer"]


def test_tutor_follows_the_lesson_troubleshoots_and_stays_within_the_trainees_lessons(app):
    ben = _client(app, "ben")
    _post(ben, "/training/register", data={"role": "OWNER"})
    _m, lesson = next((m, l) for m, l in C.lessons_for("CONTRACTOR", "OWNER") if len(l.steps) >= 2)
    first, second = lesson.steps[0], lesson.steps[1]
    assert first.if_wrong in _ask(ben, lesson=lesson.key, step=0, question="It didn't work")
    typed = _ask(ben, lesson=lesson.key, step=0, question="What do I type?")
    assert (first.enter and first.enter in typed) or "Nothing needs typing" in typed
    assert second.title in _ask(ben, lesson=lesson.key, step=0, question="What comes next?")
    last = len(lesson.steps) - 1
    assert "practice exercise" in _ask(ben, lesson=lesson.key, step=last, question="What comes next?")
    assert second.expect in _ask(ben, lesson=lesson.key, step=1, question="What should I see?")
    # Another pathway's lesson is not the trainee's: the Tutor gives general help, never that lesson's text.
    _sm, supplier_lesson = C.lessons_for("SUPPLIER", "PRO_DESK")[-1]
    answer = _ask(ben, lesson=supplier_lesson.key, step=0, question="Where is it?")
    assert all(s.where not in answer for s in supplier_lesson.steps)
    # The Tutor's answers never move the trainee's saved place.
    before = TrainingTrainee.query.one().training_resume
    _ask(ben, lesson=lesson.key, step=last, question="Where is it?")
    assert TrainingTrainee.query.one().training_resume == before


def test_tutor_on_home_and_acceptance_tests_and_minimized_everywhere(app):
    ben = _client(app, "ben")
    _post(ben, "/training/register", data={"role": "OWNER"})
    home = _get(ben, "/training").get_data(as_text=True)
    assert 'data-tutor-mode="home"' in home and "Continue where I left off" in home
    case = C.uat_for("CONTRACTOR", "OWNER")[0]
    page = _get(ben, f"/training/uat/{case.key}").get_data(as_text=True)
    assert 'data-tutor-mode="uat"' in page and "How to do this test" in page
    assert "Fail:" in _ask(ben, case=case.key, question="When is it a fail or blocked?")
    assert case.start in _ask(ben, case=case.key, question="Where do I start?")
    other = C.uat_for("SUPPLIER", "PRO_DESK")[0]
    assert other.start not in _ask(ben, case=other.key, question="Where do I start?")
    _post(ben, "/training/tutor", data={"minimized": "1"}, headers={"X-Requested-With": "fetch"})
    assert 'class="tc-tutor is-min"' in _get(ben, "/training").get_data(as_text=True)
    assert 'class="tc-tutor is-min"' in _get(ben, f"/training/uat/{case.key}").get_data(as_text=True)


def test_field_and_supplier_tutors_answer_from_their_own_lessons(app):
    kevin, pat = _client(app, "kevin"), _client(app, "pat")
    _post(kevin, "/training/register", data={"role": "FIELD"})
    _post(pat, "/training/register", data={"role": "PRO_DESK"})
    _fm, field_lesson = C.lessons_for("FIELD_CREW", "FIELD")[0]
    assert field_lesson.steps[0].where in _ask(kevin, lesson=field_lesson.key, step=0, question="Where is it?")
    office_only = next(l for m, l in C.lessons_for("CONTRACTOR", "OWNER")
                       if "FIELD" not in C.lesson_roles(m, l))
    assert office_only.steps[0].where not in _ask(kevin, lesson=office_only.key, step=0, question="Where is it?")
    _pm, pd_lesson = C.lessons_for("SUPPLIER", "PRO_DESK")[-1]
    assert pd_lesson.steps[0].where in _ask(pat, lesson=pd_lesson.key, step=0, question="Where is it?")
