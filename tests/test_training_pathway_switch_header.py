"""Change training pathway from the Training Centre header (Joel, 24 Oct 2026). Synthetic data only.

An office (not Field-only) training sign-in sees a "Pathway" control in the header on every Training Centre page,
switches Office -> Field Crew -> Office in one click each, and each pathway's lessons, progress and acceptance
results are kept. A Field-only crew member has one pathway and sees no switch. Administrators also get the Supplier
owner-review map from the same control."""

from __future__ import annotations

import pytest

from app.models.training import TrainingLessonProgress, TrainingTrainee
from app.training import content as C
from tests.test_training_module_times_and_role_switch import PW, _client, _do_lesson, _get, _post, app  # noqa: F401

pytestmark = pytest.mark.no_office_auth


def _first_lesson(track_pathway, role):
    return C.lessons_for(track_pathway, role)[0][1].key


def test_the_header_switch_takes_office_to_field_and_back_keeping_both(app):  # noqa: F811
    c = _client(app, "olivia")
    assert _post(c, "/training/register", data={"role": "OFFICE"}).status_code == 302
    page = _get(c, "/training").get_data(as_text=True)
    assert "data-pathway-switch" in page and "Pathway: Contractor (office)" in page
    assert 'data-pathway="FIELD"' in page and 'data-pathway="OFFICE"' in page
    office_key = _first_lesson(C.PATHWAY_CONTRACTOR, "OFFICE")
    _do_lesson(c, office_key)
    trainee = TrainingTrainee.query.filter_by(display_name="Olivia Office (training)").one()
    done_before = {p.lesson_key: p.completed_at for p in TrainingLessonProgress.query.filter_by(trainee_id=trainee.id)}
    assert office_key in done_before and done_before[office_key] is not None

    # The switch is on other Training Centre pages too, not only the home page.
    for path in ("/training/uat", "/training/workflow", f"/training/lessons/{office_key}"):
        assert "data-pathway-switch" in _get(c, path).get_data(as_text=True), path

    r = _post(c, "/training/register", data={"role": "FIELD"}, follow_redirects=True)
    body = r.get_data(as_text=True)
    assert "You are now on Field Crew training" in body and "Pathway: Field Crew" in body
    field_key = _first_lesson(C.PATHWAY_FIELD_CREW, "FIELD")
    assert f'data-lesson="{field_key}"' in body and f'data-lesson="{office_key}"' not in body
    _do_lesson(c, field_key)

    r = _post(c, "/training/register", data={"role": "OFFICE"}, follow_redirects=True)
    assert "Pathway: Contractor (office)" in r.get_data(as_text=True)
    after = {p.lesson_key: p.completed_at for p in TrainingLessonProgress.query.filter_by(trainee_id=trainee.id)}
    assert after[office_key] == done_before[office_key], "Office progress kept unchanged"
    assert after.get(field_key) is not None, "Field progress kept"


def test_a_field_only_crew_member_has_no_switch(app):  # noqa: F811
    c = _client(app, "kevin")
    _post(c, "/training/register", data={"role": "FIELD"})
    page = _get(c, "/training").get_data(as_text=True)
    assert "data-pathway-switch" not in page
    r = _post(c, "/training/register", data={"role": "OFFICE"}, follow_redirects=True)
    assert TrainingTrainee.query.filter_by(display_name="Kevin Field (training crew)").one().role == "FIELD"


def test_the_owner_sees_supplier_owner_review_in_the_switch(app):  # noqa: F811
    c = _client(app, "ben")
    _post(c, "/training/register", data={"role": "OWNER"})
    page = _get(c, "/training").get_data(as_text=True)
    assert "data-pathway-switch" in page
    # Ben is the training company's owner; the supplier map is offered as owner review only when he is a
    # training administrator.
    from app.training import service as svc
    from app.models.user import User

    ben = User.query.filter_by(email="ben@training.calibraytai.invalid").one()
    if svc.is_admin(ben) is not None:
        assert "data-pathway-supplier-review" in page
