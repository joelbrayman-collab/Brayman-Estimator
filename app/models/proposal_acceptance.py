"""Client proposal link and acceptance (Joel, 17 Oct 2026).

A proposal reaches the client only as a CalibraytAI link. The client ticks
Accept Proposal; the acceptance is recorded with name, time and the content
fingerprint of the proposal they saw. The office may instead record an
acceptance given by phone, email or in person.
"""

from datetime import datetime

from app import db

ACCEPTANCE_VIA_CLIENT_LINK = "CLIENT_LINK"
ACCEPTANCE_RECORDED_BY_OFFICE = "OFFICE_RECORDED"
ACCEPTANCE_METHODS = (ACCEPTANCE_VIA_CLIENT_LINK, ACCEPTANCE_RECORDED_BY_OFFICE)

OFFICE_ACCEPTANCE_CHANNELS = ("Phone", "Email", "In person")


class ProposalClientLink(db.Model):
    __tablename__ = "proposal_client_links"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey("proposals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    lookup_key = db.Column(db.String(40), nullable=False, unique=True)
    token_hash = db.Column(db.String(64), nullable=False)
    sent_to_name = db.Column(db.String(160), nullable=False)
    sent_to_email = db.Column(db.String(255), nullable=False)
    sent_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    sent_by_name = db.Column(db.String(160), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    first_viewed_at = db.Column(db.DateTime, nullable=True)
    last_viewed_at = db.Column(db.DateTime, nullable=True)
    view_count = db.Column(db.Integer, nullable=False, default=0)

    proposal = db.relationship("Proposal")

    @property
    def is_open(self):
        return self.revoked_at is None and self.expires_at > datetime.utcnow()


class ProposalAcceptance(db.Model):
    __tablename__ = "proposal_acceptances"
    __table_args__ = (
        db.CheckConstraint(
            "method IN ('CLIENT_LINK', 'OFFICE_RECORDED')",
            name="ck_proposal_acceptances_method",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey("proposals.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    method = db.Column(db.String(20), nullable=False)
    link_id = db.Column(db.Integer, db.ForeignKey("proposal_client_links.id", ondelete="RESTRICT"), nullable=True)
    accepted_name = db.Column(db.String(160), nullable=False)
    accepted_email = db.Column(db.String(255), nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    office_channel = db.Column(db.String(20), nullable=True)
    office_note = db.Column(db.Text, nullable=True)
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    recorded_by_name = db.Column(db.String(160), nullable=True)
    client_ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    proposal_content_sha256 = db.Column(db.String(64), nullable=False)
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("project_generated_contracts.id", ondelete="RESTRICT"),
        nullable=True,
    )
    contract_block_code = db.Column(db.String(80), nullable=True)

    proposal = db.relationship("Proposal")
    link = db.relationship("ProposalClientLink")


class ProposalDecline(db.Model):
    """The client declined the proposal on the CalibraytAI link (Joel, 21 Oct 2026).

    Same evidence as an acceptance: who, when, from where, and the fingerprint of the proposal
    they saw. A decline consumes the link and generates nothing.
    """

    __tablename__ = "proposal_declines"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey("proposals.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    link_id = db.Column(db.Integer, db.ForeignKey("proposal_client_links.id", ondelete="RESTRICT"), nullable=True)
    declined_name = db.Column(db.String(160), nullable=False)
    declined_email = db.Column(db.String(255), nullable=True)
    declined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reason = db.Column(db.Text, nullable=True)
    client_ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    proposal_content_sha256 = db.Column(db.String(64), nullable=False)

    proposal = db.relationship("Proposal")
    link = db.relationship("ProposalClientLink")
