"""Estimating-owned subcontract quote evidence (FG-031 Slice B / ADR-048).

A quote is evidence. It does not set EstimateLineItem cost or apply Pricing.
"""

from datetime import datetime, date
from decimal import InvalidOperation

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.estimate import EstimateLineItem
from app.models.estimate_scope_delivery import LABOUR_SUBCONTRACT
from app.models.pricing_engine import AI_ACTOR_TOKENS
from app.models.subcontractor import (
    QUOTE_STATUS_RECEIVED,
    QUOTE_STATUS_REJECTED,
    QUOTE_STATUS_SELECTED,
    QUOTE_STATUS_SUPERSEDED,
    SUBCONTRACTOR_STATUS_ACTIVE,
    Subcontractor,
    SubcontractQuoteEvidence,
)
from app.services.estimate_builder import as_money
from app.services.estimate_scope_delivery import (
    EstimateScopeDeliveryError,
    get_scope_delivery_for_line,
    line_ownership_chain,
    require_line_matches_scope,
    require_routing_editable,
)
from app.services.estimates import EstimateServiceError


class SubcontractQuoteError(EstimateServiceError):
    """Raised when subcontract identity or quote evidence cannot complete."""


def _require_line_scope(line_item, *, organization_id, project_id, estimate_version_id=None):
    try:
        return require_line_matches_scope(
            line_item,
            organization_id=organization_id,
            project_id=project_id,
            estimate_version_id=estimate_version_id,
        )
    except EstimateScopeDeliveryError as exc:
        raise SubcontractQuoteError(str(exc)) from exc


def _require_editable_version(version):
    try:
        require_routing_editable(version)
    except EstimateScopeDeliveryError as exc:
        raise SubcontractQuoteError(str(exc)) from exc
    return version


def assert_human_quote_actor(actor):
    name = (actor or "").strip()
    if not name:
        raise SubcontractQuoteError("Subcontract quote evidence requires a human actor.")
    if name.upper() in AI_ACTOR_TOKENS:
        raise SubcontractQuoteError("AI cannot select a subcontract quote.")
    return name


def labour_is_subcontract(line_item):
    routing = get_scope_delivery_for_line(line_item)
    return routing is not None and routing.labour_delivery == LABOUR_SUBCONTRACT


def require_subcontract_labour(line_item):
    if not labour_is_subcontract(line_item):
        raise SubcontractQuoteError(
            "Subcontract quote evidence applies only when labour is performed by a subcontractor."
        )
    return get_scope_delivery_for_line(line_item)


def list_subcontractors(organization_id, *, include_inactive=False):
    query = Subcontractor.query.filter_by(organization_id=organization_id)
    if not include_inactive:
        query = query.filter_by(status=SUBCONTRACTOR_STATUS_ACTIVE)
    return query.order_by(Subcontractor.code, Subcontractor.id).all()


def get_subcontractor(subcontractor_id, *, organization_id):
    row = db.session.get(Subcontractor, subcontractor_id)
    if row is None or row.organization_id != organization_id:
        raise SubcontractQuoteError("Subcontractor was not found in this organization.")
    return row


def create_subcontractor(
    *,
    organization_id,
    code,
    legal_name,
    status=SUBCONTRACTOR_STATUS_ACTIVE,
    commit=True,
):
    org_id = (organization_id or "").strip()
    if not org_id:
        raise SubcontractQuoteError("Organization is required.")
    existing = Subcontractor.query.filter_by(organization_id=org_id, code=(code or "").strip()).first()
    if existing is not None:
        raise SubcontractQuoteError("A subcontractor with this code already exists in the organization.")
    row = Subcontractor(
        organization_id=org_id,
        code=code,
        legal_name=legal_name,
        status=status or SUBCONTRACTOR_STATUS_ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    try:
        db.session.add(row)
        db.session.flush()
        if commit:
            db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise SubcontractQuoteError(
            "A subcontractor with this code already exists in the organization."
        ) from exc
    except Exception:
        db.session.rollback()
        raise
    return row


def get_or_create_subcontractor(*, organization_id, code, legal_name, commit=False):
    code_value = (code or "").strip()
    if not code_value:
        raise SubcontractQuoteError("Subcontractor code is required.")
    existing = Subcontractor.query.filter_by(
        organization_id=organization_id, code=code_value
    ).first()
    if existing is not None:
        if (legal_name or "").strip() and existing.legal_name != (legal_name or "").strip():
            raise SubcontractQuoteError(
                "Subcontractor code already exists with a different legal name."
            )
        return existing
    return create_subcontractor(
        organization_id=organization_id,
        code=code_value,
        legal_name=legal_name,
        commit=commit,
    )


def quotes_for_line(line_item):
    if line_item is None or line_item.id is None:
        return []
    return (
        SubcontractQuoteEvidence.query.filter_by(estimate_line_item_id=line_item.id)
        .order_by(SubcontractQuoteEvidence.id)
        .all()
    )


def selected_quote_for_line(line_item):
    if line_item is None or line_item.id is None:
        return None
    return SubcontractQuoteEvidence.query.filter_by(
        estimate_line_item_id=line_item.id,
        selection_status=QUOTE_STATUS_SELECTED,
    ).first()


def _parse_date(value, *, field_name):
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise SubcontractQuoteError(f"{field_name} must be a valid date.") from exc


def receive_quote(
    line_item,
    *,
    actor,
    organization_id=None,
    project_id=None,
    subcontractor_id=None,
    subcontractor_code=None,
    subcontractor_legal_name=None,
    quote_reference,
    amount,
    currency="CAD",
    quote_date,
    expires_on=None,
    included_scope=None,
    exclusions=None,
    provenance_note=None,
    user_id=None,
    commit=True,
):
    """Create RECEIVED quote evidence. Does not mutate line cost or Pricing."""
    actor_name = assert_human_quote_actor(actor)
    chain = line_ownership_chain(line_item)
    org_id = organization_id or chain["organization_id"]
    proj_id = project_id if project_id is not None else chain["project_id"]
    _require_line_scope(
        line_item,
        organization_id=org_id,
        project_id=proj_id,
        estimate_version_id=chain["estimate_version_id"],
    )
    _require_editable_version(chain["version"])
    routing = require_subcontract_labour(line_item)
    if routing.organization_id != chain["organization_id"]:
        raise SubcontractQuoteError("Scope delivery does not match the commercial line.")

    try:
        party = None
        if subcontractor_id is not None:
            party = get_subcontractor(subcontractor_id, organization_id=chain["organization_id"])
        else:
            party = get_or_create_subcontractor(
                organization_id=chain["organization_id"],
                code=subcontractor_code,
                legal_name=subcontractor_legal_name,
                commit=False,
            )
        if party.organization_id != chain["organization_id"]:
            raise SubcontractQuoteError("Subcontractor is not in this organization.")

        try:
            quoted = as_money(amount)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise SubcontractQuoteError("Quoted amount must be a number.") from exc
        now = datetime.utcnow()
        parsed_quote_date = _parse_date(quote_date, field_name="Quote date")
        if parsed_quote_date is None:
            raise SubcontractQuoteError("Quote date is required.")
        row = SubcontractQuoteEvidence(
            organization_id=chain["organization_id"],
            project_id=chain["project_id"],
            estimate_id=chain["estimate_id"],
            estimate_version_id=chain["estimate_version_id"],
            estimate_line_item_id=line_item.id,
            estimate_scope_delivery_id=routing.id,
            subcontractor_id=party.id,
            quote_reference=quote_reference,
            amount=quoted,
            currency=(currency or "").strip().upper() or "CAD",
            quote_date=parsed_quote_date,
            expires_on=_parse_date(expires_on, field_name="Expires"),
            included_scope=(included_scope or "").strip() or None,
            exclusions=(exclusions or "").strip() or None,
            provenance_note=(provenance_note or "").strip() or None,
            actor_user_id=user_id,
            actor_display_name=actor_name,
            received_at=now,
            selection_status=QUOTE_STATUS_RECEIVED,
            selected_by=None,
            selected_at=None,
            created_at=now,
            updated_at=now,
        )
        db.session.add(row)
        db.session.flush()
        if commit:
            db.session.commit()
    except SubcontractQuoteError:
        db.session.rollback()
        raise
    except ValueError as exc:
        db.session.rollback()
        raise SubcontractQuoteError(str(exc)) from exc
    except Exception:
        db.session.rollback()
        raise
    return row


def _load_quote_for_mutation(quote_id, *, organization_id, project_id):
    row = db.session.get(SubcontractQuoteEvidence, quote_id)
    if row is None:
        raise SubcontractQuoteError("Quote evidence was not found.")
    line = db.session.get(EstimateLineItem, row.estimate_line_item_id)
    chain = line_ownership_chain(line)
    _require_line_scope(
        line,
        organization_id=organization_id or chain["organization_id"],
        project_id=project_id if project_id is not None else chain["project_id"],
        estimate_version_id=chain["estimate_version_id"],
    )
    if row.organization_id != chain["organization_id"]:
        raise SubcontractQuoteError("Quote evidence organization does not match the commercial line.")
    if row.project_id != chain["project_id"]:
        raise SubcontractQuoteError("Quote evidence project does not match the commercial line.")
    if row.estimate_version_id != chain["estimate_version_id"]:
        raise SubcontractQuoteError("Quote evidence version does not match the commercial line.")
    party = db.session.get(Subcontractor, row.subcontractor_id)
    if party is None or party.organization_id != chain["organization_id"]:
        raise SubcontractQuoteError("Quote evidence subcontractor is not in this organization.")
    _require_editable_version(chain["version"])
    require_subcontract_labour(line)
    return row, line, chain


def select_quote(
    quote_id,
    *,
    actor,
    organization_id=None,
    project_id=None,
    user_id=None,
    commit=True,
):
    """Human selection. Preserves prior SELECTED rows as SUPERSEDED. No cost mutation."""
    actor_name = assert_human_quote_actor(actor)
    try:
        row, line, chain = _load_quote_for_mutation(
            quote_id, organization_id=organization_id, project_id=project_id
        )
        if row.selection_status not in (QUOTE_STATUS_RECEIVED, QUOTE_STATUS_SELECTED):
            raise SubcontractQuoteError("Only a received quote can be selected.")
        now = datetime.utcnow()
        prior_selected = (
            SubcontractQuoteEvidence.query.filter_by(
                estimate_line_item_id=line.id,
                selection_status=QUOTE_STATUS_SELECTED,
            )
            .filter(SubcontractQuoteEvidence.id != row.id)
            .all()
        )
        for prior in prior_selected:
            prior.selection_status = QUOTE_STATUS_SUPERSEDED
            prior.updated_at = now
        row.selection_status = QUOTE_STATUS_SELECTED
        row.selected_by = user_id
        row.selected_at = now
        row.actor_display_name = actor_name
        row.updated_at = now
        db.session.flush()
        if commit:
            db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return row


def reject_quote(
    quote_id,
    *,
    actor,
    organization_id=None,
    project_id=None,
    user_id=None,
    commit=True,
):
    actor_name = assert_human_quote_actor(actor)
    try:
        row, _line, _chain = _load_quote_for_mutation(
            quote_id, organization_id=organization_id, project_id=project_id
        )
        if row.selection_status == QUOTE_STATUS_SUPERSEDED:
            raise SubcontractQuoteError("A superseded quote cannot be rejected.")
        now = datetime.utcnow()
        row.selection_status = QUOTE_STATUS_REJECTED
        row.selected_by = None
        row.selected_at = None
        row.actor_display_name = actor_name
        row.actor_user_id = user_id if user_id is not None else row.actor_user_id
        row.updated_at = now
        db.session.flush()
        if commit:
            db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return row


def freeze_facts_for_line(line_item):
    """Immutable facts copied onto EstimateCostingSnapshotLine. None if no SELECTED quote."""
    quote = selected_quote_for_line(line_item)
    if quote is None:
        return {
            "subcontract_quote_evidence_id": None,
            "subcontract_quote_reference": None,
            "subcontract_quoted_amount": None,
            "subcontract_quote_currency": None,
            "subcontract_quote_date": None,
            "subcontractor_id": None,
            "subcontract_subcontractor_code": None,
            "subcontract_subcontractor_legal_name": None,
        }
    party = db.session.get(Subcontractor, quote.subcontractor_id)
    return {
        "subcontract_quote_evidence_id": quote.id,
        "subcontract_quote_reference": quote.quote_reference,
        "subcontract_quoted_amount": as_money(quote.amount),
        "subcontract_quote_currency": quote.currency,
        "subcontract_quote_date": quote.quote_date,
        "subcontractor_id": quote.subcontractor_id,
        "subcontract_subcontractor_code": party.code if party is not None else None,
        "subcontract_subcontractor_legal_name": (
            party.legal_name if party is not None else None
        ),
    }


def quote_amount_differs_from_working_cost(line_item):
    quote = selected_quote_for_line(line_item)
    if quote is None:
        return False
    try:
        return as_money(quote.amount) != as_money(line_item.extended_cost)
    except Exception:
        return True


def copy_quotes_for_cloned_line(source_line, cloned_line, *, actor="Estimate version clone"):
    """Copy quote evidence onto cloned line IDs. Selection must be reconfirmed."""
    actor_name = (actor or "Estimate version clone").strip() or "Estimate version clone"
    chain = line_ownership_chain(cloned_line)
    routing = get_scope_delivery_for_line(cloned_line)
    now = datetime.utcnow()
    copied = []
    for source in quotes_for_line(source_line):
        row = SubcontractQuoteEvidence(
            organization_id=chain["organization_id"],
            project_id=chain["project_id"],
            estimate_id=chain["estimate_id"],
            estimate_version_id=chain["estimate_version_id"],
            estimate_line_item_id=cloned_line.id,
            estimate_scope_delivery_id=routing.id if routing is not None else None,
            subcontractor_id=source.subcontractor_id,
            quote_reference=source.quote_reference,
            amount=source.amount,
            currency=source.currency,
            quote_date=source.quote_date,
            expires_on=source.expires_on,
            included_scope=source.included_scope,
            exclusions=source.exclusions,
            provenance_note=source.provenance_note,
            actor_user_id=None,
            actor_display_name=actor_name,
            received_at=now,
            selection_status=QUOTE_STATUS_RECEIVED,
            selected_by=None,
            selected_at=None,
            created_at=now,
            updated_at=now,
        )
        db.session.add(row)
        copied.append(row)
    if copied:
        db.session.flush()
    return copied


def assemble_line_quote_review(line_item):
    quotes = quotes_for_line(line_item)
    selected = selected_quote_for_line(line_item)
    return {
        "eligible": labour_is_subcontract(line_item),
        "quotes": quotes,
        "selected": selected,
        "subcontractors": (
            list_subcontractors(line_ownership_chain(line_item)["organization_id"])
            if line_item is not None
            else []
        ),
    }
