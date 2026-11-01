"""Documents: the Company library, each context's Documents page, upload, the document page, and job documents for
the crew (31 Oct 2026; internal name RDIMS).

Office pages pass the office wall (sign-in, organization, field-only redirect, supplier logins refused). Every lookup
is inside the signed-in organization and the viewer's scope; anything else is 404 (never 403), so another
organization's documents are not revealed. The two field pages are allow-listed for field-only members and show only
their jobs' crew-visible documents.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from app import db
from app.models.documents import (
    CONTEXT_COMPANY,
    CONTEXT_CUSTOMER,
    CONTEXT_EQUIPMENT,
    CONTEXT_KINDS,
    CONTEXT_PERSON,
    CONTEXT_PROJECT,
    CONTEXT_SUBCONTRACTOR,
    CONTEXT_SUPPLIER,
    DATE_CONFIRMED,
    DATE_KINDS,
    DATE_LABELS,
    DATE_PROPOSED,
    SENSITIVITIES,
    STATUS_ACTIVE,
    DocumentDate,
    DocumentEvent,
    DocumentLink,
    DocumentText,
    DocumentVersion,
)
from app.services import document_storage
from app.services.documents import ingest
from app.services.documents.access import field_scope, may_see_context_kind, office_scope, require_document
from app.services.documents.contexts import CONTEXT_LABELS, DocumentNotFound, labels_for_documents, resolve_context
from app.services.documents.dates import find_dates
from app.services.documents.extract import MAX_SYNC_BYTES, extract_text
from app.services.documents.search import Filters, search
from app.services.documents.sources import (
    SOURCE_LABELS,
    DocumentUnavailable,
    connect_project_lazily,
    read_version_bytes,
    signing_request_for,
)
from app.services.documents.types import FAMILY_ORDER, REGISTRY, TYPES, classify, get_type, types_for_context
from app.services.organizations import get_current_organization_id

documents_bp = Blueprint("documents", __name__)


# ------------------------------------------------------------------ helpers


def _org():
    return get_current_organization_id()


def _scope():
    scope = office_scope(current_user, _org())
    if scope is None:
        abort(404)
    return scope


def _actor():
    return ingest.Actor.of(current_user)


def _context_or_404(kind, target_id, scope):
    if not may_see_context_kind(scope, kind):
        abort(404)
    try:
        return resolve_context(_org(), kind, target_id)
    except DocumentNotFound:
        abort(404)


def _document_or_404(public_id, scope=None):
    try:
        return require_document(public_id, scope or _scope())
    except DocumentNotFound:
        abort(404)


def _page():
    try:
        return max(1, int(request.args.get("page") or 1))
    except ValueError:
        return 1


def _parse_date(raw):
    try:
        return date.fromisoformat((raw or "").strip())
    except ValueError:
        return None


def _upload_url(context):
    values = {"context": context.kind}
    if context.target_id is not None:
        values["context_id"] = context.target_id
    return url_for("documents.upload", **values)


def _render_context(context, scope, *, template="documents/context.html", **extra):
    filters = Filters(context_kind=context.kind, context_id=context.target_id,
                      status=(request.args.get("status") or STATUS_ACTIVE).upper())
    if filters.status not in (STATUS_ACTIVE, "ARCHIVED", "ALL"):
        filters.status = STATUS_ACTIVE
    results = search(scope, filters, page=_page())
    return render_template(template, context=context, results=results, upload_url=_upload_url(context),
                           families=FAMILY_ORDER, status=filters.status, **extra)


# ------------------------------------------------------------------ company library and search


@documents_bp.route("/documents")
def library():
    scope = _scope()
    filters = Filters.from_args(request.args)
    results = search(scope, filters, page=_page())
    company = resolve_context(_org(), CONTEXT_COMPANY)
    return render_template("documents/library.html", results=results, filters=filters, context=company,
                           upload_url=_upload_url(company), types=[t for t in REGISTRY],
                           families=FAMILY_ORDER, context_labels=CONTEXT_LABELS,
                           context_kinds=[k for k in CONTEXT_KINDS if may_see_context_kind(scope, k)],
                           people_admin=scope.people_admin)


@documents_bp.route("/documents/suppliers")
def suppliers():
    from app.models.supplier_catalogue import Supplier
    from app.services.documents.contexts import supplier_ids_for_org

    _scope()
    ids = supplier_ids_for_org(_org())
    rows = Supplier.query.filter(Supplier.id.in_(sorted(ids) or [-1])).order_by(Supplier.legal_name).all()
    return render_template("documents/parties.html", heading="Suppliers", kind=CONTEXT_SUPPLIER,
                           rows=[(r.legal_name, url_for("documents.supplier_documents", supplier_id=r.id)) for r in rows],
                           empty="No suppliers yet. Suppliers appear here once your company has an account with them.")


@documents_bp.route("/subcontractors", methods=["GET", "POST"])
def subcontractors():
    from app.models.subcontractor import Subcontractor
    from app.services.subcontract_quote import SubcontractQuoteError, create_subcontractor

    _scope()
    if request.method == "POST":
        name = (request.form.get("legal_name") or "").strip()[:220]
        if not name:
            flash("Enter the subcontractor's name.", "error")
            return redirect(url_for("documents.subcontractors"))
        code = "".join(ch for ch in name.upper() if ch.isalnum())[:30] or "SUB"
        base, n = code, 1
        while Subcontractor.query.filter_by(organization_id=_org(), code=code).first() is not None:
            n += 1
            code = f"{base}-{n}"
        try:
            row = create_subcontractor(organization_id=_org(), code=code, legal_name=name)
        except SubcontractQuoteError as exc:
            flash(str(exc), "error")
            return redirect(url_for("documents.subcontractors"))
        flash(f"{row.legal_name} added.", "success")
        return redirect(url_for("documents.subcontractor_documents", subcontractor_id=row.id))
    rows = Subcontractor.query.filter_by(organization_id=_org()).order_by(Subcontractor.legal_name).all()
    return render_template("documents/parties.html", heading="Subcontractors", kind=CONTEXT_SUBCONTRACTOR,
                           rows=[(r.legal_name + ("" if r.status == "ACTIVE" else " (inactive)"),
                                  url_for("documents.subcontractor_documents", subcontractor_id=r.id)) for r in rows],
                           can_add=True,
                           empty="No subcontractors yet. Add one to keep their WSIB clearance, insurance and agreements.")


@documents_bp.route("/documents/people")
def people():
    from app.models.user import User, UserMembership

    scope = _scope()
    if not scope.people_admin:
        abort(404)
    rows = (db.session.query(UserMembership, User).join(User, User.id == UserMembership.user_id)
            .filter(UserMembership.organization_id == _org()).order_by(User.display_name).all())
    return render_template("documents/parties.html", heading="People", kind=CONTEXT_PERSON,
                           rows=[((u.display_name or u.email) + ("" if m.is_active else " (inactive)"),
                                  url_for("documents.person_documents", membership_id=m.id)) for m, u in rows],
                           empty="No people yet.")


# ------------------------------------------------------------------ context pages


@documents_bp.route("/projects/<int:project_id>/documents")
def project_documents(project_id):
    scope = _scope()
    context = _context_or_404(CONTEXT_PROJECT, project_id, scope)
    report = connect_project_lazily(_org(), project_id)  # existing plans, contracts and signed PDFs appear here
    return _render_context(context, scope, connected=report, project_id=project_id)


@documents_bp.route("/customers/<int:client_id>/documents")
def customer_documents(client_id):
    scope = _scope()
    return _render_context(_context_or_404(CONTEXT_CUSTOMER, client_id, scope), scope)


@documents_bp.route("/suppliers/<int:supplier_id>/documents")
def supplier_documents(supplier_id):
    scope = _scope()
    return _render_context(_context_or_404(CONTEXT_SUPPLIER, supplier_id, scope), scope)


@documents_bp.route("/subcontractors/<int:subcontractor_id>/documents")
def subcontractor_documents(subcontractor_id):
    scope = _scope()
    return _render_context(_context_or_404(CONTEXT_SUBCONTRACTOR, subcontractor_id, scope), scope)


@documents_bp.route("/people/<int:membership_id>/documents")
def person_documents(membership_id):
    scope = _scope()
    return _render_context(_context_or_404(CONTEXT_PERSON, membership_id, scope), scope)


# ------------------------------------------------------------------ upload


def _upload_context(scope):
    kind = (request.values.get("context") or CONTEXT_COMPANY).upper()
    return _context_or_404(kind, request.values.get("context_id"), scope)


def _type_options(kind):
    return types_for_context(kind)


@documents_bp.route("/documents/upload", methods=["GET", "POST"])
def upload():
    scope = _scope()
    context = _upload_context(scope)
    if request.method == "GET":
        return render_template("documents/upload.html", context=context, stage="file")
    actor = _actor()
    stage = request.form.get("stage") or "file"
    try:
        if stage == "save":
            blob = ingest.blob_from_stored(_org(), request.form.get("sha256", ""), request.form.get("ext", ""),
                                           request.form.get("filename", ""))
        else:
            file = request.files.get("file")
            if file is None or not file.filename:
                raise ingest.DocumentError("Choose a file to upload.")
            blob = ingest.prepare_upload(file.filename, file.read())
    except ingest.DocumentError as exc:
        flash(str(exc), "error")
        return render_template("documents/upload.html", context=context, stage="file"), 400

    if stage != "save" and request.form.get("quick") != "1":
        # Step 2: show what was understood from the file before anything is filed.
        try:
            document_storage.store_bytes(_org(), blob.data, blob.ext)
        except document_storage.DocumentStorageError as exc:
            flash(str(exc), "error")
            return render_template("documents/upload.html", context=context, stage="file"), 400
        current, _ = ingest.find_duplicates(_org(), blob.sha256)
        visible = []
        for doc in current:
            try:
                visible.append(require_document(doc.public_id, scope))
            except DocumentNotFound:
                continue
        pages = []
        if blob.size <= MAX_SYNC_BYTES:
            pages = extract_text(blob.data, blob.media_type).pages
        suggested, _rule = classify(blob.filename, context.kind, "\n".join(pages))
        proposals = find_dates(pages)
        return render_template("documents/upload.html", context=context, stage="review", blob=blob,
                               suggested=suggested, suggested_label=get_type(suggested).label,
                               type_options=_type_options(context.kind), proposals=proposals,
                               duplicates=visible, duplicate_labels=labels_for_documents(_org(), [d.id for d in visible]),
                               date_kinds=DATE_KINDS, date_labels=DATE_LABELS)

    type_code = request.form.get("document_type") or None
    try:
        document = ingest.file_document(
            _org(), actor, blob=blob, context=context, title=request.form.get("title"),
            type_code=type_code if type_code in TYPES else None, type_confirmed=stage == "save",
            reference_number=request.form.get("reference_number"), counterparty=request.form.get("counterparty"),
            description=request.form.get("description"), keywords=request.form.get("keywords"))
    except ingest.DocumentError as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return render_template("documents/upload.html", context=context, stage="file"), 400
    confirmed = 0
    chosen = set(request.form.getlist("confirm_date"))
    if chosen:
        for row in DocumentDate.query.filter_by(document_id=document.id, status=DATE_PROPOSED).all():
            if f"{row.date_kind}|{row.value.isoformat()}" in chosen:
                try:
                    ingest.confirm_date(document, actor, row.id)
                    confirmed += 1
                except ingest.DocumentError:
                    db.session.rollback()
    entered_kind = request.form.get("enter_kind")
    entered_value = _parse_date(request.form.get("enter_value"))
    if entered_kind in DATE_KINDS and entered_value:
        try:
            ingest.enter_date(document, actor, entered_kind, entered_value,
                              remind_days_before=request.form.get("remind_days_before") or 30)
            confirmed += 1
        except ingest.DocumentError as exc:
            db.session.rollback()
            flash(str(exc), "error")
    flash(f"Filed: {document.title}." + (f" {confirmed} date{'s' if confirmed != 1 else ''} confirmed." if confirmed
                                          else ""), "success")
    return redirect(url_for("documents.detail", public_id=document.public_id))


@documents_bp.route("/documents/upload/link", methods=["POST"])
def link_duplicate():
    scope = _scope()
    context = _upload_context(scope)
    document = _document_or_404(request.form.get("public_id", ""), scope)
    try:
        ingest.link_existing_here(document, _actor(), context)
    except ingest.DocumentError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Linked here: {document.title}. No second copy was filed.", "success")
    return redirect(url_for("documents.detail", public_id=document.public_id))


# ------------------------------------------------------------------ the document page


def _signing_panel(document, version):
    """CaliSIGN status for a contract, change order, subcontract or supplier order (links to the existing pages)."""
    from app.services.calisign import office_view, status_for, timeline

    if version is None:
        return None
    request_row = signing_request_for(version)
    if request_row is not None:
        family = request_row.document_family
        if family == "CONTRACT":
            link = url_for("projects.review_contract", id=request_row.project_id,
                           _anchor=f"contract-snapshot-{request_row.source_record_id}")
        elif family == "CHANGE_ORDER":
            link = url_for("project_controls.view_change_order", id=request_row.source_record_id)
        else:
            link = url_for("documents.project_documents", project_id=request_row.project_id)
        return {"status": status_for(request_row), "history": timeline(request_row), "link": link,
                "request_number": request_row.request_number,
                "download": url_for("signing_office.download_executed", request_id=request_row.id)}
    if version.source_kind == "GENERATED_CONTRACT":
        from app.models.project_contract import GeneratedProjectContract

        contract = db.session.get(GeneratedProjectContract, version.source_id)
        if contract is None or contract.organization_id != document.organization_id:
            return None
        status = office_view("CONTRACT", contract.id, document.organization_id)
        return {"status": status, "history": status.timeline,
                "link": url_for("projects.review_contract", id=contract.project_id,
                                _anchor=f"contract-snapshot-{contract.id}"),
                "request_number": None, "download": None, "send_from_contract_page": True}
    return None


@documents_bp.route("/documents/<public_id>")
def detail(public_id):
    scope = _scope()
    document = _document_or_404(public_id, scope)
    ingest.ensure_extracted(document, _actor())
    versions = DocumentVersion.query.filter_by(document_id=document.id).order_by(
        DocumentVersion.version_number.desc()).all()
    current = next((v for v in versions if v.is_current), None)
    dates = []
    if current is not None:
        dates = DocumentDate.query.filter_by(version_id=current.id).order_by(DocumentDate.status, DocumentDate.value).all()
    text_row = DocumentText.query.filter_by(version_id=current.id).first() if current else None
    links = (DocumentLink.query.filter_by(document_id=document.id).order_by(DocumentLink.unlinked_at.isnot(None),
                                                                              DocumentLink.id).all())
    active_labels = labels_for_documents(document.organization_id, [document.id]).get(document.id, [])
    events = (DocumentEvent.query.filter_by(document_id=document.id, organization_id=document.organization_id)
              .order_by(DocumentEvent.at.desc(), DocumentEvent.id.desc()).limit(200).all())
    primary = next((link for link in links if link.is_primary and link.unlinked_at is None), None)
    kind = primary.context_kind if primary else CONTEXT_COMPANY
    return render_template(
        "documents/detail.html", document=document, doc_type=get_type(document.document_type), versions=versions,
        current=current, dates=dates, proposed=[d for d in dates if d.status == DATE_PROPOSED],
        confirmed=[d for d in dates if d.status == DATE_CONFIRMED], text_row=text_row, links=active_labels,
        events=events, type_options=_type_options(kind), date_kinds=DATE_KINDS, date_labels=DATE_LABELS,
        source_labels=SOURCE_LABELS, inline=current is not None and current.media_type in document_storage.INLINE_MEDIA_TYPES
        and current.availability == "AVAILABLE", signing=_signing_panel(document, current),
        can_set_sensitivity=scope.people_admin, sensitivities=SENSITIVITIES,
        link_kinds=[k for k in CONTEXT_KINDS if may_see_context_kind(scope, k) and k != CONTEXT_COMPANY],
        context_labels=CONTEXT_LABELS)


def _send(document, version, *, download: bool):
    try:
        data = read_version_bytes(version)
    except DocumentUnavailable:
        flash("This file is not available. Upload it again as a new version.", "error")
        return redirect(url_for("documents.detail", public_id=document.public_id))
    inline = version.media_type in document_storage.INLINE_MEDIA_TYPES and not download
    response = send_file(BytesIO(data), mimetype=version.media_type, as_attachment=not inline,
                         download_name=version.original_filename)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, no-store"
    return response


@documents_bp.route("/documents/<public_id>/file")
def file(public_id):
    scope = _scope()
    document = _document_or_404(public_id, scope)
    query = DocumentVersion.query.filter_by(document_id=document.id, organization_id=document.organization_id)
    raw = request.args.get("v")
    version = (query.filter_by(version_number=int(raw)).first() if raw and raw.isdigit()
               else query.filter_by(is_current=True).first())
    if version is None:
        abort(404)
    download = request.args.get("download") == "1"
    if download:
        ingest.record_download(document, version, _actor())
    return _send(document, version, download=download)


def _back(document):
    return redirect(url_for("documents.detail", public_id=document.public_id))


def _guard(fn):
    try:
        fn()
        return True
    except ingest.DocumentError as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return False


@documents_bp.route("/documents/<public_id>/versions", methods=["POST"])
def add_version(public_id):
    document = _document_or_404(public_id)
    file = request.files.get("file")

    def go():
        if file is None or not file.filename:
            raise ingest.DocumentError("Choose the new file.")
        ingest.add_version(document, _actor(), ingest.prepare_upload(file.filename, file.read()),
                           request.form.get("note"))

    if _guard(go):
        flash("New version saved. The earlier version is kept in the history.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/dates/<int:date_id>/confirm", methods=["POST"])
def confirm_date(public_id, date_id):
    document = _document_or_404(public_id)
    value = _parse_date(request.form.get("value"))
    if _guard(lambda: ingest.confirm_date(document, _actor(), date_id, value=value,
                                          remind_days_before=request.form.get("remind_days_before"),
                                          reason=request.form.get("reason"))):
        flash("Date confirmed.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/dates/<int:date_id>/reject", methods=["POST"])
def reject_date(public_id, date_id):
    document = _document_or_404(public_id)
    if _guard(lambda: ingest.reject_date(document, _actor(), date_id, request.form.get("reason"))):
        flash("Date removed.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/dates", methods=["POST"])
def enter_date(public_id):
    document = _document_or_404(public_id)
    value = _parse_date(request.form.get("value"))

    def go():
        if value is None:
            raise ingest.DocumentError("Enter a date.")
        ingest.enter_date(document, _actor(), request.form.get("kind", ""), value,
                          remind_days_before=request.form.get("remind_days_before") or 30,
                          reason=request.form.get("reason"))

    if _guard(go):
        flash("Date saved.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/correct", methods=["POST"])
def correct(public_id):
    scope = _scope()
    document = _document_or_404(public_id, scope)
    if _guard(lambda: ingest.correct_field(document, _actor(), request.form.get("field", ""),
                                           request.form.get("value"), request.form.get("reason"),
                                           allow_sensitivity=scope.people_admin)):
        flash("Saved.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/confirm-type", methods=["POST"])
def confirm_type(public_id):
    document = _document_or_404(public_id)
    ingest.confirm_type(document, _actor())
    flash("Type confirmed.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/archive", methods=["POST"])
def archive(public_id):
    document = _document_or_404(public_id)
    if _guard(lambda: ingest.archive(document, _actor(), request.form.get("reason"))):
        flash("Archived. It stays in the library under Archived.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/restore", methods=["POST"])
def restore(public_id):
    document = _document_or_404(public_id)
    ingest.restore(document, _actor(), request.form.get("reason"))
    flash("Restored.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/links", methods=["POST"])
def add_link(public_id):
    scope = _scope()
    document = _document_or_404(public_id, scope)
    kind = (request.form.get("context") or "").upper()
    context = _context_or_404(kind, request.form.get("context_id"), scope)

    def go():
        ingest.add_link(document, _actor(), context)
        from app.services.documents import fts

        fts.index_document(document)
        db.session.commit()

    if _guard(go):
        flash(f"Linked to {context.label}.", "success")
    return _back(document)


@documents_bp.route("/documents/<public_id>/links/<int:link_id>/end", methods=["POST"])
def end_link(public_id, link_id):
    document = _document_or_404(public_id)
    link = DocumentLink.query.filter_by(id=link_id, document_id=document.id,
                                        organization_id=document.organization_id).first()
    if link is None:
        abort(404)
    if _guard(lambda: ingest.end_link(document, _actor(), link, request.form.get("reason"))):
        flash("Link removed. It stays in the history.", "success")
    return _back(document)


# ------------------------------------------------------------------ field: job documents for the crew


def _field_project_or_404(project_id):
    from app.models import Project

    scope = field_scope(current_user, _org())
    if scope.project_ids is not None and project_id not in scope.project_ids:
        abort(404)
    project = Project.query.filter_by(id=project_id, organization_id=_org()).first()
    if project is None:
        abort(404)
    return scope, project


@documents_bp.route("/field-documents/projects/<int:project_id>")
def field_project(project_id):
    scope, project = _field_project_or_404(project_id)
    results = search(scope, Filters(context_kind=CONTEXT_PROJECT, context_id=project.id), page=_page())
    return render_template("documents/field_project.html", project=project, results=results)


@documents_bp.route("/field-documents/<public_id>/file")
def field_file(public_id):
    scope = field_scope(current_user, _org())
    try:
        document = require_document(public_id, scope)
    except DocumentNotFound:
        abort(404)
    version = DocumentVersion.query.filter_by(document_id=document.id, is_current=True).first()
    if version is None or document.status != STATUS_ACTIVE:
        abort(404)
    try:
        data = read_version_bytes(version)
    except DocumentUnavailable:
        abort(404)
    inline = version.media_type in document_storage.INLINE_MEDIA_TYPES
    response = send_file(BytesIO(data), mimetype=version.media_type, as_attachment=not inline,
                         download_name=version.original_filename)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, no-store"
    return response
