"""Deterministic jurisdiction resolution (FG-015 / ADR-037). No geocoder, web, or AI."""

from datetime import datetime
from typing import Optional

from app import db
from app.models.jurisdiction import (
    JURISDICTION_ALIAS_SEED,
    JURISDICTION_SEED,
    JurisdictionAlias,
    JurisdictionDefinition,
    normalize_jurisdiction_text,
)
from app.models.organization import Organization


class JurisdictionResolutionError(ValueError):
    """Fail-closed jurisdiction helper error."""


def ensure_jurisdiction_seed(*, commit: bool = False) -> int:
    """Insert missing platform jurisdiction nodes and aliases. Idempotent."""
    existing = {
        code for (code,) in db.session.query(JurisdictionDefinition.code).all()
    }
    added = 0
    now = datetime.utcnow()
    code_to_row = {
        row.code: row for row in JurisdictionDefinition.query.all()
    }
    for item in JURISDICTION_SEED:
        if item["code"] in existing:
            continue
        parent = None
        if item["parent_code"]:
            parent = code_to_row.get(item["parent_code"])
            if parent is None:
                parent = JurisdictionDefinition.query.filter_by(
                    code=item["parent_code"]
                ).first()
        row = JurisdictionDefinition(
            code=item["code"],
            kind=item["kind"],
            name=item["name"],
            parent_id=parent.id if parent else None,
            ahj_name=item["ahj_name"],
            created_at=now,
        )
        db.session.add(row)
        db.session.flush()
        code_to_row[row.code] = row
        added += 1

    existing_aliases = {
        (alias.jurisdiction_id, alias.normalized_alias)
        for alias in JurisdictionAlias.query.all()
    }
    for code, alias in JURISDICTION_ALIAS_SEED:
        node = code_to_row.get(code) or JurisdictionDefinition.query.filter_by(
            code=code
        ).first()
        if node is None:
            continue
        normalized = normalize_jurisdiction_text(alias)
        if (node.id, normalized) in existing_aliases:
            continue
        db.session.add(
            JurisdictionAlias(
                jurisdiction_id=node.id,
                alias=alias,
                normalized_alias=normalized,
            )
        )
        existing_aliases.add((node.id, normalized))
        added += 1

    if added and commit:
        db.session.commit()
    elif added:
        db.session.flush()
    return added


def _match_definition(text: str, kind: str, parent: Optional[JurisdictionDefinition]):
    needle = normalize_jurisdiction_text(text)
    if not needle:
        return None
    query = JurisdictionDefinition.query.filter_by(kind=kind)
    if parent is None:
        query = query.filter(JurisdictionDefinition.parent_id.is_(None))
    else:
        query = query.filter_by(parent_id=parent.id)
    for row in query.all():
        if normalize_jurisdiction_text(row.name) == needle:
            return row
        if normalize_jurisdiction_text(row.code) == needle:
            return row
        if kind == "province_state" and normalize_jurisdiction_text(
            row.code.split("-")[-1]
        ) == needle:
            return row

    alias_query = (
        JurisdictionAlias.query.join(JurisdictionDefinition)
        .filter(
            JurisdictionAlias.normalized_alias == needle,
            JurisdictionDefinition.kind == kind,
        )
    )
    if parent is None:
        alias_query = alias_query.filter(JurisdictionDefinition.parent_id.is_(None))
    else:
        alias_query = alias_query.filter(JurisdictionDefinition.parent_id == parent.id)
    alias = alias_query.first()
    if alias is None:
        return None
    return alias.jurisdiction


def resolve_jurisdiction(
    country: Optional[str],
    province_state: Optional[str],
    municipality: Optional[str],
    *,
    tax_jurisdiction: Optional[str] = None,
) -> Optional[JurisdictionDefinition]:
    """Resolve municipality AHJ from stored civic fields only.

    ``tax_jurisdiction`` is accepted only so callers cannot accidentally rely
    on it: it is ignored.
    """
    del tax_jurisdiction  # Organization.tax_jurisdiction is never used.
    ensure_jurisdiction_seed(commit=False)
    country_node = _match_definition(country or "", "country", None)
    if country_node is None:
        return None
    province_node = _match_definition(
        province_state or "", "province_state", country_node
    )
    if province_node is None:
        return None
    return _match_definition(municipality or "", "municipality", province_node)


def assert_platform_jurisdiction_not_org_mutable():
    """No org-scoped write API exists; used by tests."""
    return not hasattr(Organization, "jurisdiction_definitions")
