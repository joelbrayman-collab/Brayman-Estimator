"""Project Controls module — Change Orders and future controls features."""

from app.project_controls.routes import project_controls_bp

# Ensure models are registered with SQLAlchemy metadata.
from app.project_controls import models as _change_order_models  # noqa: F401

__all__ = ["project_controls_bp"]
