from datetime import datetime
from decimal import Decimal
import re

from app import db
from app.models.estimate import (
    AUTO_LOCK_VERSION_STATUSES,
    Estimate,
    EstimateVersion,
)
from app.models.project import Project
from app.services.organizations import get_current_organization_id


class EstimateServiceError(Exception):
    """Raised when an estimate operation cannot be completed."""


def suggest_next_estimate_number(year=None):
    """Return the next suggested estimate number in EST-YYYY-NNNN format."""
    year = year or datetime.utcnow().year
    prefix = f"EST-{year}-"
    pattern = re.compile(rf"^EST-{year}-(\d+)$", re.IGNORECASE)

    max_sequence = 0
    estimates = Estimate.query.filter(
        Estimate.estimate_number.ilike(f"{prefix}%")
    ).all()

    for estimate in estimates:
        match = pattern.match(estimate.estimate_number.strip())
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))

    return f"{prefix}{max_sequence + 1:04d}"


def create_estimate(
    *,
    project_id,
    estimate_number,
    title,
    status="Draft",
    organization_id=None,
):
    """Create an estimate and its initial Version 1 in one transaction."""
    estimate_number = (estimate_number or "").strip()
    title = (title or "").strip()

    if not estimate_number:
        raise EstimateServiceError("Estimate number is required.")
    if not title:
        raise EstimateServiceError("Estimate title is required.")
    if not project_id:
        raise EstimateServiceError("Project is required.")

    org_id = organization_id or get_current_organization_id()
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first()
    if not project:
        raise EstimateServiceError(f"Project {project_id} not found in current organization.")

    if Estimate.query.filter_by(estimate_number=estimate_number).first():
        raise EstimateServiceError(
            f'An estimate with number "{estimate_number}" already exists.'
        )

    context_id = (
        project.current_commercial_context.id
        if project.current_commercial_context
        else None
    )

    estimate = Estimate(
        project_id=project.id,
        estimate_number=estimate_number,
        title=title,
        status=status or "Draft",
    )
    version = EstimateVersion(
        version_number=1,
        version_label="Initial Estimate",
        commercial_context_id=context_id,
        status="Draft",
        subtotal=Decimal("0"),
        overhead_percent=Decimal("0"),
        profit_percent=Decimal("0"),
        tax_percent=Decimal("0"),
        total=Decimal("0"),
        is_locked=False,
    )
    estimate.versions.append(version)

    db.session.add(estimate)
    db.session.flush()
    estimate.current_version_id = version.id
    db.session.commit()

    return estimate


def clone_current_version(
    estimate,
    *,
    version_label=None,
    revision_reason=None,
):
    """Create the next version by copying values and builder content."""
    from app.services.estimate_builder import clone_sections_to_version

    current = estimate.current_version
    if current is None:
        raise EstimateServiceError(
            "Cannot create a new version because this estimate has no current version."
        )

    next_number = (
        db.session.query(db.func.max(EstimateVersion.version_number))
        .filter_by(estimate_id=estimate.id)
        .scalar()
        or 0
    ) + 1

    context_id = (
        estimate.project.current_commercial_context.id
        if (estimate.project and estimate.project.current_commercial_context)
        else current.commercial_context_id
    )

    new_version = EstimateVersion(
        estimate_id=estimate.id,
        version_number=next_number,
        version_label=(version_label or "").strip() or None,
        revision_reason=(revision_reason or "").strip() or None,
        commercial_context_id=context_id,
        status="Draft",
        subtotal=Decimal(current.subtotal or 0),
        overhead_percent=Decimal(current.overhead_percent or 0),
        profit_percent=Decimal(current.profit_percent or 0),
        tax_percent=Decimal(current.tax_percent or 0),
        total=Decimal(current.total or 0),
        is_locked=False,
    )

    db.session.add(new_version)
    db.session.flush()
    clone_sections_to_version(current, new_version)
    estimate.current_version_id = new_version.id
    db.session.commit()

    return new_version


def set_current_version(estimate, version):
    if version.estimate_id != estimate.id:
        raise EstimateServiceError("Version does not belong to this estimate.")

    estimate.current_version_id = version.id
    db.session.commit()
    return version


def lock_version(version):
    version.is_locked = True
    db.session.commit()
    return version


def unlock_version(version):
    version.is_locked = False
    db.session.commit()
    return version


def ensure_version_editable(version):
    if version.is_locked:
        raise EstimateServiceError(
            f"{version.display_label} is locked and cannot be edited."
        )


def update_estimate_version(
    version,
    *,
    version_label=None,
    revision_reason=None,
    status=None,
    overhead_percent=None,
    profit_percent=None,
    tax_percent=None,
):
    """Update version metadata/percentages and recalculate totals."""
    from app.services.estimate_builder import recalculate_version

    ensure_version_editable(version)

    if version_label is not None:
        version.version_label = version_label.strip() or None
    if revision_reason is not None:
        version.revision_reason = revision_reason.strip() or None
    if status is not None:
        version.status = status
        if status in AUTO_LOCK_VERSION_STATUSES:
            version.is_locked = True
    if overhead_percent is not None:
        version.overhead_percent = Decimal(overhead_percent)
    if profit_percent is not None:
        version.profit_percent = Decimal(profit_percent)
    if tax_percent is not None:
        version.tax_percent = Decimal(tax_percent)

    recalculate_version(version)
    db.session.commit()
    return version


def set_version_status(version, status):
    ensure_version_editable(version)
    version.status = status
    if status in AUTO_LOCK_VERSION_STATUSES:
        version.is_locked = True
    db.session.commit()
    return version


def toggle_estimate_archive(estimate):
    if estimate.status == "Archived":
        estimate.status = "Draft"
    else:
        estimate.status = "Archived"
    db.session.commit()
    return estimate
