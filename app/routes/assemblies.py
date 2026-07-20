from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Assembly, AssemblyItem, CostItem

assemblies_bp = Blueprint("assemblies", __name__, url_prefix="/assemblies")


def _parse_decimal(value, field_label, required=True):
    if value == "":
        if required:
            return None, f"{field_label} is required."
        return Decimal("0"), None

    try:
        return Decimal(value), None
    except InvalidOperation:
        return None, f"{field_label} must be a valid number."


def _parse_int(value, field_label, default=0):
    if value == "":
        return default, None

    try:
        return int(value), None
    except (TypeError, ValueError):
        return None, f"{field_label} must be a whole number."


def _assembly_form_values(assembly=None):
    if request.method == "POST":
        return {
            "code": request.form.get("code", "").strip(),
            "name": request.form.get("name", "").strip(),
            "category": request.form.get("category", "").strip(),
            "unit": request.form.get("unit", "").strip(),
            "default_markup_percent": request.form.get(
                "default_markup_percent", "0"
            ).strip(),
            "description": request.form.get("description", "").strip(),
        }

    if assembly is None:
        return {
            "code": "",
            "name": "",
            "category": "",
            "unit": "",
            "default_markup_percent": "0",
            "description": "",
        }

    return {
        "code": assembly.code or "",
        "name": assembly.name or "",
        "category": assembly.category or "",
        "unit": assembly.unit or "",
        "default_markup_percent": f"{assembly.default_markup_percent:.2f}",
        "description": assembly.description or "",
    }


def _component_form_values(assembly_item=None):
    if request.method == "POST":
        return {
            "cost_item_id": request.form.get("cost_item_id", "").strip(),
            "quantity": request.form.get("quantity", "").strip(),
            "waste_percent": request.form.get("waste_percent", "0").strip(),
            "notes": request.form.get("notes", "").strip(),
            "sort_order": request.form.get("sort_order", "0").strip(),
        }

    if assembly_item is None:
        return {
            "cost_item_id": "",
            "quantity": "",
            "waste_percent": "0",
            "notes": "",
            "sort_order": "0",
        }

    return {
        "cost_item_id": str(assembly_item.cost_item_id),
        "quantity": f"{assembly_item.quantity}",
        "waste_percent": f"{assembly_item.waste_percent:.2f}",
        "notes": assembly_item.notes or "",
        "sort_order": str(assembly_item.sort_order),
    }


def _code_exists(code, exclude_id=None):
    query = Assembly.query.filter_by(code=code)
    if exclude_id is not None:
        query = query.filter(Assembly.id != exclude_id)
    return query.first() is not None


def _validate_assembly_form(form, exclude_id=None):
    errors = []

    if not form["code"]:
        errors.append("Assembly code is required.")
    if not form["name"]:
        errors.append("Assembly name is required.")
    if not form["category"]:
        errors.append("Category is required.")
    if not form["unit"]:
        errors.append("Unit is required.")

    markup_raw = form["default_markup_percent"] or "0"
    markup, markup_error = _parse_decimal(markup_raw, "Default markup percent")
    if markup_error:
        errors.append(markup_error)

    if form["code"] and _code_exists(form["code"], exclude_id=exclude_id):
        errors.append(f'An assembly with code "{form["code"]}" already exists.')

    return errors, markup


def _validate_component_form(form, require_cost_item=True):
    errors = []
    cost_item = None

    if require_cost_item:
        if not form["cost_item_id"]:
            errors.append("Cost item is required.")
        else:
            try:
                cost_item_id = int(form["cost_item_id"])
            except (TypeError, ValueError):
                errors.append("Select a valid cost item.")
            else:
                cost_item = CostItem.query.filter_by(
                    id=cost_item_id,
                    is_active=True,
                ).first()
                if cost_item is None:
                    errors.append("Select an active cost item.")

    quantity, quantity_error = _parse_decimal(form["quantity"], "Quantity")
    if quantity_error:
        errors.append(quantity_error)

    waste_raw = form["waste_percent"] or "0"
    waste, waste_error = _parse_decimal(waste_raw, "Waste percent")
    if waste_error:
        errors.append(waste_error)

    sort_order, sort_error = _parse_int(form["sort_order"], "Sort order", default=0)
    if sort_error:
        errors.append(sort_error)

    return errors, cost_item, quantity, waste, sort_order


def _active_cost_items():
    return CostItem.query.filter_by(is_active=True).order_by(CostItem.code.asc()).all()


@assemblies_bp.route("/")
def list_assemblies():
    assemblies = Assembly.query.order_by(Assembly.code.asc()).all()
    return render_template("assemblies/list.html", assemblies=assemblies)


@assemblies_bp.route("/new", methods=["GET", "POST"])
def create_assembly():
    form = _assembly_form_values()

    if request.method == "POST":
        errors, markup = _validate_assembly_form(form)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "assemblies/form.html",
                form=form,
                assembly=None,
            )

        assembly = Assembly(
            code=form["code"],
            name=form["name"],
            category=form["category"],
            unit=form["unit"],
            default_markup_percent=markup,
            description=form["description"] or None,
            is_active=True,
        )

        db.session.add(assembly)
        db.session.commit()

        flash("Assembly created successfully. Add component cost items below.", "success")
        return redirect(url_for("assemblies.view_assembly", id=assembly.id))

    return render_template(
        "assemblies/form.html",
        form=form,
        assembly=None,
    )


@assemblies_bp.route("/<int:id>")
def view_assembly(id):
    assembly = Assembly.query.get_or_404(id)
    editing_item_id = request.args.get("edit_item", type=int)
    edit_form = None

    if editing_item_id is not None:
        editing_item = AssemblyItem.query.filter_by(
            id=editing_item_id,
            assembly_id=assembly.id,
        ).first()
        if editing_item is not None:
            edit_form = _component_form_values(editing_item)
        else:
            editing_item_id = None

    return render_template(
        "assemblies/detail.html",
        assembly=assembly,
        cost_items=_active_cost_items(),
        add_form=_component_form_values(),
        editing_item_id=editing_item_id,
        edit_form=edit_form,
    )


@assemblies_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_assembly(id):
    assembly = Assembly.query.get_or_404(id)
    form = _assembly_form_values(assembly)

    if request.method == "POST":
        errors, markup = _validate_assembly_form(form, exclude_id=assembly.id)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "assemblies/form.html",
                form=form,
                assembly=assembly,
            )

        assembly.code = form["code"]
        assembly.name = form["name"]
        assembly.category = form["category"]
        assembly.unit = form["unit"]
        assembly.default_markup_percent = markup
        assembly.description = form["description"] or None

        db.session.commit()

        flash("Assembly updated successfully.", "success")
        return redirect(url_for("assemblies.view_assembly", id=assembly.id))

    return render_template(
        "assemblies/form.html",
        form=form,
        assembly=assembly,
    )


@assemblies_bp.route("/<int:id>/toggle-active", methods=["POST"])
def toggle_assembly_active(id):
    assembly = Assembly.query.get_or_404(id)
    assembly.is_active = not assembly.is_active
    db.session.commit()

    state = "activated" if assembly.is_active else "deactivated"
    flash(f'Assembly "{assembly.code}" {state}.', "success")
    return redirect(url_for("assemblies.list_assemblies"))


@assemblies_bp.route("/<int:id>/items/add", methods=["POST"])
def add_assembly_item(id):
    assembly = Assembly.query.get_or_404(id)
    form = _component_form_values()
    errors, cost_item, quantity, waste, sort_order = _validate_component_form(form)

    if errors:
        for error in errors:
            flash(error, "error")
        return render_template(
            "assemblies/detail.html",
            assembly=assembly,
            cost_items=_active_cost_items(),
            add_form=form,
            editing_item_id=None,
            edit_form=None,
        )

    assembly_item = AssemblyItem(
        assembly_id=assembly.id,
        cost_item_id=cost_item.id,
        quantity=quantity,
        waste_percent=waste,
        notes=form["notes"] or None,
        sort_order=sort_order,
    )

    db.session.add(assembly_item)
    db.session.commit()

    flash("Component added to assembly.", "success")
    return redirect(url_for("assemblies.view_assembly", id=assembly.id))


@assemblies_bp.route("/<int:id>/items/<int:item_id>/edit", methods=["POST"])
def edit_assembly_item(id, item_id):
    assembly = Assembly.query.get_or_404(id)
    assembly_item = AssemblyItem.query.filter_by(
        id=item_id,
        assembly_id=assembly.id,
    ).first_or_404()

    form = _component_form_values()
    # Keep the existing cost item; only quantity/waste/notes/sort are edited.
    form["cost_item_id"] = str(assembly_item.cost_item_id)
    errors, _cost_item, quantity, waste, sort_order = _validate_component_form(
        form,
        require_cost_item=False,
    )

    if errors:
        for error in errors:
            flash(error, "error")
        return render_template(
            "assemblies/detail.html",
            assembly=assembly,
            cost_items=_active_cost_items(),
            add_form=_component_form_values(),
            editing_item_id=assembly_item.id,
            edit_form=form,
        )

    assembly_item.quantity = quantity
    assembly_item.waste_percent = waste
    assembly_item.notes = form["notes"] or None
    assembly_item.sort_order = sort_order

    db.session.commit()

    flash("Component updated.", "success")
    return redirect(url_for("assemblies.view_assembly", id=assembly.id))


@assemblies_bp.route("/<int:id>/items/<int:item_id>/delete", methods=["POST"])
def delete_assembly_item(id, item_id):
    assembly = Assembly.query.get_or_404(id)
    assembly_item = AssemblyItem.query.filter_by(
        id=item_id,
        assembly_id=assembly.id,
    ).first_or_404()

    db.session.delete(assembly_item)
    db.session.commit()

    flash("Component removed from assembly.", "success")
    return redirect(url_for("assemblies.view_assembly", id=assembly.id))
