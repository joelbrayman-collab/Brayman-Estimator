from datetime import datetime

from app import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    project_number = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False, default="Lead")
    description = db.Column(db.Text)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    client = db.relationship("Client", back_populates="projects")

    def __repr__(self):
        return f"<Project {self.name}>"
