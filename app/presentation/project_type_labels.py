"""Wording for the project types people choose from (Joel, 15 Nov 2026).

"What is being built" offers "Custom project" for a unique job. The stored value is unchanged (``OTHER``) and the
label is presentation, so it is set here when the app is created rather than in the model file: no schema change, and
every screen that reads ``PROJECT_TYPE_LABELS`` (the setup form, the guided pages, the wizards) shows the same word.
"""

from __future__ import annotations

CUSTOM_PROJECT_LABEL = "Custom project"


def apply_project_type_labels() -> None:
    from app.models.guided_estimating import PROJECT_OTHER, PROJECT_TYPE_LABELS

    PROJECT_TYPE_LABELS[PROJECT_OTHER] = CUSTOM_PROJECT_LABEL
