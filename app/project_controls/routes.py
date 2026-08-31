from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.models import Estimate, EstimateVersion, Project
from app.project_controls import repository as repo
from app.project_controls.models import CHANGE_ORDER_STATUSES, ChangeOrderItem
from app.project_controls.pdf import (
    generate_change_order_pdf,
    sanitize_change_order_filename,
)
from app.services.auth import form_actor
from app.services.organizations import get_current_organization_id
from app.project_controls.services import (
    ChangeOrderServiceError,
    add_change_order_item,
    create_change_order,
    delete_change_order_item,
    update_change_order,
    update_change_order_item,
    update_change_order_status,
)

project_controls_bp = Blueprint("project_controls", __name__)


def _parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_datetime_start(value):
    d = _parse_date(value)
    if d is None:
        return None
    return datetime.combine(d, datetime.min.time())


def _parse_datetime_end(value):
    d = _parse_date(value)
    if d is None:
        return None
    return datetime.combine(d, datetime.max.time())


def _form_from_change_order(change_order):
    return {
        "title": change_order.title,
        "description": change_order.description or "",
        "reason": change_order.reason or "",
        "status": change_order.status,
        "requested_by": change_order.requested_by or "",
        "requested_date": (
            change_order.requested_date.isoformat()
            if change_order.requested_date
            else ""
        ),
        "project_id": str(change_order.project_id),
        "estimate_version_id": (
            str(change_order.estimate_version_id)
            if change_order.estimate_version_id
            else ""
        ),
        "markup_percent": f"{change_order.markup_percent:.2f}",
        "tax_percent": f"{change_order.tax_percent:.2f}",
        "notes": change_order.notes or "",
    }


@project_controls_bp.route("/project-controls/change-orders/")
@project_controls_bp.route("/project-controls/change-orders")
def list_change_orders():
    project_id = request.args.get("project_id", type=int)
    status = (request.args.get("status") or "").strip() or None
    search = (request.args.get("q") or "").strip() or None
    date_from = _parse_datetime_start(request.args.get("date_from"))
    date_to = _parse_datetime_end(request.args.get("date_to"))

    change_orders = repo.list_change_orders(
        project_id=project_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    projects = Project.query.filter_by(organization_id=get_current_organization_id()).order_by(Project.name).all()
    return render_template(
        "project_controls/change_orders/list.html",
        change_orders=change_orders,
        projects=projects,
        statuses=CHANGE_ORDER_STATUSES,
        filters={
            "project_id": project_id or "",
            "status": status or "",
            "q": search or "",
            "date_from": request.args.get("date_from") or "",
            "date_to": request.args.get("date_to") or "",
        },
    )


@project_controls_bp.route("/project-controls/change-orders/new", methods=["GET", "POST"])
def create_change_order_route():
    projects = Project.query.filter_by(organization_id=get_current_organization_id()).order_by(Project.name).all()
    if not projects:
        flash("Create a project before adding a change order.", "error")
        return redirect(url_for("projects.create_project"))

    preselect_project_id = request.args.get("project_id", type=int)

    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        project = Project.query.get(project_id) if project_id else None
        try:
            change_order = create_change_order(
                project=project,
                title=request.form.get("title", ""),
                description=request.form.get("description", ""),
                reason=request.form.get("reason", ""),
                requested_by=form_actor("requested_by"),
                requested_date=_parse_date(request.form.get("requested_date")),
                markup_percent=request.form.get("markup_percent") or 0,
                tax_percent=request.form.get("tax_percent") or 0,
                notes=request.form.get("notes", ""),
                status=request.form.get("status") or "Draft",
            )
        except (ChangeOrderServiceError, ValueError) as exc:
            flash(str(exc), "error")
            return render_template(
                "project_controls/change_orders/form.html",
                form=request.form,
                projects=projects,
                statuses=CHANGE_ORDER_STATUSES,
                change_order=None,
                estimate=None,
                version=None,
            )

        flash("Change order created.", "success")
        return redirect(
            url_for("project_controls.view_change_order", id=change_order.id)
        )

    form = {
        "title": "",
        "description": "",
        "reason": "",
        "status": "Draft",
        "requested_by": "",
        "requested_date": datetime.utcnow().date().isoformat(),
        "project_id": str(preselect_project_id or projects[0].id),
        "markup_percent": "0.00",
        "tax_percent": "0.00",
        "notes": "",
    }
    return render_template(
        "project_controls/change_orders/form.html",
        form=form,
        projects=projects,
        statuses=CHANGE_ORDER_STATUSES,
        change_order=None,
        estimate=None,
        version=None,
    )


@project_controls_bp.route(
    "/estimates/<int:estimate_id>/versions/<int:version_id>/change-orders/new",
    methods=["GET", "POST"],
)
def create_from_estimate_version(estimate_id, version_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    version = EstimateVersion.query.filter_by(
        id=version_id,
        estimate_id=estimate.id,
    ).first_or_404()
    project = estimate.project
    projects = Project.query.filter_by(organization_id=get_current_organization_id()).order_by(Project.name).all()

    if request.method == "POST":
        copy_lines = request.form.get("copy_estimate_lines") == "on"
        try:
            change_order = create_change_order(
                project=project,
                title=request.form.get("title")
                or f"Change Order — {estimate.estimate_number}",
                description=request.form.get("description")
                or version.revision_reason
                or estimate.title,
                reason=request.form.get("reason", ""),
                requested_by=form_actor("requested_by"),
                requested_date=_parse_date(request.form.get("requested_date")),
                estimate_version=version,
                markup_percent=request.form.get("markup_percent")
                or (
                    0
                    if getattr(version, "pricing_snapshot", None)
                    else version.overhead_percent
                )
                or 0,
                tax_percent=request.form.get("tax_percent") or version.tax_percent or 0,
                notes=request.form.get("notes", ""),
                copy_estimate_lines=copy_lines,
                status=request.form.get("status") or "Draft",
            )
        except (ChangeOrderServiceError, ValueError) as exc:
            flash(str(exc), "error")
            form = request.form
            return render_template(
                "project_controls/change_orders/form.html",
                form=form,
                projects=projects,
                statuses=CHANGE_ORDER_STATUSES,
                change_order=None,
                estimate=estimate,
                version=version,
            )

        flash("Change order created from estimate version.", "success")
        return redirect(
            url_for("project_controls.view_change_order", id=change_order.id)
        )

    snapshot = getattr(version, "pricing_snapshot", None)
    form = {
        "title": f"Change Order — {estimate.estimate_number} {version.display_label}",
        "description": version.revision_reason or estimate.title or "",
        "reason": "",
        "status": "Draft",
        "requested_by": "",
        "requested_date": datetime.utcnow().date().isoformat(),
        "project_id": str(project.id),
        "markup_percent": (
            "0.00" if snapshot else f"{version.overhead_percent:.2f}"
        ),
        "tax_percent": f"{(snapshot.tax_percent if snapshot else version.tax_percent):.2f}",
        "notes": "",
        "copy_estimate_lines": "",
    }
    return render_template(
        "project_controls/change_orders/form.html",
        form=form,
        projects=projects,
        statuses=CHANGE_ORDER_STATUSES,
        change_order=None,
        estimate=estimate,
        version=version,
    )


@project_controls_bp.route("/project-controls/change-orders/<int:id>")
def view_change_order(id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    tab = (request.args.get("tab") or "overview").strip().lower()
    if tab not in {"overview", "items", "notes", "history"}:
        tab = "overview"
    editing_item_id = request.args.get("edit_item", type=int)
    item_edit_form = None
    if editing_item_id:
        item = next(
            (row for row in change_order.items if row.id == editing_item_id),
            None,
        )
        if item:
            item_edit_form = {
                "description": item.description,
                "quantity": f"{item.quantity}",
                "unit": item.unit,
                "unit_price": f"{item.unit_price}",
            }
        else:
            editing_item_id = None

    return render_template(
        "project_controls/change_orders/detail.html",
        change_order=change_order,
        tab=tab,
        statuses=CHANGE_ORDER_STATUSES,
        editing_item_id=editing_item_id,
        item_edit_form=item_edit_form,
    )


@project_controls_bp.route("/project-controls/change-orders/<int:id>/edit", methods=["GET", "POST"])
def edit_change_order(id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    projects = Project.query.filter_by(organization_id=get_current_organization_id()).order_by(Project.name).all()

    if request.method == "POST":
        try:
            update_change_order(
                change_order,
                title=request.form.get("title", ""),
                description=request.form.get("description", ""),
                reason=request.form.get("reason", ""),
                requested_by=form_actor("requested_by"),
                requested_date=_parse_date(request.form.get("requested_date")),
                project_id=request.form.get("project_id", type=int),
                markup_percent=request.form.get("markup_percent") or 0,
                tax_percent=request.form.get("tax_percent") or 0,
                notes=request.form.get("notes", ""),
                status=request.form.get("status") or change_order.status,
            )
        except (ChangeOrderServiceError, ValueError) as exc:
            flash(str(exc), "error")
            return render_template(
                "project_controls/change_orders/form.html",
                form=request.form,
                projects=projects,
                statuses=CHANGE_ORDER_STATUSES,
                change_order=change_order,
                estimate=None,
                version=None,
            )
        flash("Change order updated.", "success")
        return redirect(url_for("project_controls.view_change_order", id=change_order.id))

    return render_template(
        "project_controls/change_orders/form.html",
        form=_form_from_change_order(change_order),
        projects=projects,
        statuses=CHANGE_ORDER_STATUSES,
        change_order=change_order,
        estimate=None,
        version=None,
    )


@project_controls_bp.route("/project-controls/change-orders/<int:id>/status", methods=["POST"])
def update_status(id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    try:
        update_change_order_status(change_order, request.form.get("status", "").strip())
    except ChangeOrderServiceError as exc:
        flash(str(exc), "error")
    else:
        flash(f'Status set to "{change_order.status}".', "success")
    return redirect(url_for("project_controls.view_change_order", id=change_order.id))


@project_controls_bp.route("/project-controls/change-orders/<int:id>/items/new", methods=["POST"])
def add_item(id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    try:
        add_change_order_item(
            change_order,
            description=request.form.get("description", ""),
            quantity=request.form.get("quantity") or 1,
            unit=request.form.get("unit") or "ea",
            unit_price=request.form.get("unit_price") or 0,
        )
    except ChangeOrderServiceError as exc:
        flash(str(exc), "error")
    else:
        flash("Line item added.", "success")
    return redirect(
        url_for("project_controls.view_change_order", id=change_order.id, tab="items")
    )


@project_controls_bp.route(
    "/project-controls/change-orders/<int:id>/items/<int:item_id>/edit",
    methods=["POST"],
)
def edit_item(id, item_id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    item = ChangeOrderItem.query.filter_by(
        id=item_id,
        change_order_id=change_order.id,
    ).first_or_404()
    try:
        update_change_order_item(
            item,
            description=request.form.get("description"),
            quantity=request.form.get("quantity"),
            unit=request.form.get("unit"),
            unit_price=request.form.get("unit_price"),
        )
    except ChangeOrderServiceError as exc:
        flash(str(exc), "error")
        return render_template(
            "project_controls/change_orders/detail.html",
            change_order=change_order,
            tab="items",
            statuses=CHANGE_ORDER_STATUSES,
            editing_item_id=item.id,
            item_edit_form={
                "description": request.form.get("description", ""),
                "quantity": request.form.get("quantity", ""),
                "unit": request.form.get("unit", ""),
                "unit_price": request.form.get("unit_price", ""),
            },
        )
    flash("Line item updated.", "success")
    return redirect(
        url_for("project_controls.view_change_order", id=change_order.id, tab="items")
    )


@project_controls_bp.route(
    "/project-controls/change-orders/<int:id>/items/<int:item_id>/delete",
    methods=["POST"],
)
def delete_item(id, item_id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    item = ChangeOrderItem.query.filter_by(
        id=item_id,
        change_order_id=change_order.id,
    ).first_or_404()
    delete_change_order_item(item)
    flash("Line item deleted.", "success")
    return redirect(
        url_for("project_controls.view_change_order", id=change_order.id, tab="items")
    )


@project_controls_bp.route("/project-controls/change-orders/<int:id>/pdf")
def download_change_order_pdf(id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    pdf_buffer = generate_change_order_pdf(change_order)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=sanitize_change_order_filename(change_order),
    )
