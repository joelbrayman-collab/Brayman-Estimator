"""Construction Model.

Slice 1 assesses the model and refuses an incomplete one.
Slice 2 projects plan, front elevation, and side elevation from that model.
This package does not compose sheets or write a PDF.
It does not read or write a project, a plan record, or an estimate.
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
    "element_store",
    "project_construction_view",
    "project_model_views",
]
