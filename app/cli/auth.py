"""Flask CLI auth group — bootstrap, password reset, and access-domain grants."""

from __future__ import annotations

import getpass
import os

import click
from flask.cli import with_appcontext

from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    AccessDomainError,
    describe_access_domains,
    grant_access_domain,
    revoke_access_domain,
)
from app.services.instance_authority import (
    InstanceAuthorityError,
    appoint_system_administrator,
    remove_system_administrator,
    set_instance_owner,
)
from app.services.auth import AuthServiceError, bootstrap_org_001_user, reset_password


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
