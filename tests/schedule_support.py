"""Governed scheduling test support (Joel, 30 Oct 2026; decision 4): a schedule move drafts its supplier
delivery changes, and a person with Company Management sends them. Synthetic users only."""

from app import db
from app.models import Project
from app.models.user import UserMembership
from app.services import governed_schedule as GS
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain
from tests.auth_fixtures import ensure_office_user

SENDER = ("schedule.sender@example.invalid", "schedule-sender-password", "Schedule Sender (synthetic)")


def company_manager(organization_id):
    user = ensure_office_user(email=SENDER[0], password=SENDER[1], display_name=SENDER[2],
                              organization_id=organization_id)
    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=organization_id).one()
    grant_access_domain(membership_id=membership.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    return user


def send_schedule_drafts(project_id):
    """Send every pending delivery-change draft on the project, as a Company Management user."""
    project = db.session.get(Project, project_id)
    user = company_manager(project.organization_id)
    sent = []
    for draft in GS.pending_drafts(project):
        sent.extend(GS.send_draft(draft, user=user))
    return sent
