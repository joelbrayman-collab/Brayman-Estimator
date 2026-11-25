"""Company documents and the equipment register (RDIMS, 31 Oct 2026)

Revision ID: t7a8b9c0d1e2
Revises: s6f7a8b9c0d1
Create Date: 2026-10-31

The one migration of the Task-First / Documents release. Additive only: eight new tables, their indexes and
insert-only triggers, and (only when this SQLite build has FTS5) the document_search virtual table. No existing table
is altered and no row is written: existing plans, contracts and signed PDFs are connected afterwards by the
idempotent ``flask documents connect-existing`` (and lazily when a project's Documents page opens), never here.

New tables: organization_equipment, organization_equipment_events, documents, document_versions, document_links,
document_dates, document_events, document_text (+ document_search and its FTS5 shadow tables when available).

Downgrade refuses once any new table holds a row; recovery is then the pre-migration backup.
"""

from alembic import op
import sqlalchemy as sa

revision = "t7a8b9c0d1e2"
down_revision = "s6f7a8b9c0d1"
branch_labels = None
depends_on = None

NEW_TABLES = ("document_text", "document_events", "document_dates", "document_links", "document_versions",
              "documents", "organization_equipment_events", "organization_equipment")

FTS_CREATE_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS document_search USING fts5("
    "organization_id UNINDEXED, sensitivity UNINDEXED, status UNINDEXED, "
    "title, filename, keywords, labels, body, "
    "tokenize = 'unicode61 remove_diacritics 2', prefix = '2 3')"
)


def _in(column, values):
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def _org():
    return sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                     nullable=False)


def _user(name, nullable=True):
    return sa.Column(name, sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=nullable)


def _triggers(table, message):
    op.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} "
               f"BEGIN SELECT RAISE(ABORT, '{message}'); END")
    op.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} "
               f"BEGIN SELECT RAISE(ABORT, '{message}'); END")


def _fts5_available(bind) -> bool:
    try:
        bind.exec_driver_sql("CREATE VIRTUAL TABLE IF NOT EXISTS temp.__documents_fts_probe USING fts5(x)")
        bind.exec_driver_sql("DROP TABLE IF EXISTS temp.__documents_fts_probe")
        return True
    except Exception:  # noqa: BLE001
        return False


def upgrade():
    op.create_table(
        "organization_equipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("unit_number", sa.String(length=40), nullable=True),
        sa.Column("make", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("serial_number", sa.String(length=80), nullable=True),
        sa.Column("plate_or_registration", sa.String(length=40), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("purchased_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        _user("created_by_user_id"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        _user("updated_by_user_id"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(_in("category", ("VEHICLE", "TRAILER", "HEAVY_EQUIPMENT", "TOOL", "LIFT", "OTHER")),
                           name="ck_organization_equipment_category"),
        sa.CheckConstraint("status IN ('ACTIVE', 'RETIRED')", name="ck_organization_equipment_status"),
        sa.CheckConstraint("year IS NULL OR (year >= 1900 AND year <= 2100)", name="ck_organization_equipment_year"),
    )
    op.create_index("ix_organization_equipment_organization_id", "organization_equipment", ["organization_id"])
    op.create_index("ix_organization_equipment_org_status", "organization_equipment", ["organization_id", "status"])
    op.create_index("uq_organization_equipment_unit", "organization_equipment", ["organization_id", "unit_number"],
                    unique=True, sqlite_where=sa.text("unit_number IS NOT NULL"))

    op.create_table(
        "organization_equipment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("organization_equipment.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("field_name", sa.String(length=40), nullable=True),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        _user("actor_user_id"),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("event_type IN ('CREATED', 'UPDATED', 'RETIRED', 'RESTORED')",
                           name="ck_organization_equipment_events_type"),
    )
    op.create_index("ix_organization_equipment_events_organization_id", "organization_equipment_events",
                    ["organization_id"])
    op.create_index("ix_organization_equipment_events_equipment_id", "organization_equipment_events", ["equipment_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=32), nullable=False, unique=True),
        _org(),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=60), nullable=False),
        sa.Column("type_basis", sa.String(length=20), nullable=False),
        sa.Column("type_rule", sa.String(length=60), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sensitivity", sa.String(length=20), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("reference_number", sa.String(length=120), nullable=True),
        sa.Column("counterparty", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", sa.String(length=500), nullable=True),
        _user("created_by_user_id"),
        sa.Column("created_by_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        _user("archived_by_user_id"),
        sa.Column("archived_by_name", sa.String(length=150), nullable=True),
        sa.Column("archive_reason", sa.String(length=500), nullable=True),
        sa.CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_documents_status"),
        sa.CheckConstraint("type_basis IN ('SUGGESTED', 'CONFIRMED')", name="ck_documents_type_basis"),
        sa.CheckConstraint("sensitivity IN ('STANDARD', 'PEOPLE', 'FINANCIAL')", name="ck_documents_sensitivity"),
        sa.CheckConstraint("origin IN ('UPLOAD', 'LINKED_RECORD', 'BACKFILL')", name="ck_documents_origin"),
    )
    op.create_index("ix_documents_organization_id", "documents", ["organization_id"])
    op.create_index("ix_documents_org_status_created", "documents", ["organization_id", "status", "created_at"])
    op.create_index("ix_documents_org_type", "documents", ["organization_id", "document_type"])

    op.create_table(
        "document_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("source_kind", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=120), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("availability", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        _user("created_by_user_id"),
        sa.Column("created_by_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("document_id", "version_number", name="uq_document_versions_number"),
        sa.CheckConstraint("version_number >= 1", name="ck_document_versions_number"),
        sa.CheckConstraint("byte_size >= 0", name="ck_document_versions_size"),
        sa.CheckConstraint(_in("source_kind", ("UPLOAD", "PLAN_DOCUMENT", "SIGNING_EXECUTED", "GENERATED_CONTRACT",
                                               "DRAWING_SET", "HISTORICAL_WORKBOOK")),
                           name="ck_document_versions_source_kind"),
        sa.CheckConstraint(
            "(source_kind = 'UPLOAD' AND source_id IS NULL AND storage_key IS NOT NULL)"
            " OR (source_kind <> 'UPLOAD' AND source_id IS NOT NULL AND storage_key IS NULL)",
            name="ck_document_versions_source"),
        sa.CheckConstraint("availability IN ('AVAILABLE', 'MISSING')", name="ck_document_versions_availability"),
    )
    op.create_index("ix_document_versions_document_id", "document_versions", ["document_id"])
    op.create_index("ix_document_versions_org_sha", "document_versions", ["organization_id", "sha256"])
    op.create_index("uq_document_versions_one_current", "document_versions", ["document_id"], unique=True,
                    sqlite_where=sa.text("is_current = 1"))
    op.create_index("uq_document_versions_source", "document_versions", ["organization_id", "source_kind", "source_id"],
                    unique=True, sqlite_where=sa.text("source_kind <> 'UPLOAD'"))

    contexts = ("COMPANY", "PROJECT", "PERSON", "EQUIPMENT", "SUPPLIER", "SUBCONTRACTOR", "CUSTOMER")
    columns = {"PROJECT": "project_id", "PERSON": "membership_id", "EQUIPMENT": "equipment_id",
               "SUPPLIER": "supplier_id", "SUBCONTRACTOR": "subcontractor_id", "CUSTOMER": "client_id"}
    order = ("project_id", "membership_id", "equipment_id", "supplier_id", "subcontractor_id", "client_id")

    def _branch(kind):
        set_column = columns.get(kind)
        parts = [f"{c} IS NOT NULL" if c == set_column else f"{c} IS NULL" for c in order]
        # Same text as the model's CHECK (set column first).
        if set_column:
            parts = [f"{set_column} IS NOT NULL"] + [f"{c} IS NULL" for c in order if c != set_column]
        return f"(context_kind = '{kind}' AND " + " AND ".join(parts) + ")"

    op.create_table(
        "document_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("context_kind", sa.String(length=20), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("membership_id", sa.Integer(), sa.ForeignKey("user_memberships.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("organization_equipment.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("subcontractor_id", sa.Integer(), sa.ForeignKey("subcontractors.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("record_kind", sa.String(length=40), nullable=True),
        sa.Column("record_id", sa.Integer(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        _user("linked_by_user_id"),
        sa.Column("linked_by_name", sa.String(length=150), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.Column("unlinked_at", sa.DateTime(), nullable=True),
        _user("unlinked_by_user_id"),
        sa.Column("unlinked_by_name", sa.String(length=150), nullable=True),
        sa.Column("unlink_reason", sa.String(length=500), nullable=True),
        sa.CheckConstraint(_in("context_kind", contexts), name="ck_document_links_context_kind"),
        sa.CheckConstraint(" OR ".join(_branch(k) for k in contexts), name="ck_document_links_context"),
        sa.CheckConstraint("record_kind IS NULL OR " + _in("record_kind", (
            "PURCHASE_ORDER", "CHANGE_ORDER", "SUBCONTRACT_COMMITMENT", "SUBCONTRACT_QUOTE", "ESTIMATE_VERSION",
            "PROPOSAL", "SIGNING_REQUEST", "GENERATED_CONTRACT")), name="ck_document_links_record_kind"),
        sa.CheckConstraint("(record_kind IS NULL AND record_id IS NULL) OR (record_kind IS NOT NULL AND record_id IS "
                           "NOT NULL)", name="ck_document_links_record"),
    )
    op.create_index("ix_document_links_document_id", "document_links", ["document_id"])
    for column in ("membership_id", "equipment_id", "supplier_id", "subcontractor_id", "client_id"):
        op.create_index(f"ix_document_links_{column}", "document_links", [column])
    op.create_index("ix_document_links_org_context_project", "document_links",
                    ["organization_id", "context_kind", "project_id"])
    op.create_index("uq_document_links_primary", "document_links", ["document_id"], unique=True,
                    sqlite_where=sa.text("is_primary = 1 AND unlinked_at IS NULL"))
    op.create_index("uq_document_links_company", "document_links", ["document_id"], unique=True,
                    sqlite_where=sa.text("unlinked_at IS NULL AND context_kind = 'COMPANY'"))
    for kind, column in columns.items():
        op.create_index(f"uq_document_links_{kind.lower()}", "document_links", ["document_id", column], unique=True,
                        sqlite_where=sa.text(f"unlinked_at IS NULL AND context_kind = '{kind}'"))

    op.create_table(
        "document_dates",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("document_versions.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("date_kind", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Date(), nullable=False),
        sa.Column("basis", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("evidence_text", sa.String(length=240), nullable=True),
        sa.Column("evidence_page", sa.Integer(), nullable=True),
        sa.Column("extractor_version", sa.String(length=40), nullable=True),
        sa.Column("remind_days_before", sa.Integer(), nullable=False),
        sa.Column("proposed_at", sa.DateTime(), nullable=False),
        _user("decided_by_user_id"),
        sa.Column("decided_by_name", sa.String(length=150), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(_in("date_kind", ("ISSUED", "EFFECTIVE", "EXPIRES", "INSPECTION_DUE", "RENEWAL_DUE",
                                             "WARRANTY_ENDS")), name="ck_document_dates_kind"),
        sa.CheckConstraint("basis IN ('EXTRACTED', 'ENTERED')", name="ck_document_dates_basis"),
        sa.CheckConstraint("status IN ('PROPOSED', 'CONFIRMED', 'REJECTED')", name="ck_document_dates_status"),
        sa.CheckConstraint("remind_days_before >= 0 AND remind_days_before <= 365", name="ck_document_dates_remind"),
    )
    op.create_index("ix_document_dates_document_id", "document_dates", ["document_id"])
    op.create_index("ix_document_dates_version_id", "document_dates", ["version_id"])
    op.create_index("ix_document_dates_org_status_value", "document_dates", ["organization_id", "status", "value"])
    op.create_index("uq_document_dates_confirmed", "document_dates", ["version_id", "date_kind"], unique=True,
                    sqlite_where=sa.text("status = 'CONFIRMED'"))

    op.create_table(
        "document_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("document_versions.id", ondelete="RESTRICT"),
                  nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("field_name", sa.String(length=40), nullable=True),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        _user("actor_user_id"),
        sa.Column("actor_name", sa.String(length=150), nullable=False),
        sa.Column("at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(_in("event_type", (
            "CREATED", "VERSION_ADDED", "VERSION_SUPERSEDED", "FIELD_CORRECTED", "TYPE_CONFIRMED", "LINK_ADDED",
            "LINK_ENDED", "DATE_PROPOSED", "DATE_CONFIRMED", "DATE_REJECTED", "DATE_ENTERED", "DATE_CHANGED",
            "TEXT_EXTRACTED", "ARCHIVED", "RESTORED", "DUPLICATE_LINKED", "REGISTERED_FROM_RECORD", "MARKED_MISSING",
            "DOWNLOADED")), name="ck_document_events_type"),
    )
    op.create_index("ix_document_events_organization_id", "document_events", ["organization_id"])
    op.create_index("ix_document_events_document_id", "document_events", ["document_id"])

    op.create_table(
        "document_text",
        sa.Column("id", sa.Integer(), primary_key=True),
        _org(),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("document_versions.id", ondelete="RESTRICT"),
                  nullable=False, unique=True),
        sa.Column("extractor_name", sa.String(length=60), nullable=False),
        sa.Column("extractor_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('EXTRACTED', 'NO_TEXT', 'UNSUPPORTED', 'FAILED', 'FROM_SOURCE')",
                           name="ck_document_text_status"),
    )

    _triggers("document_events", "document events are insert-only")
    _triggers("organization_equipment_events", "equipment events are insert-only")

    bind = op.get_bind()
    if bind.dialect.name == "sqlite" and _fts5_available(bind):
        op.execute(FTS_CREATE_SQL)
    else:
        print("FTS5 not available: document search uses the fallback.")


def downgrade():
    bind = op.get_bind()
    held = 0
    for table in NEW_TABLES:
        held += bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()
    if held:
        raise RuntimeError("Documents or equipment are held; restore the pre-migration backup instead of "
                           "downgrading.")
    op.execute("DROP TABLE IF EXISTS document_search")
    for table in ("document_events", "organization_equipment_events"):
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_update")
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_delete")
    for table in NEW_TABLES:
        op.drop_table(table)
