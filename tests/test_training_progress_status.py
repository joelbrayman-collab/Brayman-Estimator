"""Training home lesson status (Joel, 24 Oct 2026): Completed with a green check and Review again, In Progress,
the next recommended lesson highlighted, module counts, on the Contractor, Field Crew and Supplier pathways, all
from the saved progress. Reviewing a completed lesson (opening it, stepping through it, ticking, Save and exit,
Finish again) changes neither its completion nor any acceptance test result. Synthetic data only."""

from __future__ import annotations

import re

import pytest

from app import db
from app.models.training import TrainingLessonProgress, TrainingTrainee, TrainingUatResult
from app.training import content as C
from app.training import service
from tests.test_training_centre import _client, _get, _post, app  # noqa: F401  (the app fixture)

pytestmark = pytest.mark.no_office_auth

PATHWAYS = [("ben", "OWNER", "CONTRACTOR"), ("kevin", "FIELD", "FIELD_CREW"), ("darcy", "SUPPLIER_ADMIN", "SUPPLIER")]


def _finish(client, lesson):
    for i in range(len(lesson.steps)):
        _post(client, f"/training/lessons/{lesson.key}/check", data={"step": i, "done": "1"},
              headers={"X-Requested-With": "fetch"})
    assert _post(client, f"/training/lessons/{lesson.key}/complete", data={"exercise_done": "1"}).status_code == 302


def _row(home, key):
    m = re.search(rf'<li data-lesson-row="{re.escape(key)}"(.*?)</li>', home, re.S)
    assert m, key
    return m.group(0)


def _record(trainee_id):
    db.session.expire_all()
    lessons = {p.lesson_key: (p.step_reached, sorted(p.steps_done or []), p.exercise_done, p.completed_at, p.release)
               for p in TrainingLessonProgress.query.filter_by(trainee_id=trainee_id)}
    uat = [(r.case_key, r.attempt, r.status, r.notes, r.issue, r.recorded_at)
           for r in TrainingUatResult.query.filter_by(trainee_id=trainee_id).order_by(TrainingUatResult.id)]
    return lessons, uat


@pytest.mark.parametrize("who,role,track", PATHWAYS)
def test_home_shows_completed_in_progress_next_and_module_counts(app, who, role, track):  # noqa: F811
    client = _client(app, who)
    _post(client, "/training/register", data={"role": role})
    lessons = C.lessons_for(track, role)
    first, second, third = lessons[0][1], lessons[1][1], lessons[2][1]
    _finish(client, first)
    # The second lesson is started (one step ticked) and left with Save and exit.
    _post(client, f"/training/lessons/{second.key}/check", data={"step": 0, "done": "1"})
    _post(client, f"/training/lessons/{second.key}/move", data={"step": 1, "action": "exit"})
    home = _get(client, "/training").get_data(as_text=True)

    done = _row(home, first.key)
    assert 'data-lesson-status="completed"' in done and "tc-done" in done
    assert '<span class="tc-lesson-box" aria-hidden="true">&#10003;</span>' in done
    assert ">Completed</span>" in done and f'data-review-again="{first.key}"' in done and "Review again" in done
    assert f"/training/lessons/{first.key}?step=0" in done  # completed lessons stay clickable, from the start
    assert "data-next-recommended" not in done

    started = _row(home, second.key)
    assert 'data-lesson-status="in-progress"' in started and ">In Progress</span>" in started
    assert f"1 of {len(second.steps)} steps" in started
    assert "data-next-recommended" in started and "tc-next" in started and ">Next</span>" in started
    assert home.count("data-next-recommended") == 1 and home.count("data-next-badge") == 1

    fresh = _row(home, third.key)
    assert 'data-lesson-status="not-started"' in fresh and "Completed" not in fresh and "In Progress" not in fresh

    ov = service.overview(TrainingTrainee.query.one())
    row = ov["modules"][0]
    m = re.search(rf'data-module="{row["module"].key}".*?</section>', home, re.S).group(0)
    assert f'<span aria-hidden="true">{row["done"]}/{row["total"]}</span>' in m
    assert f'data-module-progress="{row["percent"]}"' in m
    in_module = {x["lesson"].key for x in row["lessons"]}
    assert row["done"] == 1 and row["started"] == (1 if second.key in in_module else 0)
    assert f'{row["done"]} of {row["total"]} lessons completed</span>' in m
    if row["started"]:
        assert f"{row['started']} in progress" in m
    # Module times are kept.
    if row["time"]:
        assert f'data-module-time="{row["time"].minutes}"' in m


def test_a_finished_module_shows_module_complete(app):  # noqa: F811
    ben = _client(app, "ben")
    _post(ben, "/training/register", data={"role": "OWNER"})
    module = C.modules_for("CONTRACTOR", "OWNER")[0]
    for lesson in module.lessons:
        _finish(ben, lesson)
    home = _get(ben, "/training").get_data(as_text=True)
    m = re.search(rf'<section [^>]*data-module="{module.key}".*?</section>', home, re.S).group(0)
    assert "tc-module-complete" in m and "Module complete" in m and 'data-module-progress="100"' in m
    assert m.count('data-lesson-status="completed"') == len(module.lessons)
    nxt = C.modules_for("CONTRACTOR", "OWNER")[1].lessons[0]
    assert "data-next-recommended" in _row(home, nxt.key)


@pytest.mark.parametrize("who,role,track", PATHWAYS)
def test_reviewing_a_completed_lesson_changes_nothing(app, who, role, track):  # noqa: F811
    client = _client(app, who)
    _post(client, "/training/register", data={"role": role})
    lessons = C.lessons_for(track, role)
    first, second = lessons[0][1], lessons[1][1]
    _finish(client, first)
    # Part-way through the next lesson, and acceptance results with a retest.
    _post(client, f"/training/lessons/{second.key}/check", data={"step": 0, "done": "1"})
    trainee = TrainingTrainee.query.one()
    case = C.uat_for(track, role)[0].key
    _post(client, f"/training/uat/{case}", data={"status": "FAIL", "issue": "Synthetic issue", "notes": "first try"})
    _post(client, f"/training/uat/{case}", data={"status": "PASS", "notes": "retest"})
    db.session.expire_all()
    resume = TrainingTrainee.query.one().training_resume
    before = _record(trainee.id)
    assert before[0][first.key][3] is not None and len(before[1]) == 2

    page = _get(client, f"/training/lessons/{first.key}?step=0").get_data(as_text=True)
    assert "data-reviewing" in page and "Completed" in page and "data-complete" not in page
    assert page.count('data-tick="') == len(first.steps) and page.count(" disabled title=") == len(first.steps)
    for i in range(len(first.steps)):  # stepping through
        assert _get(client, f"/training/lessons/{first.key}?step={i}").status_code == 200
        _post(client, f"/training/lessons/{first.key}/move", data={"step": i, "action": "next"})
    # An untick (a stale page or a hand-made request) is ignored on a completed lesson.
    r = _post(client, f"/training/lessons/{first.key}/check", data={"step": 0, "done": "0"},
              headers={"X-Requested-With": "fetch"})
    assert r.status_code == 200 and r.get_json()["done"] is True and r.get_json()["ticked"] == len(first.steps)
    _post(client, f"/training/lessons/{first.key}/complete", data={"exercise_done": "1"})
    _post(client, f"/training/lessons/{first.key}/move", data={"step": 0, "action": "exit"})

    assert _record(trainee.id) == before  # same completed_at, ticks, release; UAT attempts unchanged
    assert TrainingTrainee.query.one().training_resume == resume  # Continue still goes to the lesson in progress
    home = _get(client, "/training").get_data(as_text=True)
    assert 'data-lesson-status="completed"' in _row(home, first.key)
    assert "data-next-recommended" in _row(home, second.key)
    assert f"/training/lessons/{second.key}?step=" in re.search(r'data-continue href="([^"]+)"', home).group(1)
    assert _get(client, "/training/uat").status_code == 200
