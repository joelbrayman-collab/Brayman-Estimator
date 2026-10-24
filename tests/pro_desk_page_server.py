"""Local Supplier PRO Desk for the browser checks and the timed demonstration (20 Oct 2026).

Temporary database, synthetic data only, clearly labelled: a synthetic store, a synthetic price file and
product matches the store would set up once. It never reads the hosted database and holds no real prices.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401  (models load before app.services)
from app.services.local_time import local_today  # noqa: E402  (the office's date, as the app uses)

STORE = ("pro.desk@example.invalid", "Synthetic-pro-desk-pass-1")
RIVAL = ("rival.store@example.invalid", "Synthetic-rival-pass-1")
TODAY = local_today()

PRICES = [  # sku, description, unit, price, discount, rule
    ("SYN-POST", "Laminated column 3-ply 2x6 (synthetic)", "EA", "62.00", "", ""),
    ("SYN-2416", "2x4x16 SPF (synthetic)", "EA", "9.25", "", ""),
    ("SYN-PT2816", "2x8x16 treated (synthetic)", "EA", "31.50", "", ""),
    ("SYN-PANEL", "Steel panel, cut to length (synthetic)", "LF", "4.10", "5", "Farm account 5% (synthetic)"),
    ("SYN-TRIM10", "Steel trim, 10 ft (synthetic)", "EA", "21.00", "", ""),
    ("SYN-OH1010", "Overhead door 10x10 (synthetic)", "EA", "1650.00", "", ""),
    ("SYN-MAN3068", "Steel man door 3068 (synthetic)", "EA", "425.00", "", ""),
    ("SYN-SCREW250", "Cladding screws, box of 250 (synthetic)", "BOX", "38.00", "", ""),
]
MATCHES = {  # takeoff line → (sku, selling units per takeoff unit)
    "CAL-OB-POST": ("SYN-POST", "1"), "CAL-OB-PURLIN-2X4-SPF": ("SYN-2416", "0.0625"),
    "CAL-OB-GIRT-2X4-SPF": ("SYN-2416", "0.0625"), "CAL-OB-SKIRT-2X8-PRESSURE-TREATED": ("SYN-PT2816", "0.0625"),
    "CAL-OB-ROOF-PANEL": ("SYN-PANEL", "1"), "CAL-OB-WALL-PANEL": ("SYN-PANEL", "1"),
    "CAL-OB-RIDGE-CAP": ("SYN-TRIM10", "0.1"), "CAL-OB-TRIM-EAVE": ("SYN-TRIM10", "0.1"),
    "CAL-OB-TRIM-RAKE": ("SYN-TRIM10", "0.1"), "CAL-OB-TRIM-CORNER": ("SYN-TRIM10", "0.1"),
    "CAL-OB-TRIM-BASE": ("SYN-TRIM10", "0.1"), "CAL-OB-TRIM-OPENING": ("SYN-TRIM10", "0.1"),
    "CAL-OB-DOOR-OH-120X120": ("SYN-OH1010", "1"), "CAL-OB-DOOR-MAN-36X80": ("SYN-MAN3068", "1"),
    "CAL-OB-CLADDING-SCREW": ("SYN-SCREW250", "0.004"),
}


def _user(email, password, name):
    from app.models.user import User
    from app.services.auth import hash_password

    user = User(email=email, display_name=name, password_hash=hash_password(password), is_active=True)
    db.session.add(user)
    db.session.commit()
    return user


def seed() -> dict:
    from app.models.supplier_portal import SupplierUserMembership
    from app.services import supplier_pro_desk as P
    from app.services.material_catalogue import ensure_canonical_material_seed
    from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
    from app.services.outbuilding import spec as S
    from app.services.outbuilding import takeoff as T
    from app.services.supplier_catalogue import create_supplier, create_supplier_location
    from tests.auth_fixtures import ensure_office_user

    ensure_default_organization()
    ensure_canonical_material_seed()
    ensure_office_user()
    supplier = create_supplier(code="SYN-STORE", legal_name="Synthetic Building Supply (demo)", demo_synthetic=True)
    location = create_supplier_location(supplier_id=supplier.id, code="WIN", display_name="Synthetic store, Winchester",
                                        demo_synthetic=True)
    rival = create_supplier(code="SYN-RIVAL", legal_name="Rival Synthetic Supply", demo_synthetic=True)
    create_supplier_location(supplier_id=rival.id, code="MAIN", display_name="Rival main", demo_synthetic=True)
    store_user = _user(*STORE, "Dana Synthetic")
    rival_user = _user(*RIVAL, "Rival Synthetic")
    for user, sup in ((store_user, supplier), (rival_user, rival)):
        db.session.add(SupplierUserMembership(user_id=user.id, supplier_id=sup.id, status="ACTIVE",
                                              created_by_name="Synthetic setup", created_by_organization_id=DEFAULT_ORGANIZATION_ID))
    db.session.commit()
    P.save_settings(supplier, {"tax_label": "HST", "tax_rate_percent": "13", "validity_days": "30",
                               "default_delivery_charge": "150",
                               "contact_line": "613-555-0199 · prodesk@example.invalid (synthetic)",
                               "terms_text": "Synthetic demonstration terms. Prices are not real store prices."}, user=store_user)
    import csv

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["sku", "description", "unit", "price", "discount_percent", "discount_rule", "effective_from", "availability"])
    for sku, desc, unit, price, disc, rule in PRICES:
        writer.writerow([sku, desc, unit, price, disc, rule, (TODAY - timedelta(days=3)).isoformat(), "IN_STOCK"])
    record = P.import_price_file(supplier, filename="synthetic-prices.csv", content=buf.getvalue().encode(),
                        authorized_by="Synthetic store manager (demo)", user=store_user, demo_synthetic=True)
    assert record.rows_rejected == 0, record.rejections_json
    # The one-time product matches a store makes; quotations then reuse them.
    from app.models.supplier_catalogue import SupplierProduct

    reference = T.takeoff(S.read_answers(REFERENCE_FORM)[0])
    lines = {l["code"]: l for l in reference["lines"]}
    for code, (sku, factor) in MATCHES.items():
        product = SupplierProduct.query.filter_by(supplier_id=supplier.id, sku=sku).one()
        P.match_product(supplier, lines[code], product_id=product.id, sales_per_unit=factor, user=store_user)
    standard, errors = P.save_assembly(supplier, {"name": "Post-frame steel, 8 ft bays (synthetic)",
                                                  "basis": "Synthetic demonstration standard, not a real store's",
                                                  **{k: REFERENCE_FORM[k] for k in S.ASSEMBLY_KEYS}},
                                       user=store_user, demo_synthetic=True)
    assert not errors, errors
    return {"supplier_id": supplier.id, "rival_id": rival.id, "store": list(STORE), "rival": list(RIVAL),
            "standard_id": standard.id}


REFERENCE_FORM = {
    "building_system": "POST_FRAME_STEEL", "width_ft": "30", "length_ft": "40", "wall_height_ft": "12",
    "roof_type": "GABLE", "roof_pitch": "4", "eave_overhang_in": "12", "gable_overhang_in": "12",
    "post_spacing_ft": "8", "endwall_post_spacing_ft": "10", "post_description": "3-ply 2×6 laminated column, treated",
    "truss_spacing_ft": "8", "purlin_spacing_in": "24", "purlin_lumber": "2×4 SPF", "girt_spacing_in": "24",
    "girt_lumber": "2×4 SPF", "skirt_lumber": "2×8 pressure-treated", "roof_panel_coverage_in": "36",
    "wall_panel_coverage_in": "36", "screws_per_sqft": "0.8", "foundation": "NONE",
    "opening_0_kind": "OVERHEAD_DOOR", "opening_0_wall": "LEFT", "opening_0_width_in": "120", "opening_0_height_in": "120",
    "opening_0_offset_ft": "10", "opening_1_kind": "MAN_DOOR", "opening_1_wall": "FRONT", "opening_1_width_in": "36",
    "opening_1_height_in": "80", "opening_1_offset_ft": "4",
}


QUICK_FORM = {"width_ft": "30", "length_ft": "40", "wall_height_ft": "12", "roof_pitch": "4", "foundation": "NONE",
              "qd_0_kind": "OVERHEAD_DOOR", "qd_0_count": "1", "qd_0_width_in": "120", "qd_0_height_in": "120",
              "qd_0_wall": "LEFT", "qd_1_kind": "MAN_DOOR", "qd_1_count": "1", "qd_1_width_in": "36",
              "qd_1_height_in": "80", "qd_1_wall": "FRONT"}


def main():
    database = tempfile.NamedTemporaryFile(prefix="pro-desk-", suffix=".db", delete=False)
    database.close()
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.name}",
                              "SECRET_KEY": "test-secret-key", "TRANSACTIONAL_EMAIL_PROVIDER": "local"})
    with application.app_context():
        db.create_all()
        facts = seed()
    facts["reference"] = REFERENCE_FORM
    facts["quick"] = QUICK_FORM
    port = int(os.environ["PRO_DESK_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
