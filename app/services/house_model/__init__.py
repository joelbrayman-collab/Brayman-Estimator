"""House model: one baseline, changed only by named change requests (Joel, 23 Nov 2026).

The model is data. Drawings and quantities are produced from it by programs, never by an AI. An AI may only translate
a contractor's words into a ChangeRequest from the closed vocabulary in changes.py; the program applies it, reports the
difference, and proves that every element the request did not name is byte-for-byte identical. Versions are kept.
"""
from app.services.house_model.changes import ChangeError, ChangeRequest, apply_change  # noqa: F401
from app.services.house_model.model import HouseModel, ModelError, fact, new_model  # noqa: F401
