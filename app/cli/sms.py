"""flask sms ... : schedule-change text notices (22 Oct 2026). Operation: docs/operations/sms-notifications.md."""

from __future__ import annotations

import click
from flask.cli import with_appcontext


@click.group("sms")
def sms_cli():
    """Schedule-change text notices."""


@sms_cli.command("send-due")
@with_appcontext
def send_due():
    """Send every worker's waiting schedule notices whose quiet period is over."""
    from app.services.crew_notices import send_due_notices

    summary = send_due_notices()
    click.echo(" ".join(f"{k}={v}" for k, v in sorted(summary.items())))


@sms_cli.command("status")
@with_appcontext
def status():
    """Print the texting settings as the app sees them (names and yes/no only, never secret values)."""
    from app.services.text_messages import settings_summary

    for key, value in sorted(settings_summary().items()):
        click.echo(f"{key}={value}")
