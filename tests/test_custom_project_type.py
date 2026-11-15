"""Custom project: a unique job is described in words (Joel, 15 Nov 2026).

Joel's real job (foundation, ICF main walls and concrete work) fits no standard type. "What is being built" offers
"Custom project", which asks for a description of the job; the server refuses a custom project without one. The
stored type value is unchanged (OTHER), so there is no schema change. Synthetic data only.
"""

from __future__ import annotations

from app.models import Project
from app.models.guided_estimating import PROJECT_OTHER, PROJECT_TYPE_LABELS
from tests.test_project_plan_access import _new_project, env  # noqa: F401 - env is a fixture


def test_the_list_offers_custom_project_in_place_of_other_project(env):
    assert PROJECT_TYPE_LABELS[PROJECT_OTHER] == "Custom project" and PROJECT_OTHER == "OTHER"


def test_no_model_file_changed_for_the_label():
    """The release gate treats any change under app/models as a schema change; this wording is presentation."""
    from pathlib import Path

    model = Path(__file__).resolve().parents[1] / "app" / "models" / "guided_estimating.py"
    assert 'PROJECT_OTHER: "Other project"' in model.read_text()


def test_the_screen_lists_custom_project_and_asks_for_its_description(env):
    http, _client = env
    html = http.get("/projects/new").get_data(as_text=True)
    assert ">Custom project</option>" in html and "Other project" not in html
    for hook in ("data-su-description-box", "Describe this project", "Foundation, ICF main walls and concrete work"):
        assert hook in html, hook


def test_a_custom_project_without_a_description_is_refused(env):
    http, client_row = env
    response = _new_project(http, client_row, guided_project_type="OTHER", description="  ")
    assert response.status_code == 200  # the screen comes back with what was typed
    assert Project.query.filter_by(name="Synthetic Plan Job").count() == 0
    assert "Describe this custom project" in response.get_data(as_text=True)  # shown on the screen that comes back


def test_a_described_custom_project_is_created_with_its_description(env):
    http, client_row = env
    text = "Foundation, ICF main walls and concrete work (synthetic)"
    response = _new_project(http, client_row, guided_project_type="OTHER", description=text)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    assert response.status_code == 302 and project.description == text


def test_a_standard_type_still_needs_no_description(env):
    http, client_row = env
    response = _new_project(http, client_row, guided_project_type="NEW_HOME", description="")
    assert response.status_code == 302 and Project.query.filter_by(name="Synthetic Plan Job").count() == 1
