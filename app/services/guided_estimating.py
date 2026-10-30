"""Guided Project Estimating (Joel, 23 Oct 2026): orchestration over the existing estimating services.

The contractor says what is being built and who does each part; this module turns that into the project's
estimating sequence and brings the existing tools to each stage. It owns no cost, quantity, price or quote:

* Each included stage (or subcomponent) is one ordinary EstimateSection on the project's estimate, named after
  the stage. Its lines are added only by the existing services: the calculation review (Contract V1 intake →
  a person confirms each quantity), estimate labour hours (LAB- lines at the approved company rate), the
  subcontract quote evidence with Pricing Decision A (a selected quote only SUGGESTS a cost; "Use this cost on
  the line" applies it, with undo and who/when), and governed manual lines (estimate_builder.add_manual_line).
* Who supplies and builds each line is the existing scope-delivery routing, confirmed by a person.
* Costing approval, pricing (true gross margin) and the proposal are the existing services, unchanged.
* Because the stage sections are the estimate's sections, the existing work-structure seed turns them into the
  project's work items once the estimate is issued: there is no second work structure.

A stage is Complete only when its costs are confirmed, an allowance was explicitly approved, or a no-cost
decision was authorized. Nothing defaults to N/A; undecided stages are allowed only while the scope is a draft.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional, Tuple

from app import db
from app.models.estimate import Estimate, EstimateLineItem, EstimateSection, EstimateVersion
from app.models.guided_estimating import (
    BASIS_APPROVED_ALLOWANCE,
    BASIS_AUTHORIZED_ZERO_COST,
    BASIS_CONFIRMED_COSTS,
    BASIS_LABELS,
    CONTRACTOR_ROLES,
    PROJECT_ADDITION,
    PROJECT_FOUNDATION,
    PROJECT_GARAGE,
    PROJECT_NEW_HOME,
    PROJECT_OTHER,
    PROJECT_TYPES,
    RESP_INTERNAL,
    RESP_NA,
    RESP_SUBCONTRACTED,
    RESPONSIBILITIES,
    RESPONSIBILITY_LABELS,
    ROLE_SUBCONTRACTOR,
    SCOPE_DRAFT,
    SCOPE_FINALIZED,
    STATUS_COMPLETE,
    STATUS_EXCLUDED,
    STATUS_IN_PROGRESS,
    STATUS_LABELS,
    STATUS_NEEDS_REVIEW,
    STATUS_NOT_STARTED,
    STATUS_WAITING_FOR_QUOTE,
    GuidedEstimate,
    GuidedEstimateEvent,
    GuidedEstimateStage,
)
from app.models.project import Project

_REJECTED_ACTORS = {"", "system", "ai", "automatic", "calibraytai", "calibrytai"}


class GuidedEstimatingError(ValueError):
    """A guided-estimating action that cannot be done; the message is for the contractor."""


# ---------------------------------------------------------------------------------------------- the stage library
@dataclass(frozen=True)
class Tool:
    kind: str       # calculator | estimate_page | project_page | labour | manual | quote | quote_sheet | compare
    target: str     # calculator key or endpoint
    label: str
    note: str = ""


@dataclass(frozen=True)
class Part:
    key: str
    name: str
    tools: Tuple[Tool, ...] = ()
    labour_part: bool = False  # the installation labour of the stage (materials vs installation, mixed work)


@dataclass(frozen=True)
class StageSpec:
    key: str
    name: str
    explanation: str
    parts: Tuple[Part, ...]
    internal_tools: Tuple[Tool, ...]
    subcontract_note: str
    gc_only: bool = False


LABOUR = Tool("labour", "estimate_labour.hours", "Labour hours", "Hours × the approved company labour rate.")
MANUAL = Tool("manual", "", "Enter a cost line", "For costs no calculator covers: labour, equipment, delivery, "
              "disposal, supplies or other direct costs.")
QUOTE = Tool("quote", "", "Record the subcontractor's quote")
QUOTE_SHEET = Tool("quote_sheet", "scope_delivery.labour_quote_request", "Printable quote request sheet",
                   "The stage's quantities for the subcontractor to price.")
COMPARE = Tool("compare", "supplier_office.quote_comparison", "Compare supplier quotes")


def _calc(key, label, note=""):
    return Tool("calculator", key, label, note)


FOOTING = _calc("footing", "Footing calculator", "Concrete for the footings.")
CONCRETE = _calc("concrete", "Concrete slab calculator", "Slab or pad concrete, ordered in m³ or yd³.")
ICF = _calc("wall_form", "ICF wall calculator", "ICF forms and core concrete for the foundation walls.")
WALL_FRAMING = _calc("wall_framing", "Wall framing calculator", "Studs, plates and members for each wall.")
FRAMING_ESTIMATE = Tool("estimate_page", "estimates.framing_quantities", "Framing quantities, purchase and "
                        "framing materials quote", "Count a wall, buy it, and ask the supplier to price it.")
DECK_TAKEOFF = Tool("project_page", "deck_takeoff.review", "Construction model takeoff and framing quote request",
                    "The construction model's member counts and the one-click framing quote request.")
MEMBER_COUNTS = Tool("estimate_page", "estimates.calculation_list", "Construction model member counts",
                     "The project's verified construction model counts, offered to the estimate review.")
ROOFING = _calc("roofing", "Roofing calculator", "Roof area, bundles, underlayment and ridge cap.")
SIDING = _calc("siding", "Siding calculator", "Net wall area and pieces.")
DRYWALL = _calc("drywall", "Drywall calculator", "Board area and sheets.")
FLOORING = _calc("flooring", "Flooring calculator", "Floor area, boxes and the room perimeter for trim.")
STAIRS = _calc("stairs", "Stair calculator", "Checks the stair design; enter the stair materials as lines.")

_NO_CALC = ("No CalibraytAI calculator covers this work yet. Enter the quantities and costs as lines; "
            "they are marked as manual entries.")

STAGES: Dict[str, StageSpec] = {s.key: s for s in (
    StageSpec("demolition", "Demolition", "Taking out what is there before the new work starts.",
              (Part("demo_work", "Demolition and removal"), Part("demo_disposal", "Disposal bins and fees")),
              (MANUAL, LABOUR), "A demolition contractor removes and disposes of the existing work."),
    StageSpec("site_prep", "Site preparation", "Clearing, layout and temporary services before digging.",
              (Part("clearing", "Clearing and grubbing"), Part("layout", "Layout and survey stakes"),
               Part("temporary_services", "Temporary power, water and toilet")),
              (MANUAL, LABOUR), "An excavation or site-services contractor prepares the site.", gc_only=True),
    StageSpec("excavation", "Excavation", "Digging for the foundation, backfill and hauling away extra soil.",
              (Part("dig", "Dig for the foundation"), Part("backfill", "Backfill and compaction"),
               Part("haul_away", "Haul away extra soil")),
              (MANUAL, LABOUR), "An excavation contractor digs, backfills and hauls."),
    StageSpec("footings_foundation", "Footings & foundation",
              "Footings, foundation walls, waterproofing, insulation, drainage and the basement slab.",
              (Part("footings", "Footings", (FOOTING,)), Part("foundation_walls", "Foundation walls", (ICF, CONCRETE)),
               Part("waterproofing", "Waterproofing and damp-proofing"), Part("foundation_insulation", "Insulation"),
               Part("drainage", "Weeping tile and drainage"), Part("slab", "Basement slab concrete", (CONCRETE,)),
               Part("foundation_labour", "Foundation labour", labour_part=True)),
              (FOOTING, ICF, CONCRETE, LABOUR, MANUAL), "A foundation contractor forms and pours the foundation."),
    StageSpec("framing", "Framing", "Floors, walls, roof framing, sheathing and connectors, and the labour to build them.",
              (Part("floor_framing", "Floor framing", (DECK_TAKEOFF,)),
               Part("wall_framing", "Wall framing", (WALL_FRAMING, FRAMING_ESTIMATE, MEMBER_COUNTS)),
               Part("roof_framing", "Roof framing (rafters or trusses)"), Part("sheathing", "Sheathing"),
               Part("connectors", "Connectors and fasteners"),
               Part("framing_labour", "Framing installation labour", labour_part=True)),
              (WALL_FRAMING, FRAMING_ESTIMATE, MEMBER_COUNTS, DECK_TAKEOFF, LABOUR, MANUAL),
              "A framing crew builds the frame. Supply the materials yourself and subcontract the installation by "
              "splitting the stage into its parts."),
    StageSpec("roofing", "Roofing", "Shingles, underlayment, ridge cap, flashing and the labour to install them.",
              (Part("roof_covering", "Roof covering", (ROOFING,)), Part("flashing_vents", "Flashing and vents"),
               Part("roofing_labour", "Roofing labour", labour_part=True)),
              (ROOFING, LABOUR, MANUAL), "A roofing contractor supplies and installs the roof."),
    StageSpec("windows_doors", "Windows & exterior doors", "The opening schedule: each window and exterior door, "
              "and the labour to install them.",
              (Part("windows", "Windows"), Part("exterior_doors", "Exterior doors"),
               Part("openings_labour", "Installation labour", labour_part=True)),
              (MANUAL, LABOUR), "An installer supplies and installs the windows and doors."),
    StageSpec("siding", "Siding & exterior finishes", "Siding, trim, soffit and fascia.",
              (Part("siding_cladding", "Siding", (SIDING,)), Part("soffit_fascia", "Soffit, fascia and trim"),
               Part("siding_labour", "Siding labour", labour_part=True)),
              (SIDING, LABOUR, MANUAL), "A siding contractor supplies and installs the exterior finishes."),
    StageSpec("electrical", "Electrical", "Wiring, panel, fixtures and the electrical permit.", (),
              (MANUAL, LABOUR), "A licensed electrician quotes the electrical work."),
    StageSpec("plumbing", "Plumbing", "Supply and drain piping, fixtures and the plumbing permit.", (),
              (MANUAL, LABOUR), "A licensed plumber quotes the plumbing."),
    StageSpec("hvac", "HVAC", "Heating, cooling, ventilation and ductwork.", (),
              (MANUAL, LABOUR), "An HVAC contractor quotes the heating and ventilation."),
    StageSpec("insulation", "Insulation", "Wall, ceiling and attic insulation and the vapour barrier.", (),
              (MANUAL, LABOUR), "An insulation contractor supplies and installs it."),
    StageSpec("drywall", "Drywall", "Board, taping and finishing.",
              (Part("drywall_board", "Drywall board", (DRYWALL,)), Part("taping", "Taping and finishing"),
               Part("drywall_labour", "Drywall labour", labour_part=True)),
              (DRYWALL, LABOUR, MANUAL), "A drywall contractor boards, tapes and finishes."),
    StageSpec("interior_finishes", "Interior finishes",
              "Flooring, trim, interior doors, cabinets, painting and other finishes.",
              (Part("flooring", "Flooring", (FLOORING,)), Part("trim", "Trim and baseboard"),
               Part("interior_doors", "Interior doors"), Part("cabinets", "Cabinets and counters"),
               Part("painting", "Painting"), Part("stairs_railings", "Stairs and railings", (STAIRS,)),
               Part("finishes_labour", "Finishing labour", labour_part=True)),
              (FLOORING, STAIRS, LABOUR, MANUAL), "Finishing trades supply and install the finishes."),
    StageSpec("garage_door", "Garage door", "The overhead door, opener and installation.", (),
              (MANUAL, LABOUR), "A garage door company supplies and installs it."),
    StageSpec("final_cleanup", "Final cleanup", "Labour, disposal, equipment and supplies to hand over a clean job.",
              (Part("cleanup_labour", "Cleanup labour", labour_part=True), Part("disposal", "Disposal bins and fees"),
               Part("cleanup_equipment", "Equipment and supplies")),
              (MANUAL, LABOUR), "A cleaning company does the final clean.", gc_only=True),
)}

TEMPLATES: Dict[str, Tuple[str, ...]] = {
    PROJECT_NEW_HOME: ("site_prep", "excavation", "footings_foundation", "framing", "roofing", "windows_doors",
                       "siding", "electrical", "plumbing", "hvac", "insulation", "drywall", "interior_finishes",
                       "final_cleanup"),
    PROJECT_ADDITION: ("demolition", "site_prep", "excavation", "footings_foundation", "framing", "roofing",
                       "windows_doors", "siding", "electrical", "plumbing", "hvac", "insulation", "drywall",
                       "interior_finishes", "final_cleanup"),
    PROJECT_GARAGE: ("site_prep", "excavation", "footings_foundation", "framing", "roofing", "windows_doors",
                     "garage_door", "siding", "electrical", "final_cleanup"),
    PROJECT_FOUNDATION: ("site_prep", "excavation", "footings_foundation", "final_cleanup"),
    PROJECT_OTHER: ("site_prep", "excavation", "footings_foundation", "framing", "roofing", "windows_doors",
                    "siding", "electrical", "plumbing", "hvac", "insulation", "drywall", "interior_finishes",
                    "final_cleanup"),
}

# The commercial project type (ProjectCommercialContext) each guided type normally goes with: a pre-selection
# on the New Project form only; the person can change it, and pricing reads the commercial context as before.
COMMERCIAL_TYPE_HINT = {
    PROJECT_NEW_HOME: "New Build", PROJECT_ADDITION: "Addition", PROJECT_GARAGE: "Garage",
    PROJECT_FOUNDATION: "Foundation", PROJECT_OTHER: "Specialty",
}

MANUAL_KINDS = (
    ("material", "Material"), ("labour", "Labour (hours)"), ("equipment", "Equipment"), ("delivery", "Delivery"),
    ("disposal", "Disposal"), ("subcontract", "Subcontract"), ("other", "Other direct cost"),
)
MANUAL_KIND_LABELS = dict(MANUAL_KINDS)
MANUAL_CODE_PREFIX = "GE-"  # manual guided lines are coded GE-<KIND>; labour hours use the existing LAB- lines
SUBCONTRACT_CODE = "GE-SUBCONTRACT"


# ---------------------------------------------------------------------------------------------- small helpers
def _actor(actor) -> str:
    name = (actor or "").strip()
    if name.lower() in _REJECTED_ACTORS:
        raise GuidedEstimatingError("A person must make this decision.")
    return name[:150]


def _now():
    return datetime.utcnow()


def _event(guided, event, *, actor, stage=None, from_value=None, to_value=None, detail=None, version=None,
           user_id=None):
    db.session.add(GuidedEstimateEvent(
        organization_id=guided.organization_id, guided_estimate_id=guided.id,
        stage_id=stage.id if stage is not None else None, event=event[:40],
        from_value=(from_value or None) and str(from_value)[:40], to_value=(to_value or None) and str(to_value)[:40],
        detail=(detail or None) and str(detail)[:600], estimate_version_id=version.id if version is not None else None,
        user_id=user_id, actor_display_name=actor, created_at=_now()))


def _money(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"))


def get_project(organization_id: str, project_id: int) -> Project:
    project = Project.query.filter_by(id=project_id, organization_id=organization_id).first()
    if project is None:
        raise GuidedEstimatingError("Project not found.")
    return project


def get_guided(organization_id: str, project_id: int) -> Optional[GuidedEstimate]:
    return GuidedEstimate.query.filter_by(organization_id=organization_id, project_id=project_id).first()


def get_stage(guided: GuidedEstimate, stage_id: int) -> GuidedEstimateStage:
    stage = GuidedEstimateStage.query.filter_by(id=stage_id, guided_estimate_id=guided.id,
                                                organization_id=guided.organization_id).first()
    if stage is None:
        raise GuidedEstimatingError("That stage is not on this project.")
    return stage


def spec_for(stage: GuidedEstimateStage) -> Optional[StageSpec]:
    key = stage.parent.stage_key if stage.parent is not None else stage.stage_key
    spec = STAGES.get(key)
    if spec is None and key.startswith("work_"):
        from app.services.selected_work import work_spec  # selected work (28 Oct 2026)

        spec = work_spec(key)
    return spec


def _selected(guided) -> bool:
    from app.services.selected_work import is_selected_work

    return is_selected_work(guided)


def part_for(stage: GuidedEstimateStage) -> Optional[Part]:
    if stage.parent is None:
        return None
    spec = spec_for(stage)
    if spec is None:
        return None
    sub_key = stage.stage_key.split(".", 1)[-1]
    return next((p for p in spec.parts if p.key == sub_key), None)


# ---------------------------------------------------------------------------------------------- start
def start_guided_estimate(*, organization_id: str, project_id: int, project_type: str, contractor_role: str,
                          actor: str, user_id=None, legacy_stages: bool = False) -> GuidedEstimate:
    """Begin (or return) the project's guided estimate (its scope). One per project: never a duplicate.

    Since 28 Oct 2026 (Approach B) a new scope is the selected work: it starts with no work in it and the
    contractor adds the work being done (``app/services/selected_work.py``). ``legacy_stages`` builds the earlier
    project-type stage template; only fixtures for estimates made before then use it."""
    name = _actor(actor)
    project = get_project(organization_id, project_id)
    existing = get_guided(organization_id, project.id)
    if existing is not None:
        return existing
    if project_type not in PROJECT_TYPES:
        raise GuidedEstimatingError("Choose what is being built.")
    if contractor_role not in CONTRACTOR_ROLES:
        raise GuidedEstimatingError("Choose your role on this project.")
    from app.services.time_entry import raise_if_company_time

    raise_if_company_time(project, GuidedEstimatingError)
    now = _now()
    guided = GuidedEstimate(organization_id=organization_id, project_id=project.id, project_type=project_type,
                            contractor_role=contractor_role, scope_status=SCOPE_DRAFT, user_id=user_id,
                            actor_display_name=name, created_at=now, updated_at=now)
    db.session.add(guided)
    db.session.flush()
    if not legacy_stages:
        from app.services.selected_work import mark_selected_work

        _event(guided, "STARTED", actor=name, to_value=project_type, detail=f"Role: {contractor_role}", user_id=user_id)
        mark_selected_work(guided, actor=name, user_id=user_id)
        db.session.commit()
        return guided
    order = 0
    for key in TEMPLATES[project_type]:
        spec = STAGES[key]
        if contractor_role == ROLE_SUBCONTRACTOR and spec.gc_only:
            continue  # a subcontractor's template leaves out the general contractor's own stages (they can add them)
        order += 10
        _add_stage_rows(guided, spec, order)
    _event(guided, "STARTED", actor=name, to_value=project_type, detail=f"Role: {contractor_role}", user_id=user_id)
    db.session.commit()
    return guided


def _add_stage_rows(guided, spec: StageSpec, order: int) -> GuidedEstimateStage:
    now = _now()
    stage = GuidedEstimateStage(organization_id=guided.organization_id, guided_estimate_id=guided.id,
                                stage_key=spec.key, display_name=spec.name, explanation=spec.explanation,
                                sort_order=order, is_custom=False, is_split=False, responsibility=None,
                                status=STATUS_NOT_STARTED, created_at=now, updated_at=now)
    db.session.add(stage)
    db.session.flush()
    for index, part in enumerate(spec.parts, start=1):
        db.session.add(GuidedEstimateStage(
            organization_id=guided.organization_id, guided_estimate_id=guided.id, parent_stage_id=stage.id,
            stage_key=f"{spec.key}.{part.key}", display_name=part.name, sort_order=order * 100 + index,
            is_custom=False, is_split=False, responsibility=None, status=STATUS_NOT_STARTED,
            created_at=now, updated_at=now))
    return stage


def available_library_stages(guided) -> List[StageSpec]:
    present = {s.stage_key for s in guided.top_stages}
    return [spec for key, spec in STAGES.items() if key not in present]


def add_stage(guided, *, actor, library_key="", custom_name="", user_id=None) -> GuidedEstimateStage:
    """Add a stage from the library or a contractor-named one. It starts undecided, never N/A."""
    name = _actor(actor)
    _require_not_committed(guided)
    last = max([s.sort_order for s in guided.top_stages] or [0])
    if library_key:
        spec = STAGES.get(library_key)
        if spec is None or any(s.stage_key == library_key for s in guided.top_stages):
            raise GuidedEstimatingError("Choose a stage that is not on the list yet.")
        stage = _add_stage_rows(guided, spec, last + 10)
    else:
        label = " ".join((custom_name or "").split())[:120]
        if not label:
            raise GuidedEstimatingError("Name the stage to add.")
        key = "custom_" + "".join(ch if ch.isalnum() else "_" for ch in label.lower())[:60]
        while any(s.stage_key == key for s in guided.stages):
            key += "_x"
        now = _now()
        stage = GuidedEstimateStage(organization_id=guided.organization_id, guided_estimate_id=guided.id,
                                    stage_key=key, display_name=label, explanation="Added by the contractor.",
                                    sort_order=last + 10, is_custom=True, is_split=False, responsibility=None,
                                    status=STATUS_NOT_STARTED, created_at=now, updated_at=now)
        db.session.add(stage)
        db.session.flush()
    _event(guided, "STAGE_ADDED", actor=name, stage=stage, detail=stage.display_name, user_id=user_id)
    if guided.scope_status == SCOPE_FINALIZED:
        # A stage added after the scope was finalized is undecided; the scope goes back to draft until decided.
        guided.scope_status = SCOPE_DRAFT
        _event(guided, "SCOPE_REOPENED", actor=name, detail="A stage was added.", user_id=user_id)
    guided.updated_at = _now()
    db.session.commit()
    return stage


# ---------------------------------------------------------------------------------------------- commitment
def accepted_proposal(guided):
    """The customer's accepted proposal on this guided estimate, if any (then changes go to change orders)."""
    if guided.estimate_id is None:
        return None
    from app.models import Proposal

    return (Proposal.query.filter_by(estimate_id=guided.estimate_id, status="Accepted")
            .order_by(Proposal.id.desc()).first())


def _require_not_committed(guided):
    if accepted_proposal(guided) is not None:
        raise GuidedEstimatingError(
            "The customer has accepted the proposal. Changes to the scope now go through a change order.")


# ---------------------------------------------------------------------------------------------- scope
def scope_rows(guided) -> List[GuidedEstimateStage]:
    """The top-level rows of the scope. In the selected-work model, removed work is not part of the estimate."""
    if _selected(guided):
        return [s for s in guided.top_stages if s.responsibility != RESP_NA]
    return list(guided.top_stages)


def leaf_stages(guided, *, include_na=True) -> List[GuidedEstimateStage]:
    """The stages and parts that are decided and estimated on their own, in construction order."""
    out = []
    if _selected(guided):
        include_na = False
    for stage in scope_rows(guided):
        rows = stage.children if stage.is_split else [stage]
        for row in rows:
            if include_na or row.responsibility != RESP_NA:
                out.append(row)
    return out


def undecided(guided) -> List[GuidedEstimateStage]:
    return [row for row in leaf_stages(guided) if row.responsibility is None]


def save_scope(guided, *, decisions: Dict[int, str], split: Iterable[int], na_reasons: Dict[int, str],
               scope_descriptions: Dict[int, str] | None = None, actor: str, finalize: bool = False,
               user_id=None) -> GuidedEstimate:
    """Record each stage's (or part's) responsibility. Undecided is allowed only until the scope is finalized."""
    name = _actor(actor)
    _require_not_committed(guided)
    split = set(int(x) for x in split)
    scope_descriptions = scope_descriptions or {}
    rows = {s.id: s for s in guided.stages}
    for stage in guided.top_stages:
        want_split = stage.id in split and bool(stage.children)
        if want_split != stage.is_split:
            if want_split and _stage_has_lines(stage):
                raise GuidedEstimatingError(
                    f"{stage.display_name} already has estimate lines. Split it before adding lines, or keep it whole.")
            if not want_split and any(_stage_has_lines(c) for c in stage.children):
                raise GuidedEstimatingError(
                    f"The parts of {stage.display_name} already have estimate lines; it stays split.")
            stage.is_split = want_split
            if want_split:
                stage.responsibility = None
            _event(guided, "SPLIT" if want_split else "UNSPLIT", actor=name, stage=stage, user_id=user_id)
    for stage_id, choice in decisions.items():
        row = rows.get(int(stage_id))
        if row is None:
            raise GuidedEstimatingError("That stage is not on this project.")
        if row.parent is None and row.is_split:
            continue  # decided part by part
        if row.parent is not None and not row.parent.is_split:
            continue  # parts of a whole stage follow the stage
        value = (choice or "").strip().upper() or None
        if value is not None and value not in RESPONSIBILITIES:
            raise GuidedEstimatingError("Choose Internal, Subcontracted or N/A.")
        if value == row.responsibility:
            continue
        _change_responsibility(guided, row, value, actor=name, reason=na_reasons.get(row.id, ""), user_id=user_id)
    for stage_id, text in scope_descriptions.items():
        row = rows.get(int(stage_id))
        if row is not None and (text or "").strip() != (row.scope_description or ""):
            row.scope_description = (text or "").strip() or None
    guided.updated_at = _now()
    if finalize:
        missing = undecided(guided)
        if missing:
            db.session.commit()  # keep what was decided
            raise GuidedEstimatingError("Decide every stage before finalizing the scope: "
                                        + ", ".join(r.section_name for r in missing) + ".")
        if not leaf_stages(guided, include_na=False):
            db.session.commit()
            raise GuidedEstimatingError("Every stage is N/A. Choose at least one stage to estimate.")
        guided.scope_status = SCOPE_FINALIZED
        guided.scope_finalized_at = _now()
        guided.scope_finalized_by = name
        _event(guided, "SCOPE_FINALIZED", actor=name, user_id=user_id)
        db.session.flush()
        ensure_estimate(guided, actor=name, user_id=user_id)
    db.session.commit()
    return guided


def _change_responsibility(guided, row, value, *, actor, reason="", user_id=None):
    if value == RESP_NA and _stage_has_lines(row):
        raise GuidedEstimatingError(
            f"{row.section_name} has estimate lines. Remove them before marking it N/A, so no cost is left behind.")
    previous = row.responsibility
    row.responsibility = value
    row.decided_by = actor if value else None
    row.decided_at = _now() if value else None
    row.na_reason = (reason or "").strip() or None if value == RESP_NA else None
    if value == RESP_NA:
        row.status = STATUS_EXCLUDED
    elif row.status == STATUS_EXCLUDED or previous is not None:
        row.status = STATUS_IN_PROGRESS if _stage_has_lines(row) else STATUS_NOT_STARTED
    _clear_completion(row)
    row.updated_at = _now()
    _event(guided, "RESPONSIBILITY", actor=actor, stage=row, from_value=previous, to_value=value,
           detail=row.na_reason, user_id=user_id)
    if guided.scope_status == SCOPE_FINALIZED and value is not None and value != RESP_NA:
        version = editable_version(guided)
        if version is not None:
            section_for(row, version, create=True)


def change_responsibility(guided, stage, value, *, actor, reason="", user_id=None):
    """Change one stage's responsibility from the workflow (a scope revision, with its history)."""
    name = _actor(actor)
    _require_not_committed(guided)
    value = (value or "").strip().upper() or None
    if value not in RESPONSIBILITIES:
        raise GuidedEstimatingError("Choose Internal, Subcontracted or N/A.")
    if value == RESP_NA and _selected(guided):
        raise GuidedEstimatingError("Choose Internal or Subcontracted. Work that is not being done is removed from "
                                    "the Work page.")
    if stage.parent is None and stage.is_split:
        raise GuidedEstimatingError("This stage is decided part by part.")
    _change_responsibility(guided, stage, value, actor=name, reason=reason, user_id=user_id)
    db.session.commit()


def _clear_completion(row):
    row.completion_basis = None
    row.completed_by = None
    row.completed_at = None


# ---------------------------------------------------------------------------------------------- estimate
def ensure_estimate(guided, *, actor, user_id=None) -> Estimate:
    """The project's estimate for this guided workflow: the existing one it already uses, or a new draft."""
    if guided.estimate is not None:
        estimate = guided.estimate
    else:
        from app.services.estimates import create_estimate, suggest_next_estimate_number

        project = guided.project
        estimate = create_estimate(project_id=project.id,
                                   estimate_number=suggest_next_estimate_number(organization_id=guided.organization_id),
                                   title=f"{project.name} — guided estimate"[:180],
                                   organization_id=guided.organization_id)
        guided.estimate_id = estimate.id
        _event(guided, "ESTIMATE_CREATED", actor=actor, detail=estimate.estimate_number,
               version=estimate.current_version, user_id=user_id)
    version = editable_version(guided)
    if version is not None:
        for row in leaf_stages(guided, include_na=False):
            section_for(row, version, create=True)
    db.session.commit()
    return estimate


def current_version(guided) -> Optional[EstimateVersion]:
    estimate = guided.estimate
    return estimate.current_version if estimate is not None else None


def version_is_editable(version) -> bool:
    return version is not None and not version.is_locked and (version.status or "Draft") == "Draft"


def editable_version(guided) -> Optional[EstimateVersion]:
    version = current_version(guided)
    return version if version_is_editable(version) else None


def section_for(stage, version, *, create=False) -> Optional[EstimateSection]:
    if version is None:
        return None
    # The durable work-package link first (30 Oct 2026); the name match remains only for sections made before the
    # link existed, and such a section is linked the first time it is found on an editable version.
    for section in version.sections:
        if section.guided_stage_id == stage.id:
            return section
    name = stage.section_name
    for section in version.sections:
        if section.guided_stage_id is None and (section.name or "") == name:
            if version_is_editable(version):
                section.guided_stage_id = stage.id
            return section
    if not create or not version_is_editable(version):
        return None
    from app.services.estimate_builder import create_section

    leaves = [r.id for r in leaf_stages(stage.guided_estimate)]
    order = (leaves.index(stage.id) + 1) * 10 if stage.id in leaves else None
    section = create_section(version, name=name, description=(stage.explanation or None), sort_order=order)
    section.guided_stage_id = stage.id
    return section


def _stage_has_lines(stage) -> bool:
    version = current_version(stage.guided_estimate)
    section = section_for(stage, version)
    return bool(section is not None and section.line_items)


def stage_lines(stage, version=None) -> List[EstimateLineItem]:
    version = version or current_version(stage.guided_estimate)
    section = section_for(stage, version)
    return list(section.line_items) if section is not None else []


# ---------------------------------------------------------------------------------------------- stage checks
def _line_kind(line) -> str:
    from app.services.estimate_labour_hours import is_labour_line

    code = (line.code or "")
    if is_labour_line(line):
        return "labour"
    if code == SUBCONTRACT_CODE:
        return "subcontract"
    if code.startswith(MANUAL_CODE_PREFIX):
        return code[len(MANUAL_CODE_PREFIX):].lower() or "other"
    if (line.line_type or "") == "Allowance":
        return "allowance"
    return "material"


def _stage_calculations(stage):
    from app.models.project_calculation import ProjectCalculation

    return (ProjectCalculation.query.filter_by(organization_id=stage.organization_id,
                                               project_id=stage.guided_estimate.project_id, guided_stage_id=stage.id)
            .order_by(ProjectCalculation.id.asc()).all())


def _set_aside_intakes(stage):
    return {int(e.to_value) for e in GuidedEstimateEvent.query.filter_by(stage_id=stage.id, event="INTAKE_SET_ASIDE")
            if (e.to_value or "").isdigit()}


def _open_intake_rows(calculations, stage=None):
    """Calculation quantities sent to the estimate review but not yet confirmed or set aside there."""
    from app.models.calculation_estimate_mapping import STATUS_OPEN, CalculationResultIntake

    aside = _set_aside_intakes(stage) if stage is not None else set()
    out = []
    for calc in calculations:
        if not calc.calculation_result_intake_id or calc.calculation_result_intake_id in aside:
            continue
        intake = db.session.get(CalculationResultIntake, calc.calculation_result_intake_id)
        if intake is None:
            continue
        open_rows = [r for r in intake.reviews if r.status == STATUS_OPEN]
        if open_rows:
            out.append((calc, intake, len(open_rows)))
    return out


def _facts_complete(line) -> bool:
    """The line has what costing needs (quantity, unit, unit cost, waste). Read only: unlike the costing check it
    does not recalculate the line, so a priced line's selling price is never touched by looking at a stage."""
    return (line.quantity is not None and bool((line.unit or "").strip()) and line.unit_cost is not None
            and line.waste_percent is not None)


def stage_check(stage, version=None) -> dict:
    """What a leaf stage (or part) has, what it is missing and whether it may be completed. Read only."""
    from app.services.estimate_scope_delivery import get_scope_delivery_for_line
    from app.services.subcontract_quote import quotes_for_line, selected_quote_for_line
    from app.services.suggested_cost import labour_suggestion, material_suggestion
    from app.models.estimate_scope_delivery import STATUS_CONFIRMED as ROUTING_CONFIRMED

    guided = stage.guided_estimate
    version = version or current_version(guided)
    lines = stage_lines(stage, version)
    calcs = _stage_calculations(stage)
    open_intakes = _open_intake_rows(calcs, stage)
    issues: List[str] = []
    line_rows = []
    allowance_line = None
    for line in lines:
        kind = _line_kind(line)
        routing = get_scope_delivery_for_line(line)
        cost = Decimal(line.unit_cost or 0)
        row = {"line": line, "kind": kind, "kind_label": MANUAL_KIND_LABELS.get(kind, kind.capitalize()),
               "routing": routing, "routing_confirmed": routing is not None and routing.status == ROUTING_CONFIRMED,
               "quotes": quotes_for_line(line), "selected_quote": selected_quote_for_line(line),
               "labour_suggestion": labour_suggestion(line), "material_suggestion": material_suggestion(line),
               "missing": []}
        if stage.allowance_line_id and line.id == stage.allowance_line_id:
            allowance_line = line
            row["kind"], row["kind_label"] = "allowance", "Approved allowance"
        if not _facts_complete(line) or cost <= 0:
            if not (row["kind"] == "allowance" and stage.allowance_approved_at):
                row["missing"].append("no cost yet")
        if kind == "subcontract":
            sug = row["labour_suggestion"]
            if not row["quotes"]:
                row["missing"].append("no quote recorded")
            elif row["selected_quote"] is None:
                row["missing"].append("choose the quote to use")
            elif sug is not None and not sug["applied"]:
                row["missing"].append("selected quote not yet used on the line (Use this cost on the line)")
        if not row["routing_confirmed"] and row["kind"] != "allowance":
            row["missing"].append("who supplies and builds it is not confirmed")
        line_rows.append(row)
    for row in line_rows:
        if row["missing"]:
            issues.append(f"{row['line'].description}: " + "; ".join(row["missing"]))
    for calc, intake, count in open_intakes:
        issues.append(f"{count} calculated quantit{'y' if count == 1 else 'ies'} from {calc.calculator_label} "
                      f"still to review")
    awaiting = [c for c in calcs if c.review_status == "AWAITING_REVIEW" and c.payload]
    for calc in awaiting:
        issues.append(f"{calc.calculator_label} result not yet sent to the estimate review")
    costed = [r for r in line_rows if not r["missing"] and Decimal(r["line"].unit_cost or 0) > 0
              and r["kind"] != "allowance"]
    total = sum((Decimal(r["line"].extended_cost or 0) for r in line_rows), Decimal("0"))
    allowance_ok = bool(stage.allowance_approved_at and allowance_line is not None
                        and Decimal(allowance_line.unit_cost or 0) > 0)
    zero_ok = bool(stage.zero_cost_authorized_at and (stage.zero_cost_reason or "").strip())
    bases = []
    if line_rows and not issues and costed:
        bases.append(BASIS_CONFIRMED_COSTS)
    if allowance_ok and not [i for r in line_rows if r["line"].id != allowance_line.id for i in r["missing"]] \
            and not open_intakes and not awaiting:
        bases.append(BASIS_APPROVED_ALLOWANCE)
    if zero_ok and total == 0 and not open_intakes and not awaiting:
        bases.append(BASIS_AUTHORIZED_ZERO_COST)
    if not line_rows and not zero_ok:
        issues.insert(0, "No cost yet: " + ("record and use the subcontractor's quote" if stage.responsibility == RESP_SUBCONTRACTED
                                            else "use a calculator or enter the cost lines"))
    waiting = (stage.responsibility == RESP_SUBCONTRACTED and stage.quote_requested_at is not None
               and not any(r["quotes"] for r in line_rows))
    return {"stage": stage, "version": version, "lines": line_rows, "issues": issues, "bases": bases,
            "total": _money(total), "calculations": calcs, "open_intakes": open_intakes, "awaiting": awaiting,
            "waiting_for_quote": waiting, "allowance_line": allowance_line}


def effective_status(stage, version=None, check=None) -> str:
    """The status shown and used by the gates. A Complete that is no longer true shows Needs Review."""
    if stage.parent is None and stage.is_split:
        statuses = [effective_status(child, version) for child in stage.children]
        if not statuses:
            return STATUS_NOT_STARTED
        if all(s == STATUS_EXCLUDED for s in statuses):
            return STATUS_EXCLUDED
        if all(s in (STATUS_COMPLETE, STATUS_EXCLUDED) for s in statuses):
            return STATUS_COMPLETE
        for status in (STATUS_NEEDS_REVIEW, STATUS_WAITING_FOR_QUOTE, STATUS_IN_PROGRESS):
            if status in statuses:
                return status
        if STATUS_COMPLETE in statuses:
            return STATUS_IN_PROGRESS
        return STATUS_NOT_STARTED
    if stage.responsibility == RESP_NA:
        return STATUS_EXCLUDED
    if stage.responsibility is None:
        return STATUS_NOT_STARTED
    check = check or stage_check(stage, version)
    if stage.completion_basis:
        return STATUS_COMPLETE if stage.completion_basis in check["bases"] else STATUS_NEEDS_REVIEW
    if check["waiting_for_quote"]:
        return STATUS_WAITING_FOR_QUOTE
    if check["lines"] or check["calculations"]:
        if check["open_intakes"] or check["awaiting"] or any(r["quotes"] for r in check["lines"]) \
                or any(r["missing"] for r in check["lines"]):
            return STATUS_NEEDS_REVIEW
        return STATUS_IN_PROGRESS
    if stage.status == STATUS_IN_PROGRESS:
        return STATUS_IN_PROGRESS
    return STATUS_NOT_STARTED


def _sync_status(stage, version=None):
    status = effective_status(stage, version)
    if stage.status != status:
        stage.status = status
        stage.updated_at = _now()
    if stage.parent is not None and stage.parent.is_split:
        _sync_status(stage.parent, version)
    return status


def next_action(stage, check) -> str:
    if stage.responsibility == RESP_NA:
        return "Nothing to estimate: excluded from the scope."
    if stage.completion_basis and stage.completion_basis in check["bases"]:
        return "Complete. Reopen it to change it."
    if check["open_intakes"]:
        return "Review the calculated quantities and add them to the estimate."
    if check["awaiting"]:
        return "Send the saved calculation to the estimate review."
    if stage.responsibility == RESP_SUBCONTRACTED:
        lines = [r for r in check["lines"] if r["kind"] == "subcontract"]
        if not lines:
            return "Set up the subcontract and request the quote."
        row = lines[0]
        if check["waiting_for_quote"]:
            return "Waiting for the subcontractor's quote. Record it when it arrives; keep estimating other stages."
        if not row["quotes"]:
            return "Request the quote, then record it when it arrives."
        if row["selected_quote"] is None:
            return "Compare the quotes and select the one to use."
        if row["labour_suggestion"] and not row["labour_suggestion"]["applied"]:
            return "Use the selected quote's cost on the line."
    if not check["lines"]:
        return "Open the calculator or enter the cost lines."
    if check["issues"]:
        return "Resolve the missing information listed below."
    return "Costs are confirmed. Press Complete & Next."


# ---------------------------------------------------------------------------------------------- stage actions
def _require_editable(guided) -> EstimateVersion:
    _require_not_committed(guided)
    if guided.scope_status != SCOPE_FINALIZED:
        raise GuidedEstimatingError("Finalize the scope first.")
    version = editable_version(guided)
    if version is None:
        raise GuidedEstimatingError("The estimate's current version is issued or locked. Start a revision "
                                    "(a new estimate version) to change it.")
    return version


def _leaf(stage):
    if stage.parent is None and stage.is_split:
        raise GuidedEstimatingError("Open one of this stage's parts.")
    if stage.responsibility in (None, RESP_NA):
        raise GuidedEstimatingError("This stage is not in the scope.")
    return stage


def mark_visited(guided, stage, *, actor, save=False, user_id=None):
    """Save / Save & Exit / opening a stage: remember where the person is (Resume)."""
    guided.last_stage_id = stage.id
    guided.updated_at = _now()
    if save and stage.responsibility not in (None, RESP_NA) and stage.status == STATUS_NOT_STARTED:
        stage.status = STATUS_IN_PROGRESS
        _event(guided, "STAGE_SAVED", actor=_actor(actor), stage=stage, user_id=user_id)
    _sync_status(stage)
    db.session.commit()


def save_stage_notes(guided, stage, *, scope_description, actor, user_id=None):
    name = _actor(actor)
    stage.scope_description = (scope_description or "").strip() or None
    if stage.status == STATUS_NOT_STARTED and stage.responsibility not in (None, RESP_NA):
        stage.status = STATUS_IN_PROGRESS
    guided.last_stage_id = stage.id
    _event(guided, "STAGE_SAVED", actor=name, stage=stage, user_id=user_id)
    db.session.commit()


def add_manual_cost(guided, stage, *, kind, description, quantity, unit, unit_cost, actor, user_id=None):
    """A governed manual line in the stage's section (no calculator covers it). Labour uses hours × the rate."""
    name = _actor(actor)
    version = _require_editable(guided)
    _leaf(stage)
    if kind not in MANUAL_KIND_LABELS:
        raise GuidedEstimatingError("Choose what kind of cost this is.")
    section = section_for(stage, version, create=True)
    from app.services.estimate_builder import add_manual_line
    from app.services.estimates import EstimateServiceError

    text = " ".join((description or "").split())
    if not text:
        raise GuidedEstimatingError("Describe the cost.")
    try:
        if kind == "labour":
            from app.services.estimate_labour_hours import LabourHoursError, version_rate

            try:  # the project labour rate (Joel, 30 Oct 2026)
                rate, source = version_rate(version, organization_id=guided.organization_id, actor=name)
            except LabourHoursError as exc:
                raise GuidedEstimatingError(str(exc)) from exc
            count = sum(1 for l in section.line_items if (l.code or "").startswith(f"LAB-GE-{stage.id}-")) + 1
            line = add_manual_line(section, line_type="Custom", description=f"Labour — {text}"[:255],
                                   quantity=quantity or "0", unit="hr", unit_cost=rate,
                                   code=f"LAB-GE-{stage.id}-{count}",
                                   notes=f"{source}. Hours entered by {name} (manual entry: no calculator covers it).")
        else:
            line = add_manual_line(section, line_type="Custom", description=text[:255], quantity=quantity or "0",
                                   unit=(unit or "").strip() or "ea", unit_cost=unit_cost or "0",
                                   code=MANUAL_CODE_PREFIX + kind.upper(),
                                   notes=f"Manual entry by {name}: no CalibraytAI calculator covers this cost.")
    except EstimateServiceError as exc:
        raise GuidedEstimatingError(str(exc)) from exc
    stage.status = STATUS_IN_PROGRESS if stage.status == STATUS_NOT_STARTED else stage.status
    _clear_completion(stage)
    _event(guided, "COST_LINE_ADDED", actor=name, stage=stage, detail=text, version=version, user_id=user_id)
    _sync_status(stage, version)
    db.session.commit()
    return line


def setup_subcontract(guided, stage, *, actor, description="", user_id=None) -> EstimateLineItem:
    """The stage's subcontract line (one lump sum), routed to the subcontractor; its cost comes from the quote."""
    name = _actor(actor)
    version = _require_editable(guided)
    _leaf(stage)
    if stage.responsibility != RESP_SUBCONTRACTED:
        raise GuidedEstimatingError("Only a subcontracted stage has a subcontract.")
    existing = [r for r in stage_lines(stage, version) if (r.code or "") == SUBCONTRACT_CODE]
    if existing:
        return existing[0]  # never a duplicate
    section = section_for(stage, version, create=True)
    from app.services.estimate_builder import add_manual_line

    scope = (description or stage.scope_description or stage.section_name).strip()
    line = add_manual_line(section, line_type="Custom", description=f"{stage.section_name} — subcontract"[:255],
                           quantity=1, unit="lump sum", unit_cost=0, code=SUBCONTRACT_CODE,
                           notes=f"Scope: {scope}"[:2000])
    _route(line, material="SUBCONTRACTOR_SUPPLIED", labour="SUBCONTRACT", actor=name, user_id=user_id)
    if description and not stage.scope_description:
        stage.scope_description = description.strip()
    stage.status = STATUS_IN_PROGRESS if stage.status == STATUS_NOT_STARTED else stage.status
    _event(guided, "SUBCONTRACT_SET_UP", actor=name, stage=stage, version=version, user_id=user_id)
    db.session.commit()
    return line


def record_quote(guided, stage, *, actor, form, user_id=None):
    """Record a received subcontract quote: the existing quote evidence on the stage's subcontract line."""
    name = _actor(actor)
    line = setup_subcontract(guided, stage, actor=name, user_id=user_id)
    from app.services.subcontract_quote import SubcontractQuoteError, receive_quote

    try:
        quote = receive_quote(
            line, actor=name, organization_id=guided.organization_id, project_id=guided.project_id,
            subcontractor_id=int(form.get("subcontractor_id")) if (form.get("subcontractor_id") or "").isdigit() else None,
            subcontractor_code=form.get("subcontractor_code"), subcontractor_legal_name=form.get("subcontractor_legal_name"),
            quote_reference=form.get("quote_reference") or "", amount=form.get("amount") or "",
            currency=form.get("currency") or "CAD", quote_date=form.get("quote_date") or "",
            expires_on=form.get("expires_on") or None, included_scope=form.get("included_scope"),
            exclusions=form.get("exclusions"), provenance_note=form.get("provenance_note"), user_id=user_id)
    except SubcontractQuoteError as exc:
        raise GuidedEstimatingError(str(exc)) from exc
    _event(guided, "QUOTE_RECEIVED", actor=name, stage=stage, detail=quote.quote_reference, user_id=user_id)
    _sync_status(stage)
    db.session.commit()
    return quote


def request_quote(guided, stage, *, actor, user_id=None):
    """The person sent the quote request (the printable sheet, email or call): the stage waits for the quote."""
    name = _actor(actor)
    _require_editable(guided)
    _leaf(stage)
    if stage.responsibility != RESP_SUBCONTRACTED:
        raise GuidedEstimatingError("Only a subcontracted stage waits for a quote.")
    setup_subcontract(guided, stage, actor=name, user_id=user_id)
    stage.quote_requested_at = _now()
    stage.quote_requested_by = name
    _event(guided, "QUOTE_REQUESTED", actor=name, stage=stage, user_id=user_id)
    _sync_status(stage)
    db.session.commit()


def _route(line, *, material, labour, actor, user_id=None):
    from app.services.estimate_scope_delivery import confirm_scope_delivery, save_scope_delivery

    save_scope_delivery(line, material_procurement=material, labour_delivery=labour, actor=actor, user_id=user_id,
                        commit=False)
    confirm_scope_delivery(line, actor=actor, user_id=user_id, commit=False)


def routing_for(stage, line) -> Tuple[str, str]:
    """Who supplies and builds a line, from the stage's (or part's) responsibility. Used when a person confirms."""
    kind = _line_kind(line)
    sibling_labour_subcontracted = False
    if stage.parent is not None and stage.parent.is_split:
        part = part_for(stage)
        if part is None or not part.labour_part:
            for sibling in stage.parent.children:
                sp = part_for(sibling)
                if sp is not None and sp.labour_part and sibling.responsibility == RESP_SUBCONTRACTED:
                    sibling_labour_subcontracted = True
    if stage.responsibility == RESP_SUBCONTRACTED:
        if kind == "labour":
            return "NO_MATERIAL", "SUBCONTRACT"
        return "SUBCONTRACTOR_SUPPLIED", "SUBCONTRACT"
    if kind in ("labour",):
        return "NO_MATERIAL", "INTERNAL"
    if kind in ("equipment", "delivery", "disposal", "other"):
        return "CONTRACTOR_PURCHASED", "NO_LABOUR"
    if kind == "subcontract":
        return "SUBCONTRACTOR_SUPPLIED", "SUBCONTRACT"
    # Materials we buy: installed by our crew, or (mixed work) by the subcontractor of the stage's labour part.
    return "CONTRACTOR_PURCHASED", "SUBCONTRACT" if sibling_labour_subcontracted else "INTERNAL"


def save_stage_labour_hours(guided, stage, *, hours_by_item, actor, override_rate="", override_reason="",
                            user_id=None) -> dict:
    """Labour hours for the stage's items: the existing estimate labour-hours service (hours × approved rate)."""
    name = _actor(actor)
    version = _require_editable(guided)
    _leaf(stage)
    from app.services import estimate_labour_hours as labour

    own = {line.id for line in stage_lines(stage, version)}
    entries = {int(k): v for k, v in hours_by_item.items() if int(k) in own}
    try:
        done = labour.save_hours(version, organization_id=guided.organization_id, hours_by_item=entries, actor=name,
                                 override_rate=override_rate, override_reason=override_reason)
    except labour.LabourHoursError as exc:
        raise GuidedEstimatingError(str(exc)) from exc
    _clear_completion(stage)
    _event(guided, "LABOUR_HOURS", actor=name, stage=stage, detail=done["source"], version=version, user_id=user_id)
    _sync_status(stage, version)
    db.session.commit()
    return done


def confirm_stage_routing(guided, stage, *, actor, user_id=None) -> int:
    """Confirm who supplies and builds each line of the stage, from the stage's responsibility (a person presses it)."""
    name = _actor(actor)
    version = _require_editable(guided)
    _leaf(stage)
    done = 0
    for line in stage_lines(stage, version):
        if stage.allowance_line_id and line.id == stage.allowance_line_id:
            continue
        material, labour = routing_for(stage, line)
        _route(line, material=material, labour=labour, actor=name, user_id=user_id)
        done += 1
    _event(guided, "ROUTING_CONFIRMED", actor=name, stage=stage, detail=f"{done} lines", version=version,
           user_id=user_id)
    _sync_status(stage, version)
    db.session.commit()
    return done


# Joel's decisions (24 Oct 2026). An allowance is approved by a person with costing-approval authority, with a
# reason, and the who/when/why is kept in the stage history. An explicit no-cost decision for included work needs the
# instance owner or a System Administrator (the delegated equivalent authority).
ALLOWANCE_REASON_REQUIRED = "Say why this stage uses an allowance (for example: the HVAC quote is still to come)."
ZERO_COST_REFUSED = ("Only the owner or a System Administrator can decide that included work has no cost. Enter "
                     "the stage's costs or approve an allowance, or ask the owner to make this decision.")


def can_authorize_zero_cost(user, organization_id: str) -> bool:
    """The instance owner or a System Administrator of the estimate's company (instance_authority)."""
    if user is None:
        return False
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    return bool(is_instance_owner(user, organization_id) or is_system_administrator(user, organization_id))


def allowance_record(stage) -> Optional[GuidedEstimateEvent]:
    """The stage's latest allowance approval in its history (who, when and the reason)."""
    return (GuidedEstimateEvent.query.filter_by(guided_estimate_id=stage.guided_estimate_id, stage_id=stage.id,
                                                event="ALLOWANCE_APPROVED")
            .order_by(GuidedEstimateEvent.id.desc()).first())


def approve_allowance(guided, stage, *, amount, approver, description="", reason="", user_id=None) -> EstimateLineItem:
    """An explicitly approved allowance for the stage, as an ordinary Allowance line on the estimate."""
    name = _actor(approver)
    version = _require_editable(guided)
    _leaf(stage)
    why = " ".join((reason or "").split())
    if not why:
        raise GuidedEstimatingError(ALLOWANCE_REASON_REQUIRED)
    try:
        value = _money(Decimal(str(amount).replace(",", "").replace("$", "").strip()))
    except (InvalidOperation, ValueError):
        raise GuidedEstimatingError("Enter the allowance amount as a number.") from None
    if value <= 0:
        raise GuidedEstimatingError("An allowance must be more than zero.")
    from app.services.estimate_builder import add_manual_line, update_line_item

    section = section_for(stage, version, create=True)
    line = db.session.get(EstimateLineItem, stage.allowance_line_id) if stage.allowance_line_id else None
    text = (description or f"{stage.section_name} allowance").strip()[:255]
    if line is not None and line.estimate_section_id == section.id:
        update_line_item(line, description=text, quantity=1, unit="allowance", unit_cost=value,
                         notes=f"Allowance approved by {name}. Reason: {why}"[:2000])
    else:
        line = add_manual_line(section, line_type="Allowance", description=text, quantity=1, unit="allowance",
                               unit_cost=value, code="GE-ALLOWANCE",
                               notes=f"Allowance approved by {name}. Reason: {why}"[:2000])
    stage.allowance_line_id = line.id
    stage.allowance_amount = value
    stage.allowance_approved_by = name
    stage.allowance_approved_at = _now()
    _clear_completion(stage)
    _event(guided, "ALLOWANCE_APPROVED", actor=name, stage=stage, to_value=str(value), version=version,
           detail=f"{text}. Reason: {why}", user_id=user_id)
    db.session.commit()
    return line


def authorize_zero_cost(guided, stage, *, reason, approver, user_id=None):
    """The owner (or a System Administrator) records that this included stage has no cost (e.g. owner supplies
    it). Refused for everyone else, including ordinary costing approvers (Joel, 24 Oct 2026)."""
    name = _actor(approver)
    from app.models.user import User

    user = db.session.get(User, user_id) if user_id else None
    if not can_authorize_zero_cost(user, guided.organization_id):
        raise GuidedEstimatingError(ZERO_COST_REFUSED)
    _require_editable(guided)
    _leaf(stage)
    text = (reason or "").strip()
    if not text:
        raise GuidedEstimatingError("Say why this stage has no cost.")
    stage.zero_cost_reason = text[:2000]
    stage.zero_cost_authorized_by = name
    stage.zero_cost_authorized_at = _now()
    _clear_completion(stage)
    _event(guided, "ZERO_COST_AUTHORIZED", actor=name, stage=stage, detail=text, user_id=user_id)
    db.session.commit()


def complete_stage(guided, stage, *, actor, user_id=None) -> Tuple[bool, List[str]]:
    """Complete only with confirmed costs, an approved allowance or an authorized no-cost decision."""
    name = _actor(actor)
    version = _require_editable(guided)
    _leaf(stage)
    check = stage_check(stage, version)
    if not check["bases"]:
        _sync_status(stage, version)
        db.session.commit()
        return False, check["issues"] or ["Add the stage's costs first."]
    basis = check["bases"][0]
    stage.completion_basis = basis
    stage.completed_by = name
    stage.completed_at = _now()
    stage.status = STATUS_COMPLETE
    guided.last_stage_id = stage.id
    _event(guided, "COMPLETED", actor=name, stage=stage, to_value=basis, version=version, user_id=user_id)
    _sync_status(stage, version)
    db.session.commit()
    return True, []


def set_aside_quantities(guided, stage, *, intake_id, actor, user_id=None):
    """The person reviewed a calculation and leaves its remaining quantities off the estimate (recorded)."""
    name = _actor(actor)
    _require_editable(guided)
    calcs = {c.calculation_result_intake_id for c in _stage_calculations(stage)}
    if int(intake_id) not in calcs:
        raise GuidedEstimatingError("That calculation is not on this stage.")
    _event(guided, "INTAKE_SET_ASIDE", actor=name, stage=stage, to_value=str(int(intake_id)),
           detail="Remaining calculated quantities left off the estimate after review.", user_id=user_id)
    db.session.flush()
    _sync_status(stage)
    db.session.commit()


def reopen_stage(guided, stage, *, actor, reason="", user_id=None):
    name = _actor(actor)
    _require_not_committed(guided)
    previous = stage.completion_basis
    _clear_completion(stage)
    stage.status = STATUS_IN_PROGRESS
    _event(guided, "REOPENED", actor=name, stage=stage, from_value=previous, detail=reason, user_id=user_id)
    _sync_status(stage)
    db.session.commit()


# ---------------------------------------------------------------------------------------------- navigation
def ordered_work(guided) -> List[GuidedEstimateStage]:
    """The leaf stages to estimate, in construction order (N/A left out)."""
    return leaf_stages(guided, include_na=False)


def next_stage(guided, after=None) -> Optional[GuidedEstimateStage]:
    """The next stage that is not complete, after ``after`` (wrapping round), or None when all are done."""
    rows = ordered_work(guided)
    if not rows:
        return None
    start = 0
    if after is not None and after in rows:
        start = rows.index(after) + 1
    sequence = rows[start:] + rows[:start]
    for row in sequence:
        if effective_status(row) != STATUS_COMPLETE:
            return row
    return None


def previous_stage(guided, current) -> Optional[GuidedEstimateStage]:
    rows = ordered_work(guided)
    if current not in rows:
        return rows[0] if rows else None
    index = rows.index(current)
    return rows[index - 1] if index > 0 else None


def resume_stage(guided) -> Optional[GuidedEstimateStage]:
    if guided.last_stage_id:
        row = db.session.get(GuidedEstimateStage, guided.last_stage_id)
        if row is not None and row.guided_estimate_id == guided.id and row.responsibility not in (None, RESP_NA):
            return row
    return next_stage(guided)


# ---------------------------------------------------------------------------------------------- tools
def tools_for(stage) -> Tuple[Tool, ...]:
    if stage.responsibility == RESP_SUBCONTRACTED:
        base = (QUOTE, QUOTE_SHEET)
        spec = spec_for(stage)
        if spec is not None and spec.key == "framing":
            base = base + (DECK_TAKEOFF,)  # the merged framing quote request
        return base + (COMPARE, MANUAL)
    part = part_for(stage)
    if part is not None:
        if part.labour_part:
            return (LABOUR, MANUAL)
        return part.tools + (LABOUR, MANUAL) if part.tools else (MANUAL, LABOUR)
    spec = spec_for(stage)
    return spec.internal_tools if spec is not None else (MANUAL, LABOUR)


def tool_limitation(stage) -> str:
    tools = tools_for(stage)
    if stage.responsibility == RESP_INTERNAL and not any(t.kind in ("calculator", "estimate_page", "project_page")
                                                         for t in tools):
        return _NO_CALC
    return ""


# ---------------------------------------------------------------------------------------------- workflow view
def workflow_view(guided) -> dict:
    version = current_version(guided)
    rows = []
    counts = {s: 0 for s in STATUS_LABELS}
    outstanding = []
    for stage in scope_rows(guided):
        children = []
        if stage.is_split:
            for child in stage.children:
                check = stage_check(child, version) if child.responsibility not in (None, RESP_NA) else None
                status = effective_status(child, version, check)
                children.append({"stage": child, "status": status, "status_label": STATUS_LABELS[status],
                                 "check": check, "next": next_action(child, check) if check else ""})
        check = None
        if not stage.is_split and stage.responsibility not in (None, RESP_NA):
            check = stage_check(stage, version)
        status = effective_status(stage, version, check)
        counts[status] += 1
        issues = []
        if check:
            issues = check["issues"]
        for child in children:
            if child["check"]:
                issues += [f"{child['stage'].display_name}: {i}" for i in child["check"]["issues"]]
        if status not in (STATUS_COMPLETE, STATUS_EXCLUDED):
            outstanding.append({"stage": stage, "status_label": STATUS_LABELS[status], "issues": issues})
        total = check["total"] if check else sum((c["check"]["total"] for c in children if c["check"]), Decimal("0"))
        rows.append({"stage": stage, "status": status, "status_label": STATUS_LABELS[status], "check": check,
                     "children": children, "total": _money(total), "issues": issues,
                     "next": next_action(stage, check) if check else (children and "Open a part to estimate it." or ""),
                     "responsibility_label": stage.responsibility_label})
    included = [r for r in rows if r["status"] != STATUS_EXCLUDED]
    done = sum(1 for r in included if r["status"] == STATUS_COMPLETE)
    return {"guided": guided, "version": version, "rows": rows, "counts": counts, "outstanding": outstanding,
            "included": len(included), "done": done,
            "percent": int(round(100 * done / len(included))) if included else 0,
            "editable": version_is_editable(version), "accepted": accepted_proposal(guided),
            "resume": resume_stage(guided) if guided.scope_status == SCOPE_FINALIZED else None,
            "direct_cost": _money(sum((r["total"] for r in rows), Decimal("0"))),
            "waiting_calculations": waiting_calculations(guided), "selected_work": _selected(guided)}


def waiting_calculations(guided):
    """Calculator results kept on the project that have not been given a stage yet (e.g. from Create New Project)."""
    from app.models.project_calculation import REVIEW_AWAITING, ProjectCalculation

    return (ProjectCalculation.query.filter_by(organization_id=guided.organization_id, project_id=guided.project_id,
                                               review_status=REVIEW_AWAITING, guided_stage_id=None)
            .order_by(ProjectCalculation.id.asc()).all())


# ---------------------------------------------------------------------------------------------- gates
def guided_blockers(guided) -> List[str]:
    """Why the guided estimate is not ready for pricing and the proposal. Empty means every stage is resolved."""
    if guided.scope_status != SCOPE_FINALIZED:
        if _selected(guided):
            return ["Add the work this estimate is for."]
        return ["Finalize the construction scope (every stage Internal, Subcontracted or N/A)."]
    out = []
    version = current_version(guided)
    for stage in scope_rows(guided):
        status = effective_status(stage, version)
        if status in (STATUS_COMPLETE, STATUS_EXCLUDED):
            continue
        out.append(f"{stage.display_name} is {STATUS_LABELS[status]}: its costs are not confirmed, and no allowance "
                   f"or exclusion was approved.")
    return out


def guided_issue_blockers(version) -> List[str]:
    """Hook for proposal issuance: a guided estimate's proposal waits until every included stage is resolved."""
    if version is None or version.estimate is None:
        return []
    guided = GuidedEstimate.query.filter_by(estimate_id=version.estimate_id).first()
    if guided is None or current_version(guided) is None or current_version(guided).id != version.id:
        return []
    return ["Guided estimate: " + b for b in guided_blockers(guided)]


# ---------------------------------------------------------------------------------------------- the internal cost document
def internal_cost_document(guided) -> dict:
    """The internal cost estimate by stage, from the estimate's own lines and evidence. Read only."""
    from app.services.estimate_costing import current_costing_snapshot, working_matches_costing_snapshot

    version = current_version(guided)
    stages = []
    totals = {"material": Decimal("0"), "labour": Decimal("0"), "labour_hours": Decimal("0"),
              "subcontract": Decimal("0"), "equipment": Decimal("0"), "delivery": Decimal("0"),
              "allowance": Decimal("0"), "other": Decimal("0")}
    for row in leaf_stages(guided):
        if row.responsibility == RESP_NA:
            stages.append({"stage": row, "excluded": True, "lines": [], "total": Decimal("0"), "issues": [],
                           "status_label": STATUS_LABELS[STATUS_EXCLUDED]})
            continue
        if row.responsibility is None:
            stages.append({"stage": row, "excluded": False, "lines": [], "total": Decimal("0"),
                           "issues": ["Responsibility not decided"], "status_label": "Not decided"})
            continue
        check = stage_check(row, version)
        lines = []
        for item in check["lines"]:
            line = item["line"]
            kind = item["kind"]
            bucket = {"labour": "labour", "subcontract": "subcontract", "equipment": "equipment",
                      "delivery": "delivery", "allowance": "allowance", "material": "material",
                      "disposal": "other", "other": "other"}.get(kind, "other")
            if bucket == "subcontract" or (row.responsibility == RESP_SUBCONTRACTED and bucket == "material"):
                bucket = "subcontract"
            amount = Decimal(line.extended_cost or 0)
            totals[bucket] += amount
            if bucket == "labour":
                totals["labour_hours"] += Decimal(line.quantity or 0)
            quote = item["selected_quote"]
            provenance = _provenance(line, item)
            lines.append({"line": line, "bucket": bucket, "amount": _money(amount), "quote": quote,
                          "provenance": provenance, "missing": item["missing"]})
        status = effective_status(row, version, check)
        stages.append({"stage": row, "excluded": False, "lines": lines, "total": check["total"],
                       "issues": check["issues"], "status_label": STATUS_LABELS[status],
                       "basis": BASIS_LABELS.get(row.completion_basis) if status == STATUS_COMPLETE else None})
    snapshot = current_costing_snapshot(version) if version is not None else None
    approved = bool(snapshot is not None and working_matches_costing_snapshot(version, snapshot))
    direct = _money(sum((s["total"] for s in stages), Decimal("0")))
    from app.services.estimate_economics import economics as project_economics
    from app.services.project_identity import reference_line

    return {"guided": guided, "project": guided.project, "version": version, "stages": stages,
            "reference": reference_line(guided.project),
            "economics": project_economics(version) if version is not None else None,
            "totals": {k: _money(v) if k != "labour_hours" else v for k, v in totals.items()},
            "direct_cost": direct, "costing_approved": approved, "snapshot": snapshot,
            "blockers": guided_blockers(guided), "generated_at": _now(),
            "marking": "INTERNAL — NOT FOR CUSTOMER DISTRIBUTION"}


def _provenance(line, item) -> str:
    kind = item["kind"]
    if kind == "allowance":
        return "Approved allowance"
    if kind == "subcontract":
        quote = item["selected_quote"]
        if quote is not None:
            applied = item["labour_suggestion"] and item["labour_suggestion"]["applied"]
            return (f"Subcontract quote {quote.quote_reference} ({quote.subcontractor.legal_name if quote.subcontractor else ''})"
                    + ("; used on the line by " + (line.costing_override_by or "") if applied else "; not yet used"))
        return "Subcontract: no quote selected"
    if kind == "labour":
        return (line.notes or "Labour hours").split(". Hours")[0]
    if line.contractor_cost_approval_id:
        return "Approved supplier cost"
    if line.cost_item_id:
        return "Company cost library"
    if line.assembly_id:
        return "Reusable work (assembly)"
    return "Manual entry"


# ---------------------------------------------------------------------------------------------- revisions
def start_revision(guided, *, reason, actor, user_id=None) -> EstimateVersion:
    """A new estimate version for changes; the issued or approved one is never overwritten."""
    name = _actor(actor)
    _require_not_committed(guided)
    if guided.estimate is None:
        raise GuidedEstimatingError("There is no estimate to revise yet.")
    text = (reason or "").strip()
    if not text:
        raise GuidedEstimatingError("Say why the estimate is being revised.")
    from app.services.estimates import EstimateServiceError, clone_current_version

    before = current_version(guided)
    try:
        version = clone_current_version(guided.estimate, version_label=f"Revision {(before.version_number or 0) + 1}",
                                        revision_reason=text)
    except EstimateServiceError as exc:
        raise GuidedEstimatingError(str(exc)) from exc
    # Stage-level evidence that pointed at the old version's allowance lines follows the cloned lines.
    for row in leaf_stages(guided):
        if row.allowance_line_id:
            old = db.session.get(EstimateLineItem, row.allowance_line_id)
            new_section = section_for(row, version)
            if old is not None and new_section is not None:
                match = next((l for l in new_section.line_items if (l.code or "") == (old.code or "")
                              and (l.line_type or "") == "Allowance"), None)
                row.allowance_line_id = match.id if match else None
    _event(guided, "REVISION_STARTED", actor=name, detail=text, version=version, user_id=user_id)
    db.session.commit()
    return version


def compare_versions(estimate, older, newer) -> List[dict]:
    """Section-by-section (stage-by-stage) differences between two versions of the same estimate. Read only."""
    def index(version):
        out = {}
        for section in version.sections:
            out[section.name] = {(l.description, l.unit): l for l in section.line_items}
        return out

    a, b = index(older), index(newer)
    rows = []
    for name in list(dict.fromkeys(list(a) + list(b))):
        old_lines, new_lines = a.get(name, {}), b.get(name, {})
        old_total = sum((Decimal(l.extended_cost or 0) for l in old_lines.values()), Decimal("0"))
        new_total = sum((Decimal(l.extended_cost or 0) for l in new_lines.values()), Decimal("0"))
        changes = []
        for key in list(dict.fromkeys(list(old_lines) + list(new_lines))):
            o, n = old_lines.get(key), new_lines.get(key)
            if o is None:
                changes.append(f"Added: {n.description} {n.quantity} {n.unit} at {n.unit_cost}")
            elif n is None:
                changes.append(f"Removed: {o.description}")
            elif (Decimal(o.quantity or 0), Decimal(o.unit_cost or 0)) != (Decimal(n.quantity or 0), Decimal(n.unit_cost or 0)):
                changes.append(f"Changed: {n.description} {o.quantity} → {n.quantity} {n.unit}, "
                               f"unit cost {o.unit_cost} → {n.unit_cost}")
        rows.append({"section": name, "old_total": _money(old_total), "new_total": _money(new_total),
                     "difference": _money(new_total - old_total), "changes": changes})
    return rows


def history(guided, limit=50):
    return (GuidedEstimateEvent.query.filter_by(guided_estimate_id=guided.id)
            .order_by(GuidedEstimateEvent.id.desc()).limit(limit).all())


# ---------------------------------------------------------------------------------------------- build handoff
def handoff(guided) -> dict:
    """Where the approved work structure continues: the same sections become the project's work items."""
    from app.services.work_structure import get_project_seed, list_project_work_elements

    seed = get_project_seed(guided.project_id, organization_id=guided.organization_id)
    elements = list_project_work_elements(guided.project_id, organization_id=guided.organization_id) if seed else []
    subcontracted = [r for r in leaf_stages(guided, include_na=False) if r.responsibility == RESP_SUBCONTRACTED]
    internal = [r for r in leaf_stages(guided, include_na=False) if r.responsibility == RESP_INTERNAL]
    return {"seed": seed, "elements": elements, "subcontracted": subcontracted, "internal": internal,
            "accepted": accepted_proposal(guided)}


__all__ = [name for name in dir() if not name.startswith("_")]
_ = (field, RESPONSIBILITY_LABELS)
