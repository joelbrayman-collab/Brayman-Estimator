"""Where to go back to after an existing page's action, when Guided Estimating opened it (23 Oct 2026).

Only a path on this site that is a guided-estimating page (or a wizard step) is accepted, so a form cannot send anyone elsewhere.
Without one the existing page keeps its own redirect, exactly as before.
"""

from __future__ import annotations

import re
from typing import Optional

_GUIDED = re.compile(r"^/projects/\d+/guided(?:/[A-Za-z0-9_\-/]*)?$")
# Guided Workflow Wizards (24 Oct 2026): a wizard step opened the page; its action comes back to the step.
_WIZARD = re.compile(r"^/wizards/run/\d+/step/[a-z0-9_]+$")


def guided_return_path(value) -> Optional[str]:
    text = (value or "").strip()
    if not text or text.startswith("//") or "\\" in text or "://" in text:
        return None
    path = text.split("#", 1)[0].split("?", 1)[0]
    return path if (_GUIDED.match(path) or _WIZARD.match(path)) else None


def from_request() -> Optional[str]:
    from flask import request

    return guided_return_path(request.form.get("return_to") or request.args.get("return_to"))
