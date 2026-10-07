"""Project contract review. Uses the existing generation service.

Does not send a signing link. Does not live in the project hub assembler.
"""

from io import BytesIO

from flask import flash, redirect, render_template, request, send_file, url_for

from app.models.estimate import Estimate
from app.models.project import Project
from app.models.project_contract import GeneratedProjectContract
from app.models.proposal import Proposal
from app.presentation import contractor_copy
from app.routes.projects import projects_bp
from app.services.auth import current_actor_display_name
from app.services.contract_generation import (
    ELIGIBLE_PROPOSAL_STATUSES,
    ELIGIBLE_VERSION_STATUSES,
    generate_project_contract,
    retrieve_generated_contract_docx,
)
from app.services.brayman_v1_contract_presentation import (
    BRAYMAN_V1_PRESENTATION_MEDIA_TYPE,
    brayman_v1_presentation_master,
)
from app.services.legal_content import select_legal_content_package_for_project
from app.services.organizations import get_current_organization_id

_BLOCK_SENTENCES = {
    "MISSING_COMMERCIAL_FACTS": (
        "The project needs a customer, a project name, a street address, "
        "an estimate number, and a contract amount before a contract can be generated."
    ),
    "JURISDICTION_UNRESOLVED": contractor_copy.CONTRACT_LOCATION_INCOMPLETE,
    "NO_ACTIVE_PACKAGE": contractor_copy.CONTRACT_NO_ACTIVE_PACKAGE,
    "PACKAGE_NOT_ACTIVE": contractor_copy.CONTRACT_NO_ACTIVE_PACKAGE,
    "PACKAGE_NOT_EFFECTIVE": contractor_copy.CONTRACT_PACKAGE_NOT_USABLE,
    "PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT": contractor_copy.CONTRACT_NO_ACTIVE_PACKAGE,
    "DRAFT_ESTIMATE_VERSION": (
        "The estimate is still a draft. Issue and lock it before generating a contract."
    ),
    "ESTIMATE_VERSION_NOT_LOCKED": (
        "The estimate is not locked. Lock the issued estimate before generating a contract."
    ),
    "ESTIMATE_VERSION_NOT_ELIGIBLE": (
        "The estimate must be issued or accepted before a contract can be generated."
    ),
    "PROPOSAL_NOT_ELIGIBLE": (
        "The proposal must be issued or accepted before a contract can be generated."
    ),
    "PROPOSAL_REQUIRED": (
        "Choose the proposal this contract is for. A contract is not generated "
        "without that proposal."
    ),
}


def _eligible_pairs(project_id: int):
    pairs = []
    estimates = Estimate.query.filter_by(project_id=project_id).all()
    for estimate in estimates:
        for version in estimate.versions:
            if version.status not in ELIGIBLE_VERSION_STATUSES or not version.is_locked:
                continue
            proposals = Proposal.query.filter_by(estimate_version_id=version.id).all()
            for proposal in proposals:
                if proposal.status not in ELIGIBLE_PROPOSAL_STATUSES:
                    continue
                pairs.append(
                    {
                        "estimate_version_id": version.id,
                        "proposal_id": proposal.id,
                        "estimate_number": estimate.estimate_number,
                        "proposal_number": proposal.proposal_number,
                        "proposal_status": proposal.status,
                        "total": version.total,
                    }
                )
    return pairs


def _contracts(project_id: int, organization_id: str):
    return (
        GeneratedProjectContract.query.filter_by(
            project_id=project_id,
            organization_id=organization_id,
        )
        .order_by(GeneratedProjectContract.generated_at.desc(), GeneratedProjectContract.id.desc())
        .all()
    )


@projects_bp.route("/<int:id>/contract", methods=["GET"])
def review_contract(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    selection = select_legal_content_package_for_project(project.id)
    contract_copy = contractor_copy.contract_selection_copy(selection)
    return render_template(
        "projects/contract_review.html",
        project=project,
        contract_copy=contract_copy,
        pairs=_eligible_pairs(project.id),
        contracts=_contracts(project.id, org_id),
        generated_note=contractor_copy.CONTRACT_GENERATED_NOT_SIGNED,
    )


@projects_bp.route("/<int:id>/contract/generate", methods=["POST"])
def generate_contract(id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    version_id = request.form.get("estimate_version_id", type=int)
    proposal_id = request.form.get("proposal_id", type=int)
    actor = current_actor_display_name(fallback="Brayman Construction")
    result = generate_project_contract(
        project.id,
        version_id or 0,
        organization_id=org_id,
        presentation_master=brayman_v1_presentation_master(),
        actor_identifier=actor,
        actor_kind="HUMAN",
        proposal_id=proposal_id,
    )
    if not result.generated:
        sentence = _BLOCK_SENTENCES.get(
            result.block_code or "",
            "The contract was not generated.",
        )
        flash(f"{sentence} Office detail: {result.block_code}.", "error")
    else:
        flash(contractor_copy.CONTRACT_GENERATED_NOT_SIGNED, "success")
    return redirect(url_for("projects.review_contract", id=project.id))


@projects_bp.route("/<int:id>/contract/<int:contract_id>/download", methods=["GET"])
def download_generated_contract(id, contract_id):
    org_id = get_current_organization_id()
    project = Project.query.filter_by(id=id, organization_id=org_id).first_or_404()
    contract = GeneratedProjectContract.query.filter_by(
        id=contract_id,
        project_id=project.id,
        organization_id=org_id,
    ).first_or_404()
    snapshot = contract.snapshot
    if snapshot is None:
        flash("The contract snapshot is missing.", "error")
        return redirect(url_for("projects.review_contract", id=project.id))
    data = retrieve_generated_contract_docx(snapshot)
    if not data:
        flash("The generated contract file is not available.", "error")
        return redirect(url_for("projects.review_contract", id=project.id))
    media_type = contract.artifact_media_type or ""
    pdf = media_type == BRAYMAN_V1_PRESENTATION_MEDIA_TYPE
    return send_file(
        BytesIO(data),
        mimetype=media_type
        or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=not pdf,
        download_name=(
            f"{contract.contract_number}.pdf"
            if pdf
            else f"{contract.contract_number}.docx"
        ),
    )
