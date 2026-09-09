"""Supplier Catalogue V1 models (FG-029 / ADR-046).

Supplier-specific identity, mapping, living evidence, and frozen Supplier Package.
Does not own CanonicalMaterial or MaterialRequirement.
"""

from datetime import datetime

from sqlalchemy import Index, text
from sqlalchemy.orm import validates

from app import db


SUPPLIER_STATUSES = ("ACTIVE", "INACTIVE")
SUPPLIER_PRODUCT_STATUSES = ("ACTIVE", "INACTIVE")
LIBRARY_MAP_STATUSES = ("ACTIVE", "INACTIVE")
MAPPING_STATUSES = ("UNRESOLVED", "REVIEW_REQUIRED", "MAPPED")
AVAILABILITY_STATUSES = ("IN_STOCK", "LIMITED", "UNKNOWN")
SUPPLIER_PACKAGE_STATUSES = ("DRAFT", "ISSUED")
PRICE_EVIDENCE_SOURCES = ("DEMO_SYNTHETIC", "MANUAL")
PACKAGE_EVIDENCE_SOURCES = ("DEMO_SYNTHETIC", "MANUAL")


class Supplier(db.Model):
    """Dealer organization. Not a CalibraytAI tenant. Not Brand Profile."""

    __tablename__ = "suppliers"
    __table_args__ = (
        db.UniqueConstraint("code", name="uq_suppliers_code"),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_suppliers_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), nullable=False)
    legal_name = db.Column(db.String(220), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    locations = db.relationship("SupplierLocation", back_populates="supplier")
    products = db.relationship("SupplierProduct", back_populates="supplier")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in SUPPLIER_STATUSES:
            raise ValueError("Supplier status must be ACTIVE or INACTIVE.")
        return value

    @validates("code")
    def _validate_code(self, key, value):
        code = (value or "").strip()
        if not code:
            raise ValueError("Supplier code is required.")
        return code

    def __repr__(self):
        return f"<Supplier {self.code}>"


class SupplierLocation(db.Model):
    """Supplier branch / yard."""

    __tablename__ = "supplier_locations"
    __table_args__ = (
        db.UniqueConstraint(
            "supplier_id",
            "code",
            name="uq_supplier_locations_supplier_code",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_supplier_locations_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    code = db.Column(db.String(80), nullable=False)
    display_name = db.Column(db.String(220), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    supplier = db.relationship("Supplier", back_populates="locations")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in SUPPLIER_STATUSES:
            raise ValueError("Supplier location status must be ACTIVE or INACTIVE.")
        return value

    def __repr__(self):
        return f"<SupplierLocation {self.code} supplier={self.supplier_id}>"


class ContractorSupplierAccount(db.Model):
    """Relationship A: contractor organization ↔ supplier location."""

    __tablename__ = "contractor_supplier_accounts"
    __table_args__ = (
        db.UniqueConstraint(
            "organization_id",
            "supplier_id",
            "supplier_location_id",
            name="uq_contractor_supplier_accounts_org_supplier_location",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_contractor_supplier_accounts_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_location_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    supplier = db.relationship("Supplier")
    supplier_location = db.relationship("SupplierLocation")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in SUPPLIER_STATUSES:
            raise ValueError("Contractor supplier account status must be ACTIVE or INACTIVE.")
        return value

    def __repr__(self):
        return (
            f"<ContractorSupplierAccount org={self.organization_id} "
            f"supplier={self.supplier_id}>"
        )


class SupplierProduct(db.Model):
    """Dealer SKU. Supplier-specific identity. Maps to CanonicalMaterial."""

    __tablename__ = "supplier_products"
    __table_args__ = (
        db.UniqueConstraint(
            "supplier_id",
            "sku",
            name="uq_supplier_products_supplier_sku",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_supplier_products_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sku = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(220), nullable=False)
    sales_uom = db.Column(db.String(20), nullable=False)
    pack_qty = db.Column(db.Numeric(12, 4), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    supplier = db.relationship("Supplier", back_populates="products")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in SUPPLIER_PRODUCT_STATUSES:
            raise ValueError("Supplier product status must be ACTIVE or INACTIVE.")
        return value

    @validates("sku")
    def _validate_sku(self, key, value):
        sku = (value or "").strip()
        if not sku:
            raise ValueError("Supplier SKU is required.")
        return sku

    def __repr__(self):
        return f"<SupplierProduct {self.sku} supplier={self.supplier_id}>"


class SupplierProductPriceEvidence(db.Model):
    """Living supplier price evidence. Inform only. Not EstimateLineItem cost."""

    __tablename__ = "supplier_product_price_evidence"

    id = db.Column(db.Integer, primary_key=True)
    supplier_product_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    contractor_supplier_account_id = db.Column(
        db.Integer,
        db.ForeignKey("contractor_supplier_accounts.id", ondelete="RESTRICT"),
        nullable=True,
    )
    amount = db.Column(db.Numeric(12, 4), nullable=False)
    currency = db.Column(db.String(8), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    effective_from = db.Column(db.DateTime, nullable=True)
    captured_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    source = db.Column(db.String(40), nullable=False)
    actor_display_name = db.Column(db.String(150), nullable=False)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    supplier_product = db.relationship("SupplierProduct")
    contractor_supplier_account = db.relationship("ContractorSupplierAccount")

    def __repr__(self):
        return f"<SupplierProductPriceEvidence {self.id} product={self.supplier_product_id}>"


class SupplierProductAvailabilityEvidence(db.Model):
    """Living availability evidence. Not live inventory."""

    __tablename__ = "supplier_product_availability_evidence"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('IN_STOCK', 'LIMITED', 'UNKNOWN')",
            name="ck_supplier_product_availability_evidence_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    supplier_product_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_location_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = db.Column(db.String(20), nullable=False)
    captured_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    source = db.Column(db.String(40), nullable=False)
    actor_display_name = db.Column(db.String(150), nullable=False)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    supplier_product = db.relationship("SupplierProduct")
    supplier_location = db.relationship("SupplierLocation")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in AVAILABILITY_STATUSES:
            raise ValueError("Availability status must be IN_STOCK, LIMITED, or UNKNOWN.")
        return value

    def __repr__(self):
        return (
            f"<SupplierProductAvailabilityEvidence {self.id} "
            f"product={self.supplier_product_id}>"
        )


class CanonicalMaterialSupplierMap(db.Model):
    """Library map CanonicalMaterial ↔ SupplierProduct. Human-reviewed."""

    __tablename__ = "canonical_material_supplier_maps"
    __table_args__ = (
        db.UniqueConstraint(
            "canonical_material_id",
            "supplier_product_id",
            name="uq_canonical_material_supplier_maps_identity_product",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_canonical_material_supplier_maps_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    canonical_material_id = db.Column(
        db.Integer,
        db.ForeignKey("canonical_materials.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_product_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    requirement_to_sales_factor = db.Column(db.Numeric(12, 6), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    approved_by_display_name = db.Column(db.String(150), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    canonical_material = db.relationship("CanonicalMaterial")
    supplier_product = db.relationship("SupplierProduct")

    @validates("status")
    def _validate_status(self, key, value):
        if value not in LIBRARY_MAP_STATUSES:
            raise ValueError("Library map status must be ACTIVE or INACTIVE.")
        return value

    def __repr__(self):
        return (
            f"<CanonicalMaterialSupplierMap material={self.canonical_material_id} "
            f"product={self.supplier_product_id}>"
        )


class SupplierRequirementMap(db.Model):
    """Project mapping of a MaterialRequirement to a supplier SKU."""

    __tablename__ = "supplier_requirement_maps"
    __table_args__ = (
        db.UniqueConstraint(
            "material_requirement_id",
            "supplier_id",
            "supplier_location_id",
            name="uq_supplier_requirement_maps_requirement_supplier_location",
        ),
        db.CheckConstraint(
            "mapping_status IN ('UNRESOLVED', 'REVIEW_REQUIRED', 'MAPPED')",
            name="ck_supplier_requirement_maps_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    material_requirement_id = db.Column(
        db.Integer,
        db.ForeignKey("material_requirements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_location_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_product_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_products.id", ondelete="RESTRICT"),
        nullable=True,
    )
    mapping_status = db.Column(db.String(20), nullable=False)
    actor_display_name = db.Column(db.String(150), nullable=False)
    mapped_at = db.Column(db.DateTime, nullable=True)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    material_requirement = db.relationship("MaterialRequirement")
    supplier = db.relationship("Supplier")
    supplier_location = db.relationship("SupplierLocation")
    supplier_product = db.relationship("SupplierProduct")

    @validates("mapping_status")
    def _validate_status(self, key, value):
        if value not in MAPPING_STATUSES:
            raise ValueError(
                "Mapping status must be UNRESOLVED, REVIEW_REQUIRED, or MAPPED."
            )
        return value

    def __repr__(self):
        return (
            f"<SupplierRequirementMap {self.id} req={self.material_requirement_id} "
            f"{self.mapping_status}>"
        )


class SupplierPackage(db.Model):
    """Frozen supplier-facing package header. ISSUED rows are immutable."""

    __tablename__ = "supplier_packages"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('DRAFT', 'ISSUED')",
            name="ck_supplier_packages_status",
        ),
        Index(
            "uq_supplier_packages_issued_project_supplier_location",
            "project_id",
            "supplier_id",
            "supplier_location_id",
            unique=True,
            sqlite_where=text("status = 'ISSUED'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.String(50),
        db.ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_location_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    contractor_supplier_account_id = db.Column(
        db.Integer,
        db.ForeignKey("contractor_supplier_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = db.Column(db.String(20), nullable=False, default="DRAFT")
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    issued_at = db.Column(db.DateTime, nullable=True)
    issued_by_display_name = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship("Organization")
    project = db.relationship("Project")
    supplier = db.relationship("Supplier")
    supplier_location = db.relationship("SupplierLocation")
    contractor_supplier_account = db.relationship("ContractorSupplierAccount")
    lines = db.relationship(
        "SupplierPackageLine",
        back_populates="supplier_package",
        order_by="SupplierPackageLine.id",
    )

    @validates("status")
    def _validate_status(self, key, value):
        if value not in SUPPLIER_PACKAGE_STATUSES:
            raise ValueError("Supplier package status must be DRAFT or ISSUED.")
        return value

    def __repr__(self):
        return f"<SupplierPackage {self.id} project={self.project_id} {self.status}>"


class SupplierPackageLine(db.Model):
    """Frozen supplier-facing line facts. Not live catalogue pointers."""

    __tablename__ = "supplier_package_lines"

    id = db.Column(db.Integer, primary_key=True)
    supplier_package_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_packages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    material_requirement_id = db.Column(db.Integer, nullable=False)
    canonical_material_code = db.Column(db.String(80), nullable=False)
    canonical_material_name = db.Column(db.String(220), nullable=False)
    requirement_qty = db.Column(db.Numeric(14, 4), nullable=False)
    requirement_uom = db.Column(db.String(8), nullable=False)
    mapping_status = db.Column(db.String(20), nullable=False)
    supplier_sku = db.Column(db.String(80), nullable=True)
    supplier_product_description = db.Column(db.String(220), nullable=True)
    sales_qty = db.Column(db.Numeric(14, 4), nullable=True)
    sales_uom = db.Column(db.String(20), nullable=True)
    price_amount = db.Column(db.Numeric(12, 4), nullable=True)
    price_currency = db.Column(db.String(8), nullable=True)
    price_captured_at = db.Column(db.DateTime, nullable=True)
    availability_status = db.Column(db.String(20), nullable=True)
    availability_captured_at = db.Column(db.DateTime, nullable=True)
    delivery_stage = db.Column(db.String(40), nullable=True)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    evidence_source = db.Column(db.String(40), nullable=False)

    supplier_package = db.relationship("SupplierPackage", back_populates="lines")

    def __repr__(self):
        return (
            f"<SupplierPackageLine {self.id} pkg={self.supplier_package_id} "
            f"{self.canonical_material_code}>"
        )
