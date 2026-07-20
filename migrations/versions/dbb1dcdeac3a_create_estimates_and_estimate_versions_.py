"""Create estimates and estimate_versions tables

Revision ID: dbb1dcdeac3a
Revises: ba7989951903
Create Date: 2026-07-20 11:46:28.939865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbb1dcdeac3a'
down_revision = 'ba7989951903'
branch_labels = None
depends_on = None


def upgrade():
    # Create estimates without current_version_id FK first to avoid circular dependency.
    op.create_table(
        'estimates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('estimate_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_version_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('estimate_number'),
    )

    op.create_table(
        'estimate_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('estimate_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_label', sa.String(length=100), nullable=True),
        sa.Column('revision_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('overhead_percent', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('profit_percent', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('tax_percent', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('is_locked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'estimate_id',
            'version_number',
            name='uq_estimate_versions_estimate_id_version_number',
        ),
    )

    # Add the circular FK after both tables exist.
    with op.batch_alter_table('estimates') as batch_op:
        batch_op.create_foreign_key(
            'fk_estimates_current_version_id',
            'estimate_versions',
            ['current_version_id'],
            ['id'],
        )


def downgrade():
    with op.batch_alter_table('estimates') as batch_op:
        batch_op.drop_constraint(
            'fk_estimates_current_version_id',
            type_='foreignkey',
        )

    op.drop_table('estimate_versions')
    op.drop_table('estimates')
