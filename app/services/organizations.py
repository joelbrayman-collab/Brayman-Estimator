"""Organization context and scoping service."""

from flask import g, has_request_context

from app import db
from app.models.organization import Organization

DEFAULT_ORGANIZATION_ID = "ORG-001"


def get_current_organization_id() -> str:
    """Return the active organization ID for the current context.

    In single-tenant / development mode, defaults to ORG-001 (Brayman Construction Inc.).
    When request context contains an explicit organization override on flask.g, returns that.
    """
    if has_request_context() and hasattr(g, "organization_id") and g.organization_id:
        return g.organization_id
    return DEFAULT_ORGANIZATION_ID


def set_current_organization_id(org_id: str) -> None:
    """Set the active organization ID for the current request context."""
    if has_request_context():
        g.organization_id = org_id


def ensure_default_organization(*, commit: bool = True) -> Organization:
    """Ensure the default Brayman Construction organization (ORG-001) exists."""
    org = Organization.query.get(DEFAULT_ORGANIZATION_ID)
    if not org:
        org = Organization(
            id=DEFAULT_ORGANIZATION_ID,
            legal_name="Brayman Construction Inc.",
            display_name="Brayman Construction",
            primary_address="411 St. John Street, Merrickville, Ontario K0G 1N0",
            default_region="Eastern Ontario / Ottawa Valley",
            currency="CAD",
            tax_jurisdiction="Ontario (HST 13%)",
            is_active=True,
        )
        db.session.add(org)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
    return org


def get_current_organization() -> Organization:
    """Return the active Organization model instance for the current context."""
    org_id = get_current_organization_id()
    org = Organization.query.get(org_id)
    if not org and org_id == DEFAULT_ORGANIZATION_ID:
        org = ensure_default_organization()
    if not org:
        raise RuntimeError(f"Active organization '{org_id}' not found in database.")
    return org
