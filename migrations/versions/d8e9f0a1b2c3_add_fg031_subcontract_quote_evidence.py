"""add fg031 subcontract quote evidence

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-09-10 10:00:00.000000

Additive FG-031 Slice B Subcontractor + SubcontractQuoteEvidence + nullable
costing-snapshot quote freeze columns. No seed. Do not run live flask db
upgrade from the FG-031 Slice B implementation prompt.
Downgrade drops new tables and freeze columns only.
"""

from alembic import op
import sqlalchemy as sa


revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "subcontractors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("legal_name", sa.String(length=220), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_subcontractors_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_subcontractors_org_code",
        ),
    )
    op.create_index(
        "ix_subcontractors_organization_id",
        "subcontractors",
        ["organization_id"],
    )

    op.create_table(
        "subcontract_quote_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("estimate_id", sa.Integer(), nullable=False),
        sa.Column("estimate_version_id", sa.Integer(), nullable=False),
        sa.Column("estimate_line_item_id", sa.Integer(), nullable=False),
        sa.Column("estimate_scope_delivery_id", sa.Integer(), nullable=True),
        sa.Column("subcontractor_id", sa.Integer(), nullable=False),
        sa.Column("quote_reference", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("quote_date", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("included_scope", sa.Text(), nullable=True),
        sa.Column("exclusions", sa.Text(), nullable=True),
        sa.Column("provenance_note", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=150), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("selection_status", sa.String(length=20), nullable=False),
        sa.Column("selected_by", sa.Integer(), nullable=True),
        sa.Column("selected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "selection_status IN ('RECEIVED', 'SELECTED', 'REJECTED', 'SUPERSEDED')",
            name="ck_subcontract_quote_evidence_selection_status",
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
            ["estimate_id"],
            ["estimates.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_version_id"],
            ["estimate_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_line_item_id"],
            ["estimate_line_items.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_scope_delivery_id"],
            ["estimate_scope_deliveries.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subcontractor_id"],
            ["subcontractors.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["selected_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_subcontract_quote_evidence_organization_id",
        "subcontract_quote_evidence",
        ["organization_id"],
    )
    op.create_index(
        "ix_subcontract_quote_evidence_project_id",
        "subcontract_quote_evidence",
        ["project_id"],
    )
    op.create_index(
        "ix_subcontract_quote_evidence_estimate_version_id",
        "subcontract_quote_evidence",
        ["estimate_version_id"],
    )
    op.create_index(
        "ix_subcontract_quote_evidence_estimate_line_item_id",
        "subcontract_quote_evidence",
        ["estimate_line_item_id"],
    )
    op.create_index(
        "ix_subcontract_quote_evidence_subcontractor_id",
        "subcontract_quote_evidence",
        ["subcontractor_id"],
    )

    with op.batch_alter_table("estimate_costing_snapshot_lines", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("subcontract_quote_evidence_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("subcontract_quote_reference", sa.String(length=120), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "subcontract_quoted_amount",
                sa.Numeric(precision=14, scale=2),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("subcontract_quote_currency", sa.String(length=3), nullable=True)
        )
        batch_op.add_column(sa.Column("subcontract_quote_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("subcontractor_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("subcontract_subcontractor_code", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "subcontract_subcontractor_legal_name",
                sa.String(length=220),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "fk_costing_snapshot_lines_subcontract_quote_evidence_id",
            "subcontract_quote_evidence",
            ["subcontract_quote_evidence_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_foreign_key(
            "fk_costing_snapshot_lines_subcontractor_id",
            "subcontractors",
            ["subcontractor_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade():
    with op.batch_alter_table("estimate_costing_snapshot_lines", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_costing_snapshot_lines_subcontractor_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_costing_snapshot_lines_subcontract_quote_evidence_id",
            type_="foreignkey",
        )
        batch_op.drop_column("subcontract_subcontractor_legal_name")
        batch_op.drop_column("subcontract_subcontractor_code")
        batch_op.drop_column("subcontractor_id")
        batch_op.drop_column("subcontract_quote_date")
        batch_op.drop_column("subcontract_quote_currency")
        batch_op.drop_column("subcontract_quoted_amount")
        batch_op.drop_column("subcontract_quote_reference")
        batch_op.drop_column("subcontract_quote_evidence_id")

    op.drop_index(
        "ix_subcontract_quote_evidence_subcontractor_id",
        table_name="subcontract_quote_evidence",
    )
    op.drop_index(
        "ix_subcontract_quote_evidence_estimate_line_item_id",
        table_name="subcontract_quote_evidence",
    )
    op.drop_index(
        "ix_subcontract_quote_evidence_estimate_version_id",
        table_name="subcontract_quote_evidence",
    )
    op.drop_index(
        "ix_subcontract_quote_evidence_project_id",
        table_name="subcontract_quote_evidence",
    )
    op.drop_index(
        "ix_subcontract_quote_evidence_organization_id",
        table_name="subcontract_quote_evidence",
    )
    op.drop_table("subcontract_quote_evidence")
    op.drop_index("ix_subcontractors_organization_id", table_name="subcontractors")
    op.drop_table("subcontractors")
