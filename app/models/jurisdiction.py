"""Platform jurisdiction definitions (FG-015 / ADR-037). Shared; not org-owned."""

from datetime import datetime

from app import db

JURISDICTION_KINDS = ("country", "province_state", "municipality")

JURISDICTION_SEED = (
    {
        "code": "CA",
        "kind": "country",
        "name": "Canada",
        "parent_code": None,
        "ahj_name": None,
    },
    {
        "code": "CA-ON",
        "kind": "province_state",
        "name": "Ontario",
        "parent_code": "CA",
        "ahj_name": None,
    },
    {
        "code": "CA-ON-OTTAWA",
        "kind": "municipality",
        "name": "City of Ottawa",
        "parent_code": "CA-ON",
        "ahj_name": "City of Ottawa",
    },
)

JURISDICTION_ALIAS_SEED = (
    ("CA", "Canada"),
    ("CA", "CA"),
    ("CA-ON", "Ontario"),
    ("CA-ON", "ON"),
    ("CA-ON-OTTAWA", "Ottawa"),
    ("CA-ON-OTTAWA", "City of Ottawa"),
    ("CA-ON-OTTAWA", "North Gower"),
)


def normalize_jurisdiction_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


class JurisdictionDefinition(db.Model):
    __tablename__ = "jurisdiction_definitions"
    __table_args__ = (
        db.CheckConstraint(
            "kind IN ('country', 'province_state', 'municipality')",
            name="ck_jurisdiction_definitions_kind",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), nullable=False, unique=True)
    kind = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=True,
        index=True,
    )
    ahj_name = db.Column(db.String(160), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    parent = db.relationship(
        "JurisdictionDefinition",
        remote_side=[id],
        backref="children",
    )
    aliases = db.relationship(
        "JurisdictionAlias",
        back_populates="jurisdiction",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<JurisdictionDefinition {self.code} {self.kind}>"


class JurisdictionAlias(db.Model):
    __tablename__ = "jurisdiction_aliases"
    __table_args__ = (
        db.UniqueConstraint(
            "normalized_alias",
            "jurisdiction_id",
            name="uq_jurisdiction_aliases_normalized_jurisdiction",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(
        db.Integer,
        db.ForeignKey("jurisdiction_definitions.id"),
        nullable=False,
        index=True,
    )
    alias = db.Column(db.String(160), nullable=False)
    normalized_alias = db.Column(db.String(160), nullable=False, index=True)

    jurisdiction = db.relationship("JurisdictionDefinition", back_populates="aliases")

    def __repr__(self):
        return f"<JurisdictionAlias {self.alias}>"
