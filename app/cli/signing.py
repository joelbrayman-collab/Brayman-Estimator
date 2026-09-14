"""Flask CLI signing group — SIGN-A/B/C office request, invite, complete, lifecycle.
"""

from __future__ import annotations

import click
from flask.cli import with_appcontext

from app.models.signing import ACTOR_HUMAN
from app.services.organizations import get_current_organization_id
from app.services.signing import (
    SigningServiceError,
    approve_signing_request,
    countersign_and_execute,
    create_change_order_signing_request,
    create_contract_signing_request,
    execute_signed_request,
    expire_signing_request,
    get_signing_request,
    issue_customer_invitation,
    resend_customer_invitation,
    retrieve_executed_artifact_bytes,
    void_signing_request,
)


@click.group("signing")
def signing_cli():
    """Native Signing office operator commands (SIGN-A / SIGN-B / SIGN-C)."""


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
    executed_sha = ""
    if request.executed_artifact is not None:
        executed_sha = f" executed_sha={request.executed_artifact.sha256}"
    click.echo(
        f"{request.request_number} status={request.status} "
        f"family={request.document_family} authority={request.authority_class} "
        f"sha={request.frozen_artifact.sha256} "
        f"countersign={request.countersign_required}{executed_sha}"
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


@signing_cli.command("resend")
@click.option("--request-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@with_appcontext
def resend_command(request_id, actor_user_id, actor_identifier):
    """Rotate the SENT customer token. Old secret fails. Frozen artifact is unchanged."""
    try:
        issued = resend_customer_invitation(
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


@signing_cli.command("countersign")
@click.option("--request-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@with_appcontext
def countersign_command(request_id, actor_user_id, actor_identifier):
    """HUMAN countersign a SIGNED request and retain the executed PDF."""
    try:
        request = countersign_and_execute(
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
        f"executed_sha={request.executed_artifact.sha256}"
    )


@signing_cli.command("execute")
@click.option("--request-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@with_appcontext
def execute_command(request_id, actor_user_id, actor_identifier):
    """Complete a SIGNED request that does not require countersignature."""
    try:
        request = execute_signed_request(
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
        f"executed_sha={request.executed_artifact.sha256}"
    )


@signing_cli.command("void")
@click.option("--request-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@click.option("--reason", required=True)
@with_appcontext
def void_command(request_id, actor_user_id, actor_identifier, reason):
    """Human VOID for a non-executed request. Artifacts and events are retained."""
    try:
        request = void_signing_request(
            request_id,
            organization_id=get_current_organization_id(),
            actor_kind=ACTOR_HUMAN,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
            reason=reason,
        )
    except SigningServiceError as exc:
        _fail(exc)
    click.echo(f"{request.request_number} status={request.status}")


@signing_cli.command("expire")
@click.option("--request-id", type=int, required=True)
@click.option("--actor-user-id", type=int, required=True)
@click.option("--actor-identifier", required=True)
@with_appcontext
def expire_command(request_id, actor_user_id, actor_identifier):
    """Expire a request whose expires_at has passed and that is not yet signed."""
    try:
        request = expire_signing_request(
            request_id,
            organization_id=get_current_organization_id(),
            actor_kind=ACTOR_HUMAN,
            actor_user_id=actor_user_id,
            actor_identifier=actor_identifier,
        )
    except SigningServiceError as exc:
        _fail(exc)
    click.echo(f"{request.request_number} status={request.status}")


@signing_cli.command("download-executed")
@click.option("--request-id", type=int, required=True)
@click.option("--output", type=click.Path(dir_okay=False), required=True)
@with_appcontext
def download_executed_command(request_id, output):
    """Write exact retained executed PDF bytes for the current organization."""
    try:
        request = get_signing_request(request_id, get_current_organization_id())
        data = retrieve_executed_artifact_bytes(
            request_id,
            get_current_organization_id(),
        )
    except SigningServiceError as exc:
        _fail(exc)
    with open(output, "wb") as handle:
        handle.write(data)
    click.echo(
        f"{request.request_number} bytes={len(data)} sha={request.executed_artifact.sha256}"
    )
