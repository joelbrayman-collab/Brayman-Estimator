"""Estimating-owned scope delivery routing (FG-031 Slice A / ADR-048)."""

from datetime import datetime

from app import db
from app.models.cost_item import CostItem
from app.models.estimate import EstimateLineItem
from app.models.estimate_scope_delivery import (
    LABOUR_DELIVERY_VALUES,
    LABOUR_INTERNAL,
    LABOUR_NO_LABOUR,
    LABOUR_OWNER_THIRD_PARTY,
    LABOUR_SUBCONTRACT,
    LABOUR_UNRESOLVED,
    MATERIAL_CONTRACTOR_PURCHASED,
    MATERIAL_NO_MATERIAL,
    MATERIAL_OWNER_SUPPLIED,
    MATERIAL_PROCUREMENT_VALUES,
    MATERIAL_SUBCONTRACTOR_SUPPLIED,
    MATERIAL_UNRESOLVED,
    NORMAL_UI_LABOUR_CHOICES,
    NORMAL_UI_MATERIAL_CHOICES,
    STATUS_CONFIRMED,
    STATUS_DRAFT,
    STATUS_PROPOSED,
    SUGGESTION_NONE,
    SUGGESTION_ORG_DEFAULT,
    SUGGESTION_RULE,
    EstimateScopeDelivery,
)
from app.models.pricing_engine import AI_ACTOR_TOKENS
from app.services.estimate_builder import as_decimal, as_money
from app.services.estimates import EstimateServiceError, ensure_version_editable
from app.services.organizations import get_current_organization_id

CLONE_ACTOR = "Estimate version clone"

DISPLAY_INTERNAL = "Internal"
DISPLAY_SUBCONTRACT = "Subcontract"
DISPLAY_MATERIAL_ONLY = "Material only"
DISPLAY_HYBRID = "Hybrid"
DISPLAY_UNRESOLVED = "Unresolved"
DISPLAY_ALLOWANCE = "Allowance"


class EstimateScopeDeliveryError(EstimateServiceError):
    """Raised when scope-delivery routing cannot complete."""


def assert_human_routing_actor(actor):
    name = (actor or "").strip()
    if not name:
        raise EstimateScopeDeliveryError("Scope delivery requires a human actor.")
    if name.upper() in AI_ACTOR_TOKENS:
        raise EstimateScopeDeliveryError("AI cannot confirm scope delivery.")
    return name


def dimensions_are_resolved(material_procurement, labour_delivery):
    return (
        material_procurement in MATERIAL_PROCUREMENT_VALUES
        and labour_delivery in LABOUR_DELIVERY_VALUES
        and material_procurement != MATERIAL_UNRESOLVED
        and labour_delivery != LABOUR_UNRESOLVED
    )


def org_routing_default(_organization_id):
    """Future-compatible org default hook. Slice A has no defaults table."""
    return None


def line_ownership_chain(line_item):
    if line_item is None:
        raise EstimateScopeDeliveryError("Estimate line item is required.")
    section = line_item.section
    if section is None:
        raise EstimateScopeDeliveryError("Estimate line is missing its section.")
    version = section.estimate_version
    if version is None:
        raise EstimateScopeDeliveryError("Estimate line is missing its version.")
    estimate = version.estimate
    if estimate is None:
        raise EstimateScopeDeliveryError("Estimate line is missing its estimate.")
    project = estimate.project
    if project is None:
        raise EstimateScopeDeliveryError("Estimate line is missing its project.")
    organization_id = project.organization_id
    if not organization_id:
        raise EstimateScopeDeliveryError("Estimate line is missing its organization.")
    if estimate.project_id != project.id:
        raise EstimateScopeDeliveryError("Estimate does not belong to its project.")
    if version.estimate_id != estimate.id:
        raise EstimateScopeDeliveryError("Version does not belong to its estimate.")
    if section.estimate_version_id != version.id:
        raise EstimateScopeDeliveryError("Section does not belong to its version.")
    if line_item.estimate_section_id != section.id:
        raise EstimateScopeDeliveryError("Line does not belong to its section.")
    return {
        "organization_id": organization_id,
        "project_id": project.id,
        "estimate_id": estimate.id,
        "estimate_version_id": version.id,
        "estimate": estimate,
        "version": version,
        "project": project,
    }


def require_line_matches_scope(
    line_item, *, organization_id, project_id, estimate_version_id=None
):
    chain = line_ownership_chain(line_item)
    if chain["organization_id"] != organization_id:
        raise EstimateScopeDeliveryError(
            "Scope delivery organization does not match the commercial line."
        )
    if chain["project_id"] != project_id:
        raise EstimateScopeDeliveryError(
            "Scope delivery project does not match the commercial line."
        )
    if (
        estimate_version_id is not None
        and chain["estimate_version_id"] != estimate_version_id
    ):
        raise EstimateScopeDeliveryError(
            "Scope delivery version does not match the commercial line."
        )
    return chain


def version_is_routing_editable(version):
    if version is None:
        return False
    try:
        ensure_version_editable(version)
    except EstimateServiceError:
        return False
    return (version.status or "") == "Draft"


def require_routing_editable(version):
    try:
        ensure_version_editable(version)
    except EstimateServiceError as exc:
        raise EstimateScopeDeliveryError(str(exc)) from exc
    if (version.status or "") != "Draft":
        raise EstimateScopeDeliveryError(
            "Scope delivery can only be edited on a Draft estimate version."
        )
    return version


def get_scope_delivery_for_line(line_item):
    if line_item is None or line_item.id is None:
        return None
    return EstimateScopeDelivery.query.filter_by(
        estimate_line_item_id=line_item.id
    ).first()


def suggest_routing_for_line(line_item):
    org_id = None
    try:
        org_id = line_ownership_chain(line_item)["organization_id"]
    except EstimateScopeDeliveryError:
        org_id = None
    default = org_routing_default(org_id) if org_id else None
    if default is not None:
        return (
            default.get("material_procurement", MATERIAL_UNRESOLVED),
            default.get("labour_delivery", LABOUR_UNRESOLVED),
            SUGGESTION_ORG_DEFAULT,
        )

    if (line_item.line_type or "") == "Allowance":
        return MATERIAL_NO_MATERIAL, LABOUR_NO_LABOUR, SUGGESTION_RULE

    cost_item = None
    if line_item.cost_item_id:
        cost_item = db.session.get(CostItem, line_item.cost_item_id)
    category = (cost_item.category or "") if cost_item is not None else ""
    if category in ("Material", "Equipment"):
        return MATERIAL_CONTRACTOR_PURCHASED, LABOUR_NO_LABOUR, SUGGESTION_RULE
    if category == "Labour":
        return MATERIAL_NO_MATERIAL, LABOUR_INTERNAL, SUGGESTION_RULE
    if category == "Subcontractor":
        return MATERIAL_SUBCONTRACTOR_SUPPLIED, LABOUR_SUBCONTRACT, SUGGESTION_RULE
    if category == "Allowance":
        return MATERIAL_NO_MATERIAL, LABOUR_NO_LABOUR, SUGGESTION_RULE
    return MATERIAL_UNRESOLVED, LABOUR_UNRESOLVED, SUGGESTION_NONE


def derived_display_class(material_procurement, labour_delivery, *, line_type=None):
    if (
        not material_procurement
        or not labour_delivery
        or material_procurement == MATERIAL_UNRESOLVED
        or labour_delivery == LABOUR_UNRESOLVED
    ):
        return DISPLAY_UNRESOLVED
    if (
        (line_type or "") == "Allowance"
        and material_procurement == MATERIAL_NO_MATERIAL
        and labour_delivery == LABOUR_NO_LABOUR
    ):
        return DISPLAY_ALLOWANCE
    if material_procurement == MATERIAL_NO_MATERIAL and labour_delivery == LABOUR_NO_LABOUR:
        return DISPLAY_ALLOWANCE
    if labour_delivery == LABOUR_SUBCONTRACT and material_procurement in (
        MATERIAL_SUBCONTRACTOR_SUPPLIED,
        MATERIAL_NO_MATERIAL,
    ):
        return DISPLAY_SUBCONTRACT
    if labour_delivery == LABOUR_NO_LABOUR and material_procurement in (
        MATERIAL_CONTRACTOR_PURCHASED,
        MATERIAL_SUBCONTRACTOR_SUPPLIED,
        MATERIAL_OWNER_SUPPLIED,
    ):
        return DISPLAY_MATERIAL_ONLY
    if labour_delivery == LABOUR_INTERNAL and material_procurement == MATERIAL_NO_MATERIAL:
        return DISPLAY_INTERNAL
    if labour_delivery == LABOUR_INTERNAL and material_procurement == MATERIAL_CONTRACTOR_PURCHASED:
        return DISPLAY_HYBRID
    if labour_delivery == LABOUR_SUBCONTRACT and material_procurement == MATERIAL_CONTRACTOR_PURCHASED:
        return DISPLAY_HYBRID
    if labour_delivery == LABOUR_INTERNAL:
        return DISPLAY_INTERNAL
    if labour_delivery == LABOUR_SUBCONTRACT:
        return DISPLAY_SUBCONTRACT
    if labour_delivery == LABOUR_OWNER_THIRD_PARTY:
        return DISPLAY_HYBRID
    return DISPLAY_HYBRID


def _status_for_dimensions(material_procurement, labour_delivery):
    if dimensions_are_resolved(material_procurement, labour_delivery):
        return STATUS_PROPOSED
    return STATUS_DRAFT


def _new_routing_row(line_item, *, actor, material, labour, suggestion, status=None):
    chain = line_ownership_chain(line_item)
    now = datetime.utcnow()
    row = EstimateScopeDelivery(
        organization_id=chain["organization_id"],
        project_id=chain["project_id"],
        estimate_id=chain["estimate_id"],
        estimate_version_id=chain["estimate_version_id"],
        estimate_line_item_id=line_item.id,
        material_procurement=material,
        labour_delivery=labour,
        status=status or _status_for_dimensions(material, labour),
        suggestion_source=suggestion,
        confirmed_by=None,
        confirmed_at=None,
        actor_display_name=actor,
        created_at=now,
        updated_at=now,
    )
    db.session.add(row)
    return row


def ensure_routing_rows_for_version(version, *, actor, commit=False):
    """Create missing routing rows from deterministic suggestions. Not approval."""
    actor_name = assert_human_routing_actor(actor)
    require_routing_editable(version)
    created = []
    for section in version.sections:
        for item in section.line_items:
            existing = get_scope_delivery_for_line(item)
            if existing is not None:
                continue
            material, labour, source = suggest_routing_for_line(item)
            row = _new_routing_row(
                item,
                actor=actor_name,
                material=material,
                labour=labour,
                suggestion=source,
            )
            created.append(row)
    db.session.flush()
    if commit:
        db.session.commit()
    return created


def save_scope_delivery(
    line_item,
    *,
    material_procurement,
    labour_delivery,
    actor,
    organization_id=None,
    project_id=None,
    user_id=None,
    commit=True,
):
    actor_name = assert_human_routing_actor(actor)
    chain = line_ownership_chain(line_item)
    org_id = organization_id or chain["organization_id"]
    proj_id = project_id or chain["project_id"]
    require_line_matches_scope(
        line_item,
        organization_id=org_id,
        project_id=proj_id,
        estimate_version_id=chain["estimate_version_id"],
    )
    require_routing_editable(chain["version"])
    if material_procurement not in MATERIAL_PROCUREMENT_VALUES:
        raise EstimateScopeDeliveryError("Invalid material procurement routing.")
    if labour_delivery not in LABOUR_DELIVERY_VALUES:
        raise EstimateScopeDeliveryError("Invalid labour delivery routing.")

    row = get_scope_delivery_for_line(line_item)
    now = datetime.utcnow()
    if row is None:
        row = _new_routing_row(
            line_item,
            actor=actor_name,
            material=material_procurement,
            labour=labour_delivery,
            suggestion=SUGGESTION_NONE,
        )
    else:
        if (
            row.organization_id != chain["organization_id"]
            or row.project_id != chain["project_id"]
            or row.estimate_id != chain["estimate_id"]
            or row.estimate_version_id != chain["estimate_version_id"]
        ):
            raise EstimateScopeDeliveryError(
                "Stored scope delivery does not match the commercial line."
            )
        changed = (
            row.material_procurement != material_procurement
            or row.labour_delivery != labour_delivery
        )
        row.material_procurement = material_procurement
        row.labour_delivery = labour_delivery
        row.actor_display_name = actor_name
        row.updated_at = now
        if changed and row.status == STATUS_CONFIRMED:
            row.status = STATUS_PROPOSED
            row.confirmed_by = None
            row.confirmed_at = None

    if not dimensions_are_resolved(material_procurement, labour_delivery):
        row.status = STATUS_DRAFT
        row.confirmed_by = None
        row.confirmed_at = None
    elif row.status != STATUS_CONFIRMED:
        row.status = STATUS_PROPOSED
        row.confirmed_by = None
        row.confirmed_at = None

    if row.suggestion_source is None:
        row.suggestion_source = SUGGESTION_NONE
    db.session.flush()
    if commit:
        db.session.commit()
    return row


def confirm_scope_delivery(
    line_item,
    *,
    actor,
    organization_id=None,
    project_id=None,
    user_id=None,
    commit=True,
):
    actor_name = assert_human_routing_actor(actor)
    chain = line_ownership_chain(line_item)
    org_id = organization_id or chain["organization_id"]
    proj_id = project_id or chain["project_id"]
    require_line_matches_scope(
        line_item,
        organization_id=org_id,
        project_id=proj_id,
        estimate_version_id=chain["estimate_version_id"],
    )
    require_routing_editable(chain["version"])
    row = get_scope_delivery_for_line(line_item)
    if row is None:
        raise EstimateScopeDeliveryError("Scope delivery routing is missing.")
    if not dimensions_are_resolved(row.material_procurement, row.labour_delivery):
        raise EstimateScopeDeliveryError(
            "Unresolved scope delivery cannot be confirmed."
        )
    now = datetime.utcnow()
    row.status = STATUS_CONFIRMED
    row.confirmed_by = user_id
    row.confirmed_at = now
    row.actor_display_name = actor_name
    row.updated_at = now
    db.session.flush()
    if commit:
        db.session.commit()
    return row


def approve_all_scope_routing(
    version,
    *,
    actor,
    organization_id=None,
    project_id=None,
    user_id=None,
    commit=True,
):
    """Confirm eligible PROPOSED resolved rows atomically. Skips unresolved."""
    actor_name = assert_human_routing_actor(actor)
    require_routing_editable(version)
    estimate = version.estimate
    project = estimate.project if estimate is not None else None
    if project is None:
        raise EstimateScopeDeliveryError("Estimate version is missing its project.")
    org_id = organization_id or project.organization_id
    proj_id = project_id or project.id
    if project.organization_id != org_id or project.id != proj_id:
        raise EstimateScopeDeliveryError(
            "Scope delivery tenant does not match this estimate version."
        )
    if estimate.project_id != project.id:
        raise EstimateScopeDeliveryError("Estimate does not belong to its project.")

    confirmed = []
    skipped = []
    try:
        now = datetime.utcnow()
        for section in version.sections:
            for item in section.line_items:
                row = get_scope_delivery_for_line(item)
                if row is None:
                    skipped.append(item)
                    continue
                require_line_matches_scope(
                    item,
                    organization_id=org_id,
                    project_id=proj_id,
                    estimate_version_id=version.id,
                )
                if (
                    row.organization_id != org_id
                    or row.project_id != proj_id
                    or row.estimate_version_id != version.id
                ):
                    raise EstimateScopeDeliveryError(
                        "Stored scope delivery does not match the commercial line."
                    )
                if row.status != STATUS_PROPOSED:
                    skipped.append(item)
                    continue
                if not dimensions_are_resolved(
                    row.material_procurement, row.labour_delivery
                ):
                    skipped.append(item)
                    continue
                row.status = STATUS_CONFIRMED
                row.confirmed_by = user_id
                row.confirmed_at = now
                row.actor_display_name = actor_name
                row.updated_at = now
                confirmed.append(row)
        db.session.flush()
        if commit:
            db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {"confirmed": confirmed, "skipped": skipped}


def copy_scope_delivery_for_cloned_line(source_line, cloned_line, *, actor=CLONE_ACTOR):
    """Copy dimensions onto the cloned line. Conservative reconfirmation."""
    source = get_scope_delivery_for_line(source_line)
    if source is None:
        return None
    actor_name = (actor or CLONE_ACTOR).strip() or CLONE_ACTOR
    material = source.material_procurement
    labour = source.labour_delivery
    status = (
        STATUS_PROPOSED
        if dimensions_are_resolved(material, labour)
        else STATUS_DRAFT
    )
    row = _new_routing_row(
        cloned_line,
        actor=actor_name,
        material=material,
        labour=labour,
        suggestion=source.suggestion_source or SUGGESTION_NONE,
        status=status,
    )
    row.confirmed_by = None
    row.confirmed_at = None
    return row


def material_requirement_is_supplier_package_eligible(requirement):
    """Fail-closed: cited line with confirmed CONTRACTOR_PURCHASED only."""
    if requirement is None:
        return False
    line_id = requirement.estimate_line_item_id
    if line_id is None:
        return False
    routing = EstimateScopeDelivery.query.filter_by(
        estimate_line_item_id=line_id
    ).first()
    if routing is None:
        return False
    if routing.status != STATUS_CONFIRMED:
        return False
    if routing.material_procurement != MATERIAL_CONTRACTOR_PURCHASED:
        return False
    try:
        line = db.session.get(EstimateLineItem, line_id)
        chain = line_ownership_chain(line)
    except EstimateScopeDeliveryError:
        return False
    if chain["organization_id"] != requirement.organization_id:
        return False
    if chain["project_id"] != requirement.project_id:
        return False
    return True


def ui_material_choices(current_value=None):
    values = list(NORMAL_UI_MATERIAL_CHOICES)
    if current_value == MATERIAL_OWNER_SUPPLIED and MATERIAL_OWNER_SUPPLIED not in values:
        values.append(MATERIAL_OWNER_SUPPLIED)
    return values


def ui_labour_choices(current_value=None):
    values = list(NORMAL_UI_LABOUR_CHOICES)
    if (
        current_value == LABOUR_OWNER_THIRD_PARTY
        and LABOUR_OWNER_THIRD_PARTY not in values
    ):
        values.append(LABOUR_OWNER_THIRD_PARTY)
    return values


def _cost_evidence(line_item):
    kind = line_item.costing_source_kind or ""
    try:
        amount = as_money(line_item.extended_cost)
    except Exception:
        amount = as_decimal(line_item.extended_cost or 0)
    return {"source_kind": kind, "extended_cost": amount}


def assemble_scope_delivery_review(
    *,
    project,
    version=None,
    organization_id=None,
    actor="office-reviewer",
):
    org_id = organization_id or get_current_organization_id()
    if project is None or project.organization_id != org_id:
        raise EstimateScopeDeliveryError("Project is not in this organization.")
    if version is None:
        estimates = list(project.estimates or [])
        estimates.sort(key=lambda row: row.id or 0, reverse=True)
        for estimate in estimates:
            if estimate.current_version is not None:
                version = estimate.current_version
                break
    if version is None:
        return {
            "project": project,
            "version": None,
            "estimate": None,
            "editable": False,
            "rows": [],
            "eligible_proposed_count": 0,
        }
    estimate = version.estimate
    if estimate is None or estimate.project_id != project.id:
        raise EstimateScopeDeliveryError("Estimate version is not on this project.")
    chain_org = project.organization_id
    if chain_org != org_id:
        raise EstimateScopeDeliveryError("Estimate version is not in this organization.")
    editable = version_is_routing_editable(version)
    if editable:
        ensure_routing_rows_for_version(version, actor=actor, commit=True)
    rows = []
    eligible = 0
    for section in version.sections:
        for item in section.line_items:
            routing = get_scope_delivery_for_line(item)
            material = routing.material_procurement if routing else MATERIAL_UNRESOLVED
            labour = routing.labour_delivery if routing else LABOUR_UNRESOLVED
            status = routing.status if routing else STATUS_DRAFT
            display = derived_display_class(
                material, labour, line_type=item.line_type
            )
            if (
                routing is not None
                and routing.status == STATUS_PROPOSED
                and dimensions_are_resolved(material, labour)
            ):
                eligible += 1
            rows.append(
                {
                    "line_item": item,
                    "section": section,
                    "routing": routing,
                    "material_procurement": material,
                    "labour_delivery": labour,
                    "status": status,
                    "display_class": display,
                    "suggestion_source": (
                        routing.suggestion_source if routing is not None else None
                    ),
                    "confirmed_at": routing.confirmed_at if routing else None,
                    "confirmed_by": routing.confirmed_by if routing else None,
                    "cost_evidence": _cost_evidence(item),
                    "material_choices": ui_material_choices(material),
                    "labour_choices": ui_labour_choices(labour),
                    "can_confirm": (
                        editable
                        and routing is not None
                        and dimensions_are_resolved(material, labour)
                        and status != STATUS_CONFIRMED
                    ),
                }
            )
    return {
        "project": project,
        "version": version,
        "estimate": estimate,
        "editable": editable,
        "rows": rows,
        "eligible_proposed_count": eligible,
    }
