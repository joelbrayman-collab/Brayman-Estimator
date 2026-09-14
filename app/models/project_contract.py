"""FG-024 Slice C generated project contract + immutable snapshot.

Organization-scoped and project-tied. Not a second legal-content library.
Not Native Signing. Status GENERATED is not execution.
"""

from datetime import datetime

from app import db

CONTRACT_STATUS_GENERATED = "GENERATED"
GENERATED_CONTRACT_STATUSES = (CONTRACT_STATUS_GENERATED,)

GENERATION_PROCESS_SLICE_C = "fg024_slice_c"


class GeneratedProjectContract(db.Model):
    """Org-scoped generated contract / execution-package instance."""

    __tablename__ = "project_generated_contracts"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('GENERATED')",
            name="ck_project_generated_contracts_status",
        ),
        db.UniqueConstraint(
            "organization_id",
            "contract_number",
            name="uq_project_generated_contracts_org_number",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("estimates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey("proposals.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    contract_number = db.Column(db.String(40), nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=CONTRACT_STATUS_GENERATED,
        index=True,
    )
    artifact_sha256 = db.Column(db.String(64), nullable=False, index=True)
    artifact_storage_key = db.Column(db.String(255), nullable=True)
    artifact_media_type = db.Column(db.String(120), nullable=True)
    generated_at = db.Column(db.DateTime, nullable=False)
    generated_by_identifier = db.Column(db.String(150), nullable=False)
    generation_process = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    snapshot = db.relationship(
        "ProjectContractSnapshot",
        back_populates="generated_contract",
        uselist=False,
    )

    def __repr__(self):
        return (
            f"<GeneratedProjectContract {self.contract_number} "
            f"{self.status} id={self.id}>"
        )


class ProjectContractSnapshot(db.Model):
    """Immutable pin of legal + commercial + presentation used at generation."""

    __tablename__ = "project_contract_snapshots"
    __table_args__ = (
        db.UniqueConstraint(
            "generated_contract_id",
            name="uq_project_contract_snapshots_generated_contract_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    generated_contract_id = db.Column(
        db.Integer,
        db.ForeignKey("project_generated_contracts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organization_id = db.Column(db.String(50), nullable=False)
    client_id = db.Column(db.Integer, nullable=False)
    client_name = db.Column(db.String(150), nullable=False)
    project_id = db.Column(db.Integer, nullable=False)
    project_name = db.Column(db.String(180), nullable=False)
    jurisdiction_definition_id = db.Column(db.Integer, nullable=False)
    jurisdiction_code = db.Column(db.String(64), nullable=False)
    package_id = db.Column(db.Integer, nullable=False)
    package_code = db.Column(db.String(80), nullable=False)
    package_library_state = db.Column(db.String(20), nullable=False)
    package_support_status = db.Column(db.String(32), nullable=False)
    package_effective_from = db.Column(db.Date, nullable=True)
    package_effective_to = db.Column(db.Date, nullable=True)
    legal_content_sha256 = db.Column(db.String(64), nullable=False)
    presentation_family_code = db.Column(db.String(16), nullable=False)
    presentation_master_filename = db.Column(db.String(255), nullable=False)
    presentation_master_version = db.Column(db.String(40), nullable=False)
    presentation_master_sha256 = db.Column(db.String(64), nullable=False)
    presentation_legal_status = db.Column(db.String(40), nullable=False)
    estimate_version_id = db.Column(db.Integer, nullable=False)
    estimate_number = db.Column(db.String(50), nullable=False)
    estimate_version_number = db.Column(db.Integer, nullable=False)
    estimate_version_status = db.Column(db.String(50), nullable=False)
    proposal_id = db.Column(db.Integer, nullable=True, index=True)
    proposal_number = db.Column(db.String(50), nullable=True)
    proposal_status = db.Column(db.String(50), nullable=True)
    selection_status = db.Column(db.String(20), nullable=True)
    warn_code = db.Column(db.String(40), nullable=True)
    pending_candidate_id = db.Column(db.Integer, nullable=True)
    pending_candidate_used_as_authority = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )
    commercial_variables_json = db.Column(db.JSON, nullable=False)
    commercial_sha256 = db.Column(db.String(64), nullable=False)
    artifact_text = db.Column(db.Text, nullable=False)
    artifact_sha256 = db.Column(db.String(64), nullable=False)
    artifact_storage_key = db.Column(db.String(255), nullable=True)
    artifact_media_type = db.Column(db.String(120), nullable=True)
    generated_at = db.Column(db.DateTime, nullable=False)
    generated_by_identifier = db.Column(db.String(150), nullable=False)
    generation_process = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    generated_contract = db.relationship(
        "GeneratedProjectContract",
        back_populates="snapshot",
    )
    content_objects = db.relationship(
        "ProjectContractSnapshotObject",
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="ProjectContractSnapshotObject.id",
    )

    def __repr__(self):
        return f"<ProjectContractSnapshot {self.artifact_sha256[:12]}>"


class ProjectContractSnapshotObject(db.Model):
    """Frozen legal-content object identity/version/body used at generation."""

    __tablename__ = "project_contract_snapshot_objects"

    id = db.Column(db.Integer, primary_key=True)
    snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("project_contract_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    legal_content_object_id = db.Column(db.Integer, nullable=False)
    object_kind = db.Column(db.String(40), nullable=False)
    object_version_number = db.Column(db.Integer, nullable=False)
    object_library_state = db.Column(db.String(20), nullable=False)
    object_body = db.Column(db.Text, nullable=False)
    object_sha256 = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    snapshot = db.relationship(
        "ProjectContractSnapshot",
        back_populates="content_objects",
    )

    def __repr__(self):
        return (
            f"<ProjectContractSnapshotObject {self.object_kind} "
            f"v{self.object_version_number}>"
        )
