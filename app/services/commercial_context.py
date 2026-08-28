"""Project Commercial Decision Context service and policy validation."""

from typing import Any, Dict, List, Optional

from app import db
from app.models.project import Project, ProjectCommercialContext
from app.services.organizations import get_current_organization_id

PROJECT_TYPES = (
    "New Build",
    "Addition",
    "Renovation",
    "Garage",
    "Foundation",
    "Commercial",
    "Specialty",
)

PRICING_POSTURES = (
    "Lean / Strategic",
    "Competitive",
    "Fair Market",
    "Selective",
    "Premium",
)

EXECUTION_RISKS = (
    "Low",
    "Normal",
    "Elevated",
    "High",
)

SCHEDULE_CONDITIONS = (
    "Flexible",
    "Normal",
    "Compressed",
    "Critical",
)

SITE_CONDITIONS = (
    "Normal",
    "Restricted Access",
    "Remote",
    "Occupied",
    "Congested",
)

ESTIMATE_STAGES = (
    "Budget",
    "Preliminary",
    "Tender",
    "Contract",
)

DELIVERY_MODELS = (
    "Self-Perform",
    "Mixed",
    "Primarily Subcontracted",
)

LEGACY_UNKNOWN_VALUE = "Legacy / Unknown"

# Organization-configurable policy registry for reason-required selections.
# For ORG-001 (Brayman Construction Inc.), initial policy requires reasons for Premium and High risk.
# Other organizations can register distinct policy sets.
ORGANIZATION_REASON_POLICIES: Dict[str, Dict[str, List[str]]] = {
    "ORG-001": {
        "pricing_postures": ["Premium"],
        "execution_risks": ["High"],
    }
}


class CommercialContextValidationError(ValueError):
    """Raised when commercial context data fails validation."""
    pass


def get_organization_reason_policy(organization_id: str) -> Dict[str, List[str]]:
    """Return the reason-requirement policy configured for an organization."""
    return ORGANIZATION_REASON_POLICIES.get(organization_id, {})


def set_organization_reason_policy(organization_id: str, policy: Dict[str, List[str]]) -> None:
    """Register or update an organization's reason-requirement policy (for configuration/testing)."""
    ORGANIZATION_REASON_POLICIES[organization_id] = policy


def selection_requires_reason(organization_id: str, field_name: str, value: str) -> bool:
    """Check whether a selected value requires a justification reason under the organization's policy."""
    policy = get_organization_reason_policy(organization_id)
    if not policy:
        return False
    required_values = policy.get(field_name, [])
    return value in required_values


def validate_commercial_context_data(
    data: Dict[str, Any],
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate all 7 mandatory commercial decision parameters and policy-driven reasons."""
    org_id = organization_id or get_current_organization_id()

    field_options = {
        "project_type": PROJECT_TYPES,
        "pricing_posture": PRICING_POSTURES,
        "execution_risk": EXECUTION_RISKS,
        "schedule_condition": SCHEDULE_CONDITIONS,
        "site_condition": SITE_CONDITIONS,
        "estimate_stage": ESTIMATE_STAGES,
        "delivery_model": DELIVERY_MODELS,
    }

    validated: Dict[str, Any] = {}
    for field, options in field_options.items():
        val = data.get(field)
        if not val or val not in options:
            raise CommercialContextValidationError(
                f"Invalid or missing {field.replace('_', ' ').title()}: '{val}'. Must be one of {options}."
            )
        validated[field] = val

    # Policy-driven justification verification
    reason = (data.get("justification_reason") or "").strip()
    reason_required_fields: List[str] = []

    if selection_requires_reason(org_id, "pricing_postures", validated["pricing_posture"]):
        reason_required_fields.append(f"Pricing Posture '{validated['pricing_posture']}'")
    if selection_requires_reason(org_id, "execution_risks", validated["execution_risk"]):
        reason_required_fields.append(f"Execution Risk '{validated['execution_risk']}'")
    if selection_requires_reason(org_id, "schedule_conditions", validated["schedule_condition"]):
        reason_required_fields.append(f"Schedule Condition '{validated['schedule_condition']}'")
    if selection_requires_reason(org_id, "site_conditions", validated["site_condition"]):
        reason_required_fields.append(f"Site Condition '{validated['site_condition']}'")

    if reason_required_fields and not reason:
        fields_str = ", ".join(reason_required_fields)
        raise CommercialContextValidationError(
            f"A justification reason is required by organization policy for exceptional selection: {fields_str}."
        )

    validated["justification_reason"] = reason if reason else None
    validated["change_summary"] = (data.get("change_summary") or "").strip() or None
    return validated


def create_initial_commercial_context(
    project_id: int,
    data: Dict[str, Any],
    created_by: str = "Estimator",
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> ProjectCommercialContext:
    """Create version 1 of commercial context for a newly created project."""
    org_id = organization_id or get_current_organization_id()
    validated = validate_commercial_context_data(data, organization_id=org_id)

    ctx = ProjectCommercialContext(
        project_id=project_id,
        version_number=1,
        is_current=True,
        project_type=validated["project_type"],
        pricing_posture=validated["pricing_posture"],
        execution_risk=validated["execution_risk"],
        schedule_condition=validated["schedule_condition"],
        site_condition=validated["site_condition"],
        estimate_stage=validated["estimate_stage"],
        delivery_model=validated["delivery_model"],
        justification_reason=validated["justification_reason"],
        change_summary=validated["change_summary"] or "Initial project creation",
        created_by=created_by,
    )
    db.session.add(ctx)
    if commit:
        db.session.commit()
    return ctx


def update_commercial_context(
    project_id: int,
    data: Dict[str, Any],
    updated_by: str = "Estimator",
    change_summary: Optional[str] = None,
    organization_id: Optional[str] = None,
    commit: bool = True,
) -> ProjectCommercialContext:
    """Create a new version of commercial context, leaving historical versions immutable."""
    project = Project.query.get(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found.")

    org_id = organization_id or project.organization_id or get_current_organization_id()
    validated = validate_commercial_context_data(data, organization_id=org_id)

    # Deactivate current version(s)
    prior_version_number = 0
    for old_ctx in project.commercial_contexts:
        if old_ctx.is_current:
            old_ctx.is_current = False
        if old_ctx.version_number > prior_version_number:
            prior_version_number = old_ctx.version_number

    new_version_number = prior_version_number + 1

    new_ctx = ProjectCommercialContext(
        project_id=project_id,
        version_number=new_version_number,
        is_current=True,
        project_type=validated["project_type"],
        pricing_posture=validated["pricing_posture"],
        execution_risk=validated["execution_risk"],
        schedule_condition=validated["schedule_condition"],
        site_condition=validated["site_condition"],
        estimate_stage=validated["estimate_stage"],
        delivery_model=validated["delivery_model"],
        justification_reason=validated["justification_reason"],
        change_summary=change_summary or validated["change_summary"] or f"Updated to version {new_version_number}",
        created_by=updated_by,
    )
    db.session.add(new_ctx)
    if commit:
        db.session.commit()
    return new_ctx
