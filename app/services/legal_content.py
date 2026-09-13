"""FG-024 Slice A legal-content package selection. Fail closed. Empty library valid."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.models import Project
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.organization import Organization
from app.services.jurisdiction import resolve_jurisdiction

STATUS_AVAILABLE = "AVAILABLE"
STATUS_BLOCK = "BLOCK"

BLOCK_JURISDICTION_UNRESOLVED = "JURISDICTION_UNRESOLVED"
BLOCK_JURISDICTION_NOT_SUPPORTED = "JURISDICTION_NOT_SUPPORTED"
BLOCK_NO_ACTIVE_PACKAGE = "NO_ACTIVE_PACKAGE"
BLOCK_PACKAGE_NOT_ACTIVE = "PACKAGE_NOT_ACTIVE"
BLOCK_PACKAGE_NOT_EFFECTIVE = "PACKAGE_NOT_EFFECTIVE"
BLOCK_PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT = (
    "PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT"
)
BLOCK_EFFECTIVE_DATE_UNRESOLVED = "EFFECTIVE_DATE_UNRESOLVED"
BLOCK_COVERAGE_LIMITED = "COVERAGE_LIMITED"


@dataclass(frozen=True)
class LegalContentSelection:
    available: bool
    status: str
    block_code: Optional[str]
    package_id: Optional[int]
    jurisdiction_code: Optional[str]
    library_state: Optional[str]
    support_status: Optional[str]


def _block(
    code: str,
    *,
    package: Optional[LegalContentJurisdictionPackage] = None,
    jurisdiction_code: Optional[str] = None,
) -> LegalContentSelection:
    return LegalContentSelection(
        available=False,
        status=STATUS_BLOCK,
        block_code=code,
        package_id=package.id if package is not None else None,
        jurisdiction_code=(
            jurisdiction_code
            if jurisdiction_code is not None
            else (package.jurisdiction.code if package is not None else None)
        ),
        library_state=package.library_state if package is not None else None,
        support_status=package.support_status if package is not None else None,
    )


def _available(package: LegalContentJurisdictionPackage) -> LegalContentSelection:
    return LegalContentSelection(
        available=True,
        status=STATUS_AVAILABLE,
        block_code=None,
        package_id=package.id,
        jurisdiction_code=package.jurisdiction.code,
        library_state=package.library_state,
        support_status=package.support_status,
    )


def _packages_for_node(node: JurisdictionDefinition):
    return LegalContentJurisdictionPackage.query.filter_by(
        jurisdiction_definition_id=node.id
    ).all()


def _active_package(node: JurisdictionDefinition):
    return LegalContentJurisdictionPackage.query.filter_by(
        jurisdiction_definition_id=node.id,
        library_state="ACTIVE",
    ).one_or_none()


def _selection_nodes(municipal: JurisdictionDefinition):
    """Province/state first; municipal only as a more specific ACTIVE candidate.

    Never include the country node (generic Canada / USA / North America).
    """
    province = municipal.parent
    nodes = []
    if province is not None and province.kind == "province_state":
        nodes.append(province)
    if municipal.kind == "municipality":
        nodes.append(municipal)
    return nodes


def _block_for_non_active_rows(rows, jurisdiction_code: str) -> LegalContentSelection:
    if not rows:
        return _block(
            BLOCK_JURISDICTION_NOT_SUPPORTED,
            jurisdiction_code=jurisdiction_code,
        )
    if all(row.library_state == "SUPERSEDED" for row in rows):
        return _block(
            BLOCK_PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT,
            package=rows[0],
            jurisdiction_code=jurisdiction_code,
        )
    preferred = None
    for state in ("APPROVED", "COUNSEL_REVIEW", "PROPOSED"):
        preferred = next((row for row in rows if row.library_state == state), None)
        if preferred is not None:
            break
    if preferred is None:
        return _block(
            BLOCK_NO_ACTIVE_PACKAGE,
            package=rows[0],
            jurisdiction_code=jurisdiction_code,
        )
    return _block(
        BLOCK_PACKAGE_NOT_ACTIVE,
        package=preferred,
        jurisdiction_code=jurisdiction_code,
    )


def _evaluate_active(package: LegalContentJurisdictionPackage, as_of: date):
    if package.support_status == "LIMITED":
        return _block(BLOCK_COVERAGE_LIMITED, package=package)
    if package.effective_date_unresolved():
        return _block(BLOCK_EFFECTIVE_DATE_UNRESOLVED, package=package)
    if not package.is_effective_on(as_of):
        return _block(BLOCK_PACKAGE_NOT_EFFECTIVE, package=package)
    return _available(package)


def select_legal_content_package_for_project(
    project_id: int,
    *,
    as_of: Optional[date] = None,
) -> LegalContentSelection:
    """Return AVAILABLE or a deterministic BLOCK. Never invents legal authority.

    Reuses ADR-037 / FG-015 ``resolve_jurisdiction``. Does not consult
    Organization.tax_jurisdiction, Permit Rules, or FG-022 presentation masters.
    """
    day = as_of or date.today()
    project = Project.query.get(project_id)
    if project is None:
        return _block(BLOCK_JURISDICTION_UNRESOLVED)

    location = project.location
    if location is None:
        return _block(BLOCK_JURISDICTION_UNRESOLVED)

    municipal = resolve_jurisdiction(
        location.country,
        location.province_state,
        location.municipality,
        tax_jurisdiction=None,
    )
    if municipal is None:
        return _block(BLOCK_JURISDICTION_UNRESOLVED)

    nodes = _selection_nodes(municipal)
    if not nodes:
        return _block(
            BLOCK_JURISDICTION_NOT_SUPPORTED,
            jurisdiction_code=municipal.code,
        )

    municipal_node = nodes[-1] if municipal.kind == "municipality" else None
    province_node = nodes[0] if nodes[0].kind == "province_state" else None

    if municipal_node is not None:
        municipal_active = _active_package(municipal_node)
        if municipal_active is not None:
            return _evaluate_active(municipal_active, day)

    if province_node is not None:
        province_active = _active_package(province_node)
        if province_active is not None:
            return _evaluate_active(province_active, day)

    scoped_rows = []
    for node in nodes:
        scoped_rows.extend(_packages_for_node(node))
    jurisdiction_code = (
        province_node.code if province_node is not None else municipal.code
    )
    return _block_for_non_active_rows(scoped_rows, jurisdiction_code)


def assert_platform_library_not_org_mutable():
    """Library tables are platform-governed; no org-scoped package owner."""
    return not hasattr(Organization, "legal_content_jurisdiction_packages")
