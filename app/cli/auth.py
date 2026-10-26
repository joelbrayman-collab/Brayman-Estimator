"""Flask CLI auth group — bootstrap, password reset, and access-domain grants."""

from __future__ import annotations

import getpass
import os

import click

from app import db
from flask.cli import with_appcontext

from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    AccessDomainError,
    describe_access_domains,
    grant_access_domain,
    revoke_access_domain,
    set_field_only,
)
from app.services.instance_authority import (
    InstanceAuthorityError,
    appoint_system_administrator,
    remove_system_administrator,
    set_instance_owner,
)
from app.services.auth import AuthServiceError, bootstrap_org_001_user, reset_password
from app.services.organization_people import (
    PersonAuthorityError,
    create_person,
    deactivate_person,
    get_person_hourly_wage,
    reactivate_person,
    update_person,
)


@click.group("auth")
def auth_cli():
    """Office authentication operator commands."""


def _acquire_password(env_name: str, *, confirm: bool) -> str:
    password = os.environ.get(env_name)
    if password is not None:
        if password == "":
            raise click.ClickException("Password is required.")
        return password
    password = getpass.getpass("Password: ")
    if confirm:
        repeated = getpass.getpass("Confirm password: ")
        if password != repeated:
            raise click.ClickException("Passwords do not match.")
    if password == "":
        raise click.ClickException("Password is required.")
    return password


@auth_cli.command("bootstrap-org-001-user")
@click.option("--email", required=True)
@click.option("--display-name", "display_name", required=True)
@with_appcontext
def bootstrap_org_001_user_command(email, display_name):
    """Create the first active ORG-001 office user and membership."""
    password = _acquire_password("AUTH_BOOTSTRAP_PASSWORD", confirm=True)
    try:
        user = bootstrap_org_001_user(
            email=email,
            display_name=display_name,
            password=password,
        )
    except AuthServiceError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Created office user {user.email} with ORG-001 membership.")


@auth_cli.command("reset-password")
@click.option("--email", required=True)
@with_appcontext
def reset_password_command(email):
    """Replace the password hash for an existing office user."""
    password = _acquire_password("AUTH_RESET_PASSWORD", confirm=True)
    try:
        user = reset_password(email=email, password=password)
    except AuthServiceError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Password updated for {user.email}.")


@auth_cli.command("grant-access-domain")
@click.option("--membership-id", "membership_id", required=True, type=int)
@click.option("--domain", "domain_key", required=True)
@with_appcontext
def grant_access_domain_command(membership_id, domain_key):
    """Grant a recognized stored access domain onto one membership. Idempotent."""
    try:
        grant_access_domain(membership_id=membership_id, domain_key=domain_key)
    except AccessDomainError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Access domain {domain_key} is present on membership {membership_id}."
    )


@auth_cli.command("revoke-access-domain")
@click.option("--membership-id", "membership_id", required=True, type=int)
@click.option("--domain", "domain_key", required=True)
@with_appcontext
def revoke_access_domain_command(membership_id, domain_key):
    """Revoke a recognized stored access domain from one membership. Idempotent."""
    try:
        revoke_access_domain(membership_id=membership_id, domain_key=domain_key)
    except AccessDomainError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Access domain {domain_key} is absent on membership {membership_id}."
    )


@auth_cli.command("set-instance-owner")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--membership-id", "membership_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@with_appcontext
def set_instance_owner_command(organization_id, membership_id, actor_user_id):
    """Set the Instance Owner for one organization. Explicit ids only. No inference."""
    try:
        org = set_instance_owner(
            organization_id,
            membership_id,
            actor_user_id,
        )
    except InstanceAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Instance Owner membership {org.instance_owner_membership_id} "
        f"is set for organization {org.id}."
    )


@auth_cli.command("appoint-system-administrator")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--membership-id", "membership_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@with_appcontext
def appoint_system_administrator_command(organization_id, membership_id, actor_user_id):
    """Appoint a System Administrator. Explicit ids only. Owner actor only."""
    try:
        row = appoint_system_administrator(
            organization_id,
            membership_id,
            actor_user_id,
        )
    except InstanceAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"System Administrator membership {row.membership_id} "
        f"is appointed for organization {row.organization_id}."
    )


@auth_cli.command("remove-system-administrator")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--membership-id", "membership_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@with_appcontext
def remove_system_administrator_command(organization_id, membership_id, actor_user_id):
    """Remove a System Administrator. Explicit ids only. No inference."""
    try:
        remove_system_administrator(
            organization_id,
            membership_id,
            actor_user_id,
        )
    except InstanceAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"System Administrator membership {membership_id} "
        f"is removed for organization {organization_id}."
    )


@auth_cli.command("show-access-domains")
@click.option("--membership-id", "membership_id", required=True, type=int)
@with_appcontext
def show_access_domains_command(membership_id):
    """Show stored grants and whether COMPANY_MANAGEMENT is currently effective."""
    try:
        info = describe_access_domains(membership_id=membership_id)
    except AccessDomainError as exc:
        raise click.ClickException(str(exc)) from exc
    stored = ", ".join(info["stored_domains"]) or "(none)"
    effective = "yes" if info["effective_COMPANY_MANAGEMENT"] else "no"
    click.echo(f"membership_id: {info['membership_id']}")
    click.echo(f"organization_id: {info['organization_id']}")
    click.echo(f"user_id: {info['user_id']}")
    click.echo(f"user_active: {'yes' if info['user_active'] else 'no'}")
    click.echo(f"membership_active: {'yes' if info['membership_active'] else 'no'}")
    click.echo(f"stored_domains: {stored}")
    click.echo(f"effective_{ACCESS_DOMAIN_COMPANY_MANAGEMENT}: {effective}")
    click.echo(f"field_only: {'yes' if info['field_only'] else 'no'}")


@auth_cli.command("set-field-only")
@click.option("--membership-id", "membership_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@click.option("--off", "turn_off", is_flag=True, default=False, help="Clear the mark (office access again).")
@with_appcontext
def set_field_only_command(membership_id, actor_user_id, turn_off):
    """Mark one membership field-only (Field pages and own account only), or clear it with --off.
    Owner or System Administrator actor only. Idempotent."""
    try:
        state = set_field_only(membership_id, not turn_off, actor_user_id)
    except AccessDomainError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Membership {membership_id} field_only: {'yes' if state else 'no'}.")


@auth_cli.command("create-person")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@click.option("--full-name", "full_name", required=True)
@click.option("--address", required=True)
@click.option("--mobile-number", "mobile_number", required=True)
@click.option("--email-address", "email_address", required=True)
@click.option("--hourly-wage", "hourly_wage", required=True)
@with_appcontext
def create_person_command(
    organization_id,
    actor_user_id,
    full_name,
    address,
    mobile_number,
    email_address,
    hourly_wage,
):
    """Create an organization Person. Does not create User, Membership, or access."""
    try:
        identity = create_person(
            organization_id=organization_id,
            actor=actor_user_id,
            full_name=full_name,
            address=address,
            mobile_number=mobile_number,
            email_address=email_address,
            hourly_wage=hourly_wage,
        )
    except PersonAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Person {identity.id} is created for organization {identity.organization_id}."
    )


@auth_cli.command("update-person")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--person-id", "person_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@click.option("--full-name", "full_name", required=False)
@click.option("--address", required=False)
@click.option("--mobile-number", "mobile_number", required=False)
@click.option("--email-address", "email_address", required=False)
@click.option("--hourly-wage", "hourly_wage", required=False)
@with_appcontext
def update_person_command(
    organization_id,
    person_id,
    actor_user_id,
    full_name,
    address,
    mobile_number,
    email_address,
    hourly_wage,
):
    """Update Person identity or wage. Owner or System Administrator only."""
    kwargs = {}
    if full_name is not None:
        kwargs["full_name"] = full_name
    if address is not None:
        kwargs["address"] = address
    if mobile_number is not None:
        kwargs["mobile_number"] = mobile_number
    if email_address is not None:
        kwargs["email_address"] = email_address
    if hourly_wage is not None:
        kwargs["hourly_wage"] = hourly_wage
    try:
        identity = update_person(
            organization_id=organization_id,
            person_id=person_id,
            actor=actor_user_id,
            **kwargs,
        )
    except PersonAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Person {identity.id} is updated for organization {identity.organization_id}."
    )


@auth_cli.command("deactivate-person")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--person-id", "person_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@with_appcontext
def deactivate_person_command(organization_id, person_id, actor_user_id):
    """Deactivate a Person without deleting the row or rewriting history."""
    try:
        identity = deactivate_person(
            organization_id=organization_id,
            person_id=person_id,
            actor=actor_user_id,
        )
    except PersonAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Person {identity.id} is deactivated for organization {identity.organization_id}."
    )


@auth_cli.command("reactivate-person")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--person-id", "person_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@with_appcontext
def reactivate_person_command(organization_id, person_id, actor_user_id):
    """Reactivate a Person. Owner or System Administrator only."""
    try:
        identity = reactivate_person(
            organization_id=organization_id,
            person_id=person_id,
            actor=actor_user_id,
        )
    except PersonAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Person {identity.id} is reactivated for organization {identity.organization_id}."
    )


@auth_cli.command("show-person-wage")
@click.option("--organization-id", "organization_id", required=True)
@click.option("--person-id", "person_id", required=True, type=int)
@click.option("--actor-user-id", "actor_user_id", required=True, type=int)
@with_appcontext
def show_person_wage_command(organization_id, person_id, actor_user_id):
    """Read Person hourly wage through the protected seam. Do not use for ordinary identity."""
    try:
        wage = get_person_hourly_wage(
            organization_id=organization_id,
            person_id=person_id,
            actor=actor_user_id,
        )
    except PersonAuthorityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"person_id: {person_id}")
    click.echo(f"hourly_wage: {wage}")


@auth_cli.command("issue-link")
@click.option("--email", required=True)
@with_appcontext
def issue_link_command(email):
    """Emergency access (26 Oct 2026): print a one-time set-password link for an existing, active sign-in. No email
    is sent; the link is printed here only. It works once and replaces the person's unused links."""
    from app.models.user import User
    from app.services.password_reset import PasswordResetServiceError, issue_link_without_email
    from app.services.transactional_email import link_base_url

    user = User.query.filter(db.func.lower(User.email) == (email or "").strip().lower()).first()
    try:
        path, expires_at = issue_link_without_email(user)
    except PasswordResetServiceError:
        raise click.ClickException("No active sign-in has that email address.")
    click.echo(f"One-time link for {user.display_name} (works once, expires {expires_at:%Y-%m-%d %H:%M} UTC):")
    click.echo(f"{link_base_url()}{path}")
