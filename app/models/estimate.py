from datetime import datetime
from decimal import Decimal

from app import db

ESTIMATE_STATUSES = (
    "Draft",
    "In Review",
    "Issued",
    "Accepted",
    "Rejected",
    "Superseded",
    "Archived",
)

ESTIMATE_VERSION_STATUSES = (
    "Draft",
    "In Review",
    "Issued",
    "Accepted",
    "Rejected",
    "Superseded",
)

AUTO_LOCK_VERSION_STATUSES = frozenset(
    {
        "Issued",
        "Accepted",
        "Rejected",
        "Superseded",
    }
)


class Estimate(db.Model):
    __tablename__ = "estimates"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["current_version_id"],
            ["estimate_versions.id"],
            name="fk_estimates_current_version_id",
            use_alter=True,
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
    )
    estimate_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Draft")
    current_version_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = db.relationship("Project", back_populates="estimates")
    versions = db.relationship(
        "EstimateVersion",
        back_populates="estimate",
        cascade="all, delete-orphan",
        order_by="desc(EstimateVersion.version_number)",
        foreign_keys="EstimateVersion.estimate_id",
    )
    current_version = db.relationship(
        "EstimateVersion",
        foreign_keys=[current_version_id],
        post_update=True,
        uselist=False,
    )

    def __repr__(self):
        return f"<Estimate {self.estimate_number}>"


class EstimateVersion(db.Model):
    __tablename__ = "estimate_versions"
    __table_args__ = (
        db.UniqueConstraint(
            "estimate_id",
            "version_number",
            name="uq_estimate_versions_estimate_id_version_number",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(
        db.Integer,
        db.ForeignKey("estimates.id"),
        nullable=False,
    )
    version_number = db.Column(db.Integer, nullable=False)
    version_label = db.Column(db.String(100))
    revision_reason = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default="Draft")
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    overhead_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    profit_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    tax_percent = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=Decimal("0"),
    )
    total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0"))
    is_locked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    estimate = db.relationship(
        "Estimate",
        back_populates="versions",
        foreign_keys=[estimate_id],
    )

    @property
    def display_label(self):
        label = self.version_label or "Untitled"
        return f"v{self.version_number} — {label}"

    def __repr__(self):
        return f"<EstimateVersion {self.estimate_id}v{self.version_number}>"
