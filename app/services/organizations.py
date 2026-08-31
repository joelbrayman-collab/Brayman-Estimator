"""Organization context and scoping service."""

from flask import g, has_request_context
from flask_login import current_user

from app import db
from app.models.organization import Organization

DEFAULT_ORGANIZATION_ID = "ORG-001"


class OrganizationAccessError(RuntimeError):
    """Authenticated request cannot resolve a unique active membership."""


def resolve_membership_organization_id(user) -> str:
    """Return the sole active membership organization, or fail closed."""
    from app.models.user import UserMembership

    try:
        user_id = int(user.get_id())
    except (TypeError, ValueError, AttributeError) as exc:
        raise OrganizationAccessError(
            "Organization context requires an authenticated user."
        ) from exc

    rows = UserMembership.query.filter_by(user_id=user_id, is_active=True).all()
    if len(rows) != 1:
        raise OrganizationAccessError(
            "Organization context requires exactly one active membership."
        )
    return rows[0].organization_id


def _authenticated_user():
    if not has_request_context():
        return None
    if not getattr(current_user, "is_authenticated", False):
        return None
    return current_user


def get_current_organization_id() -> str:
    """Return the active organization ID for the current context.

    Authenticated HTTP: exactly one active UserMembership. Never silent ORG-001.
    Unauthenticated HTTP: fail closed (operating routes are login-gated).
    No request context (CLI / seed): DEFAULT_ORGANIZATION_ID.
    """
    user = _authenticated_user()
    if user is not None:
        org_id = resolve_membership_organization_id(user)
        g.organization_id = org_id
        return org_id
    if has_request_context():
        if getattr(g, "organization_id", None):
            return g.organization_id
        raise OrganizationAccessError(
            "Unauthenticated HTTP requests cannot use organization context."
        )
    return DEFAULT_ORGANIZATION_ID


def set_current_organization_id(org_id: str) -> None:
    """Set the active organization ID for unauthenticated / non-HTTP tests.

    Authenticated HTTP ignores this override and uses membership only.
    """
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
