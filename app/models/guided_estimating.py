"""Guided Project Estimating (Joel, 23 Oct 2026): the project's construction scope and its estimating progress.

Orchestration state only. Quantities, costs, quotes, approvals and prices stay in the existing estimate,
scope-delivery, subcontract-quote, costing and pricing records; this module never stores a cost of its own
except the amount of an allowance a person approved for a stage (which is also put on the estimate as an
ordinary Allowance line, so the estimate stays the one authoritative cost).

- GuidedEstimate: one per project; the project type and contractor role that chose the stage template, the
  estimate it works on, whether the scope is still a draft, and where the person stopped (Resume).
- GuidedEstimateStage: one construction stage, or one subcomponent of a stage (parent_stage_id). Each carries
  exactly one of INTERNAL, SUBCONTRACTED or NA, or nothing yet (undecided; allowed only while the scope is a
  draft). A stage split into subcomponents is decided part by part.
- GuidedEstimateEvent: append-only history of scope decisions, completions, reopenings and revisions.
- CalculatorResultCarry: a completed calculator result kept while the person creates the project it belongs
  to ("Create New Project" from a calculator), so the calculation is never entered twice.
"""

from datetime import datetime

from sqlalchemy.orm import validates

from app import db

PROJECT_NEW_HOME = "NEW_HOME"
PROJECT_ADDITION = "ADDITION_RENOVATION"
PROJECT_GARAGE = "GARAGE_OUTBUILDING"
PROJECT_FOUNDATION = "FOUNDATION_ONLY"
PROJECT_OTHER = "OTHER"
PROJECT_TYPES = (PROJECT_NEW_HOME, PROJECT_ADDITION, PROJECT_GARAGE, PROJECT_FOUNDATION, PROJECT_OTHER)
PROJECT_TYPE_LABELS = {
    PROJECT_NEW_HOME: "New Home Construction",
    PROJECT_ADDITION: "Addition / Renovation",
    PROJECT_GARAGE: "Garage / Outbuilding",
    PROJECT_FOUNDATION: "Foundation Only",
    PROJECT_OTHER: "Other project",
}

ROLE_GENERAL_CONTRACTOR = "GENERAL_CONTRACTOR"
ROLE_SELECTED_PORTIONS = "SELECTED_PORTIONS"
ROLE_SUBCONTRACTOR = "SUBCONTRACTOR"
CONTRACTOR_ROLES = (ROLE_GENERAL_CONTRACTOR, ROLE_SELECTED_PORTIONS, ROLE_SUBCONTRACTOR)
CONTRACTOR_ROLE_LABELS = {
    ROLE_GENERAL_CONTRACTOR: "General Contractor",
    ROLE_SELECTED_PORTIONS: "Contractor performing selected portions",
    ROLE_SUBCONTRACTOR: "Subcontractor performing a defined scope",
}

SCOPE_DRAFT = "DRAFT"
SCOPE_FINALIZED = "FINALIZED"
SCOPE_STATUSES = (SCOPE_DRAFT, SCOPE_FINALIZED)

RESP_INTERNAL = "INTERNAL"
RESP_SUBCONTRACTED = "SUBCONTRACTED"
RESP_NA = "NA"
RESPONSIBILITIES = (RESP_INTERNAL, RESP_SUBCONTRACTED, RESP_NA)
RESPONSIBILITY_LABELS = {RESP_INTERNAL: "Internal", RESP_SUBCONTRACTED: "Subcontracted", RESP_NA: "N/A"}

STATUS_NOT_STARTED = "NOT_STARTED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_WAITING_FOR_QUOTE = "WAITING_FOR_QUOTE"
STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
STATUS_COMPLETE = "COMPLETE"
STATUS_EXCLUDED = "EXCLUDED"
STAGE_STATUSES = (STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_WAITING_FOR_QUOTE, STATUS_NEEDS_REVIEW,
                  STATUS_COMPLETE, STATUS_EXCLUDED)
STATUS_LABELS = {
    STATUS_NOT_STARTED: "Not Started",
    STATUS_IN_PROGRESS: "In Progress",
    STATUS_WAITING_FOR_QUOTE: "Waiting for Quote",
    STATUS_NEEDS_REVIEW: "Needs Review",
    STATUS_COMPLETE: "Complete",
    STATUS_EXCLUDED: "Excluded / N/A",
}

BASIS_CONFIRMED_COSTS = "CONFIRMED_COSTS"
BASIS_APPROVED_ALLOWANCE = "APPROVED_ALLOWANCE"
BASIS_AUTHORIZED_ZERO_COST = "AUTHORIZED_ZERO_COST"
COMPLETION_BASES = (BASIS_CONFIRMED_COSTS, BASIS_APPROVED_ALLOWANCE, BASIS_AUTHORIZED_ZERO_COST)
BASIS_LABELS = {
    BASIS_CONFIRMED_COSTS: "Confirmed costs",
    BASIS_APPROVED_ALLOWANCE: "Approved allowance",
    BASIS_AUTHORIZED_ZERO_COST: "Authorized no-cost decision",
}


class GuidedEstimate(db.Model):
    __tablename__ = "guided_estimates"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "project_id", name="uq_guided_estimates_project"),
        db.CheckConstraint(
            "project_type IN ('NEW_HOME', 'ADDITION_RENOVATION', 'GARAGE_OUTBUILDING', 'FOUNDATION_ONLY', 'OTHER')",
            name="ck_guided_estimates_project_type"),
        db.CheckConstraint(
            "contractor_role IN ('GENERAL_CONTRACTOR', 'SELECTED_PORTIONS', 'SUBCONTRACTOR')",
            name="ck_guided_estimates_contractor_role"),
        db.CheckConstraint("scope_status IN ('DRAFT', 'FINALIZED')", name="ck_guided_estimates_scope_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False,
                           index=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey("estimates.id", ondelete="RESTRICT"), nullable=True,
                            index=True)
    project_type = db.Column(db.String(40), nullable=False)
    contractor_role = db.Column(db.String(40), nullable=False)
    scope_status = db.Column(db.String(20), nullable=False, default=SCOPE_DRAFT)
    scope_finalized_at = db.Column(db.DateTime, nullable=True)
    scope_finalized_by = db.Column(db.String(150), nullable=True)
    last_stage_id = db.Column(db.Integer, nullable=True)  # where the person stopped (Resume); no FK, a pointer
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    project = db.relationship("Project")
    estimate = db.relationship("Estimate")
    stages = db.relationship(
        "GuidedEstimateStage",
        back_populates="guided_estimate",
        order_by="GuidedEstimateStage.sort_order, GuidedEstimateStage.id",
    )

    @validates("project_type")
    def _v_type(self, key, value):
        if value not in PROJECT_TYPES:
            raise ValueError("Choose what is being built.")
        return value

    @validates("contractor_role")
    def _v_role(self, key, value):
        if value not in CONTRACTOR_ROLES:
            raise ValueError("Choose your role on this project.")
        return value

    @property
    def project_type_label(self):
        return PROJECT_TYPE_LABELS.get(self.project_type, self.project_type)

    @property
    def contractor_role_label(self):
        return CONTRACTOR_ROLE_LABELS.get(self.contractor_role, self.contractor_role)

    @property
    def top_stages(self):
        return [s for s in self.stages if s.parent_stage_id is None]


class GuidedEstimateStage(db.Model):
    __tablename__ = "guided_estimate_stages"
    __table_args__ = (
        db.UniqueConstraint("guided_estimate_id", "stage_key", name="uq_guided_estimate_stages_key"),
        db.CheckConstraint("responsibility IS NULL OR responsibility IN ('INTERNAL', 'SUBCONTRACTED', 'NA')",
                           name="ck_guided_estimate_stages_responsibility"),
        db.CheckConstraint(
            "status IN ('NOT_STARTED', 'IN_PROGRESS', 'WAITING_FOR_QUOTE', 'NEEDS_REVIEW', 'COMPLETE', 'EXCLUDED')",
            name="ck_guided_estimate_stages_status"),
        db.CheckConstraint(
            "completion_basis IS NULL OR completion_basis IN "
            "('CONFIRMED_COSTS', 'APPROVED_ALLOWANCE', 'AUTHORIZED_ZERO_COST')",
            name="ck_guided_estimate_stages_completion_basis"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    guided_estimate_id = db.Column(db.Integer, db.ForeignKey("guided_estimates.id", ondelete="RESTRICT"),
                                   nullable=False, index=True)
    parent_stage_id = db.Column(db.Integer, db.ForeignKey("guided_estimate_stages.id", ondelete="RESTRICT"),
                                nullable=True, index=True)
    stage_key = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(180), nullable=False)
    explanation = db.Column(db.String(400), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_custom = db.Column(db.Boolean, nullable=False, default=False)
    is_split = db.Column(db.Boolean, nullable=False, default=False)  # decided part by part (subcomponents)
    responsibility = db.Column(db.String(20), nullable=True)  # None = not decided yet
    status = db.Column(db.String(30), nullable=False, default=STATUS_NOT_STARTED)
    scope_description = db.Column(db.Text, nullable=True)  # what the subcontractor (or crew) is to do
    na_reason = db.Column(db.Text, nullable=True)
    decided_by = db.Column(db.String(150), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    completion_basis = db.Column(db.String(30), nullable=True)
    completed_by = db.Column(db.String(150), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    allowance_amount = db.Column(db.Numeric(14, 2), nullable=True)
    allowance_approved_by = db.Column(db.String(150), nullable=True)
    allowance_approved_at = db.Column(db.DateTime, nullable=True)
    allowance_line_id = db.Column(db.Integer, db.ForeignKey("estimate_line_items.id", ondelete="SET NULL"),
                                  nullable=True)
    zero_cost_reason = db.Column(db.Text, nullable=True)
    zero_cost_authorized_by = db.Column(db.String(150), nullable=True)
    zero_cost_authorized_at = db.Column(db.DateTime, nullable=True)
    quote_requested_at = db.Column(db.DateTime, nullable=True)
    quote_requested_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    guided_estimate = db.relationship("GuidedEstimate", back_populates="stages")
    parent = db.relationship("GuidedEstimateStage", remote_side=[id], backref="children_rows")

    @validates("responsibility")
    def _v_resp(self, key, value):
        if value in ("", None):
            return None
        if value not in RESPONSIBILITIES:
            raise ValueError("Choose Internal, Subcontracted or N/A.")
        return value

    @validates("status")
    def _v_status(self, key, value):
        if value not in STAGE_STATUSES:
            raise ValueError("Stage status is not recognized.")
        return value

    @validates("completion_basis")
    def _v_basis(self, key, value):
        if value in ("", None):
            return None
        if value not in COMPLETION_BASES:
            raise ValueError("Completion basis is not recognized.")
        return value

    @property
    def children(self):
        return sorted(self.children_rows, key=lambda s: (s.sort_order, s.id))

    @property
    def responsibility_label(self):
        if self.is_split:
            return "Mixed (by part)"
        return RESPONSIBILITY_LABELS.get(self.responsibility, "Not decided")

    @property
    def section_name(self):
        """The estimate section that holds this stage's (or part's) lines."""
        if self.parent is not None:
            return f"{self.parent.display_name} — {self.display_name}"[:180]
        return self.display_name[:180]


class GuidedEstimateEvent(db.Model):
    """Append-only history of the guided estimate."""

    __tablename__ = "guided_estimate_events"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    guided_estimate_id = db.Column(db.Integer, db.ForeignKey("guided_estimates.id", ondelete="RESTRICT"),
                                   nullable=False, index=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("guided_estimate_stages.id", ondelete="RESTRICT"),
                         nullable=True, index=True)
    event = db.Column(db.String(40), nullable=False)
    from_value = db.Column(db.String(40), nullable=True)
    to_value = db.Column(db.String(40), nullable=True)
    detail = db.Column(db.String(600), nullable=True)
    estimate_version_id = db.Column(db.Integer, db.ForeignKey("estimate_versions.id", ondelete="RESTRICT"),
                                    nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    stage = db.relationship("GuidedEstimateStage")


class CalculatorResultCarry(db.Model):
    """A completed calculator result kept while its project is created (Option C)."""

    __tablename__ = "calculator_result_carries"
    __table_args__ = (db.UniqueConstraint("token", name="uq_calculator_result_carries_token"),)

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    token = db.Column(db.String(64), nullable=False)
    calculator = db.Column(db.String(40), nullable=False)
    summary = db.Column(db.String(600), nullable=False)
    entered = db.Column(db.JSON, nullable=False)
    result_text = db.Column(db.Text, nullable=False)
    payload = db.Column(db.JSON, nullable=True)       # the calculator's Contract V1 result, when it has one
    form_state = db.Column(db.JSON, nullable=True)    # [[field name, value], ...] to show the result again
    return_path = db.Column(db.String(300), nullable=False)
    project_calculation_id = db.Column(db.Integer, db.ForeignKey("project_calculations.id", ondelete="SET NULL"),
                                       nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    consumed_at = db.Column(db.DateTime, nullable=True)
