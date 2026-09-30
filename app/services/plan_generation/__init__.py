"""Reusable Plan Generation request validation (PGE-1).

This package does not render a sheet and does not write project records.
Member coordinates live on the drawing request. Contract V1 does not carry them.
"""

from app.services.plan_generation.validation import (
    ENGINE_VERSION,
    SUPPORTED_DRAWING_TYPES,
    validate_plan_generation_request,
)

__all__ = [
    "ENGINE_VERSION",
    "SUPPORTED_DRAWING_TYPES",
    "validate_plan_generation_request",
]
