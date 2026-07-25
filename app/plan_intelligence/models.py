"""Plan Intelligence models — Phase A document register only."""

from datetime import datetime

from app import db


class PlanDocument(db.Model):
    """Project-scoped uploaded plan PDF (Phase A).

    Drawing Set / Revision ownership is documented in ADR-012 and is not
    implemented as separate entities in Phase A.
    """

    __tablename__ = "plan_documents"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    byte_size = db.Column(db.Integer, nullable=False)
    sha256_hex = db.Column(db.String(64), nullable=False)
    page_count = db.Column(db.Integer, nullable=True)
    has_text_layer = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship(
        "Project",
        back_populates="plan_documents",
    )

    def __repr__(self):
        return f"<PlanDocument {self.id} {self.original_filename}>"
