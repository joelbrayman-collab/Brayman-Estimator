"""Plan Intelligence module — Phase A: PDF upload and storage."""

from app.plan_intelligence.routes import plan_intelligence_bp

# Register models with SQLAlchemy metadata.
from app.plan_intelligence import models as _plan_models  # noqa: F401

__all__ = ["plan_intelligence_bp"]
