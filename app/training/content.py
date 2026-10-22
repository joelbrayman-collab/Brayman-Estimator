"""Lesson and acceptance-test content for the Training & Acceptance Centre (Joel, 21 Oct 2026).

The lessons live in three modules beside this one, one per group the Centre serves: contractor.py (12 modules,
contractor owners and office staff), field_crew.py (8 modules, the Field crew on the iPhone; Joel, 22 Oct 2026)
and supplier.py (10 modules, supplier owners and PRO Desk staff).
Every step says, for someone who has never used CalibraytAI: what they are doing and why, which application
to open, where to go, which button to press, what to enter, what they should see, what to do if something
goes wrong. A step may name the office page it is about (``endpoint``); tests check that page exists, and
that every screenshot named is in app/static/training/shots, so a lesson cannot point at something
CalibraytAI does not have.

The connected example used throughout (synthetic training records only):
    Brayman Construction (training) — Ben Brayman (owner), Olivia Office (office), Kevin and Liam (field crew)
    Customer Morgan Ellis — job "Harbour Lane Pool Deck" in Merrickville, Ontario
    Supplier BMR Winchester (training) — Darcy (store), Pat at the PRO Desk; BMR sells the concrete to the
    contractor and Tomlinson Ready-Mix supplies it to BMR (upstream, not a party in CalibraytAI)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.models.training import (
    PATHWAY_CONTRACTOR,
    PATHWAY_FIELD_CREW,
    PATHWAY_SUPPLIER,
    ROLE_FIELD,
    ROLE_OFFICE,
    ROLE_OWNER,
    ROLE_PRO_DESK,
    ROLE_SUPPLIER_ADMIN,
    ROLE_SUPPLIER_OWNER,
)

APP_OFFICE = "CalibraytAI on your computer (the office)"
APP_FIELD = "CalibraytAI Field on your iPhone"
APP_SUPPLIER = "CalibraytAI Supplier Hub on your computer"
APP_PRO_DESK = "CalibraytAI PRO Desk at the store counter"
APP_CUSTOMER = "The customer's link (email or text) on their phone or computer"
APP_QUICKBOOKS = "QuickBooks Online in your web browser"
APP_PHONE_CALENDAR = "Your phone's or computer's own calendar (Apple, Google or Outlook)"
APP_EMAIL = "Your email"
APP_TRAINING_PHONE = "The Training Centre in Safari on your iPhone"
APPS = (APP_OFFICE, APP_FIELD, APP_SUPPLIER, APP_PRO_DESK, APP_CUSTOMER, APP_QUICKBOOKS, APP_PHONE_CALENDAR,
        APP_EMAIL, APP_TRAINING_PHONE)

ALL_CONTRACTOR = (ROLE_OWNER, ROLE_OFFICE, ROLE_FIELD)
OFFICE_ROLES = (ROLE_OWNER, ROLE_OFFICE)
ALL_SUPPLIER = (ROLE_SUPPLIER_OWNER, ROLE_SUPPLIER_ADMIN, ROLE_PRO_DESK)
SUPPLIER_DESK = (ROLE_SUPPLIER_OWNER, ROLE_SUPPLIER_ADMIN)


@dataclass(frozen=True)
class Step:
    title: str          # short: "Open People & Access"
    app: str            # one of APPS
    where: str          # menu path or screen: "Company → People & Access"
    do: str             # the button or action: "Press Add a person"
    expect: str         # what they should see
    if_wrong: str       # what to do if it did not work
    enter: str = ""     # what to type, if anything
    why: str = ""       # why this step matters, when not obvious from the lesson
    shot: str = ""      # screenshot file in app/static/training/shots (desktop or phone)
    endpoint: str = ""  # the office page this step is about (checked to exist)


@dataclass(frozen=True)
class Lesson:
    key: str
    title: str
    what: str           # what the trainee will do in this lesson
    why: str            # why it matters to the business
    steps: Tuple[Step, ...]
    exercise: str       # the practice task on the training site, with the connected example
    roles: Tuple[str, ...] = ()  # empty = every role of the module


@dataclass(frozen=True)
class Module:
    key: str
    pathway: str
    number: int
    title: str
    summary: str
    roles: Tuple[str, ...]
    lessons: Tuple[Lesson, ...]


@dataclass(frozen=True)
class UatCase:
    key: str
    pathway: str
    module_key: str
    title: str
    start: str          # exact starting location
    action: str         # what to do
    expected: str       # the result that means PASS
    roles: Tuple[str, ...]


def _load() -> Tuple[Tuple[Module, ...], Tuple[UatCase, ...]]:
    from app.training import contractor, field_crew, supplier
    from app.training.useful_calculators_lesson import attach  # Useful Calculators lesson in Field module 1

    return attach(contractor.MODULES + field_crew.MODULES + supplier.MODULES,
                  contractor.UAT_CASES + field_crew.UAT_CASES + supplier.UAT_CASES)


_CACHE: Dict[str, object] = {}


def modules() -> Tuple[Module, ...]:
    if "modules" not in _CACHE:
        _CACHE["modules"], _CACHE["uat"] = _load()
    return _CACHE["modules"]  # type: ignore[return-value]


def uat_cases() -> Tuple[UatCase, ...]:
    modules()
    return _CACHE["uat"]  # type: ignore[return-value]


def track(pathway: str, role: str) -> str:
    """The lessons a trainee follows. A contractor trainee with role FIELD (the crew) follows the Field Crew
    pathway; everyone else follows their stored pathway (Joel, 22 Oct 2026)."""
    if pathway == PATHWAY_CONTRACTOR and role == ROLE_FIELD:
        return PATHWAY_FIELD_CREW
    return pathway


PATHWAY_TITLES = {PATHWAY_CONTRACTOR: "Contractor training", PATHWAY_FIELD_CREW: "Field Crew training",
                  PATHWAY_SUPPLIER: "Supplier training"}


def lesson_roles(module: Module, lesson: Lesson) -> Tuple[str, ...]:
    return lesson.roles or module.roles


def modules_for(pathway: str, role: str) -> List[Module]:
    """The trainee's modules, each with only the lessons for their role (a field worker never gets the
    office or financial lessons)."""
    out = []
    for module in modules():
        if module.pathway != pathway or role not in module.roles:
            continue
        lessons = tuple(lesson for lesson in module.lessons if role in lesson_roles(module, lesson))
        if lessons:
            out.append(Module(module.key, module.pathway, module.number, module.title, module.summary, module.roles,
                              lessons))
    return out


def lessons_for(pathway: str, role: str) -> List[Tuple[Module, Lesson]]:
    return [(m, lesson) for m in modules_for(pathway, role) for lesson in m.lessons]


def find_lesson(key: str) -> Optional[Tuple[Module, Lesson]]:
    for module in modules():
        for lesson in module.lessons:
            if lesson.key == key:
                return module, lesson
    return None


def uat_for(pathway: str, role: str) -> List[UatCase]:
    return [c for c in uat_cases() if c.pathway == pathway and role in c.roles]


def find_uat(key: str) -> Optional[UatCase]:
    return next((c for c in uat_cases() if c.key == key), None)


__all__ = [
    "APPS", "APP_OFFICE", "APP_FIELD", "APP_SUPPLIER", "APP_PRO_DESK", "APP_CUSTOMER", "APP_QUICKBOOKS",
    "APP_PHONE_CALENDAR", "APP_EMAIL", "APP_TRAINING_PHONE", "ALL_CONTRACTOR", "OFFICE_ROLES", "ALL_SUPPLIER", "SUPPLIER_DESK",
    "Step", "Lesson", "Module", "UatCase", "modules", "uat_cases", "modules_for", "lessons_for", "find_lesson",
    "uat_for", "find_uat", "lesson_roles", "PATHWAY_CONTRACTOR", "PATHWAY_SUPPLIER", "PATHWAY_FIELD_CREW", "track",
    "PATHWAY_TITLES",
]
_ = field  # dataclasses.field kept for content modules that need defaults
