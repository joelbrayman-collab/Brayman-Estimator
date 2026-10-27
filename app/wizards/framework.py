"""The shared Guided Workflow Wizard framework (Joel, 24 Oct 2026).

A wizard is an ordered list of steps over the platform's existing pages and services. It is a guided interface
to the platform, not a second application:

* A step never stores business data of its own. Its progress (``StepView``) is read from the real records every
  time it is shown, so a step is complete only when the records say so ("3 of 5 materials ordered").
* A step's actions open the existing page (with a way back to the wizard), post to an existing endpoint that
  already knows how to come back (``return_to``), or call an existing service function from a small form.
  Approvals, permissions and duplicate checks are the existing ones.
* Steps can depend on the project type, the contractor role, the stage decisions or the kind of supplier
  transaction (``applies``); required steps must be satisfied before Next moves on (``required``).
* Each step carries its own contextual help (what it is, what to do, what happens next), which is also what
  Ask the Tutor answers from (app/presentation/help_content.py, surface ``wizard``).

New wizards register a ``Wizard`` in app/wizards/registry.py; nothing else in the framework changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

# What a step's records say, as shown on the step and in the progress list.
DONE = "done"          # the records satisfy the step
TODO = "todo"          # something is still to do here
WAITING = "waiting"    # waiting for someone else (a quote, a customer, a supplier)
INFO = "info"          # a review step: nothing is required, Next is always allowed
NOT_NEEDED = "na"      # the step does not apply to this record (shown greyed, never blocks)
STATES = (DONE, TODO, WAITING, INFO, NOT_NEEDED)
STATE_LABELS = {DONE: "Done", TODO: "To do", WAITING: "Waiting", INFO: "Review", NOT_NEEDED: "Not needed"}
PASSABLE = (DONE, INFO, NOT_NEEDED)


@dataclass
class Action:
    """One thing the person can do from a step. Every action is an existing page or endpoint."""

    label: str
    href: str
    primary: bool = False
    note: str = ""
    method: str = "get"            # "post": a small form to an existing endpoint
    fields: Dict[str, str] = field(default_factory=dict)  # hidden fields for a post action
    opens_page: bool = True        # a get action that leaves the wizard (shows "Return to the wizard" there)
    key: str = ""                  # stable hook for tests and training captures (data-wizard-action)


@dataclass
class Item:
    """One line of real status on a step: a stage, an order, a line, a requirement."""

    label: str
    state: str = INFO
    note: str = ""
    href: str = ""


@dataclass
class StepView:
    state: str
    headline: str                         # the real status in one line, e.g. "3 of 5 orders delivered"
    items: List[Item] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)   # what blocks Next on a required step
    actions: List[Action] = field(default_factory=list)
    form: Optional[str] = None            # a template under templates/wizards/forms/ for a small form
    form_ctx: Dict = field(default_factory=dict)
    note: str = ""


@dataclass(frozen=True)
class Step:
    key: str
    title: str
    what: str                 # contextual instructions: what this step is
    do: str                   # what to do here
    next: str                 # what happens next
    evaluate: Callable        # (ctx) -> StepView, read only
    required: bool = True
    applies: Optional[Callable] = None     # (ctx) -> bool; None = always
    handle: Optional[Callable] = None      # (ctx, form) -> str (flash text); calls existing services only
    manual: Optional[Callable] = None      # (ctx) -> (label, url) the manual page for this step
    draft: bool = False       # the step's form is answers kept in the run (saved by Save, Next and autosave)
    # The step's form is sent by Save & Continue (and Save / Save & Exit) through ``handle``, never autosaved: for
    # steps that change real records (Project Creation UX, 27 Oct 2026). ``handle`` must be safe to repeat.
    continue_form: bool = False

    def is_applicable(self, ctx) -> bool:
        return True if self.applies is None else bool(self.applies(ctx))


@dataclass(frozen=True)
class Wizard:
    key: str
    side: str                 # CONTRACTOR | SUPPLIER
    title: str
    short: str                # one line for Home / the supplier dashboard
    audience: str
    steps: Sequence[Step]
    manual_label: str
    manual_url: Callable      # (ctx_or_none) -> url of the manual workflow's entry page
    subject: Callable         # (ctx) -> str, what the run is about ("Avery New Home (synthetic)")
    finish_label: str = "Finish"
    after_finish: Optional[Callable] = None   # (ctx) -> url to go to when the person finishes
    # Compact presentation (Project Creation UX, 27 Oct 2026): "Title · Step X of Y", a thin progress bar, the step
    # list behind "View all steps", one task card, Back · Save & Exit · Save & Continue.
    compact: bool = False

    def step(self, key: str) -> Optional[Step]:
        return next((s for s in self.steps if s.key == key), None)


# ------------------------------------------------------------------------------------------------ navigation
def visible_steps(wizard: Wizard, ctx) -> List[Step]:
    return [s for s in wizard.steps if s.is_applicable(ctx)]


def evaluate_all(wizard: Wizard, ctx) -> List[dict]:
    """Every applicable step with its real status (read only)."""
    out = []
    for index, step in enumerate(visible_steps(wizard, ctx), start=1):
        view = safe_evaluate(step, ctx)
        out.append({"number": index, "step": step, "view": view, "state_label": STATE_LABELS[view.state]})
    return out


def safe_evaluate(step: Step, ctx) -> StepView:
    view = step.evaluate(ctx)
    if view.state not in STATES:
        raise ValueError(f"Step {step.key} returned an unknown state {view.state!r}")
    if not step.required and view.state == TODO:
        # An optional step never blocks; it is shown as something you may do.
        view.missing = []
    return view


def first_open_step(rows: List[dict]) -> Optional[Step]:
    """The first applicable step whose records are not yet satisfied (the next required action)."""
    for row in rows:
        if row["step"].required and row["view"].state not in PASSABLE:
            return row["step"]
    return None


def can_leave(step: Step, view: StepView) -> List[str]:
    """Why Next is refused on this step (empty: Next may go on)."""
    if not step.required or view.state in PASSABLE:
        return []
    if view.state == WAITING:
        return []  # waiting for someone else never traps the person: they may go on and come back
    return view.missing or [view.headline]


def neighbour(rows: List[dict], key: str, offset: int) -> Optional[Step]:
    keys = [r["step"].key for r in rows]
    if key not in keys:
        return rows[0]["step"] if rows else None
    index = keys.index(key) + offset
    return rows[index]["step"] if 0 <= index < len(rows) else None


def progress(rows: List[dict]) -> dict:
    counted = [r for r in rows if r["view"].state != NOT_NEEDED]
    done = sum(1 for r in counted if r["view"].state in (DONE, INFO))
    total = len(counted)
    return {"done": done, "total": total, "percent": int(round(100 * done / total)) if total else 0}


def count_headline(done: int, total: int, noun: str, verb: str) -> str:
    """'3 of 5 materials ordered' — the plain real-status line every step uses."""
    plural = noun if total == 1 else (noun[:-1] + "ies" if noun.endswith("y") and noun[-2:-1] not in "aeiou"
                                     else noun + "s")
    return f"{done} of {total} {plural} {verb}"
