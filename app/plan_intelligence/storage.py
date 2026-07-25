"""Private filesystem storage for plan PDFs."""

from __future__ import annotations

import os
from pathlib import Path

from flask import current_app


def get_plan_upload_root() -> Path:
    root = current_app.config.get("PLAN_UPLOAD_ROOT")
    if root:
        path = Path(root)
    else:
        path = Path(current_app.instance_path) / "plan_uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_upload_dir(project_id: int) -> Path:
    path = get_plan_upload_root() / str(int(project_id))
    path.mkdir(parents=True, exist_ok=True)
    return path


def absolute_stored_path(project_id: int, stored_filename: str) -> Path:
    """Resolve a stored filename under the project upload dir (no path traversal)."""
    safe_name = os.path.basename(stored_filename)
    if (
        not safe_name
        or safe_name != stored_filename
        or "/" in stored_filename
        or "\\" in stored_filename
        or ".." in stored_filename
    ):
        raise ValueError("Invalid stored filename.")
    path = (project_upload_dir(project_id) / safe_name).resolve()
    root = get_plan_upload_root().resolve()
    if root not in path.parents:
        raise ValueError("Stored path escapes upload root.")
    return path
