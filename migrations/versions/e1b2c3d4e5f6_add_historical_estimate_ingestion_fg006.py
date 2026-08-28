"""add historical estimate ingestion fg006

Revision ID: e1b2c3d4e5f6
Revises: d0a1b2c3d4e5
Create Date: 2026-08-28 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1b2c3d4e5f6'
down_revision = 'd0a1b2c3d4e5'
branch_labels = None
depends_on = None


def upgrade():
    # 1. historical_source_workbooks
    op.create_table(
        'historical_source_workbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=50), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('extension', sa.String(length=10), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('byte_size', sa.Integer(), nullable=False),
        sa.Column('filesystem_modified_at', sa.DateTime(), nullable=True),
        sa.Column('template_family', sa.String(length=50), nullable=False),
        sa.Column('ingestion_status', sa.String(length=50), nullable=False),
        sa.Column('ingestion_version', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=150), nullable=False),
        sa.Column('source_file_path', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'sha256', 'ingestion_version', name='uq_historical_source_workbooks_org_sha_version')
    )
    with op.batch_alter_table('historical_source_workbooks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_source_workbooks_idempotency_key'), ['idempotency_key'], unique=True)
        batch_op.create_index(batch_op.f('ix_historical_source_workbooks_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_source_workbooks_sha256'), ['sha256'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_source_workbooks_source_id'), ['source_id'], unique=False)

    # 2. historical_estimates
    op.create_table(
        'historical_estimates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('source_workbook_id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(length=255), nullable=True),
        sa.Column('client_name', sa.String(length=255), nullable=True),
        sa.Column('project_address', sa.String(length=255), nullable=True),
        sa.Column('project_type', sa.String(length=100), nullable=True),
        sa.Column('template_family', sa.String(length=50), nullable=False),
        sa.Column('estimate_date', sa.String(length=50), nullable=True),
        sa.Column('estimate_number', sa.String(length=100), nullable=True),
        sa.Column('evidence_tier', sa.String(length=50), nullable=False),
        sa.Column('pricing_method', sa.String(length=50), nullable=False),
        sa.Column('markup_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('margin_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('direct_cost_total', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('markup_total', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('contingency_total', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('selling_price_before_tax', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('extraction_confidence', sa.Float(), nullable=False),
        sa.Column('review_status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['source_workbook_id'], ['historical_source_workbooks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('historical_estimates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_estimates_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_estimates_source_workbook_id'), ['source_workbook_id'], unique=False)

    # 3. historical_source_observations
    op.create_table(
        'historical_source_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('source_workbook_id', sa.Integer(), nullable=False),
        sa.Column('sheet_name', sa.String(length=100), nullable=False),
        sa.Column('cell_coordinate', sa.String(length=20), nullable=False),
        sa.Column('raw_formula', sa.Text(), nullable=True),
        sa.Column('raw_value', sa.Text(), nullable=True),
        sa.Column('display_value', sa.Text(), nullable=True),
        sa.Column('normalized_entity_type', sa.String(length=100), nullable=False),
        sa.Column('normalized_entity_id', sa.Integer(), nullable=True),
        sa.Column('normalized_field', sa.String(length=100), nullable=False),
        sa.Column('extraction_rule_id', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['source_workbook_id'], ['historical_source_workbooks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('historical_source_observations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_source_observations_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_source_observations_source_workbook_id'), ['source_workbook_id'], unique=False)

    # 4. historical_cost_line_items
    op.create_table(
        'historical_cost_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('historical_estimate_id', sa.Integer(), nullable=False),
        sa.Column('division', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('extended_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('markup_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('selling_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=True),
        sa.Column('is_allowance', sa.Boolean(), nullable=False),
        sa.Column('provenance_observation_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['historical_estimate_id'], ['historical_estimates.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['provenance_observation_id'], ['historical_source_observations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('historical_cost_line_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_cost_line_items_historical_estimate_id'), ['historical_estimate_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_cost_line_items_organization_id'), ['organization_id'], unique=False)

    # 5. historical_labour_items
    op.create_table(
        'historical_labour_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('historical_estimate_id', sa.Integer(), nullable=False),
        sa.Column('task_description', sa.String(length=255), nullable=False),
        sa.Column('crew_size', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('duration_days', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('hours_per_day', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('total_man_hours', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('extended_labour_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('formula_pattern', sa.String(length=100), nullable=True),
        sa.Column('provenance_observation_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['historical_estimate_id'], ['historical_estimates.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['provenance_observation_id'], ['historical_source_observations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('historical_labour_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_labour_items_historical_estimate_id'), ['historical_estimate_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_labour_items_organization_id'), ['organization_id'], unique=False)

    # 6. historical_subcontract_items
    op.create_table(
        'historical_subcontract_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('historical_estimate_id', sa.Integer(), nullable=False),
        sa.Column('trade_category', sa.String(length=100), nullable=False),
        sa.Column('scope_description', sa.String(length=255), nullable=False),
        sa.Column('subcontractor_name', sa.String(length=255), nullable=True),
        sa.Column('direct_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('markup_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('selling_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('installation_included', sa.Boolean(), nullable=True),
        sa.Column('quote_date', sa.String(length=50), nullable=True),
        sa.Column('provenance_observation_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['historical_estimate_id'], ['historical_estimates.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['provenance_observation_id'], ['historical_source_observations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('historical_subcontract_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_subcontract_items_historical_estimate_id'), ['historical_estimate_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_subcontract_items_organization_id'), ['organization_id'], unique=False)

    # 7. historical_data_quality_flags
    op.create_table(
        'historical_data_quality_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('source_workbook_id', sa.Integer(), nullable=False),
        sa.Column('historical_estimate_id', sa.Integer(), nullable=True),
        sa.Column('flag_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('sheet_name', sa.String(length=100), nullable=True),
        sa.Column('cell_coordinate', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['historical_estimate_id'], ['historical_estimates.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['source_workbook_id'], ['historical_source_workbooks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('historical_data_quality_flags', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_data_quality_flags_organization_id'), ['organization_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_data_quality_flags_source_workbook_id'), ['source_workbook_id'], unique=False)

    # 8. historical_estimate_review_decisions
    op.create_table(
        'historical_estimate_review_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(length=50), nullable=False),
        sa.Column('historical_estimate_id', sa.Integer(), nullable=False),
        sa.Column('review_status', sa.String(length=50), nullable=False),
        sa.Column('evidence_tier', sa.String(length=50), nullable=False),
        sa.Column('reviewed_by', sa.String(length=100), nullable=False),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['historical_estimate_id'], ['historical_estimates.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('historical_estimate_review_decisions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historical_estimate_review_decisions_historical_estimate_id'), ['historical_estimate_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_historical_estimate_review_decisions_organization_id'), ['organization_id'], unique=False)


def downgrade():
    op.drop_table('historical_estimate_review_decisions')
    op.drop_table('historical_data_quality_flags')
    op.drop_table('historical_subcontract_items')
    op.drop_table('historical_labour_items')
    op.drop_table('historical_cost_line_items')
    op.drop_table('historical_source_observations')
    op.drop_table('historical_estimates')
    op.drop_table('historical_source_workbooks')
