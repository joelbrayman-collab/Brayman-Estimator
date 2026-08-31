"""Organization Brand Profile lifecycle and Proposal brand snapshots (FG-017)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from flask import current_app, has_app_context, has_request_context
from sqlalchemy import func

from app import db
from app.models.brand_profile import (
    BRAND_PROFILE_STATUSES,
    BRAND_SNAPSHOT_FREEZE_TRIGGERS,
    OrganizationBrandProfile,
    ProposalBrandSnapshot,
)
from app.models.organization import Organization
from app.models.proposal import Proposal
from app.services.brand_logo_storage import (
    BrandLogoStorageError,
    logo_mimetype,
    resolve_logo_filesystem_path,
    store_logo_bytes,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)

DEFAULT_PRIMARY_COLOR = "#1f3a5f"
DEFAULT_ACCENT_COLOR = "#c79a2b"
DEFAULT_BRAYMAN_STATIC_LOGO = "branding/brayman-construction-logo.png"


class BrandProfileServiceError(Exception):
    """Raised when a Brand Profile or snapshot operation cannot complete."""


@dataclass(frozen=True)
class BrandRenderContext:
    organization_id: str
    legal_name: str
    customer_facing_name: str
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    primary_color: str | None
    accent_color: str | None
    logo_sha256: str | None
    logo_extension: str | None
    logo_byte_size: int | None
    logo_original_filename: str | None
    frozen: bool
    source: str

    @property
    def display_primary_color(self) -> str:
        return (self.primary_color or "").strip() or DEFAULT_PRIMARY_COLOR

    @property
    def display_accent_color(self) -> str:
        return (self.accent_color or "").strip() or DEFAULT_ACCENT_COLOR

    @property
    def has_logo(self) -> bool:
        return bool(self.logo_sha256 and self.logo_extension)


def _actor_name() -> str:
    if has_request_context():
        from flask_login import current_user

        if getattr(current_user, "is_authenticated", False):
            name = (getattr(current_user, "display_name", None) or "").strip()
            if name:
                return name
    if has_app_context():
        return current_app.config.get("HISTORICAL_UPLOAD_ACTOR") or "Joel Brayman"
    return "Joel Brayman"


def _blank_to_none(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_name(value, field_label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise BrandProfileServiceError(f"{field_label} is required.")
    return text[:255]


def _optional_limited(value, length: int) -> str | None:
    text = _blank_to_none(value)
    if text is None:
        return None
    return text[:length]


def get_current_brand_profile(organization_id: str) -> OrganizationBrandProfile | None:
    return (
        OrganizationBrandProfile.query.filter_by(
            organization_id=organization_id,
            status="CURRENT",
        ).first()
    )


def get_proposal_brand_snapshot(proposal_id: int) -> ProposalBrandSnapshot | None:
    return ProposalBrandSnapshot.query.filter_by(proposal_id=proposal_id).first()


def resolve_proposal_organization_id(proposal) -> str:
    template = getattr(proposal, "proposal_template", None)
    if template is not None and template.organization_id:
        return template.organization_id
    estimate = getattr(proposal, "estimate", None)
    project = getattr(estimate, "project", None) if estimate is not None else None
    if project is not None and project.organization_id:
        return project.organization_id
    raise BrandProfileServiceError(
        "Proposal organization could not be resolved for Brand Profile."
    )


def _identity_from_organization(org: Organization) -> dict:
    return {
        "legal_name": org.legal_name,
        "customer_facing_name": org.display_name,
        "address": _blank_to_none(org.primary_address),
        "phone": None,
        "email": None,
        "website": None,
        "primary_color": None,
        "accent_color": None,
    }


def _copy_org001_static_logo() -> tuple[str, str, int, str] | None:
    if not has_app_context() or not current_app.static_folder:
        return None
    path = Path(current_app.static_folder) / DEFAULT_BRAYMAN_STATIC_LOGO
    if not path.is_file():
        return None
    data = path.read_bytes()
    digest, extension, byte_size, original = store_logo_bytes(
        DEFAULT_ORGANIZATION_ID,
        data,
        path.name,
    )
    return digest, extension, byte_size, original or path.name


def _next_version_number(organization_id: str) -> int:
    current_max = (
        db.session.query(func.max(OrganizationBrandProfile.version_number))
        .filter_by(organization_id=organization_id)
        .scalar()
    )
    return int(current_max or 0) + 1


def _insert_current_profile(
    organization_id: str,
    *,
    identity: dict,
    logo: tuple[str, str, int, str | None] | None,
    actor: str,
    prior: OrganizationBrandProfile | None,
) -> OrganizationBrandProfile:
    if prior is not None:
        prior.status = "SUPERSEDED"
        db.session.flush()

    profile = OrganizationBrandProfile(
        organization_id=organization_id,
        version_number=_next_version_number(organization_id),
        status="CURRENT",
        legal_name=identity["legal_name"],
        customer_facing_name=identity["customer_facing_name"],
        address=identity.get("address"),
        phone=identity.get("phone"),
        email=identity.get("email"),
        website=identity.get("website"),
        primary_color=identity.get("primary_color"),
        accent_color=identity.get("accent_color"),
        logo_sha256=logo[0] if logo else None,
        logo_extension=logo[1] if logo else None,
        logo_byte_size=logo[2] if logo else None,
        logo_original_filename=logo[3] if logo else None,
        created_by=actor,
    )
    db.session.add(profile)
    db.session.flush()
    if prior is not None:
        prior.superseded_by_id = profile.id
        db.session.flush()
    return profile


def ensure_current_brand_profile(
    organization_id: str,
    *,
    commit: bool = False,
) -> OrganizationBrandProfile:
    existing = get_current_brand_profile(organization_id)
    if existing is not None:
        return existing

    if organization_id == DEFAULT_ORGANIZATION_ID:
        org = ensure_default_organization(commit=False)
    else:
        org = Organization.query.get(organization_id)
        if org is None:
            raise BrandProfileServiceError(
                f"Organization '{organization_id}' was not found."
            )

    identity = _identity_from_organization(org)
    logo = None
    if organization_id == DEFAULT_ORGANIZATION_ID:
        try:
            logo = _copy_org001_static_logo()
        except BrandLogoStorageError as exc:
            raise BrandProfileServiceError(str(exc)) from exc

    profile = _insert_current_profile(
        organization_id,
        identity=identity,
        logo=logo,
        actor=_actor_name(),
        prior=None,
    )
    if commit:
        db.session.commit()
    return profile


def ensure_brand_profiles_for_existing_organizations(*, commit: bool = True) -> int:
    created = 0
    for org in Organization.query.order_by(Organization.id.asc()).all():
        before = get_current_brand_profile(org.id)
        profile = ensure_current_brand_profile(org.id, commit=False)
        if before is None and profile is not None:
            created += 1
    if commit:
        db.session.commit()
    return created


def _logo_tuple_from_profile(
    profile: OrganizationBrandProfile | None,
) -> tuple[str, str, int, str | None] | None:
    if profile is None or not profile.logo_sha256 or not profile.logo_extension:
        return None
    return (
        profile.logo_sha256,
        profile.logo_extension,
        profile.logo_byte_size,
        profile.logo_original_filename,
    )


def _identity_tuple(identity: dict, logo) -> tuple:
    return (
        identity["legal_name"],
        identity["customer_facing_name"],
        identity.get("address"),
        identity.get("phone"),
        identity.get("email"),
        identity.get("website"),
        identity.get("primary_color"),
        identity.get("accent_color"),
        logo[0] if logo else None,
        logo[1] if logo else None,
        logo[2] if logo else None,
        logo[3] if logo else None,
    )


def save_brand_profile(
    organization_id: str,
    *,
    legal_name,
    customer_facing_name,
    address=None,
    phone=None,
    email=None,
    website=None,
    primary_color=None,
    accent_color=None,
    logo_bytes: bytes | None = None,
    logo_filename: str | None = None,
    clear_logo: bool = False,
    actor: str | None = None,
    commit: bool = True,
) -> OrganizationBrandProfile:
    if logo_bytes and clear_logo:
        raise BrandProfileServiceError("Cannot replace and clear the logo in one save.")

    current = ensure_current_brand_profile(organization_id, commit=False)
    identity = {
        "legal_name": _required_name(legal_name, "Legal name"),
        "customer_facing_name": _required_name(
            customer_facing_name,
            "Customer-facing name",
        ),
        "address": _optional_limited(address, 255),
        "phone": _optional_limited(phone, 50),
        "email": _optional_limited(email, 150),
        "website": _optional_limited(website, 180),
        "primary_color": _optional_limited(primary_color, 20),
        "accent_color": _optional_limited(accent_color, 20),
    }

    logo = _logo_tuple_from_profile(current)
    if clear_logo:
        logo = None
    elif logo_bytes is not None:
        try:
            logo = store_logo_bytes(organization_id, logo_bytes, logo_filename)
        except BrandLogoStorageError as exc:
            raise BrandProfileServiceError(str(exc)) from exc

    current_identity = {
        "legal_name": current.legal_name,
        "customer_facing_name": current.customer_facing_name,
        "address": current.address,
        "phone": current.phone,
        "email": current.email,
        "website": current.website,
        "primary_color": current.primary_color,
        "accent_color": current.accent_color,
    }
    if _identity_tuple(identity, logo) == _identity_tuple(
        current_identity,
        _logo_tuple_from_profile(current),
    ):
        return current

    profile = _insert_current_profile(
        organization_id,
        identity=identity,
        logo=logo,
        actor=actor or _actor_name(),
        prior=current,
    )
    if commit:
        db.session.commit()
    return profile


def _context_from_record(record, *, frozen: bool, source: str) -> BrandRenderContext:
    return BrandRenderContext(
        organization_id=record.organization_id,
        legal_name=record.legal_name,
        customer_facing_name=record.customer_facing_name,
        address=record.address,
        phone=record.phone,
        email=record.email,
        website=record.website,
        primary_color=record.primary_color,
        accent_color=record.accent_color,
        logo_sha256=record.logo_sha256,
        logo_extension=record.logo_extension,
        logo_byte_size=record.logo_byte_size,
        logo_original_filename=record.logo_original_filename,
        frozen=frozen,
        source=source,
    )


def brand_render_context_from_profile(profile) -> BrandRenderContext:
    return _context_from_record(profile, frozen=False, source="current")


def get_proposal_brand_render_context(
    proposal,
    *,
    commit_ensure: bool = True,
) -> BrandRenderContext:
    snapshot = get_proposal_brand_snapshot(proposal.id)
    if snapshot is not None:
        return _context_from_record(snapshot, frozen=True, source="snapshot")
    org_id = resolve_proposal_organization_id(proposal)
    profile = ensure_current_brand_profile(org_id, commit=commit_ensure)
    return _context_from_record(profile, frozen=False, source="current")


def brand_logo_filesystem_path(context: BrandRenderContext) -> Path | None:
    if not context.has_logo:
        return None
    try:
        return resolve_logo_filesystem_path(
            context.organization_id,
            context.logo_sha256,
            context.logo_extension,
        )
    except BrandLogoStorageError:
        return None


def brand_logo_mimetype(context: BrandRenderContext) -> str:
    return logo_mimetype(context.logo_extension)


def freeze_proposal_brand_snapshot(
    proposal,
    freeze_trigger: str,
    *,
    actor: str | None = None,
    commit: bool = False,
) -> ProposalBrandSnapshot:
    if freeze_trigger not in BRAND_SNAPSHOT_FREEZE_TRIGGERS:
        raise BrandProfileServiceError("Invalid brand snapshot freeze trigger.")
    existing = get_proposal_brand_snapshot(proposal.id)
    if existing is not None:
        return existing

    org_id = resolve_proposal_organization_id(proposal)
    profile = ensure_current_brand_profile(org_id, commit=False)
    snapshot = ProposalBrandSnapshot(
        proposal_id=proposal.id,
        organization_id=org_id,
        source_brand_profile_id=profile.id,
        freeze_trigger=freeze_trigger,
        legal_name=profile.legal_name,
        customer_facing_name=profile.customer_facing_name,
        address=profile.address,
        phone=profile.phone,
        email=profile.email,
        website=profile.website,
        primary_color=profile.primary_color,
        accent_color=profile.accent_color,
        logo_sha256=profile.logo_sha256,
        logo_extension=profile.logo_extension,
        logo_byte_size=profile.logo_byte_size,
        logo_original_filename=profile.logo_original_filename,
        frozen_at=datetime.utcnow(),
        frozen_by=actor or _actor_name(),
    )
    db.session.add(snapshot)
    db.session.flush()
    if commit:
        db.session.commit()
    return snapshot


def maybe_freeze_proposal_brand_snapshot(proposal, *, commit: bool = False):
    if proposal is None:
        return None
    if proposal.status == "Issued":
        return freeze_proposal_brand_snapshot(
            proposal,
            "ISSUED",
            commit=commit,
        )
    if proposal.status == "Accepted":
        existing = get_proposal_brand_snapshot(proposal.id)
        if existing is not None:
            return existing
        return freeze_proposal_brand_snapshot(
            proposal,
            "ACCEPTED",
            commit=commit,
        )
    return None


def backfill_proposal_brand_snapshots(*, commit: bool = True) -> int:
    """Freeze Issued/Accepted proposals that have no brand snapshot.

    Copies the organization's CURRENT Brand Profile. Does not read
    ProposalTemplate company identity fields and does not alter commercial
    proposal columns.
    """
    created = 0
    proposals = (
        Proposal.query.filter(Proposal.status.in_(("Issued", "Accepted")))
        .order_by(Proposal.id.asc())
        .all()
    )
    for proposal in proposals:
        if get_proposal_brand_snapshot(proposal.id) is not None:
            continue
        freeze_proposal_brand_snapshot(
            proposal,
            "MIGRATION_BACKFILL",
            commit=False,
        )
        created += 1
    if commit:
        db.session.commit()
    return created
