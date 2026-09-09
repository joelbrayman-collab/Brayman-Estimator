"""Test-only FG-031 helpers. Not production auto-approval."""

from app.models.estimate_scope_delivery import (
    LABOUR_INTERNAL,
    MATERIAL_CONTRACTOR_PURCHASED,
    STATUS_CONFIRMED,
)
from app.services.estimate_costing import iter_version_line_items
from app.services.estimate_scope_delivery import (
    confirm_scope_delivery,
    dimensions_are_resolved,
    ensure_routing_rows_for_version,
    get_scope_delivery_for_line,
    save_scope_delivery,
    version_is_routing_editable,
)


def ensure_resolved_scope_routing(version, *, actor="Joel Brayman"):
    """Make non-Allowance lines resolved (PROPOSED). Does not confirm.

    Suggestion is not approval. Skips locked/non-Draft versions.
    """
    if not version_is_routing_editable(version):
        return
    ensure_routing_rows_for_version(version, actor=actor, commit=False)
    for item in iter_version_line_items(version):
        if (item.line_type or "") == "Allowance":
            continue
        routing = get_scope_delivery_for_line(item)
        if routing is not None and dimensions_are_resolved(
            routing.material_procurement, routing.labour_delivery
        ):
            continue
        save_scope_delivery(
            item,
            material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
            labour_delivery=LABOUR_INTERNAL,
            actor=actor,
            commit=False,
        )


def ensure_confirmed_scope_routing(version, *, actor="Joel Brayman"):
    """Resolve and confirm non-Allowance lines so FG-027 costing tests can approve.

    Test-only. Not production auto-approval. Skips locked/non-Draft versions.
    """
    if not version_is_routing_editable(version):
        return
    ensure_resolved_scope_routing(version, actor=actor)
    for item in iter_version_line_items(version):
        if (item.line_type or "") == "Allowance":
            continue
        routing = get_scope_delivery_for_line(item)
        if routing is None:
            continue
        if routing.status == STATUS_CONFIRMED:
            continue
        if not dimensions_are_resolved(
            routing.material_procurement, routing.labour_delivery
        ):
            continue
        confirm_scope_delivery(item, actor=actor, commit=False)


def confirm_contractor_purchased_routing(line_item, *, actor="Joel Brayman"):
    save_scope_delivery(
        line_item,
        material_procurement=MATERIAL_CONTRACTOR_PURCHASED,
        labour_delivery=LABOUR_INTERNAL,
        actor=actor,
        commit=False,
    )
    row = confirm_scope_delivery(line_item, actor=actor, commit=False)
    assert row.status == STATUS_CONFIRMED
    return row
