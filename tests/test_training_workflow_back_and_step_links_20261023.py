"""Workflow map Back button and step buttons that open the page or calculator (23 Oct 2026). Synthetic data only."""

from __future__ import annotations

import re

import pytest
from flask import g

from app import create_app, db
from app.training import content as C
from app.training import environment
from app.training.links import STEP_LINKS, links_for_lesson

pytestmark = pytest.mark.no_office_auth
PW = {k: f"Synthetic-{k}-training-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")}


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


def _client(app, key, role):
    g.pop("_login_user", None)
    client = app.test_client()
    if key in ("darcy", "pat"):
        client.post("/supplier/login", data={"email": _email(key), "password": PW[key], "next": "/training"})
    else:
        client.post("/login", data={"email": _email(key), "password": PW[key]})
    g.pop("_login_user", None)
    client.post("/training/register", data={"role": role})
    return client


def _get(client, path):
    g.pop("_login_user", None)
    return client.get(path)


def test_the_workflow_map_has_a_back_button_to_where_it_was_opened_from(app):
    ben = _client(app, "ben", "OWNER")
    direct = _get(ben, "/training/workflow").get_data(as_text=True)
    assert 'data-map-back' in direct and 'href="/training"' in direct and "Back to the Training Centre" in direct
    page = _get(ben, "/training/workflow?back=/training/lessons/c08-concrete-request%3Fstep%3D1").get_data(as_text=True)
    assert 'href="/training/lessons/c08-concrete-request?step=1"' in page and "Back to the lesson" in page
    assert page.index("data-map-back") < page.index('id="workflow-map"')  # above the map
    # The stage links inside the map keep the way back.
    assert re.search(r'workflow\?[^"]*back=%2Ftraining%2Flessons', page) or "back=/training/lessons" in page


@pytest.mark.parametrize("bad", ["https://evil.example/", "//evil.example", "/login", "/training/../admin\\x",
                                 "javascript:alert(1)", "/training/workflow?back=/training"])
def test_the_back_target_must_be_a_training_page_on_this_site(app, bad):
    ben = _client(app, "ben", "OWNER")
    page = _get(ben, "/training/workflow?back=" + bad).get_data(as_text=True)
    assert 'data-map-back' in page and "evil.example" not in page and "javascript:" not in page
    assert re.search(r'data-map-back[^>]*>|href="/training"[^>]*data-map-back', page)
    assert 'href="/training" data-map-back' in page


def test_the_navigation_link_to_the_map_remembers_the_page_it_was_clicked_on(app):
    ben = _client(app, "ben", "OWNER")
    page = _get(ben, "/training/lessons/c08-concrete-request").get_data(as_text=True)
    assert "data-workflow-map-link" in page and "back=%2Ftraining%2Flessons%2Fc08-concrete-request" in page


def test_the_concrete_quote_step_opens_the_calculator_and_the_request_form(app):
    ben = _client(app, "ben", "OWNER")
    page = _get(ben, "/training/lessons/c08-concrete-request").get_data(as_text=True)
    assert "Open the concrete calculator" in page and 'href="/calculators/concrete?tc_back=' in page
    assert "Complete the concrete request" in page and "/supplier-requests?tc_back=" in page and "#concrete" in page
    assert page.count("data-step-link") >= 2
    assert "tc_focus=volume_m3" in page and "tc_back=%2Ftraining%2Flessons%2Fc08-concrete-request%3Fstep%3D1%23step-2" in page
    # Ticking, order and the lesson itself are unchanged.
    assert page.count("I did this step") == len(C.find_lesson("c08-concrete-request")[1].steps)


def test_every_listed_step_exists_and_every_button_points_at_a_real_page(app):
    ben = _client(app, "ben", "OWNER")
    for (key, number), _links in STEP_LINKS.items():
        found = C.find_lesson(key)
        assert found, key
        assert 1 <= number <= len(found[1].steps), (key, number)
    for lesson_key in {k for k, _n in STEP_LINKS}:
        for _label, href in sum(links_for_lesson(lesson_key, _trainee(app, "ben")).values(), []):
            assert href.startswith("/") and "None" not in href, (lesson_key, href)


def _trainee(app, who):
    from app.models.training import TrainingTrainee
    return TrainingTrainee.query.order_by(TrainingTrainee.id.desc()).first()


def test_a_supplier_step_opens_the_supplier_page_only_when_the_page_exists(app):
    darcy = _client(app, "darcy", "SUPPLIER_ADMIN")
    page = _get(darcy, "/training/lessons/s08-settings").get_data(as_text=True)
    assert "Complete the Quote settings page" in page and "/pro-desk/settings" in page
    # No request has been sent to this store yet, so the quote buttons are not shown rather than invented.
    assert "data-step-link" not in _get(darcy, "/training/lessons/s05-confirm").get_data(as_text=True)


def test_a_page_opened_from_a_step_has_a_one_click_way_back_and_the_field_focus_hook(app):
    ben = _client(app, "ben", "OWNER")
    back = "/training/lessons/c08-concrete-request?step=1%23step-2"
    page = _get(ben, "/calculators/concrete?tc_back=" + back.replace("?", "%3F").replace("/", "%2F") + "&tc_focus=length").get_data(as_text=True)
    assert "data-training-return" in page and "Back to the lesson step" in page
    assert 'href="/training/lessons/c08-concrete-request?step=1#step-2"' in page
    assert 'data-tc-focus="length"' in page and "training/site-bar.js" in page
    # The way back survives moving around the office pages, and is cleared once the trainee is back in the lessons.
    assert "Back to the lesson step" in _get(ben, "/calculators/concrete").get_data(as_text=True)
    _get(ben, "/training")
    assert "Back to the lesson step" not in _get(ben, "/calculators/concrete").get_data(as_text=True)


@pytest.mark.parametrize("bad", ["https://evil.example/", "//evil.example/x", "/login", "/training/lessons/a//b",
                                 "/training/lessons/x\ry"])
def test_only_a_lesson_page_on_this_site_can_be_the_way_back(app, bad):
    ben = _client(app, "ben", "OWNER")
    from urllib.parse import quote
    page = _get(ben, "/calculators/concrete?tc_back=" + quote(bad, safe="")).get_data(as_text=True)
    assert "data-training-return" not in page and "evil.example" not in page


def test_a_focus_value_is_only_a_plain_field_name(app):
    ben = _client(app, "ben", "OWNER")
    page = _get(ben, "/calculators/concrete?tc_focus=%22%3E%3Cscript%3Ex%3C%2Fscript%3E").get_data(as_text=True)
    assert "data-tc-focus" not in page and "<script>x</script>" not in page
