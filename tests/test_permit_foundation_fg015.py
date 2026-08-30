"""Tests for FG-015 Permit Foundation V1 — location, jurisdiction, preliminary profile."""

import inspect
import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import (
    Client,
    Estimate,
    Organization,
    PermitProfile,
    Project,
    ProjectLocation,
)
from app.models.jurisdiction import (
    JURISDICTION_ALIAS_SEED,
    JURISDICTION_SEED,
    JurisdictionAlias,
    JurisdictionDefinition,
)
from app.models.project import (
    DEFAULT_PERMIT_CONTEXT_CLASS,
    JURISDICTION_RESOLVED,
    JURISDICTION_UNRESOLVED,
    LOCATION_COMPLETE,
    LOCATION_INCOMPLETE,
    PERMIT_ADVISORY_STATUS,
    PERMIT_CONTEXT_CLASSES,
    PERMIT_GENERATION_METHOD,
    PERMIT_PROFILE_KIND_PRELIMINARY,
    PLAN_SITE_REVIEW_NOT_PERFORMED,
    SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE,
)
from app.plan_intelligence.models import PlanDocument, TakeoffPackage
from app.services.commercial_context import create_initial_commercial_context
from app.services.jurisdiction import (
    assert_platform_jurisdiction_not_org_mutable,
    ensure_jurisdiction_seed,
    resolve_jurisdiction,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
)
from app.services.permit_foundation import (
    PermitFoundationError,
    assemble_permit_foundation_state,
    establish_project_location_and_profile,
)
from app.services.project_hub import assemble_project_hub


OTTAWA_LOCATION = {
    "street": "100 Test Civic Street",
    "municipality": "Ottawa",
    "province_state": "Ontario",
    "postal_zip": None,
    "country": "Canada",
}

COMMERCIAL_CREATE = {
    "project_type": "Addition",
    "pricing_posture": "Competitive",
    "execution_risk": "Normal",
    "schedule_condition": "Normal",
    "site_condition": "Normal",
    "estimate_stage": "Preliminary",
    "delivery_model": "Self-Perform",
    "justification_reason": "",
}


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg015",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_jurisdiction_seed(commit=True)
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="City of Ottawa",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _make_client(name="FG015 Client", org_id=DEFAULT_ORGANIZATION_ID):
    row = Client(name=name, organization_id=org_id)
    db.session.add(row)
    db.session.commit()
    return row


def _make_existing_project(
    *,
    name="Existing Address Project",
    address="99 Ambiguous Free Text Road",
    org_id=DEFAULT_ORGANIZATION_ID,
    client_name="Existing Client",
):
    client_row = _make_client(client_name, org_id)
    project = Project(
        name=name,
        address=address,
        client_id=client_row.id,
        status="Lead",
        organization_id=org_id,
    )
    db.session.add(project)
    db.session.flush()
    create_initial_commercial_context(
        project_id=project.id,
        data={
            "project_type": "Addition",
            "pricing_posture": "Competitive",
            "execution_risk": "Normal",
            "schedule_condition": "Normal",
            "site_condition": "Normal",
            "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform",
            "change_summary": "Existing project commercial context",
        },
        created_by="Estimator",
        organization_id=org_id,
    )
    db.session.commit()
    return project


def _html(response):
    return response.data.decode("utf-8")


def test_project_location_one_to_one(app):
    project = _make_existing_project()
    first = ProjectLocation(
        project_id=project.id,
        organization_id=project.organization_id,
        street="1 One Street",
        municipality="Ottawa",
        province_state="Ontario",
        country="Canada",
    )
    db.session.add(first)
    db.session.commit()
    with pytest.raises(IntegrityError):
        db.session.add(
            ProjectLocation(
                project_id=project.id,
                organization_id=project.organization_id,
                street="2 Two Street",
                municipality="Ottawa",
                province_state="Ontario",
                country="Canada",
            )
        )
        db.session.commit()
    db.session.rollback()
    assert ProjectLocation.query.filter_by(project_id=project.id).count() == 1
    assert project.location.id == first.id


def test_existing_project_address_preserved_and_not_parsed(app):
    project = _make_existing_project(address="Unit 4, somewhere rural-ish")
    assert project.address == "Unit 4, somewhere rural-ish"
    assert project.location is None
    source = inspect.getsource(establish_project_location_and_profile)
    assert "project.address" not in source
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        "New dwelling",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    db.session.refresh(project)
    assert project.address == "Unit 4, somewhere rural-ish"
    assert project.location.street == "100 Test Civic Street"


def test_complete_ontario_civic_location_and_postal_optional(app):
    project = _make_existing_project()
    profile = establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        "New dwelling",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    assert project.location.completeness == LOCATION_COMPLETE
    assert profile.location_completeness == LOCATION_COMPLETE
    assert project.location.postal_zip is None
    assert profile.postal_zip_snapshot is None


def test_incomplete_location_valid(app):
    project = _make_existing_project()
    profile = establish_project_location_and_profile(
        project.id,
        {
            "street": None,
            "municipality": "Ottawa",
            "province_state": "Ontario",
            "country": "Canada",
        },
        "Renovation",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    assert project.location.completeness == LOCATION_INCOMPLETE
    assert profile.location_completeness == LOCATION_INCOMPLETE
    assert profile.jurisdiction_status == JURISDICTION_RESOLVED


def test_jurisdiction_resolves_ottawa_and_north_gower(app):
    ottawa = resolve_jurisdiction("Canada", "Ontario", "Ottawa")
    city = resolve_jurisdiction("Canada", "ON", "City of Ottawa")
    gower = resolve_jurisdiction("Canada", "Ontario", "North Gower")
    assert ottawa is not None
    assert ottawa.code == "CA-ON-OTTAWA"
    assert city.code == "CA-ON-OTTAWA"
    assert gower.code == "CA-ON-OTTAWA"
    assert gower.ahj_name == "City of Ottawa"


def test_unknown_municipality_unresolved_and_no_ottawa_fallback(app):
    assert resolve_jurisdiction("Canada", "Ontario", "Toronto") is None
    assert resolve_jurisdiction("Canada", "Ontario", "Kanata") is None
    assert resolve_jurisdiction("Canada", "Ontario", None) is None
    assert resolve_jurisdiction("Canada", "Ontario", "") is None
    project = _make_existing_project()
    profile = establish_project_location_and_profile(
        project.id,
        {
            "street": "10 King Street",
            "municipality": "Toronto",
            "province_state": "Ontario",
            "country": "Canada",
        },
        "Commercial",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    assert profile.jurisdiction_status == JURISDICTION_UNRESOLVED
    assert profile.resolved_jurisdiction_id is None
    assert profile.resolved_jurisdiction_name is None


def test_tax_jurisdiction_not_used(app, org_b):
    assert org_b.tax_jurisdiction == "City of Ottawa"
    result = resolve_jurisdiction(
        "Canada",
        "Ontario",
        "Toronto",
        tax_jurisdiction=org_b.tax_jurisdiction,
    )
    assert result is None
    assert resolve_jurisdiction(
        None, None, None, tax_jurisdiction="City of Ottawa"
    ) is None
    source = inspect.getsource(resolve_jurisdiction)
    assert "del tax_jurisdiction" in source


def test_permit_context_values_valid_and_do_not_mutate_commercial_type(app):
    assert "New dwelling" in PERMIT_CONTEXT_CLASSES
    assert "Additional dwelling/coach house" in PERMIT_CONTEXT_CLASSES
    assert DEFAULT_PERMIT_CONTEXT_CLASS == "Other/unspecified"
    project = _make_existing_project()
    commercial_type = project.current_commercial_context.project_type
    assert commercial_type == "Addition"
    with pytest.raises(PermitFoundationError):
        establish_project_location_and_profile(
            project.id,
            OTTAWA_LOCATION,
            "Not a permit context",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    db.session.rollback()
    profile = establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        "New dwelling",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    db.session.refresh(project)
    assert profile.permit_context_class == "New dwelling"
    assert project.current_commercial_context.project_type == commercial_type


def test_new_project_auto_creates_location_and_preliminary_profile(client, app):
    row = _make_client("Create Client")
    resp = client.post(
        "/projects/new",
        data={
            "name": "FG015 New Civic Project",
            "client_id": row.id,
            "status": "Lead",
            "address": "Keep this free text",
            "street": "100 Test Civic Street",
            "municipality": "Ottawa",
            "province_state": "Ontario",
            "country": "Canada",
            "permit_context_class": "New dwelling",
            **COMMERCIAL_CREATE,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    project = Project.query.filter_by(name="FG015 New Civic Project").first()
    assert project is not None
    assert project.address == "Keep this free text"
    assert project.location is not None
    assert project.location.completeness == LOCATION_COMPLETE
    profile = project.current_permit_profile
    assert profile is not None
    assert profile.kind == PERMIT_PROFILE_KIND_PRELIMINARY
    assert profile.jurisdiction_status == JURISDICTION_RESOLVED
    assert profile.advisory_status == PERMIT_ADVISORY_STATUS
    assert profile.generation_method == PERMIT_GENERATION_METHOD
    html = _html(resp)
    assert "complete" in html
    assert "resolved" in html
    assert "preliminary" in html
    assert "PRELIMINARY / FOUNDATION ONLY" in html


def test_incomplete_new_project_creates_unresolved_preliminary_profile(client, app):
    row = _make_client("Incomplete Client")
    resp = client.post(
        "/projects/new",
        data={
            "name": "FG015 Incomplete Project",
            "client_id": row.id,
            "status": "Lead",
            **COMMERCIAL_CREATE,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    project = Project.query.filter_by(name="FG015 Incomplete Project").first()
    assert project.location is not None
    assert project.location.completeness == LOCATION_INCOMPLETE
    profile = project.current_permit_profile
    assert profile is not None
    assert profile.location_completeness == LOCATION_INCOMPLETE
    assert profile.jurisdiction_status == JURISDICTION_UNRESOLVED
    assert profile.resolved_jurisdiction_id is None
    assert profile.permit_context_class == DEFAULT_PERMIT_CONTEXT_CLASS
    html = _html(resp)
    assert "incomplete" in html
    assert "unresolved" in html
    assert "preliminary" in html


def test_existing_project_not_automatically_backfilled_or_profiled(client, app):
    project = _make_existing_project()
    assert project.location is None
    assert project.current_permit_profile is None
    assert PermitProfile.query.filter_by(project_id=project.id).count() == 0
    resp = client.get(f"/projects/{project.id}")
    html = _html(resp)
    assert resp.status_code == 200
    assert "not generated" in html
    assert "incomplete" in html
    assert "unresolved" in html
    db.session.refresh(project)
    assert project.location is None
    assert project.current_permit_profile is None
    assert project.address == "99 Ambiguous Free Text Road"


def test_profile_is_explicitly_preliminary_and_has_no_pass_or_zoning(app):
    project = _make_existing_project()
    profile = establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        "Garage/accessory",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    assert profile.is_preliminary
    assert profile.advisory_status == "PRELIMINARY_FOUNDATION_ONLY"
    assert profile.plan_site_review_status == PLAN_SITE_REVIEW_NOT_PERFORMED
    assert profile.substantive_analysis_status == SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE
    assert "findings" not in PermitProfile.__table__.columns
    assert "zoning_status" not in PermitProfile.__table__.columns
    assert "pass" not in profile.advisory_status.lower()
    assert profile.kind != "PASS"


def test_snapshot_preserves_location_and_edits_do_not_rewrite_old_profile(app):
    project = _make_existing_project()
    first = establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        "Renovation",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    first_id = first.id
    first_street = first.street_snapshot
    first_context = first.permit_context_class
    second = establish_project_location_and_profile(
        project.id,
        {
            **OTTAWA_LOCATION,
            "street": "200 Changed Civic Street",
        },
        "Renovation",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    old = PermitProfile.query.get(first_id)
    assert old.street_snapshot == first_street == "100 Test Civic Street"
    assert old.is_current is False
    assert old.is_stale is True
    assert old.recheck_required is True
    assert second.id != first_id
    assert second.version_number == 2
    assert second.is_current is True
    assert second.street_snapshot == "200 Changed Civic Street"
    third = establish_project_location_and_profile(
        project.id,
        {
            **OTTAWA_LOCATION,
            "street": "200 Changed Civic Street",
        },
        "Addition",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    old_second = PermitProfile.query.get(second.id)
    assert old_second.permit_context_class == first_context
    assert old_second.street_snapshot == "200 Changed Civic Street"
    assert old_second.is_current is False
    assert old_second.is_stale is True
    assert old_second.recheck_required is True
    assert third.version_number == 3
    assert third.permit_context_class == "Addition"
    assert third.is_stale is False


def test_project_hub_displays_foundation_states_and_no_substantive_findings(
    client, app
):
    existing = _make_existing_project(name="Hub Existing")
    html = _html(client.get(f"/projects/{existing.id}"))
    assert "Permit &amp; Approvals" in html or "Permit & Approvals" in html
    assert "PRELIMINARY / FOUNDATION ONLY" in html
    assert "not generated" in html
    assert "not performed" in html
    assert "not available" in html
    assert ">PASS<" not in html
    state = assemble_permit_foundation_state(existing)
    assert state["profile_state"] == "not generated"
    assert state["plan_site_analysis"] == PLAN_SITE_REVIEW_NOT_PERFORMED
    assert state["substantive_report"] == SUBSTANTIVE_ANALYSIS_NOT_AVAILABLE

    row = _make_client("Hub New Client")
    created = client.post(
        "/projects/new",
        data={
            "name": "Hub Preliminary Project",
            "client_id": row.id,
            "status": "Lead",
            "street": "100 Test Civic Street",
            "municipality": "North Gower",
            "province_state": "Ontario",
            "country": "Canada",
            "permit_context_class": "Additional dwelling/coach house",
            **COMMERCIAL_CREATE,
        },
        follow_redirects=True,
    )
    html = _html(created)
    assert "complete" in html
    assert "resolved" in html
    assert "preliminary" in html
    assert "not performed" in html
    assert "not available" in html
    assert ">PASS<" not in html
    project = Project.query.filter_by(name="Hub Preliminary Project").first()
    hub = assemble_project_hub(project, DEFAULT_ORGANIZATION_ID)
    assert hub["permit_foundation"]["profile"].resolved_jurisdiction_code == (
        "CA-ON-OTTAWA"
    )


def test_fg015_establish_does_not_mutate_plans_estimates_or_create_pass2(app):
    from app.models.permit_intelligence import PermitAnalysis, ProjectPermitFact

    project = _make_existing_project()
    plan_count = PlanDocument.query.count()
    takeoff_count = TakeoffPackage.query.count()
    estimate_count = Estimate.query.count()
    fact_count = ProjectPermitFact.query.count()
    analysis_count = PermitAnalysis.query.count()
    establish_project_location_and_profile(
        project.id,
        OTTAWA_LOCATION,
        "New dwelling",
        organization_id=DEFAULT_ORGANIZATION_ID,
        commit=True,
    )
    assert PlanDocument.query.count() == plan_count
    assert TakeoffPackage.query.count() == takeoff_count
    assert Estimate.query.count() == estimate_count
    assert ProjectPermitFact.query.count() == fact_count
    assert PermitAnalysis.query.count() == analysis_count
    names = set(sa.inspect(db.engine).get_table_names())
    assert "permit_rule_library" not in names
    assert "zoning_rules" not in names
    assert not hasattr(JurisdictionDefinition, "setback")
    from app import models as models_pkg

    assert not hasattr(models_pkg, "ZoningRule")


def test_cross_org_profile_read_and_location_edit_fail_closed(client, app, org_b):
    other = _make_existing_project(
        name="Apex Secret Project",
        org_id="ORG-002",
        client_name="Apex Client",
    )
    establish_project_location_and_profile(
        other.id,
        OTTAWA_LOCATION,
        "Commercial",
        organization_id="ORG-002",
        commit=True,
    )
    assert client.get(f"/projects/{other.id}").status_code == 404
    assert client.get(f"/projects/{other.id}/location/edit").status_code == 404
    posted = client.post(
        f"/projects/{other.id}/location/edit",
        data={
            "street": "Hacked Street",
            "municipality": "Ottawa",
            "province_state": "Ontario",
            "country": "Canada",
            "permit_context_class": "New dwelling",
        },
    )
    assert posted.status_code == 404
    with pytest.raises(PermitFoundationError):
        establish_project_location_and_profile(
            other.id,
            {"street": "Hacked Street"},
            "New dwelling",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
    db.session.rollback()
    db.session.refresh(other)
    assert other.location.street == "100 Test Civic Street"
    assert other.current_permit_profile.permit_context_class == "Commercial"


def test_platform_jurisdiction_definitions_not_org_mutable(client, app):
    assert assert_platform_jurisdiction_not_org_mutable()
    ottawa = JurisdictionDefinition.query.filter_by(code="CA-ON-OTTAWA").one()
    original = ottawa.name
    count = JurisdictionDefinition.query.count()
    alias_count = JurisdictionAlias.query.count()
    assert client.get("/jurisdiction-definitions").status_code == 404
    assert client.post(
        "/jurisdiction-definitions",
        data={"name": "Hacked AHJ", "code": "HACK"},
    ).status_code == 404
    endpoints = {rule.endpoint for rule in client.application.url_map.iter_rules()}
    assert not any("jurisdiction" in endpoint for endpoint in endpoints)
    project = _make_existing_project()
    client.post(
        f"/projects/{project.id}/location/edit",
        data={
            "street": "100 Test Civic Street",
            "municipality": "Ottawa",
            "province_state": "Ontario",
            "country": "Canada",
            "permit_context_class": "New dwelling",
        },
        follow_redirects=True,
    )
    db.session.refresh(ottawa)
    assert ottawa.name == original
    assert JurisdictionDefinition.query.count() == count
    assert JurisdictionAlias.query.count() == alias_count


def test_no_external_lookup_path_and_no_pratt_seed(app):
    jurisdiction_src = inspect.getsource(
        inspect.getmodule(resolve_jurisdiction)
    )
    foundation_src = inspect.getsource(
        inspect.getmodule(establish_project_location_and_profile)
    )
    combined = jurisdiction_src + foundation_src
    assert "import requests" not in combined
    assert "urllib.request" not in combined
    assert "httpx" not in combined
    assert "openai" not in combined
    assert "anthropic" not in combined
    blob = str(JURISDICTION_SEED) + str(JURISDICTION_ALIAS_SEED)
    assert "Pratt" not in blob
    assert "2562" not in blob
    assert "Church Street" not in blob
    assert "Mike" not in blob
    assert Project.query.filter(Project.name.ilike("%pratt%")).count() == 0
    assert Project.query.filter(Project.address.ilike("%2562%")).count() == 0


def test_alembic_fg015_upgrade_seed_and_downgrade(tmp_path):
    db_path = tmp_path / "fg015_migration.db"
    db_uri = f"sqlite:///{db_path}"
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        cfg_path = (
            "migrations/alembic.ini"
            if os.path.exists("migrations/alembic.ini")
            else "alembic.ini"
        )
        alembic_cfg = Config(cfg_path)
        alembic_cfg.set_main_option("script_location", "migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", db_uri)

        command.upgrade(alembic_cfg, "d6e7f8a9b0c1")
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO clients ("
                    "organization_id, name, created_at"
                    ") VALUES ("
                    "'ORG-001', 'Legacy Location Client', '2026-01-01 00:00:00')"
                )
            )
            client_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO projects ("
                    "organization_id, name, project_number, address, status, "
                    "client_id, created_at"
                    ") VALUES ("
                    "'ORG-001', 'Legacy Address Project', 'LEG-ADDR-001', "
                    "'99 Ambiguous Free Text Road', 'Lead', :client_id, "
                    "'2026-01-01 00:00:00')"
                ),
                {"client_id": client_id},
            )

        command.upgrade(alembic_cfg, "e7f8a9b0c1d2")
        with engine.begin() as conn:
            defs = conn.execute(
                sa.text("SELECT code, name FROM jurisdiction_definitions ORDER BY code")
            ).fetchall()
            assert [row[0] for row in defs] == ["CA", "CA-ON", "CA-ON-OTTAWA"]
            aliases = conn.execute(
                sa.text("SELECT alias FROM jurisdiction_aliases")
            ).fetchall()
            alias_names = {row[0] for row in aliases}
            assert {"Ottawa", "City of Ottawa", "North Gower"} <= alias_names
            assert "Pratt" not in alias_names
            address = conn.execute(
                sa.text("SELECT address FROM projects WHERE project_number = 'LEG-ADDR-001'")
            ).scalar()
            assert address == "99 Ambiguous Free Text Road"
            assert conn.execute(sa.text("SELECT COUNT(*) FROM project_locations")).scalar() == 0
            assert conn.execute(sa.text("SELECT COUNT(*) FROM permit_profiles")).scalar() == 0
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["e7f8a9b0c1d2"]

        command.downgrade(alembic_cfg, "d6e7f8a9b0c1")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "project_locations" not in tables
            assert "permit_profiles" not in tables
            assert "jurisdiction_definitions" not in tables
            assert "jurisdiction_aliases" not in tables
            leftover = conn.execute(
                sa.text(
                    "SELECT address FROM projects WHERE project_number = 'LEG-ADDR-001'"
                )
            ).scalar()
            assert leftover == "99 Ambiguous Free Text Road"
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d6e7f8a9b0c1"]
