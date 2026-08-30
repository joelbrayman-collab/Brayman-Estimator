"""add permit foundation v1 fg015

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-08-30 19:30:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa

from app.models.jurisdiction import (
    JURISDICTION_ALIAS_SEED,
    JURISDICTION_SEED,
    normalize_jurisdiction_text,
)


revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jurisdiction_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("ahj_name", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["jurisdiction_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_jurisdiction_definitions_code"),
        sa.CheckConstraint(
            "kind IN ('country', 'province_state', 'municipality')",
            name="ck_jurisdiction_definitions_kind",
        ),
    )
    with op.batch_alter_table("jurisdiction_definitions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_jurisdiction_definitions_kind"),
            ["kind"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_jurisdiction_definitions_parent_id"),
            ["parent_id"],
            unique=False,
        )

    op.create_table(
        "jurisdiction_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jurisdiction_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=160), nullable=False),
        sa.Column("normalized_alias", sa.String(length=160), nullable=False),
        sa.ForeignKeyConstraint(
            ["jurisdiction_id"],
            ["jurisdiction_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalized_alias",
            "jurisdiction_id",
            name="uq_jurisdiction_aliases_normalized_jurisdiction",
        ),
    )
    with op.batch_alter_table("jurisdiction_aliases", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_jurisdiction_aliases_jurisdiction_id"),
            ["jurisdiction_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_jurisdiction_aliases_normalized_alias"),
            ["normalized_alias"],
            unique=False,
        )

    op.create_table(
        "project_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("street", sa.String(length=255), nullable=True),
        sa.Column("municipality", sa.String(length=160), nullable=True),
        sa.Column("province_state", sa.String(length=120), nullable=True),
        sa.Column("postal_zip", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("location_kind", sa.String(length=40), nullable=False),
        sa.Column("legal_description", sa.Text(), nullable=True),
        sa.Column("parcel_identifier", sa.String(length=120), nullable=True),
        sa.Column("future_civic_address", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_project_locations_project_id"),
    )
    with op.batch_alter_table("project_locations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_project_locations_organization_id"),
            ["organization_id"],
            unique=False,
        )

    op.create_table(
        "permit_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=50), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("is_stale", sa.Boolean(), nullable=False),
        sa.Column("recheck_required", sa.Boolean(), nullable=False),
        sa.Column("street_snapshot", sa.String(length=255), nullable=True),
        sa.Column("municipality_snapshot", sa.String(length=160), nullable=True),
        sa.Column("province_state_snapshot", sa.String(length=120), nullable=True),
        sa.Column("postal_zip_snapshot", sa.String(length=20), nullable=True),
        sa.Column("country_snapshot", sa.String(length=120), nullable=True),
        sa.Column("location_completeness", sa.String(length=32), nullable=False),
        sa.Column("jurisdiction_status", sa.String(length=32), nullable=False),
        sa.Column("resolved_jurisdiction_id", sa.Integer(), nullable=True),
        sa.Column("resolved_jurisdiction_code", sa.String(length=80), nullable=True),
        sa.Column("resolved_jurisdiction_name", sa.String(length=160), nullable=True),
        sa.Column("resolved_ahj_name", sa.String(length=160), nullable=True),
        sa.Column("permit_context_class", sa.String(length=80), nullable=False),
        sa.Column("advisory_status", sa.String(length=40), nullable=False),
        sa.Column("generation_method", sa.String(length=40), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("generated_by", sa.String(length=150), nullable=True),
        sa.Column("plan_site_review_status", sa.String(length=40), nullable=False),
        sa.Column("substantive_analysis_status", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(
            ["resolved_jurisdiction_id"],
            ["jurisdiction_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_permit_profiles_project_version",
        ),
        sa.CheckConstraint(
            "kind IN ('PRELIMINARY_FOUNDATION')",
            name="ck_permit_profiles_kind",
        ),
        sa.CheckConstraint(
            "location_completeness IN ('LOCATION_COMPLETE', 'LOCATION_INCOMPLETE')",
            name="ck_permit_profiles_location_completeness",
        ),
        sa.CheckConstraint(
            "jurisdiction_status IN ('JURISDICTION_RESOLVED', 'JURISDICTION_UNRESOLVED')",
            name="ck_permit_profiles_jurisdiction_status",
        ),
        sa.CheckConstraint(
            "permit_context_class IN ("
            "'New dwelling', 'Addition', 'Renovation', 'Garage/accessory', "
            "'Additional dwelling/coach house', 'Commercial', 'Other/unspecified'"
            ")",
            name="ck_permit_profiles_permit_context_class",
        ),
        sa.CheckConstraint(
            "advisory_status IN ('PRELIMINARY_FOUNDATION_ONLY')",
            name="ck_permit_profiles_advisory_status",
        ),
        sa.CheckConstraint(
            "generation_method IN ('DETERMINISTIC_PLATFORM')",
            name="ck_permit_profiles_generation_method",
        ),
        sa.CheckConstraint(
            "plan_site_review_status IN ('NOT_PERFORMED')",
            name="ck_permit_profiles_plan_site_review",
        ),
        sa.CheckConstraint(
            "substantive_analysis_status IN ('NOT_AVAILABLE')",
            name="ck_permit_profiles_substantive_analysis",
        ),
    )
    with op.batch_alter_table("permit_profiles", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_permit_profiles_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_profiles_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_permit_profiles_resolved_jurisdiction_id"),
            ["resolved_jurisdiction_id"],
            unique=False,
        )

    now = datetime.utcnow()
    bind = op.get_bind()
    definitions = sa.table(
        "jurisdiction_definitions",
        sa.column("code", sa.String),
        sa.column("kind", sa.String),
        sa.column("name", sa.String),
        sa.column("parent_id", sa.Integer),
        sa.column("ahj_name", sa.String),
        sa.column("created_at", sa.DateTime),
    )
    aliases = sa.table(
        "jurisdiction_aliases",
        sa.column("jurisdiction_id", sa.Integer),
        sa.column("alias", sa.String),
        sa.column("normalized_alias", sa.String),
    )
    code_to_id = {}
    for item in JURISDICTION_SEED:
        exists = bind.execute(
            sa.text("SELECT id FROM jurisdiction_definitions WHERE code = :code"),
            {"code": item["code"]},
        ).fetchone()
        if exists:
            code_to_id[item["code"]] = exists[0]
            continue
        parent_id = code_to_id.get(item["parent_code"]) if item["parent_code"] else None
        bind.execute(
            definitions.insert().values(
                code=item["code"],
                kind=item["kind"],
                name=item["name"],
                parent_id=parent_id,
                ahj_name=item["ahj_name"],
                created_at=now,
            )
        )
        row_id = bind.execute(
            sa.text("SELECT id FROM jurisdiction_definitions WHERE code = :code"),
            {"code": item["code"]},
        ).scalar()
        code_to_id[item["code"]] = row_id

    for code, alias in JURISDICTION_ALIAS_SEED:
        jurisdiction_id = code_to_id.get(code)
        if jurisdiction_id is None:
            continue
        normalized = normalize_jurisdiction_text(alias)
        exists = bind.execute(
            sa.text(
                "SELECT 1 FROM jurisdiction_aliases "
                "WHERE jurisdiction_id = :jid AND normalized_alias = :alias"
            ),
            {"jid": jurisdiction_id, "alias": normalized},
        ).fetchone()
        if exists:
            continue
        bind.execute(
            aliases.insert().values(
                jurisdiction_id=jurisdiction_id,
                alias=alias,
                normalized_alias=normalized,
            )
        )


def downgrade():
    with op.batch_alter_table("permit_profiles", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_permit_profiles_resolved_jurisdiction_id"))
        batch_op.drop_index(batch_op.f("ix_permit_profiles_project_id"))
        batch_op.drop_index(batch_op.f("ix_permit_profiles_organization_id"))
    op.drop_table("permit_profiles")

    with op.batch_alter_table("project_locations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_project_locations_organization_id"))
    op.drop_table("project_locations")

    with op.batch_alter_table("jurisdiction_aliases", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_jurisdiction_aliases_normalized_alias"))
        batch_op.drop_index(batch_op.f("ix_jurisdiction_aliases_jurisdiction_id"))
    op.drop_table("jurisdiction_aliases")

    with op.batch_alter_table("jurisdiction_definitions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_jurisdiction_definitions_parent_id"))
        batch_op.drop_index(batch_op.f("ix_jurisdiction_definitions_kind"))
    op.drop_table("jurisdiction_definitions")
