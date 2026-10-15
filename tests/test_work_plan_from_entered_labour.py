"""V1 workflow (15 Oct 2026): project work is built from the contractor's entered labour hours
when the estimate has no labour-engine snapshots, once the estimate is locked and its proposal is
issued or accepted."""

from decimal import Decimal

import pytest

from app import db
from app.models.work_structure import ProjectWorkActivity, ProjectWorkElement
from app.services import estimate_labour_hours as labour
from app.services.estimates import lock_version
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from app.services.proposals import create_proposal, create_proposal_template, update_proposal_status
from app.services.work_structure import WorkStructureError, eligible_seed_versions, seed_project_work_structure
from tests.proposal_issue_support import approve_for_issue
from tests.test_estimate_labour_hours import _version_with_items, app  # noqa: F401


def _with_hours():
    estimate, version, footing, framing = _version_with_items()
    labour.save_hours(version, organization_id=DEFAULT_ORGANIZATION_ID,
                      hours_by_item={footing.id: "6", framing.id: "10.5"}, actor="Joel Brayman")
    return estimate, version


def _accept(estimate, version):
    approve_for_issue(version)
    template = create_proposal_template(name="WP template", is_active=True, default_intro_text="i",
                                        default_payment_terms="p")
    proposal = create_proposal(estimate=estimate, version=version, template=template)
    update_proposal_status(proposal, "Accepted")
    return proposal


def test_unlocked_or_uncommitted_estimates_do_not_build_project_work(app):
    estimate, version = _with_hours()
    project = estimate.project
    assert eligible_seed_versions(project) == []
    lock_version(version)
    assert eligible_seed_versions(project) == []  # locked, but nothing issued or accepted
    with pytest.raises(WorkStructureError, match="locked issued or accepted"):
        seed_project_work_structure(project_id=project.id, estimate_version_id=version.id)


def test_entered_labour_hours_become_the_project_work(app):
    estimate, version = _with_hours()
    _accept(estimate, version)
    lock_version(version)
    assert eligible_seed_versions(estimate.project) == [version]
    seed_project_work_structure(project_id=estimate.project.id, estimate_version_id=version.id, seeded_by="Joel")
    element = ProjectWorkElement.query.filter_by(project_id=estimate.project.id).one()
    assert element.display_name == "Work" and element.estimated_hours == Decimal("16.5")
    activities = ProjectWorkActivity.query.filter_by(project_work_element_id=element.id).order_by(ProjectWorkActivity.sort_order).all()
    assert [(a.display_name, a.estimated_hours, a.unit) for a in activities] == [
        ("Labour — Footing concrete", Decimal("6"), "hr"), ("Labour — Wall framing", Decimal("10.5"), "hr")]
    assert all(a.source_estimate_version_id == version.id and a.labour_task_id is None for a in activities)
    with pytest.raises(WorkStructureError, match="already built"):
        seed_project_work_structure(project_id=estimate.project.id, estimate_version_id=version.id)
