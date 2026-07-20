"""Add proposal templates and proposals

Revision ID: c8e4f2a91b07
Revises: f57338a61491
Create Date: 2026-07-20 12:22:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c8e4f2a91b07'
down_revision = 'f57338a61491'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'proposal_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_name', sa.String(length=180), nullable=True),
        sa.Column('company_address', sa.String(length=255), nullable=True),
        sa.Column('company_phone', sa.String(length=50), nullable=True),
        sa.Column('company_email', sa.String(length=150), nullable=True),
        sa.Column('company_website', sa.String(length=180), nullable=True),
        sa.Column('logo_path', sa.String(length=255), nullable=True),
        sa.Column('primary_color', sa.String(length=20), nullable=True),
        sa.Column('accent_color', sa.String(length=20), nullable=True),
        sa.Column('default_intro_text', sa.Text(), nullable=True),
        sa.Column('default_scope_intro', sa.Text(), nullable=True),
        sa.Column('default_exclusions', sa.Text(), nullable=True),
        sa.Column('default_clarifications', sa.Text(), nullable=True),
        sa.Column('default_schedule_text', sa.Text(), nullable=True),
        sa.Column('default_payment_terms', sa.Text(), nullable=True),
        sa.Column('default_warranty_text', sa.Text(), nullable=True),
        sa.Column('default_acceptance_text', sa.Text(), nullable=True),
        sa.Column('show_detailed_pricing', sa.Boolean(), nullable=False),
        sa.Column('show_section_totals', sa.Boolean(), nullable=False),
        sa.Column('show_allowances', sa.Boolean(), nullable=False),
        sa.Column('show_tax', sa.Boolean(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proposal_number', sa.String(length=50), nullable=False),
        sa.Column('estimate_id', sa.Integer(), nullable=False),
        sa.Column('estimate_version_id', sa.Integer(), nullable=False),
        sa.Column('proposal_template_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('client_name', sa.String(length=150), nullable=False),
        sa.Column('client_company', sa.String(length=150), nullable=True),
        sa.Column('client_address', sa.String(length=255), nullable=True),
        sa.Column('client_email', sa.String(length=150), nullable=True),
        sa.Column('client_phone', sa.String(length=50), nullable=True),
        sa.Column('project_name', sa.String(length=180), nullable=False),
        sa.Column('project_address', sa.String(length=255), nullable=True),
        sa.Column('estimate_number', sa.String(length=50), nullable=False),
        sa.Column('estimate_version_number', sa.Integer(), nullable=False),
        sa.Column('estimate_version_label', sa.String(length=100), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('overhead_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('profit_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('intro_text', sa.Text(), nullable=True),
        sa.Column('scope_intro', sa.Text(), nullable=True),
        sa.Column('exclusions', sa.Text(), nullable=True),
        sa.Column('clarifications', sa.Text(), nullable=True),
        sa.Column('schedule_text', sa.Text(), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('warranty_text', sa.Text(), nullable=True),
        sa.Column('acceptance_text', sa.Text(), nullable=True),
        sa.Column('show_detailed_pricing', sa.Boolean(), nullable=False),
        sa.Column('show_section_totals', sa.Boolean(), nullable=False),
        sa.Column('show_allowances', sa.Boolean(), nullable=False),
        sa.Column('show_tax', sa.Boolean(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates.id']),
        sa.ForeignKeyConstraint(['estimate_version_id'], ['estimate_versions.id']),
        sa.ForeignKeyConstraint(['proposal_template_id'], ['proposal_templates.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('proposal_number'),
    )


def downgrade():
    op.drop_table('proposals')
    op.drop_table('proposal_templates')
