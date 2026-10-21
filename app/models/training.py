"""Training & Acceptance Centre records (Joel, 21 Oct 2026).

Training and user acceptance testing (UAT) are kept apart, as in the AiRIA Training Centre's register
(lessons and lesson checks separate from UAT results, each with its own resume point):

- training_trainees          one per signed-in person who registered: pathway (CONTRACTOR / SUPPLIER), role,
                             the organization or supplier they belong to, resume points, Tutor minimized or open
- training_lesson_progress   one row per trainee and lesson: the step reached, done, the exercise confirmed
- training_uat_results       append-only: every Pass / Fail / Blocked is a new row (attempt 1, 2, ...), so a
                             retest never overwrites an earlier result; notes and the issue found are kept
- training_feedback          the trainee's own notes and feedback on a lesson

The Centre runs only on the separate training site (TRAINING_ENVIRONMENT=1); on the production office
these tables stay empty.
"""

from datetime import datetime

from app import db

PATHWAY_CONTRACTOR = "CONTRACTOR"
PATHWAY_SUPPLIER = "SUPPLIER"
PATHWAYS = (PATHWAY_CONTRACTOR, PATHWAY_SUPPLIER)

ROLE_OWNER = "OWNER"
ROLE_OFFICE = "OFFICE"
ROLE_FIELD = "FIELD"
ROLE_SUPPLIER_OWNER = "SUPPLIER_OWNER"
ROLE_SUPPLIER_ADMIN = "SUPPLIER_ADMIN"
ROLE_PRO_DESK = "PRO_DESK"
CONTRACTOR_ROLES = (ROLE_OWNER, ROLE_OFFICE, ROLE_FIELD)
SUPPLIER_ROLES = (ROLE_SUPPLIER_OWNER, ROLE_SUPPLIER_ADMIN, ROLE_PRO_DESK)
ROLES = CONTRACTOR_ROLES + SUPPLIER_ROLES
ROLE_LABELS = {
    ROLE_OWNER: "Contractor owner",
    ROLE_OFFICE: "Office staff",
    ROLE_FIELD: "Field worker",
    ROLE_SUPPLIER_OWNER: "Supplier owner",
    ROLE_SUPPLIER_ADMIN: "Supplier administrator",
    ROLE_PRO_DESK: "PRO Desk staff",
}

UAT_PASS = "PASS"
UAT_FAIL = "FAIL"
UAT_BLOCKED = "BLOCKED"
UAT_STATUSES = (UAT_PASS, UAT_FAIL, UAT_BLOCKED)


class TrainingTrainee(db.Model):
    __tablename__ = "training_trainees"
    __table_args__ = (
        db.CheckConstraint("pathway IN ('CONTRACTOR', 'SUPPLIER')", name="ck_training_trainees_pathway"),
        db.CheckConstraint(
            "role IN ('OWNER', 'OFFICE', 'FIELD', 'SUPPLIER_OWNER', 'SUPPLIER_ADMIN', 'PRO_DESK')",
            name="ck_training_trainees_role",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True)
    display_name = db.Column(db.String(160), nullable=False)
    pathway = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    organization_id = db.Column(db.String(50), db.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True,
                                index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True, index=True)
    training_resume = db.Column(db.String(120), nullable=True)  # lesson key and step, e.g. "c01-welcome:2"
    uat_resume = db.Column(db.String(120), nullable=True)
    tutor_minimized = db.Column(db.Boolean, nullable=False, default=False)
    release = db.Column(db.String(60), nullable=True)  # the CalibraytAI version they registered on
    registered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)


class TrainingLessonProgress(db.Model):
    __tablename__ = "training_lesson_progress"
    __table_args__ = (db.UniqueConstraint("trainee_id", "lesson_key", name="uq_training_lesson_progress_lesson"),)

    id = db.Column(db.Integer, primary_key=True)
    trainee_id = db.Column(db.Integer, db.ForeignKey("training_trainees.id", ondelete="RESTRICT"), nullable=False,
                           index=True)
    lesson_key = db.Column(db.String(60), nullable=False)
    step_reached = db.Column(db.Integer, nullable=False, default=0)
    exercise_done = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    release = db.Column(db.String(60), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrainingUatResult(db.Model):
    __tablename__ = "training_uat_results"
    __table_args__ = (
        db.UniqueConstraint("trainee_id", "case_key", "attempt", name="uq_training_uat_results_attempt"),
        db.CheckConstraint("status IN ('PASS', 'FAIL', 'BLOCKED')", name="ck_training_uat_results_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    trainee_id = db.Column(db.Integer, db.ForeignKey("training_trainees.id", ondelete="RESTRICT"), nullable=False,
                           index=True)
    case_key = db.Column(db.String(60), nullable=False)
    attempt = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    issue = db.Column(db.Text, nullable=True)
    release = db.Column(db.String(60), nullable=True)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class TrainingFeedback(db.Model):
    __tablename__ = "training_feedback"

    id = db.Column(db.Integer, primary_key=True)
    trainee_id = db.Column(db.Integer, db.ForeignKey("training_trainees.id", ondelete="RESTRICT"), nullable=False,
                           index=True)
    lesson_key = db.Column(db.String(60), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
