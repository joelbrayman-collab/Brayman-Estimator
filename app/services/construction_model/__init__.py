"""Construction Model.

Slice 1 assesses the model and refuses an incomplete one.
Slice 2 projects plan, front elevation, and side elevation from that model.
Slice 3 composes those projections on one governed 11×17 sheet.
Slice 4 reads stair, section, detail, and schedule views from that same model.
Slice 6 stores a known coordinate without inventing the missing ones, and a view that does not fit moves to another sheet.
Slice 7 places paper-space callouts and dimension chains, and refuses a required view that cannot be placed.
Slice 8 stores deck components, including a member that is only partly known.
Slice 9 draws a complete generic deck from that same model, one filtered view per sheet.
Slice 10 draws a supplied rectangular profile, including a sloped member, and groups construction schedules from that same model.
This package does not read or write a project, a plan record, or an estimate.
Plan Generation stays a separate contract.
"""

from app.services.construction_model.completeness import (
    ENGINE_VERSION,
    assess_construction_model,
)
from app.services.construction_model.model import (
    DOCUMENT_STATUS_ISSUED_FOR_PERMIT,
    DOCUMENT_STATUS_PRELIMINARY,
    SOURCE_GOVERNED_CALCULATION,
    SOURCE_INSTANCE_CONFIGURATION,
    SOURCE_PROJECT_INPUT,
    SOURCE_SOURCE_DOCUMENT,
    STRUCTURE_CLASS_DECK,
    element_store,
)
from app.services.construction_model.projection import (
    PROJECTION_VERSION,
    VIEW_FRONT_ELEVATION,
    VIEW_PLAN,
    VIEW_SIDE_ELEVATION,
    project_construction_view,
    project_model_views,
)
from app.services.construction_model.sheet import (
    compose_construction_sheet,
    compose_construction_wave,
)
from app.services.construction_model.views import project_construction_wave

__all__ = [
    "DOCUMENT_STATUS_ISSUED_FOR_PERMIT",
    "DOCUMENT_STATUS_PRELIMINARY",
    "ENGINE_VERSION",
    "PROJECTION_VERSION",
    "SOURCE_GOVERNED_CALCULATION",
    "SOURCE_INSTANCE_CONFIGURATION",
    "SOURCE_PROJECT_INPUT",
    "SOURCE_SOURCE_DOCUMENT",
    "STRUCTURE_CLASS_DECK",
    "VIEW_FRONT_ELEVATION",
    "VIEW_PLAN",
    "VIEW_SIDE_ELEVATION",
    "assess_construction_model",
    "compose_construction_sheet",
    "compose_construction_wave",
    "element_store",
    "project_construction_view",
    "project_construction_wave",
    "project_model_views",
]
