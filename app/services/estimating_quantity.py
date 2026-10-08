"""Common V1 estimating quantity contract.

Existing engines keep their formulas. A scope with no stored rule stays
unresolved. Plumbing, electrical, and HVAC stay quote or allowance scopes.
"""

from __future__ import annotations

from app.services.deck_framing_quantity import quantity_result_from_model
from app.services.foundation_quantity import quantity_result_from_facts
from app.services.purchasing_quantity import annotate_purchasing
from app.services.work_structure import ICF_WALL_CODE

CONTRACT = "estimating_quantity"
CONTRACT_VERSION = "1"

SUBCONTRACT_SCOPES = ("plumbing", "electrical", "hvac")

# The text is the missing rule. It is not a formula.
MISSING_RULES = {
    "excavation": "No governed excavation quantity rule. A length is not a volume.",
    "roof_framing": "No governed roof-framing rule beyond a stored member count. Pitch is not assumed.",
    "sheathing": "No governed sheathing area rule. Area is not a sheet count.",
    "roofing": "No governed roofing coverage rule. Pitch is not assumed.",
    "siding": "No governed cladding area rule. Openings are not deducted by assumption.",
    "windows": "No governed window quantity rule.",
    "exterior_doors": "No governed exterior-door quantity rule.",
    "interior_framing": "No governed interior-framing rule beyond a stored member count.",
    "insulation": "No governed insulation quantity rule. Area is not a package count.",
    "drywall": "No governed drywall quantity rule. Area is not a sheet count.",
    "flooring": "No governed flooring quantity rule.",
    "interior_doors": "No governed interior-door quantity rule.",
    "trim": "No governed trim quantity rule. A length is not a stock-length purchase.",
    "stairs": "No governed stair material quantity rule. A stored riser count is not a lumber quantity.",
    "porches": "No governed porch rule beyond a stored member count.",
    "site": "No governed site-work quantity rule.",
    "flatwork": "No governed flatwork quantity rule. concrete_slab has no producer.",
    "equipment": "No governed equipment quantity.",
    "general_conditions": "No governed general-conditions quantity.",
    "allowances": "An allowance is a contractor amount, not a calculated quantity.",
}

_TASKS = {
    "framing": ("STRUCT", "FRAME", "Framing"),
    "decks": ("STRUCT", "FRAME", "Framing"),
    "roof_framing": ("STRUCT", "FRAME", "Framing"),
    "interior_framing": ("STRUCT", "FRAME", "Framing"),
    "foundations": ("FOUND", None, "Foundation"),
    "footings": ("FOUND", None, "Foundation"),
    "excavation": ("FOUND", "EXCAV", "Excavation"),
    "site": ("SITE", "CLEAR", "Clearing"),
    "flatwork": ("FOUND", None, "Foundation"),
}


def estimate_project(plan, catalogue=()):
    """Read one plan and return one quantity result.

    A missing fact or a missing rule flags that scope. Other scopes stay
    in the result. Subcontract trades are not treated as unknown work.
    """
    project_id = plan.get("project_id")
    lines = []
    if plan.get("construction_model") is not None:
        deck = quantity_result_from_model(plan["construction_model"], catalogue)
        lines.extend(_adapt_deck(deck, project_id))
    foundation_elements = plan.get("foundation_elements") or ()
    if foundation_elements:
        foundation = quantity_result_from_facts(
            {"project_id": project_id, "elements": foundation_elements}
        )
        lines.extend(_adapt_foundation(foundation, project_id))
    for scope in plan.get("scopes") or ():
        name = scope.get("scope")
        if name in SUBCONTRACT_SCOPES:
            lines.append(_subcontract(project_id, name, scope.get("facts") or {}))
        elif name in MISSING_RULES and not _already_calculated(lines, name):
            lines.append(_missing(project_id, name, scope.get("facts") or {}))
        elif name not in ("framing", "decks", "foundations", "footings", "flatwork"):
            lines.append(
                _missing(
                    project_id,
                    name,
                    scope.get("facts") or {},
                    rule="No governed quantity rule is stored for this scope.",
                )
            )
    return {
        "contract": CONTRACT,
        "contract_version": CONTRACT_VERSION,
        "project_id": project_id,
        "blocked": False,
        "continues_with_unresolved_items": any(
            line["status"] != "KNOWN" for line in lines
        ),
        "lines": tuple(lines),
        "subcontracts": tuple(
            line for line in lines if line.get("kind") == "subcontract"
        ),
        "learning_identity": {
            "contract": CONTRACT,
            "contract_version": CONTRACT_VERSION,
            "project_id": project_id,
            "estimated_quantity": "governed_quantity",
            "estimated_labour": None,
            "estimated_material_cost": None,
            "estimated_subcontract_cost": None,
            "actual_quantity": None,
            "actual_labour": None,
            "actual_material_cost": None,
            "actual_subcontract_cost": None,
        },
    }


def _already_calculated(lines, scope):
    return any(line.get("scope") == scope and line.get("status") == "KNOWN" for line in lines)


def _adapt_deck(result, project_id):
    adapted = []
    for line in result.get("lines") or ():
        scope = "decks" if line.get("element") in ("decking", "guard") else "framing"
        adapted.append(_copy_line(line, project_id, scope, result.get("labour")))
    return adapted


def _adapt_foundation(result, project_id):
    adapted = []
    for source in result.get("lines") or ():
        element = source.get("element")
        if element == "footing":
            scope = "footings"
        elif element == "concrete_slab":
            scope = "flatwork"
        else:
            scope = "foundations"
        labour = _labour(scope)
        if scope == "foundations":
            labour["element_code"] = ICF_WALL_CODE
            labour["activity_name"] = "ICF wall"
            labour["activity_code"] = None
        adapted.append(_copy_line(source, project_id, scope, labour))
    return adapted


def _copy_line(source, project_id, scope, labour):
    line = dict(source)
    line["project_id"] = project_id
    line["scope"] = scope
    line["task"] = _task(scope)
    line["labour"] = dict(labour) if isinstance(labour, dict) else _labour(scope)
    line["purchase_quantity"] = None
    line["stock_length"] = None
    line["waste"] = None
    provenance = dict(line.get("provenance") or {})
    provenance["project_id"] = project_id
    line["provenance"] = provenance
    return annotate_purchasing(line)


def _missing(project_id, scope, facts, rule=None):
    text = rule or MISSING_RULES[scope]
    retained = tuple(
        "{0}={1}".format(key, value)
        for key, value in facts.items()
        if value not in (None, "")
    )
    missing = [text]
    for key, value in facts.items():
        if value in (None, ""):
            missing.append(key)
    return {
        "project_id": project_id,
        "scope": scope,
        "element": scope,
        "kind": "missing_rule",
        "status": "CONTRACTOR_INPUT",
        "quantity": None,
        "unit": None,
        "quantity_meaning": None,
        "purchase_quantity": None,
        "stock_length": None,
        "waste": None,
        "canonical_material_code": None,
        "missing_facts": tuple(missing),
        "retained_facts": retained,
        "item_text": "{0}. Unresolved.".format(scope.replace("_", " ").capitalize()),
        "task": _task(scope),
        "labour": _labour(scope),
        "provenance": {
            "project_id": project_id,
            "source_facts": dict(facts),
            "engine_id": CONTRACT,
            "engine_version": CONTRACT_VERSION,
            "rule": "missing_rule",
            "missing_rule": text,
        },
    }


def _subcontract(project_id, scope, facts):
    return {
        "project_id": project_id,
        "scope": scope,
        "element": scope,
        "kind": "subcontract",
        "status": "SUBCONTRACT",
        "quantity": None,
        "unit": None,
        "quantity_meaning": "quote_or_allowance",
        "purchase_quantity": None,
        "stock_length": None,
        "waste": None,
        "canonical_material_code": None,
        "missing_facts": ("subcontractor quote or allowance",),
        "retained_facts": tuple(
            "{0}={1}".format(key, value)
            for key, value in facts.items()
            if value not in (None, "")
        ),
        "item_text": "{0}. Quote or allowance.".format(scope.capitalize()),
        "task": {
            "element_code": None,
            "activity_code": None,
            "activity_name": scope,
            "production_assumption": None,
            "hours": None,
        },
        "labour": {
            "element_code": None,
            "activity_code": None,
            "production_assumption": None,
            "hours": None,
            "status": "SUBCONTRACT",
            "note": "Subcontract scope. No crew production rate is applied.",
        },
        "provenance": {
            "project_id": project_id,
            "source_facts": dict(facts),
            "engine_id": CONTRACT,
            "engine_version": CONTRACT_VERSION,
            "rule": "subcontract_quote_or_allowance",
        },
    }


def _task(scope):
    element, activity, name = _TASKS.get(scope, (None, None, None))
    return {
        "element_code": element,
        "activity_code": activity,
        "activity_name": name,
        "production_assumption": None,
        "hours": None,
    }


def _labour(scope):
    task = _task(scope)
    return {
        "element_code": task["element_code"],
        "activity_code": task["activity_code"],
        "activity_name": task["activity_name"],
        "production_assumption": None,
        "hours": None,
        "status": "CONTRACTOR_INPUT",
        "note": (
            "A contractor-confirmed production assumption is required "
            "before labour hours can be calculated."
        ),
    }
