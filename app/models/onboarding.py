"""Ben's First Day: the guided setup checklist's saved progress (Joel, 21 Oct 2026).

One row per organization and step the office marked done by hand. Steps the platform can see for itself
(a client exists, a proposal was made) are worked out from the records and never stored here.
"""

from datetime import datetime

from app import db


class OrganizationOnboardingStep(db.Model):
    __tablename__ = "organization_onboarding_steps"
    __table_args__ = (db.UniqueConstraint("organization_id", "step_key", name="uq_organization_onboarding_steps_step"),)

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False,
                                index=True)
    step_key = db.Column(db.String(40), nullable=False)
    done_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    done_by_name = db.Column(db.String(150), nullable=False)
    done_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
