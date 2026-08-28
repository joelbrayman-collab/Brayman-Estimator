from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Client
from app.services.organizations import get_current_organization_id

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.route("/")
def list_clients():
    org_id = get_current_organization_id()
    clients = Client.query.filter_by(organization_id=org_id).order_by(Client.name.asc()).all()
    return render_template("clients/list.html", clients=clients)


@clients_bp.route("/new", methods=["GET", "POST"])
def create_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("Client name is required.", "error")
            return render_template("clients/form.html")

        client = Client(
            organization_id=get_current_organization_id(),
            name=name,
            company=request.form.get("company", "").strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
            address=request.form.get("address", "").strip(),
            notes=request.form.get("notes", "").strip(),
        )

        db.session.add(client)
        db.session.commit()

        flash("Client created successfully.", "success")
        return redirect(url_for("clients.list_clients"))

    return render_template("clients/form.html")
