"""People & Access office pages (V1 defect, Joel 21 Oct 2026). Owner or System Administrator only.

/settings/people              list of sign-ins in this company, their status and access
/settings/people/new          add a person (name, email) and email them a set-password link
/settings/people/<id>         one person: deactivate / reactivate, send the link again, access, role

``<id>`` is the person's membership in the current organization; another company's id answers 404.
Everyone else is refused (403) by require_instance_owner_or_system_administrator before any view runs.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.services.local_time import local_today
from app.models.user import UserMembership
from app.services.access_domains import (
    RECOGNIZED_STORED_DOMAINS,
    AccessDomainError,
    membership_is_field_only,
    set_field_only,
)
from app.services.instance_authority import (
    is_instance_owner,
    require_instance_owner_or_system_administrator,
)
from app.services.organizations import get_current_organization_id
from app.services.password_reset import BLOCK_RATE_LIMITED, PasswordResetServiceError, send_set_password_link
from app.services.people_access import (
    people_history,
    ACCESS_DOMAIN_LABELS,
    PERSON_NOT_FOUND,
    PeopleAccessError,
    add_person,
    deactivate_person,
    get_person_access,
    list_people_access,
    membership_user,
    reactivate_person,
    set_access_domain,
    set_system_administrator,
)

people_access_bp = Blueprint("people_access", __name__, url_prefix="/settings/people")

LINK_SENT = ("A link to choose a password was emailed to {email}. It works once and expires in {expires}. The same "
             "link is below, so you can text it if the email does not arrive; Email history shows when the mail "
             "service confirms delivery.")
LINK_NOT_EMAILED = ("The email to {email} was not delivered ({reason}). Give {name} the one-time link shown "
                    "below yourself, in person or by text. It works once and expires in {expires}.")
NOT_DELIVERED_REASONS = {
    "SKIPPED_ALLOWLIST": "this office only emails the test addresses on its allowlist",
    "FAILED_CONFIG": "email delivery is not set up",
    "FAILED": "the mail service refused or could not be reached",
    "LOCAL_CAPTURED": "email delivery is not set up on this server",
}
LINK_RATE_LIMITED = "Several links were already sent to {email} in the last hour. Try again later."


@people_access_bp.before_request
def _owner_or_system_administrator_only():
    return require_instance_owner_or_system_administrator()


def _org() -> str:
    return get_current_organization_id()


def _person_or_404(membership_id):
    try:
        return get_person_access(organization_id=_org(), membership_id=membership_id, actor=current_user)
    except PeopleAccessError as exc:
        if str(exc) == PERSON_NOT_FOUND:
            abort(404)
        abort(403)


def _invited_not_activated(membership) -> bool:
    from app.models.people_access_event import PeopleAccessEvent

    events = PeopleAccessEvent.query.filter_by(membership_id=membership.id)
    return bool(events.filter_by(action="ADDED").count()) and not events.filter_by(action="ACTIVATED").count()


def _expires_phrase(outcome) -> str:
    from datetime import datetime

    seconds = max(0, (outcome.expires_at - datetime.utcnow()).total_seconds())
    hours = round(seconds / 3600)
    return f"{hours} hours" if hours >= 2 else "an hour"


def _send_link(user):
    """Send the set-password link. Returns the link to show the owner once, whether or not the email went
    (sign-in reliability, Joel, 26 Oct 2026; defect 9), or None when no link was made. The link is never
    flashed, stored in the session or logged."""
    from app.models.organization import Organization
    from app.models.user import UserMembership
    from app.services.people_access import record_people_event

    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=_org()).first()
    invitation = None
    if membership is not None and _invited_not_activated(membership):
        org = db_session_get(Organization, _org())
        invitation = {"company_name": (getattr(org, "display_name", None) or getattr(org, "legal_name", None) or "Your company"),
                      "invited_by": getattr(current_user, "display_name", "") or ""}
    try:
        outcome = send_set_password_link(user, client_ip=request.remote_addr, invitation=invitation)
    except PasswordResetServiceError as exc:
        if exc.code == BLOCK_RATE_LIMITED:
            flash(LINK_RATE_LIMITED.format(email=user.email), "error")
        else:
            flash("This sign-in is deactivated. Reactivate it before sending a link.", "error")
        return None
    action = "INVITATION_SENT" if invitation is not None else "PASSWORD_LINK_SENT"
    from app.services.transactional_email import link_base_url

    link = {"url": f"{link_base_url()}{outcome.path}", "expires_at": outcome.expires_at, "email": user.email,
            "name": user.display_name, "emailed": outcome.delivered, "place": "CalibraytAI"}
    if outcome.delivered:
        if membership is not None:
            record_people_event(organization_id=_org(), membership=membership, action=action, actor=current_user,
                                detail="Emailed; the same one-time link was also shown to "
                                       f"{getattr(current_user, 'display_name', '') or 'the owner'}")
        _confirm_to_sender(user, invitation is not None, outcome)
        flash(LINK_SENT.format(email=user.email, expires=_expires_phrase(outcome)), "success")
        return link
    reason = NOT_DELIVERED_REASONS.get(outcome.status, "the email could not be sent")
    if membership is not None:
        actor = getattr(current_user, "display_name", "") or "the owner"
        record_people_event(organization_id=_org(), membership=membership, action=action, actor=current_user,
                            detail=f"Not emailed ({outcome.status}); one-time link shown to {actor} to give in person")
    flash(LINK_NOT_EMAILED.format(email=user.email, reason=reason, name=user.display_name,
                                  expires=_expires_phrase(outcome)), "error")
    return link


def _confirm_to_sender(user, is_invitation, outcome):
    """People & Access (Joel, 23 Oct 2026): tell the person who pressed the button that the invitation or
    set-password link was accepted by the mail service. A separate email to them, never a copy of the real one:
    it has the person's name and address, the kind and the times only, never the link or any part of its token.
    The same transactional service and allowlist as every other send. If it is not delivered, the invitation's
    own outcome is unchanged."""
    from datetime import datetime

    from app.models.transactional_message import TEMPLATE_INVITATION_SENT_CONFIRMATION
    from app.services.local_time import format_local
    from app.services.transactional_email import send_transactional_message

    sender = (getattr(current_user, "email", "") or "").strip()
    if not sender:
        return None
    try:
        return send_transactional_message(
            TEMPLATE_INVITATION_SENT_CONFIRMATION,
            sender,
            {"kind": "invitation" if is_invitation else "password_link",
             "person_name": user.display_name or user.email, "person_email": user.email,
             "sent_at": format_local(datetime.utcnow(), "%b %-d, %Y at %-I:%M %p"),
             "expires": format_local(outcome.expires_at, "%b %-d, %Y at %-I:%M %p")},
            related_type="user",
            related_id=getattr(current_user, "id", None),
        )
    except Exception:  # pragma: no cover - a confirmation never changes the invitation's outcome
        from flask import current_app

        current_app.logger.warning("People & Access: the sender's confirmation email could not be sent")
        return None


EMAIL_KINDS = {
    "ACCOUNT_INVITATION": "Invitation",
    "PASSWORD_RESET": "Set-password link",
    "INVITATION_SENT_CONFIRMATION": "Confirmation of a link they sent",
    "PROPOSAL_INVITATION": "Proposal",
    "SIGNING_INVITATION": "Signing invitation",
    "SIGNING_RESEND": "Signing reminder",
    "SIGNING_COMPLETE": "Signed copy",
    "DELIVERY_SCHEDULE": "Delivery schedule",
    "SUPPLIER_QUOTE": "Quotation",
    "DELIVERY_TEST": "Email test",
}


def _email_rows(email, limit=5):
    from app import db
    from app.models.transactional_message import TransactionalMessage

    address = (email or "").strip().lower()
    if not address:
        return []
    return (TransactionalMessage.query.filter(db.func.lower(TransactionalMessage.to_email) == address)
            .order_by(TransactionalMessage.created_at.desc(), TransactionalMessage.id.desc()).limit(limit).all())


def email_history(email, limit=5):
    """The last emails to this person (transactional_messages): when, what kind, and what the mail service
    reported: Delivered, Bounced with its reason, Waiting, or Not sent with a plain reason (sign-in reliability,
    26 Oct 2026: accepted is never shown as delivered). Never a link: the table keeps no link, token or body."""
    from app.services.email_delivery import STATE_CAPTURED, STATE_NOT_SENT, state_of

    out = []
    for row in _email_rows(email, limit):
        state = state_of(row)
        sent = state.code not in (STATE_NOT_SENT,)
        out.append({"at": row.created_at, "kind": EMAIL_KINDS.get(row.template_id, row.template_id.replace("_", " ").title()),
                    "sent": sent, "state": state, "captured": state.code == STATE_CAPTURED,
                    "reason": "" if sent else NOT_DELIVERED_REASONS.get(row.status, "the email could not be sent")})
    return out


def db_session_get(model, ident):
    from app import db

    return db.session.get(model, ident)


def _record(membership, action, detail=""):
    from app.services.people_access import record_people_event

    record_people_event(organization_id=_org(), membership=membership, action=action, actor=current_user, detail=detail)


def _crews_of(membership_id):
    """The person's current crew memberships (read-only here; crews are managed under Crews)."""
    from datetime import date

    from app.models.organization_crew import OrganizationCrew, OrganizationCrewMember
    from app.models.user import UserMembership

    membership = UserMembership.query.get(membership_id)
    if membership is None:
        return []
    rows = (OrganizationCrewMember.query.filter_by(organization_id=_org(), user_id=membership.user_id).all())
    out = []
    for m in rows:
        crew = OrganizationCrew.query.get(m.crew_id)
        ends = m.effective_to
        if crew is not None and (ends is None or ends >= local_today()):
            out.append({"crew": crew, "member": m})
    return out


def _texts_of(membership_id):
    """The person's schedule-text number, consent and consent history (SMS notices, 22 Oct 2026)."""
    from app.services.text_messages import consent_history, contact_for

    membership = UserMembership.query.get(membership_id)
    if membership is None or membership.user is None:
        return {"contact": None, "history": []}
    return {"contact": contact_for(membership.user), "history": consent_history(membership.user_id, limit=10)}


@people_access_bp.route("")
def index():
    people = list_people_access(organization_id=_org(), actor=current_user)
    return render_template(
        "settings/people/index.html",
        people=people,
        domain_labels=ACCESS_DOMAIN_LABELS,
    )


@people_access_bp.route("/new", methods=["GET", "POST"])
def new():
    values = {"display_name": "", "email": ""}
    if request.method == "POST":
        values = {
            "display_name": (request.form.get("display_name") or "").strip(),
            "email": (request.form.get("email") or "").strip(),
            "field_only": request.form.get("field_only") == "yes",
        }
        try:
            membership = add_person(
                organization_id=_org(),
                actor=current_user,
                display_name=values["display_name"],
                email=values["email"],
            )
        except PeopleAccessError as exc:
            flash(str(exc), "error")
            return render_template("settings/people/new.html", values=values), 400
        if request.form.get("field_only") == "yes":
            try:
                set_field_only(membership, True, current_user)
                _record(membership, "FIELD_ONLY_MARKED")
            except AccessDomainError as exc:
                flash(f"Added, but not marked Field only: {exc}", "error")
        flash(f"{membership.user.display_name} was added.", "success")
        one_time = _send_link(membership.user)
        if one_time is not None:
            return _detail_page(membership.id, one_time_link=one_time)
        return redirect(url_for("people_access.detail", membership_id=membership.id))
    return render_template("settings/people/new.html", values=values)


@people_access_bp.route("/<int:membership_id>")
def detail(membership_id):
    return _detail_page(membership_id)


def _detail_page(membership_id, one_time_link=None):
    """The person's page. ``one_time_link`` is shown only in this one response, to the owner who just
    made it (emailed or not); the response is never cached."""
    person = _person_or_404(membership_id)
    texts = _texts_of(membership_id)
    page = render_template(
        "settings/people/detail.html",
        person=person,
        domains=sorted(RECOGNIZED_STORED_DOMAINS),
        domain_labels=ACCESS_DOMAIN_LABELS,
        viewer_is_owner=is_instance_owner(current_user, _org()),
        field_only=membership_is_field_only(UserMembership.query.get(membership_id)),
        history=people_history(organization_id=_org(), membership_id=membership_id),
        crews=_crews_of(membership_id),
        one_time_link=one_time_link,
        texts=texts,
        emails=email_history(person.email),
    )
    if one_time_link is None:
        return page
    return page, 200, {"Cache-Control": "no-store", "Pragma": "no-cache", "Referrer-Policy": "no-referrer"}


def _act(membership_id, action):
    _person_or_404(membership_id)
    try:
        message = action()
        if message:
            flash(message, "success")
    except PeopleAccessError as exc:
        flash(str(exc), "error")
    return redirect(url_for("people_access.detail", membership_id=membership_id))


@people_access_bp.route("/<int:membership_id>/deactivate", methods=["POST"])
def deactivate(membership_id):
    def run():
        user = deactivate_person(organization_id=_org(), membership_id=membership_id, actor=current_user)
        return f"{user.display_name} is deactivated and signed out. They cannot sign in."

    return _act(membership_id, run)


@people_access_bp.route("/<int:membership_id>/reactivate", methods=["POST"])
def reactivate(membership_id):
    def run():
        user = reactivate_person(organization_id=_org(), membership_id=membership_id, actor=current_user)
        return f"{user.display_name} can sign in again with their password."

    return _act(membership_id, run)


@people_access_bp.route("/<int:membership_id>/check-email", methods=["POST"])
def check_email(membership_id):
    """Ask the mail service what happened to this person's recent emails (sign-in reliability, 26 Oct 2026)."""
    from app.services.email_delivery import check_waiting

    person = _person_or_404(membership_id)
    added, problem = check_waiting(_email_rows(person.email))
    if problem:
        flash(f"Could not ask the mail service: {problem}", "error")
    else:
        flash("Delivery checked with the mail service." if added else
              "Delivery checked: nothing new from the mail service yet.", "success")
    return redirect(url_for("people_access.detail", membership_id=membership_id) + "#email-history-heading")


@people_access_bp.route("/<int:membership_id>/send-link", methods=["POST"])
def send_link(membership_id):
    _person_or_404(membership_id)
    user = membership_user(organization_id=_org(), membership_id=membership_id, actor=current_user)
    one_time = _send_link(user)
    if one_time is not None:
        return _detail_page(membership_id, one_time_link=one_time)
    return redirect(url_for("people_access.detail", membership_id=membership_id))


@people_access_bp.route("/<int:membership_id>/access", methods=["POST"])
def access(membership_id):
    domain = (request.form.get("domain") or "").strip()
    granted = request.form.get("action") == "grant"
    label = ACCESS_DOMAIN_LABELS.get(domain, domain)

    def run():
        set_access_domain(
            organization_id=_org(), membership_id=membership_id, actor=current_user, domain_key=domain, granted=granted
        )
        return f"{label}: {'given' if granted else 'removed'}."

    return _act(membership_id, run)


@people_access_bp.route("/<int:membership_id>/administrator", methods=["POST"])
def administrator(membership_id):
    appointed = request.form.get("action") == "appoint"

    def run():
        if appointed and membership_is_field_only(UserMembership.query.get(membership_id)):
            raise PeopleAccessError("Remove Field only first: a System Administrator needs the office.")
        set_system_administrator(
            organization_id=_org(), membership_id=membership_id, actor=current_user, appointed=appointed
        )
        return "Appointed System Administrator." if appointed else "No longer a System Administrator."

    return _act(membership_id, run)


@people_access_bp.route("/<int:membership_id>/field-only", methods=["POST"])
def field_only(membership_id):
    """Mark or clear Field only (crew: Field pages and their own account, no office pages)."""
    marked = request.form.get("action") == "mark"

    def run():
        try:
            before = membership_is_field_only(UserMembership.query.get(membership_id))
            set_field_only(membership_id, marked, current_user)
        except AccessDomainError as exc:
            raise PeopleAccessError(str(exc))
        if before != marked:
            _record(membership_id, "FIELD_ONLY_MARKED" if marked else "FIELD_ONLY_CLEARED")
        return ("Marked Field only: Field pages and their own account, no office pages or costs."
                if marked else "Field only removed: office access as before.")

    return _act(membership_id, run)
