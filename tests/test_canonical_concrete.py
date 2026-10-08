"""One supplier-neutral concrete identity for every concrete volume.

The 10 ft by 10 ft by 12 in slab is the proof quantity. The identity is
not a slab, an ICF wall, a footing, or a supplier product.
"""

import os
from datetime import datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models import Client, CostItem, Project
from app.models.canonical_material import (
    CANONICAL_MATERIAL_SEED,
    CONCRETE_CANONICAL_CODE,
    FORBIDDEN_CANONICAL_IDENTITY_FIELDS,
    CanonicalMaterial,
)
from app.models.estimate_costing import SOURCE_APPROVED_CONTRACTOR_COST
from app.models.material_requirement import (
    MATERIAL_REQUIREMENT_UOMS,
    MaterialRequirement,
)
from app.services.construction_measurement import rectangular_prism_cubic_yards
from app.services.contractor_cost_approval import record_contractor_cost_approval
from app.services.estimate_builder import create_section
from app.services.estimate_costing import consume_approved_contractor_cost
from app.services.estimates import create_estimate
from app.services.estimating_handoff import (
    add_estimate_line_from_requirement,
    create_requirements_from_project,
    supplier_request_from_project,
)
from app.services.estimating_quantity import estimate_project
from app.services.labour_engine import ensure_org_001_direct_labour_cost_rate_standard
from app.services.material_catalogue import (
    ensure_canonical_material_seed,
    get_canonical_material_by_code,
)
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.supplier_catalogue import (
    approve_canonical_material_supplier_map,
    create_contractor_supplier_account,
    create_supplier,
    create_supplier_location,
    create_supplier_product,
    record_price_evidence,
)
from app.services.unit_conversion import convert, three_decimal_display
from tests.scope_delivery_support import ensure_confirmed_scope_routing

ACTOR = "Joel Brayman"
HEAD = "s9f0a1b2c3d4"
PRIOR = "r8e9f0a1b2c3"


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
        ensure_org_001_direct_labour_cost_rate_standard()
        yield application
        db.session.remove()
        db.drop_all()


def _plan():
    return {
        "project_id": "scratch-concrete-identity",
        "foundation_elements": [
            {
                "id": "slab-a",
                "kind": "concrete_slab",
                "length_ft": "10",
                "width_ft": "10",
                "thickness_in": "12",
            },
            {
                "id": "wall-a",
                "kind": "icf_wall",
                "manufacturer_id": "logix",
                "net_wall_area_ft2": "100",
                "corner_90_count": 0,
                "corner_45_count": 0,
            },
        ],
    }


def _project(name):
    client = Client(name="{0} client".format(name), organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
    )
    db.session.add(project)
    db.session.commit()
    return project


def test_concrete_identity_is_one_supplier_neutral_material(app):
    rows = CanonicalMaterial.query.filter_by(code=CONCRETE_CANONICAL_CODE).all()
    assert len(rows) == 1
    material = rows[0]
    assert material.display_name == "Concrete"
    assert material.category == "CONCRETE"
    assert material.canonical_uom == "M3"
    assert material.kind == "GENERIC"
    assert material.manufacturer in (None, "")
    assert material.status == "ACTIVE"
    columns = set(CanonicalMaterial.__table__.columns.keys())
    assert set(FORBIDDEN_CANONICAL_IDENTITY_FIELDS).isdisjoint(columns)
    codes = {item["code"] for item in CANONICAL_MATERIAL_SEED}
    assert CONCRETE_CANONICAL_CODE not in codes
    assert "CAL-SLAB-CONCRETE" not in codes
    assert "CAL-ICF-CONCRETE" not in codes
    assert "CAL-FOOTING-CONCRETE" not in codes
    units = {item["canonical_uom"] for item in CANONICAL_MATERIAL_SEED}
    assert {"EA", "LF", "SF", "BF"}.issubset(units)
    assert MATERIAL_REQUIREMENT_UOMS[:4] == ("EA", "LF", "SF", "BF")
    assert "M3" in MATERIAL_REQUIREMENT_UOMS


def test_dimensioned_slab_and_icf_concrete_share_one_requirement_identity(app):
    measured = rectangular_prism_cubic_yards(10, 10, 12)
    purchasing = convert(measured["cubic_yards"], "YD3", "M3")
    from_rounded = convert(Decimal("3.704"), "YD3", "M3")
    assert purchasing["quantity"] != from_rounded["quantity"]
    result = estimate_project(_plan())
    slab = next(line for line in result["lines"] if line["element"] == "concrete_slab")
    icf = next(line for line in result["lines"] if line["element"] == "concrete")
    assert slab["unit"] == "YD3"
    assert slab["quantity"] == measured["cubic_yards"]
    assert slab["purchasing_unit"] == "M3"
    assert slab["purchasing_quantity"] == purchasing["quantity"]
    assert slab["canonical_material_code"] == CONCRETE_CANONICAL_CODE
    assert slab["truck_count"] is None
    assert slab["waste"] is None
    assert icf["canonical_material_code"] == CONCRETE_CANONICAL_CODE
    assert icf["unit"] == "YD3"
    assert icf["purchasing_unit"] == "M3"
    project = _project("CONC-ID")
    first = create_requirements_from_project(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    second = create_requirements_from_project(
        project_id=project.id,
        result=result,
        actor=ACTOR,
        organization_id=DEFAULT_ORGANIZATION_ID,
    )
    assert len(second["created"]) == 0
    concrete_rows = [
        row for row in first["created"] if row.canonical_material.code == CONCRETE_CANONICAL_CODE
    ]
    assert len(concrete_rows) == 2
    assert len({row.canonical_material_id for row in concrete_rows}) == 1
    slab_requirement = next(row for row in concrete_rows if "concrete_slab" in row.note)
    stored = purchasing["quantity"].quantize(Decimal("0.0001"))
    assert stored == Decimal("2.8317")
    assert slab_requirement.quantity == stored
    assert slab_requirement.canonical_uom == "M3"
    assert slab_requirement.canonical_material.display_name == "Concrete"
    assert str(measured["cubic_yards"]) in slab_requirement.note
    assert "YD3" in slab_requirement.note
    assert str(purchasing["quantity"]) in slab_requirement.note
    note = slab_requirement.note.lower()
    assert "supplier" not in note
    assert "sku" not in note
    assert "price" not in note
    request = supplier_request_from_project(
        result,
        project_name="Synthetic slab",
        project_address="1 Scratch Lane",
        supplier_name="Yard",
        issued_on="2026-10-08",
    )
    slab_row = next(row for row in request["rows"] if "Concrete slab" in row["item"])
    assert slab_row["qty"] == "2.832"
    assert slab_row["unit"] == "m³"
    assert three_decimal_display(measured["cubic_yards"]) in slab_row["note"]
    assert "yd³" in slab_row["note"]
    assert request["response_fields"] == (
        "product",
        "sku",
        "availability",
        "price",
        "substitutions_or_exceptions",
    )
    material = get_canonical_material_by_code(CONCRETE_CANONICAL_CODE)
    supplier = create_supplier(code="YARD-CONC-ID", legal_name="Yard Concrete", demo_synthetic=True)
    location = create_supplier_location(
        supplier_id=supplier.id,
        code="YARD-C1",
        display_name="Yard Concrete plant",
        demo_synthetic=True,
    )
    account = create_contractor_supplier_account(
        organization_id=DEFAULT_ORGANIZATION_ID,
        supplier_id=supplier.id,
        supplier_location_id=location.id,
        demo_synthetic=True,
    )
    product = create_supplier_product(
        supplier_id=supplier.id,
        sku="YARD-CONC-M3",
        description="Synthetic concrete",
        sales_uom="m³",
        pack_qty=Decimal("1"),
        demo_synthetic=True,
    )
    assert product.sku != material.code
    approve_canonical_material_supplier_map(
        canonical_material_id=material.id,
        supplier_product_id=product.id,
        actor_display_name=ACTOR,
        demo_synthetic=True,
    )
    record_price_evidence(
        supplier_product_id=product.id,
        amount=Decimal("200.00"),
        currency="CAD",
        unit="m³",
        price_class="CONTRACTOR_CONFIRMED_PRICE",
        actor_display_name=ACTOR,
        contractor_supplier_account_id=account.id,
        source="MANUAL",
        demo_synthetic=True,
        effective_from=datetime(2026, 10, 1),
        effective_to=None,
    )
    approval = record_contractor_cost_approval(
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        contractor_supplier_account_id=account.id,
        as_of=datetime(2026, 10, 8),
        approved_by=ACTOR,
        status="APPROVED",
    )
    assert approval.unit == "m³"
    estimate = create_estimate(
        project_id=project.id,
        estimate_number="EST-CONC-ID",
        title="Synthetic concrete",
    )
    version = estimate.current_version
    section = create_section(version, name="Concrete")
    cost_item = CostItem(
        code="MAT-CONC-ID",
        name="Concrete",
        category="Material",
        unit="m³",
        unit_cost=Decimal("1.00"),
        default_markup_percent=Decimal("0"),
        organization_id=DEFAULT_ORGANIZATION_ID,
        canonical_material_id=material.id,
        is_active=True,
    )
    db.session.add(cost_item)
    db.session.commit()
    line = add_estimate_line_from_requirement(section, slab_requirement, cost_item_id=cost_item.id)
    assert line.quantity == stored
    assert line.waste_percent == 0
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    snapshot = consume_approved_contractor_cost(
        version,
        estimate_line_item_id=line.id,
        contractor_cost_approval_id=approval.id,
        actor=ACTOR,
    )
    frozen = snapshot.lines[0]
    assert line.costing_source_kind == SOURCE_APPROVED_CONTRACTOR_COST
    assert frozen.quantity == stored
    assert frozen.unit_cost == Decimal("200.00")
    assert frozen.contractor_cost_approval_id == approval.id
    assert MaterialRequirement.query.filter_by(project_id=project.id).count() == len(first["created"])


def test_concrete_identity_migration_inserts_one_row(tmp_path):
    db_path = tmp_path / "concrete_identity.db"
    db_uri = "sqlite:///{0}".format(db_path)
    assert "brayman_estimator.db" not in db_uri
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
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == [HEAD]
        command.upgrade(alembic_cfg, PRIOR)
        engine = db.engine
        with engine.begin() as conn:
            before = conn.execute(sa.text("SELECT COUNT(*) FROM canonical_materials")).scalar()
            missing = conn.execute(
                sa.text("SELECT 1 FROM canonical_materials WHERE code = :code"),
                {"code": CONCRETE_CANONICAL_CODE},
            ).fetchone()
            assert missing is None
            lumber = conn.execute(
                sa.text(
                    "SELECT canonical_uom FROM canonical_materials WHERE code = 'CAL-LUM-2X4-8'"
                )
            ).scalar()
            assert lumber == "EA"
        command.upgrade(alembic_cfg, HEAD)
        with engine.begin() as conn:
            after = conn.execute(sa.text("SELECT COUNT(*) FROM canonical_materials")).scalar()
            assert after == before + 1
            row = conn.execute(
                sa.text(
                    "SELECT display_name, category, canonical_uom, manufacturer "
                    "FROM canonical_materials WHERE code = :code"
                ),
                {"code": CONCRETE_CANONICAL_CODE},
            ).fetchone()
            assert row[0] == "Concrete"
            assert row[1] == "CONCRETE"
            assert row[2] == "M3"
            assert row[3] in (None, "")
        command.downgrade(alembic_cfg, PRIOR)
        with engine.begin() as conn:
            gone = conn.execute(
                sa.text("SELECT 1 FROM canonical_materials WHERE code = :code"),
                {"code": CONCRETE_CANONICAL_CODE},
            ).fetchone()
            assert gone is None
            still = conn.execute(sa.text("SELECT COUNT(*) FROM canonical_materials")).scalar()
            assert still == before
        command.upgrade(alembic_cfg, HEAD)
        with engine.begin() as conn:
            once = conn.execute(
                sa.text("SELECT COUNT(*) FROM canonical_materials WHERE code = :code"),
                {"code": CONCRETE_CANONICAL_CODE},
            ).scalar()
            assert once == 1
