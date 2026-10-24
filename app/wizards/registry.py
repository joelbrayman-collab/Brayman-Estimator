"""The wizards CalibraytAI offers. A new wizard is one more entry here (and its own module of steps)."""

from __future__ import annotations

from typing import List, Optional

from app.models.wizard import SIDE_CONTRACTOR, SIDE_SUPPLIER


def all_wizards():
    from app.wizards import estimating, manage_project, new_project, supplier_pro_desk

    return (new_project.WIZARD, estimating.WIZARD, manage_project.WIZARD, supplier_pro_desk.WIZARD)


def wizard_for(key: str):
    return next((w for w in all_wizards() if w.key == key), None)


def contractor_wizards() -> List:
    return [w for w in all_wizards() if w.side == SIDE_CONTRACTOR]


def supplier_wizards() -> List:
    return [w for w in all_wizards() if w.side == SIDE_SUPPLIER]


def require(key: str, side: str):
    wizard = wizard_for(key)
    if wizard is None or wizard.side != side:
        return None
    return wizard


_ = Optional
