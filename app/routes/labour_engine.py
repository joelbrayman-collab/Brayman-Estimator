"""Office routes for Labour Engine Phase B (FG-008)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.models.historical_estimates import HistoricalLabourItem
from app.models.labour_engine import CANDIDATE_STANDARD_KINDS, EVIDENCE_CLASSES
from app.services.labour_engine import (
    LabourEngineError,
    accept_labour_task_mapping,
    archive_labour_task,
    create_calibration_candidate,
    create_labour_task,
    create_production_rate_standard,
    get_calibration_candidate_or_404,
    get_direct_labour_cost_rate_standard_or_404,
    get_labour_task_mapping_or_404,
    get_labour_task_or_404,
    get_production_rate_standard_or_404,
    list_calibration_candidates,
    list_direct_labour_cost_rate_standards,
    list_labour_task_mappings,
    list_labour_tasks,
    list_production_rate_standards,
    list_unmapped_historical_labour_items,
    mark_mapping_not_labour,
    reject_labour_task_mapping,
    suggest_labour_task_mapping,
    transition_calibration_candidate,
    update_labour_task,
)
from app.services.organizations import get_current_organization_id

labour_engine_bp = Blueprint("labour_engine", __name__, url_prefix="/labour-engine")

DEFAULT_REVIEWER = "Joel Brayman"


def _actor():
    return request.form.get("reviewed_by", "").strip() or DEFAULT_REVIEWER


@labour_engine_bp.route("/")
def index():
    org_id = get_current_organization_id()
    return render_template(
        "labour_engine/index.html",
        tasks=list_labour_tasks(),
        mappings=list_labour_task_mappings()[:25],
        standards=list_production_rate_standards()[:25],
        cost_rates=list_direct_labour_cost_rate_standards(),
        candidates=list_calibration_candidates()[:25],
        unmapped_count=len(list_unmapped_historical_labour_items()),
        organization_id=org_id,
    )


# ----- Labour Tasks -----


@labour_engine_bp.route("/tasks")
def list_tasks():
    include_archived = request.args.get("archived") == "1"
    return render_template(
        "labour_engine/tasks_list.html",
        tasks=list_labour_tasks(include_archived=include_archived),
        include_archived=include_archived,
    )


@labour_engine_bp.route("/tasks/new", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        try:
            task = create_labour_task(
                task_code=request.form.get("task_code", ""),
                canonical_name=request.form.get("canonical_name", ""),
                production_unit=request.form.get("production_unit", ""),
                unit_of_measure=request.form.get("unit_of_measure", ""),
                trade=request.form.get("trade", ""),
                category=request.form.get("category", ""),
                description=request.form.get("description", ""),
                provenance=request.form.get("provenance", ""),
                created_by=_actor(),
            )
            flash(f"Labour Task {task.task_code} created.", "success")
            return redirect(url_for("labour_engine.task_detail", task_id=task.id))
        except LabourEngineError as exc:
            flash(str(exc), "danger")
    return render_template("labour_engine/task_form.html", task=None)


@labour_engine_bp.route("/tasks/<int:task_id>")
def task_detail(task_id):
    try:
        task = get_labour_task_or_404(task_id)
    except LabourEngineError:
        abort(404)
    standards = list_production_rate_standards(labour_task_id=task.id)
    return render_template(
        "labour_engine/task_detail.html",
        task=task,
        standards=standards,
    )


@labour_engine_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    try:
        task = get_labour_task_or_404(task_id)
    except LabourEngineError:
        abort(404)
    if request.method == "POST":
        try:
            update_labour_task(
                task.id,
                canonical_name=request.form.get("canonical_name", ""),
                production_unit=request.form.get("production_unit", ""),
                unit_of_measure=request.form.get("unit_of_measure", ""),
                trade=request.form.get("trade", ""),
                category=request.form.get("category", ""),
                description=request.form.get("description", ""),
                provenance=request.form.get("provenance", ""),
                actor=_actor(),
            )
            flash("Labour Task updated.", "success")
            return redirect(url_for("labour_engine.task_detail", task_id=task.id))
        except LabourEngineError as exc:
            flash(str(exc), "danger")
    return render_template("labour_engine/task_form.html", task=task)


@labour_engine_bp.route("/tasks/<int:task_id>/archive", methods=["POST"])
def archive_task(task_id):
    try:
        archive_labour_task(task_id, actor=_actor())
        flash("Labour Task archived.", "success")
    except LabourEngineError:
        abort(404)
    return redirect(url_for("labour_engine.list_tasks"))


# ----- Mappings -----


@labour_engine_bp.route("/mappings")
def list_mappings():
    status = request.args.get("status", "").strip() or None
    return render_template(
        "labour_engine/mappings_list.html",
        mappings=list_labour_task_mappings(review_status=status),
        unmapped=list_unmapped_historical_labour_items(),
        tasks=list_labour_tasks(),
        status_filter=status or "",
    )


@labour_engine_bp.route("/mappings/suggest", methods=["POST"])
def suggest_mapping():
    try:
        historical_id = request.form.get("historical_labour_item_id", "").strip()
        task_id = request.form.get("labour_task_id", "").strip()
        source_string = request.form.get("source_string", "").strip()
        historical_item = None
        if historical_id:
            historical_item = HistoricalLabourItem.query.filter_by(
                id=int(historical_id),
                organization_id=get_current_organization_id(),
            ).first()
            if not historical_item:
                raise LabourEngineError(
                    "Historical labour item not found in current organization."
                )
            source_string = historical_item.task_description
        mapping = suggest_labour_task_mapping(
            source_string=source_string,
            historical_labour_item_id=historical_item.id if historical_item else None,
            labour_task_id=int(task_id) if task_id else None,
            suggested_by="HUMAN",
            actor=_actor(),
        )
        flash(
            f"Mapping suggested (status {mapping.review_status}; not accepted).",
            "success",
        )
        return redirect(url_for("labour_engine.mapping_detail", mapping_id=mapping.id))
    except LabourEngineError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("labour_engine.list_mappings"))


@labour_engine_bp.route("/mappings/<int:mapping_id>")
def mapping_detail(mapping_id):
    try:
        mapping = get_labour_task_mapping_or_404(mapping_id)
    except LabourEngineError:
        abort(404)
    return render_template(
        "labour_engine/mapping_detail.html",
        mapping=mapping,
        tasks=list_labour_tasks(),
    )


@labour_engine_bp.route("/mappings/<int:mapping_id>/accept", methods=["POST"])
def accept_mapping(mapping_id):
    try:
        task_id = request.form.get("labour_task_id", "").strip()
        accept_labour_task_mapping(
            mapping_id,
            reviewed_by=_actor(),
            review_notes=request.form.get("review_notes", ""),
            labour_task_id=int(task_id) if task_id else None,
        )
        flash("Mapping accepted.", "success")
    except LabourEngineError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("labour_engine.mapping_detail", mapping_id=mapping_id))


@labour_engine_bp.route("/mappings/<int:mapping_id>/reject", methods=["POST"])
def reject_mapping(mapping_id):
    try:
        reject_labour_task_mapping(
            mapping_id,
            reviewed_by=_actor(),
            review_notes=request.form.get("review_notes", ""),
        )
        flash("Mapping rejected.", "success")
    except LabourEngineError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("labour_engine.mapping_detail", mapping_id=mapping_id))


@labour_engine_bp.route("/mappings/<int:mapping_id>/not-labour", methods=["POST"])
def not_labour_mapping(mapping_id):
    try:
        mark_mapping_not_labour(
            mapping_id,
            reviewed_by=_actor(),
            review_notes=request.form.get("review_notes", ""),
        )
        flash("Source string marked NOT_LABOUR. Historical row unchanged.", "success")
    except LabourEngineError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("labour_engine.mapping_detail", mapping_id=mapping_id))


# ----- Production rate standards -----


@labour_engine_bp.route("/standards")
def list_standards():
    return render_template(
        "labour_engine/standards_list.html",
        standards=list_production_rate_standards(),
    )


@labour_engine_bp.route("/standards/new", methods=["GET", "POST"])
def create_standard():
    tasks = list_labour_tasks()
    if request.method == "POST":
        try:
            task_id = request.form.get("labour_task_id", "").strip()
            standard = create_production_rate_standard(
                labour_task_id=int(task_id) if task_id else 0,
                production_rate=request.form.get("production_rate", ""),
                production_unit=request.form.get("production_unit", "") or None,
                unit_of_measure=request.form.get("unit_of_measure", "") or None,
                crew_size_assumption=request.form.get("crew_size_assumption", "") or None,
                hours_per_day_assumption=request.form.get("hours_per_day_assumption", "")
                or None,
                applicable_conditions=request.form.get("applicable_conditions", ""),
                evidence_class=request.form.get("evidence_class", "PROVISIONAL"),
                provenance=request.form.get("provenance", ""),
                created_by=_actor(),
            )
            flash(
                f"Draft production rate standard v{standard.version_number} created. "
                "It is not ORG-APPROVED.",
                "success",
            )
            return redirect(
                url_for("labour_engine.standard_detail", standard_id=standard.id)
            )
        except (LabourEngineError, ValueError) as exc:
            flash(str(exc), "danger")
    return render_template(
        "labour_engine/standard_form.html",
        tasks=tasks,
        evidence_classes=[c for c in EVIDENCE_CLASSES if c != "ORG-APPROVED"],
    )


@labour_engine_bp.route("/standards/<int:standard_id>")
def standard_detail(standard_id):
    try:
        standard = get_production_rate_standard_or_404(standard_id)
    except LabourEngineError:
        abort(404)
    return render_template("labour_engine/standard_detail.html", standard=standard)


# ----- Direct labour cost rates -----


@labour_engine_bp.route("/cost-rates")
def list_cost_rates():
    return render_template(
        "labour_engine/cost_rates_list.html",
        cost_rates=list_direct_labour_cost_rate_standards(),
    )


@labour_engine_bp.route("/cost-rates/<int:rate_id>")
def cost_rate_detail(rate_id):
    try:
        standard = get_direct_labour_cost_rate_standard_or_404(rate_id)
    except LabourEngineError:
        abort(404)
    return render_template("labour_engine/cost_rate_detail.html", standard=standard)


# ----- Candidates -----


@labour_engine_bp.route("/candidates")
def list_candidates():
    state = request.args.get("state", "").strip() or None
    return render_template(
        "labour_engine/candidates_list.html",
        candidates=list_calibration_candidates(state=state),
        state_filter=state or "",
    )


@labour_engine_bp.route("/candidates/new", methods=["GET", "POST"])
def create_candidate():
    tasks = list_labour_tasks()
    if request.method == "POST":
        try:
            task_id = request.form.get("labour_task_id", "").strip()
            candidate = create_calibration_candidate(
                standard_kind=request.form.get("standard_kind", "PRODUCTION_RATE"),
                labour_task_id=int(task_id) if task_id else None,
                proposed_production_rate=request.form.get("proposed_production_rate", "")
                or None,
                proposed_production_unit=request.form.get("proposed_production_unit", "")
                or None,
                proposed_direct_labour_cost_rate=request.form.get(
                    "proposed_direct_labour_cost_rate", ""
                )
                or None,
                proposed_currency=request.form.get("proposed_currency", "CAD"),
                applicable_conditions=request.form.get("applicable_conditions", ""),
                evidence_class=request.form.get("evidence_class", "ORG-HISTORICAL"),
                analysis_summary=request.form.get("analysis_summary", ""),
                supporting_evidence_refs=request.form.get("supporting_evidence_refs", ""),
                created_by=_actor(),
            )
            flash("Calibration candidate created in DRAFT. Not ORG-APPROVED.", "success")
            return redirect(
                url_for("labour_engine.candidate_detail", candidate_id=candidate.id)
            )
        except (LabourEngineError, ValueError) as exc:
            flash(str(exc), "danger")
    return render_template(
        "labour_engine/candidate_form.html",
        tasks=tasks,
        kinds=CANDIDATE_STANDARD_KINDS,
        evidence_classes=EVIDENCE_CLASSES,
    )


@labour_engine_bp.route("/candidates/<int:candidate_id>")
def candidate_detail(candidate_id):
    try:
        candidate = get_calibration_candidate_or_404(candidate_id)
    except LabourEngineError:
        abort(404)
    return render_template("labour_engine/candidate_detail.html", candidate=candidate)


@labour_engine_bp.route("/candidates/<int:candidate_id>/transition", methods=["POST"])
def candidate_transition(candidate_id):
    try:
        transition_calibration_candidate(
            candidate_id,
            request.form.get("new_state", ""),
            actor=_actor(),
            review_notes=request.form.get("review_notes", ""),
        )
        flash("Candidate state updated.", "success")
    except LabourEngineError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("labour_engine.candidate_detail", candidate_id=candidate_id))
