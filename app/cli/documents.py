"""flask documents connect-existing | reindex (31 Oct 2026).

connect-existing: idempotent; connects existing plans, generated contracts, CaliSIGN signed copies, drawing sets and
past job workbooks as documents by reference (no file is copied or moved) and prints the reconciliation. Writes only
to the document tables. Run it after the release migration; re-running is a no-op.
"""

from __future__ import annotations

import click
from flask.cli import with_appcontext

from app.models import Organization


@click.group("documents")
def documents_cli():
    """Company documents."""


@documents_cli.command("connect-existing")
@click.option("--organization", "organization_id", default=None, help="Only this organization (e.g. ORG-001).")
@click.option("--dry-run", is_flag=True, help="Report the counts and keep nothing.")
@with_appcontext
def connect_existing(organization_id, dry_run):
    from app.services.documents.sources import connect_existing_documents

    orgs = [organization_id] if organization_id else [o.id for o in Organization.query.order_by(Organization.id)]
    all_reconciled = True
    for org in orgs:
        report = connect_existing_documents(org, dry_run=dry_run)
        click.echo(f"[{org}]{' (dry run)' if dry_run else ''}")
        for line in report.lines():
            click.echo(f"  {line}")
        all_reconciled = all_reconciled and report.reconciled
    click.echo(f"RECONCILED={'yes' if all_reconciled else 'no'}")
    if not all_reconciled:
        raise SystemExit(1)


@documents_cli.command("reindex")
@click.option("--organization", "organization_id", default=None)
@with_appcontext
def reindex(organization_id):
    from app.services.documents.fts import rebuild
    from app.services.documents.ingest import extract_missing

    # Review fix I3 (1 Nov 2026): text a document page does not extract in the request (files over MAX_SYNC_BYTES).
    click.echo(f"TEXT_EXTRACTED={extract_missing(organization_id)}")
    count = rebuild(organization_id)
    click.echo(f"INDEXED={count}" if count else "INDEXED=0 (FTS5 not available or no documents; search uses the fallback)")
