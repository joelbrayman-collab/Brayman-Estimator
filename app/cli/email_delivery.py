"""Email checks for the server's shell (sign-in reliability, Joel, 26 Oct 2026).

    flask email status                       how this server sends email (names only; secrets as set / not set)
    flask email test-delivery --to ADDRESS   send a test and wait for the mail service to confirm delivery

The test reports two things separately: whether the mail service ACCEPTED it, and whether it confirmed
DELIVERY (the receiving mail server took it). Whether it is in the inbox is for the person to check: the
email's subject carries a test code to look for.
"""

from __future__ import annotations

import os
import secrets
import time

import click
from flask import current_app
from flask.cli import with_appcontext

email_cli = click.Group("email", help="Check how this server sends email, and prove an inbox receives it.")


def _mask(address: str) -> str:
    address = (address or "").strip().lower()
    if "@" not in address:
        return "?"
    user, domain = address.split("@", 1)
    return f"{user[:2]}***@{domain}"


def _setting(name: str) -> str:
    value = current_app.config.get(name)
    if value is None:
        value = os.environ.get(name, "")
    return str(value or "").strip()


@email_cli.command("status")
@with_appcontext
def status_command():
    """How this server sends email. Changes nothing; prints no secret."""
    from app.services.email_delivery import webhook_configured
    from app.services.transactional_email import email_delivery_configured, public_base_url

    provider = _setting("TRANSACTIONAL_EMAIL_PROVIDER") or "local (nothing is sent)"
    allow = [a for a in _setting("TRANSACTIONAL_UAT_ALLOWLIST").split(",") if a.strip()]
    click.echo(f"PROVIDER={provider}")
    click.echo(f"FROM={_setting('TRANSACTIONAL_FROM_EMAIL') or '(not set)'}")
    click.echo(f"POSTMARK_SERVER_TOKEN={'set' if _setting('POSTMARK_SERVER_TOKEN') else 'not set'}")
    click.echo(f"POSTMARK_WEBHOOK={'set' if webhook_configured() else 'not set'}")
    click.echo("ALLOWLIST=" + ("(empty: any address)" if not allow else
                               f"{len(allow)} address(es): " + ", ".join(_mask(a) for a in allow)))
    click.echo(f"PUBLIC_BASE_URL={public_base_url() or '(not set)'}")
    click.echo(f"READY={'yes' if email_delivery_configured() else 'no'}")


@email_cli.command("test-delivery")
@click.option("--to", "to_address", required=True, help="An inbox you can open, e.g. an iCloud or Gmail address.")
@click.option("--wait", "wait_seconds", default=180, show_default=True, type=int,
              help="How long to wait for the mail service to confirm delivery.")
@with_appcontext
def test_delivery_command(to_address, wait_seconds):
    """Send a test email and wait until the mail service confirms delivery or a bounce."""
    from app.models.transactional_message import PROVIDER_POSTMARK, STATUS_ACCEPTED, TEMPLATE_DELIVERY_TEST
    from app.services.email_delivery import (
        STATE_BOUNCED,
        STATE_DELIVERED,
        DeliveryError,
        check_with_postmark,
        state_of,
    )
    from app.services.transactional_email import send_transactional_message

    code = secrets.token_hex(3).upper()
    site = _setting("PUBLIC_BASE_URL") or "CalibraytAI"
    message = send_transactional_message(TEMPLATE_DELIVERY_TEST, to_address, variables={"code": code, "site": site},
                                         related_type="delivery_test")
    click.echo(f"TO={_mask(to_address)} TEST_CODE={code}")
    if message.status != STATUS_ACCEPTED:
        click.echo(f"ACCEPTED=no ({state_of(message).label})")
        raise SystemExit(1)
    click.echo(f"ACCEPTED=yes provider={message.provider} id={message.provider_message_id or '-'}")
    if message.provider != PROVIDER_POSTMARK:
        click.echo("DELIVERY=cannot be confirmed by this mail path (only Postmark reports delivery)")
        click.echo(f"INBOX=check {_mask(to_address)} for the subject 'CalibraytAI email test {code}'")
        raise SystemExit(2)
    deadline = time.monotonic() + max(0, wait_seconds)
    state = state_of(message)
    while True:
        try:
            check_with_postmark(message)
        except DeliveryError as exc:
            click.echo(f"CHECK=could not ask Postmark: {exc}")
        state = state_of(message)
        if state.code in (STATE_DELIVERED, STATE_BOUNCED) or time.monotonic() >= deadline:
            break
        time.sleep(5)
    click.echo(f"DELIVERY={state.code} ({state.label}{': ' + state.detail if state.detail and state.code != 'BOUNCED' else ''})")
    click.echo(f"INBOX=check {_mask(to_address)} (and junk) for the subject 'CalibraytAI email test {code}'")
    raise SystemExit(0 if state.code == STATE_DELIVERED else 1)
