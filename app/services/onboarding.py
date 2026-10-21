"""Ben's First Day: the guided setup checklist (Joel, 21 Oct 2026).

Fifteen steps in the order a contractor sets up and starts using CalibraytAI. Each step links to the real
page that does it. A step is done when the records show it (a client exists, a proposal was made, a crew
member was invited) or when the office marked it done by hand (steps the platform cannot see, such as
setting up the crew's phones). Read-only apart from those marks; never changes business records.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional

from app import db
from app.models.onboarding import OrganizationOnboardingStep


class OnboardingError(ValueError):
    pass


@dataclass(frozen=True)
class Step:
    key: str
    title: str
    why: str
    how: str
    endpoint: str
    check: Optional[Callable[[str, object], bool]] = None  # (organization_id, user) -> done from the records


def _count(model, **filters) -> int:
    try:
        return model.query.filter_by(**filters).count()
    except Exception:  # a step's check never breaks the checklist
        db.session.rollback()
        return 0


def _brand(org, _user):
    """Done once the brand profile has been saved. Opening the page (or making a proposal) creates version 1
    from the organization record by itself, so only a saved version (2 or later) counts."""
    from app.models.brand_profile import OrganizationBrandProfile

    try:
        return OrganizationBrandProfile.query.filter(OrganizationBrandProfile.organization_id == org,
                                                     OrganizationBrandProfile.version_number > 1).count() > 0
    except Exception:
        db.session.rollback()
        return False


def _pricing(org, _user):
    from app.models.pricing_engine import OrganizationPricingPolicy

    return _count(OrganizationPricingPolicy, organization_id=org) > 0


def _accounting(org, _user):
    from app.models.accounting import EVENT_EXPORT, AccountingEvent

    return _count(AccountingEvent, organization_id=org, kind=EVENT_EXPORT) > 0


def _people(org, _user):
    from app.models.user import UserMembership

    return _count(UserMembership, organization_id=org) > 1


def _appointments(org, _user):
    from app.models.appointment import CompanyAppointment

    return _count(CompanyAppointment, organization_id=org) > 0


def _feed(org, user):
    from app.models.appointment import CalendarFeedKey

    return user is not None and _count(CalendarFeedKey, organization_id=org, user_id=user.id, revoked_at=None) > 0


def _suppliers(org, _user):
    from app.models.supplier_catalogue import ContractorSupplierAccount

    return _count(ContractorSupplierAccount, organization_id=org) > 0


def _customers(org, _user):
    from app.models import Client, Project

    return _count(Client, organization_id=org) > 0 and _count(Project, organization_id=org) > 0


def _estimate(org, _user):
    from app.models import Estimate

    return _count(Estimate, organization_id=org) > 0


def _proposal(org, _user):
    from app.models import Proposal

    return _count(Proposal, organization_id=org) > 0


def _purchase_order(org, _user):
    from app.models.supplier_portal import SupplierPurchaseOrder

    return _count(SupplierPurchaseOrder, organization_id=org) > 0


def _crew_scheduling(org, _user):
    from app.models.schedule import WorkScheduleAssignment

    try:
        return WorkScheduleAssignment.query.filter(WorkScheduleAssignment.organization_id == org,
                                                   WorkScheduleAssignment.crew_id.isnot(None)).count() > 0
    except Exception:
        db.session.rollback()
        return False


STEPS: List[Step] = [
    Step("sign_in", "Sign in for the first time", "Your own sign-in keeps your work under your name.",
         "You are signed in. Change your password any time under Account (your name, top right).",
         "auth.change_password", lambda org, user: True),
    Step("company", "Set up your company", "Your logo, colours and contact details go on every proposal.",
         "Your company name (top right) → Brand profile: company name, logo, colours, address and phone. Save Brand Profile.",
         "settings.brand_profile", _brand),
    Step("finance", "Financial and HST settings", "Your markup and HST are used on every estimate and proposal.",
         "How we price → New pricing draft: your margin or markup and the 13 % HST for Ontario. Create draft, Approve, then Use for this company.",
         "pricing_engine.index", _pricing),
    Step("accounting", "Accounting with QuickBooks", "Keep your books in QuickBooks; CalibraytAI prepares the records.",
         "Company → Accounting → Customers → Download, then in QuickBooks: gear icon → Import data → Customers.",
         "accounting.index", _accounting),
    Step("people", "Invite the boys", "Each person gets their own sign-in; crew see only Field.",
         "Company → People & Access → Add a person. Tick Field only for crew. They get an email to set a password.",
         "people_access.index", _people),
    Step("phones", "Set up their iPhones", "Field works on the phone like an app.",
         "On each iPhone: open the email link in Safari, set the password, then Share → Add to Home Screen. Mark done.",
         "people_access.index"),
    Step("calendars", "Company and personal calendars", "Appointments and the job schedule in one place.",
         "Calendar → New appointment. Choose Company (everyone sees it) or Personal (only you).",
         "schedule.new_appointment", _appointments),
    Step("subscribe", "See it on your phone's calendar", "Your CalibraytAI calendar shows in Apple, Google or Outlook.",
         "Calendar → Outlook · Google · Apple Calendar → Turn on my calendar feed, then add it to your phone's calendar (steps on that page).",
         "schedule.calendar_feed_settings", _feed),
    Step("suppliers", "Suppliers and pricing", "Request quotes and send orders to your suppliers.",
         "Suppliers → Add supplier. Add the store people who will sign in to the Supplier Hub.",
         "supplier_office.suppliers", _suppliers),
    Step("customers", "Existing customers and jobs", "Bring in the work you already have.",
         "Clients → New client, then Home → + Start New Project for each current job.",
         "clients.list_clients", _customers),
    Step("estimate", "Your first estimate", "Price a job with your costs and the calculators.",
         "Open the project → New estimate. Add lines or use a calculator, then review costing and pricing.",
         "projects.create_project", _estimate),
    Step("proposal", "Your first proposal", "Send the customer a link to accept or decline.",
         "Once: Proposals → Templates → New template. Then on the priced estimate → Sign off estimate → Send proposal to client.",
         "clients.list_clients", _proposal),
    Step("purchase_order", "Your first purchase order", "Order material from your supplier, linked to the job.",
         "Project → Supplier requests → approve the supplier's quote → Place order.",
         "supplier_office.deliveries", _purchase_order),
    Step("crew_schedule", "Schedule the crew", "The boys see their work on their phones.",
         "Project → Open project work → Add work item. Then Calendar → Set dates, and on those dates assign a crew. It shows on Field for that crew.",
         "schedule.company", _crew_scheduling),
    Step("working_day", "Run a complete working day", "Schedule, field time, deliveries and changes, end to end.",
         "Check Home in the morning, follow the job on Field, approve time, answer deliveries. Mark done after a full day.",
         "main.dashboard"),
]
STEP_BY_KEY = {s.key: s for s in STEPS}


def checklist(organization_id: str, user) -> dict:
    marks = {m.step_key: m for m in OrganizationOnboardingStep.query.filter_by(organization_id=organization_id).all()}
    rows = []
    for number, step in enumerate(STEPS, 1):
        auto = bool(step.check and step.check(organization_id, user))
        mark = marks.get(step.key)
        rows.append({"number": number, "step": step, "auto": auto, "mark": mark, "done": auto or mark is not None,
                     "manual": step.check is None})
    done = sum(1 for r in rows if r["done"])
    return {"rows": rows, "done": done, "total": len(rows),
            "next": next((r for r in rows if not r["done"]), None)}


def mark_step(organization_id: str, user, key: str, done: bool) -> None:
    step = STEP_BY_KEY.get(key)
    if step is None:
        raise OnboardingError("Unknown step.")
    existing = OrganizationOnboardingStep.query.filter_by(organization_id=organization_id, step_key=key).first()
    if done and existing is None:
        name = (getattr(user, "display_name", None) or getattr(user, "email", "") or "Unknown")[:150]
        db.session.add(OrganizationOnboardingStep(organization_id=organization_id, step_key=key, done_by_user_id=user.id,
                                                  done_by_name=name, done_at=datetime.utcnow()))
    elif not done and existing is not None:
        db.session.delete(existing)
    db.session.commit()
