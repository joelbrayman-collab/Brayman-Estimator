"""Tests for FG-014 Material Catalogue V1 — identity only."""

import inspect
import os
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Assembly, AssemblyItem, CanonicalMaterial, CostItem, Organization
from app.models.assembly import AssemblyItem as AssemblyItemModel
from app.models.canonical_material import (
    CANONICAL_MATERIAL_SEED,
    FORBIDDEN_CANONICAL_IDENTITY_FIELDS,
)
from app.plan_intelligence.models import TakeoffPackageItem
from app.services.material_catalogue import (
    MaterialCatalogueError,
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
    link_material_cost_item,
    list_canonical_materials,
    list_org_cost_items_for_material,
    set_cost_item_canonical_material,
    unlink_material_cost_item,
)
from app.services.organizations import (
    DEFAULT_ORGANIZATION_ID,
    ensure_default_organization,
    set_current_organization_id,
)


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
        ensure_canonical_material_seed()
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
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


def _cost_item(org_id=DEFAULT_ORGANIZATION_ID, category="Material", code="MAT-001", **kwargs):
    defaults = dict(
        organization_id=org_id,
        code=code,
        name="Test material",
        category=category,
        unit="ea",
        unit_cost=Decimal("10.00"),
        default_markup_percent=Decimal("0"),
        is_active=True,
    )
    defaults.update(kwargs)
    item = CostItem(**defaults)
    db.session.add(item)
    db.session.commit()
    return item


def test_canonical_material_model_and_platform_ownership(app):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    assert material is not None
    assert not hasattr(material, "organization_id") or "organization_id" not in material.__table__.c
    assert "organization_id" not in CanonicalMaterial.__table__.columns
    assert material.status == "ACTIVE"
    assert material.kind == "GENERIC"


def test_stable_code_unique(app):
    with pytest.raises(IntegrityError):
        db.session.add(
            CanonicalMaterial(
                code="CAL-LUM-2X6-12",
                display_name="Duplicate",
                status="ACTIVE",
                kind="GENERIC",
                category="DIMENSIONAL_LUMBER",
                canonical_uom="EA",
                substitution_policy="ALLOWED",
            )
        )
        db.session.commit()
    db.session.rollback()


def test_generic_and_specified_seed_rows(app):
    lumber = get_canonical_material_by_code("CAL-LUM-2X6-12")
    sheet = get_canonical_material_by_code("CAL-SHT-OSB-7-16-4X8")
    specified = get_canonical_material_by_code("CAL-SHT-HUBER-ZIP-1-2-4X8")
    assert lumber.kind == "GENERIC"
    assert lumber.category == "DIMENSIONAL_LUMBER"
    assert sheet.kind == "GENERIC"
    assert sheet.category == "SHEET_GOODS"
    assert specified.kind == "SPECIFIED"
    assert specified.manufacturer == "Huber Engineered Woods"
    assert specified.specification_text and "Not a dealer SKU" in specified.specification_text


def test_controlled_uom_accepts_vocabulary_and_rejects_invalid(app):
    codes = {row.canonical_uom for row in CanonicalMaterial.query.all()}
    assert {"EA", "LF", "SF", "BF"} <= codes
    with pytest.raises(ValueError):
        CanonicalMaterial(
            code="CAL-BAD-UOM",
            display_name="Bad",
            status="ACTIVE",
            kind="GENERIC",
            category="DIMENSIONAL_LUMBER",
            canonical_uom="BOX",
            substitution_policy="ALLOWED",
        )


def test_active_discontinued_validation(app):
    with pytest.raises(ValueError):
        CanonicalMaterial(
            code="CAL-BAD-STATUS",
            display_name="Bad",
            status="DELETED",
            kind="GENERIC",
            category="DIMENSIONAL_LUMBER",
            canonical_uom="EA",
            substitution_policy="ALLOWED",
        )
    row = CanonicalMaterial(
        code="CAL-TEST-DISC",
        display_name="Discontinued test",
        status="DISCONTINUED",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
    )
    db.session.add(row)
    db.session.commit()
    assert row.status == "DISCONTINUED"


def test_seed_catalogue_bounded_and_expected_kinds(app):
    rows = CanonicalMaterial.query.all()
    assert 10 <= len(rows) <= 80
    assert len(rows) == len(CANONICAL_MATERIAL_SEED)
    assert {r.code for r in rows} == {item["code"] for item in CANONICAL_MATERIAL_SEED}
    categories = {r.category for r in rows}
    assert categories == {"DIMENSIONAL_LUMBER", "SHEET_GOODS"}


def test_canonical_identity_has_no_commercial_or_supplier_fields(app):
    column_names = set(CanonicalMaterial.__table__.columns.keys())
    for forbidden in FORBIDDEN_CANONICAL_IDENTITY_FIELDS:
        assert forbidden not in column_names
    source = inspect.getsource(CanonicalMaterial)
    for token in (
        "unit_cost",
        "sku",
        "list_price",
        "promotional_price",
        "inventory",
        "waste_percent",
    ):
        assert token not in source


def test_existing_cost_item_valid_with_null_link(app):
    item = _cost_item()
    assert item.canonical_material_id is None
    assert CostItem.query.get(item.id) is not None


def test_material_cost_item_link_and_unlink(app):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    item = _cost_item()
    linked = link_material_cost_item(item.id, material.id)
    assert linked.canonical_material_id == material.id
    unlinked = unlink_material_cost_item(item.id)
    assert unlinked.canonical_material_id is None


@pytest.mark.parametrize(
    "category",
    ["Labour", "Equipment", "Subcontractor", "Allowance", "Other"],
)
def test_non_material_cost_item_link_fails(app, category):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    item = _cost_item(category=category, code=f"{category[:3].upper()}-001")
    with pytest.raises(MaterialCatalogueError, match="cannot link"):
        link_material_cost_item(item.id, material.id)
    db.session.refresh(item)
    assert item.canonical_material_id is None


def test_no_automatic_cost_item_backfill(app):
    item = _cost_item(name="2x6 SPF 12ft", supplier="Winchester")
    ensure_canonical_material_seed()
    db.session.refresh(item)
    assert item.canonical_material_id is None
    assert CostItem.query.filter(CostItem.canonical_material_id.isnot(None)).count() == 0


def test_no_historical_free_text_mapping_module(app):
    import app.services.material_catalogue as mc

    source = inspect.getsource(mc)
    assert "HistoricalCostLineItem" not in source
    assert "backfill" not in source.lower()


def test_current_org_sees_only_its_linked_cost_items(app, org_b, client):
    material = get_canonical_material_by_code("CAL-SHT-OSB-7-16-4X8")
    mine = _cost_item(code="MAT-ORG1")
    link_material_cost_item(mine.id, material.id)
    other = _cost_item(org_id="ORG-002", code="MAT-ORG2", name="Apex sheet")
    set_current_organization_id("ORG-002")
    link_material_cost_item(other.id, material.id, organization_id="ORG-002")
    set_current_organization_id(DEFAULT_ORGANIZATION_ID)

    visible = list_org_cost_items_for_material(material.id)
    assert {item.code for item in visible} == {"MAT-ORG1"}

    html = client.get(f"/material-catalogue/{material.id}").get_data(as_text=True)
    assert "MAT-ORG1" in html
    assert "MAT-ORG2" not in html
    assert "Apex sheet" not in html


def test_cross_org_cost_item_link_fails_closed(app, org_b):
    material = get_canonical_material_by_code("CAL-LUM-2X4-12")
    other = _cost_item(org_id="ORG-002", code="MAT-X")
    with pytest.raises(MaterialCatalogueError, match="not found in current organization"):
        link_material_cost_item(other.id, material.id)
    db.session.refresh(other)
    assert other.canonical_material_id is None


def test_platform_identity_shared_across_orgs(app, org_b, client):
    codes_org1 = {row.code for row in list_canonical_materials()}
    set_current_organization_id("ORG-002")
    codes_org2 = {row.code for row in list_canonical_materials()}
    set_current_organization_id(DEFAULT_ORGANIZATION_ID)
    assert codes_org1 == codes_org2
    html = client.get("/material-catalogue/").get_data(as_text=True)
    assert "CAL-LUM-2X6-12" in html
    assert "CAL-SHT-OSB-7-16-4X8" in html


def test_ordinary_org_ux_cannot_mutate_canonical_identity(app, client):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    html = client.get("/material-catalogue/").get_data(as_text=True)
    assert "New Canonical" not in html
    assert "Create canonical" not in html.lower()
    assert client.post(f"/material-catalogue/{material.id}/edit").status_code in (404, 405)
    assert client.post(f"/material-catalogue/{material.id}/delete").status_code in (404, 405)
    assert client.get("/material-catalogue/new").status_code == 404
    original = material.display_name
    material.display_name = original
    db.session.commit()
    html_detail = client.get(f"/material-catalogue/{material.id}").get_data(as_text=True)
    assert "cannot edit this definition" in html_detail


def test_search_and_category_and_status_filters(app, client):
    html = client.get("/material-catalogue/?q=2X6").get_data(as_text=True)
    assert "CAL-LUM-2X6-12" in html
    lumber = client.get(
        "/material-catalogue/?category=DIMENSIONAL_LUMBER"
    ).get_data(as_text=True)
    assert "CAL-LUM-2X6-12" in lumber
    assert "CAL-SHT-OSB-7-16-4X8" not in lumber
    sheets = client.get("/material-catalogue/?category=SHEET_GOODS").get_data(as_text=True)
    assert "CAL-SHT-OSB-7-16-4X8" in sheets
    assert "CAL-LUM-2X6-12" not in sheets

    disc = CanonicalMaterial(
        code="CAL-TEST-DISC-FILTER",
        display_name="Discontinued filter row",
        status="DISCONTINUED",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
    )
    db.session.add(disc)
    db.session.commit()
    active = client.get("/material-catalogue/?status=ACTIVE").get_data(as_text=True)
    discontinued = client.get("/material-catalogue/?status=DISCONTINUED").get_data(
        as_text=True
    )
    assert "CAL-TEST-DISC-FILTER" not in active
    assert "CAL-TEST-DISC-FILTER" in discontinued


def test_link_unlink_ux(app, client):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    item = _cost_item(code="MAT-LINK")
    resp = client.post(
        f"/material-catalogue/{material.id}/link",
        data={"cost_item_id": str(item.id)},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(item)
    assert item.canonical_material_id == material.id
    assert b"MAT-LINK" in resp.data
    html = resp.get_data(as_text=True)
    assert "Linked cost item" in html
    resp = client.post(
        f"/material-catalogue/{material.id}/unlink",
        data={"cost_item_id": str(item.id)},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(item)
    assert item.canonical_material_id is None
    assert "Unlinked cost item" in resp.get_data(as_text=True)


@pytest.mark.parametrize(
    "category",
    ["Labour", "Equipment", "Subcontractor", "Allowance", "Other"],
)
def test_catalogue_link_flash_uses_service_reason_for_non_material(app, client, category):
    """Office catalogue POST must flash the service reason, not the empty-select message."""
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    item = _cost_item(category=category, code=f"{category[:3].upper()}-FLASH")
    resp = client.post(
        f"/material-catalogue/{material.id}/link",
        data={"cost_item_id": str(item.id)},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert f"{category} cost items cannot link to a canonical material." in html
    assert "Select a Material cost item to link." not in html
    db.session.refresh(item)
    assert item.canonical_material_id is None


def test_catalogue_link_flash_uses_service_reason_for_cross_org(app, org_b, client):
    material = get_canonical_material_by_code("CAL-LUM-2X4-12")
    other = _cost_item(org_id="ORG-002", code="MAT-X-FLASH")
    resp = client.post(
        f"/material-catalogue/{material.id}/link",
        data={"cost_item_id": str(other.id)},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Cost item not found in current organization." in html
    assert "Select a Material cost item to link." not in html
    db.session.refresh(other)
    assert other.canonical_material_id is None


def test_catalogue_link_empty_selection_keeps_select_flash(app, client):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    resp = client.post(
        f"/material-catalogue/{material.id}/link",
        data={"cost_item_id": ""},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Select a Material cost item to link." in html


def test_new_link_rejects_discontinued_without_destroying_existing(app):
    disc = CanonicalMaterial(
        code="CAL-TEST-DISC-LINK",
        display_name="Discontinued lumber",
        status="DISCONTINUED",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
    )
    db.session.add(disc)
    db.session.commit()
    item = _cost_item(code="MAT-DISC")
    with pytest.raises(MaterialCatalogueError, match="ACTIVE"):
        link_material_cost_item(item.id, disc.id)

    active = get_canonical_material_by_code("CAL-LUM-2X4-8")
    link_material_cost_item(item.id, active.id)
    active.status = "DISCONTINUED"
    db.session.commit()
    db.session.refresh(item)
    assert item.canonical_material_id == active.id
    unlink_material_cost_item(item.id)
    assert item.canonical_material_id is None


def test_assembly_read_through_only_via_cost_item(app, client):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    item = _cost_item(code="MAT-ASM")
    link_material_cost_item(item.id, material.id)
    assembly = Assembly(
        organization_id=DEFAULT_ORGANIZATION_ID,
        code="ASM-001",
        name="Wall",
        category="Framing",
        unit="sf",
        default_markup_percent=Decimal("0"),
        is_active=True,
    )
    db.session.add(assembly)
    db.session.flush()
    component = AssemblyItem(
        assembly_id=assembly.id,
        cost_item_id=item.id,
        quantity=Decimal("1"),
        waste_percent=Decimal("10"),
        sort_order=1,
    )
    db.session.add(component)
    db.session.commit()
    assert not hasattr(component, "canonical_material_id")
    assert "canonical_material_id" not in AssemblyItemModel.__table__.columns
    html = client.get(f"/assemblies/{assembly.id}").get_data(as_text=True)
    assert "CAL-LUM-2X6-12" in html
    assert "10.00%" in html


def test_no_material_requirement_or_supplier_or_takeoff_fks(app):
    import app.models as models_pkg

    assert not hasattr(models_pkg, "MaterialRequirement")
    assert "class MaterialRequirement" not in Path(
        "app/models/canonical_material.py"
    ).read_text()
    assert not hasattr(models_pkg, "Supplier")
    assert not hasattr(models_pkg, "SupplierProduct")
    takeoff_cols = set(TakeoffPackageItem.__table__.columns.keys())
    assert "canonical_material_id" not in takeoff_cols
    assert "cost_item_id" not in takeoff_cols
    assert "sku" not in takeoff_cols
    assert "waste_percent" not in CanonicalMaterial.__table__.columns
    class_source = inspect.getsource(CanonicalMaterial)
    assert "unit_cost = " not in class_source
    assert "sku =" not in class_source


def test_cost_library_shows_canonical_code(app, client):
    material = get_canonical_material_by_code("CAL-LUM-2X6-12")
    item = _cost_item(code="MAT-LIB")
    link_material_cost_item(item.id, material.id)
    html = client.get("/cost-library/").get_data(as_text=True)
    assert "CAL-LUM-2X6-12" in html
    nav = client.get("/material-catalogue/").get_data(as_text=True)
    assert "Material Catalogue" in nav
    assert "does not show live supplier" in nav.lower()


def test_adr_008_remains_proposed():
    text = Path("docs/adr/ADR-008-supplier-price-snapshotting.md").read_text()
    assert "**Proposed**" in text
    assert "Accepted" not in text.split("Status")[1].split("\n")[0]


def test_alembic_fg014_upgrade_seed_and_downgrade(tmp_path):
    db_path = tmp_path / "fg014_migration.db"
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

        command.upgrade(alembic_cfg, "c5d6e7f8a9b0")
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO cost_items ("
                    "organization_id, code, name, category, unit, unit_cost, "
                    "default_markup_percent, is_active, created_at, updated_at"
                    ") VALUES ("
                    "'ORG-001', 'LEGACY-MAT', 'Legacy material', 'Material', 'ea', "
                    "12.50, 0, 1, '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
                )
            )

        command.upgrade(alembic_cfg, "d6e7f8a9b0c1")
        with engine.begin() as conn:
            count = conn.execute(
                sa.text("SELECT COUNT(*) FROM canonical_materials")
            ).scalar()
            assert count == len(CANONICAL_MATERIAL_SEED)
            lumber = conn.execute(
                sa.text(
                    "SELECT kind, category FROM canonical_materials "
                    "WHERE code = 'CAL-LUM-2X6-12'"
                )
            ).fetchone()
            assert lumber[0] == "GENERIC"
            specified = conn.execute(
                sa.text(
                    "SELECT kind, manufacturer FROM canonical_materials "
                    "WHERE code = 'CAL-SHT-HUBER-ZIP-1-2-4X8'"
                )
            ).fetchone()
            assert specified[0] == "SPECIFIED"
            legacy = conn.execute(
                sa.text(
                    "SELECT code, canonical_material_id FROM cost_items "
                    "WHERE code = 'LEGACY-MAT'"
                )
            ).fetchone()
            assert legacy[0] == "LEGACY-MAT"
            assert legacy[1] is None
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["d6e7f8a9b0c1"]

        command.downgrade(alembic_cfg, "c5d6e7f8a9b0")
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    sa.text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            assert "canonical_materials" not in tables
            cols = {
                row[1]
                for row in conn.execute(sa.text("PRAGMA table_info(cost_items)"))
            }
            assert "canonical_material_id" not in cols
            leftover = conn.execute(
                sa.text("SELECT code FROM cost_items WHERE code = 'LEGACY-MAT'")
            ).scalar()
            assert leftover == "LEGACY-MAT"
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == ["c5d6e7f8a9b0"]
