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


@identity_cli.command("owner-setup")
@click.option("--owner-email", required=True, help="The one identity that becomes Instance Owner here.")
@click.option("--supplier-to", default="", help="Move the owner email's Supplier Hub login(s) to this address.")
@click.option("--organization-id", default="ORG-001", show_default=True)
@click.option("--create", "create_name", default="", help="Create OWNER-EMAIL's sign-in here with this display name if it "
              "does not exist (the Training Centre: the password stays the one CalibraytAI password on Production).")
@click.option("--apply", "apply_changes", is_flag=True, default=False, help="Make the changes (default: list only).")
@with_appcontext
def owner_setup_command(owner_email, supplier_to, organization_id, create_name, apply_changes):
    """Joel's one identity (26 Oct 2026): make OWNER-EMAIL this company's Instance Owner, keep the previous owner as a
    System Administrator, and move any Supplier Hub login on OWNER-EMAIL to SUPPLIER-TO (a sign-in cannot be both a
    contractor and a supplier). Uses the existing authority services, so their history is recorded. No password is
    read, changed or printed; a new supplier address gets a sign-in with no usable password (send it a link)."""
    from app import db
    from app.models.organization import Organization
    from app.models.supplier_catalogue import Supplier
    from app.models.supplier_portal import SupplierUserMembership
    from app.models.user import User, UserMembership
    from app.services.instance_authority import (
        appoint_system_administrator,
        is_instance_owner,
        set_instance_owner,
    )
    from app.services.supplier_hub import add_supplier_user, revoke_supplier_user

    org = db.session.get(Organization, organization_id)
    if org is None:
        raise click.ClickException(f"No company {organization_id} here.")
    owner = User.query.filter(db.func.lower(User.email) == owner_email.strip().lower()).first()
    if owner is None and create_name:
        click.echo(f"  {_mask(owner_email)}: no sign-in here yet; will be created as {create_name}")
        if apply_changes:
            import secrets

            from app.services.auth import hash_password

            owner = User(email=owner_email.strip().lower(), display_name=create_name[:150],
                         password_hash=hash_password(secrets.token_urlsafe(32)), is_active=True)
            db.session.add(owner)
            db.session.commit()
        else:
            click.echo(f"{'DRY RUN (nothing changes)'} for {org.display_name}: then member and Instance Owner")
            return
    if owner is None or not owner.is_active:
        raise click.ClickException("OWNER-EMAIL is not an active sign-in here (use --create \"Name\" to add it).")
    previous = next((m for m in UserMembership.query.filter_by(organization_id=org.id, is_active=True)
                     if is_instance_owner(m.user, org.id)), None)
    supplier_rows = SupplierUserMembership.query.filter_by(user_id=owner.id, status="ACTIVE").all()
    if supplier_rows and not supplier_to:
        raise click.ClickException(f"{_mask(owner.email)} is a Supplier Hub login for {len(supplier_rows)} supplier(s); "
                                   "give --supplier-to <address> to move it first.")
    click.echo(f"{'APPLY' if apply_changes else 'DRY RUN (nothing changes)'} for {org.display_name}")
    for row in supplier_rows:
        supplier = db.session.get(Supplier, row.supplier_id)
        click.echo(f"  move Supplier Hub login for {supplier.legal_name if supplier else row.supplier_id}: "
                   f"{_mask(owner.email)} -> {_mask(supplier_to)}")
    owner_membership = UserMembership.query.filter_by(user_id=owner.id, organization_id=org.id).first()
    click.echo(f"  {_mask(owner.email)}: {'already a member' if owner_membership else 'add as a member'} of "
               f"{org.display_name}; make Instance Owner")
    if previous is not None and previous.user_id != owner.id:
        click.echo(f"  previous owner {_mask(previous.user.email)}: stays active, appointed System Administrator")
    if not apply_changes:
        return
    for row in supplier_rows:
        supplier = db.session.get(Supplier, row.supplier_id)
        add_supplier_user(organization_id=row.created_by_organization_id, supplier=supplier,
                          display_name=f"{owner.display_name} (supplier)", email=supplier_to,
                          actor_name="Joel's one identity (owner-setup)")
        revoke_supplier_user(row)
    if owner_membership is None:
        owner_membership = UserMembership(user_id=owner.id, organization_id=org.id, is_active=True)
        db.session.add(owner_membership)
        db.session.commit()
    elif not owner_membership.is_active:
        owner_membership.is_active = True
        db.session.commit()
    actor = previous.user_id if previous is not None else owner.id
    set_instance_owner(org.id, owner_membership.id, actor)
    db.session.commit()
    if previous is not None and previous.user_id != owner.id:
        appoint_system_administrator(org.id, previous.id, owner.id)
        db.session.commit()
    click.echo("  done")
