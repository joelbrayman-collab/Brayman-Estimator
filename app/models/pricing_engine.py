"""Pricing Engine models (FG-009 / ADR-025 / ADR-030)."""

from datetime import datetime
from decimal import Decimal

from app import db
from app.services.organizations import get_current_organization_id


# Labour at the labour rate with no margin; materials at cost + true gross margin; equipment, delivery and other
# direct costs at cost; subcontracts at cost + the subcontract markup (Joel, 2 Nov 2026).
LABOUR_AT_RATE_MATERIAL_MARGIN = "LABOUR_AT_RATE_MATERIAL_MARGIN"

PRICING_METHODS = (
    "TRUE_GROSS_MARGIN",
    "COST_PLUS_MARKUP",
    "COST_PLUS_MARKUP_STACK",
    LABOUR_AT_RATE_MATERIAL_MARGIN,
)

POLICY_APPROVAL_STATUSES = (
    "DRAFT",
    "ORG_APPROVED",
    "SUPERSEDED",
    "WITHDRAWN",
)

OVERHEAD_TREATMENTS = (
    "UNSPECIFIED",
    "NOT_APPLIED",
    "DIRECT_PROJECT_COST",
    "INCLUDED_IN_MARGIN_ECONOMICS",
    "SEPARATELY_CUSTOMER_PRICED",
)

PROFIT_TREATMENTS = (
    "UNSPECIFIED",
    "NOT_APPLIED",
    "INCLUDED_IN_MARGIN_ECONOMICS",
    "SEPARATELY_CUSTOMER_PRICED",
)

CONTINGENCY_VISIBILITIES = (
    "UNSPECIFIED",
    "INTERNAL_RESERVE",
    "CUSTOMER_PRICED",
    "NOT_APPLIED",
)

# Math-only: no extra commercial layer is applied. These are not the same
# governance fact — UNSPECIFIED means not yet selected; NOT_APPLIED is an
# org-approved decision that the layer is not applied.
NO_SELECTED_COMMERCIAL_LAYER = frozenset({"UNSPECIFIED", "NOT_APPLIED"})

CONTINGENCY_PRICING_TREATMENTS = (
    "INCLUDED_IN_MARGIN_BASIS",
    "ADDED_AFTER_BASE_PRICING",
)

RESOLUTION_SOURCES = (
    "ESTIMATE_OVERRIDE",
    "COMMERCIAL_CONTEXT",
    "ORG_APPROVED_ACTIVE",
    "ORGANIZATION_DEFAULT",
    "CALIBAI_BASELINE",
    "PROVISIONAL_LEGACY_STACK",
)

AI_ACTOR_TOKENS = frozenset({"AI", "CALIBAI-AI", "SYSTEM-AI"})


class OrganizationPricingPolicy(db.Model):
    __tablename__ = "organization_pricing_policies"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "policy_code",
            "version_number",
            name="uq_org_pricing_policies_org_code_version",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    policy_code = db.Column(db.String(80), nullable=False)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    method = db.Column(db.String(40), nullable=False)
    target_gross_margin = db.Column(db.Numeric(10, 6), nullable=True)
    markup_rate = db.Column(db.Numeric(10, 6), nullable=True)
    stack_overhead_percent = db.Column(db.Numeric(8, 2), nullable=True)
    stack_profit_percent = db.Column(db.Numeric(8, 2), nullable=True)
    overhead_treatment = db.Column(
        db.String(40), nullable=False, default="UNSPECIFIED"
    )
    profit_treatment = db.Column(
        db.String(40), nullable=False, default="UNSPECIFIED"
    )
    contingency_source = db.Column(db.String(120), nullable=True)
    contingency_visibility = db.Column(
        db.String(40), nullable=False, default="UNSPECIFIED"
    )
    contingency_pricing_treatment = db.Column(db.String(40), nullable=True)
    contingency_rate = db.Column(db.Numeric(10, 6), nullable=True)
    tax_jurisdiction = db.Column(db.String(80), nullable=True)
    tax_percent = db.Column(db.Numeric(8, 2), nullable=True)
    # LABOUR_AT_RATE_MATERIAL_MARGIN: subcontracts at cost x (1 + this fraction); None is 0 (Joel, 2 Nov 2026).
    subcontract_markup_rate = db.Column(db.Numeric(10, 6), nullable=True)
    # Company pricing rules by cost type (Joel, 2 Nov 2026 rulings): equipment, delivery, other direct cost and
    # unclassified change-order item markups, as JSON (pricing_engine.policy_rules). None: the defaults (0 %; an
    # unclassified item takes the material margin).
    pricing_rules_json = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    approval_status = db.Column(db.String(20), nullable=False, default="DRAFT")
    effective_from = db.Column(db.DateTime, nullable=True)
    effective_to = db.Column(db.DateTime, nullable=True)
    provenance = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.String(150), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    superseded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_pricing_policies.id"),
        nullable=True,
    )
    created_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = db.relationship("Organization")

    def __repr__(self):
        return (
            f"<OrganizationPricingPolicy {self.organization_id} "
            f"{self.policy_code} v{self.version_number}>"
        )


class EstimatePricingSnapshot(db.Model):
    __tablename__ = "estimate_pricing_snapshots"
    __table_args__ = (
        db.UniqueConstraint(
            "estimate_version_id",
            name="uq_estimate_pricing_snapshots_version",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    estimate_version_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_versions.id"),
        nullable=False,
        index=True,
    )
    costing_snapshot_id = db.Column(
        db.Integer,
        db.ForeignKey("estimate_costing_snapshots.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    policy_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_pricing_policies.id"),
        nullable=True,
        index=True,
    )
    policy_code = db.Column(db.String(80), nullable=True)
    policy_version_number = db.Column(db.Integer, nullable=True)
    method = db.Column(db.String(40), nullable=False)
    resolution_source = db.Column(db.String(40), nullable=False)
    requires_review = db.Column(db.Boolean, nullable=False, default=False)
    override_reason = db.Column(db.Text, nullable=True)
    direct_cost_basis = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    target_gross_margin = db.Column(db.Numeric(10, 6), nullable=True)
    markup_rate = db.Column(db.Numeric(10, 6), nullable=True)
    stack_overhead_percent = db.Column(db.Numeric(8, 2), nullable=True)
    stack_profit_percent = db.Column(db.Numeric(8, 2), nullable=True)
    contingency_source = db.Column(db.String(120), nullable=True)
    contingency_visibility = db.Column(db.String(40), nullable=False)
    contingency_pricing_treatment = db.Column(db.String(40), nullable=True)
    contingency_rate = db.Column(db.Numeric(10, 6), nullable=True)
    contingency_amount = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    overhead_treatment = db.Column(db.String(40), nullable=False)
    profit_treatment = db.Column(db.String(40), nullable=False)
    pricing_posture = db.Column(db.String(50), nullable=True)
    execution_risk = db.Column(db.String(50), nullable=True)
    tax_jurisdiction = db.Column(db.String(80), nullable=True)
    tax_percent = db.Column(db.Numeric(8, 2), nullable=False, default=Decimal("0"))
    # LABOUR_AT_RATE_MATERIAL_MARGIN parameters, frozen with the price (2 Nov 2026).
    labour_rate = db.Column(db.Numeric(10, 2), nullable=True)
    subcontract_markup_rate = db.Column(db.Numeric(10, 6), nullable=True)
    pricing_rules_json = db.Column(db.Text, nullable=True)  # the cost-type rules used, frozen with the price
    pre_tax_selling_price = db.Column(
        db.Numeric(14, 2), nullable=False, default=Decimal("0")
    )
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    customer_total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    provenance = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")
    estimate_version = db.relationship(
        "EstimateVersion",
        backref=db.backref("pricing_snapshot", uselist=False),
    )
    policy = db.relationship("OrganizationPricingPolicy")
    costing_snapshot = db.relationship("EstimateCostingSnapshot")

    def __repr__(self):
        return f"<EstimatePricingSnapshot ev={self.estimate_version_id} {self.method}>"


class PricingAuditEvent(db.Model):
    __tablename__ = "pricing_audit_events"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    event_type = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    actor = db.Column(db.String(150), nullable=True)
    detail = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization")

    def __repr__(self):
        return f"<PricingAuditEvent {self.id} {self.event_type}>"
