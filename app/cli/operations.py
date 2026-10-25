"""flask reminders ... and flask quickbooks-online ... (Magnificent Seven, 25 Oct 2026).

Operation: docs/operations/end-of-day-reminders.md and docs/operations/quickbooks-online-receipts.md. Both commands are
safe to run as often as a scheduler likes: nothing is sent twice. They print counts only, never a name, number,
amount or token.
"""

from __future__ import annotations

import click
from flask.cli import with_appcontext


@click.group("reminders")
def reminders_cli():
    """End-of-day reminders."""


@reminders_cli.command("send-due")
@with_appcontext
def send_due():
    """Make today's end-of-day reminders for every company whose reminder time has come (once a day each)."""
    from app.services.reminders import send_due as run

    summary = run()
    click.echo(" ".join(f"{k}={v}" for k, v in sorted(summary.items())))


@click.group("quickbooks-online")
def quickbooks_online_cli():
    """QuickBooks Online receipt transfers."""


@quickbooks_online_cli.command("send-waiting")
@with_appcontext
def send_waiting():
    """Send every approved receipt still waiting (only where the company is connected and switched on)."""
    from app.services.quickbooks_online import send_waiting as run

    summary = run()
    click.echo(" ".join(f"{k}={v}" for k, v in sorted(summary.items())))


@quickbooks_online_cli.command("status")
@with_appcontext
def status():
    """Which activation settings the server has (names and yes/no only)."""
    from app.services.quickbooks_online import activation

    act = activation()
    click.echo(f"mode={act['mode']} ready={act['ready']}")
    for name, ok in act["items"]:
        click.echo(f"{name}={'yes' if ok else 'no'}")
