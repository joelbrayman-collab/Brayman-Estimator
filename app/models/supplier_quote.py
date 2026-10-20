"""Supplier PRO Desk: a supplier's own walk-in customers and quotations (ADR-047 Amendment 1, 20 Oct 2026).

Every row here belongs to one supplier (``supplier_id``) and to no contractor organization. A supplier
quotation is materials only: it never creates a project, an estimate, a proposal or a contract.
"""

from datetime import datetime

from app import db

QUOTE_DRAFT = "DRAFT"
QUOTE_ISSUED = "ISSUED"
QUOTE_ACCEPTED = "ACCEPTED"
QUOTE_DECLINED = "DECLINED"
QUOTE_CANCELLED = "CANCELLED"
QUOTE_STATUSES = (QUOTE_DRAFT, QUOTE_ISSUED, QUOTE_ACCEPTED, QUOTE_DECLINED, QUOTE_CANCELLED)

ACCEPT_LINK = "CUSTOMER_LINK"
ACCEPT_IN_PERSON = "IN_PERSON"
ACCEPT_PHONE = "PHONE"
ACCEPT_EMAIL = "EMAIL"
ACCEPTANCE_METHODS = (ACCEPT_LINK, ACCEPT_IN_PERSON, ACCEPT_PHONE, ACCEPT_EMAIL)

PRICE_FILE_SOURCES = ("SUPPLIER_FILE", "DEMO_SYNTHETIC")


class SupplierCustomer(db.Model):
    """A supplier's own customer (a farmer at the counter). Not a contractor client, not a CalibraytAI user."""

    __tablename__ = "supplier_customers"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    display_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(254), nullable=True)
    address = db.Column(db.String(300), nullable=True)
    town = db.Column(db.String(120), nullable=True)
    # Consent the customer gave at the counter to be sent this quotation (CASL); recorded, not assumed.
    consent_email = db.Column(db.Boolean, nullable=False, default=False)
    consent_text = db.Column(db.Boolean, nullable=False, default=False)
    consent_recorded_by_name = db.Column(db.String(160), nullable=True)
    consent_recorded_at = db.Column(db.DateTime, nullable=True)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_by_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class SupplierQuote(db.Model):
    """One walk-in quotation: the confirmed building, its takeoff, its prices and its approval."""

    __tablename__ = "supplier_quotes"
    __table_args__ = (
        db.UniqueConstraint("supplier_id", "number", name="uq_supplier_quotes_supplier_number"),
        db.CheckConstraint(
            "status IN ('DRAFT', 'ISSUED', 'ACCEPTED', 'DECLINED', 'CANCELLED')", name="ck_supplier_quotes_status"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_location_id = db.Column(db.Integer, db.ForeignKey("supplier_locations.id", ondelete="RESTRICT"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("supplier_customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    number = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=QUOTE_DRAFT)
    building_system = db.Column(db.String(40), nullable=True)
    # The guided answers, each with who confirmed it (no default is ever assumed).
    spec_json = db.Column(db.JSON, nullable=True)
    # Product choices made at pricing: {line code: supplier_product_id}, plus substitutions.
    choices_json = db.Column(db.JSON, nullable=True)
    delivery_charge = db.Column(db.Numeric(12, 2), nullable=True)
    discount_percent = db.Column(db.Numeric(6, 3), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    # Frozen at issue: the drawing fingerprint, every line, price and source, and the totals.
    issued_json = db.Column(db.JSON, nullable=True)
    issued_sha256 = db.Column(db.String(64), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    issued_by_name = db.Column(db.String(160), nullable=True)
    valid_until = db.Column(db.Date, nullable=True)
    total = db.Column(db.Numeric(14, 2), nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    acceptance_method = db.Column(db.String(20), nullable=True)
    accepted_by_name = db.Column(db.String(160), nullable=True)
    acceptance_recorded_by_name = db.Column(db.String(160), nullable=True)
    accepted_sha256 = db.Column(db.String(64), nullable=True)
    order_ready_at = db.Column(db.DateTime, nullable=True)
    order_ready_by_name = db.Column(db.String(160), nullable=True)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_by_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    customer = db.relationship("SupplierCustomer")
    supplier = db.relationship("Supplier")
    location = db.relationship("SupplierLocation")


class SupplierQuoteFile(db.Model):
    """A sketch photo or PDF the customer brought, kept with the quote. Staff read it; nothing interprets it."""

    __tablename__ = "supplier_quote_files"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("supplier_quotes.id", ondelete="RESTRICT"), nullable=False, index=True)
    filename = db.Column(db.String(200), nullable=False)
    mime = db.Column(db.String(40), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    content = db.Column(db.LargeBinary, nullable=False)
    uploaded_by_name = db.Column(db.String(160), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    removed_at = db.Column(db.DateTime, nullable=True)


class SupplierQuoteEvent(db.Model):
    """Who did what to a quote and when, including every price and quantity change."""

    __tablename__ = "supplier_quote_events"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("supplier_quotes.id", ondelete="RESTRICT"), nullable=False, index=True)
    event_type = db.Column(db.String(40), nullable=False)
    actor_side = db.Column(db.String(20), nullable=False)  # SUPPLIER or CUSTOMER
    actor_name = db.Column(db.String(160), nullable=False)
    at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    detail_json = db.Column(db.JSON, nullable=True)


class SupplierQuoteLink(db.Model):
    """A customer's approval link: a lookup key and a hashed secret, like a proposal link."""

    __tablename__ = "supplier_quote_links"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("supplier_quotes.id", ondelete="RESTRICT"), nullable=False, index=True)
    lookup_key = db.Column(db.String(40), nullable=False, unique=True)
    secret_sha256 = db.Column(db.String(64), nullable=False)
    created_by_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    last_viewed_at = db.Column(db.DateTime, nullable=True)

    quote = db.relationship("SupplierQuote")


class SupplierPriceImport(db.Model):
    """One price file the supplier loaded: who, when, from what file, and who authorized it."""

    __tablename__ = "supplier_price_imports"
    __table_args__ = (
        db.CheckConstraint("source IN ('SUPPLIER_FILE', 'DEMO_SYNTHETIC')", name="ck_supplier_price_imports_source"),
    )

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_location_id = db.Column(db.Integer, db.ForeignKey("supplier_locations.id", ondelete="RESTRICT"), nullable=True)
    filename = db.Column(db.String(200), nullable=False)
    file_sha256 = db.Column(db.String(64), nullable=False)
    source = db.Column(db.String(20), nullable=False)
    authorized_by_name = db.Column(db.String(160), nullable=False)
    imported_by_name = db.Column(db.String(160), nullable=False)
    imported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rows_read = db.Column(db.Integer, nullable=False, default=0)
    rows_loaded = db.Column(db.Integer, nullable=False, default=0)
    rows_rejected = db.Column(db.Integer, nullable=False, default=0)
    rejections_json = db.Column(db.JSON, nullable=True)


class SupplierSellingPrice(db.Model):
    """A store selling price from the supplier's own file. Kept apart from contractor cost evidence (ADR-047 D9)."""

    __tablename__ = "supplier_selling_prices"

    id = db.Column(db.Integer, primary_key=True)
    supplier_product_id = db.Column(db.Integer, db.ForeignKey("supplier_products.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_location_id = db.Column(db.Integer, db.ForeignKey("supplier_locations.id", ondelete="RESTRICT"), nullable=True)
    import_id = db.Column(db.Integer, db.ForeignKey("supplier_price_imports.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 4), nullable=False)
    currency = db.Column(db.String(8), nullable=False, default="CAD")
    unit = db.Column(db.String(20), nullable=False)
    discount_percent = db.Column(db.Numeric(6, 3), nullable=True)
    discount_rule = db.Column(db.String(160), nullable=True)
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)
    availability = db.Column(db.String(20), nullable=True)
    demo_synthetic = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    product = db.relationship("SupplierProduct")
    price_import = db.relationship("SupplierPriceImport")


class SupplierQuoteSettings(db.Model):
    """A supplier's own quotation settings: tax, validity, delivery and terms."""

    __tablename__ = "supplier_quote_settings"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, unique=True)
    tax_label = db.Column(db.String(20), nullable=True)
    tax_rate_percent = db.Column(db.Numeric(6, 3), nullable=True)
    validity_days = db.Column(db.Integer, nullable=True)
    default_delivery_charge = db.Column(db.Numeric(12, 2), nullable=True)
    terms_text = db.Column(db.Text, nullable=True)
    contact_line = db.Column(db.String(300), nullable=True)
    updated_by_name = db.Column(db.String(160), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
