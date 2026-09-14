"""Flask CLI signing group — SIGN-A office request create / inspect / approve.
SIGN-B: issue a one-time copyable customer invitation URL.
"""

from __future__ import annotations

import click
from flask.cli import with_appcontext

from app.models.signing import ACTOR_HUMAN
from app.services.organizations import get_current_organization_id
from app.services.signing import (
    SigningServiceError,
    approve_signing_request,
    create_change_order_signing_request,
    create_contract_signing_request,
    get_signing_request,
    issue_customer_invitation,
)


@click.group("signing")
def signing_cli():
    """Native Signing office operator commands (SIGN-A / SIGN-B invite)."""


def _fail(exc: SigningServiceError):
    raise click.ClickException(exc.code) from exc


@signing_cli.command("create-change-order")
@click.option("--change-order-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@click.option("--signer-name", required=True)
@click.option("--signer-email", required=True)
@click.option("--consent-version-id", type=int, required=True)
@click.option("--authority-class", required=True)
@click.option(
    "--countersign-required/--no-countersign-required",
    default=True,
    show_default=True,
)
@with_appcontext
def create_change_order_command(
    change_order_id,
    actor_user_id,
    actor_identifier,
    signer_name,
    signer_email,
    consent_version_id,
    authority_class,
    countersign_required,
):
    """Create a CREATED signing request and freeze the Approved CO PDF once."""
    try:
        request = create_change_order_signing_request(
            change_order_id,
            organization_id=get_current_organization_id(),
            actor_kind=ACTOR_HUMAN,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
            invited_name=signer_name,
            invited_email=signer_email,
            consent_version_id=consent_version_id,
            countersign_required=countersign_required,
            authority_class=authority_class,
        )
    except SigningServiceError as exc:
        _fail(exc)
    click.echo(
        f"{request.request_number} status={request.status} "
        f"family={request.document_family} sha={request.frozen_artifact.sha256}"
    )


@signing_cli.command("create-contract")
@click.option("--generated-contract-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@click.option("--signer-name", required=True)
@click.option("--signer-email", required=True)
@click.option("--consent-version-id", type=int, required=True)
@click.option("--authority-class", required=True)
@click.option(
    "--countersign-required/--no-countersign-required",
    default=True,
    show_default=True,
)
@with_appcontext
def create_contract_command(
    generated_contract_id,
    actor_user_id,
    actor_identifier,
    signer_name,
    signer_email,
    consent_version_id,
    authority_class,
    countersign_required,
):
    """Bind a GENERATED contract DOCX source and create a CREATED request."""
    try:
        request = create_contract_signing_request(
            generated_contract_id,
            organization_id=get_current_organization_id(),
            actor_kind=ACTOR_HUMAN,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
            invited_name=signer_name,
            invited_email=signer_email,
            consent_version_id=consent_version_id,
            countersign_required=countersign_required,
            authority_class=authority_class,
        )
    except SigningServiceError as exc:
        _fail(exc)
    click.echo(
        f"{request.request_number} status={request.status} "
        f"family={request.document_family} sha={request.frozen_artifact.sha256}"
    )


@signing_cli.command("approve")
@click.option("--request-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@with_appcontext
def approve_command(request_id, actor_user_id, actor_identifier):
    """HUMAN APPROVED_FOR_SIGNATURE only. AI/AUTOMATION cannot call this path."""
    try:
        request = approve_signing_request(
            request_id,
            organization_id=get_current_organization_id(),
            actor_kind=ACTOR_HUMAN,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _fail(exc)
    click.echo(
        f"{request.request_number} status={request.status} "
        f"approved_by={request.approved_by_identifier}"
    )


@signing_cli.command("show")
@click.option("--request-id", type=int, required=True)
@with_appcontext
def show_command(request_id):
    """Inspect a signing request in the current organization."""
    try:
        request = get_signing_request(request_id, get_current_organization_id())
    except SigningServiceError as exc:
        _fail(exc)
    click.echo(
        f"{request.request_number} status={request.status} "
        f"family={request.document_family} authority={request.authority_class} "
        f"sha={request.frozen_artifact.sha256} "
        f"countersign={request.countersign_required}"
    )
    for event in request.events:
        click.echo(
            f"  event {event.event_type} actor={event.actor_kind}:"
            f"{event.actor_identifier} sha={event.artifact_sha256 or ''}"
        )


@signing_cli.command("invite")
@click.option("--request-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@with_appcontext
def invite_command(request_id, actor_user_id, actor_identifier):
    """Issue one copyable customer signing URL. Raw secret is not stored."""
    try:
        issued = issue_customer_invitation(
            request_id,
            organization_id=get_current_organization_id(),
            actor_kind=ACTOR_HUMAN,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _fail(exc)
    click.echo(f"{issued.request.request_number} status={issued.request.status}")
    click.echo(issued.path)
