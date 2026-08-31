"""Flask CLI BUILD group — place a Derived Candidate for UAT without AI."""

from __future__ import annotations

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_login import login_user

from app.models.build import DERIVED_SOURCE_UAT_CLI
from app.models.user import User
from app.services.auth import AuthServiceError, normalize_email
from app.services.build import (
    BuildServiceError,
    get_field_event,
    propose_derived_candidate,
)
from app.services.organizations import (
    OrganizationAccessError,
    resolve_membership_organization_id,
)


@click.group("build")
def build_cli():
    """BUILD Field Observation operator commands."""


@build_cli.command("propose-derived-candidate")
@click.option("--email", required=True)
@click.option("--project-id", "project_id", type=int, required=True)
@click.option("--event-id", "event_id", type=int, required=True)
@click.option("--kind", required=True)
@click.option("--payload", required=True, help="JSON object text.")
@with_appcontext
def propose_derived_candidate_command(email, project_id, event_id, kind, payload):
    """Create a PROPOSED Derived Candidate with source UAT_CLI. No AI."""
    try:
        normalized = normalize_email(email)
    except AuthServiceError as exc:
        raise click.ClickException(str(exc)) from exc
    user = User.query.filter_by(email=normalized).first()
    if user is None or not user.is_active:
        raise click.ClickException("User was not found.")
    with current_app.test_request_context():
        login_user(user)
        try:
            org_id = resolve_membership_organization_id(user)
        except OrganizationAccessError as exc:
            raise click.ClickException(str(exc)) from exc
        event = get_field_event(org_id, project_id, event_id)
        if event is None:
            raise click.ClickException("Field observation was not found.")
        try:
            candidate = propose_derived_candidate(
                event,
                kind=kind,
                payload=payload,
                source=DERIVED_SOURCE_UAT_CLI,
            )
        except BuildServiceError as exc:
            raise click.ClickException(str(exc)) from exc
    click.echo(
        f"Proposed derived candidate {candidate.id} on event {event.id} "
        f"(source={DERIVED_SOURCE_UAT_CLI})."
    )
