"""Supplier training for training administrators, with a synthetic supplier practice login (Joel, 24 Oct 2026).

Joel's Owner training sign-in takes the full Supplier trainee pathway from the header Pathway switch. Its Supplier
Hub practice opens as his own synthetic practice login "Joel Brayman (supplier practice)": made only on the training
site by environment.build, a member of BMR Winchester (training) only, with no usable password, opened only by a
CSRF-protected, audited POST from the Training Centre, with a way back to his own sign-in. His Supplier progress and
results are on his own trainee record, separate from his Contractor and Field ones, which stay intact. Everyone
else is refused, and nothing of it exists with TRAINING_ENVIRONMENT off. Synthetic data only; no password is
printed.
"""

from __future__ import annotations

import logging
import re

import pytest
from flask import g

from app import create_app, db
from app.models.supplier_catalogue import Supplier
from app.models.supplier_portal import SupplierUserMembership
from app.models.training import TrainingLessonProgress, TrainingTrainee, TrainingUatResult
from app.models.user import User, UserMembership
from app.services.auth import authenticate, verify_password
from app.services.supplier_hub import principal_class
from app.training import content as C
from app.training import environment
from app.training import practice as P
from app.training import service as svc

pytestmark = pytest.mark.no_office_auth
PW = {k: f"Synthetic-{k}-practice-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat", "admin")}
ADMIN = ("Joel Brayman", "joel.admin@training-test.invalid")
PRACTICE_NAME = "Joel Brayman (supplier practice)"


def _app(**extra):
    config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "t",
              "WTF_CSRF_ENABLED": False, "TRAINING_ENVIRONMENT": True}
    config.update(extra)
    return create_app(config)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.delenv("TRAINING_ENVIRONMENT", raising=False)
    application = _app()
    with application.app_context():
        db.create_all()
        environment.build(application, PW, administrator=ADMIN)
        yield application
        db.session.remove()
        db.drop_all()


def _get(client, path, **kw):
    g.pop("_login_user", None)
    return client.get(path, **kw)


def _post(client, path, **kw):
    g.pop("_login_user", None)
    return client.post(path, **kw)


def _email(key):
    if key == "admin":
        return ADMIN[1]
    return next(e for k, _n, e, *_ in environment.OFFICE_PEOPLE + environment.SUPPLIER_PEOPLE if k == key)


def _client(app, key):
    client = app.test_client()
    if key in ("darcy", "pat"):
        r = _post(client, "/supplier/login", data={"email": _email(key), "password": PW[key]})
    else:
        r = _post(client, "/login", data={"email": _email(key), "password": PW[key]})
    assert r.status_code == 302, key
    return client


def _who(client):
    """The signed-in person's name, from the Training Centre header (or the practice page)."""
    page = _get(client, "/training").get_data(as_text=True)
    return page


def _joel():
    return User.query.filter_by(email=ADMIN[1]).one()


def _practice_for(user):
    return User.query.filter_by(email=P.practice_email(user.id)).first()


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


def _keys(pathway, role):
    return {lesson.key for _m, lesson in C.lessons_for(pathway, role)} | {c.key for c in C.uat_for(pathway, role)}


# ------------------------------------------------------------------ the practice logins environment.build makes


def test_build_makes_one_synthetic_supplier_only_practice_login_per_training_administrator(app):
    supplier = Supplier.query.filter_by(code=P.TRAINING_SUPPLIER_CODE).one()
    assert supplier.demo_synthetic
    admins = P.training_administrators("ORG-001")
    assert {u.email for u in admins} == {ADMIN[1], _email("ben")}
    for admin in admins:
        practice = _practice_for(admin)
        assert practice.display_name == f"{admin.display_name} (supplier practice)"
        assert practice.email.endswith("@training.calibraytai.invalid") and practice.is_active
        assert UserMembership.query.filter_by(user_id=practice.id).count() == 0  # never on the contractor side
        assert [(m.supplier_id, m.status) for m in SupplierUserMembership.query.filter_by(user_id=practice.id)] == [
            (supplier.id, "ACTIVE")]
        assert principal_class(practice) == "SUPPLIER" and P.practice_login_for(admin).id == practice.id
        # No usable password: nothing verifies against it, and neither sign-in page lets it in.
        for guess in ("", "password", PW["admin"], practice.password_hash):
            assert not verify_password(practice.password_hash, guess)
            assert authenticate(practice.email, guess) is None
    # Nobody else has one.
    for key in ("olivia", "kevin", "liam", "darcy", "pat"):
        user = User.query.filter_by(email=_email(key)).one()
        assert _practice_for(user) is None and P.practice_login_for(user) is None
    # Running the build again adds nothing.
    count = (User.query.count(), SupplierUserMembership.query.count())
    again = environment.build(app, administrator=ADMIN)
    assert (User.query.count(), SupplierUserMembership.query.count()) == count
    assert {r["email"] for r in again["_practice"]} == {P.practice_email(u.id) for u in admins}
    assert not any(r["created"] for r in again["_practice"])


def test_only_training_administrators_get_the_supplier_pathway_and_the_practice_site(app):
    for key in ("olivia", "kevin"):
        user = User.query.filter_by(email=_email(key)).one()
        assert not set(svc.allowed_roles(user)) & {"SUPPLIER_OWNER", "SUPPLIER_ADMIN", "PRO_DESK"}, key
        c = _client(app, key)
        _post(c, "/training/register", data={"role": "FIELD"})
        assert _post(c, "/training/register", data={"role": "SUPPLIER_OWNER"}).status_code == 302
        assert TrainingTrainee.query.filter_by(user_id=user.id).one().role == "FIELD"
        r = _post(c, "/training/supplier-practice/open", data={"next": "/supplier/"})
        assert r.headers["Location"].endswith("/training")
        assert "/supplier" not in r.headers["Location"]
        page = _who(c)
        assert P.REFUSED in page and "data-supplier-practice-away" not in page  # refused; still themselves
    darcy = _client(app, "darcy")
    r = _post(darcy, "/training/supplier-practice/open", data={"next": "/supplier/"})
    assert r.headers["Location"].endswith("/training")
    assert "(supplier practice)" not in _get(darcy, "/supplier/", follow_redirects=True).get_data(as_text=True)
    joel = _joel()
    assert {"SUPPLIER_OWNER", "SUPPLIER_ADMIN", "PRO_DESK"} <= set(svc.allowed_roles(joel))


class _Lines(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())

    @property
    def text(self):
        return "\n".join(self.lines)


def test_joel_takes_the_supplier_pathway_on_his_own_record_with_the_practice_login(app):
    joel_user = _joel()
    owner_lesson = C.lessons_for(C.PATHWAY_CONTRACTOR, "OWNER")[0][1].key
    owner_case = C.uat_for(C.PATHWAY_CONTRACTOR, "OWNER")[0].key
    field_lesson = C.lessons_for(C.PATHWAY_FIELD_CREW, "FIELD")[0][1].key
    field_case = C.uat_for(C.PATHWAY_FIELD_CREW, "FIELD")[0].key
    supplier_lesson = C.lessons_for(C.PATHWAY_SUPPLIER, "SUPPLIER_OWNER")[0][1].key
    supplier_case = C.uat_for(C.PATHWAY_SUPPLIER, "SUPPLIER_OWNER")[0].key
    contractor_keys, field_keys = _keys(C.PATHWAY_CONTRACTOR, "OWNER"), _keys(C.PATHWAY_FIELD_CREW, "FIELD")
    supplier_keys = _keys(C.PATHWAY_SUPPLIER, "SUPPLIER_OWNER")
    assert not (contractor_keys | field_keys) & supplier_keys

    joel = _client(app, "admin")
    _post(joel, "/training/register", data={"role": "OWNER"})
    _do_lesson(joel, owner_lesson)
    _post(joel, f"/training/uat/{owner_case}", data={"status": "PASS", "notes": "owner ok"})
    _post(joel, "/training/register", data={"role": "FIELD"})
    _do_lesson(joel, field_lesson)
    _post(joel, f"/training/uat/{field_case}", data={"status": "BLOCKED", "issue": "synthetic: no signal"})
    trainee = TrainingTrainee.query.filter_by(user_id=joel_user.id).one()
    contractor_before, field_before = _snapshot(trainee.id, contractor_keys), _snapshot(trainee.id, field_keys)

    # The header Pathway switch offers the Supplier roles to the administrator.
    page = _get(joel, "/training").get_data(as_text=True)
    for role in ("SUPPLIER_OWNER", "SUPPLIER_ADMIN", "PRO_DESK"):
        assert f'data-pathway="{role}"' in page
    r = _post(joel, "/training/register", data={"role": "SUPPLIER_OWNER"}, follow_redirects=True)
    body = r.get_data(as_text=True)
    assert "You are now on Supplier owner training" in body and "Pathway: Supplier owner" in body
    assert "Supplier training from your own sign-in" in body
    assert f'data-lesson="{supplier_lesson}"' in body and f'data-lesson="{owner_lesson}"' not in body
    db.session.expire_all()
    assert trainee.track == C.PATHWAY_SUPPLIER and trainee.pathway == C.PATHWAY_CONTRACTOR

    # The supplier lesson's Supplier Hub steps open through the practice login.
    lesson = _get(joel, f"/training/lessons/{supplier_lesson}").get_data(as_text=True)
    assert f"Open the supplier practice site as {PRACTICE_NAME}" in lesson
    nexts = re.findall(r'name="next" value="([^"]+)"', lesson)
    assert nexts and all(n.startswith("/supplier") for n in nexts)
    caplog = _Lines()  # the audit lines, read straight from the audit logger (other tests reconfigure logging)
    P.audit.addHandler(caplog)
    P.audit.setLevel(logging.INFO)
    P.audit.disabled = False  # a logging dictConfig elsewhere in the suite may have disabled existing loggers
    r = _post(joel, "/training/supplier-practice/open", data={"next": nexts[0].replace("&amp;", "&")})
    assert r.status_code == 302 and r.headers["Location"].startswith("/supplier")
    hub = _get(joel, "/supplier/", follow_redirects=True).get_data(as_text=True)
    assert environment.SUPPLIER in hub and PRACTICE_NAME in hub
    assert f"Back to the Training Centre as {ADMIN[0]}" in hub
    assert "supplier practice opened" in caplog.text and str(joel_user.id) in caplog.text
    # In the Training Centre the practice login records nothing: it is offered the way back.
    away = _get(joel, "/training").get_data(as_text=True)
    assert "data-supplier-practice-away" in away and f"Back to the Training Centre as {ADMIN[0]}" in away
    _get(joel, f"/training/lessons/{supplier_lesson}")
    _post(joel, f"/training/lessons/{supplier_lesson}/check", data={"step": 0, "done": "1"})
    practice = _practice_for(joel_user)
    assert TrainingTrainee.query.filter_by(user_id=practice.id).count() == 0
    # Back to his own sign-in and the lesson step.
    r = _post(joel, "/training/supplier-practice/return", data={"back": f"/training/lessons/{supplier_lesson}?step=0"})
    assert r.headers["Location"].endswith(f"/training/lessons/{supplier_lesson}?step=0")
    assert "supplier practice closed" in caplog.text
    P.audit.removeHandler(caplog)
    home = _get(joel, "/training").get_data(as_text=True)
    assert "data-supplier-practice-away" not in home and "Pathway: Supplier owner" in home

    # Supplier progress and results go on Joel's own record.
    _do_lesson(joel, supplier_lesson)
    _post(joel, f"/training/uat/{supplier_case}", data={"status": "PASS", "notes": "supplier ok"})
    supplier_after = _snapshot(trainee.id, supplier_keys)
    assert supplier_after[0][supplier_lesson][3] is not None and supplier_after[1][0][2] == "PASS"
    assert _snapshot(trainee.id, contractor_keys) == contractor_before
    assert _snapshot(trainee.id, field_keys) == field_before
    tracks = svc.tracks_taken(trainee)
    assert [t[0] for t in tracks] == [C.PATHWAY_SUPPLIER, C.PATHWAY_CONTRACTOR, C.PATHWAY_FIELD_CREW]

    # Back to Owner: the Contractor lesson is still done; Supplier and Field are kept and shown on the dashboard.
    _post(joel, "/training/register", data={"role": "OWNER"})
    assert _snapshot(trainee.id, supplier_keys) == supplier_after
    admin = _get(joel, "/training/admin").get_data(as_text=True)
    tracks_shown = set(re.findall(rf'data-admin-trainee="{ADMIN[0]}[^"]*" data-admin-track="([A-Z_]+)"', admin))
    assert tracks_shown == {C.PATHWAY_CONTRACTOR, C.PATHWAY_FIELD_CREW, C.PATHWAY_SUPPLIER}


def test_the_practice_login_is_refused_unless_it_is_exactly_the_synthetic_supplier_only_login(app):
    joel_user = _joel()
    practice = _practice_for(joel_user)
    # Not on the contractor side.
    row = UserMembership(user_id=practice.id, organization_id="ORG-001", is_active=False)
    db.session.add(row)
    db.session.commit()
    assert P.practice_login_for(joel_user) is None
    db.session.delete(row)
    db.session.commit()
    assert P.practice_login_for(joel_user) is not None
    # Never a member of a real (not synthetic) supplier.
    from app.services.supplier_catalogue import create_supplier

    real = create_supplier(code="REAL-SUPPLIER-TEST", legal_name="A real store (test)", demo_synthetic=False)
    extra = SupplierUserMembership(user_id=practice.id, supplier_id=real.id, status="ACTIVE", created_by_name="test",
                                   created_by_organization_id="ORG-001")
    db.session.add(extra)
    db.session.commit()
    joel = _client(app, "admin")
    _post(joel, "/training/register", data={"role": "SUPPLIER_OWNER"})
    r = _post(joel, "/training/supplier-practice/open", data={"next": "/supplier/"})
    assert r.headers["Location"].endswith("/training")
    assert "data-supplier-practice-away" not in _who(joel)
    db.session.delete(extra)
    db.session.commit()
    # Only his own: the open always uses the signed-in administrator's linked login, whatever is posted.
    ben_practice = _practice_for(User.query.filter_by(email=_email("ben")).one())
    _post(joel, "/training/supplier-practice/open", data={"next": "/supplier/", "user_id": ben_practice.id})
    page = _get(joel, "/supplier/", follow_redirects=True).get_data(as_text=True)
    assert PRACTICE_NAME in page and ben_practice.display_name not in page
    # A next page off the Supplier Hub is not followed.
    _post(joel, "/training/supplier-practice/return", data={})
    r = _post(joel, "/training/supplier-practice/open", data={"next": "https://example.com/supplier/"})
    assert r.headers["Location"] == "/supplier/"


def test_open_and_return_need_the_csrf_token(monkeypatch):
    monkeypatch.delenv("TRAINING_ENVIRONMENT", raising=False)
    application = _app(WTF_CSRF_ENABLED=True)
    with application.app_context():
        db.create_all()
        environment.build(application, PW, administrator=ADMIN)
        client = application.test_client()
        page = _get(client, "/login").get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        assert _post(client, "/login", data={"email": ADMIN[1], "password": PW["admin"],
                                             "csrf_token": token}).status_code == 302
        assert _post(client, "/training/supplier-practice/open", data={"next": "/supplier/"}).status_code == 400
        assert _post(client, "/training/supplier-practice/return", data={}).status_code == 400
        assert "data-supplier-practice-away" not in _get(client, "/training").get_data(as_text=True)
        db.session.remove()
        db.drop_all()


def test_nothing_of_it_exists_when_training_environment_is_off(app, monkeypatch):
    joel_user = _joel()
    joel = _client(app, "admin")
    _post(joel, "/training/register", data={"role": "SUPPLIER_OWNER"})
    monkeypatch.setitem(app.config, "TRAINING_ENVIRONMENT", False)
    assert not svc.enabled()
    assert _post(joel, "/training/supplier-practice/open", data={"next": "/supplier/"}).status_code == 404
    assert _post(joel, "/training/supplier-practice/return", data={}).status_code == 404
    assert _get(joel, "/training").status_code == 404
    assert P.practice_login_for(joel_user) is None
    assert not set(svc.allowed_roles(joel_user)) & {"SUPPLIER_OWNER", "SUPPLIER_ADMIN", "PRO_DESK"}
    with pytest.raises(P.PracticeError):
        P.open_practice(joel_user, "/supplier/")
    with pytest.raises(P.PracticeError):
        P.ensure_practice_logins("ORG-001", Supplier.query.filter_by(code=P.TRAINING_SUPPLIER_CODE).one())
    with pytest.raises(environment.TrainingEnvironmentError):
        environment.build(app, administrator=ADMIN)
    # A practice login that somehow had a session gets no way back and no Training Centre.
    practice = _practice_for(joel_user)
    with app.test_request_context("/supplier/"):
        from flask_login import login_user

        login_user(practice)
        assert P.marker_for(practice) is None


def test_build_environment_says_when_an_account_already_existed(monkeypatch, tmp_path):
    monkeypatch.delenv("TRAINING_ENVIRONMENT", raising=False)
    uri = f"sqlite:///{tmp_path}/t.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri, "SECRET_KEY": "t",
                              "TRAINING_ENVIRONMENT": True})
    monkeypatch.setenv("TRAINING_PASSWORD_BEN", "Synthetic-ben-from-env-2")
    with application.app_context():
        db.create_all()
        runner = application.test_cli_runner()
        first = runner.invoke(args=["training", "build-environment", "--passwords-from-env"])
        assert first.exit_code == 0, first.output
        lines = {line.split()[1]: line for line in first.output.splitlines() if line.startswith(("OWNER", "OFFICE",
                                                                                                   "FIELD", "SUPPLIER"))}
        assert "(password from the site's settings)" in lines["Ben"]
        assert "(random; reset it to sign in)" in lines["Olivia"]
        second = runner.invoke(args=["training", "build-environment", "--passwords-from-env"])
        assert second.exit_code == 0, second.output
        people = [line for line in second.output.splitlines() if line.startswith(("OWNER", "OFFICE", "FIELD",
                                                                                     "SUPPLIER"))]
        assert people and all("(already existed; password unchanged)" in line for line in people), second.output
        assert "(random; reset it to sign in)" not in second.output
        assert "(password from the site's settings)" not in second.output
        assert "Synthetic-ben-from-env-2" not in first.output + second.output
        assert "PRACTICE" in second.output and "(no password: opened from the Training Centre" in second.output
        db.drop_all()


def test_a_supplier_acceptance_test_opens_the_practice_site_and_comes_back_to_the_test(app):
    joel = _client(app, "admin")
    _post(joel, "/training/register", data={"role": "PRO_DESK"})
    case = C.uat_for(C.PATHWAY_SUPPLIER, "PRO_DESK")[0].key
    page = _get(joel, f"/training/uat/{case}").get_data(as_text=True)
    assert f"Open the supplier practice site as {PRACTICE_NAME}" in page
    r = _post(joel, "/training/supplier-practice/open", data={"next": "/supplier/", "back": f"/training/uat/{case}"})
    assert r.headers["Location"] == "/supplier/"
    r = _post(joel, "/training/supplier-practice/return", data={})
    assert r.headers["Location"].endswith(f"/training/uat/{case}")
    assert _post(joel, f"/training/uat/{case}", data={"status": "PASS"}).status_code == 302
    trainee = TrainingTrainee.query.filter_by(user_id=_joel().id).one()
    assert TrainingUatResult.query.filter_by(trainee_id=trainee.id, case_key=case).count() == 1
