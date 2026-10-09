"""Offer one stored member group from the current project model.

The estimate page calls this service. The existing calculation review
and the existing confirmation stay where they are.
"""

from __future__ import annotations

import copy

from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.services.calculation_estimate_mapping import CalculationEstimateMappingError
from app.services.construction_model.views import read_stored_member_quantities
from app.services.deck_framing_handoff import (
    StoredMemberCountError,
    offer_stored_member_count,
    stored_member_count_result_id,
    stored_member_group,
)
from app.services.project_construction_model import (
    ProjectConstructionModelError,
    load_current_revision,
    load_revision,
)


def groups_on_project(*, organization_id, project_id):
    """Return the current revision and its stored groups, or none."""
    try:
        revision = load_current_revision(
            organization_id=organization_id,
            project_id=project_id,
        )
    except ProjectConstructionModelError:
        return None, ()
    if revision is None:
        return None, ()
    groups = read_stored_member_quantities(copy.deepcopy(revision.content_json))
    return revision, groups


def offer_project_member_count(
    *,
    organization_id,
    project_id,
    estimate_version_id,
    revision_id,
    member_ids,
    actor,
):
    """Return the review intake id, or an error message. Does not add a line."""
    try:
        revision = load_revision(
            organization_id=organization_id,
            project_id=project_id,
            revision_id=revision_id,
        )
        working = copy.deepcopy(revision.content_json)
        group = stored_member_group(working, member_ids)
        result_id = stored_member_count_result_id(group, revision_id=revision.id)
        intake = offer_stored_member_count(
            organization_id=organization_id,
            estimate_version_id=estimate_version_id,
            model=copy.deepcopy(revision.content_json),
            member_ids=member_ids,
            actor=actor,
            construction_model_revision_id=revision.id,
        )
    except CalculationEstimateMappingError as exc:
        if "already on this estimate" in str(exc):
            existing = CalculationResultIntake.query.filter_by(
                organization_id=organization_id,
                estimate_version_id=estimate_version_id,
                result_id=result_id,
            ).first()
            if existing is not None:
                return existing.id, None
        return None, str(exc)
    except (StoredMemberCountError, ProjectConstructionModelError) as exc:
        return None, str(exc)
    return intake.id, None
