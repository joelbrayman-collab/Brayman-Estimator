from decimal import ROUND_HALF_UP, Decimal

from app import db
from app.models.assembly import Assembly
from app.models.cost_item import CostItem
from app.models.estimate import (
    EstimateLineItem,
    EstimateSection,
    EstimateVersion,
)
from app.services.estimates import EstimateServiceError, ensure_version_editable

MONEY = Decimal("0.01")
HUNDRED = Decimal("100")


def as_money(value):
    return Decimal(value or 0).quantize(MONEY, rounding=ROUND_HALF_UP)


def as_decimal(value, default="0"):
    if value is None or value == "":
        return Decimal(default)
    return Decimal(value)


def calculate_extended_cost(quantity, unit_cost, waste_percent):
    quantity = as_decimal(quantity)
    unit_cost = as_decimal(unit_cost)
    waste_percent = as_decimal(waste_percent)
    return quantity * unit_cost * (Decimal("1") + waste_percent / HUNDRED)


def calculate_sell_price(extended_cost, markup_percent):
    extended_cost = as_decimal(extended_cost)
    markup_percent = as_decimal(markup_percent)
    return extended_cost * (Decimal("1") + markup_percent / HUNDRED)


def apply_line_item_calculations(line_item):
    extended = calculate_extended_cost(
        line_item.quantity,
        line_item.unit_cost,
        line_item.waste_percent,
    )
    sell = calculate_sell_price(extended, line_item.markup_percent)
    line_item.extended_cost = as_money(extended)
    line_item.sell_price = as_money(sell)
    return line_item


def recalculate_section(section):
    total = Decimal("0")
    line_items = (
        EstimateLineItem.query.filter_by(estimate_section_id=section.id)
        .order_by(EstimateLineItem.sort_order.asc(), EstimateLineItem.id.asc())
        .all()
    )
    for line_item in line_items:
        apply_line_item_calculations(line_item)
        total += Decimal(line_item.sell_price or 0)
    section.subtotal = as_money(total)
    return section


def recalculate_version(version):
    from app.models.pricing_engine import EstimatePricingSnapshot
    from app.services.pricing_engine import refresh_version_from_snapshot

    sections = (
        EstimateSection.query.filter_by(estimate_version_id=version.id)
        .order_by(EstimateSection.sort_order.asc(), EstimateSection.id.asc())
        .all()
    )
    for section in sections:
        recalculate_section(section)

    snapshot = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).first()
    if snapshot is not None:
        return refresh_version_from_snapshot(version)

    subtotal = Decimal("0")
    for section in sections:
        subtotal += Decimal(section.subtotal or 0)

    version.subtotal = as_money(subtotal)
    overhead_percent = as_decimal(version.overhead_percent)
    profit_percent = as_decimal(version.profit_percent)
    tax_percent = as_decimal(version.tax_percent)

    overhead_amount = as_money(version.subtotal * overhead_percent / HUNDRED)
    profit_amount = as_money(
        (version.subtotal + overhead_amount) * profit_percent / HUNDRED
    )
    taxable_amount = version.subtotal + overhead_amount + profit_amount
    tax_amount = as_money(taxable_amount * tax_percent / HUNDRED)
    version.total = as_money(taxable_amount + tax_amount)
    return version


def _next_section_sort_order(version):
    if not version.sections:
        return 0
    return max(section.sort_order for section in version.sections) + 1


def _next_line_sort_order(section):
    if not section.line_items:
        return 0
    return max(item.sort_order for item in section.line_items) + 1


def create_section(version, *, name, description=None, sort_order=None):
    ensure_version_editable(version)
    name = (name or "").strip()
    if not name:
        raise EstimateServiceError("Section name is required.")

    section = EstimateSection(
        estimate_version_id=version.id,
        name=name,
        description=(description or "").strip() or None,
        sort_order=_next_section_sort_order(version)
        if sort_order is None
        else int(sort_order),
        subtotal=Decimal("0"),
    )
    db.session.add(section)
    db.session.flush()
    recalculate_version(version)
    db.session.commit()
    return section


def update_section(section, *, name, description=None):
    version = section.estimate_version
    ensure_version_editable(version)
    name = (name or "").strip()
    if not name:
        raise EstimateServiceError("Section name is required.")

    section.name = name
    section.description = (description or "").strip() or None
    db.session.commit()
    return section


def delete_section(section):
    version = section.estimate_version
    ensure_version_editable(version)
    db.session.delete(section)
    db.session.flush()
    recalculate_version(version)
    db.session.commit()


def reorder_section(section, direction):
    version = section.estimate_version
    ensure_version_editable(version)
    sections = list(version.sections)
    index = next((i for i, item in enumerate(sections) if item.id == section.id), None)
    if index is None:
        raise EstimateServiceError("Section not found on this version.")

    swap_with = index - 1 if direction == "up" else index + 1
    if swap_with < 0 or swap_with >= len(sections):
        return section

    other = sections[swap_with]
    section.sort_order, other.sort_order = other.sort_order, section.sort_order
    db.session.commit()
    return section


def _validate_non_negative(value, label):
    amount = as_decimal(value)
    if amount < 0:
        raise EstimateServiceError(f"{label} cannot be negative.")
    return amount


def add_cost_item_line(section, *, cost_item_id, quantity=1, waste_percent=0, notes=None):
    version = section.estimate_version
    ensure_version_editable(version)

    cost_item = CostItem.query.filter_by(id=cost_item_id, is_active=True).first()
    if cost_item is None:
        raise EstimateServiceError("Select an active cost item.")

    quantity = _validate_non_negative(quantity, "Quantity")
    waste_percent = _validate_non_negative(waste_percent, "Waste percent")

    line_item = EstimateLineItem(
        estimate_section_id=section.id,
        line_type="Cost Item",
        cost_item_id=cost_item.id,
        assembly_id=None,
        code=cost_item.code,
        description=cost_item.name,
        quantity=quantity,
        unit=cost_item.unit,
        unit_cost=as_decimal(cost_item.unit_cost),
        waste_percent=waste_percent,
        markup_percent=as_decimal(cost_item.default_markup_percent),
        notes=(notes or "").strip() or None,
        sort_order=_next_line_sort_order(section),
    )
    apply_line_item_calculations(line_item)
    db.session.add(line_item)
    db.session.flush()
    recalculate_version(version)
    db.session.commit()
    return line_item


def add_assembly_line(section, *, assembly_id, quantity=1, waste_percent=0, notes=None):
    version = section.estimate_version
    ensure_version_editable(version)

    assembly = Assembly.query.filter_by(id=assembly_id, is_active=True).first()
    if assembly is None:
        raise EstimateServiceError("Select an active assembly.")

    quantity = _validate_non_negative(quantity, "Quantity")
    waste_percent = _validate_non_negative(waste_percent, "Waste percent")

    line_item = EstimateLineItem(
        estimate_section_id=section.id,
        line_type="Assembly",
        cost_item_id=None,
        assembly_id=assembly.id,
        code=assembly.code,
        description=assembly.name,
        quantity=quantity,
        unit=assembly.unit,
        unit_cost=as_decimal(assembly.base_unit_cost),
        waste_percent=waste_percent,
        markup_percent=as_decimal(assembly.default_markup_percent),
        notes=(notes or "").strip() or None,
        sort_order=_next_line_sort_order(section),
    )
    apply_line_item_calculations(line_item)
    db.session.add(line_item)
    db.session.flush()
    recalculate_version(version)
    db.session.commit()
    return line_item


def add_manual_line(
    section,
    *,
    line_type,
    description,
    quantity=1,
    unit,
    unit_cost=0,
    waste_percent=0,
    markup_percent=0,
    code=None,
    notes=None,
):
    version = section.estimate_version
    ensure_version_editable(version)

    if line_type not in ("Custom", "Allowance"):
        raise EstimateServiceError("Invalid line type.")

    description = (description or "").strip()
    unit = (unit or "").strip()
    if not description:
        raise EstimateServiceError("Description is required.")
    if not unit:
        raise EstimateServiceError("Unit is required.")

    quantity = _validate_non_negative(quantity, "Quantity")
    unit_cost = _validate_non_negative(unit_cost, "Unit cost")
    waste_percent = _validate_non_negative(waste_percent, "Waste percent")
    markup_percent = _validate_non_negative(markup_percent, "Markup percent")

    line_item = EstimateLineItem(
        estimate_section_id=section.id,
        line_type=line_type,
        cost_item_id=None,
        assembly_id=None,
        code=(code or "").strip() or None,
        description=description,
        quantity=quantity,
        unit=unit,
        unit_cost=unit_cost,
        waste_percent=waste_percent,
        markup_percent=markup_percent,
        notes=(notes or "").strip() or None,
        sort_order=_next_line_sort_order(section),
    )
    apply_line_item_calculations(line_item)
    db.session.add(line_item)
    db.session.flush()
    recalculate_version(version)
    db.session.commit()
    return line_item


def update_line_item(
    line_item,
    *,
    description=None,
    quantity=None,
    unit=None,
    unit_cost=None,
    waste_percent=None,
    markup_percent=None,
    code=None,
    notes=None,
):
    version = line_item.section.estimate_version
    ensure_version_editable(version)

    if description is not None:
        description = description.strip()
        if not description:
            raise EstimateServiceError("Description is required.")
        line_item.description = description

    if unit is not None:
        unit = unit.strip()
        if not unit:
            raise EstimateServiceError("Unit is required.")
        line_item.unit = unit

    if quantity is not None:
        line_item.quantity = _validate_non_negative(quantity, "Quantity")
    if unit_cost is not None:
        line_item.unit_cost = _validate_non_negative(unit_cost, "Unit cost")
    if waste_percent is not None:
        line_item.waste_percent = _validate_non_negative(waste_percent, "Waste percent")
    if markup_percent is not None:
        line_item.markup_percent = _validate_non_negative(
            markup_percent,
            "Markup percent",
        )
    if code is not None:
        line_item.code = code.strip() or None
    if notes is not None:
        line_item.notes = notes.strip() or None

    apply_line_item_calculations(line_item)
    recalculate_version(version)
    db.session.commit()
    return line_item


def delete_line_item(line_item):
    version = line_item.section.estimate_version
    ensure_version_editable(version)
    db.session.delete(line_item)
    db.session.flush()
    recalculate_version(version)
    db.session.commit()


def reorder_line_item(line_item, direction):
    section = line_item.section
    version = section.estimate_version
    ensure_version_editable(version)

    items = list(section.line_items)
    index = next((i for i, item in enumerate(items) if item.id == line_item.id), None)
    if index is None:
        raise EstimateServiceError("Line item not found in this section.")

    swap_with = index - 1 if direction == "up" else index + 1
    if swap_with < 0 or swap_with >= len(items):
        return line_item

    other = items[swap_with]
    line_item.sort_order, other.sort_order = other.sort_order, line_item.sort_order
    db.session.commit()
    return line_item


def update_version_pricing(version, *, overhead_percent, profit_percent, tax_percent):
    ensure_version_editable(version)
    version.overhead_percent = _validate_non_negative(
        overhead_percent,
        "Overhead percent",
    )
    version.profit_percent = _validate_non_negative(profit_percent, "Profit percent")
    version.tax_percent = _validate_non_negative(tax_percent, "Tax percent")
    recalculate_version(version)
    db.session.commit()
    return version


def clone_sections_to_version(source_version, target_version):
    """Copy all sections and line-item snapshots onto target_version."""
    for section in source_version.sections:
        new_section = EstimateSection(
            estimate_version_id=target_version.id,
            name=section.name,
            description=section.description,
            sort_order=section.sort_order,
            subtotal=as_decimal(section.subtotal),
        )
        db.session.add(new_section)
        db.session.flush()

        for item in section.line_items:
            new_item = EstimateLineItem(
                estimate_section_id=new_section.id,
                line_type=item.line_type,
                cost_item_id=item.cost_item_id,
                assembly_id=item.assembly_id,
                code=item.code,
                description=item.description,
                quantity=as_decimal(item.quantity),
                unit=item.unit,
                unit_cost=as_decimal(item.unit_cost),
                waste_percent=as_decimal(item.waste_percent),
                markup_percent=as_decimal(item.markup_percent),
                extended_cost=as_decimal(item.extended_cost),
                sell_price=as_decimal(item.sell_price),
                notes=item.notes,
                sort_order=item.sort_order,
            )
            db.session.add(new_item)

    db.session.flush()
    recalculate_version(target_version)
