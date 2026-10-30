"""Governed work packages (Joel, 30 Oct 2026).

Selected work (``GuidedEstimateStage``) is the governed work package and the single scope owner.
See docs/architecture/estimate-to-project-lifecycle.md, approved decisions 3 and 4.

This module owns the commercial side of a package:

- **Commercial status.** INCLUDED or EXCLUDED. Excluding is non-destructive: every line, calculation, quote,
  requirement and history row stays. Only the package's participation in Brayman's price and its responsible
  party change.
- **Responsible party.** Brayman when included. When excluded: By Others (the default), the Client / Owner, or a
  named party such as Lockwood.
- **Delivery method.** Self-performed, subcontracted, material only, labour only or allowance. Derived from the
  existing Internal / Subcontracted responsibility unless set.
- **Shared packages.** General conditions that participate while any contractor work is included (the proven
  Paulusse rule), or always.
- **Participation.** Which estimate lines count in the direct cost, the selling price and the customer documents.

Removing work (responsibility N/A, ``selected_work.remove_work``) stays a separate statement: the work is not
part of the project at all.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from app import db
from app.models.guided_estimating import (
    COMMERCIAL_EXCLUDED,
    COMMERCIAL_INCLUDED,
    DELIVERY_ALLOWANCE,
    DELIVERY_LABELS,
    DELIVERY_METHODS,
    DELIVERY_SELF_PERFORMED,
    DELIVERY_SUBCONTRACTED,
    PARTY_BY_OTHERS,
    PARTY_CLIENT,
    PARTY_CONTRACTOR,
    PARTY_NAMED,
    RESP_INTERNAL,
    RESP_NA,
    RESP_SUBCONTRACTED,
    RESPONSIBLE_PARTIES,
    SHARED_ALWAYS,
    SHARED_RULES,
    SHARED_WHILE_ANY_INCLUDED,
    GuidedEstimateStage,
)

_REJECTED_ACTORS = {"", "system", "ai", "automatic", "calibraytai", "calibrayt", "claude"}


class WorkPackageError(ValueError):
    """A work-package change that cannot be made; the message is for the contractor."""


def _actor(actor) -> str:
    name = (actor or "").strip()
    if name.lower() in _REJECTED_ACTORS:
        raise WorkPackageError("A person must make this scope decision.")
    return name[:150]


def _now():
    return datetime.utcnow()


# ---------------------------------------------------------------------------------------------- reading
def package_of(stage: Optional[GuidedEstimateStage]) -> Optional[GuidedEstimateStage]:
    """The governed work package for a stage or one of its parts."""
    if stage is None:
        return None
    return stage.parent if stage.parent is not None else stage


def package_of_section(section) -> Optional[GuidedEstimateStage]:
    return package_of(getattr(section, "guided_stage", None))


def is_removed(package: GuidedEstimateStage) -> bool:
    return package.responsibility == RESP_NA


def is_included(package: GuidedEstimateStage) -> bool:
    return package.commercial_status == COMMERCIAL_INCLUDED


def _productive_included(guided) -> bool:
    for row in guided.top_stages:
        if row.shared_rule is None and not is_removed(row) and is_included(row):
            return True
    return False


def package_participates(package: Optional[GuidedEstimateStage]) -> bool:
    """Whether the package's lines count in Brayman's price."""
    if package is None:
        return True  # a section no package governs (manual or older estimates) is priced as before
    if not is_included(package):
        return False
    if package.shared_rule == SHARED_ALWAYS:
        return True
    if package.shared_rule == SHARED_WHILE_ANY_INCLUDED:
        return _productive_included(package.guided_estimate)
    return True


def section_participates(section) -> bool:
    return package_participates(package_of_section(section))


def line_participates(line) -> bool:
    section = getattr(line, "section", None)
    return section is None or section_participates(section)


def participating_lines(version) -> List:
    """The lines that make up Brayman's price, in section order."""
    out = []
    for section in version.sections:
        if section_participates(section):
            out.extend(section.line_items)
    return out


def delivery_method(package: GuidedEstimateStage) -> Optional[str]:
    if package.delivery_method:
        return package.delivery_method
    if package.allowance_amount is not None:
        return DELIVERY_ALLOWANCE
    if package.is_split:
        return None  # decided part by part
    return {RESP_INTERNAL: DELIVERY_SELF_PERFORMED, RESP_SUBCONTRACTED: DELIVERY_SUBCONTRACTED}.get(
        package.responsibility)


def delivery_label(package: GuidedEstimateStage) -> str:
    method = delivery_method(package)
    if method is None:
        return "Mixed (by part)" if package.is_split else "Not decided"
    return DELIVERY_LABELS[method]


def responsible_label(package: GuidedEstimateStage, *, contractor_name: str = "Brayman Construction") -> str:
    if is_included(package):
        return contractor_name
    party = package.responsible_party or PARTY_BY_OTHERS
    if party == PARTY_CLIENT:
        return "Owner / Client"
    if party == PARTY_NAMED and package.responsible_party_name:
        return package.responsible_party_name
    if party == PARTY_CONTRACTOR:
        return contractor_name
    return "By Others"


def customer_exclusion_text(package: GuidedEstimateStage, *, contractor_name: str = "Brayman Construction") -> str:
    """The proven customer wording: 'Excluded from Brayman Construction scope / By Others' or '...; by Lockwood'."""
    base = f"Excluded from {contractor_name} scope"
    party = package.responsible_party or PARTY_BY_OTHERS
    if party == PARTY_NAMED and package.responsible_party_name:
        return f"{base}; by {package.responsible_party_name}"
    if party == PARTY_CLIENT:
        return f"{base}; by the Owner / Client"
    return f"{base} / By Others"


def packages(guided) -> List[GuidedEstimateStage]:
    """The governed work packages of a scope: every top-level selected work item not removed from the project."""
    if guided is None:
        return []
    return [row for row in guided.top_stages if not is_removed(row)]


def package_lines(package: GuidedEstimateStage, version) -> List:
    rows = [package] + list(package.children)
    ids = {row.id for row in rows}
    return [line for section in version.sections if section.guided_stage_id in ids for line in section.line_items]


def customer_scope(version, *, contractor_name: str = "Brayman Construction") -> dict:
    """The customer's view of the scope: what is included in Brayman's price and what is excluded, with whom.

    Both lists come from the same package selections that drive the price, so the customer documents cannot
    drift from the estimate."""
    from app.models.guided_estimating import GuidedEstimate

    estimate_id = getattr(version, "estimate_id", None)
    guided = GuidedEstimate.query.filter_by(estimate_id=estimate_id).first() if estimate_id else None
    included, excluded = [], []
    for package in packages(guided):
        entry = {
            "id": package.id,
            "name": package.display_name,
            "description": (package.scope_description or package.explanation or "").strip()
            if not package.is_custom or package.scope_description else "",
            "shared": package.shared_rule is not None,
        }
        if package_participates(package):
            entry["sell_price"] = sum((line.sell_price or 0) for line in package_lines(package, version))
            included.append(entry)
        elif not is_included(package):
            entry["responsible"] = responsible_label(package, contractor_name=contractor_name)
            entry["text"] = customer_exclusion_text(package, contractor_name=contractor_name)
            excluded.append(entry)
    return {"governed": guided is not None, "included": included, "excluded": excluded}


# ---------------------------------------------------------------------------------------------- changing
def _event(package, event, *, actor, from_value=None, to_value=None, detail=None, user_id=None):
    from app.services import guided_estimating as G

    G._event(package.guided_estimate, event, actor=actor, stage=package, from_value=from_value, to_value=to_value,
             detail=detail, user_id=user_id)


def _require_package(package):
    if package is None or package.parent is not None:
        raise WorkPackageError("Choose the work, not a part of it.")
    if is_removed(package):
        raise WorkPackageError("That work was removed from the project.")


def _require_editable(package):
    from app.services import guided_estimating as G

    version = G.current_version(package.guided_estimate)
    if version is not None and not G.version_is_editable(version):
        raise WorkPackageError("The estimate is approved or issued. Make a new version to change its scope.")
    return version


def _refresh_commercials(version, actor, user_id=None) -> dict:
    """After a participation change: re-approve the costing if it was otherwise current, and re-apply pricing if it
    had been applied. This uses the same steps as a project labour-rate or margin change."""
    from app.services.estimate_costing import (
        approve_all_costing,
        current_costing_snapshot,
        working_matches_costing_snapshot,
    )
    from app.services.pricing_engine import apply_resolved_pricing_to_version

    if version is None:
        return {"reapproved": False, "repriced": False}
    costing = current_costing_snapshot(version)
    had_pricing = getattr(version, "pricing_snapshot", None) is not None
    reapproved = repriced = False
    if costing is not None and not working_matches_costing_snapshot(version, costing):
        approve_all_costing(version, actor=actor, user_id=user_id, commit=False)
        reapproved = True
    costing_now = current_costing_snapshot(version)
    if had_pricing and costing_now is not None and working_matches_costing_snapshot(version, costing_now):
        apply_resolved_pricing_to_version(version, actor=actor)
        repriced = True
    else:
        from app.services.estimate_builder import recalculate_version

        recalculate_version(version)
    db.session.flush()
    return {"reapproved": reapproved, "repriced": repriced}


def exclude_work(package, *, actor, party: str = PARTY_BY_OTHERS, party_name: str = "", reason: str = "",
                 user_id=None) -> dict:
    """Exclude a package from Brayman's price. Nothing is deleted."""
    name = _actor(actor)
    _require_package(package)
    version = _require_editable(package)
    party = (party or PARTY_BY_OTHERS).strip().upper()
    if party not in RESPONSIBLE_PARTIES or party == PARTY_CONTRACTOR:
        raise WorkPackageError("Choose who does the excluded work: By Others, the Owner / Client, or a named party.")
    label = " ".join((party_name or "").split())[:160]
    if party == PARTY_NAMED and not label:
        raise WorkPackageError("Name the party responsible for the excluded work.")
    before = (package.commercial_status, package.responsible_party, package.responsible_party_name)
    package.commercial_status = COMMERCIAL_EXCLUDED
    package.responsible_party = party
    package.responsible_party_name = label if party == PARTY_NAMED else None
    package.commercial_reason = (reason or "").strip() or None
    package.commercial_decided_by = name
    package.commercial_decided_at = _now()
    package.updated_at = _now()
    if before != (package.commercial_status, package.responsible_party, package.responsible_party_name):
        _event(package, "WORK_EXCLUDED", actor=name, from_value=before[0], to_value=COMMERCIAL_EXCLUDED,
               detail=f"{package.display_name}: {responsible_label(package)}"
                      + (f"; reason: {package.commercial_reason}" if package.commercial_reason else ""),
               user_id=user_id)
    result = _refresh_commercials(version, name, user_id)
    db.session.commit()
    return result


def include_work(package, *, actor, reason: str = "", user_id=None) -> dict:
    """Bring an excluded package back into Brayman's price. Its preserved lines count again."""
    name = _actor(actor)
    _require_package(package)
    version = _require_editable(package)
    if is_included(package):
        return {"reapproved": False, "repriced": False}
    package.commercial_status = COMMERCIAL_INCLUDED
    package.responsible_party = None
    package.responsible_party_name = None
    package.commercial_reason = (reason or "").strip() or None
    package.commercial_decided_by = name
    package.commercial_decided_at = _now()
    package.updated_at = _now()
    _event(package, "WORK_INCLUDED", actor=name, from_value=COMMERCIAL_EXCLUDED, to_value=COMMERCIAL_INCLUDED,
           detail=package.display_name, user_id=user_id)
    result = _refresh_commercials(version, name, user_id)
    db.session.commit()
    return result


def set_responsible_party(package, *, actor, party: str, party_name: str = "", user_id=None) -> None:
    """Change who does excluded work, without changing the price."""
    name = _actor(actor)
    _require_package(package)
    _require_editable(package)
    if is_included(package):
        raise WorkPackageError("Included work is Brayman's. Exclude it first to name who does it.")
    party = (party or "").strip().upper()
    if party not in RESPONSIBLE_PARTIES or party == PARTY_CONTRACTOR:
        raise WorkPackageError("Choose By Others, the Owner / Client, or a named party.")
    label = " ".join((party_name or "").split())[:160]
    if party == PARTY_NAMED and not label:
        raise WorkPackageError("Name the party responsible for the excluded work.")
    before = responsible_label(package)
    package.responsible_party = party
    package.responsible_party_name = label if party == PARTY_NAMED else None
    package.commercial_decided_by = name
    package.commercial_decided_at = _now()
    _event(package, "RESPONSIBLE_PARTY", actor=name, from_value=before[:80],
           to_value=responsible_label(package)[:80], detail=package.display_name, user_id=user_id)
    db.session.commit()


def set_delivery_method(package, *, actor, method: Optional[str], user_id=None) -> None:
    name = _actor(actor)
    _require_package(package)
    _require_editable(package)
    method = (method or "").strip().upper() or None
    if method is not None and method not in DELIVERY_METHODS:
        raise WorkPackageError("Choose how the work is delivered.")
    before = delivery_method(package)
    package.delivery_method = method
    if method == DELIVERY_SUBCONTRACTED and not package.is_split:
        package.responsibility = RESP_SUBCONTRACTED
    elif method == DELIVERY_SELF_PERFORMED and not package.is_split:
        package.responsibility = RESP_INTERNAL
    _event(package, "DELIVERY_METHOD", actor=name, from_value=before, to_value=delivery_method(package),
           detail=package.display_name, user_id=user_id)
    db.session.commit()


def set_shared(package, *, actor, rule: Optional[str], user_id=None) -> dict:
    """Mark a package as shared / general conditions (or ordinary again). It decides when its costs count."""
    name = _actor(actor)
    _require_package(package)
    version = _require_editable(package)
    rule = (rule or "").strip().upper() or None
    if rule is not None and rule not in SHARED_RULES:
        raise WorkPackageError("Choose when the shared costs count.")
    before = package.shared_rule
    package.shared_rule = rule
    _event(package, "SHARED_RULE", actor=name, from_value=before, to_value=rule, detail=package.display_name,
           user_id=user_id)
    result = _refresh_commercials(version, name, user_id)
    db.session.commit()
    return result


def lines_of(packages_: Iterable[GuidedEstimateStage], version) -> List:
    out = []
    for package in packages_:
        out.extend(package_lines(package, version))
    return out
