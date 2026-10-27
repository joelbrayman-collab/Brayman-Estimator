import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Client
from app.services.organizations import get_current_organization_id

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


def _options(**extra):
    from app.services.clients import form_options

    return {**form_options(), **extra}


_BACK_TO = re.compile(r"^/(?:|operations/attention|projects/\d+)$")


def _return_to():
    """A page that sent the person here (Attention's "Complete information", a project, a wizard step) and wants
    them back after Save. Only these paths on this site are accepted."""
    from app.services.return_path import guided_return_path

    raw = (request.values.get("return_to") or "").strip()
    wizard_or_guided = guided_return_path(raw)
    if wizard_or_guided:
        return wizard_or_guided
    if raw.startswith("//") or "\\" in raw or "://" in raw:
        return None
    path = raw.split("#", 1)[0].split("?", 1)[0]
    return path if _BACK_TO.match(path) else None


@clients_bp.route("/")
def list_clients():
    org_id = get_current_organization_id()
    from app.services.time_entry import customer_clients_only  # the own-company record is not a customer

    clients = customer_clients_only(Client.query.filter_by(organization_id=org_id), org_id).order_by(Client.name.asc()).all()
    return render_template("clients/list.html", clients=clients)


@clients_bp.route("/new", methods=["GET", "POST"])
def create_client():
    from app.services import clients as C

    if request.method == "POST":
        fields = C.fields_from_form(request.form)
        try:
            client = C.create_client(get_current_organization_id(), fields)
        except C.ClientError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("clients/form.html", form=fields, return_to=_return_to(), **_options())
        missing = C.missing_information(client)
        flash("Client created successfully." + (f" Still to add: {', '.join(missing).lower()} (listed under What needs my "
                                   "attention)." if missing else ""), "success")
        return redirect(_return_to() or url_for("clients.list_clients"))

    return render_template("clients/form.html", form={}, return_to=_return_to(), **_options())


@clients_bp.route("/<int:client_id>", methods=["GET", "POST"])
def edit_client(client_id):
    from app.services import clients as C

    client = Client.query.filter_by(
        id=client_id,
        organization_id=get_current_organization_id(),
    ).first_or_404()

    if request.method == "POST":
        fields = C.fields_from_form(request.form)
        try:
            C.update_client(client, fields)
        except C.ClientError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("clients/form.html", client=client, form=fields, return_to=_return_to(),
                                   missing=C.missing_information(client), **_options())
        missing = C.missing_information(client)
        flash("Client updated successfully." + (f" Still to add: {', '.join(missing).lower()}." if missing else ""), "success")
        return redirect(_return_to() or url_for("clients.list_clients"))

    return render_template(
        "clients/form.html",
        client=client,
        form=C.stored_fields(client),
        missing=C.missing_information(client),
        return_to=_return_to(),
        **_options(),
    )
