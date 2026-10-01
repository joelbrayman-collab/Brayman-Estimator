"""Construction Model. Slice 1: the model of record and completeness refusal.

This package does not project views, compose sheets, or write a PDF.
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

__all__ = [
    "DOCUMENT_STATUS_ISSUED_FOR_PERMIT",
    "DOCUMENT_STATUS_PRELIMINARY",
    "ENGINE_VERSION",
    "SOURCE_GOVERNED_CALCULATION",
    "SOURCE_INSTANCE_CONFIGURATION",
    "SOURCE_PROJECT_INPUT",
    "SOURCE_SOURCE_DOCUMENT",
    "STRUCTURE_CLASS_DECK",
    "assess_construction_model",
    "element_store",
]
