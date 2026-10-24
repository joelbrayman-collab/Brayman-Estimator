"""Guided Workflow Wizards (Joel, 24 Oct 2026): where a person is in a guided activity, and nothing else.

A wizard run is a bookmark over the platform's own records. It owns no project, estimate, schedule, order,
quotation, price or cost. It points at the real records the activity works on (a project, a supplier request,
a PRO Desk quotation) and remembers the step the person was on, so Save & Exit and Resume Later work and the
manual pages stay the source of truth. Every step's progress is read from those records each time it is shown.

- WizardRun: one person's guided activity. Contractor runs belong to one company (organization_id); supplier
  runs belong to one supplier (supplier_id) and never to a contractor company. ``draft_json`` holds only the
  answers typed before the record they belong to exists (Start a New Project, steps 1 to 3), so they are not lost
  when the person stops; once the project is created the project is the record.
- WizardRunEvent: append-only history of the run (started, step saved, confirmations a person made in the
  wizard, switched to the manual page, finished).
"""

from datetime import datetime

from app import db

WIZARD_NEW_PROJECT = "NEW_PROJECT"
WIZARD_GUIDED_ESTIMATING = "GUIDED_ESTIMATING"
WIZARD_MANAGE_PROJECT = "MANAGE_PROJECT"
WIZARD_SUPPLIER_PRO_DESK = "SUPPLIER_PRO_DESK"
WIZARD_KEYS = (WIZARD_NEW_PROJECT, WIZARD_GUIDED_ESTIMATING, WIZARD_MANAGE_PROJECT, WIZARD_SUPPLIER_PRO_DESK)

SIDE_CONTRACTOR = "CONTRACTOR"
SIDE_SUPPLIER = "SUPPLIER"
SIDES = (SIDE_CONTRACTOR, SIDE_SUPPLIER)

RUN_ACTIVE = "ACTIVE"
RUN_COMPLETED = "COMPLETED"
RUN_ENDED = "ENDED"  # stopped by the person before the end; the records it pointed at are untouched
RUN_STATUSES = (RUN_ACTIVE, RUN_COMPLETED, RUN_ENDED)


class WizardRun(db.Model):
    __tablename__ = "wizard_runs"
    __table_args__ = (
        db.CheckConstraint(
            "wizard_key IN ('NEW_PROJECT', 'GUIDED_ESTIMATING', 'MANAGE_PROJECT', 'SUPPLIER_PRO_DESK')",
            name="ck_wizard_runs_wizard_key"),
        db.CheckConstraint("side IN ('CONTRACTOR', 'SUPPLIER')", name="ck_wizard_runs_side"),
        db.CheckConstraint("status IN ('ACTIVE', 'COMPLETED', 'ENDED')", name="ck_wizard_runs_status"),
        db.CheckConstraint(
            "(side = 'CONTRACTOR' AND organization_id IS NOT NULL AND supplier_id IS NULL) OR "
            "(side = 'SUPPLIER' AND supplier_id IS NOT NULL AND organization_id IS NULL)",
            name="ck_wizard_runs_owner"),
    )

    id = db.Column(db.Integer, primary_key=True)
    wizard_key = db.Column(db.String(40), nullable=False)
    side = db.Column(db.String(20), nullable=False)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"),
                                nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True,
                            index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=RUN_ACTIVE)
    current_step = db.Column(db.String(60), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True,
                           index=True)
    supplier_share_id = db.Column(db.Integer, db.ForeignKey("supplier_request_shares.id", ondelete="RESTRICT"),
                                  nullable=True, index=True)
    supplier_quote_id = db.Column(db.Integer, db.ForeignKey("supplier_quotes.id", ondelete="RESTRICT"),
                                  nullable=True, index=True)
    draft_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship("Project")
    share = db.relationship("SupplierRequestShare")
    quote = db.relationship("SupplierQuote")
    events = db.relationship("WizardRunEvent", back_populates="run", order_by="WizardRunEvent.id")

    @property
    def is_active(self) -> bool:
        return self.status == RUN_ACTIVE


class WizardRunEvent(db.Model):
    """Append-only history of one wizard run."""

    __tablename__ = "wizard_run_events"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("wizard_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    event = db.Column(db.String(40), nullable=False)
    step = db.Column(db.String(60), nullable=True)
    detail = db.Column(db.String(600), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_display_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    run = db.relationship("WizardRun", back_populates="events")
