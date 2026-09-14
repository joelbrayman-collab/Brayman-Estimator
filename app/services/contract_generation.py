"""FG-024 contract generation + immutable snapshot.

Reuses Slice A selector and ADR-037 via that selector. Does not own legal
approval or Native Signing. TECH-C merges a copy of the governed Family 05
master from the frozen snapshot and retains the DOCX bytes privately.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app import db
from app.models.estimate import EstimateVersion
from app.models.legal_content import LegalContentJurisdictionPackage
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_contract import (
    CONTRACT_STATUS_GENERATED,
    GENERATION_PROCESS_SLICE_C,
    GeneratedProjectContract,
    ProjectContractSnapshot,
    ProjectContractSnapshotObject,
)
from app.models.proposal import Proposal
from app.services.contract_artifact_storage import (
    read_retained_docx,
    store_immutable_docx,
)
from app.services.family_05_contract_merge import merge_family_05_from_frozen
from app.services.family_05_master import (
    FAMILY_05_MEDIA_TYPE,
)
from app.services.legal_content import (
    AUTHORITY_PRODUCTION,
    STATUS_ALLOW,
    STATUS_AVAILABLE,
    STATUS_WARN,
    select_legal_content_package_for_project,
)

STATUS_GENERATED = CONTRACT_STATUS_GENERATED
STATUS_BLOCK = "BLOCK"

BLOCK_ORGANIZATION_MISMATCH = "ORGANIZATION_MISMATCH"
BLOCK_PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
BLOCK_ESTIMATE_VERSION_NOT_FOUND = "ESTIMATE_VERSION_NOT_FOUND"
BLOCK_ESTIMATE_VERSION_NOT_PINNED = "ESTIMATE_VERSION_NOT_PINNED"
BLOCK_DRAFT_ESTIMATE_VERSION = "DRAFT_ESTIMATE_VERSION"
BLOCK_ESTIMATE_VERSION_NOT_ELIGIBLE = "ESTIMATE_VERSION_NOT_ELIGIBLE"
BLOCK_ESTIMATE_VERSION_NOT_LOCKED = "ESTIMATE_VERSION_NOT_LOCKED"
BLOCK_PROPOSAL_REQUIRED = "PROPOSAL_REQUIRED"
BLOCK_PROPOSAL_NOT_FOUND = "PROPOSAL_NOT_FOUND"
BLOCK_PROPOSAL_NOT_ELIGIBLE = "PROPOSAL_NOT_ELIGIBLE"
BLOCK_PROPOSAL_VERSION_MISMATCH = "PROPOSAL_VERSION_MISMATCH"
BLOCK_PROPOSAL_PROJECT_MISMATCH = "PROPOSAL_PROJECT_MISMATCH"
BLOCK_MISSING_COMMERCIAL_FACTS = "MISSING_COMMERCIAL_FACTS"
BLOCK_MISSING_PRESENTATION_MASTER = "MISSING_PRESENTATION_MASTER"
BLOCK_PRESENTATION_MASTER_SHA_MISMATCH = "PRESENTATION_MASTER_SHA_MISMATCH"
BLOCK_MISSING_REQUIRED_LEGAL_OBJECT = "MISSING_REQUIRED_LEGAL_OBJECT"
BLOCK_LEGAL_OBJECT_NOT_AUTHORITATIVE = "LEGAL_OBJECT_NOT_AUTHORITATIVE"
BLOCK_PENDING_REVIEW_UNSUPPORTED = "PENDING_REVIEW_UNSUPPORTED"
BLOCK_AI_CANNOT_GENERATE = "AI_CANNOT_GENERATE"
BLOCK_ACTOR_REQUIRED = "ACTOR_REQUIRED"

AUTHORITATIVE_OBJECT_STATES = frozenset({"APPROVED", "ACTIVE"})
REQUIRED_LEGAL_KIND = "contract_provision"
REQUIRED_WARRANTY_KIND = "warranty"
ONTARIO_REQUIRED_KINDS = (REQUIRED_LEGAL_KIND, REQUIRED_WARRANTY_KIND)
ELIGIBLE_VERSION_STATUSES = frozenset({"Issued", "Accepted"})
ELIGIBLE_PROPOSAL_STATUSES = frozenset({"Issued", "Accepted"})
GENERATION_ELIGIBLE_SELECTION = frozenset({STATUS_ALLOW, STATUS_WARN, STATUS_AVAILABLE})
PRESENTATION_FAMILY_CONTRACT = "05"
PRESENTATION_LEGAL_STATUS = "COMMERCIAL_DRAFT"
SHA256_HEX_LENGTH = 64
ONTARIO_PROVINCE_CODE = "CA-ON"

_AI_ACTORS = frozenset({"AI", "AUTOMATION"})


@dataclass(frozen=True)
class ContractGenerationResult:
    generated: bool
    status: str
    block_code: Optional[str]
    contract_id: Optional[int]
    snapshot_id: Optional[int]
    artifact_sha256: Optional[str]
    warn_code: Optional[str] = None


def _block(code: str) -> ContractGenerationResult:
    return ContractGenerationResult(
        generated=False,
        status=STATUS_BLOCK,
        block_code=code,
        contract_id=None,
        snapshot_id=None,
        artifact_sha256=None,
        warn_code=None,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(payload) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _money(value) -> str:
    return str(Decimal(value or 0).quantize(Decimal("0.01")))


def _normalize_master(raw) -> Optional[dict]:
    if not isinstance(raw, dict):
        return None
    family = str(raw.get("family_code") or "").strip()
    version = str(raw.get("version") or "").strip()
    filename = str(raw.get("filename") or "").strip()
    sha = str(raw.get("sha256") or "").strip().lower()
    if family != PRESENTATION_FAMILY_CONTRACT:
        return None
    if not version or not filename:
        return None
    if len(sha) != SHA256_HEX_LENGTH or any(ch not in "0123456789abcdef" for ch in sha):
        return None
    return {
        "family_code": family,
        "version": version,
        "filename": filename,
        "sha256": sha,
        "legal_status": PRESENTATION_LEGAL_STATUS,
    }


def _suggest_contract_number(organization_id: str, year: Optional[int] = None) -> str:
    year = year or datetime.utcnow().year
    prefix = f"CTR-{year}-"
    pattern = re.compile(rf"^CTR-{year}-(\d+)$", re.IGNORECASE)
    max_sequence = 0
    rows = GeneratedProjectContract.query.filter_by(
        organization_id=organization_id
    ).all()
    for row in rows:
        match = pattern.match((row.contract_number or "").strip())
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))
    return f"{prefix}{max_sequence + 1:04d}"


def _is_ontario_package(package: LegalContentJurisdictionPackage) -> bool:
    province = (package.province_or_state_code or "").strip()
    if province == ONTARIO_PROVINCE_CODE:
        return True
    code = ""
    if package.jurisdiction is not None:
        code = (package.jurisdiction.code or "").strip()
    return code == ONTARIO_PROVINCE_CODE or code.startswith(f"{ONTARIO_PROVINCE_CODE}-")


def _required_legal_kinds(package: LegalContentJurisdictionPackage):
    if _is_ontario_package(package):
        return ONTARIO_REQUIRED_KINDS
    return (REQUIRED_LEGAL_KIND,)


def _authoritative_objects(package: LegalContentJurisdictionPackage, kinds):
    allowed = frozenset(kinds)
    rows = [obj for obj in package.content_objects if obj.kind in allowed]
    return sorted(rows, key=lambda obj: (obj.kind, obj.version_number, obj.id))


def generate_project_contract(
    project_id: int,
    estimate_version_id: int,
    *,
    organization_id: str,
    presentation_master: dict,
    actor_identifier: str,
    actor_kind: str = "HUMAN",
    proposal_id: Optional[int] = None,
    as_of: Optional[date] = None,
    commit: bool = True,
    authority_class: str = AUTHORITY_PRODUCTION,
) -> ContractGenerationResult:
    """Generate a project contract artifact and freeze an immutable snapshot.

    Fail closed. Never falls back to generic NA, Family 05 legal text,
    Permit Rules, draft legal content, or cross-jurisdiction packages.
    Never auto-selects a Proposal. Candidate legal content is never authority.
    """
    kind = (actor_kind or "").strip().upper()
    actor = (actor_identifier or "").strip()
    if kind in _AI_ACTORS:
        return _block(BLOCK_AI_CANNOT_GENERATE)
    if not actor:
        return _block(BLOCK_ACTOR_REQUIRED)

    org = db.session.get(Organization, organization_id)
    if org is None:
        return _block(BLOCK_ORGANIZATION_MISMATCH)

    project = db.session.get(Project, project_id)
    if project is None:
        return _block(BLOCK_PROJECT_NOT_FOUND)
    if project.organization_id != organization_id:
        return _block(BLOCK_ORGANIZATION_MISMATCH)

    version = db.session.get(EstimateVersion, estimate_version_id)
    if version is None:
        return _block(BLOCK_ESTIMATE_VERSION_NOT_FOUND)
    estimate = version.estimate
    if estimate is None or estimate.project_id != project.id:
        return _block(BLOCK_ESTIMATE_VERSION_NOT_PINNED)

    if (version.status or "") == "Draft":
        return _block(BLOCK_DRAFT_ESTIMATE_VERSION)
    if version.status not in ELIGIBLE_VERSION_STATUSES:
        return _block(BLOCK_ESTIMATE_VERSION_NOT_ELIGIBLE)
    if not version.is_locked:
        return _block(BLOCK_ESTIMATE_VERSION_NOT_LOCKED)

    if proposal_id is None:
        return _block(BLOCK_PROPOSAL_REQUIRED)
    proposal = db.session.get(Proposal, proposal_id)
    if proposal is None:
        return _block(BLOCK_PROPOSAL_NOT_FOUND)
    if proposal.estimate_version_id != version.id:
        return _block(BLOCK_PROPOSAL_VERSION_MISMATCH)
    proposal_estimate = proposal.estimate
    if proposal_estimate is None or proposal_estimate.project_id != project.id:
        return _block(BLOCK_PROPOSAL_PROJECT_MISMATCH)
    if proposal.status not in ELIGIBLE_PROPOSAL_STATUSES:
        return _block(BLOCK_PROPOSAL_NOT_ELIGIBLE)

    client = project.client
    if client is None or client.organization_id != organization_id:
        return _block(BLOCK_ORGANIZATION_MISMATCH)
    client_name = (client.name or "").strip()
    project_name = (project.name or "").strip()
    project_address = (project.address or "").strip()
    estimate_number = (estimate.estimate_number or "").strip()
    if not client_name or not project_name or not estimate_number or not project_address:
        return _block(BLOCK_MISSING_COMMERCIAL_FACTS)
    if Decimal(version.total or 0) <= 0 and Decimal(version.subtotal or 0) <= 0:
        return _block(BLOCK_MISSING_COMMERCIAL_FACTS)

    master = _normalize_master(presentation_master)
    if master is None:
        return _block(BLOCK_MISSING_PRESENTATION_MASTER)

    selection = select_legal_content_package_for_project(
        project.id,
        as_of=as_of,
        authority_class=authority_class,
    )
    if not selection.available or selection.status not in GENERATION_ELIGIBLE_SELECTION:
        return _block(selection.block_code or "NO_ACTIVE_PACKAGE")

    package = db.session.get(LegalContentJurisdictionPackage, selection.package_id)
    if package is None or package.library_state != "ACTIVE":
        return _block("NO_ACTIVE_PACKAGE")

    required_kinds = _required_legal_kinds(package)
    objects = _authoritative_objects(package, required_kinds)
    present_kinds = {obj.kind for obj in objects}
    if any(kind not in present_kinds for kind in required_kinds):
        return _block(BLOCK_MISSING_REQUIRED_LEGAL_OBJECT)
    frozen_objects = []
    for obj in objects:
        body = (obj.body or "").strip()
        if obj.library_state not in AUTHORITATIVE_OBJECT_STATES:
            return _block(BLOCK_LEGAL_OBJECT_NOT_AUTHORITATIVE)
        if not body:
            return _block(BLOCK_MISSING_REQUIRED_LEGAL_OBJECT)
        frozen_objects.append(obj)

    generated_at = datetime.utcnow()
    warn_code = selection.warn_code if selection.status == STATUS_WARN else None
    pending_candidate_id = (
        selection.pending_candidate_id if selection.status == STATUS_WARN else None
    )
    commercial = {
        "organization_id": organization_id,
        "client_id": client.id,
        "client_name": client_name,
        "project_id": project.id,
        "project_name": project_name,
        "project_address": project_address,
        "site": project_address,
        "contract_date": generated_at.date().isoformat(),
        "estimate_id": estimate.id,
        "estimate_number": estimate_number,
        "estimate_version_id": version.id,
        "estimate_version_number": version.version_number,
        "estimate_version_status": version.status,
        "proposal_id": proposal.id,
        "proposal_number": proposal.proposal_number,
        "proposal_status": proposal.status,
        "subtotal": _money(version.subtotal),
        "tax_percent": _money(version.tax_percent),
        "total": _money(version.total),
    }
    legal_payload = [
        {
            "id": obj.id,
            "kind": obj.kind,
            "version_number": obj.version_number,
            "library_state": obj.library_state,
            "body": (obj.body or "").strip(),
        }
        for obj in frozen_objects
    ]
    legal_content_sha256 = _sha256_text(_canonical_json(legal_payload))
    commercial_sha256 = _sha256_text(_canonical_json(commercial))

    merged = merge_family_05_from_frozen(
        presentation_master=master,
        commercial=commercial,
        legal_objects=legal_payload,
    )
    if not merged.merged or not merged.docx_bytes:
        return _block(merged.block_code or BLOCK_MISSING_PRESENTATION_MASTER)
    storage_key, docx_sha256 = store_immutable_docx(
        organization_id,
        merged.docx_bytes,
    )

    artifact_lines = [
        "CALIBRAYTAI GENERATED CONTRACT ARTIFACT",
        "GENERATED DOCUMENT — NOT AN EXECUTED CONTRACT",
        "NOT FOR SIGNATURE",
        f"organization_id={organization_id}",
        f"client_id={client.id}",
        f"client_name={client_name}",
        f"project_id={project.id}",
        f"project_name={project_name}",
        f"jurisdiction_code={selection.jurisdiction_code}",
        f"package_id={package.id}",
        f"package_code={package.package_code}",
        f"package_library_state={package.library_state}",
        f"selection_status={selection.status}",
        f"warn_code={warn_code or ''}",
        f"pending_candidate_id={pending_candidate_id or ''}",
        "pending_candidate_used_as_authority=false",
        f"proposal_id={proposal.id}",
        f"proposal_number={proposal.proposal_number}",
        f"proposal_status={proposal.status}",
        f"estimate_version_id={version.id}",
        f"estimate_number={estimate_number}",
        f"presentation_family={master['family_code']}",
        f"presentation_master_sha256={master['sha256']}",
        f"presentation_legal_status={master['legal_status']}",
        f"legal_content_sha256={legal_content_sha256}",
        f"commercial_sha256={commercial_sha256}",
        f"artifact_storage_key={storage_key}",
        f"docx_sha256={docx_sha256}",
        "LEGAL CONTENT",
    ]
    for item in legal_payload:
        artifact_lines.append(
            f"object id={item['id']} kind={item['kind']} "
            f"v{item['version_number']} state={item['library_state']}"
        )
        artifact_lines.append(item["body"])
    artifact_lines.append("COMMERCIAL")
    artifact_lines.append(_canonical_json(commercial))
    artifact_text = "\n".join(artifact_lines) + "\n"
    artifact_sha256 = docx_sha256

    contract = GeneratedProjectContract(
        organization_id=organization_id,
        client_id=client.id,
        project_id=project.id,
        estimate_id=estimate.id,
        estimate_version_id=version.id,
        proposal_id=proposal.id,
        contract_number=_suggest_contract_number(organization_id),
        status=STATUS_GENERATED,
        artifact_sha256=artifact_sha256,
        artifact_storage_key=storage_key,
        artifact_media_type=FAMILY_05_MEDIA_TYPE,
        generated_at=generated_at,
        generated_by_identifier=actor,
        generation_process=GENERATION_PROCESS_SLICE_C,
        created_at=generated_at,
    )
    db.session.add(contract)
    db.session.flush()

    snapshot = ProjectContractSnapshot(
        generated_contract_id=contract.id,
        organization_id=organization_id,
        client_id=client.id,
        client_name=client_name,
        project_id=project.id,
        project_name=project_name,
        jurisdiction_definition_id=package.jurisdiction_definition_id,
        jurisdiction_code=selection.jurisdiction_code or "",
        package_id=package.id,
        package_code=package.package_code,
        package_library_state=package.library_state,
        package_support_status=package.support_status,
        package_effective_from=package.effective_from,
        package_effective_to=package.effective_to,
        legal_content_sha256=legal_content_sha256,
        presentation_family_code=master["family_code"],
        presentation_master_filename=master["filename"],
        presentation_master_version=master["version"],
        presentation_master_sha256=master["sha256"],
        presentation_legal_status=master["legal_status"],
        estimate_version_id=version.id,
        estimate_number=estimate_number,
        estimate_version_number=version.version_number,
        estimate_version_status=version.status,
        proposal_id=proposal.id,
        proposal_number=proposal.proposal_number,
        proposal_status=proposal.status,
        selection_status=selection.status,
        warn_code=warn_code,
        pending_candidate_id=pending_candidate_id,
        pending_candidate_used_as_authority=False,
        commercial_variables_json=commercial,
        commercial_sha256=commercial_sha256,
        artifact_text=artifact_text,
        artifact_sha256=artifact_sha256,
        artifact_storage_key=storage_key,
        artifact_media_type=FAMILY_05_MEDIA_TYPE,
        generated_at=generated_at,
        generated_by_identifier=actor,
        generation_process=GENERATION_PROCESS_SLICE_C,
        created_at=generated_at,
    )
    db.session.add(snapshot)
    db.session.flush()

    for obj in frozen_objects:
        body = (obj.body or "").strip()
        db.session.add(
            ProjectContractSnapshotObject(
                snapshot_id=snapshot.id,
                legal_content_object_id=obj.id,
                object_kind=obj.kind,
                object_version_number=obj.version_number,
                object_library_state=obj.library_state,
                object_body=body,
                object_sha256=_sha256_text(body),
            )
        )

    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return ContractGenerationResult(
        generated=True,
        status=STATUS_GENERATED,
        block_code=None,
        contract_id=contract.id,
        snapshot_id=snapshot.id,
        artifact_sha256=contract.artifact_sha256,
        warn_code=warn_code,
    )


def retrieve_generated_contract_docx(snapshot: ProjectContractSnapshot) -> Optional[bytes]:
    """Return retained merged DOCX bytes. Does not re-render from live state."""
    key = (snapshot.artifact_storage_key or "").strip()
    if not key:
        return None
    data = read_retained_docx(key)
    digest = hashlib.sha256(data).hexdigest()
    if digest != (snapshot.artifact_sha256 or "").lower():
        raise ValueError("Retained generated-contract bytes do not match frozen SHA-256.")
    return data


def generation_service_source() -> str:
    return inspect.getsource(generate_project_contract)
