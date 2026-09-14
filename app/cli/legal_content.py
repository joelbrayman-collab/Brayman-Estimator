"""Flask CLI legal-content group — platform library operator commands."""

from __future__ import annotations

from datetime import date

import click
from flask.cli import with_appcontext

from app.services.legal_content_update import (
    LegalContentUpdateError,
    activate_legal_content,
)


@click.group("legal-content")
def legal_content_cli():
    """Platform legal-content library operator commands."""


@legal_content_cli.command("activate")
@click.option("--package-id", "package_id", type=int, required=True)
@click.option(
    "--actor-kind",
    required=True,
    type=click.Choice(["HUMAN", "COUNSEL"], case_sensitive=False),
)
@click.option("--actor-identifier", "actor_identifier", required=True)
@click.option("--effective-from", "effective_from", required=True)
@click.option("--effective-to", "effective_to", default=None)
@click.option("--supersede-package-id", "supersede_package_id", type=int, default=None)
@with_appcontext
def activate_command(
    package_id,
    actor_kind,
    actor_identifier,
    effective_from,
    effective_to,
    supersede_package_id,
):
    """Activate an APPROVED package. HUMAN/COUNSEL only. No AI."""
    try:
        from_day = date.fromisoformat(effective_from)
        to_day = date.fromisoformat(effective_to) if effective_to else None
    except ValueError as exc:
        raise click.ClickException("effective-from / effective-to must be YYYY-MM-DD.") from exc
    try:
        package = activate_legal_content(
            package_id,
            actor_kind=actor_kind.upper(),
            actor_identifier=actor_identifier,
            effective_from=from_day,
            effective_to=to_day,
            supersede_package_id=supersede_package_id,
        )
    except LegalContentUpdateError as exc:
        raise click.ClickException(exc.code) from exc
    click.echo(
        f"Activated package {package.id} {package.package_code} "
        f"state={package.library_state} authority_class={package.authority_class} "
        f"actor={package.activated_by}."
    )
