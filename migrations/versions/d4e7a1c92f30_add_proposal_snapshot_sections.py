"""Add proposal snapshot sections and line items

Revision ID: d4e7a1c92f30
Revises: c8e4f2a91b07
Create Date: 2026-07-20 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e7a1c92f30'
down_revision = 'c8e4f2a91b07'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('proposals') as batch_op:
        batch_op.add_column(
            sa.Column(
                'overhead_percent',
                sa.Numeric(precision=8, scale=2),
                nullable=False,
                server_default='0',
            )
        )
        batch_op.add_column(
            sa.Column(
                'profit_percent',
                sa.Numeric(precision=8, scale=2),
                nullable=False,
                server_default='0',
            )
        )
        batch_op.add_column(
            sa.Column(
                'tax_percent',
                sa.Numeric(precision=8, scale=2),
                nullable=False,
                server_default='0',
            )
        )
        batch_op.alter_column(
            'estimate_id',
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.alter_column(
            'estimate_version_id',
            existing_type=sa.Integer(),
            nullable=True,
        )

    op.create_table(
        'proposal_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proposal_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=180), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'proposal_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proposal_section_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('source_line_item_id', sa.Integer(), nullable=True),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('markup_percent', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('extended_cost', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('extended_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['proposal_section_id'], ['proposal_sections.id']),
        sa.ForeignKeyConstraint(
            ['source_line_item_id'],
            ['estimate_line_items.id'],
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('proposal_line_items')
    op.drop_table('proposal_sections')
    with op.batch_alter_table('proposals') as batch_op:
        batch_op.drop_column('tax_percent')
        batch_op.drop_column('profit_percent')
        batch_op.drop_column('overhead_percent')
        batch_op.alter_column(
            'estimate_version_id',
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            'estimate_id',
            existing_type=sa.Integer(),
            nullable=False,
        )
