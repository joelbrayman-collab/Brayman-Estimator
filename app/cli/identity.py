"""One CalibraytAI identity: reconcile this site's people with Production (26 Oct 2026).

    flask identity reconcile            list what would happen (changes nothing)
    flask identity reconcile --apply    do it

Run on the Training Centre once it is connected (IDENTITY_PROVIDER_URL / IDENTITY_CLIENT_SECRET). For every real
person on this site (not a practice persona, i.e. not an address ending in ".invalid"):
- already has a Production identity: nothing changes on Production; from now on they sign in here with their
  Production password (their old Training Centre password stops being used). Listed so Joel can tell them.
- has no Production identity: one is created on Production carrying the password they already chose here (its
  hash; the password itself is never read), so it keeps working on both. No Production access is given.
What each person may do on each site is not touched.
"""

from __future__ import annotations

import click
from flask.cli import with_appcontext

identity_cli = click.Group("identity", help="One CalibraytAI identity across Production and the Training Centre.")


def _mask(address):
    user, _, domain = (address or "").partition("@")
    return f"{user[:2]}***@{domain}"


@identity_cli.command("reconcile")
@click.option("--apply", "apply_changes", is_flag=True, default=False, help="Make the changes (default: list only).")
@with_appcontext
def reconcile_command(apply_changes):
    from app.models.user import User
    from app.services.identity import (
        IdentityRefused,
        IdentityUnavailable,
        is_identity_client,
        local_only,
        remote_import,
        remote_lookup,
    )

    if not is_identity_client():
        raise click.ClickException("This site is not connected to CalibraytAI sign-in (IDENTITY_PROVIDER_URL / "
                                   "IDENTITY_CLIENT_SECRET are not set).")
    people = [u for u in User.query.order_by(User.id).all() if not local_only(u.email)]
    click.echo(f"{'APPLY' if apply_changes else 'DRY RUN (nothing changes)'}: {len(people)} real people on this site")
    try:
        known = remote_lookup([u.email for u in people])
    except (IdentityRefused, IdentityUnavailable) as exc:
        raise click.ClickException(str(exc))
    for user in people:
        state = "active" if user.is_active else "inactive"
        found = known.get(user.email.strip().lower()) or {}
        if not apply_changes:
            if not found.get("exists"):
                plan = "only here: will be created on Production with the password chosen here (no Production access)"
            else:
                plan = ("on both: Production's password wins from now on"
                        + ("" if found.get("production_access") else " (identity only, no Production access)")
                        + ("" if found.get("active") else "; INACTIVE on Production, so they cannot sign in here either"))
            click.echo(f"  {_mask(user.email)} ({state} here): {plan}")
            continue
        try:
            answer = remote_import(user.email, user.display_name, user.password_hash)
        except (IdentityRefused, IdentityUnavailable) as exc:
            click.echo(f"  {_mask(user.email)} ({state}): NOT DONE: {exc}")
            continue
        if answer.get("created"):
            click.echo(f"  {_mask(user.email)} ({state}): created on Production with the password chosen here")
        else:
            click.echo(f"  {_mask(user.email)} ({state}): already on Production; signs in here with that password")
