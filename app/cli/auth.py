"""Flask CLI auth group — bootstrap and password reset. No credentials in Git."""

from __future__ import annotations

import getpass
import os

import click
from flask.cli import with_appcontext

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
