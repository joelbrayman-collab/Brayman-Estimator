from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Client
from app.services.organizations import get_current_organization_id

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")

_CLIENT_FIELDS = ("name", "company", "email", "phone", "address", "notes")


def _posted_client_fields():
    return {
        field: request.form.get(field, "").strip()
        for field in _CLIENT_FIELDS
    }


def _stored_client_fields(client):
    return {
        field: (getattr(client, field) or "").strip()
        for field in _CLIENT_FIELDS
    }


def _apply_client_fields(client, fields):
    for field in _CLIENT_FIELDS:
        setattr(client, field, fields[field])


@clients_bp.route("/")
def list_clients():
    org_id = get_current_organization_id()
    clients = Client.query.filter_by(organization_id=org_id).order_by(Client.name.asc()).all()
    return render_template("clients/list.html", clients=clients)


@clients_bp.route("/new", methods=["GET", "POST"])
def create_client():
    if request.method == "POST":
        fields = _posted_client_fields()
        if not fields["name"]:
            flash("Client name is required.", "error")
            return render_template("clients/form.html", form=fields)

        client = Client(organization_id=get_current_organization_id())
        _apply_client_fields(client, fields)
        db.session.add(client)
        db.session.commit()

        flash("Client created successfully.", "success")
        return redirect(url_for("clients.list_clients"))

    return render_template("clients/form.html", form={})


@clients_bp.route("/<int:client_id>", methods=["GET", "POST"])
def edit_client(client_id):
    client = Client.query.filter_by(
        id=client_id,
        organization_id=get_current_organization_id(),
    ).first_or_404()

    if request.method == "POST":
        fields = _posted_client_fields()
        if not fields["name"]:
            flash("Client name is required.", "error")
            return render_template("clients/form.html", client=client, form=fields)

        _apply_client_fields(client, fields)
        db.session.commit()
        flash("Client updated successfully.", "success")
        return redirect(url_for("clients.list_clients"))

    return render_template(
        "clients/form.html",
        client=client,
        form=_stored_client_fields(client),
    )
