from datetime import datetime

from app import db
from app.services.organizations import get_current_organization_id


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id"),
        nullable=False,
        default=get_current_organization_id,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organization = db.relationship("Organization", back_populates="clients")
    projects = db.relationship(
        "Project",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Client {self.name}>"
