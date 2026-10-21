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

LINK_SENT = "A link to choose a password was emailed to {email}. It works once and expires in an hour."
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


def _send_link(user) -> None:
    try:
        send_set_password_link(user, client_ip=request.remote_addr)
    except PasswordResetServiceError as exc:
        if exc.code == BLOCK_RATE_LIMITED:
            flash(LINK_RATE_LIMITED.format(email=user.email), "error")
        else:
            flash("This sign-in is deactivated. Reactivate it before sending a link.", "error")
        return
    flash(LINK_SENT.format(email=user.email), "success")


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
            except AccessDomainError as exc:
                flash(f"Added, but not marked Field only: {exc}", "error")
        flash(f"{membership.user.display_name} was added.", "success")
        _send_link(membership.user)
        return redirect(url_for("people_access.detail", membership_id=membership.id))
    return render_template("settings/people/new.html", values=values)


@people_access_bp.route("/<int:membership_id>")
def detail(membership_id):
    person = _person_or_404(membership_id)
    return render_template(
        "settings/people/detail.html",
        person=person,
        domains=sorted(RECOGNIZED_STORED_DOMAINS),
        domain_labels=ACCESS_DOMAIN_LABELS,
        viewer_is_owner=is_instance_owner(current_user, _org()),
        field_only=membership_is_field_only(UserMembership.query.get(membership_id)),
    )


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


@people_access_bp.route("/<int:membership_id>/send-link", methods=["POST"])
def send_link(membership_id):
    _person_or_404(membership_id)
    user = membership_user(organization_id=_org(), membership_id=membership_id, actor=current_user)
    _send_link(user)
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
            set_field_only(membership_id, marked, current_user)
        except AccessDomainError as exc:
            raise PeopleAccessError(str(exc))
        return ("Marked Field only: Field pages and their own account, no office pages or costs."
                if marked else "Field only removed: office access as before.")

    return _act(membership_id, run)
