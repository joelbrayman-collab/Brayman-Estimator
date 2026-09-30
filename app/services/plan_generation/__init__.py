"""Reusable Plan Generation.

PGE-1 validates a request. PGE-2 draws a dimensioned plan. PGE-3 draws a
supplied stair result. None of these steps writes a project record. Contract
V1 does not carry a stair profile.
"""

from app.services.plan_generation.render import render_dimensioned_plan, render_plan_generation
from app.services.plan_generation.validation import (
    ENGINE_VERSION,
    SUPPORTED_DRAWING_TYPES,
    validate_plan_generation_request,
)

__all__ = [
    "ENGINE_VERSION",
    "SUPPORTED_DRAWING_TYPES",
    "render_dimensioned_plan",
    "render_plan_generation",
    "validate_plan_generation_request",
]
