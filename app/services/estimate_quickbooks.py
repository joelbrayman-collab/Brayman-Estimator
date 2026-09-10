"""Estimating-owned QuickBooks-ready package workflow (FG-032 / ADR-049).

Copies frozen Proposal selling lines and costing snapshot cost-class lines.
Does not mutate costing, pricing, Proposal, Scope Delivery, or catalogues.
Slice C entry events are not implemented.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from sqlalchemy import event, inspect as sa_inspect
from sqlalchemy.orm import object_mapper

from app import db
from app.models.estimate import Estimate, EstimateLineItem, EstimateVersion
from app.models.estimate_costing import (
    SOURCE_MANUAL_ALLOWANCE,
    EstimateCostingSnapshotLine,
)
from app.models.estimate_quickbooks import (
    QB_STATUS_DRAFT,
    QB_STATUS_ISSUED,
    QB_STATUS_REVIEWED,
    QB_STATUS_SUPERSEDED,
    QUICKBOOKS_ISSUED_STATUSES,
    EstimateQuickBooksCostClassLine,
    EstimateQuickBooksPackage,
    EstimateQuickBooksSalesLine,
)
from app.models.estimate_scope_delivery import (
    LABOUR_INTERNAL,
    LABOUR_NO_LABOUR,
    LABOUR_OWNER_THIRD_PARTY,
    LABOUR_SUBCONTRACT,
    LABOUR_UNRESOLVED,
    MATERIAL_CONTRACTOR_PURCHASED,
    MATERIAL_NO_MATERIAL,
    MATERIAL_OWNER_SUPPLIED,
    MATERIAL_SUBCONTRACTOR_SUPPLIED,
    MATERIAL_UNRESOLVED,
)
from app.models.organization import Organization
from app.models.pricing_engine import AI_ACTOR_TOKENS, EstimatePricingSnapshot
from app.models.project import Project
from app.models.proposal import Proposal, ProposalLineItem, ProposalSection
from app.services.estimate_costing import (
    PRICING_STATUS_CURRENT,
    current_costing_snapshot,
    pricing_consume_status,
)
from app.services.organizations import get_current_organization_id
from app.services.pricing_engine import as_money
from app.services.estimate_quickbooks_pdf import (
    generate_cost_class_pdf,
    generate_sales_entry_pdf,
)
from app.services.estimate_quickbooks_storage import (
    QuickBooksPackageStorageError,
    read_issued_pdf,
    write_issued_pdf,
)

MONEY_BLOCK = Decimal("0.01")

BLOCK_CROSS_ORG = "CROSS_ORG"
BLOCK_INVALID_RELATIONSHIP = "INVALID_RELATIONSHIP"
BLOCK_NO_CURRENT_COSTING = "NO_CURRENT_COSTING"
BLOCK_PRICING_NOT_CURRENT = "PRICING_NOT_CURRENT"
BLOCK_PRICING_COSTING_MISMATCH = "PRICING_COSTING_IDENTITY_MISMATCH"
BLOCK_PROPOSAL_NOT_ELIGIBLE = "PROPOSAL_NOT_ISSUED_OR_ACCEPTED"
BLOCK_PROPOSAL_PRICING_MISMATCH = "PROPOSAL_PRICING_MISMATCH"
BLOCK_MISSING_CLIENT_IDENTITY = "MISSING_CLIENT_IDENTITY"
BLOCK_MISSING_PROJECT_IDENTITY = "MISSING_PROJECT_IDENTITY"
BLOCK_MISSING_TAX = "MISSING_TAX"
BLOCK_CURRENCY_NOT_CAD = "CURRENCY_NOT_CAD"
BLOCK_UNRESOLVED_ROUTING = "UNRESOLVED_NON_ALLOWANCE_ROUTING"
BLOCK_SALES_LINE_SUM_MISMATCH = "SALES_LINE_SUM_MISMATCH"
BLOCK_COST_CLASS_SUM_MISMATCH = "COST_CLASS_SUM_MISMATCH"
BLOCK_SOURCE_IDENTITY_CHANGED = "SOURCE_IDENTITY_CHANGED"
BLOCK_NOT_REVIEWED = "NOT_REVIEWED"
BLOCK_ISSUED_IMMUTABLE = "ISSUED_IMMUTABLE"
BLOCK_DUPLICATE_ACTIVE_ISSUED = "DUPLICATE_ACTIVE_ISSUED"
BLOCK_STALE_UNISSUED = "STALE_UNISSUED"
BLOCK_NO_PROPOSAL = "NO_ELIGIBLE_PROPOSAL"
BLOCK_NO_PRICING = "NO_PRICING_SNAPSHOT"

WARN_PROPOSAL_ISSUED_NOT_ACCEPTED = "PROPOSAL_ISSUED_NOT_ACCEPTED"
WARN_HYBRID_UNSPLIT = "HYBRID_UNSPLIT"
WARN_ALLOWANCE = "ALLOWANCE"
WARN_BLANK_PROJECT_ADDRESS = "BLANK_PROJECT_ADDRESS"
WARN_CLIENT_NAME_MISMATCH = "CLIENT_NAME_MISMATCH"
WARN_MISSING_PRODUCT_SERVICE = "MISSING_PRODUCT_SERVICE_MAPPING"
WARN_OWNER_ROUTING = "OWNER_ROUTING"

ELIGIBLE_PROPOSAL_STATUSES = frozenset({"Issued", "Accepted"})
_ISSUED_HEADER_MUTABLE = frozenset({"status", "superseded_by_id", "updated_at"})


class EstimateQuickBooksError(Exception):
    """Raised when QuickBooks-ready generation, review, or issue cannot complete."""

    def __init__(self, message, *, block_codes=None, warning_codes=None):
        super().__init__(message)
        self.block_codes = list(block_codes or [])
        self.warning_codes = list(warning_codes or [])


def _org_id(organization_id=None):
    return organization_id or get_current_organization_id()


def _unique_append(bucket, code):
    if code not in bucket:
        bucket.append(code)


def _mismatch(left, right) -> bool:
    return abs(as_money(left) - as_money(right)) >= MONEY_BLOCK


def _assert_human_actor(actor: str, *, action: str) -> str:
    name = (actor or "").strip()
    if not name:
        raise EstimateQuickBooksError(f"{action} requires a human actor.")
    if name.upper() in AI_ACTOR_TOKENS:
        raise EstimateQuickBooksError("AI cannot review or issue a QuickBooks-ready package.")
    return name


def suggest_next_package_number(organization_id, year=None):
    year = year or datetime.utcnow().year
    prefix = f"QB-{year}-"
    pattern = re.compile(rf"^QB-{year}-(\d+)$", re.IGNORECASE)
    max_sequence = 0
    packages = EstimateQuickBooksPackage.query.filter(
        EstimateQuickBooksPackage.organization_id == organization_id,
        EstimateQuickBooksPackage.package_number.ilike(f"{prefix}%"),
    ).all()
    for package in packages:
        match = pattern.match((package.package_number or "").strip())
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))
    return f"{prefix}{max_sequence + 1:04d}"


def _iter_proposal_lines(proposal):
    sections = (
        ProposalSection.query.filter_by(proposal_id=proposal.id)
        .order_by(ProposalSection.sort_order.asc(), ProposalSection.id.asc())
        .all()
    )
    for section in sections:
        lines = (
            ProposalLineItem.query.filter_by(proposal_section_id=section.id)
            .order_by(ProposalLineItem.sort_order.asc(), ProposalLineItem.id.asc())
            .all()
        )
        for line in lines:
            yield line


def _select_proposal(version, proposal=None):
    if proposal is not None:
        return proposal
    rows = (
        Proposal.query.filter_by(estimate_version_id=version.id)
        .order_by(Proposal.id.desc())
        .all()
    )
    accepted = [row for row in rows if row.status == "Accepted"]
    if accepted:
        return accepted[0]
    issued = [row for row in rows if row.status == "Issued"]
    if issued:
        return issued[0]
    return rows[0] if rows else None


def _tax_label(pricing) -> str:
    jurisdiction = (pricing.tax_jurisdiction or "").strip()
    if jurisdiction:
        return jurisdiction
    percent = as_money(pricing.tax_percent)
    return f"Tax {percent}%"


def planned_class_for_routing(material, labour, *, is_allowance: bool) -> str:
    if is_allowance:
        return "ALLOWANCE"
    if material == MATERIAL_CONTRACTOR_PURCHASED and labour == LABOUR_SUBCONTRACT:
        return "HYBRID"
    if material == MATERIAL_OWNER_SUPPLIED or labour == LABOUR_OWNER_THIRD_PARTY:
        return "OWNER"
    if material == MATERIAL_SUBCONTRACTOR_SUPPLIED or labour == LABOUR_SUBCONTRACT:
        return "SUBCONTRACT"
    if labour == LABOUR_INTERNAL and material == MATERIAL_NO_MATERIAL:
        return "INTERNAL_LABOUR"
    if material == MATERIAL_CONTRACTOR_PURCHASED:
        return "MATERIAL"
    if labour == LABOUR_INTERNAL:
        return "INTERNAL_LABOUR"
    if material == MATERIAL_NO_MATERIAL and labour == LABOUR_NO_LABOUR:
        return "NONE"
    return "UNCLASSIFIED"


def _is_allowance_line(costing_line, estimate_line=None) -> bool:
    if (costing_line.line_type or "") == "Allowance":
        return True
    if costing_line.source_kind == SOURCE_MANUAL_ALLOWANCE:
        return True
    if estimate_line is not None and (estimate_line.line_type or "") == "Allowance":
        return True
    return False


def _routing_unresolved(material, labour) -> bool:
    if material in (None, "", MATERIAL_UNRESOLVED):
        return True
    if labour in (None, "", LABOUR_UNRESOLVED):
        return True
    return False


def assemble_quickbooks_preview(
    *,
    project,
    version=None,
    proposal=None,
    organization_id=None,
):
    """Read-only eligibility + copied line DTOs. Does not persist."""
    org_id = _org_id(organization_id)
    block_codes = []
    warning_codes = []
    sales_lines = []
    cost_class_lines = []

    if project is None or project.organization_id != org_id:
        _unique_append(block_codes, BLOCK_CROSS_ORG)
        return {
            "eligible": False,
            "block_codes": block_codes,
            "warning_codes": warning_codes,
            "sales_lines": sales_lines,
            "cost_class_lines": cost_class_lines,
            "header": None,
            "project": project,
            "version": version,
            "proposal": proposal,
        }

    if version is None:
        estimate = (
            Estimate.query.filter_by(project_id=project.id)
            .order_by(Estimate.id.desc())
            .first()
        )
        version = estimate.current_version if estimate is not None else None
    if version is None:
        _unique_append(block_codes, BLOCK_INVALID_RELATIONSHIP)
        return {
            "eligible": False,
            "block_codes": block_codes,
            "warning_codes": warning_codes,
            "sales_lines": sales_lines,
            "cost_class_lines": cost_class_lines,
            "header": None,
            "project": project,
            "version": None,
            "proposal": proposal,
        }

    estimate = version.estimate
    if (
        estimate is None
        or estimate.project_id != project.id
        or estimate.project.organization_id != org_id
    ):
        _unique_append(block_codes, BLOCK_INVALID_RELATIONSHIP)

    org = db.session.get(Organization, org_id)
    if org is None or (org.currency or "").upper() != "CAD":
        _unique_append(block_codes, BLOCK_CURRENCY_NOT_CAD)

    costing = current_costing_snapshot(version)
    if costing is None:
        _unique_append(block_codes, BLOCK_NO_CURRENT_COSTING)
    elif costing.organization_id != org_id or costing.project_id != project.id:
        _unique_append(block_codes, BLOCK_CROSS_ORG)

    pricing = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).first()
    if pricing is None:
        _unique_append(block_codes, BLOCK_NO_PRICING)
    elif pricing.organization_id != org_id:
        _unique_append(block_codes, BLOCK_CROSS_ORG)

    consume = pricing_consume_status(version)
    if consume != PRICING_STATUS_CURRENT:
        _unique_append(block_codes, BLOCK_PRICING_NOT_CURRENT)
    if (
        costing is not None
        and pricing is not None
        and pricing.costing_snapshot_id != costing.id
    ):
        _unique_append(block_codes, BLOCK_PRICING_COSTING_MISMATCH)

    proposal = _select_proposal(version, proposal=proposal)
    if proposal is None:
        _unique_append(block_codes, BLOCK_NO_PROPOSAL)
    else:
        if proposal.estimate_version_id != version.id:
            _unique_append(block_codes, BLOCK_INVALID_RELATIONSHIP)
        if proposal.estimate_id != estimate.id:
            _unique_append(block_codes, BLOCK_INVALID_RELATIONSHIP)
        if proposal.status not in ELIGIBLE_PROPOSAL_STATUSES:
            _unique_append(block_codes, BLOCK_PROPOSAL_NOT_ELIGIBLE)
        elif proposal.status == "Issued":
            _unique_append(warning_codes, WARN_PROPOSAL_ISSUED_NOT_ACCEPTED)

    client = project.client
    if project.name is None or not str(project.name).strip():
        _unique_append(block_codes, BLOCK_MISSING_PROJECT_IDENTITY)
    client_name = ""
    if proposal is not None:
        client_name = (proposal.client_name or "").strip()
    if not client_name and client is not None:
        client_name = (client.name or "").strip()
    if not client_name:
        _unique_append(block_codes, BLOCK_MISSING_CLIENT_IDENTITY)
    if (
        proposal is not None
        and client is not None
        and (client.name or "").strip()
        and (proposal.client_name or "").strip()
        and (client.name or "").strip() != (proposal.client_name or "").strip()
    ):
        _unique_append(warning_codes, WARN_CLIENT_NAME_MISMATCH)

    address = ""
    if proposal is not None:
        address = (proposal.project_address or "").strip()
    if not address:
        address = (project.address or "").strip()
    if not address:
        _unique_append(warning_codes, WARN_BLANK_PROJECT_ADDRESS)

    if pricing is not None and pricing.tax_percent is None:
        _unique_append(block_codes, BLOCK_MISSING_TAX)

    tax_label = _tax_label(pricing) if pricing is not None else ""
    if pricing is not None and not (pricing.tax_jurisdiction or "").strip():
        if pricing.tax_percent is None:
            _unique_append(block_codes, BLOCK_MISSING_TAX)

    if costing is not None:
        for costing_line in costing.lines:
            estimate_line = db.session.get(
                EstimateLineItem, costing_line.estimate_line_item_id
            )
            is_allowance = _is_allowance_line(costing_line, estimate_line)
            material = costing_line.material_procurement
            labour = costing_line.labour_delivery
            line_warns = []
            if is_allowance:
                _unique_append(warning_codes, WARN_ALLOWANCE)
                _unique_append(line_warns, WARN_ALLOWANCE)
            elif _routing_unresolved(material, labour):
                _unique_append(block_codes, BLOCK_UNRESOLVED_ROUTING)
            is_hybrid = (
                material == MATERIAL_CONTRACTOR_PURCHASED
                and labour == LABOUR_SUBCONTRACT
            )
            if is_hybrid:
                _unique_append(warning_codes, WARN_HYBRID_UNSPLIT)
                _unique_append(line_warns, WARN_HYBRID_UNSPLIT)
            if (
                material == MATERIAL_OWNER_SUPPLIED
                or labour == LABOUR_OWNER_THIRD_PARTY
            ):
                _unique_append(warning_codes, WARN_OWNER_ROUTING)
                _unique_append(line_warns, WARN_OWNER_ROUTING)
            description = ""
            if estimate_line is not None:
                description = estimate_line.description or ""
            cost_class_lines.append(
                {
                    "source_costing_snapshot_line_id": costing_line.id,
                    "description": description,
                    "quantity": costing_line.quantity,
                    "unit": costing_line.unit,
                    "extended_cost": as_money(costing_line.extended_cost),
                    "material_procurement": material,
                    "labour_delivery": labour,
                    "planned_class": planned_class_for_routing(
                        material, labour, is_allowance=is_allowance
                    ),
                    "is_hybrid": is_hybrid,
                    "is_allowance": is_allowance,
                    "warning_codes": line_warns,
                }
            )

    if proposal is not None:
        missing_product = False
        for index, line in enumerate(_iter_proposal_lines(proposal)):
            product_label = ""
            if not product_label:
                missing_product = True
            sales_lines.append(
                {
                    "source_proposal_line_id": line.id,
                    "sort_order": index,
                    "description": line.description or "",
                    "quantity": line.quantity,
                    "unit": line.unit,
                    "unit_price": line.unit_price,
                    "amount": as_money(line.extended_price),
                    "tax_label": tax_label,
                    "product_service_label": product_label,
                }
            )
        if missing_product:
            _unique_append(warning_codes, WARN_MISSING_PRODUCT_SERVICE)

    header = None
    if (
        costing is not None
        and pricing is not None
        and proposal is not None
        and estimate is not None
    ):
        header = {
            "organization_id": org_id,
            "project_id": project.id,
            "estimate_id": estimate.id,
            "estimate_version_id": version.id,
            "costing_snapshot_id": costing.id,
            "pricing_snapshot_id": pricing.id,
            "proposal_id": proposal.id,
            "currency": "CAD",
            "tax_percent": pricing.tax_percent,
            "pre_tax": as_money(pricing.pre_tax_selling_price),
            "tax_amount": as_money(pricing.tax_amount),
            "customer_total": as_money(pricing.customer_total),
            "approved_direct_cost_total": as_money(costing.approved_direct_cost_total),
            "client_name": client_name or (proposal.client_name or ""),
            "client_company": proposal.client_company,
            "project_name": project.name,
            "project_number": project.project_number,
            "project_address": address or None,
            "estimate_number": estimate.estimate_number,
            "estimate_version_number": version.version_number,
            "proposal_number": proposal.proposal_number,
            "proposal_status_at_freeze": proposal.status,
            "tax_jurisdiction": pricing.tax_jurisdiction,
            "tax_label": tax_label,
            "customer_message": proposal.intro_text,
            "estimate_date": (
                proposal.issued_at.date()
                if proposal.issued_at is not None
                else proposal.created_at.date()
                if proposal.created_at is not None
                else None
            ),
        }
        if _mismatch(header["pre_tax"], pricing.pre_tax_selling_price):
            _unique_append(block_codes, BLOCK_PROPOSAL_PRICING_MISMATCH)
        if _mismatch(header["tax_amount"], pricing.tax_amount):
            _unique_append(block_codes, BLOCK_PROPOSAL_PRICING_MISMATCH)
        if _mismatch(header["customer_total"], pricing.customer_total):
            _unique_append(block_codes, BLOCK_PROPOSAL_PRICING_MISMATCH)
        if _mismatch(proposal.subtotal, pricing.pre_tax_selling_price):
            _unique_append(block_codes, BLOCK_PROPOSAL_PRICING_MISMATCH)
        if _mismatch(proposal.tax_amount, pricing.tax_amount):
            _unique_append(block_codes, BLOCK_PROPOSAL_PRICING_MISMATCH)
        if _mismatch(proposal.total, pricing.customer_total):
            _unique_append(block_codes, BLOCK_PROPOSAL_PRICING_MISMATCH)
        sales_sum = as_money(sum((row["amount"] for row in sales_lines), Decimal("0")))
        cost_sum = as_money(
            sum((row["extended_cost"] for row in cost_class_lines), Decimal("0"))
        )
        if _mismatch(sales_sum, header["pre_tax"]):
            _unique_append(block_codes, BLOCK_SALES_LINE_SUM_MISMATCH)
        if _mismatch(cost_sum, header["approved_direct_cost_total"]):
            _unique_append(block_codes, BLOCK_COST_CLASS_SUM_MISMATCH)

    eligible = not block_codes
    return {
        "eligible": eligible,
        "block_codes": block_codes,
        "warning_codes": warning_codes,
        "sales_lines": sales_lines,
        "cost_class_lines": cost_class_lines,
        "header": header,
        "project": project,
        "estimate": estimate if version is not None else None,
        "version": version,
        "proposal": proposal,
        "costing": costing if version is not None else None,
        "pricing": pricing if version is not None else None,
        "pricing_consume_status": consume if version is not None else None,
    }


def list_packages_for_project(project_id, organization_id=None):
    org_id = _org_id(organization_id)
    return (
        EstimateQuickBooksPackage.query.filter_by(
            project_id=project_id,
            organization_id=org_id,
        )
        .order_by(EstimateQuickBooksPackage.id.desc())
        .all()
    )


def get_package_or_404(package_id, *, project_id, organization_id=None):
    org_id = _org_id(organization_id)
    package = EstimateQuickBooksPackage.query.filter_by(
        id=package_id,
        project_id=project_id,
        organization_id=org_id,
    ).first_or_404()
    return package


def _unissued_for_version(version_id, organization_id):
    return (
        EstimateQuickBooksPackage.query.filter(
            EstimateQuickBooksPackage.estimate_version_id == version_id,
            EstimateQuickBooksPackage.organization_id == organization_id,
            EstimateQuickBooksPackage.status.in_(
                (QB_STATUS_DRAFT, QB_STATUS_REVIEWED)
            ),
        )
        .order_by(EstimateQuickBooksPackage.id.desc())
        .first()
    )


def _issued_for_pins(header):
    return EstimateQuickBooksPackage.query.filter_by(
        estimate_version_id=header["estimate_version_id"],
        costing_snapshot_id=header["costing_snapshot_id"],
        pricing_snapshot_id=header["pricing_snapshot_id"],
        proposal_id=header["proposal_id"],
        status=QB_STATUS_ISSUED,
    ).first()


def _replace_lines(package, preview):
    if package.status in QUICKBOOKS_ISSUED_STATUSES:
        raise EstimateQuickBooksError(
            "Issued QuickBooks packages cannot be rewritten.",
            block_codes=[BLOCK_ISSUED_IMMUTABLE],
        )
    package.sales_lines.clear()
    package.cost_class_lines.clear()
    db.session.flush()
    for index, row in enumerate(preview["sales_lines"]):
        package.sales_lines.append(
            EstimateQuickBooksSalesLine(
                sort_order=index,
                source_proposal_line_id=row["source_proposal_line_id"],
                description=row["description"],
                quantity=row["quantity"],
                unit=row["unit"],
                unit_price=row["unit_price"],
                amount=row["amount"],
                tax_label=row["tax_label"],
                product_service_label=row["product_service_label"] or None,
            )
        )
    for index, row in enumerate(preview["cost_class_lines"]):
        package.cost_class_lines.append(
            EstimateQuickBooksCostClassLine(
                sort_order=index,
                source_costing_snapshot_line_id=row["source_costing_snapshot_line_id"],
                description=row["description"],
                quantity=row["quantity"],
                unit=row["unit"],
                extended_cost=row["extended_cost"],
                material_procurement=row["material_procurement"],
                labour_delivery=row["labour_delivery"],
                planned_class=row["planned_class"],
                is_hybrid=bool(row["is_hybrid"]),
                is_allowance=bool(row["is_allowance"]),
                warning_codes=row["warning_codes"] or None,
            )
        )


def _apply_header(package, header, warning_codes, block_codes):
    for key, value in header.items():
        setattr(package, key, value)
    package.warning_codes = list(warning_codes)
    package.block_codes = list(block_codes)


def _require_preview(preview, *, action):
    if preview.get("eligible") and preview.get("header"):
        return preview
    codes = list(preview.get("block_codes") or [BLOCK_INVALID_RELATIONSHIP])
    raise EstimateQuickBooksError(
        f"{action} is blocked until eligibility and reconciliation pass.",
        block_codes=codes,
        warning_codes=preview.get("warning_codes") or [],
    )


def save_reviewed_package(
    *,
    project,
    version=None,
    proposal=None,
    actor,
    actor_user_id=None,
    organization_id=None,
    commit=True,
):
    actor_name = _assert_human_actor(actor, action="Review QuickBooks-ready package")
    org_id = _org_id(organization_id)
    preview = assemble_quickbooks_preview(
        project=project,
        version=version,
        proposal=proposal,
        organization_id=org_id,
    )
    _require_preview(preview, action="Review")
    header = preview["header"]
    package = _unissued_for_version(header["estimate_version_id"], org_id)
    now = datetime.utcnow()
    if package is None:
        package = EstimateQuickBooksPackage(
            package_number=suggest_next_package_number(org_id),
            status=QB_STATUS_DRAFT,
        )
        db.session.add(package)
    elif package.status in QUICKBOOKS_ISSUED_STATUSES:
        raise EstimateQuickBooksError(
            "Issued QuickBooks packages cannot be rewritten.",
            block_codes=[BLOCK_ISSUED_IMMUTABLE],
        )
    _apply_header(package, header, preview["warning_codes"], preview["block_codes"])
    db.session.flush()
    _replace_lines(package, preview)
    package.status = QB_STATUS_REVIEWED
    package.reviewed_by_user_id = actor_user_id
    package.reviewed_by_display_name = actor_name
    package.reviewed_at = now
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return package


def regenerate_draft(
    *,
    project,
    version=None,
    proposal=None,
    actor,
    organization_id=None,
    commit=True,
):
    """Replace unissued draft/reviewed from current sources. Does not issue."""
    _assert_human_actor(actor, action="Regenerate QuickBooks-ready package")
    org_id = _org_id(organization_id)
    preview = assemble_quickbooks_preview(
        project=project,
        version=version,
        proposal=proposal,
        organization_id=org_id,
    )
    _require_preview(preview, action="Regenerate")
    header = preview["header"]
    package = _unissued_for_version(header["estimate_version_id"], org_id)
    if package is None:
        package = EstimateQuickBooksPackage(
            package_number=suggest_next_package_number(org_id),
            status=QB_STATUS_DRAFT,
        )
        db.session.add(package)
    _apply_header(package, header, preview["warning_codes"], preview["block_codes"])
    db.session.flush()
    _replace_lines(package, preview)
    package.status = QB_STATUS_DRAFT
    package.reviewed_by_user_id = None
    package.reviewed_by_display_name = None
    package.reviewed_at = None
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return package


def _pins_match(package, header) -> bool:
    return (
        package.costing_snapshot_id == header["costing_snapshot_id"]
        and package.pricing_snapshot_id == header["pricing_snapshot_id"]
        and package.proposal_id == header["proposal_id"]
        and package.estimate_version_id == header["estimate_version_id"]
    )


def issue_package(
    package,
    *,
    actor,
    actor_user_id=None,
    supersede_package_id=None,
    organization_id=None,
    commit=True,
):
    actor_name = _assert_human_actor(actor, action="Issue QuickBooks-ready package")
    org_id = _org_id(organization_id)
    if package.organization_id != org_id:
        raise EstimateQuickBooksError(
            "QuickBooks package does not belong to this organization.",
            block_codes=[BLOCK_CROSS_ORG],
        )
    if package.status in QUICKBOOKS_ISSUED_STATUSES:
        raise EstimateQuickBooksError(
            "Issued QuickBooks packages are immutable.",
            block_codes=[BLOCK_ISSUED_IMMUTABLE],
        )
    if package.status != QB_STATUS_REVIEWED:
        raise EstimateQuickBooksError(
            "Review the QuickBooks-ready package before issue.",
            block_codes=[BLOCK_NOT_REVIEWED],
        )

    project = db.session.get(Project, package.project_id)
    version = db.session.get(EstimateVersion, package.estimate_version_id)
    proposal = db.session.get(Proposal, package.proposal_id)
    preview = assemble_quickbooks_preview(
        project=project,
        version=version,
        proposal=proposal,
        organization_id=org_id,
    )
    _require_preview(preview, action="Issue")
    header = preview["header"]
    if not _pins_match(package, header):
        raise EstimateQuickBooksError(
            "Current costing, pricing, or Proposal identity changed. "
            "Regenerate the QuickBooks-ready package from the current sources.",
            block_codes=[BLOCK_SOURCE_IDENTITY_CHANGED, BLOCK_STALE_UNISSUED],
            warning_codes=preview["warning_codes"],
        )

    existing_issued = _issued_for_pins(header)
    if existing_issued is not None and existing_issued.id != package.id:
        if supersede_package_id != existing_issued.id:
            raise EstimateQuickBooksError(
                "An ISSUED QuickBooks-ready package already exists for these "
                "source pins. Explicitly supersede it before issuing another.",
                block_codes=[BLOCK_DUPLICATE_ACTIVE_ISSUED],
            )

    _apply_header(package, header, preview["warning_codes"], preview["block_codes"])
    _replace_lines(package, preview)
    db.session.flush()

    with db.session.no_autoflush:
        package.status = QB_STATUS_ISSUED
        package.issued_by_user_id = actor_user_id
        package.issued_by_display_name = actor_name
        package.issued_at = datetime.utcnow()
        sales_pdf = generate_sales_entry_pdf(package).getvalue()
        cost_pdf = generate_cost_class_pdf(package).getvalue()
        try:
            sales_key, sales_sha = write_issued_pdf(
                organization_id=org_id,
                package_id=package.id,
                kind="sales",
                data=sales_pdf,
            )
            cost_key, cost_sha = write_issued_pdf(
                organization_id=org_id,
                package_id=package.id,
                kind="cost_class",
                data=cost_pdf,
            )
        except QuickBooksPackageStorageError as exc:
            db.session.rollback()
            raise EstimateQuickBooksError(str(exc)) from exc
        package.sales_storage_key = sales_key
        package.sales_pdf_sha256 = sales_sha
        package.cost_class_storage_key = cost_key
        package.cost_class_pdf_sha256 = cost_sha
        if existing_issued is not None and existing_issued.id != package.id:
            existing_issued.status = QB_STATUS_SUPERSEDED
            existing_issued.superseded_by_id = package.id

    if commit:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    else:
        db.session.flush()
    return package


def issued_pdf_bytes(package, kind: str, *, organization_id=None) -> bytes:
    org_id = _org_id(organization_id)
    if package.organization_id != org_id:
        raise EstimateQuickBooksError(
            "QuickBooks package does not belong to this organization.",
            block_codes=[BLOCK_CROSS_ORG],
        )
    if package.status not in QUICKBOOKS_ISSUED_STATUSES:
        raise EstimateQuickBooksError("PDFs are stored only after issue.")
    if kind == "sales":
        key = package.sales_storage_key
        expected = package.sales_pdf_sha256
    elif kind in ("cost_class", "cost-class"):
        key = package.cost_class_storage_key
        expected = package.cost_class_pdf_sha256
        kind = "cost_class"
    else:
        raise EstimateQuickBooksError("Unknown QuickBooks artifact kind.")
    data = read_issued_pdf(key)
    from app.services.estimate_quickbooks_storage import sha256_hex

    digest = sha256_hex(data)
    if expected and digest != expected:
        raise EstimateQuickBooksError("Stored QuickBooks PDF hash does not match.")
    return data


def sales_artifact_text(package) -> str:
    """Plain text used by privacy tests for Artifact A."""
    parts = [
        "INTERNAL ENTRY REFERENCE",
        "QUICKBOOKS ESTIMATE / ENTRY SHEET",
        package.client_name or "",
        package.project_name or "",
        package.project_number or "",
        package.proposal_number or "",
        str(package.pre_tax),
        str(package.tax_amount),
        str(package.customer_total),
    ]
    for line in package.sales_lines:
        parts.extend(
            [
                line.description or "",
                str(line.unit_price),
                str(line.amount),
                line.product_service_label or "",
            ]
        )
    return "\n".join(parts)


def cost_class_artifact_text(package) -> str:
    parts = [
        "INTERNAL / PLANNED COST-CLASSIFICATION",
        package.project_name or "",
        str(package.approved_direct_cost_total),
        str(package.costing_snapshot_id),
    ]
    for line in package.cost_class_lines:
        parts.extend(
            [
                line.description or "",
                str(line.extended_cost),
                line.material_procurement or "",
                line.labour_delivery or "",
                line.planned_class or "",
            ]
        )
    return "\n".join(parts)


def _issued_package_from_target(target):
    if isinstance(target, EstimateQuickBooksPackage):
        return target if target.status in QUICKBOOKS_ISSUED_STATUSES else None
    package = getattr(target, "package", None)
    if isinstance(package, EstimateQuickBooksPackage):
        return package if package.status in QUICKBOOKS_ISSUED_STATUSES else None
    return None


@event.listens_for(EstimateQuickBooksPackage, "before_update")
def _reject_issued_header_rewrite(mapper, connection, target):
    state = sa_inspect(target)
    if state.unmodified == set(object_mapper(target).column_attrs.keys()):
        return
    hist = state.attrs.status.history
    prior_status = None
    if hist.has_changes() and hist.deleted:
        prior_status = hist.deleted[0]
    elif not hist.has_changes():
        prior_status = target.status
    if prior_status not in QUICKBOOKS_ISSUED_STATUSES:
        return
    changed = {attr.key for attr in state.attrs if attr.history.has_changes()}
    if changed <= _ISSUED_HEADER_MUTABLE and target.status in (
        QB_STATUS_SUPERSEDED,
        "VOID",
        QB_STATUS_ISSUED,
    ):
        return
    raise EstimateQuickBooksError(
        "Issued QuickBooks packages are immutable.",
        block_codes=[BLOCK_ISSUED_IMMUTABLE],
    )


@event.listens_for(EstimateQuickBooksSalesLine, "before_update")
@event.listens_for(EstimateQuickBooksSalesLine, "before_delete")
@event.listens_for(EstimateQuickBooksCostClassLine, "before_update")
@event.listens_for(EstimateQuickBooksCostClassLine, "before_delete")
def _reject_issued_line_rewrite(mapper, connection, target):
    package = _issued_package_from_target(target)
    if package is None and target.package_id:
        package = db.session.get(EstimateQuickBooksPackage, target.package_id)
        if package is not None and package.status not in QUICKBOOKS_ISSUED_STATUSES:
            package = None
    if package is None:
        return
    raise EstimateQuickBooksError(
        "Issued QuickBooks package lines are immutable.",
        block_codes=[BLOCK_ISSUED_IMMUTABLE],
    )
