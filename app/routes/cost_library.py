from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import CostItem
from app.models.cost_item import COST_ITEM_CATEGORIES

cost_library_bp = Blueprint("cost_library", __name__, url_prefix="/cost-library")


def _form_values(cost_item=None):
    if request.method == "POST":
        return {
            "code": request.form.get("code", "").strip(),
            "name": request.form.get("name", "").strip(),
            "category": request.form.get("category", "").strip(),
            "unit": request.form.get("unit", "").strip(),
            "unit_cost": request.form.get("unit_cost", "").strip(),
            "default_markup_percent": request.form.get(
                "default_markup_percent", "0"
            ).strip(),
            "supplier": request.form.get("supplier", "").strip(),
            "description": request.form.get("description", "").strip(),
        }

    if cost_item is None:
        return {
            "code": "",
            "name": "",
            "category": "",
            "unit": "",
            "unit_cost": "",
            "default_markup_percent": "0",
            "supplier": "",
            "description": "",
        }

    return {
        "code": cost_item.code or "",
        "name": cost_item.name or "",
        "category": cost_item.category or "",
        "unit": cost_item.unit or "",
        "unit_cost": f"{cost_item.unit_cost:.2f}",
        "default_markup_percent": f"{cost_item.default_markup_percent:.2f}",
        "supplier": cost_item.supplier or "",
        "description": cost_item.description or "",
    }


def _parse_decimal(value, field_label):
    if value == "":
        return None, f"{field_label} is required."

    try:
        return Decimal(value), None
    except InvalidOperation:
        return None, f"{field_label} must be a valid number."


def _code_exists(code, exclude_id=None):
    query = CostItem.query.filter_by(code=code)
    if exclude_id is not None:
        query = query.filter(CostItem.id != exclude_id)
    return query.first() is not None


def _validate_cost_item_form(form, exclude_id=None):
    errors = []

    if not form["code"]:
        errors.append("Cost item code is required.")
    if not form["name"]:
        errors.append("Item name is required.")
    if not form["category"]:
        errors.append("Category is required.")
    elif form["category"] not in COST_ITEM_CATEGORIES:
        errors.append("Select a valid category.")
    if not form["unit"]:
        errors.append("Unit is required.")

    unit_cost, unit_cost_error = _parse_decimal(form["unit_cost"], "Unit cost")
    if unit_cost_error:
        errors.append(unit_cost_error)

    markup_raw = form["default_markup_percent"] or "0"
    markup, markup_error = _parse_decimal(markup_raw, "Default markup percent")
    if markup_error:
        errors.append(markup_error)

    if form["code"] and _code_exists(form["code"], exclude_id=exclude_id):
        errors.append(f'A cost item with code "{form["code"]}" already exists.')

    return errors, unit_cost, markup


@cost_library_bp.route("/")
def list_cost_items():
    cost_items = CostItem.query.order_by(CostItem.code.asc()).all()
    return render_template("cost_library/list.html", cost_items=cost_items)


@cost_library_bp.route("/new", methods=["GET", "POST"])
def create_cost_item():
    form = _form_values()

    if request.method == "POST":
        errors, unit_cost, markup = _validate_cost_item_form(form)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "cost_library/form.html",
                form=form,
                categories=COST_ITEM_CATEGORIES,
                cost_item=None,
            )

        cost_item = CostItem(
            code=form["code"],
            name=form["name"],
            category=form["category"],
            unit=form["unit"],
            unit_cost=unit_cost,
            default_markup_percent=markup,
            supplier=form["supplier"] or None,
            description=form["description"] or None,
            is_active=True,
        )

        db.session.add(cost_item)
        db.session.commit()

        flash("Cost item created successfully.", "success")
        return redirect(url_for("cost_library.list_cost_items"))

    return render_template(
        "cost_library/form.html",
        form=form,
        categories=COST_ITEM_CATEGORIES,
        cost_item=None,
    )


@cost_library_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_cost_item(id):
    cost_item = CostItem.query.get_or_404(id)
    form = _form_values(cost_item)

    if request.method == "POST":
        errors, unit_cost, markup = _validate_cost_item_form(
            form,
            exclude_id=cost_item.id,
        )

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "cost_library/form.html",
                form=form,
                categories=COST_ITEM_CATEGORIES,
                cost_item=cost_item,
            )

        cost_item.code = form["code"]
        cost_item.name = form["name"]
        cost_item.category = form["category"]
        cost_item.unit = form["unit"]
        cost_item.unit_cost = unit_cost
        cost_item.default_markup_percent = markup
        cost_item.supplier = form["supplier"] or None
        cost_item.description = form["description"] or None

        db.session.commit()

        flash("Cost item updated successfully.", "success")
        return redirect(url_for("cost_library.list_cost_items"))

    return render_template(
        "cost_library/form.html",
        form=form,
        categories=COST_ITEM_CATEGORIES,
        cost_item=cost_item,
    )


@cost_library_bp.route("/<int:id>/toggle-active", methods=["POST"])
def toggle_cost_item_active(id):
    cost_item = CostItem.query.get_or_404(id)
    cost_item.is_active = not cost_item.is_active
    db.session.commit()

    state = "activated" if cost_item.is_active else "deactivated"
    flash(f'Cost item "{cost_item.code}" {state}.', "success")
    return redirect(url_for("cost_library.list_cost_items"))
