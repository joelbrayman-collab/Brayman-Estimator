"""Project identity and estimate controls (Joel, 30 Oct 2026)

Revision ID: r5e6f7a8b9c0
Revises: a4d5e6f7a8b9
Create Date: 2026-10-30

The four project-level values Brayman works with: Brayman Project #, Client Project #, labour rate and target gross
margin.

Brayman Project # (projects.project_number, the existing column): assigned automatically when a project record is
created, BC-YYYY-NNNN for Brayman (ORG-001; another organization uses its own id as the prefix). The new table
project_number_sequences holds the last number issued per organization and year; it only counts up, so a number is
never reused. Existing projects with no number get one here, in creation order (year of creation); a project that
already has a number keeps it untouched, and the internal Shop / Company Work record keeps its COMPANY-TIME number.

Client Project # (projects.client_project_number, new, text, not unique): the client's own reference; never generated,
so every existing project starts blank. project_identity_events is the append-only history of both identifiers.

Estimate labour rate and target gross margin (four new nullable columns on estimate_versions): captured from the
company defaults when an estimate or version is created and changed by the estimator. Existing versions stay NULL
and keep resolving as before: no estimate is repriced.

Downgrade refuses once any number has been issued through the new sequence or any new value is held; recovery is
then the pre-migration backup.
"""

import re
from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = "r5e6f7a8b9c0"
down_revision = "a4d5e6f7a8b9"
branch_labels = None
depends_on = None

ORG_PREFIXES = {"ORG-001": "BC"}  # app/services/project_identity.py keeps the same map

VERSION_COLUMNS = (
    ("labour_rate", sa.Numeric(10, 2)),
    ("labour_rate_reason", sa.Text()),
    ("target_gross_margin", sa.Numeric(10, 6)),
    ("target_gross_margin_reason", sa.Text()),
)


def _prefix(org_id):
    return ORG_PREFIXES.get(org_id) or re.sub(r"[^A-Z0-9-]", "", (org_id or "").upper()) or "P"


def _year(value):
    if isinstance(value, datetime):
        return value.year
    return int(str(value)[:4])


def upgrade():
    # Plain ADD COLUMN (no table rebuild): existing rows stay byte-for-byte as they are.
    for name, kind in VERSION_COLUMNS:
        op.add_column("estimate_versions", sa.Column(name, kind, nullable=True))
    op.add_column("projects", sa.Column("client_project_number", sa.String(length=80), nullable=True))
    op.create_index("ix_projects_client_project_number", "projects", ["client_project_number"])
    op.create_table(
        "project_number_sequences",
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("last_value", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("organization_id", "year"),
    )
    op.create_table(
        "project_identity_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=50), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("field", sa.String(length=40), nullable=False),
        sa.Column("previous_value", sa.String(length=80), nullable=True),
        sa.Column("new_value", sa.String(length=80), nullable=True),
        sa.Column("actor_identifier", sa.String(length=150), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("field IN ('BRAYMAN_PROJECT_NUMBER', 'CLIENT_PROJECT_NUMBER')",
                           name="ck_project_identity_events_field"),
    )
    op.create_index("ix_project_identity_events_project_id", "project_identity_events", ["project_id"])
    op.create_index("ix_project_identity_events_org_project", "project_identity_events", ["organization_id", "project_id"])

    # Brayman Project # for existing projects without one, in creation order. Existing numbers are never touched.
    bind = op.get_bind()
    now = datetime.utcnow()
    taken = {row[0] for row in bind.execute(sa.text("SELECT project_number FROM projects WHERE project_number IS NOT NULL"))}
    last = {}
    pattern = re.compile(r"^(.+)-(\d{4})-(\d{4,})$")
    for org_id, number in bind.execute(sa.text(
            "SELECT organization_id, project_number FROM projects WHERE project_number IS NOT NULL")):
        found = pattern.match(number or "")
        if found and found.group(1) == _prefix(org_id):
            key = (org_id, int(found.group(2)))
            last[key] = max(last.get(key, 0), int(found.group(3)))
    rows = bind.execute(sa.text(
        "SELECT id, organization_id, created_at FROM projects WHERE project_number IS NULL "
        "ORDER BY organization_id, created_at, id")).fetchall()
    for project_id, org_id, created_at in rows:
        year = _year(created_at)
        key = (org_id, year)
        value = last.get(key, 0)
        while True:
            value += 1
            number = f"{_prefix(org_id)}-{year}-{value:04d}"
            if number not in taken:
                break
        last[key] = value
        taken.add(number)
        bind.execute(sa.text("UPDATE projects SET project_number = :n WHERE id = :i AND project_number IS NULL"),
                     {"n": number, "i": project_id})
        bind.execute(sa.text(
            "INSERT INTO project_identity_events (organization_id, project_id, field, previous_value, new_value, "
            "actor_identifier, actor_user_id, reason, created_at) VALUES (:o, :p, 'BRAYMAN_PROJECT_NUMBER', NULL, :n, "
            "'migration r5e6f7a8b9c0', NULL, 'Assigned to an existing project in creation order', :t)"),
            {"o": org_id, "p": project_id, "n": number, "t": now})
    for (org_id, year), value in sorted(last.items()):
        bind.execute(sa.text("INSERT INTO project_number_sequences (organization_id, year, last_value, updated_at) "
                             "VALUES (:o, :y, :v, :t)"), {"o": org_id, "y": year, "v": value, "t": now})


def downgrade():
    bind = op.get_bind()
    used = bind.execute(sa.text(
        "SELECT (SELECT COUNT(*) FROM project_number_sequences) + (SELECT COUNT(*) FROM project_identity_events)"
        " + (SELECT COUNT(*) FROM projects WHERE client_project_number IS NOT NULL)"
        " + (SELECT COUNT(*) FROM estimate_versions WHERE labour_rate IS NOT NULL OR labour_rate_reason IS NOT NULL"
        "    OR target_gross_margin IS NOT NULL OR target_gross_margin_reason IS NOT NULL)"
    )).scalar()
    if used:
        raise RuntimeError("Project numbers have been issued or new values are held; restore the pre-migration backup instead.")
    op.drop_index("ix_project_identity_events_org_project", table_name="project_identity_events")
    op.drop_index("ix_project_identity_events_project_id", table_name="project_identity_events")
    op.drop_table("project_identity_events")
    op.drop_table("project_number_sequences")
    op.drop_index("ix_projects_client_project_number", table_name="projects")
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("client_project_number")
    with op.batch_alter_table("estimate_versions") as batch_op:
        for name, _kind in reversed(VERSION_COLUMNS):
            batch_op.drop_column(name)
