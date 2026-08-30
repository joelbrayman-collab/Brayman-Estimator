"""Permit Foundation V1 services (FG-015). Location, resolution, preliminary profile."""

from datetime import datetime
from typing import Optional

from app import db
from app.models.project import (
    DEFAULT_PERMIT_CONTEXT_CLASS,
    JURISDICTION_RESOLVED,
    JURISDICTION_UNRESOLVED,
    LOCATION_COMPLETE,
    LOCATION_INCOMPLETE,
    LOCATION_KIND_CIVIC,
    PERMIT_ADVISORY_STATUS,
    PERMIT_CONTEXT_CLASSES,
    PERMIT_GENERATION_METHOD,
    PERMIT_PROFILE_KIND_PRELIMINARY,
    PLAN_SITE_REVIEW_NOT_PERFORMED,
    SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE,
    PermitProfile,
    Project,
    ProjectLocation,
)
from app.services.jurisdiction import resolve_jurisdiction
from app.services.organizations import get_current_organization_id


class PermitFoundationError(ValueError):
    """Fail-closed Permit Foundation error."""


def _org_id(organization_id: Optional[str] = None) -> str:
    return organization_id or get_current_organization_id()


def _owned_project(project_id: int, organization_id: Optional[str] = None) -> Project:
    org_id = _org_id(organization_id)
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first()
    if project is None:
        raise PermitFoundationError("Project not found in current organization.")
    return project


def normalize_permit_context_class(value: Optional[str]) -> str:
    token = (value or "").strip()
    if not token:
        return DEFAULT_PERMIT_CONTEXT_CLASS
    if token not in PERMIT_CONTEXT_CLASSES:
        raise PermitFoundationError("Invalid permit context class.")
    return token


def location_payload_from_form(form) -> dict:
    return {
        "street": (form.get("street") or "").strip() or None,
        "municipality": (form.get("municipality") or "").strip() or None,
        "province_state": (form.get("province_state") or "").strip() or None,
        "postal_zip": (form.get("postal_zip") or "").strip() or None,
        "country": (form.get("country") or "").strip() or None,
    }


def _location_tuple(values: dict) -> tuple:
    return (
        (values.get("street") or "").strip(),
        (values.get("municipality") or "").strip(),
        (values.get("province_state") or "").strip(),
        (values.get("postal_zip") or "").strip(),
        (values.get("country") or "").strip(),
    )


def _apply_location_fields(location: ProjectLocation, values: dict) -> None:
    location.street = values.get("street")
    location.municipality = values.get("municipality")
    location.province_state = values.get("province_state")
    location.postal_zip = values.get("postal_zip")
    location.country = values.get("country")
    location.location_kind = LOCATION_KIND_CIVIC
    location.updated_at = datetime.utcnow()


def _create_profile(
    *,
    project: Project,
    location: ProjectLocation,
    permit_context_class: str,
    version_number: int,
    generated_by: Optional[str],
) -> PermitProfile:
    resolved = resolve_jurisdiction(
        location.country,
        location.province_state,
        location.municipality,
        tax_jurisdiction=None,
    )
    values = location.civic_values()
    completeness = location.completeness
    if resolved is None:
        jurisdiction_status = JURISDICTION_UNRESOLVED
    else:
        jurisdiction_status = JURISDICTION_RESOLVED
    profile = PermitProfile(
        organization_id=project.organization_id,
        project_id=project.id,
        kind=PERMIT_PROFILE_KIND_PRELIMINARY,
        version_number=version_number,
        is_current=True,
        is_stale=False,
        recheck_required=False,
        street_snapshot=values["street"],
        municipality_snapshot=values["municipality"],
        province_state_snapshot=values["province_state"],
        postal_zip_snapshot=values["postal_zip"],
        country_snapshot=values["country"],
        location_completeness=completeness,
        jurisdiction_status=jurisdiction_status,
        resolved_jurisdiction_id=resolved.id if resolved else None,
        resolved_jurisdiction_code=resolved.code if resolved else None,
        resolved_jurisdiction_name=resolved.name if resolved else None,
        resolved_ahj_name=resolved.ahj_name if resolved else None,
        permit_context_class=permit_context_class,
        advisory_status=PERMIT_ADVISORY_STATUS,
        generation_method=PERMIT_GENERATION_METHOD,
        generated_at=datetime.utcnow(),
        generated_by=generated_by or "Estimator",
        plan_site_review_status=PLAN_SITE_REVIEW_NOT_PERFORMED,
        substantive_analysis_status=SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE,
    )
    db.session.add(profile)
    db.session.flush()
    return profile


def establish_project_location_and_profile(
    project_id: int,
    location_values: dict,
    permit_context_class: Optional[str] = None,
    *,
    organization_id: Optional[str] = None,
    generated_by: Optional[str] = None,
    commit: bool = False,
) -> PermitProfile:
    """Create or update ProjectLocation and a preliminary profile.

    New projects always get a location row and profile. Existing projects get
    a profile only when this is called from explicit location review.
    Does not overwrite Project.address or derive civic fields from free text.
    """
    project = _owned_project(project_id, organization_id)
    context = normalize_permit_context_class(permit_context_class)
    values = {
        "street": (location_values.get("street") or "").strip() or None,
        "municipality": (location_values.get("municipality") or "").strip() or None,
        "province_state": (location_values.get("province_state") or "").strip() or None,
        "postal_zip": (location_values.get("postal_zip") or "").strip() or None,
        "country": (location_values.get("country") or "").strip() or None,
    }

    location = project.location
    created_location = False
    if location is None:
        location = ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            location_kind=LOCATION_KIND_CIVIC,
        )
        db.session.add(location)
        db.session.flush()
        created_location = True
        project.location = location

    current = project.current_permit_profile
    location_changed = created_location or _location_tuple(
        location.civic_values()
    ) != _location_tuple(values)
    context_changed = current is None or current.permit_context_class != context

    _apply_location_fields(location, values)

    if current is not None and not location_changed and not context_changed:
        if commit:
            db.session.commit()
        return current

    if current is not None:
        current.is_current = False
        current.is_stale = True
        current.recheck_required = True
        next_version = current.version_number + 1
    else:
        next_version = 1

    profile = _create_profile(
        project=project,
        location=location,
        permit_context_class=context,
        version_number=next_version,
        generated_by=generated_by,
    )
    from app.services.permit_intelligence import mark_current_analysis_recheck

    mark_current_analysis_recheck(project)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return profile


def assemble_permit_foundation_state(project: Project) -> dict:
    """Read-only Hub facts. Does not create records."""
    location = project.location
    profile = project.current_permit_profile
    if location is None:
        completeness = LOCATION_INCOMPLETE
        jurisdiction_status = JURISDICTION_UNRESOLVED
    else:
        completeness = location.completeness
        jurisdiction_status = (
            profile.jurisdiction_status
            if profile is not None
            else JURISDICTION_UNRESOLVED
        )
    return {
        "location": location,
        "profile": profile,
        "location_completeness": completeness,
        "jurisdiction_status": jurisdiction_status,
        "profile_state": "preliminary" if profile is not None else "not generated",
        "plan_site_analysis": PLAN_SITE_REVIEW_NOT_PERFORMED,
        "substantive_report": SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE,
        "advisory_label": "PRELIMINARY / FOUNDATION ONLY",
    }
