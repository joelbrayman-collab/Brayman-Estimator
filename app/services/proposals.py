from datetime import datetime
from decimal import Decimal
import re

from app import db
from app.models.estimate import Estimate, EstimateVersion
from app.models.proposal import (
    PROPOSAL_STATUSES,
    Proposal,
    ProposalLineItem,
    ProposalSection,
    ProposalTemplate,
)
from app.services.estimate_output import named_method_governs
from app.services.organizations import get_current_organization_id


class ProposalServiceError(Exception):
    """Raised when a proposal operation cannot be completed."""


ACCEPTED_PROPOSAL_LOCKED_MESSAGE = (
    "This proposal is Accepted and is locked. It cannot be edited or "
    "have its status changed. Corrections require a future void, "
    "supersede, or revision workflow that preserves this snapshot."
)


def is_proposal_immutable(proposal):
    """Return True when the proposal must not be mutated."""
    return proposal is not None and proposal.status == "Accepted"


def ensure_proposal_mutable(proposal):
    """Raise if the proposal is Accepted and therefore immutable."""
    if is_proposal_immutable(proposal):
        raise ProposalServiceError(ACCEPTED_PROPOSAL_LOCKED_MESSAGE)
    return proposal


def suggest_next_proposal_number(year=None):
    """Return the next suggested proposal number in PROP-YYYY-NNNN format."""
    year = year or datetime.utcnow().year
    prefix = f"PROP-{year}-"
    pattern = re.compile(rf"^PROP-{year}-(\d+)$", re.IGNORECASE)

    max_sequence = 0
    proposals = Proposal.query.filter(
        Proposal.proposal_number.ilike(f"{prefix}%")
    ).all()

    for proposal in proposals:
        match = pattern.match(proposal.proposal_number.strip())
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))

    return f"{prefix}{max_sequence + 1:04d}"


def get_default_template(organization_id=None):
    org_id = organization_id or get_current_organization_id()
    return ProposalTemplate.query.filter_by(organization_id=org_id, is_default=True, is_active=True).first()


def get_active_templates(organization_id=None):
    org_id = organization_id or get_current_organization_id()
    return (
        ProposalTemplate.query.filter_by(organization_id=org_id, is_active=True)
        .order_by(ProposalTemplate.name.asc())
        .all()
    )


def _clear_other_defaults(organization_id=None, exclude_id=None):
    org_id = organization_id or get_current_organization_id()
    query = ProposalTemplate.query.filter_by(organization_id=org_id, is_default=True)
    if exclude_id is not None:
        query = query.filter(ProposalTemplate.id != exclude_id)
    for template in query.all():
        template.is_default = False


def create_proposal_template(**fields):
    org_id = fields.get("organization_id") or get_current_organization_id()
    name = (fields.get("name") or "").strip()
    if not name:
        raise ProposalServiceError("Template name is required.")
    if ProposalTemplate.query.filter_by(organization_id=org_id, name=name).first():
        raise ProposalServiceError(
            f'A proposal template named "{name}" already exists.'
        )

    is_default = bool(fields.get("is_default"))
    is_active = fields.get("is_active", True)
    if is_default and not is_active:
        raise ProposalServiceError("The default template must be active.")

    if is_default:
        _clear_other_defaults(organization_id=org_id)

    template = ProposalTemplate(
        organization_id=org_id,
        name=name,
        description=(fields.get("description") or "").strip() or None,
        company_name=(fields.get("company_name") or "").strip() or None,
        company_address=(fields.get("company_address") or "").strip() or None,
        company_phone=(fields.get("company_phone") or "").strip() or None,
        company_email=(fields.get("company_email") or "").strip() or None,
        company_website=(fields.get("company_website") or "").strip() or None,
        logo_path=(fields.get("logo_path") or "").strip() or None,
        primary_color=(fields.get("primary_color") or "").strip() or None,
        accent_color=(fields.get("accent_color") or "").strip() or None,
        default_intro_text=(fields.get("default_intro_text") or "").strip() or None,
        default_scope_intro=(fields.get("default_scope_intro") or "").strip() or None,
        default_exclusions=(fields.get("default_exclusions") or "").strip() or None,
        default_clarifications=(
            fields.get("default_clarifications") or ""
        ).strip()
        or None,
        default_schedule_text=(
            fields.get("default_schedule_text") or ""
        ).strip()
        or None,
        default_payment_terms=(
            fields.get("default_payment_terms") or ""
        ).strip()
        or None,
        default_warranty_text=(
            fields.get("default_warranty_text") or ""
        ).strip()
        or None,
        default_acceptance_text=(
            fields.get("default_acceptance_text") or ""
        ).strip()
        or None,
        show_detailed_pricing=bool(fields.get("show_detailed_pricing", True)),
        show_section_totals=bool(fields.get("show_section_totals", True)),
        show_allowances=bool(fields.get("show_allowances", True)),
        show_tax=bool(fields.get("show_tax", True)),
        is_default=is_default,
        is_active=bool(is_active),
    )
    db.session.add(template)
    db.session.commit()
    return template


def update_proposal_template(template, **fields):
    name = fields.get("name")
    if name is not None:
        name = name.strip()
        if not name:
            raise ProposalServiceError("Template name is required.")
        duplicate = ProposalTemplate.query.filter(
            ProposalTemplate.organization_id == template.organization_id,
            ProposalTemplate.name == name,
            ProposalTemplate.id != template.id,
        ).first()
        if duplicate:
            raise ProposalServiceError(
                f'A proposal template named "{name}" already exists.'
            )
        template.name = name

    text_fields = (
        "description",
        "company_name",
        "company_address",
        "company_phone",
        "company_email",
        "company_website",
        "logo_path",
        "primary_color",
        "accent_color",
        "default_intro_text",
        "default_scope_intro",
        "default_exclusions",
        "default_clarifications",
        "default_schedule_text",
        "default_payment_terms",
        "default_warranty_text",
        "default_acceptance_text",
    )
    for field in text_fields:
        if field in fields:
            value = (fields.get(field) or "").strip() or None
            setattr(template, field, value)

    for field in (
        "show_detailed_pricing",
        "show_section_totals",
        "show_allowances",
        "show_tax",
        "is_active",
        "is_default",
    ):
        if field in fields:
            setattr(template, field, bool(fields[field]))

    if template.is_default and not template.is_active:
        raise ProposalServiceError("The default template must be active.")

    if template.is_default:
        _clear_other_defaults(organization_id=template.organization_id, exclude_id=template.id)

    db.session.commit()
    return template


def set_default_template(template):
    if not template.is_active:
        raise ProposalServiceError("Cannot set an inactive template as default.")
    _clear_other_defaults(organization_id=template.organization_id, exclude_id=template.id)
    template.is_default = True
    db.session.commit()
    return template


def toggle_template_active(template):
    if template.is_active and template.is_default:
        raise ProposalServiceError(
            "Cannot deactivate the default template. Set another default first."
        )
    template.is_active = not template.is_active
    db.session.commit()
    return template


def build_proposal_snapshot(estimate, version, template):
    """Return snapshot dict from estimate/version/template without persisting."""
    project = estimate.project
    client = project.client
    pricing = getattr(version, "pricing_snapshot", None)

    if named_method_governs(pricing):
        subtotal = Decimal(pricing.pre_tax_selling_price or 0)
        overhead_percent = Decimal("0")
        profit_percent = Decimal("0")
        tax_percent = Decimal(pricing.tax_percent or 0)
        overhead_amount = Decimal("0")
        profit_amount = Decimal("0")
        tax_amount = Decimal(pricing.tax_amount or 0)
        total = Decimal(pricing.customer_total or 0)
    else:
        subtotal = Decimal(version.subtotal or 0)
        overhead_percent = Decimal(version.overhead_percent or 0)
        profit_percent = Decimal(version.profit_percent or 0)
        tax_percent = Decimal(version.tax_percent or 0)
        overhead_amount = version.overhead_amount
        profit_amount = version.profit_amount
        tax_amount = version.tax_amount
        total = Decimal(version.total or 0)

    return {
        "client_name": client.name,
        "client_company": client.company,
        "client_address": client.address,
        "client_email": client.email,
        "client_phone": client.phone,
        "project_name": project.name,
        "project_address": project.address,
        "estimate_number": estimate.estimate_number,
        "estimate_version_number": version.version_number,
        "estimate_version_label": version.version_label,
        "subtotal": subtotal,
        "overhead_percent": overhead_percent,
        "profit_percent": profit_percent,
        "tax_percent": tax_percent,
        "overhead_amount": overhead_amount,
        "profit_amount": profit_amount,
        "tax_amount": tax_amount,
        "total": total,
        "intro_text": template.default_intro_text,
        "scope_intro": template.default_scope_intro,
        "exclusions": template.default_exclusions,
        "clarifications": template.default_clarifications,
        "schedule_text": template.default_schedule_text,
        "payment_terms": template.default_payment_terms,
        "warranty_text": template.default_warranty_text,
        "acceptance_text": template.default_acceptance_text,
        "show_detailed_pricing": template.show_detailed_pricing,
        "show_section_totals": template.show_section_totals,
        "show_allowances": template.show_allowances,
        "show_tax": template.show_tax,
        "title": f"{estimate.title} — Proposal",
    }


def _as_money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"))


def _as_decimal(value, default="0"):
    if value is None or value == "":
        return Decimal(default)
    return Decimal(value)


def apply_proposal_line_calculations(line_item):
    quantity = _as_decimal(line_item.quantity)
    unit_cost = _as_decimal(line_item.unit_cost)
    markup_percent = _as_decimal(line_item.markup_percent)

    extended_cost = quantity * unit_cost
    unit_price = unit_cost * (Decimal("1") + markup_percent / Decimal("100"))
    extended_price = quantity * unit_price

    line_item.extended_cost = _as_money(extended_cost)
    line_item.unit_price = unit_price.quantize(Decimal("0.0001"))
    line_item.extended_price = _as_money(extended_price)
    return line_item


def recalculate_proposal(proposal, *, allow_when_accepted=False):
    """Recalculate section and proposal totals from snapshot line items.

    ``allow_when_accepted`` is only for the initial create-time snapshot path,
    which may persist a proposal that is already marked Accepted.
    """
    if not allow_when_accepted:
        ensure_proposal_mutable(proposal)
    sections = (
        ProposalSection.query.filter_by(proposal_id=proposal.id)
        .order_by(ProposalSection.sort_order.asc(), ProposalSection.id.asc())
        .all()
    )
    subtotal = Decimal("0")
    for section in sections:
        line_items = (
            ProposalLineItem.query.filter_by(proposal_section_id=section.id)
            .order_by(
                ProposalLineItem.sort_order.asc(),
                ProposalLineItem.id.asc(),
            )
            .all()
        )
        section_total = Decimal("0")
        for line_item in line_items:
            apply_proposal_line_calculations(line_item)
            section_total += Decimal(line_item.extended_price or 0)
        section.subtotal = _as_money(section_total)
        subtotal += section.subtotal

    proposal.subtotal = _as_money(subtotal)
    overhead_percent = _as_decimal(proposal.overhead_percent)
    profit_percent = _as_decimal(proposal.profit_percent)
    tax_percent = _as_decimal(proposal.tax_percent)

    overhead_amount = _as_money(proposal.subtotal * overhead_percent / Decimal("100"))
    profit_amount = _as_money(
        (proposal.subtotal + overhead_amount) * profit_percent / Decimal("100")
    )
    tax_amount = _as_money(
        (proposal.subtotal + overhead_amount + profit_amount)
        * tax_percent
        / Decimal("100")
    )
    proposal.overhead_amount = overhead_amount
    proposal.profit_amount = profit_amount
    proposal.tax_amount = tax_amount
    proposal.total = _as_money(
        proposal.subtotal + overhead_amount + profit_amount + tax_amount
    )
    return proposal


def _apply_named_method_customer_totals(proposal, pricing_snapshot):
    """Copy frozen snapshot commercial totals. Do not restack markup/OH/profit."""
    proposal.subtotal = _as_money(pricing_snapshot.pre_tax_selling_price)
    proposal.overhead_percent = Decimal("0")
    proposal.profit_percent = Decimal("0")
    proposal.overhead_amount = Decimal("0.00")
    proposal.profit_amount = Decimal("0.00")
    proposal.tax_percent = _as_decimal(pricing_snapshot.tax_percent)
    proposal.tax_amount = _as_money(pricing_snapshot.tax_amount)
    proposal.total = _as_money(pricing_snapshot.customer_total)
    return proposal


def snapshot_estimate_version_content(proposal, version):
    """Copy estimate sections/line items into independent proposal snapshots."""
    pricing = getattr(version, "pricing_snapshot", None)
    use_named_allocation = named_method_governs(pricing)

    for section in version.sections:
        proposal_section = ProposalSection(
            proposal_id=proposal.id,
            sort_order=section.sort_order,
            name=section.name,
            description=section.description,
            subtotal=_as_decimal(section.subtotal),
        )
        db.session.add(proposal_section)
        db.session.flush()

        for item in section.line_items:
            quantity = _as_decimal(item.quantity)
            waste = _as_decimal(item.waste_percent)
            # Bake waste into unit_cost so later draft recalc stays independent.
            unit_cost = _as_decimal(item.unit_cost) * (
                Decimal("1") + waste / Decimal("100")
            )

            if use_named_allocation:
                extended_price = _as_money(item.sell_price)
                if quantity != 0:
                    unit_price = (
                        Decimal(item.sell_price or 0) / quantity
                    ).quantize(Decimal("0.0001"))
                else:
                    unit_price = _as_money(item.sell_price)
                line_item = ProposalLineItem(
                    proposal_section_id=proposal_section.id,
                    sort_order=item.sort_order,
                    source_line_item_id=item.id,
                    item_type=item.line_type,
                    description=item.description,
                    quantity=quantity,
                    unit=item.unit,
                    unit_cost=unit_cost,
                    unit_price=unit_price,
                    markup_percent=Decimal("0"),
                    extended_cost=_as_decimal(item.extended_cost),
                    extended_price=extended_price,
                    notes=item.notes,
                )
            else:
                markup = _as_decimal(item.markup_percent)
                unit_price = unit_cost * (Decimal("1") + markup / Decimal("100"))
                line_item = ProposalLineItem(
                    proposal_section_id=proposal_section.id,
                    sort_order=item.sort_order,
                    source_line_item_id=item.id,
                    item_type=item.line_type,
                    description=item.description,
                    quantity=quantity,
                    unit=item.unit,
                    unit_cost=unit_cost,
                    unit_price=unit_price,
                    markup_percent=markup,
                    extended_cost=_as_decimal(item.extended_cost),
                    extended_price=_as_decimal(item.sell_price),
                    notes=item.notes,
                )
                apply_proposal_line_calculations(line_item)
            db.session.add(line_item)

    db.session.flush()
    if use_named_allocation:
        _apply_named_method_customer_totals(proposal, pricing)
        for proposal_section in (
            ProposalSection.query.filter_by(proposal_id=proposal.id)
            .order_by(ProposalSection.sort_order.asc(), ProposalSection.id.asc())
            .all()
        ):
            section_total = Decimal("0")
            for line_item in proposal_section.line_items:
                section_total += Decimal(line_item.extended_price or 0)
            proposal_section.subtotal = _as_money(section_total)
    else:
        # Create-time snapshot may run while status is already Accepted.
        recalculate_proposal(proposal, allow_when_accepted=True)


def create_proposal(
    *,
    estimate,
    version,
    template,
    title=None,
    proposal_number=None,
    status="Draft",
    valid_until=None,
    overrides=None,
):
    if version.estimate_id != estimate.id:
        raise ProposalServiceError("Version does not belong to this estimate.")
    if not template.is_active:
        raise ProposalServiceError(
            "Inactive proposal templates cannot be used for new proposals."
        )

    proposal_number = (proposal_number or suggest_next_proposal_number()).strip()
    if not proposal_number:
        raise ProposalServiceError("Proposal number is required.")
    if Proposal.query.filter_by(proposal_number=proposal_number).first():
        raise ProposalServiceError(
            f'A proposal with number "{proposal_number}" already exists.'
        )

    snapshot = build_proposal_snapshot(estimate, version, template)
    overrides = overrides or {}
    snapshot.update({k: v for k, v in overrides.items() if v is not None})

    title = (title or snapshot["title"] or "").strip()
    if not title:
        raise ProposalServiceError("Proposal title is required.")

    if status not in PROPOSAL_STATUSES:
        raise ProposalServiceError("Select a valid proposal status.")

    proposal = Proposal(
        proposal_number=proposal_number,
        estimate_id=estimate.id,
        estimate_version_id=version.id,
        proposal_template_id=template.id,
        title=title,
        status=status,
        client_name=snapshot["client_name"],
        client_company=snapshot.get("client_company"),
        client_address=snapshot.get("client_address"),
        client_email=snapshot.get("client_email"),
        client_phone=snapshot.get("client_phone"),
        project_name=snapshot["project_name"],
        project_address=snapshot.get("project_address"),
        estimate_number=snapshot["estimate_number"],
        estimate_version_number=snapshot["estimate_version_number"],
        estimate_version_label=snapshot.get("estimate_version_label"),
        subtotal=Decimal(snapshot["subtotal"] or 0),
        overhead_percent=Decimal(snapshot.get("overhead_percent") or 0),
        profit_percent=Decimal(snapshot.get("profit_percent") or 0),
        tax_percent=Decimal(snapshot.get("tax_percent") or 0),
        overhead_amount=Decimal(snapshot["overhead_amount"] or 0),
        profit_amount=Decimal(snapshot["profit_amount"] or 0),
        tax_amount=Decimal(snapshot["tax_amount"] or 0),
        total=Decimal(snapshot["total"] or 0),
        intro_text=snapshot.get("intro_text"),
        scope_intro=snapshot.get("scope_intro"),
        exclusions=snapshot.get("exclusions"),
        clarifications=snapshot.get("clarifications"),
        schedule_text=snapshot.get("schedule_text"),
        payment_terms=snapshot.get("payment_terms"),
        warranty_text=snapshot.get("warranty_text"),
        acceptance_text=snapshot.get("acceptance_text"),
        show_detailed_pricing=bool(snapshot.get("show_detailed_pricing", True)),
        show_section_totals=bool(snapshot.get("show_section_totals", True)),
        show_allowances=bool(snapshot.get("show_allowances", True)),
        show_tax=bool(snapshot.get("show_tax", True)),
        valid_until=valid_until,
        issued_at=datetime.utcnow() if status == "Issued" else None,
    )
    db.session.add(proposal)
    db.session.flush()
    snapshot_estimate_version_content(proposal, version)
    db.session.commit()
    return proposal


def update_proposal_line_item(
    line_item,
    *,
    description=None,
    quantity=None,
    unit=None,
    unit_cost=None,
    markup_percent=None,
    notes=None,
):
    proposal = line_item.section.proposal
    ensure_proposal_mutable(proposal)

    if description is not None:
        description = description.strip()
        if not description:
            raise ProposalServiceError("Description is required.")
        line_item.description = description

    if unit is not None:
        unit = unit.strip()
        if not unit:
            raise ProposalServiceError("Unit is required.")
        line_item.unit = unit

    if quantity is not None:
        quantity = _as_decimal(quantity)
        if quantity < 0:
            raise ProposalServiceError("Quantity cannot be negative.")
        line_item.quantity = quantity

    if unit_cost is not None:
        unit_cost = _as_decimal(unit_cost)
        if unit_cost < 0:
            raise ProposalServiceError("Unit cost cannot be negative.")
        line_item.unit_cost = unit_cost

    if markup_percent is not None:
        markup_percent = _as_decimal(markup_percent)
        if markup_percent < 0:
            raise ProposalServiceError("Markup percent cannot be negative.")
        line_item.markup_percent = markup_percent

    if notes is not None:
        line_item.notes = notes.strip() or None

    apply_proposal_line_calculations(line_item)
    recalculate_proposal(proposal)
    db.session.commit()
    return line_item


def update_proposal(proposal, **fields):
    """Update proposal fields. Accepted proposals cannot be mutated.

    Status policy for this milestone:
    - Non-Accepted proposals may transition to any value in PROPOSAL_STATUSES
      (including Accepted) via existing callers.
    - Accepted proposals cannot change status or any other field.
    """
    ensure_proposal_mutable(proposal)

    if "title" in fields:
        title = (fields["title"] or "").strip()
        if not title:
            raise ProposalServiceError("Proposal title is required.")
        proposal.title = title

    if "proposal_number" in fields:
        number = (fields["proposal_number"] or "").strip()
        if not number:
            raise ProposalServiceError("Proposal number is required.")
        duplicate = Proposal.query.filter(
            Proposal.proposal_number == number,
            Proposal.id != proposal.id,
        ).first()
        if duplicate:
            raise ProposalServiceError(
                f'A proposal with number "{number}" already exists.'
            )
        proposal.proposal_number = number

    if "status" in fields:
        status = fields["status"]
        if status not in PROPOSAL_STATUSES:
            raise ProposalServiceError("Select a valid proposal status.")
        if status == "Issued" and proposal.status != "Issued":
            proposal.issued_at = datetime.utcnow()
        proposal.status = status

    if "valid_until" in fields:
        proposal.valid_until = fields["valid_until"]

    if "proposal_template_id" in fields:
        template = db.session.get(ProposalTemplate, fields["proposal_template_id"])
        if template is None:
            raise ProposalServiceError("Proposal template is required.")
        # Allow keeping an inactive template already linked; only block switching
        # to a newly selected inactive template.
        if (
            template.id != proposal.proposal_template_id
            and not template.is_active
        ):
            raise ProposalServiceError(
                "Inactive proposal templates cannot be selected."
            )
        proposal.proposal_template_id = template.id

    text_fields = (
        "client_name",
        "client_company",
        "client_address",
        "client_email",
        "client_phone",
        "project_name",
        "project_address",
        "intro_text",
        "scope_intro",
        "exclusions",
        "clarifications",
        "schedule_text",
        "payment_terms",
        "warranty_text",
        "acceptance_text",
    )
    for field in text_fields:
        if field in fields:
            value = fields[field]
            if field in ("client_name", "project_name"):
                value = (value or "").strip()
                if not value:
                    raise ProposalServiceError(
                        f"{field.replace('_', ' ').title()} is required."
                    )
                setattr(proposal, field, value)
            else:
                setattr(proposal, field, (value or "").strip() or None)

    for field in (
        "show_detailed_pricing",
        "show_section_totals",
        "show_allowances",
        "show_tax",
    ):
        if field in fields:
            setattr(proposal, field, bool(fields[field]))

    db.session.commit()
    return proposal


def update_proposal_status(proposal, status):
    return update_proposal(proposal, status=status)


def get_estimate_and_version(estimate_id, version_id, organization_id=None):
    org_id = organization_id or get_current_organization_id()
    estimate = (
        Estimate.query.join(Estimate.project)
        .filter(Estimate.id == estimate_id, Estimate.project.has(organization_id=org_id))
        .first()
    )
    if estimate is None:
        return None, None
    version = EstimateVersion.query.filter_by(
        id=version_id,
        estimate_id=estimate.id,
    ).first()
    return estimate, version
