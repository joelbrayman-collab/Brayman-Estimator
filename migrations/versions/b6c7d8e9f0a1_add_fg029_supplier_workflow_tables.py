"""add fg029 supplier workflow tables

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-09-09 12:00:00.000000

Additive FG-029 MaterialRequirement + Supplier Catalogue tables.
No seed. Do not run live flask db upgrade from the FG-029 implementation prompt.
Downgrade drops new tables only.
"""

from alembic import op
import sqlalchemy as sa


revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("legal_name", sa.String(length=220), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_suppliers_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_suppliers_code"),
    )

    op.create_table(
        "supplier_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=220), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_supplier_locations_status",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supplier_id",
            "code",
            name="uq_supplier_locations_supplier_code",
        ),
    )
    op.create_index(
        "ix_supplier_locations_supplier_id",
        "supplier_locations",
        ["supplier_id"],
    )

    op.create_table(
        "contractor_supplier_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("supplier_location_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_contractor_supplier_accounts_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_location_id"],
            ["supplier_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "supplier_id",
            "supplier_location_id",
            name="uq_contractor_supplier_accounts_org_supplier_location",
        ),
    )
    op.create_index(
        "ix_contractor_supplier_accounts_organization_id",
        "contractor_supplier_accounts",
        ["organization_id"],
    )

    op.create_table(
        "supplier_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=220), nullable=False),
        sa.Column("sales_uom", sa.String(length=20), nullable=False),
        sa.Column("pack_qty", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_supplier_products_status",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supplier_id",
            "sku",
            name="uq_supplier_products_supplier_sku",
        ),
    )
    op.create_index(
        "ix_supplier_products_supplier_id",
        "supplier_products",
        ["supplier_id"],
    )

    op.create_table(
        "supplier_product_price_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=False),
        sa.Column("contractor_supplier_account_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["supplier_product_id"],
            ["supplier_products.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contractor_supplier_account_id"],
            ["contractor_supplier_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_supplier_product_price_evidence_supplier_product_id",
        "supplier_product_price_evidence",
        ["supplier_product_id"],
    )

    op.create_table(
        "supplier_product_availability_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=False),
        sa.Column("supplier_location_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('IN_STOCK', 'LIMITED', 'UNKNOWN')",
            name="ck_supplier_product_availability_evidence_status",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_product_id"],
            ["supplier_products.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_location_id"],
            ["supplier_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_supplier_product_availability_evidence_supplier_product_id",
        "supplier_product_availability_evidence",
        ["supplier_product_id"],
    )

    op.create_table(
        "canonical_material_supplier_maps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("canonical_material_id", sa.Integer(), nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=False),
        sa.Column(
            "requirement_to_sales_factor",
            sa.Numeric(precision=12, scale=6),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("approved_by_display_name", sa.String(length=150), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_canonical_material_supplier_maps_status",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_material_id"],
            ["canonical_materials.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_product_id"],
            ["supplier_products.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canonical_material_id",
            "supplier_product_id",
            name="uq_canonical_material_supplier_maps_identity_product",
        ),
    )
    op.create_index(
        "ix_canonical_material_supplier_maps_canonical_material_id",
        "canonical_material_supplier_maps",
        ["canonical_material_id"],
    )
    op.create_index(
        "ix_canonical_material_supplier_maps_supplier_product_id",
        "canonical_material_supplier_maps",
        ["supplier_product_id"],
    )

    op.create_table(
        "material_requirements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("canonical_material_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("canonical_uom", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_kind", sa.String(length=40), nullable=False),
        sa.Column("estimate_line_item_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'REVIEWED')",
            name="ck_material_requirements_status",
        ),
        sa.CheckConstraint(
            "canonical_uom IN ('EA', 'LF', 'SF', 'BF')",
            name="ck_material_requirements_uom",
        ),
        sa.CheckConstraint(
            "source_kind IN ('MANUAL', 'DEMO_SYNTHETIC', 'ESTIMATE_LINE_CITE', 'TAKEOFF_CITE')",
            name="ck_material_requirements_source_kind",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_material_id"],
            ["canonical_materials.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_line_item_id"],
            ["estimate_line_items.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_material_requirements_organization_id",
        "material_requirements",
        ["organization_id"],
    )
    op.create_index(
        "ix_material_requirements_project_id",
        "material_requirements",
        ["project_id"],
    )
    op.create_index(
        "ix_material_requirements_canonical_material_id",
        "material_requirements",
        ["canonical_material_id"],
    )

    op.create_table(
        "supplier_requirement_maps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("material_requirement_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("supplier_location_id", sa.Integer(), nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=True),
        sa.Column("mapping_status", sa.String(length=20), nullable=False),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("mapped_at", sa.DateTime(), nullable=True),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "mapping_status IN ('UNRESOLVED', 'REVIEW_REQUIRED', 'MAPPED')",
            name="ck_supplier_requirement_maps_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["material_requirement_id"],
            ["material_requirements.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_location_id"],
            ["supplier_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_product_id"],
            ["supplier_products.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "material_requirement_id",
            "supplier_id",
            "supplier_location_id",
            name="uq_supplier_requirement_maps_requirement_supplier_location",
        ),
    )
    op.create_index(
        "ix_supplier_requirement_maps_organization_id",
        "supplier_requirement_maps",
        ["organization_id"],
    )
    op.create_index(
        "ix_supplier_requirement_maps_project_id",
        "supplier_requirement_maps",
        ["project_id"],
    )
    op.create_index(
        "ix_supplier_requirement_maps_material_requirement_id",
        "supplier_requirement_maps",
        ["material_requirement_id"],
    )

    op.create_table(
        "supplier_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("supplier_location_id", sa.Integer(), nullable=False),
        sa.Column("contractor_supplier_account_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("issued_by_display_name", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'ISSUED')",
            name="ck_supplier_packages_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_location_id"],
            ["supplier_locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contractor_supplier_account_id"],
            ["contractor_supplier_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_supplier_packages_organization_id",
        "supplier_packages",
        ["organization_id"],
    )
    op.create_index(
        "ix_supplier_packages_project_id",
        "supplier_packages",
        ["project_id"],
    )
    op.create_index(
        "uq_supplier_packages_issued_project_supplier_location",
        "supplier_packages",
        ["project_id", "supplier_id", "supplier_location_id"],
        unique=True,
        sqlite_where=sa.text("status = 'ISSUED'"),
    )

    op.create_table(
        "supplier_package_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_package_id", sa.Integer(), nullable=False),
        sa.Column("material_requirement_id", sa.Integer(), nullable=False),
        sa.Column("canonical_material_code", sa.String(length=80), nullable=False),
        sa.Column("canonical_material_name", sa.String(length=220), nullable=False),
        sa.Column("requirement_qty", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("requirement_uom", sa.String(length=8), nullable=False),
        sa.Column("mapping_status", sa.String(length=20), nullable=False),
        sa.Column("supplier_sku", sa.String(length=80), nullable=True),
        sa.Column("supplier_product_description", sa.String(length=220), nullable=True),
        sa.Column("sales_qty", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("sales_uom", sa.String(length=20), nullable=True),
        sa.Column("price_amount", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("price_currency", sa.String(length=8), nullable=True),
        sa.Column("price_captured_at", sa.DateTime(), nullable=True),
        sa.Column("availability_status", sa.String(length=20), nullable=True),
        sa.Column("availability_captured_at", sa.DateTime(), nullable=True),
        sa.Column("delivery_stage", sa.String(length=40), nullable=True),
        sa.Column("demo_synthetic", sa.Boolean(), nullable=False),
        sa.Column("evidence_source", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(
            ["supplier_package_id"],
            ["supplier_packages.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_supplier_package_lines_supplier_package_id",
        "supplier_package_lines",
        ["supplier_package_id"],
    )


def downgrade():
    op.drop_index(
        "ix_supplier_package_lines_supplier_package_id",
        table_name="supplier_package_lines",
    )
    op.drop_table("supplier_package_lines")
    op.drop_index(
        "uq_supplier_packages_issued_project_supplier_location",
        table_name="supplier_packages",
    )
    op.drop_index("ix_supplier_packages_project_id", table_name="supplier_packages")
    op.drop_index(
        "ix_supplier_packages_organization_id",
        table_name="supplier_packages",
    )
    op.drop_table("supplier_packages")
    op.drop_index(
        "ix_supplier_requirement_maps_material_requirement_id",
        table_name="supplier_requirement_maps",
    )
    op.drop_index(
        "ix_supplier_requirement_maps_project_id",
        table_name="supplier_requirement_maps",
    )
    op.drop_index(
        "ix_supplier_requirement_maps_organization_id",
        table_name="supplier_requirement_maps",
    )
    op.drop_table("supplier_requirement_maps")
    op.drop_index(
        "ix_material_requirements_canonical_material_id",
        table_name="material_requirements",
    )
    op.drop_index(
        "ix_material_requirements_project_id",
        table_name="material_requirements",
    )
    op.drop_index(
        "ix_material_requirements_organization_id",
        table_name="material_requirements",
    )
    op.drop_table("material_requirements")
    op.drop_index(
        "ix_canonical_material_supplier_maps_supplier_product_id",
        table_name="canonical_material_supplier_maps",
    )
    op.drop_index(
        "ix_canonical_material_supplier_maps_canonical_material_id",
        table_name="canonical_material_supplier_maps",
    )
    op.drop_table("canonical_material_supplier_maps")
    op.drop_index(
        "ix_supplier_product_availability_evidence_supplier_product_id",
        table_name="supplier_product_availability_evidence",
    )
    op.drop_table("supplier_product_availability_evidence")
    op.drop_index(
        "ix_supplier_product_price_evidence_supplier_product_id",
        table_name="supplier_product_price_evidence",
    )
    op.drop_table("supplier_product_price_evidence")
    op.drop_index("ix_supplier_products_supplier_id", table_name="supplier_products")
    op.drop_table("supplier_products")
    op.drop_index(
        "ix_contractor_supplier_accounts_organization_id",
        table_name="contractor_supplier_accounts",
    )
    op.drop_table("contractor_supplier_accounts")
    op.drop_index("ix_supplier_locations_supplier_id", table_name="supplier_locations")
    op.drop_table("supplier_locations")
    op.drop_table("suppliers")
