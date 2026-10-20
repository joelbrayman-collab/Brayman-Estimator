"""supplier PRO Desk: a supplier's own walk-in customers and quotations

Revision ID: pd1a2b3c4d5e
Revises: z3c4d5e6f7a8
Create Date: 2026-10-20

ADR-047 Amendment 1 (Joel, 20 Oct 2026). Eight new tables, all scoped to a
supplier and none to a contractor organization: supplier_customers,
supplier_quotes, supplier_quote_files, supplier_quote_events,
supplier_quote_links, supplier_price_imports, supplier_selling_prices,
supplier_quote_settings and supplier_building_assemblies (Quick Quote).

The canonical material catalogue gains five categories for the outbuilding
takeoff (ROOFING, CLADDING, TRIM, DOOR, TRUSS). No existing row is inserted,
changed or deleted; identities are created later, one at a time, when a
supplier maps a product (ADR-057 pattern).

Downgrade refuses while any row exists in the new tables or uses a new
category. Recovery for a database that holds such rows is the pre-migration
backup.
"""

from alembic import op
import sqlalchemy as sa


revision = "pd1a2b3c4d5e"
down_revision = "z3c4d5e6f7a8"
branch_labels = None
depends_on = None

NEW_TABLES = (
    "supplier_building_assemblies",
    "supplier_quote_settings",
    "supplier_selling_prices",
    "supplier_price_imports",
    "supplier_quote_links",
    "supplier_quote_events",
    "supplier_quote_files",
    "supplier_quotes",
    "supplier_customers",
)
NEW_CATEGORIES = ("ROOFING", "CLADDING", "TRIM", "DOOR", "TRUSS")
_CATEGORY = (
    "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS', 'CONCRETE', "
    "'DECKING', 'FASCIA', 'RAILING', 'GATE', 'FOUNDATION', 'CONNECTOR', 'FASTENER', "
    "'ROOFING', 'CLADDING', 'TRIM', 'DOOR', 'TRUSS')"
)
_CATEGORY_PRIOR = (
    "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS', 'CONCRETE', "
    "'DECKING', 'FASCIA', 'RAILING', 'GATE', 'FOUNDATION', 'CONNECTOR', 'FASTENER')"
)


def _replace_check(table, name, expression):
    with op.batch_alter_table(table) as batch:
        batch.drop_constraint(name, type_="check")
        batch.create_check_constraint(name, expression)


def _fk(column, target):
    return sa.ForeignKey(target, ondelete="RESTRICT")


def upgrade():
    op.create_table(
        "supplier_customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), _fk("supplier_id", "suppliers.id"), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("town", sa.String(120), nullable=True),
        sa.Column("consent_email", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_text", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_recorded_by_name", sa.String(160), nullable=True),
        sa.Column("consent_recorded_at", sa.DateTime(), nullable=True),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_name", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_supplier_customers_supplier_id", "supplier_customers", ["supplier_id"])

    op.create_table(
        "supplier_quotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), _fk("supplier_id", "suppliers.id"), nullable=False),
        sa.Column("supplier_location_id", sa.Integer(), _fk("supplier_location_id", "supplier_locations.id"), nullable=True),
        sa.Column("customer_id", sa.Integer(), _fk("customer_id", "supplier_customers.id"), nullable=False),
        sa.Column("number", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("building_system", sa.String(40), nullable=True),
        sa.Column("spec_json", sa.JSON(), nullable=True),
        sa.Column("choices_json", sa.JSON(), nullable=True),
        sa.Column("delivery_charge", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount_percent", sa.Numeric(6, 3), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("issued_json", sa.JSON(), nullable=True),
        sa.Column("issued_sha256", sa.String(64), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("issued_by_name", sa.String(160), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("total", sa.Numeric(14, 2), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("acceptance_method", sa.String(20), nullable=True),
        sa.Column("accepted_by_name", sa.String(160), nullable=True),
        sa.Column("acceptance_recorded_by_name", sa.String(160), nullable=True),
        sa.Column("accepted_sha256", sa.String(64), nullable=True),
        sa.Column("order_ready_at", sa.DateTime(), nullable=True),
        sa.Column("order_ready_by_name", sa.String(160), nullable=True),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_name", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("supplier_id", "number", name="uq_supplier_quotes_supplier_number"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'ISSUED', 'ACCEPTED', 'DECLINED', 'CANCELLED')", name="ck_supplier_quotes_status"
        ),
    )
    op.create_index("ix_supplier_quotes_supplier_id", "supplier_quotes", ["supplier_id"])
    op.create_index("ix_supplier_quotes_customer_id", "supplier_quotes", ["customer_id"])

    op.create_table(
        "supplier_quote_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quote_id", sa.Integer(), _fk("quote_id", "supplier_quotes.id"), nullable=False),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("mime", sa.String(40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("uploaded_by_name", sa.String(160), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("removed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_supplier_quote_files_quote_id", "supplier_quote_files", ["quote_id"])

    op.create_table(
        "supplier_quote_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quote_id", sa.Integer(), _fk("quote_id", "supplier_quotes.id"), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("actor_side", sa.String(20), nullable=False),
        sa.Column("actor_name", sa.String(160), nullable=False),
        sa.Column("at", sa.DateTime(), nullable=False),
        sa.Column("detail_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_supplier_quote_events_quote_id", "supplier_quote_events", ["quote_id"])

    op.create_table(
        "supplier_quote_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quote_id", sa.Integer(), _fk("quote_id", "supplier_quotes.id"), nullable=False),
        sa.Column("lookup_key", sa.String(40), nullable=False, unique=True),
        sa.Column("secret_sha256", sa.String(64), nullable=False),
        sa.Column("created_by_name", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("last_viewed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_supplier_quote_links_quote_id", "supplier_quote_links", ["quote_id"])

    op.create_table(
        "supplier_price_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), _fk("supplier_id", "suppliers.id"), nullable=False),
        sa.Column("supplier_location_id", sa.Integer(), _fk("supplier_location_id", "supplier_locations.id"), nullable=True),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("authorized_by_name", sa.String(160), nullable=False),
        sa.Column("imported_by_name", sa.String(160), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("rows_read", sa.Integer(), nullable=False),
        sa.Column("rows_loaded", sa.Integer(), nullable=False),
        sa.Column("rows_rejected", sa.Integer(), nullable=False),
        sa.Column("rejections_json", sa.JSON(), nullable=True),
        sa.CheckConstraint("source IN ('SUPPLIER_FILE', 'DEMO_SYNTHETIC')", name="ck_supplier_price_imports_source"),
    )
    op.create_index("ix_supplier_price_imports_supplier_id", "supplier_price_imports", ["supplier_id"])

    op.create_table(
        "supplier_selling_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_product_id", sa.Integer(), _fk("supplier_product_id", "supplier_products.id"), nullable=False),
        sa.Column("supplier_location_id", sa.Integer(), _fk("supplier_location_id", "supplier_locations.id"), nullable=True),
        sa.Column("import_id", sa.Integer(), _fk("import_id", "supplier_price_imports.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 4), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("discount_percent", sa.Numeric(6, 3), nullable=True),
        sa.Column("discount_rule", sa.String(160), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("availability", sa.String(20), nullable=True),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_supplier_selling_prices_supplier_product_id", "supplier_selling_prices", ["supplier_product_id"])
    op.create_index("ix_supplier_selling_prices_import_id", "supplier_selling_prices", ["import_id"])

    op.create_table(
        "supplier_quote_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), _fk("supplier_id", "suppliers.id"), nullable=False, unique=True),
        sa.Column("tax_label", sa.String(20), nullable=True),
        sa.Column("tax_rate_percent", sa.Numeric(6, 3), nullable=True),
        sa.Column("validity_days", sa.Integer(), nullable=True),
        sa.Column("default_delivery_charge", sa.Numeric(12, 2), nullable=True),
        sa.Column("terms_text", sa.Text(), nullable=True),
        sa.Column("contact_line", sa.String(300), nullable=True),
        sa.Column("updated_by_name", sa.String(160), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "supplier_building_assemblies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), _fk("supplier_id", "suppliers.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("building_system", sa.String(40), nullable=False),
        sa.Column("values_json", sa.JSON(), nullable=False),
        sa.Column("basis", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("approved_by_name", sa.String(160), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("retired_by_name", sa.String(160), nullable=True),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'RETIRED')", name="ck_supplier_building_assemblies_status"),
    )
    op.create_index("ix_supplier_building_assemblies_supplier_id", "supplier_building_assemblies", ["supplier_id"])

    _replace_check("canonical_materials", "ck_canonical_materials_category", _CATEGORY)


def downgrade():
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError(f"Downgrade refused: {table} holds rows. Restore the pre-migration backup instead.")
    placeholders = ", ".join(f"'{c}'" for c in NEW_CATEGORIES)
    if bind.execute(sa.text(f"SELECT COUNT(*) FROM canonical_materials WHERE category IN ({placeholders})")).scalar():
        raise RuntimeError("Downgrade refused: outbuilding catalogue rows exist. Restore the pre-migration backup instead.")
    _replace_check("canonical_materials", "ck_canonical_materials_category", _CATEGORY_PRIOR)
    for table in NEW_TABLES:
        op.drop_table(table)
