"""Routes for Historical Estimates Ingestion and Evidence Review (FG-006)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.services.historical_review import (
    EVIDENCE_TIER_LABELS,
    REVIEW_STATUS_LABELS,
    VALID_EVIDENCE_TIERS,
    VALID_REVIEW_STATUSES,
    HistoricalReviewError,
    get_historical_estimate_or_404,
    list_historical_estimates,
    list_historical_workbooks,
    record_review_decision,
)
from app.services.historical_ingestion.upload import (
    process_upload_files,
)
from app.services.auth import form_actor

bp = Blueprint("historical_estimates", __name__, url_prefix="/historical-estimates")


@bp.route("/")
def index():
    workbooks = list_historical_workbooks()
    estimates = list_historical_estimates()
    return render_template(
        "historical_estimates/index.html",
        workbooks=workbooks,
        estimates=estimates,
        upload_summary=None,
        evidence_tier_labels=EVIDENCE_TIER_LABELS,
        review_status_labels=REVIEW_STATUS_LABELS,
    )


@bp.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("workbooks")
    summary = process_upload_files(files)
    workbooks = list_historical_workbooks()
    estimates = list_historical_estimates()
    if summary.files_received == 0:
        flash("No files were received. Select one or more .xlsx / .xlsm workbooks.", "danger")
    return render_template(
        "historical_estimates/index.html",
        workbooks=workbooks,
        estimates=estimates,
        upload_summary=summary,
        evidence_tier_labels=EVIDENCE_TIER_LABELS,
        review_status_labels=REVIEW_STATUS_LABELS,
    )


@bp.route("/<int:estimate_id>")
def detail(estimate_id: int):
    try:
        estimate = get_historical_estimate_or_404(estimate_id)
    except HistoricalReviewError:
        abort(404)

    return render_template(
        "historical_estimates/detail.html",
        estimate=estimate,
        review_statuses=VALID_REVIEW_STATUSES,
        evidence_tiers=VALID_EVIDENCE_TIERS,
        evidence_tier_labels=EVIDENCE_TIER_LABELS,
        review_status_labels=REVIEW_STATUS_LABELS,
    )


@bp.route("/<int:estimate_id>/review", methods=["POST"])
def post_review(estimate_id: int):
    try:
        review_status = request.form.get("review_status", "").strip()
        evidence_tier = request.form.get("evidence_tier", "").strip()
        reviewed_by = form_actor("reviewed_by")
        review_notes = request.form.get("review_notes", "").strip()

        record_review_decision(
            estimate_id=estimate_id,
            review_status=review_status,
            evidence_tier=evidence_tier,
            reviewed_by=reviewed_by,
            review_notes=review_notes,
        )
        flash("Historical evidence review decision saved successfully.", "success")
    except HistoricalReviewError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error saving review decision: {e}", "danger")

    return redirect(url_for("historical_estimates.detail", estimate_id=estimate_id))
