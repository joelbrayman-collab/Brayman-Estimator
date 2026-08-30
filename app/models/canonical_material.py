"""CalibAi canonical material identity (FG-014 / ADR-034). Platform-shared; not org-owned."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import validates

from app import db


CANONICAL_MATERIAL_STATUSES = ("ACTIVE", "DISCONTINUED")
CANONICAL_MATERIAL_KINDS = ("GENERIC", "SPECIFIED")
CANONICAL_MATERIAL_UOMS = ("EA", "LF", "SF", "BF")
CANONICAL_MATERIAL_CATEGORIES = ("DIMENSIONAL_LUMBER", "SHEET_GOODS")
CANONICAL_MATERIAL_SUBSTITUTION_POLICIES = ("ALLOWED", "RESTRICTED", "PROHIBITED")

FORBIDDEN_CANONICAL_IDENTITY_FIELDS = (
    "organization_id",
    "unit_cost",
    "markup",
    "default_markup_percent",
    "supplier",
    "supplier_id",
    "sku",
    "supplier_sku",
    "list_price",
    "contractor_price",
    "promotional_price",
    "sale_price",
    "quote_price",
    "inventory",
    "branch",
    "availability",
    "retrieved_at",
    "supplier_feed",
    "waste_percent",
    "waste",
)


def _seed_row(
    *,
    code,
    display_name,
    kind,
    category,
    trade,
    canonical_uom,
    substitution_policy,
    description,
    status="ACTIVE",
    nominal_thickness_in=None,
    nominal_width_in=None,
    length_ft=None,
    sheet_width_in=None,
    sheet_length_in=None,
    grade_species=None,
    performance_class=None,
    manufacturer=None,
    specification_text=None,
):
    return {
        "code": code,
        "display_name": display_name,
        "status": status,
        "kind": kind,
        "category": category,
        "trade": trade,
        "canonical_uom": canonical_uom,
        "nominal_thickness_in": nominal_thickness_in,
        "nominal_width_in": nominal_width_in,
        "length_ft": length_ft,
        "sheet_width_in": sheet_width_in,
        "sheet_length_in": sheet_length_in,
        "grade_species": grade_species,
        "performance_class": performance_class,
        "manufacturer": manufacturer,
        "specification_text": specification_text,
        "substitution_policy": substitution_policy,
        "description": description,
    }


# Platform-owned V1 vocabulary. Tens of rows. Not ORG-001. Not BMR/SKU/price.
CANONICAL_MATERIAL_SEED = (
    _seed_row(
        code="CAL-LUM-2X4-8",
        display_name="2×4 SPF No.2 or better — 8 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("4"),
        length_ft=Decimal("8"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×4, 8 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X4-10",
        display_name="2×4 SPF No.2 or better — 10 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("4"),
        length_ft=Decimal("10"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×4, 10 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X4-12",
        display_name="2×4 SPF No.2 or better — 12 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("4"),
        length_ft=Decimal("12"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×4, 12 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X4-16",
        display_name="2×4 SPF No.2 or better — 16 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("4"),
        length_ft=Decimal("16"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×4, 16 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X4-STUD-9258",
        display_name="2×4 SPF No.2 or better — 92-5/8 in stud",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("4"),
        grade_species="SPF No.2 or better",
        description="Generic pre-cut stud length. 2×4, 92-5/8 in.",
    ),
    _seed_row(
        code="CAL-LUM-2X6-8",
        display_name="2×6 SPF No.2 or better — 8 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("6"),
        length_ft=Decimal("8"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×6, 8 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X6-12",
        display_name="2×6 SPF No.2 or better — 12 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("6"),
        length_ft=Decimal("12"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×6, 12 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X6-16",
        display_name="2×6 SPF No.2 or better — 16 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("6"),
        length_ft=Decimal("16"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×6, 16 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X8-12",
        display_name="2×8 SPF No.2 or better — 12 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("8"),
        length_ft=Decimal("12"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×8, 12 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X8-16",
        display_name="2×8 SPF No.2 or better — 16 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("8"),
        length_ft=Decimal("16"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×8, 16 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X10-12",
        display_name="2×10 SPF No.2 or better — 12 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("10"),
        length_ft=Decimal("12"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×10, 12 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X10-16",
        display_name="2×10 SPF No.2 or better — 16 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("10"),
        length_ft=Decimal("16"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×10, 16 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X12-16",
        display_name="2×12 SPF No.2 or better — 16 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("12"),
        length_ft=Decimal("16"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 2×12, 16 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-4X4-8",
        display_name="4×4 SPF No.2 or better — 8 ft",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("4"),
        nominal_width_in=Decimal("4"),
        length_ft=Decimal("8"),
        grade_species="SPF No.2 or better",
        description="Generic dimensional lumber. 4×4, 8 ft length class.",
    ),
    _seed_row(
        code="CAL-LUM-2X4-LF",
        display_name="2×4 SPF No.2 or better — per linear foot",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="LF",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("4"),
        grade_species="SPF No.2 or better",
        description="Generic 2×4 requirement measured in linear feet. Not a pack or supplier sales UOM.",
    ),
    _seed_row(
        code="CAL-LUM-2X6-BF",
        display_name="2×6 SPF No.2 or better — per board foot",
        kind="GENERIC",
        category="DIMENSIONAL_LUMBER",
        trade="Framing",
        canonical_uom="BF",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("2"),
        nominal_width_in=Decimal("6"),
        grade_species="SPF No.2 or better",
        description="Generic 2×6 requirement measured in board feet. Not a pack or supplier sales UOM.",
    ),
    _seed_row(
        code="CAL-SHT-OSB-7-16-4X8",
        display_name="7/16 in OSB — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.4375"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        performance_class="OSB",
        description="Generic oriented strand board sheet. 7/16 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-OSB-19-32-4X8",
        display_name="19/32 in OSB — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.59375"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        performance_class="OSB",
        description="Generic oriented strand board sheet. 19/32 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-OSB-23-32-4X8",
        display_name="23/32 in OSB — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.71875"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        performance_class="OSB",
        description="Generic oriented strand board sheet. 23/32 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-OSB-7-16-4X9",
        display_name="7/16 in OSB — 4×9",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.4375"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("108"),
        performance_class="OSB",
        description="Generic oriented strand board sheet. 7/16 in, 48×108 in.",
    ),
    _seed_row(
        code="CAL-SHT-OSB-TNG-23-32-4X8",
        display_name="23/32 in T&G OSB — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.71875"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        performance_class="OSB T&G",
        description="Generic tongue-and-groove OSB floor/roof sheet. 23/32 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-PLY-CDX-1-2-4X8",
        display_name="1/2 in CDX plywood — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.5"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        grade_species="CDX",
        performance_class="Plywood",
        description="Generic CDX plywood sheet. 1/2 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-PLY-CDX-5-8-4X8",
        display_name="5/8 in CDX plywood — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.625"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        grade_species="CDX",
        performance_class="Plywood",
        description="Generic CDX plywood sheet. 5/8 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-PLY-CDX-3-4-4X8",
        display_name="3/4 in CDX plywood — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.75"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        grade_species="CDX",
        performance_class="Plywood",
        description="Generic CDX plywood sheet. 3/4 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-PLY-TNG-3-4-4X8",
        display_name="3/4 in T&G plywood — 4×8",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.75"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        performance_class="Plywood T&G",
        description="Generic tongue-and-groove plywood sheet. 3/4 in, 48×96 in.",
    ),
    _seed_row(
        code="CAL-SHT-OSB-7-16-SF",
        display_name="7/16 in OSB — per square foot",
        kind="GENERIC",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="SF",
        substitution_policy="ALLOWED",
        nominal_thickness_in=Decimal("0.4375"),
        performance_class="OSB",
        description="Generic 7/16 in OSB requirement measured in square feet. Not a pack or supplier sales UOM.",
    ),
    _seed_row(
        code="CAL-SHT-HUBER-ZIP-1-2-4X8",
        display_name="Huber ZIP System Sheathing — 1/2 in, 4×8",
        kind="SPECIFIED",
        category="SHEET_GOODS",
        trade="Sheathing",
        canonical_uom="EA",
        substitution_policy="PROHIBITED",
        nominal_thickness_in=Decimal("0.5"),
        sheet_width_in=Decimal("48"),
        sheet_length_in=Decimal("96"),
        performance_class="Structural sheathing with integrated water-resistive barrier",
        manufacturer="Huber Engineered Woods",
        specification_text="ZIP System Sheathing, 1/2 in, 48×96 in. Manufacturer/product identity. Not a dealer SKU.",
        description="Specified proprietary sheathing panel. Identity is the named product, not a supplier catalogue SKU.",
    ),
)


class CanonicalMaterial(db.Model):
    __tablename__ = "canonical_materials"
    __table_args__ = (
        db.UniqueConstraint("code", name="uq_canonical_materials_code"),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'DISCONTINUED')",
            name="ck_canonical_materials_status",
        ),
        db.CheckConstraint(
            "kind IN ('GENERIC', 'SPECIFIED')",
            name="ck_canonical_materials_kind",
        ),
        db.CheckConstraint(
            "canonical_uom IN ('EA', 'LF', 'SF', 'BF')",
            name="ck_canonical_materials_uom",
        ),
        db.CheckConstraint(
            "category IN ('DIMENSIONAL_LUMBER', 'SHEET_GOODS')",
            name="ck_canonical_materials_category",
        ),
        db.CheckConstraint(
            "substitution_policy IN ('ALLOWED', 'RESTRICTED', 'PROHIBITED')",
            name="ck_canonical_materials_substitution",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(220), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    kind = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    trade = db.Column(db.String(80), nullable=True)
    canonical_uom = db.Column(db.String(8), nullable=False)
    nominal_thickness_in = db.Column(db.Numeric(8, 4), nullable=True)
    nominal_width_in = db.Column(db.Numeric(8, 4), nullable=True)
    length_ft = db.Column(db.Numeric(8, 4), nullable=True)
    sheet_width_in = db.Column(db.Numeric(8, 4), nullable=True)
    sheet_length_in = db.Column(db.Numeric(8, 4), nullable=True)
    grade_species = db.Column(db.String(120), nullable=True)
    performance_class = db.Column(db.String(160), nullable=True)
    manufacturer = db.Column(db.String(160), nullable=True)
    specification_text = db.Column(db.Text, nullable=True)
    substitution_policy = db.Column(db.String(20), nullable=False, default="ALLOWED")
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    @validates("status")
    def _validate_status(self, key, value):
        if value not in CANONICAL_MATERIAL_STATUSES:
            raise ValueError("Canonical material status must be ACTIVE or DISCONTINUED.")
        return value

    @validates("kind")
    def _validate_kind(self, key, value):
        if value not in CANONICAL_MATERIAL_KINDS:
            raise ValueError("Canonical material kind must be GENERIC or SPECIFIED.")
        return value

    @validates("canonical_uom")
    def _validate_uom(self, key, value):
        if value not in CANONICAL_MATERIAL_UOMS:
            raise ValueError("Canonical UOM must be one of EA, LF, SF, BF.")
        return value

    @validates("category")
    def _validate_category(self, key, value):
        if value not in CANONICAL_MATERIAL_CATEGORIES:
            raise ValueError(
                "Canonical material category must be DIMENSIONAL_LUMBER or SHEET_GOODS."
            )
        return value

    @validates("substitution_policy")
    def _validate_substitution(self, key, value):
        if value not in CANONICAL_MATERIAL_SUBSTITUTION_POLICIES:
            raise ValueError("Invalid substitution policy.")
        return value

    @validates("code")
    def _validate_code(self, key, value):
        code = (value or "").strip()
        if not code:
            raise ValueError("Canonical material code is required.")
        return code

    def __repr__(self):
        return f"<CanonicalMaterial {self.code}>"
