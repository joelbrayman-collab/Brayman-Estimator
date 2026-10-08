"""Brayman Construction Ontario V1 interim contract package.

Installed on the existing legal-content library. Not a second contract engine.
Not counsel-reviewed. counsel_approved_at stays null.

A later counsel-reviewed package replaces this row through
activate_legal_content(..., supersede_package_id=this package).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app import db
from app.models.jurisdiction import JurisdictionDefinition
from app.models.legal_content import (
    LegalContentActivationEvent,
    LegalContentJurisdictionPackage,
    LegalContentObject,
)
from app.services.jurisdiction import ensure_jurisdiction_seed

INTERIM_PACKAGE_CODE = "CA-ON-BRAYMAN-V1-INTERIM"
INTERIM_PACKAGE_TITLE = "Brayman V1 Interim Contract"
INTERIM_EFFECTIVE_FROM = date(2026, 10, 7)
INTERIM_OBJECT_VERSION = 1
ONTARIO_JURISDICTION_CODE = "CA-ON"
INTERIM_ACTOR = "Brayman Construction"
INTERIM_AUTHORIZATION = "Brayman V1 Interim Authorization"
INTERIM_PROVENANCE = (
    "BRAYMAN V1 INTERIM. Internal Brayman Construction Ontario package. "
    "External counsel has not reviewed this package. "
    "Replaceable by a later counsel-reviewed production package through "
    "the existing activation path. This row is not a counsel approval. "
    f"Authorization: {INTERIM_AUTHORIZATION}."
)

CONTRACT_PROVISION_BODY = """\
BRAYMAN V1 INTERIM CONTRACT PACKAGE
Ontario. Version 1. Effective 2026-10-07.
Status: Brayman V1 Interim. External counsel has not reviewed this package.

Parties. The contractor is Brayman Construction Inc., 411 St. John Street, Merrickville, ON K0G 1N0. The owner is the customer named on this generated contract.

Project. The project is the project name and site named on this generated contract.

Scope. The work is the work in the accepted proposal and the locked estimate named on this generated contract. Work that is not on that proposal is not in this contract. Qualifications printed on the presentation page do not remove work the accepted proposal includes.

Contract documents. This generated contract, the accepted proposal, and the locked estimate are the contract documents for this project. The contract snapshot records the package and version used.

Price. The contract amount is the total named on this generated contract.

Payment. The owner pays the contract amount as the accepted proposal states. This package does not add a deposit, a progress draw, or a holdback figure that is not written on that proposal. Generating this contract does not send an invoice.

Changes. A change to the work is a change order. The change is not part of this contract until the change order is recorded. A change order does not rewrite this snapshot.

Allowances. An allowance on the estimate is an allowance. It is not a fixed price for that item unless the accepted proposal says it is.

Schedule. Dates are the dates on the project schedule. A date that is not scheduled is not a promise in this contract.

Delays. If the site or the owner stops the work, the schedule moves with the dates that are recorded. This package does not create a delay claim or a delay penalty.

Site conditions. The site is the address on this generated contract. Brayman works from the site conditions known when the estimate was locked. A condition that was not known then is handled as a change order when it changes the work.

Owner responsibilities. The owner gives access to the site and the decisions the work needs.

Contractor responsibilities. Brayman performs the work in the accepted proposal.

Subcontractors. A subcontractor is the party named on Scope Delivery when Brayman is not doing that work. Naming a subcontractor does not by itself change the contract amount.

Materials. Brayman supplies the material the estimate says Brayman supplies. A supplier estimate request asks a supplier for a price. It is not this contract, and the supplier does not approve Brayman's cost.

Permits. A permit report is not a permit and is not this contract. Permit work is included only when the accepted proposal includes it.

Inspections. An inspection is recorded when it happens. This package does not state an inspection result.

Insurance. Brayman carries the insurance the company already holds. This package does not state a coverage amount.

Deficiencies. Unfinished or defective work in the accepted proposal stays on the punch list until it is corrected. A punch-list item does not by itself change the contract amount.

Substantial completion. The work is performed when the work in the accepted proposal is done. This package does not issue a certificate.

Termination. Joel records the end of the work. This package does not add a termination penalty.

Suspension. Joel records a stop in the work. The schedule then follows the dates that are recorded.

Disputes. A dispute is raised in writing with Joel. The parties deal with it directly before either starts a proceeding.

Responsibility. Each party is responsible for its own work and decisions under this contract. This package does not add a liability cap or a waiver that external counsel has not written.

Notices. A notice is a written note to Joel or to the customer named on this contract.

Governing law. This contract is governed by the law of Ontario, Canada.

Entire agreement. This generated contract and its snapshot are the agreement for this project. A later package does not rewrite this snapshot.

Amendments. A change to this agreement is a change order or a new contract snapshot. It is not an edit of this snapshot.

Assignment. Brayman does not assign this contract under this package.

Signatures. Generating this contract does not sign it. It does not send a signing link. A signature, when it is used, is a separate signing step.

Document hierarchy. The contract snapshot is the record of what was generated. The accepted proposal and the locked estimate are the commercial facts frozen on that snapshot. If a presentation line conflicts with the accepted proposal, the accepted proposal governs the work.

Electronic execution. When signing is used, it uses the existing signing step. This generation is not that step.
"""

WARRANTY_BODY = """\
BRAYMAN V1 INTERIM WARRANTY
Ontario. Version 1. Effective 2026-10-07.
This warranty is part of the Brayman V1 Interim contract package. External counsel has not reviewed it.

Brayman corrects a defect in the work described in the accepted proposal when the owner reports that defect in writing to Joel. A manufacturer warranty, if the manufacturer gives one, is the manufacturer's warranty.

This package does not state a statutory warranty period. Words typed on a proposal are not this warranty. This is not a counsel-reviewed warranty schedule.
"""


@dataclass(frozen=True)
class InterimInstallResult:
    package: LegalContentJurisdictionPackage | None
    created: bool
    blocked_by_active_package: bool


@dataclass(frozen=True)
class InterimStageResult:
    package: LegalContentJurisdictionPackage | None
    created: bool


def ensure_brayman_v1_interim_ontario_package(
    *,
    actor_identifier: str = INTERIM_ACTOR,
    commit: bool = True,
) -> InterimInstallResult:
    """Insert the interim package when Ontario has no active package.

    Idempotent. Does not reactivate a superseded interim row.
    Does not replace a different active package.
    Does not set counsel_approved_at.
    """
    ensure_jurisdiction_seed(commit=False)
    node = JurisdictionDefinition.query.filter_by(code=ONTARIO_JURISDICTION_CODE).one()
    existing = LegalContentJurisdictionPackage.query.filter_by(
        package_code=INTERIM_PACKAGE_CODE
    ).one_or_none()
    if existing is not None:
        return InterimInstallResult(
            package=existing,
            created=False,
            blocked_by_active_package=False,
        )

    active = LegalContentJurisdictionPackage.query.filter_by(
        jurisdiction_definition_id=node.id,
        library_state="ACTIVE",
    ).one_or_none()
    if active is not None:
        return InterimInstallResult(
            package=active,
            created=False,
            blocked_by_active_package=True,
        )

    now = datetime.utcnow()
    actor = (actor_identifier or INTERIM_ACTOR).strip() or INTERIM_ACTOR
    package = LegalContentJurisdictionPackage(
        package_code=INTERIM_PACKAGE_CODE,
        jurisdiction_definition_id=node.id,
        country_code="CA",
        province_or_state_code="CA-ON",
        support_status="SUPPORTED",
        library_state="ACTIVE",
        authority_class="PRODUCTION",
        effective_from=INTERIM_EFFECTIVE_FROM,
        effective_to=None,
        counsel_approved_at=None,
        counsel_approved_by=None,
        activated_at=now,
        activated_by=actor,
        provenance=INTERIM_PROVENANCE,
        created_at=now,
    )
    db.session.add(package)
    db.session.flush()
    db.session.add(
        LegalContentObject(
            package_id=package.id,
            kind="contract_provision",
            version_number=INTERIM_OBJECT_VERSION,
            library_state="ACTIVE",
            source_citation=INTERIM_PROVENANCE,
            body=CONTRACT_PROVISION_BODY.strip(),
            created_at=now,
        )
    )
    db.session.add(
        LegalContentObject(
            package_id=package.id,
            kind="warranty",
            version_number=INTERIM_OBJECT_VERSION,
            library_state="ACTIVE",
            source_citation=INTERIM_PROVENANCE,
            body=WARRANTY_BODY.strip(),
            created_at=now,
        )
    )
    db.session.add(
        LegalContentActivationEvent(
            package_id=package.id,
            action="ACTIVATE",
            actor_kind="HUMAN",
            actor_identifier=actor,
            predecessor_package_id=None,
            created_at=now,
        )
    )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return InterimInstallResult(
        package=package,
        created=True,
        blocked_by_active_package=False,
    )


def stage_brayman_v1_interim_ontario_package(
    *,
    commit: bool = True,
) -> InterimStageResult:
    """Create the interim package as APPROVED. Does not activate or supersede.

    Counsel fields stay empty. Brayman internal authorization is recorded in
    provenance. Activation remains activate_legal_content.
    """
    ensure_jurisdiction_seed(commit=False)
    node = JurisdictionDefinition.query.filter_by(code=ONTARIO_JURISDICTION_CODE).one()
    existing = LegalContentJurisdictionPackage.query.filter_by(
        package_code=INTERIM_PACKAGE_CODE
    ).one_or_none()
    if existing is not None:
        return InterimStageResult(package=existing, created=False)

    now = datetime.utcnow()
    package = LegalContentJurisdictionPackage(
        package_code=INTERIM_PACKAGE_CODE,
        jurisdiction_definition_id=node.id,
        country_code="CA",
        province_or_state_code="CA-ON",
        support_status="SUPPORTED",
        library_state="APPROVED",
        authority_class="PRODUCTION",
        effective_from=INTERIM_EFFECTIVE_FROM,
        effective_to=None,
        counsel_approved_at=None,
        counsel_approved_by=None,
        activated_at=None,
        activated_by=None,
        provenance=INTERIM_PROVENANCE,
        created_at=now,
    )
    db.session.add(package)
    db.session.flush()
    db.session.add(
        LegalContentObject(
            package_id=package.id,
            kind="contract_provision",
            version_number=INTERIM_OBJECT_VERSION,
            library_state="APPROVED",
            source_citation=INTERIM_PROVENANCE,
            body=CONTRACT_PROVISION_BODY.strip(),
            created_at=now,
        )
    )
    db.session.add(
        LegalContentObject(
            package_id=package.id,
            kind="warranty",
            version_number=INTERIM_OBJECT_VERSION,
            library_state="APPROVED",
            source_citation=INTERIM_PROVENANCE,
            body=WARRANTY_BODY.strip(),
            created_at=now,
        )
    )
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return InterimStageResult(package=package, created=True)
