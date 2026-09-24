from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
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
from app.services.shared_api import get_organization_project
from app.services.signing import overlay_for_change_order, overlays_for_change_orders
from app.project_controls.services import (
    ChangeOrderServiceError,
    add_change_order_item,
    create_change_order,
    delete_change_order_item,
    form_approved_internal_direct_cost,
    update_change_order,
    update_change_order_item,
    update_change_order_status,
)
from app.services.work_scope import change_order_is_extra_work

CHANGE_ORDER_PROJECT_MISMATCH = "That project is not the project for this change order."

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


def _operating_project_id():
    return request.args.get("project_id", type=int)


def _next_view():
    return (request.args.get("next") or request.form.get("next") or "").strip()


def _change_order_cancel_url(*, operating_project_id=None, next_view=""):
    if next_view == "hub" and operating_project_id:
        return url_for("projects.view_project", id=operating_project_id)
    if operating_project_id:
        return url_for(
            "project_controls.list_change_orders", project_id=operating_project_id
        )
    return url_for("project_controls.list_change_orders")


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
        "approved_internal_direct_cost": (
            ""
            if change_order.approved_internal_direct_cost is None
            else f"{change_order.approved_internal_direct_cost:.2f}"
        ),
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
    signing_overlays = overlays_for_change_orders(
        get_current_organization_id(), [row.id for row in change_orders]
    )
    return render_template(
        "project_controls/change_orders/list.html",
        change_orders=change_orders,
        signing_overlays=signing_overlays,
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


def _render_change_order_form(
    *,
    form,
    projects,
    extra_work_activity_id=None,
    change_order=None,
    estimate=None,
    version=None,
    operating_project_id=None,
    lock_project=False,
    next_view="",
):
    return render_template(
        "project_controls/change_orders/form.html",
        form=form,
        projects=projects,
        statuses=CHANGE_ORDER_STATUSES,
        change_order=change_order,
        estimate=estimate,
        version=version,
        extra_work_activity_id=extra_work_activity_id,
        operating_project_id=operating_project_id,
        lock_project=lock_project,
        next_view=next_view,
        is_extra_work=(
            extra_work_activity_id is not None
            or (
                change_order is not None
                and change_order_is_extra_work(change_order)
            )
        ),
        approved_internal_cost_frozen=(
            change_order is not None
            and change_order.status in ("Approved", "Invoiced")
        ),
        cancel_url=_change_order_cancel_url(
            operating_project_id=operating_project_id,
            next_view=next_view,
        ),
    )


@project_controls_bp.route("/project-controls/change-orders/new", methods=["GET", "POST"])
def create_change_order_route():
    org_id = get_current_organization_id()
    projects = Project.query.filter_by(organization_id=org_id).order_by(Project.name).all()
    if not projects:
        flash("Create a project before adding a change order.", "error")
        return redirect(url_for("projects.create_project"))

    operating_project_id = _operating_project_id()
    next_view = _next_view()
    bound_project = (
        get_organization_project(org_id, operating_project_id)
        if operating_project_id
        else None
    )
    extra_work_activity_id = request.args.get("extra_work_activity_id", type=int) or request.form.get(
        "extra_work_activity_id", type=int
    )
    lock_project = bound_project is not None

    if request.method == "POST":
        from flask_login import current_user

        from app.services.work_scope import (
            WorkScopeError,
            actor_name,
            create_change_order_from_extra_work,
        )

        posted_id = request.form.get("project_id", type=int)
        try:
            if operating_project_id:
                if bound_project is None:
                    raise ChangeOrderServiceError("Project not found.")
                if posted_id != bound_project.id:
                    raise ChangeOrderServiceError(CHANGE_ORDER_PROJECT_MISMATCH)
                project = bound_project
            else:
                project = get_organization_project(org_id, posted_id) if posted_id else None
            if extra_work_activity_id:
                change_order, _linked = create_change_order_from_extra_work(
                    project_work_activity_id=extra_work_activity_id,
                    title=request.form.get("title", ""),
                    description=request.form.get("description", ""),
                    reason=request.form.get("reason", ""),
                    requested_by=form_actor("requested_by"),
                    requested_date=_parse_date(request.form.get("requested_date")),
                    markup_percent=request.form.get("markup_percent") or 0,
                    tax_percent=request.form.get("tax_percent") or 0,
                    notes=request.form.get("notes", ""),
                    status=request.form.get("status") or "Draft",
                    actor_user_id=getattr(current_user, "id", None),
                    actor_display_name=actor_name(current_user),
                    organization_id=org_id,
                    project=project,
                    link_reason="Extra work linked when the change order was created.",
                    approved_internal_direct_cost=form_approved_internal_direct_cost(
                        request.form
                    ),
                )
            else:
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
                    organization_id=org_id,
                )
        except (ChangeOrderServiceError, WorkScopeError, ValueError) as exc:
            flash(str(exc), "error")
            return _render_change_order_form(
                form=request.form,
                projects=projects,
                extra_work_activity_id=extra_work_activity_id,
                operating_project_id=operating_project_id if bound_project else None,
                lock_project=lock_project,
                next_view=next_view,
            )

        flash("Change order created.", "success")
        detail_kwargs = {"id": change_order.id}
        if next_view == "hub":
            detail_kwargs["next"] = "hub"
        return redirect(url_for("project_controls.view_change_order", **detail_kwargs))

    form = {
        "title": "",
        "description": "",
        "reason": "",
        "status": "Draft",
        "requested_by": "",
        "requested_date": datetime.utcnow().date().isoformat(),
        "project_id": str(bound_project.id) if bound_project else "",
        "markup_percent": "0.00",
        "tax_percent": "0.00",
        "notes": "",
    }
    return _render_change_order_form(
        form=form,
        projects=projects,
        extra_work_activity_id=extra_work_activity_id,
        operating_project_id=operating_project_id if bound_project else None,
        lock_project=lock_project,
        next_view=next_view,
    )


@project_controls_bp.route(
    "/estimates/<int:estimate_id>/versions/<int:version_id>/change-orders/new",
    methods=["GET", "POST"],
)
def create_from_estimate_version(estimate_id, version_id):
    org_id = get_current_organization_id()
    estimate = (
        Estimate.query.join(Project, Estimate.project_id == Project.id)
        .filter(Estimate.id == estimate_id, Project.organization_id == org_id)
        .first_or_404()
    )
    version = EstimateVersion.query.filter_by(
        id=version_id,
        estimate_id=estimate.id,
    ).first_or_404()
    project = estimate.project
    projects = Project.query.filter_by(organization_id=org_id).order_by(Project.name).all()

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
                organization_id=org_id,
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

    organization_id = getattr(g, "organization_id", None) or get_current_organization_id()
    signing_overlay = overlay_for_change_order(change_order.id, organization_id)
    invitation_url = ""
    if (
        signing_overlay.request_id
        and session.get("signing_invitation_request_id") == signing_overlay.request_id
    ):
        invitation_url = session.get("signing_invitation_url") or ""

    next_view = _next_view()
    return render_template(
        "project_controls/change_orders/detail.html",
        change_order=change_order,
        tab=tab,
        statuses=CHANGE_ORDER_STATUSES,
        editing_item_id=editing_item_id,
        item_edit_form=item_edit_form,
        signing_overlay=signing_overlay,
        invitation_url=invitation_url,
        extra_work=change_order_is_extra_work(change_order),
        approved_internal_cost_frozen=change_order.status in ("Approved", "Invoiced"),
        next_view=next_view,
        back_url=(
            url_for("projects.view_project", id=change_order.project_id)
            if next_view == "hub"
            else url_for("project_controls.list_change_orders")
        ),
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
                approved_internal_direct_cost=form_approved_internal_direct_cost(
                    request.form
                ),
            )
        except (ChangeOrderServiceError, ValueError) as exc:
            flash(str(exc), "error")
            return _render_change_order_form(
                form=request.form,
                projects=projects,
                change_order=change_order,
                lock_project=True,
                operating_project_id=change_order.project_id,
            )
        flash("Change order updated.", "success")
        return redirect(url_for("project_controls.view_change_order", id=change_order.id))

    return _render_change_order_form(
        form=_form_from_change_order(change_order),
        projects=projects,
        change_order=change_order,
        lock_project=True,
        operating_project_id=change_order.project_id,
    )


@project_controls_bp.route("/project-controls/change-orders/<int:id>/status", methods=["POST"])
def update_status(id):
    change_order = repo.get_change_order(id)
    if change_order is None:
        abort(404)
    try:
        update_change_order_status(
            change_order,
            request.form.get("status", "").strip(),
            approved_internal_direct_cost=form_approved_internal_direct_cost(
                request.form
            ),
        )
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
        organization_id = getattr(g, "organization_id", None) or get_current_organization_id()
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
            signing_overlay=overlay_for_change_order(change_order.id, organization_id),
            invitation_url="",
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
