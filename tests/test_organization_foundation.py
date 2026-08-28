"""Tests for Milestone 011: Organization Foundation & Project Commercial Context (FG-007 / ADR-028)."""

from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import (
    Assembly,
    AssemblyItem,
    Client,
    CostItem,
    Estimate,
    EstimateLineItem,
    EstimateSection,
    EstimateVersion,
    Organization,
    Project,
    ProjectCommercialContext,
    Proposal,
    ProposalTemplate,
)
from app.services.commercial_context import (
    CommercialContextValidationError,
    create_initial_commercial_context,
    set_organization_reason_policy,
    update_commercial_context,
    validate_commercial_context_data,
)
from app.services.estimates import clone_current_version, create_estimate
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
    get_current_organization_id,
    set_current_organization_id,
)
from app.services.proposals import create_proposal_template, set_default_template


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )

    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def org_b(app):
    """Create a second organization for tenant isolation tests."""
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


# =========================================================================
# A. Organization Seed & Metadata Tests
# =========================================================================


def test_org_001_seed_and_metadata(app):
    org = Organization.query.get(DEFAULT_ORGANIZATION_ID)
    assert org is not None
    assert org.id == "ORG-001"
    assert org.legal_name == "Brayman Construction Inc."
    assert org.display_name == "Brayman Construction"
    assert "Merrickville" in org.primary_address
    assert org.default_region == "Eastern Ontario / Ottawa Valley"
    assert org.currency == "CAD"
    assert org.tax_jurisdiction == "Ontario (HST 13%)"
    assert org.is_active is True


# =========================================================================
# B. Tenant Query Isolation Tests
# =========================================================================


def test_organization_isolation_client(client, app, org_b):
    # Org 1 Client
    c1 = Client(name="Brayman Client", organization_id="ORG-001")
    # Org 2 Client
    c2 = Client(name="Apex Client", organization_id="ORG-002")
    db.session.add_all([c1, c2])
    db.session.commit()

    # Default request context is ORG-001
    resp = client.get("/clients/")
    assert resp.status_code == 200
    assert b"Brayman Client" in resp.data
    assert b"Apex Client" not in resp.data


def test_organization_isolation_project(client, app, org_b):
    c1 = Client(name="Brayman Client", organization_id="ORG-001")
    c2 = Client(name="Apex Client", organization_id="ORG-002")
    db.session.add_all([c1, c2])
    db.session.flush()

    p1 = Project(name="Brayman Project", client_id=c1.id, organization_id="ORG-001")
    p2 = Project(name="Apex Project", client_id=c2.id, organization_id="ORG-002")
    db.session.add_all([p1, p2])
    db.session.commit()

    resp = client.get("/projects/")
    assert resp.status_code == 200
    assert b"Brayman Project" in resp.data
    assert b"Apex Project" not in resp.data

    # Direct ID access to Org B project fails closed with 404
    resp_cross = client.get(f"/projects/{p2.id}")
    assert resp_cross.status_code == 404


def test_organization_isolation_cost_library(client, app, org_b):
    ci1 = CostItem(
        organization_id="ORG-001",
        code="LAB-001",
        name="Brayman Carpenter",
        category="Labour",
        unit="hr",
        unit_cost=Decimal("75.00"),
    )
    ci2 = CostItem(
        organization_id="ORG-002",
        code="LAB-001",  # Same code allowed in different org
        name="Apex Carpenter",
        category="Labour",
        unit="hr",
        unit_cost=Decimal("85.00"),
    )
    db.session.add_all([ci1, ci2])
    db.session.commit()

    resp = client.get("/cost-library/")
    assert resp.status_code == 200
    assert b"Brayman Carpenter" in resp.data
    assert b"Apex Carpenter" not in resp.data

    # Direct edit of Org B cost item fails closed
    resp_edit = client.get(f"/cost-library/{ci2.id}/edit")
    assert resp_edit.status_code == 404


def test_organization_isolation_assembly(client, app, org_b):
    a1 = Assembly(
        organization_id="ORG-001",
        code="ASY-001",
        name="Brayman Framing",
        category="Framing",
        unit="sqft",
    )
    a2 = Assembly(
        organization_id="ORG-002",
        code="ASY-001",
        name="Apex Framing",
        category="Framing",
        unit="sqft",
    )
    db.session.add_all([a1, a2])
    db.session.commit()

    resp = client.get("/assemblies/")
    assert resp.status_code == 200
    assert b"Brayman Framing" in resp.data
    assert b"Apex Framing" not in resp.data

    # Direct view of Org B assembly fails closed
    resp_view = client.get(f"/assemblies/{a2.id}")
    assert resp_view.status_code == 404


def test_organization_isolation_proposal_template(client, app, org_b):
    t1 = create_proposal_template(
        organization_id="ORG-001",
        name="Standard Proposal",
        company_name="Brayman Construction",
    )
    t2 = create_proposal_template(
        organization_id="ORG-002",
        name="Standard Proposal",  # Same name allowed in different org
        company_name="Apex Contracting",
    )

    resp = client.get("/proposal-templates/")
    assert resp.status_code == 200
    assert b"Standard Proposal" in resp.data
    assert t1.organization_id == "ORG-001"
    assert t2.organization_id == "ORG-002"


# =========================================================================
# C. Project Commercial Context Creation & Validation Tests
# =========================================================================


def test_project_context_validation_valid():
    data = {
        "project_type": "New Build",
        "pricing_posture": "Competitive",
        "execution_risk": "Normal",
        "schedule_condition": "Normal",
        "site_condition": "Normal",
        "estimate_stage": "Preliminary",
        "delivery_model": "Self-Perform",
    }
    validated = validate_commercial_context_data(data, organization_id="ORG-001")
    assert validated["project_type"] == "New Build"
    assert validated["pricing_posture"] == "Competitive"


def test_project_context_validation_invalid_choice():
    data = {
        "project_type": "InvalidType",
        "pricing_posture": "Competitive",
        "execution_risk": "Normal",
        "schedule_condition": "Normal",
        "site_condition": "Normal",
        "estimate_stage": "Preliminary",
        "delivery_model": "Self-Perform",
    }
    with pytest.raises(CommercialContextValidationError, match="Invalid or missing Project Type"):
        validate_commercial_context_data(data, organization_id="ORG-001")


def test_project_context_atomic_creation(app):
    c = Client(name="Test Client", organization_id="ORG-001")
    db.session.add(c)
    db.session.flush()

    p = Project(name="Atomic Project", client_id=c.id, organization_id="ORG-001")
    db.session.add(p)
    db.session.flush()

    ctx = create_initial_commercial_context(
        project_id=p.id,
        data={
            "project_type": "Addition",
            "pricing_posture": "Fair Market",
            "execution_risk": "Low",
            "schedule_condition": "Flexible",
            "site_condition": "Normal",
            "estimate_stage": "Budget",
            "delivery_model": "Mixed",
        },
        created_by="Lead Estimator",
        organization_id="ORG-001",
    )

    assert p.current_commercial_context.id == ctx.id
    assert ctx.version_number == 1
    assert ctx.is_current is True
    assert ctx.project_type == "Addition"
    assert ctx.created_by == "Lead Estimator"


# =========================================================================
# D. Project Commercial Context Versioning & History Tests
# =========================================================================


def test_project_context_versioning(app):
    c = Client(name="Versioning Client", organization_id="ORG-001")
    db.session.add(c)
    db.session.flush()

    p = Project(name="Versioned Project", client_id=c.id, organization_id="ORG-001")
    db.session.add(p)
    db.session.flush()

    v1 = create_initial_commercial_context(
        project_id=p.id,
        data={
            "project_type": "Renovation",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Budget",
            "delivery_model": "Self-Perform",
        },
        organization_id="ORG-001",
    )

    # Update to Version 2
    v2 = update_commercial_context(
        project_id=p.id,
        data={
            "project_type": "Renovation",
            "pricing_posture": "Selective",
            "execution_risk": "Elevated",
            "schedule_condition": "Compressed",
            "site_condition": "Restricted Access",
            "estimate_stage": "Tender",
            "delivery_model": "Self-Perform",
        },
        updated_by="Senior Estimator",
        change_summary="Scope expanded after site review",
        organization_id="ORG-001",
    )

    assert v2.version_number == 2
    assert v2.is_current is True
    assert v1.is_current is False
    assert v1.version_number == 1
    assert len(p.commercial_contexts) == 2
    assert p.current_commercial_context.id == v2.id
    assert v2.change_summary == "Scope expanded after site review"
    assert v2.created_by == "Senior Estimator"


# =========================================================================
# E. Policy-Driven Justification Tests
# =========================================================================


def test_org_001_policy_requires_reason_for_premium_and_high_risk(app):
    # Premium without justification must fail
    with pytest.raises(CommercialContextValidationError, match="justification reason is required"):
        validate_commercial_context_data(
            {
                "project_type": "New Build",
                "pricing_posture": "Premium",
                "execution_risk": "Normal",
                "schedule_condition": "Normal",
                "site_condition": "Normal",
                "estimate_stage": "Preliminary",
                "delivery_model": "Self-Perform",
                "justification_reason": "",
            },
            organization_id="ORG-001",
        )

    # Premium WITH justification must succeed
    validated = validate_commercial_context_data(
        {
            "project_type": "New Build",
            "pricing_posture": "Premium",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "justification_reason": "Executive client requested expedited luxury finishes",
        },
        organization_id="ORG-001",
    )
    assert validated["pricing_posture"] == "Premium"
    assert validated["justification_reason"] == "Executive client requested expedited luxury finishes"


def test_second_organization_custom_policy(app, org_b):
    # Register custom policy for ORG-002 where 'Critical' schedule requires reason, but 'Premium' posture does not
    set_organization_reason_policy(
        "ORG-002",
        {
            "schedule_conditions": ["Critical"],
        },
    )

    # In ORG-002, Premium without reason is allowed:
    validated_b = validate_commercial_context_data(
        {
            "project_type": "New Build",
            "pricing_posture": "Premium",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "justification_reason": "",
        },
        organization_id="ORG-002",
    )
    assert validated_b["pricing_posture"] == "Premium"

    # But Critical schedule without reason is rejected in ORG-002:
    with pytest.raises(CommercialContextValidationError, match="justification reason is required"):
        validate_commercial_context_data(
            {
                "project_type": "New Build",
                "pricing_posture": "Competitive",
                "execution_risk": "Normal",
                "schedule_condition": "Critical",
                "site_condition": "Normal",
                "estimate_stage": "Preliminary",
                "delivery_model": "Self-Perform",
                "justification_reason": "",
            },
            organization_id="ORG-002",
        )


# =========================================================================
# F & G. Estimate Version Context Immutability & Capture Tests
# =========================================================================


def test_estimate_version_captures_current_context_immutably(app):
    c = Client(name="Estimate Client", organization_id="ORG-001")
    db.session.add(c)
    db.session.flush()

    p = Project(name="Estimate Context Project", client_id=c.id, organization_id="ORG-001")
    db.session.add(p)
    db.session.flush()

    v1_ctx = create_initial_commercial_context(
        project_id=p.id,
        data={
            "project_type": "New Build",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Budget",
            "delivery_model": "Self-Perform",
        },
        organization_id="ORG-001",
    )

    est = create_estimate(
        project_id=p.id,
        estimate_number="EST-2026-CTX1",
        title="Contextual Estimate",
        organization_id="ORG-001",
    )

    est_v1 = est.current_version
    assert est_v1.commercial_context_id == v1_ctx.id
    assert est_v1.commercial_context.pricing_posture == "Competitive"

    # Update Project Commercial Context to v2
    v2_ctx = update_commercial_context(
        project_id=p.id,
        data={
            "project_type": "New Build",
            "pricing_posture": "Selective",
            "execution_risk": "Elevated",
            "schedule_condition": "Compressed",
            "site_condition": "Restricted Access",
            "estimate_stage": "Tender",
            "delivery_model": "Self-Perform",
        },
        updated_by="Project Manager",
        organization_id="ORG-001",
    )

    # est_v1 must STILL point to v1_ctx!
    db.session.refresh(est_v1)
    assert est_v1.commercial_context_id == v1_ctx.id
    assert est_v1.commercial_context.pricing_posture == "Competitive"

    # Cloning to a new estimate version captures the NEW context (v2_ctx)
    est_v2 = clone_current_version(
        est,
        version_label="Revised for Tender",
        revision_reason="Updated to project v2 context",
    )

    assert est_v2.commercial_context_id == v2_ctx.id
    assert est_v2.commercial_context.pricing_posture == "Selective"
    assert est_v1.commercial_context_id == v1_ctx.id


# =========================================================================
# H. UI Route Integration Tests (Project Creation & Context Edit)
# =========================================================================


def test_ui_project_creation_with_commercial_context(client, app):
    c = Client(name="UI Client", organization_id="ORG-001")
    db.session.add(c)
    db.session.commit()

    resp = client.post(
        "/projects/new",
        data={
            "name": "Commercial Context Project",
            "client_id": c.id,
            "status": "Lead",
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "justification_reason": "",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Commercial Context Project" in resp.data
    assert b"Addition" in resp.data
    assert b"Competitive" in resp.data

    p = Project.query.filter_by(name="Commercial Context Project").first()
    assert p is not None
    assert p.current_commercial_context is not None
    assert p.current_commercial_context.version_number == 1
    assert p.current_commercial_context.project_type == "Addition"


def test_ui_project_creation_rejected_when_reason_missing(client, app):
    c = Client(name="UI Client 2", organization_id="ORG-001")
    db.session.add(c)
    db.session.commit()

    # Premium pricing posture requires reason for ORG-001
    resp = client.post(
        "/projects/new",
        data={
            "name": "Premium Project Without Reason",
            "client_id": c.id,
            "status": "Lead",
            "project_type": "Addition",
            "pricing_posture": "Premium",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "justification_reason": "",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"justification reason is required" in resp.data
    assert Project.query.filter_by(name="Premium Project Without Reason").first() is None


def test_ui_project_context_edit_creates_new_version(client, app):
    c = Client(name="UI Client 3", organization_id="ORG-001")
    db.session.add(c)
    db.session.flush()
    p = Project(name="Context Edit Project", client_id=c.id, organization_id="ORG-001")
    db.session.add(p)
    db.session.flush()
    create_initial_commercial_context(
        project_id=p.id,
        data={
            "project_type": "Renovation",
            "pricing_posture": "Fair Market",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Budget",
            "delivery_model": "Self-Perform",
        },
        organization_id="ORG-001",
    )

    resp = client.post(
        f"/projects/{p.id}/commercial-context/edit",
        data={
            "project_type": "Renovation",
            "pricing_posture": "Selective",
            "execution_risk": "Elevated",
            "schedule_condition": "Compressed",
            "site_condition": "Occupied",
            "estimate_stage": "Tender",
            "delivery_model": "Self-Perform",
            "change_summary": "Updated after client consultation",
            "justification_reason": "",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Project commercial decision context updated to new version" in resp.data

    db.session.refresh(p)
    assert p.current_commercial_context.version_number == 2
    assert p.current_commercial_context.pricing_posture == "Selective"
    assert p.current_commercial_context.site_condition == "Occupied"


# =========================================================================
# I. Alembic Migration Upgrade & Backfill Cycle Test
# =========================================================================


def test_alembic_migration_upgrade_and_backfill(tmp_path):
    import os
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config

    db_path = tmp_path / "migration_test.db"
    db_uri = f"sqlite:///{db_path}"

    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = "migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini"
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)

        # 1. Upgrade to pre-M011 head (c9e0f1a2b3d4)
        command.upgrade(alembic_cfg, "c9e0f1a2b3d4")

        # 2. Insert legacy pre-M011 records directly into DB
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO clients (id, name, company, created_at) "
                    "VALUES (1, 'Legacy Client', 'Legacy Corp', '2026-01-01 10:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO projects (id, name, project_number, status, client_id, created_at) "
                    "VALUES (1, 'Legacy Project', 'PRJ-LEGACY', 'Estimating', 1, '2026-01-01 10:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO cost_items (id, code, name, category, unit, unit_cost, default_markup_percent, is_active, created_at, updated_at) "
                    "VALUES (1, 'LEG-01', 'Legacy Item', 'Material', 'ea', 10.00, 0, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO assemblies (id, code, name, category, unit, default_markup_percent, is_active, created_at, updated_at) "
                    "VALUES (1, 'ASY-LEG', 'Legacy Assembly', 'Framing', 'sqft', 0, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO proposal_templates (id, name, show_detailed_pricing, show_section_totals, show_allowances, show_tax, is_default, is_active, created_at, updated_at) "
                    "VALUES (1, 'Legacy Template', 1, 1, 1, 1, 1, 1, '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO estimates (id, project_id, estimate_number, title, status, created_at, updated_at) "
                    "VALUES (1, 1, 'EST-LEG-001', 'Legacy Estimate', 'Draft', '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO estimate_versions (id, estimate_id, version_number, version_label, status, subtotal, overhead_percent, profit_percent, tax_percent, total, is_locked, created_at, updated_at) "
                    "VALUES (1, 1, 1, 'v1', 'Draft', 100.00, 0, 0, 0, 100.00, 0, '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
                )
            )

        # 3. Upgrade to M011 head (d0a1b2c3d4e5)
        command.upgrade(alembic_cfg, "d0a1b2c3d4e5")

        # 4. Verify post-migration state
        with engine.begin() as conn:
            # ORG-001 seeded
            org = conn.execute(sa.text("SELECT id, display_name FROM organizations WHERE id='ORG-001'")).fetchone()
            assert org is not None
            assert org[0] == "ORG-001"
            assert org[1] == "Brayman Construction"

            # Root records backfilled to ORG-001
            client_org = conn.execute(sa.text("SELECT organization_id FROM clients WHERE id=1")).scalar()
            assert client_org == "ORG-001"

            proj_org = conn.execute(sa.text("SELECT organization_id FROM projects WHERE id=1")).scalar()
            assert proj_org == "ORG-001"

            cost_org = conn.execute(sa.text("SELECT organization_id FROM cost_items WHERE id=1")).scalar()
            assert cost_org == "ORG-001"

            asm_org = conn.execute(sa.text("SELECT organization_id FROM assemblies WHERE id=1")).scalar()
            assert asm_org == "ORG-001"

            tmpl_org = conn.execute(sa.text("SELECT organization_id FROM proposal_templates WHERE id=1")).scalar()
            assert tmpl_org == "ORG-001"

            # Project Commercial Context created with explicit Legacy / Unknown semantics
            pcc = conn.execute(
                sa.text("SELECT id, project_id, version_number, is_current, project_type, pricing_posture, execution_risk, schedule_condition, site_condition, estimate_stage, delivery_model, change_summary FROM project_commercial_contexts WHERE project_id=1")
            ).fetchone()
            assert pcc is not None
            assert pcc[1] == 1
            assert pcc[2] == 1
            assert pcc[3] == 1
            assert pcc[4] == "Legacy / Unknown"
            assert pcc[5] == "Legacy / Unknown"
            assert pcc[6] == "Legacy / Unknown"
            assert pcc[7] == "Legacy / Unknown"
            assert pcc[8] == "Legacy / Unknown"
            assert pcc[9] == "Legacy / Unknown"
            assert pcc[10] == "Legacy / Unknown"
            assert "Legacy project — commercial context not recorded historically" in pcc[11]

            # EstimateVersion backfilled to point to the commercial context
            ev_ctx = conn.execute(sa.text("SELECT commercial_context_id FROM estimate_versions WHERE id=1")).scalar()
            assert ev_ctx == pcc[0]

        # 5. Downgrade back to c9e0f1a2b3d4 and verify
        command.downgrade(alembic_cfg, "c9e0f1a2b3d4")


# =========================================================================
# J. Legacy Unknown Semantics & Protection Invariants
# =========================================================================


def test_new_project_rejects_legacy_unknown_submission(client, app):
    c = Client(name="New Project Client", organization_id="ORG-001")
    db.session.add(c)
    db.session.commit()

    # Attempt to submit 'Legacy / Unknown' during new project creation
    resp = client.post(
        "/projects/new",
        data={
            "name": "Invalid Legacy Selection Project",
            "client_id": c.id,
            "status": "Lead",
            "project_type": "Legacy / Unknown",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "justification_reason": "",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Invalid or missing Project Type" in resp.data
    assert Project.query.filter_by(name="Invalid Legacy Selection Project").first() is None


def test_legacy_project_can_update_to_version_2_while_old_estimate_stays_pinned(app, client):
    c = Client(name="Legacy Migration Client", organization_id="ORG-001")
    db.session.add(c)
    db.session.flush()

    p = Project(name="Historic Legacy Project", client_id=c.id, organization_id="ORG-001")
    db.session.add(p)
    db.session.flush()

    # Create the simulated M011 migration v1 legacy unknown context
    legacy_ctx = ProjectCommercialContext(
        project_id=p.id,
        version_number=1,
        is_current=True,
        project_type="Legacy / Unknown",
        pricing_posture="Legacy / Unknown",
        execution_risk="Legacy / Unknown",
        schedule_condition="Legacy / Unknown",
        site_condition="Legacy / Unknown",
        estimate_stage="Legacy / Unknown",
        delivery_model="Legacy / Unknown",
        change_summary="Legacy project — commercial context not recorded historically (M011 migration backfill)",
        created_by="M011 Migration Backfill",
    )
    db.session.add(legacy_ctx)
    db.session.flush()

    assert legacy_ctx.is_legacy_unknown is True

    # Legacy estimate created and tied to migration context
    est = create_estimate(
        project_id=p.id,
        estimate_number="EST-LEGACY-001",
        title="Pre-M011 Estimate",
        organization_id="ORG-001",
    )
    db.session.commit()

    legacy_est_version = est.current_version
    assert legacy_est_version.commercial_context_id == legacy_ctx.id
    assert legacy_est_version.commercial_context.is_legacy_unknown is True
    assert legacy_est_version.commercial_context.project_type == "Legacy / Unknown"

    # UI renders human-readable legacy unrecorded banner
    resp_view = client.get(f"/projects/{p.id}")
    assert resp_view.status_code == 200
    assert b"Legacy project \xe2\x80\x94 commercial context not recorded" in resp_view.data

    # User updates project to active valid Version 2
    resp_edit = client.post(
        f"/projects/{p.id}/commercial-context/edit",
        data={
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Elevated",
            "schedule_condition": "Compressed",
            "site_condition": "Restricted Access",
            "estimate_stage": "Tender",
            "delivery_model": "Self-Perform",
            "change_summary": "Activated legacy project with explicit commercial parameters",
            "justification_reason": "",
        },
        follow_redirects=True,
    )
    assert resp_edit.status_code == 200
    assert b"Project commercial decision context updated to new version" in resp_edit.data

    db.session.refresh(p)
    db.session.refresh(legacy_est_version)

    # Project is now on v2
    assert p.current_commercial_context.version_number == 2
    assert p.current_commercial_context.is_legacy_unknown is False
    assert p.current_commercial_context.project_type == "Addition"
    assert p.current_commercial_context.pricing_posture == "Competitive"

    # CRITICAL: Old historical estimate version is STILL pinned to the legacy unknown v1 context!
    assert legacy_est_version.commercial_context_id == legacy_ctx.id
    assert legacy_est_version.commercial_context.is_legacy_unknown is True
    assert legacy_est_version.commercial_context.version_number == 1
    assert legacy_est_version.commercial_context.project_type == "Legacy / Unknown"



