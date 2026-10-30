"""Project closeout records (Joel, 30 Oct 2026): what was learned, recorded by a person. The calibration factors in
a record are proposals for future estimates; nothing applies them automatically."""

from datetime import datetime

from app import db


class ProjectCloseoutRecord(db.Model):
    __tablename__ = "project_closeout_records"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.String(50), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    recorded_by_name = db.Column(db.String(160), nullable=False)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    note = db.Column(db.Text, nullable=True)
    report_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
