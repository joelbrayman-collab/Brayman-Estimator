"""Selected-work scope (Approach B, Joel 28 Oct 2026): the contractor chooses the work; CalibraytAI estimates it.

The one authoritative scope service for an estimate, used by Project Creation, the Guided Estimating wizard, the
manual Work page, the estimating workflow, the project and estimate pages. Design:
docs/architecture/selected-work-estimating.md.

Storage is the project's existing guided-estimate record and its rows (no parallel schema):

- the scope holder is the project's one ``GuidedEstimate`` (``estimate_id`` = the estimate it governs);
- the selected-work model is marked by the append-only event ``SCOPE_MODEL`` → ``SELECTED_WORK`` (scopes made
  before 28 Oct 2026 have none and keep the legacy stage model);
- each selected work item is one top-level ``GuidedEstimateStage`` keyed by its catalogue key (``work_siding``) or
  ``custom_<name>``; mixed responsibility is the existing split into two parts (materials, installation);
- removed work keeps its row (history references it) with responsibility N/A; in this model such a row is simply
  not part of the estimate and is never shown, counted or priced.

Quantities, labour, materials, quotes, allowances, pricing and proposals stay in the estimate's own records
(``app/services/guided_estimating.py`` and the estimate services); nothing here stores a cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from app import db
from app.models.guided_estimating import (
    CONTRACTOR_ROLES,
    PROJECT_OTHER,
    PROJECT_TYPES,
    RESP_INTERNAL,
    RESP_NA,
    RESP_SUBCONTRACTED,
    ROLE_GENERAL_CONTRACTOR,
    SCOPE_DRAFT,
    SCOPE_FINALIZED,
    STATUS_COMPLETE,
    STATUS_EXCLUDED,
    STATUS_NOT_STARTED,
    GuidedEstimate,
    GuidedEstimateEvent,
    GuidedEstimateStage,
)

SCOPE_MODEL_EVENT = "SCOPE_MODEL"
SELECTED_WORK = "SELECTED_WORK"
WORK_PREFIX = "work_"
WORK_RESPONSIBILITIES = (RESP_INTERNAL, RESP_SUBCONTRACTED)
PART_MATERIALS = "materials"
PART_INSTALLATION = "installation"


class SelectedWorkError(ValueError):
    """A scope change that cannot be made; the message is for the contractor."""


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    items: Tuple[object, ...]  # StageSpec


# ---------------------------------------------------------------------------------------------- the catalogue
def _build():
    from app.services import guided_estimating as G

    def parts(tools=()):
        return (G.Part(PART_MATERIALS, "Materials", tools), G.Part(PART_INSTALLATION, "Installation", (),
                                                                     labour_part=True))

    def work(key, name, explanation, calcs=(), sub=""):
        return G.StageSpec(WORK_PREFIX + key, name, explanation, parts(calcs), tuple(calcs) + (G.LABOUR, G.MANUAL),
                           sub or f"A {name.lower()} contractor supplies and installs it.")

    categories = (
        ("exterior", "Exterior", (
            work("siding", "Siding", "Siding on the walls: the net wall area, pieces and accessories.", (G.SIDING,),
                 "A siding contractor supplies and installs the siding."),
            work("soffit_fascia", "Soffit, fascia & trim", "Soffit, fascia and exterior trim."),
            work("roofing", "Roofing", "Roof covering, underlayment, ridge cap, flashing and vents.", (G.ROOFING,),
                 "A roofing contractor supplies and installs the roof."),
            work("windows", "Windows", "Each window on the opening schedule, supplied and installed.",
                 sub="A window installer supplies and installs the windows."),
            work("exterior_doors", "Exterior doors", "Each exterior door, supplied and installed."),
            work("garage_door", "Garage door", "The overhead door, opener and installation."),
            work("deck", "Deck", "Deck framing, decking, stairs and railings.", (G.DECK_TAKEOFF,),
                 "A deck builder supplies and builds the deck."),
        )),
        ("structure", "Structure", (
            work("wall_framing", "Wall framing", "Studs, plates, headers and sheathing for the walls.",
                 (G.WALL_FRAMING, G.FRAMING_ESTIMATE, G.MEMBER_COUNTS)),
            work("floor_framing", "Floor framing", "Joists, beams, rim and subfloor.", (G.DECK_TAKEOFF,)),
            work("roof_framing", "Roof framing", "Rafters or trusses, bracing and roof sheathing."),
        )),
        ("foundation_site", "Foundation & site", (
            work("demolition", "Demolition", "Taking out what is there, and its disposal."),
            work("site_prep", "Site preparation", "Clearing, layout and temporary services."),
            work("excavation", "Excavation", "Digging, backfill and hauling away extra soil."),
            work("footings", "Footings", "Footing concrete and forming.", (G.FOOTING,)),
            work("foundation_walls", "Foundation walls", "ICF or poured foundation walls.", (G.ICF, G.CONCRETE)),
            work("concrete_slab", "Concrete slab", "Slab or pad concrete, ordered in m³ or yd³.", (G.CONCRETE,)),
            work("waterproofing", "Waterproofing & drainage", "Damp-proofing, weeping tile and drainage."),
        )),
        ("interior", "Interior", (
            work("insulation", "Insulation", "Wall, ceiling and attic insulation and the vapour barrier."),
            work("drywall", "Drywall", "Board, taping and finishing.", (G.DRYWALL,)),
            work("flooring", "Flooring", "Floor area, boxes and the room perimeter for trim.", (G.FLOORING,)),
            work("trim", "Trim & baseboard", "Interior trim, casing and baseboard."),
            work("interior_doors", "Interior doors", "Each interior door, supplied and installed."),
            work("cabinets", "Cabinets & counters", "Cabinets, counters and their installation."),
            work("painting", "Painting", "Interior or exterior painting."),
            work("stairs_railings", "Stairs & railings", "Stairs, treads, risers and railings.", (G.STAIRS,)),
        )),
        ("mechanical_electrical", "Mechanical & electrical", (
            work("electrical", "Electrical", "Wiring, panel, fixtures and the electrical permit.",
                 sub="A licensed electrician quotes the electrical work."),
            work("plumbing", "Plumbing", "Supply and drain piping, fixtures and the plumbing permit.",
                 sub="A licensed plumber quotes the plumbing."),
            work("hvac", "HVAC", "Heating, cooling, ventilation and ductwork.",
                 sub="An HVAC contractor quotes the heating and ventilation."),
        )),
        ("general", "General", (
            work("final_cleanup", "Final cleanup", "Labour, disposal and supplies to hand over a clean job."),
        )),
    )
    return tuple(Category(key, label, items) for key, label, items in categories)


_CATALOGUE = None


def catalogue() -> Tuple[Category, ...]:
    """Categories (navigation: choosing one adds nothing) and the work in each (what is actually estimated)."""
    global _CATALOGUE
    if _CATALOGUE is None:
        _CATALOGUE = _build()
    return _CATALOGUE


def work_spec(key: str):
    """The catalogue entry for a work key, or None (a category or an unknown key is never work)."""
    for category in catalogue():
        for spec in category.items:
            if spec.key == key:
                return spec
    return None


# ---------------------------------------------------------------------------------------------- the model
def is_selected_work(guided) -> bool:
    """True for scopes in the selected-work model (every scope started from 28 Oct 2026)."""
    if guided is None:
        return True  # a scope not started yet will be started in this model
    cached = getattr(guided, "_selected_work_cache", None)
    if cached is None:
        cached = guided.id is not None and db.session.query(GuidedEstimateEvent.id).filter_by(
            guided_estimate_id=guided.id, event=SCOPE_MODEL_EVENT, to_value=SELECTED_WORK).first() is not None
        guided._selected_work_cache = cached
    return cached


def mark_selected_work(guided, *, actor, user_id=None, detail="Scope is the selected work."):
    from app.services import guided_estimating as G

    G._event(guided, SCOPE_MODEL_EVENT, actor=actor, to_value=SELECTED_WORK, detail=detail, user_id=user_id)
    guided._selected_work_cache = True


def _active(row) -> bool:
    return row.responsibility != RESP_NA


def work_items(guided) -> List[GuidedEstimateStage]:
    """The selected work, in the order it was added. Removed work is not part of the estimate."""
    if guided is None:
        return []
    return [r for r in guided.top_stages if _active(r)]


def ensure_scope(organization_id: str, project_id: int, *, actor: str, user_id=None, estimate_id=None,
                 project_type: str = "", contractor_role: str = "") -> GuidedEstimate:
    """The project's scope, started on first use in the selected-work model with no work in it."""
    from app.services import guided_estimating as G

    guided = G.get_guided(organization_id, project_id)
    if guided is None:
        guided = G.start_guided_estimate(
            organization_id=organization_id, project_id=project_id,
            project_type=project_type if project_type in PROJECT_TYPES else _project_type_hint(organization_id, project_id),
            contractor_role=contractor_role if contractor_role in CONTRACTOR_ROLES else ROLE_GENERAL_CONTRACTOR,
            actor=actor, user_id=user_id)
    if estimate_id and guided.estimate_id is None:
        from app.models import Estimate

        estimate = Estimate.query.filter_by(id=estimate_id, project_id=project_id).first()
        if estimate is not None:
            guided.estimate_id = estimate.id
            G._event(guided, "ESTIMATE_LINKED", actor=G._actor(actor), detail=estimate.estimate_number,
                     user_id=user_id)
            db.session.commit()
    return guided


def _project_type_hint(organization_id, project_id) -> str:
    """What is being built, for the scope holder (a fact about the job; it adds no work)."""
    hint = {"New Build": "NEW_HOME", "Addition": "ADDITION_RENOVATION", "Renovation": "ADDITION_RENOVATION",
            "Garage": "GARAGE_OUTBUILDING", "Foundation": "FOUNDATION_ONLY"}
    try:
        from app.models.project_commercial_context import ProjectCommercialContext

        ctx = ProjectCommercialContext.query.filter_by(project_id=project_id).first()
        return hint.get(getattr(ctx, "project_type", "") or "", PROJECT_OTHER)
    except Exception:  # noqa: BLE001 - the hint is optional
        return PROJECT_OTHER


def _custom_key(name: str) -> str:
    return "custom_" + "".join(ch if ch.isalnum() else "_" for ch in name.lower())[:60]


def _add_parts(guided, stage, spec):
    from app.services import guided_estimating as G

    now = G._now()
    names = [(p.key, p.name) for p in spec.parts] if spec is not None else [
        (PART_MATERIALS, "Materials"), (PART_INSTALLATION, "Installation")]
    for index, (key, name) in enumerate(names, start=1):
        db.session.add(GuidedEstimateStage(
            organization_id=guided.organization_id, guided_estimate_id=guided.id, parent_stage_id=stage.id,
            stage_key=f"{stage.stage_key}.{key}", display_name=name, sort_order=stage.sort_order * 100 + index,
            is_custom=stage.is_custom, is_split=False, responsibility=None, status=STATUS_NOT_STARTED,
            created_at=now, updated_at=now))
    db.session.flush()
    db.session.expire(stage, ["children_rows"])
    db.session.expire(guided, ["stages"])


def add_work(guided, *, keys: Sequence[str] = (), custom_name: str = "", actor: str, user_id=None,
             defer_estimate: bool = False) -> List[GuidedEstimateStage]:
    """Add catalogue work and/or one named piece of work. Internal by default (one choice changes it).

    ``defer_estimate``: project scope confirmed before any estimate (project setup, 30 Oct 2026) does not start an
    estimate; the estimate is made when the person creates it, and it then adopts this scope."""
    from app.services import guided_estimating as G

    name = G._actor(actor)
    _require_model(guided)
    G._require_not_committed(guided)
    wanted = []
    for key in keys:
        spec = work_spec(key)
        if spec is None:
            raise SelectedWorkError("Choose the work from the list.")
        if spec not in wanted:
            wanted.append(spec)
    order_of = {spec.key: i for i, spec in enumerate(s for c in catalogue() for s in c.items)}
    wanted.sort(key=lambda spec: order_of[spec.key])
    label = " ".join((custom_name or "").split())[:120]
    if not wanted and not label:
        raise SelectedWorkError("Choose the work, or name it.")
    by_key = {s.stage_key: s for s in guided.top_stages}
    added = []
    order = max([s.sort_order for s in guided.top_stages] or [0])
    now = G._now()
    for spec in wanted:
        row = by_key.get(spec.key)
        if row is not None and _active(row):
            continue  # already in the estimate
        if row is None:
            order += 10
            row = GuidedEstimateStage(organization_id=guided.organization_id, guided_estimate_id=guided.id,
                                      stage_key=spec.key, display_name=spec.name, explanation=spec.explanation,
                                      sort_order=order, is_custom=False, is_split=False, responsibility=None,
                                      status=STATUS_NOT_STARTED, created_at=now, updated_at=now)
            db.session.add(row)
            db.session.flush()
        db.session.expire(guided, ["stages"])
        _bring_in(guided, row, actor=name, user_id=user_id)
        added.append(row)
    if label:
        key = _custom_key(label)
        row = by_key.get(key)
        if row is None or not _active(row):
            if row is None:
                order += 10
                row = GuidedEstimateStage(organization_id=guided.organization_id, guided_estimate_id=guided.id,
                                          stage_key=key, display_name=label, explanation="Named by the contractor.",
                                          sort_order=order, is_custom=True, is_split=False, responsibility=None,
                                          status=STATUS_NOT_STARTED, created_at=now, updated_at=now)
                db.session.add(row)
                db.session.flush()
            db.session.expire(guided, ["stages"])
            _bring_in(guided, row, actor=name, user_id=user_id)
            added.append(row)
    _settle(guided, actor=name, user_id=user_id, create_estimate=not defer_estimate)
    db.session.commit()
    return added


def _bring_in(guided, row, *, actor, user_id=None):
    from app.services import guided_estimating as G

    row.responsibility = RESP_INTERNAL
    row.decided_by = actor
    row.decided_at = G._now()
    row.na_reason = None
    row.status = STATUS_NOT_STARTED
    row.is_split = False
    for child in row.children:
        child.responsibility = None
    row.updated_at = G._now()
    G._event(guided, "WORK_ADDED", actor=actor, stage=row, to_value=RESP_INTERNAL, detail=row.display_name,
             user_id=user_id)


def _settle(guided, *, actor, user_id=None, create_estimate: bool = True):
    """The scope is final whenever it has work and every work item is decided; then the estimate has a section for
    each work item (or part). With no work it goes back to a draft."""
    from app.services import guided_estimating as G

    items = work_items(guided)
    if items and not G.undecided(guided):
        if guided.scope_status != SCOPE_FINALIZED:
            guided.scope_status = SCOPE_FINALIZED
            guided.scope_finalized_at = G._now()
            guided.scope_finalized_by = actor
        db.session.flush()
        if create_estimate or guided.estimate is not None:
            G.ensure_estimate(guided, actor=actor, user_id=user_id)
    elif not items and guided.scope_status != SCOPE_DRAFT:
        guided.scope_status = SCOPE_DRAFT
    guided.updated_at = G._now()


def _require_model(guided):
    if not is_selected_work(guided):
        raise SelectedWorkError("This estimate uses the earlier stage list. Switch it to selected work first.")


def get_row(guided, row_id) -> GuidedEstimateStage:
    row = GuidedEstimateStage.query.filter_by(id=row_id, guided_estimate_id=guided.id,
                                              organization_id=guided.organization_id).first()
    if row is None or (row.parent is None and not _active(row)) or (row.parent is not None and not _active(row.parent)):
        raise SelectedWorkError("That work is not in this estimate.")
    return row


def set_responsibility(guided, row, value, *, actor, user_id=None, defer_estimate: bool = False):
    """Who does selected work (or one of its parts): Internal or Subcontracted. Never asked for other work."""
    from app.services import guided_estimating as G

    name = G._actor(actor)
    _require_model(guided)
    value = (value or "").strip().upper()
    if value not in WORK_RESPONSIBILITIES:
        raise SelectedWorkError("Choose Internal or Subcontracted.")
    if row.parent is None and row.is_split:
        raise SelectedWorkError("This work is decided by materials and installation.")
    if row.parent is not None and not row.parent.is_split:
        raise SelectedWorkError("Split the work into materials and installation first.")
    try:
        G.change_responsibility(guided, row, value, actor=name, user_id=user_id)
    except G.GuidedEstimatingError as exc:
        raise SelectedWorkError(str(exc)) from exc
    _settle(guided, actor=name, user_id=user_id, create_estimate=not defer_estimate)
    db.session.commit()


def split_work(guided, row, split: bool, *, actor, user_id=None):
    """Mixed responsibility (progressive): decide materials and installation separately, or the work as a whole."""
    from app.services import guided_estimating as G

    name = G._actor(actor)
    _require_model(guided)
    G._require_not_committed(guided)
    if row.parent is not None:
        raise SelectedWorkError("Choose the work, not a part of it.")
    if bool(split) == row.is_split:
        return
    if split:
        if G._stage_has_lines(row):
            raise SelectedWorkError(f"{row.display_name} already has estimate lines. Split it before adding lines, "
                                    "or keep it whole.")
        if not row.children:
            _add_parts(guided, row, work_spec(row.stage_key))
        whole = row.responsibility if row.responsibility in WORK_RESPONSIBILITIES else RESP_INTERNAL
        row.is_split = True
        row.responsibility = None
        for child in row.children:
            child.responsibility = whole
            child.decided_by = name
            child.decided_at = G._now()
            child.status = STATUS_NOT_STARTED
    else:
        if any(G._stage_has_lines(c) for c in row.children):
            raise SelectedWorkError(f"The materials or installation of {row.display_name} already have estimate "
                                    "lines; it stays split.")
        first = next((c.responsibility for c in row.children if c.responsibility in WORK_RESPONSIBILITIES),
                     RESP_INTERNAL)
        row.is_split = False
        row.responsibility = first
        row.decided_by = name
        row.decided_at = G._now()
        for child in row.children:
            child.responsibility = None
    # The estimate follows: one section for the work as a whole, or one for each of its parts (all still empty).
    version = G.editable_version(guided)
    if version is not None:
        for target in ([row] if split else list(row.children)):
            section = G.section_for(target, version)
            if section is not None and not section.line_items:
                db.session.delete(section)
        db.session.flush()
        db.session.expire(version, ["sections"])
    G._event(guided, "SPLIT" if split else "UNSPLIT", actor=name, stage=row, user_id=user_id)
    _settle(guided, actor=name, user_id=user_id)
    db.session.commit()


# ---------------------------------------------------------------------------------------------- removing work
def removal_check(row) -> List[str]:
    """What estimate data the work holds. Work with any of it is not removed (nothing is silently destroyed)."""
    from app.services import guided_estimating as G

    rows = [row] + list(row.children)
    found = []
    lines = sum(len(G.stage_lines(r)) for r in rows)
    if lines:
        found.append(f"{lines} estimate line{'s' if lines != 1 else ''}")
    calcs = sum(len(G._stage_calculations(r)) for r in rows)
    if calcs:
        found.append(f"{calcs} calculator result{'s' if calcs != 1 else ''}")
    if any(r.quote_requested_at for r in rows):
        found.append("a requested quotation")
    if any(r.allowance_amount is not None for r in rows):
        found.append("an approved allowance")
    if any(r.zero_cost_reason for r in rows):
        found.append("a no-cost decision")
    if any(r.status == STATUS_COMPLETE or r.completion_basis for r in rows):
        found.append("a completed status")
    if any((r.scope_description or "").strip() for r in rows):
        found.append("notes")
    return found


def remove_work(guided, row, *, actor, confirmed: bool, user_id=None, defer_estimate: bool = False):
    """Remove selected work that holds no estimate data, after the person confirms. The row and its history stay."""
    from app.services import guided_estimating as G

    name = G._actor(actor)
    _require_model(guided)
    G._require_not_committed(guided)
    if row.parent is not None:
        raise SelectedWorkError("Remove the whole work item, not a part of it.")
    held = removal_check(row)
    if held:
        raise SelectedWorkError(f"{row.display_name} has {', '.join(held)}. Remove those from the estimate first; "
                                "nothing is deleted without you.")
    if not confirmed:
        raise SelectedWorkError(f"Confirm that {row.display_name} is not part of this estimate.")
    version = G.editable_version(guided)
    for target in [row] + list(row.children):
        section = G.section_for(target, version) if version is not None else None
        if section is not None and not section.line_items:
            db.session.delete(section)
    for child in row.children:
        child.responsibility = None
    row.is_split = False
    row.responsibility = RESP_NA
    row.status = STATUS_EXCLUDED
    row.na_reason = None
    row.updated_at = G._now()
    G._event(guided, "WORK_REMOVED", actor=name, stage=row, detail=row.display_name, user_id=user_id)
    _settle(guided, actor=name, user_id=user_id, create_estimate=not defer_estimate)
    db.session.commit()


# ---------------------------------------------------------------------------------------------- progress
def progress(guided) -> Tuple[int, int]:
    """(complete, total) over the selected work: one item = 1 of 1. A split item counts once."""
    from app.services import guided_estimating as G

    items = work_items(guided)
    if not items:
        return 0, 0
    version = G.current_version(guided)
    done = sum(1 for r in items if G.effective_status(r, version) == STATUS_COMPLETE)
    return done, len(items)


# ---------------------------------------------------------------------------------------------- legacy drafts
def convert_legacy_draft(guided, *, actor, confirmed: bool, user_id=None):
    """Person-triggered only: a legacy draft keeps its Internal and Subcontracted stages as its work; stages that
    were N/A or never decided leave the estimate. Every earlier decision stays in the history."""
    from app.services import guided_estimating as G

    name = G._actor(actor)
    if is_selected_work(guided):
        return
    G._require_not_committed(guided)
    if not confirmed:
        raise SelectedWorkError("Confirm the switch to selected work.")
    for stage in guided.top_stages:
        if stage.is_split:
            decided = [c for c in stage.children if c.responsibility in WORK_RESPONSIBILITIES]
            if decided:
                for child in stage.children:
                    if child.responsibility not in WORK_RESPONSIBILITIES:
                        child.responsibility = decided[0].responsibility
                continue
            stage.is_split = False
            for child in stage.children:
                child.responsibility = None
            stage.responsibility = None
        if stage.responsibility not in WORK_RESPONSIBILITIES:
            if G._stage_has_lines(stage):
                raise SelectedWorkError(f"{stage.display_name} has estimate lines but no responsibility. Decide it "
                                        "first.")
            previous = stage.responsibility
            stage.responsibility = RESP_NA
            stage.status = STATUS_EXCLUDED
            G._event(guided, "WORK_REMOVED", actor=name, stage=stage, from_value=previous,
                     detail="Not selected when the draft was switched to selected work.", user_id=user_id)
    mark_selected_work(guided, actor=name, user_id=user_id, detail="Switched from the earlier stage list by a person.")
    _settle(guided, actor=name, user_id=user_id)
    db.session.commit()


# ---------------------------------------------------------------------------------------------- the estimate page
def estimate_panel(estimate) -> Optional[dict]:
    """What the estimate page shows about its scope: the selected work and one Add work, or None when this
    estimate is not the one the project's scope governs (a second estimate, or a legacy stage-model scope)."""
    from app.services import guided_estimating as G

    if estimate is None or estimate.project_id is None:
        return None
    guided = G.get_guided(estimate.organization_id, estimate.project_id)
    if guided is not None and guided.estimate_id not in (None, estimate.id):
        return None
    if guided is not None and not is_selected_work(guided):
        return {"legacy": True, "guided": guided, "items": [], "progress": (0, 0)}
    items = work_items(guided)
    return {"legacy": False, "guided": guided, "items": items, "progress": progress(guided) if items else (0, 0)}
