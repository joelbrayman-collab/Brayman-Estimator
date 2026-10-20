"""Supplier PRO Desk pages (ADR-047 Amendment 1; Joel, 20 Oct 2026).

Under /supplier/<id>/pro-desk, behind the same supplier sign-in and guard as the rest of the Supplier
Hub. Every page checks the signed-in person belongs to the supplier; every record is looked up within that
supplier; anything else is Not found.
"""

from __future__ import annotations

import os
import tempfile
from datetime import date

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.models.supplier_catalogue import SupplierLocation
from app.models.supplier_quote import (
    ACCEPT_EMAIL,
    ACCEPT_IN_PERSON,
    ACCEPT_PHONE,
    QUOTE_ACCEPTED,
    QUOTE_DRAFT,
    QUOTE_ISSUED,
)
from app.routes.supplier_portal import _brand_helpers
from app.services import supplier_pro_desk as P
from app.services.drawings import outbuilding as OB
from app.services.outbuilding import spec as S
from app.services.outbuilding import takeoff as T
from app.services.supplier_hub import SupplierHubError, active_supplier_memberships, require_supplier_membership, supplier_brand

supplier_pro_desk_bp = Blueprint("supplier_pro_desk", __name__, url_prefix="/supplier")
supplier_pro_desk_bp.context_processor(_brand_helpers)

NO_STORE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


def _supplier(supplier_id):
    try:
        return require_supplier_membership(current_user, supplier_id).supplier
    except SupplierHubError:
        abort(404)


def _areas():
    return [m.supplier for m in active_supplier_memberships(current_user)]


def _quote(supplier, quote_id):
    try:
        return P.supplier_quote(supplier.id, quote_id)
    except P.ProDeskError:
        abort(404)


def _back(supplier, quote, anchor=""):
    return redirect(url_for("supplier_pro_desk.quote", supplier_id=supplier.id, quote_id=quote.id) + anchor)


def identity_for(quote) -> OB.Identity:
    name = P._supplier_name(quote.supplier_id)
    settings = P.settings_for(quote.supplier_id)
    location = db.session.get(SupplierLocation, quote.supplier_location_id) if quote.supplier_location_id else None
    lines = [x for x in ((location.display_name if location else ""), (settings.contact_line if settings else "")) if x]
    customer = quote.customer
    when = (quote.issued_at.date() if quote.issued_at else date.today()).isoformat()
    return OB.Identity(company=name, company_lines=lines or ["Prepared at the PRO Desk"],
                       project=f"{quote.number} · {customer.display_name}",
                       address=", ".join(x for x in (customer.address, customer.town) if x) or "Address to be confirmed",
                       date=when)


def _logo_file(supplier_id):
    brand = supplier_brand(supplier_id)
    if not brand or not brand.logo_bytes:
        return None, None
    suffix = ".png" if (brand.logo_mime or "").endswith("png") else ".jpg"
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    handle.write(brand.logo_bytes)
    handle.close()
    return handle.name, brand


def drawing_bytes(quote, fmt="pdf", sheet=0, values=None):
    values = values if values is not None else P.spec_values(quote)
    path, _brand = _logo_file(quote.supplier_id)
    try:
        return OB.render(values, identity_for(quote), fmt=fmt, logo_path=path, sheet=sheet)
    finally:
        if path:
            os.unlink(path)


def quote_pdf_bytes(quote) -> bytes:
    from app.services.supplier_quote_pdf import render_quote_pdf

    frozen = dict(quote.issued_json or {})
    frozen["_sha256"] = quote.issued_sha256 or ""
    brand = supplier_brand(quote.supplier_id)
    png = []
    if S.drawable(frozen.get("building") or {}):
        png = [drawing_bytes(quote, "png", sheet, values=frozen["building"]) for sheet in (0, 1)]
    note = ("Accepted by " + quote.accepted_by_name + f" on {quote.accepted_at:%Y-%m-%d}.") if quote.status == QUOTE_ACCEPTED else ""
    return render_quote_pdf(frozen, logo_bytes=brand.logo_bytes if brand else None,
                            brand_color=brand.primary_color if brand else None, drawing_png=png, approval_note=note)


# ------------------------------------------------------------------ pages


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/")
def index(supplier_id):
    supplier = _supplier(supplier_id)
    return render_template("supplier/pro_desk/index.html", supplier=supplier, areas=_areas(),
                           quotes=P.supplier_quotes(supplier.id), settings_blockers=P.settings_blockers(supplier.id),
                           imports=P.price_imports(supplier.id)[:1])


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/new", methods=["GET", "POST"])
def new_quote(supplier_id):
    supplier = _supplier(supplier_id)
    locations = SupplierLocation.query.filter_by(supplier_id=supplier.id, status="ACTIVE").order_by(SupplierLocation.id).all()
    if request.method == "POST":
        try:
            quote = P.start_quote(supplier, request.form, user=current_user,
                                  demo_synthetic=request.form.get("demo_synthetic") == "yes")
        except P.ProDeskError as exc:
            flash(str(exc), "error")
            return render_template("supplier/pro_desk/new.html", supplier=supplier, areas=_areas(), locations=locations,
                                   form=request.form), 400
        flash(f"Quotation {quote.number} started for {quote.customer.display_name}.", "success")
        return _back(supplier, quote, "#sketch")
    return render_template("supplier/pro_desk/new.html", supplier=supplier, areas=_areas(), locations=locations, form={})


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/quick", methods=["GET", "POST"])
def quick(supplier_id):
    """Quick Quote: customer, the store's standard building, size, doors and floor on one page."""
    supplier = _supplier(supplier_id)
    assemblies = P.active_assemblies(supplier.id)
    locations = SupplierLocation.query.filter_by(supplier_id=supplier.id, status="ACTIVE").order_by(SupplierLocation.id).all()
    context = dict(supplier=supplier, areas=_areas(), assemblies=assemblies, locations=locations, fields=S.FIELD_BY_KEY,
                   opening_kinds=S.OPENING_KINDS, walls=S.WALLS, foundations=S.FOUNDATIONS, rows=S.QUICK_DOOR_ROWS,
                   settings_blockers=P.settings_blockers(supplier.id))
    if request.method == "POST":
        try:
            quote, errors = P.quick_quote(supplier, request.form, user=current_user,
                                          demo_synthetic=request.form.get("demo_synthetic") == "yes")
        except P.ProDeskError as exc:
            quote, errors = None, [str(exc)]
        if errors:
            return render_template("supplier/pro_desk/quick.html", form=request.form, errors=errors,
                                   started_at=request.form.get("started_at", ""), **context), 400
        upload = request.files.get("sketch")
        if upload and upload.filename:
            try:
                P.add_sketch(quote, filename=upload.filename, content=upload.read(P.MAX_SKETCH_BYTES + 1), user=current_user)
            except P.ProDeskError as exc:
                flash(f"Quotation started, but the sketch was not kept: {exc}", "error")
        flash(f"Quotation {quote.number} for {quote.customer.display_name}: check the price review, then issue.", "success")
        return _back(supplier, quote, "#pricing")
    from datetime import datetime

    return render_template("supplier/pro_desk/quick.html", form={}, errors=[],
                           started_at=datetime.utcnow().isoformat(timespec="seconds"), **context)


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/standards", methods=["GET", "POST"])
def standards(supplier_id):
    """The store's standard buildings for Quick Quote: set up once, used on every walk-in."""
    supplier = _supplier(supplier_id)
    form, errors = {}, []
    if request.method == "POST":
        if request.form.get("retire"):
            try:
                row = P.retire_assembly(supplier, request.form.get("retire"), user=current_user)
            except P.ProDeskError:
                abort(404)
            flash(f"\u201c{row.name}\u201d retired. Quotations already made keep their record of it.", "success")
            return redirect(url_for("supplier_pro_desk.standards", supplier_id=supplier.id))
        row, errors = P.save_assembly(supplier, request.form, user=current_user,
                                      demo_synthetic=request.form.get("demo_synthetic") == "yes")
        if row is not None:
            flash(f"Standard building \u201c{row.name}\u201d saved for Quick Quote.", "success")
            return redirect(url_for("supplier_pro_desk.standards", supplier_id=supplier.id))
        form = request.form
    from app.models.supplier_quote import SupplierBuildingAssembly

    rows = (SupplierBuildingAssembly.query.filter_by(supplier_id=supplier.id)
            .order_by(SupplierBuildingAssembly.status, SupplierBuildingAssembly.name).all())
    return render_template("supplier/pro_desk/standards.html", supplier=supplier, areas=_areas(), rows=rows, form=form,
                           errors=errors, keys=S.ASSEMBLY_KEYS, fields=S.FIELD_BY_KEY, systems=S.BUILDING_SYSTEMS,
                           roofs=S.ROOF_TYPES), (400 if errors else 200)


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/timing")
def timing(supplier_id):
    """How long each walk-in quotation took, stage by stage, apart from the store's one-time setup."""
    supplier = _supplier(supplier_id)
    quotes = P.supplier_quotes(supplier.id)
    return render_template("supplier/pro_desk/timing.html", supplier=supplier, areas=_areas(),
                           timings=[(q, P.quote_timing(q)) for q in quotes], setup=P.setup_record(supplier.id))


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>")
def quote(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    values = P.spec_values(q)
    priced = P.price_quote(q)
    return render_template(
        "supplier/pro_desk/quote.html", supplier=supplier, areas=_areas(), q=q, values=values, fields=S.FIELDS, field_labels={f.key: f.label for f in S.FIELDS},
        systems=S.BUILDING_SYSTEMS, not_yet=S.SYSTEMS_NOT_YET_AVAILABLE, opening_kinds=S.OPENING_KINDS, walls=S.WALLS,
        max_openings=S.MAX_OPENINGS, drawable=S.drawable(values), describe=S.describe(values), priced=priced,
        summary=T.summary(priced["takeoff"]), sketches=P.active_sketches(q), events=P.quote_events(q),
        products=P.supplier_products_for(supplier.id), settings=P.settings_for(supplier.id),
        frozen=q.issued_json or {}, today=date.today(), draft=q.status == QUOTE_DRAFT,
        credential=request.args.get("link"), statuses={"DRAFT": "Draft", "ISSUED": "Issued", "ACCEPTED": "Accepted",
                                                       "DECLINED": "Declined", "CANCELLED": "Replaced by a revision"})


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/sketch", methods=["POST"])
def add_sketch(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    upload = request.files.get("sketch")
    try:
        content = upload.read(P.MAX_SKETCH_BYTES + 1) if upload else b""
        P.add_sketch(q, filename=upload.filename if upload else "", content=content, user=current_user)
    except P.ProDeskError as exc:
        flash(str(exc), "error")
    else:
        flash("Sketch kept with the quotation. Read it with the customer and answer the questions below.", "success")
    return _back(supplier, q, "#sketch")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/sketch/<int:file_id>")
def sketch(supplier_id, quote_id, file_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        row = P.sketch_for(q, file_id)
    except P.ProDeskError:
        abort(404)
    return Response(row.content, mimetype=row.mime,
                    headers={**NO_STORE, "Content-Disposition": f'inline; filename="{row.filename}"',
                             "Content-Security-Policy": "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'"})


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/sketch/<int:file_id>/remove", methods=["POST"])
def remove_sketch(supplier_id, quote_id, file_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        P.remove_sketch(q, file_id, user=current_user)
    except P.ProDeskError as exc:
        flash(str(exc), "error")
    return _back(supplier, q, "#sketch")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/building", methods=["POST"])
def save_building(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        errors = P.save_spec(q, request.form, user=current_user)
    except P.ProDeskError as exc:
        flash(str(exc), "error")
        return _back(supplier, q, "#building")
    for e in errors:
        flash(e, "error")
    if not errors:
        flash("Building confirmed. Drawing and material list updated.", "success")
    return _back(supplier, q, "#drawing" if not errors else "#building")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/drawing.<fmt>")
def drawing(supplier_id, quote_id, fmt):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    if fmt not in ("pdf", "dxf", "png"):
        abort(404)
    values = (q.issued_json or {}).get("building") if q.status != QUOTE_DRAFT else P.spec_values(q)
    if not S.drawable(values or {}):
        abort(404)
    sheet = 1 if request.args.get("sheet") == "2" else 0
    data = drawing_bytes(q, fmt, sheet, values=values)
    mime = {"pdf": "application/pdf", "dxf": "application/dxf", "png": "image/png"}[fmt]
    headers = dict(NO_STORE)
    if fmt != "png":
        headers["Content-Disposition"] = f'attachment; filename="{q.number}-preliminary-sales-drawing.{fmt}"'
    return Response(data, mimetype=mime, headers=headers)


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/match", methods=["POST"])
def match(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    code = request.form.get("code", "")
    line = next((l for l in P.takeoff_for(q).get("lines", []) if l["code"] == code), None)
    if line is None:
        abort(404)
    try:
        product_id = int(request.form.get("product_id") or 0)
        mapping = P.match_product(supplier, line, product_id=product_id, sales_per_unit=request.form.get("sales_per_unit", ""),
                                  user=current_user)
        P.choose_line(q, code=code, product_id=mapping.supplier_product_id, exclude_reason="", user=current_user)
    except (P.ProDeskError, ValueError) as exc:
        flash(str(exc), "error")
    else:
        flash("Product matched. It will be offered for this line on future quotations too.", "success")
    return _back(supplier, q, "#pricing")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/line", methods=["POST"])
def line(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        product_id = int(request.form.get("product_id") or 0) or None
        P.choose_line(q, code=request.form.get("code", ""), product_id=product_id,
                      exclude_reason=request.form.get("exclude_reason", ""), user=current_user)
    except (P.ProDeskError, ValueError) as exc:
        flash(str(exc), "error")
    return _back(supplier, q, "#pricing")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/commercials", methods=["POST"])
def commercials(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        P.set_commercials(q, request.form, user=current_user)
    except P.ProDeskError as exc:
        flash(str(exc), "error")
    return _back(supplier, q, "#quotation")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/issue", methods=["POST"])
def issue(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        P.issue_quote(q, user=current_user, drawing_fingerprint=OB.fingerprint(P.spec_values(q)))
    except P.ProDeskError as exc:
        flash(str(exc), "error")
        return _back(supplier, q, "#quotation")
    flash(f"Quotation {q.number} issued: ${q.total:,.2f} including tax, valid until {q.valid_until:%b %d, %Y}.", "success")
    return _back(supplier, q, "#approval")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/quotation.pdf")
def quote_pdf(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    if not q.issued_json:
        abort(404)
    data = quote_pdf_bytes(q)
    P.record_printed(q, user=current_user)
    return Response(data, mimetype="application/pdf",
                    headers={**NO_STORE, "Content-Disposition": f'inline; filename="{q.number}-material-quotation.pdf"'})


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/link", methods=["POST"])
def make_link(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        credential = P.create_link(q, user=current_user)
        if request.form.get("send_email") == "yes":
            message = P.send_quote_email(q, credential=credential, base_url=request.host_url, user=current_user)
            flash({"ACCEPTED": "Quotation emailed to the customer.", "LOCAL_CAPTURED": "Quotation email recorded (local test mail)."}.get(
                message.status, f"Email not sent ({message.status.replace('_', ' ').lower()})."),
                "success" if message.status in ("ACCEPTED", "LOCAL_CAPTURED") else "error")
    except P.ProDeskError as exc:
        flash(str(exc), "error")
        return _back(supplier, q, "#approval")
    return redirect(url_for("supplier_pro_desk.quote", supplier_id=supplier.id, quote_id=q.id, link=credential) + "#approval")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/accept", methods=["POST"])
def accept(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    method = {"in_person": ACCEPT_IN_PERSON, "phone": ACCEPT_PHONE, "email": ACCEPT_EMAIL}.get(request.form.get("method", ""), "")
    try:
        P.record_acceptance(q, method=method, name=request.form.get("customer_name", ""), user=current_user,
                            accepted=request.form.get("answer") != "decline")
    except P.ProDeskError as exc:
        flash(str(exc), "error")
    else:
        flash("Customer's answer recorded.", "success")
    return _back(supplier, q, "#approval")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/revise", methods=["POST"])
def revise(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        copy = P.start_revision(q, user=current_user)
    except P.ProDeskError as exc:
        flash(str(exc), "error")
        return _back(supplier, q)
    flash(f"Revision {copy.number} started. {q.number} is kept as issued and its approval link no longer works.", "success")
    return _back(supplier, copy, "#building")


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/order-ready", methods=["POST"])
def order_ready(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    try:
        P.mark_order_ready(q, user=current_user)
    except P.ProDeskError as exc:
        flash(str(exc), "error")
        return _back(supplier, q, "#order")
    return redirect(url_for("supplier_pro_desk.order", supplier_id=supplier.id, quote_id=q.id))


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/order")
def order(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    if q.order_ready_at is None:
        abort(404)
    return render_template("supplier/pro_desk/order.html", supplier=supplier, areas=_areas(), q=q, package=P.order_package(q))


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/<int:quote_id>/order.csv")
def order_csv(supplier_id, quote_id):
    supplier = _supplier(supplier_id)
    q = _quote(supplier, quote_id)
    if q.order_ready_at is None:
        abort(404)
    return Response(P.order_csv(q), mimetype="text/csv",
                    headers={**NO_STORE, "Content-Disposition": f'attachment; filename="{q.number}-order.csv"'})


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/prices", methods=["GET", "POST"])
def prices(supplier_id):
    supplier = _supplier(supplier_id)
    if request.method == "POST":
        upload = request.files.get("price_file")
        try:
            content = upload.read(P.MAX_PRICE_FILE_BYTES + 1) if upload else b""
            record = P.import_price_file(supplier, filename=upload.filename if upload else "", content=content,
                                         authorized_by=request.form.get("authorized_by", ""), user=current_user,
                                         demo_synthetic=request.form.get("demo_synthetic") == "yes")
        except P.ProDeskError as exc:
            flash(str(exc), "error")
        else:
            flash(f"{record.rows_loaded} prices loaded; {record.rows_rejected} rows not loaded (listed below).",
                  "success" if not record.rows_rejected else "error")
        return redirect(url_for("supplier_pro_desk.prices", supplier_id=supplier.id))
    return render_template("supplier/pro_desk/prices.html", supplier=supplier, areas=_areas(), imports=P.price_imports(supplier.id),
                           columns=P.PRICE_COLUMNS, required=P.REQUIRED_PRICE_COLUMNS)


@supplier_pro_desk_bp.route("/<int:supplier_id>/pro-desk/settings", methods=["GET", "POST"])
def settings(supplier_id):
    supplier = _supplier(supplier_id)
    if request.method == "POST":
        try:
            P.save_settings(supplier, request.form, user=current_user)
        except P.ProDeskError as exc:
            flash(str(exc), "error")
        else:
            flash("Quote settings saved.", "success")
        return redirect(url_for("supplier_pro_desk.settings", supplier_id=supplier.id))
    return render_template("supplier/pro_desk/settings.html", supplier=supplier, areas=_areas(), s=P.settings_for(supplier.id))
