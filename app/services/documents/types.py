"""Document types and deterministic classification (no AI, no external call).

The registry is code (frozen). A type lists the contexts it is offered in, the dates it usually carries, the keyword
tuples that suggest it (every word of a tuple must appear) and whether the crew may see it on their jobs.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional

from app.models.documents import (
    CONTEXT_COMPANY as CO,
    CONTEXT_CUSTOMER as CU,
    CONTEXT_EQUIPMENT as EQ,
    CONTEXT_PERSON as PE,
    CONTEXT_PROJECT as PR,
    CONTEXT_SUBCONTRACTOR as SC,
    CONTEXT_SUPPLIER as SU,
    DATE_EFFECTIVE,
    DATE_EXPIRES,
    DATE_INSPECTION_DUE,
    DATE_RENEWAL_DUE,
    DATE_WARRANTY_ENDS,
    SENSITIVITY_FINANCIAL,
    SENSITIVITY_PEOPLE,
    SENSITIVITY_STANDARD,
)

ALL = frozenset({CO, PR, PE, EQ, SU, SC, CU})


@dataclass(frozen=True)
class DocumentType:
    code: str
    label: str
    family: str
    contexts: frozenset
    expects: tuple = ()
    keywords: tuple = ()
    field_visible: bool = False
    sensitivity: str = SENSITIVITY_STANDARD
    extension_hints: dict = field(default_factory=dict)


def _t(code, label, family, contexts, expects=(), keywords=(), *, field_visible=False, sensitivity=SENSITIVITY_STANDARD,
       ext=None):
    return DocumentType(code, label, family, frozenset(contexts), tuple(expects), tuple(keywords), field_visible,
                        sensitivity, dict(ext or {}))


REGISTRY = (
    # Compliance
    _t("WSIB_CLEARANCE", "WSIB clearance certificate", "Compliance", {CO, SC}, (DATE_EXPIRES,),
       (("wsib",), ("workplace", "safety", "clearance"), ("clearance", "certificate"))),
    _t("INSURANCE_CERT", "Certificate of insurance", "Compliance", {CO, SC, SU, PR}, (DATE_EXPIRES,),
       (("certificate", "insurance"), ("coi",), ("liability", "insurance"), ("insurance",), ("cgl",))),
    _t("LICENCE", "Licence", "Compliance", {CO, SC, SU}, (DATE_EXPIRES,),
       (("licence",), ("license",), ("tarion",), ("registration", "certificate"))),
    _t("PERMIT", "Permit", "Compliance", {CO, PR}, (DATE_EXPIRES,),
       (("building", "permit"), ("permit",))),
    # Company
    _t("POLICY", "Policy", "Company", {CO}, (DATE_EFFECTIVE,), (("policy",), ("handbook",))),
    _t("PROCEDURE", "Procedure", "Company", {CO}, (DATE_EFFECTIVE,), (("procedure",), ("sop",))),
    _t("FORM_TEMPLATE", "Form / template", "Company", {CO}, (), (("form",), ("template",))),
    _t("SAFETY", "Safety document", "Company", {CO, PR}, (DATE_EFFECTIVE,),
       (("safety",), ("hazard",), ("jhsc",), ("toolbox", "talk"), ("sds",), ("msds",), ("fall", "protection")),
       field_visible=True),
    _t("TRAINING_MATERIAL", "Training material", "Company", {CO}, (), (("training", "material"), ("course",))),
    # People
    _t("EMPLOYMENT", "Employment document", "People", {PE}, (),
       (("employment",), ("offer", "letter"), ("contract", "employment"), ("td1",)), sensitivity=SENSITIVITY_PEOPLE),
    _t("CERTIFICATION", "Certification / ticket", "People", {PE}, (DATE_EXPIRES,),
       (("working", "heights"), ("whmis",), ("first", "aid"), ("ticket",), ("certification",), ("certificate",),
        ("cpr",), ("forklift",)), sensitivity=SENSITIVITY_PEOPLE),
    _t("TRAINING_RECORD", "Training record", "People", {PE}, (DATE_EXPIRES,),
       (("training", "record"), ("training",), ("orientation",)), sensitivity=SENSITIVITY_PEOPLE),
    _t("SIGNED_POLICY", "Signed policy acknowledgement", "People", {PE}, (),
       (("acknowledgement",), ("acknowledgment",), ("signed", "policy")), sensitivity=SENSITIVITY_PEOPLE),
    # Equipment
    _t("MANUAL", "Manual", "Equipment", {EQ}, (), (("manual",), ("owner", "guide"), ("operator",))),
    _t("PURCHASE", "Purchase record", "Equipment", {EQ}, (), (("purchase",), ("bill", "sale"), ("receipt",))),
    _t("INSPECTION", "Inspection report", "Equipment", {EQ}, (DATE_INSPECTION_DUE,),
       (("inspection",), ("cvip",), ("safety", "check"), ("annual", "inspection"))),
    _t("MAINTENANCE", "Maintenance record", "Equipment", {EQ}, (), (("maintenance",), ("service",), ("repair",))),
    _t("REGISTRATION", "Registration", "Equipment", {EQ}, (DATE_RENEWAL_DUE, DATE_EXPIRES),
       (("registration",), ("ownership",), ("plate",), ("permit", "vehicle"))),
    _t("EQUIPMENT_CERT", "Equipment certification", "Equipment", {EQ}, (DATE_EXPIRES,),
       (("certification",), ("certificate",), ("load", "test"))),
    # Project
    _t("DRAWING", "Drawing / plan", "Project", {PR, CU}, (),
       (("drawing",), ("drawings",), ("plan",), ("plans",), ("elevation",), ("site", "plan"), ("sheet",)),
       field_visible=True, ext={".dwg": 2}),
    _t("SPECIFICATION", "Specification", "Project", {PR, SU}, (), (("spec",), ("specification",), ("specs",)),
       field_visible=True),
    _t("INSTRUCTION", "Installation / work instructions", "Project", {PR, SU}, (),
       (("installation",), ("instructions",), ("install", "guide"), ("method", "statement")), field_visible=True),
    _t("ESTIMATE", "Estimate", "Project", {PR, CU, CO}, (), (("estimate",), ("takeoff",)), ext={".xlsm": 1}),
    _t("PROPOSAL", "Proposal", "Project", {PR, CU}, (), (("proposal",), ("quote", "customer"))),
    _t("CONTRACT", "Contract", "Project", {PR, CU, SC, SU}, (), (("contract",), ("agreement", "construction"))),
    _t("SIGNED_CONTRACT", "Signed contract", "Project", {PR, CU}, (), (("signed", "contract"), ("executed",))),
    _t("CHANGE_ORDER", "Change order", "Project", {PR, CU}, (), (("change", "order"), ("co",), ("variation",))),
    _t("SUPPLIER_QUOTE", "Supplier quote", "Project", {PR, SU, SC}, (), (("quote",), ("quotation",))),
    _t("PURCHASE_ORDER", "Purchase order", "Project", {PR, SU}, (), (("purchase", "order"), ("po",))),
    _t("SUBCONTRACT", "Subcontract", "Project", {PR, SC}, (), (("subcontract",), ("sub", "agreement"))),
    _t("SCHEDULE", "Schedule", "Project", {PR}, (), (("schedule",), ("gantt",), ("lookahead",))),
    _t("INVOICE", "Invoice", "Project", {PR, SU, SC, CU}, (), (("invoice",), ("bill",)),
       sensitivity=SENSITIVITY_FINANCIAL),
    _t("PHOTO", "Photo", "Project", {PR, EQ, CU}, (), (("photo",), ("img",)),
       ext={".jpg": 2, ".jpeg": 2, ".png": 2, ".heic": 2, ".heif": 2}),
    _t("CLOSEOUT", "Closeout document", "Project", {PR, CU}, (),
       (("closeout",), ("as", "built"), ("operation", "maintenance"), ("handover",))),
    # Warranty
    _t("WARRANTY", "Warranty", "Warranty", {PR, EQ, SU, CU}, (DATE_WARRANTY_ENDS,), (("warranty",), ("guarantee",))),
    # Agreements
    _t("AGREEMENT", "Agreement", "Agreements", {SU, SC, CU, CO}, (DATE_EXPIRES,),
       (("agreement",), ("terms",), ("nda",), ("credit", "application"))),
    _t("APPROVAL", "Customer approval", "Agreements", {CU, PR}, (), (("approval",), ("approved",), ("sign", "off"))),
    _t("PRODUCT_INFO", "Product information", "Agreements", {SU, PR}, (),
       (("product", "data"), ("data", "sheet"), ("brochure",), ("catalogue",), ("catalog",))),
    _t("OTHER", "Other", "Other", ALL, ()),
)
TYPES = {t.code: t for t in REGISTRY}
FAMILY_ORDER = ("Compliance", "Project", "Warranty", "Agreements", "People", "Equipment", "Company", "Other")
FIELD_VISIBLE_TYPES = frozenset(t.code for t in REGISTRY if t.field_visible)


def get_type(code: Optional[str]) -> DocumentType:
    return TYPES.get(code or "", TYPES["OTHER"])


def type_label(code: Optional[str]) -> str:
    return get_type(code).label


def types_for_context(context_kind: str) -> list:
    """Types offered on an upload in this context (OTHER last)."""
    return [t for t in REGISTRY if context_kind in t.contexts]


_WORD_RE = re.compile(r"[a-z0-9]+")


def _words(value: str) -> set:
    words = set(_WORD_RE.findall((value or "").lower()))
    return words | {w[:-1] for w in words if len(w) > 3 and w.endswith("s")}  # plurals: elevations, specs


def classify(filename: str, context_kind: str, text: str = "") -> tuple[str, Optional[str]]:
    """(type code, rule) for a file in a context. Pure function.

    +3 per keyword tuple fully present in the filename, +1 if present in the first 2,000 characters of the text,
    plus extension hints. Highest score >= 2 wins (one name keyword, or two in the text); ties go to registry order;
    otherwise OTHER.
    """
    stem = os.path.splitext(filename or "")[0]
    name_words = _words(stem.replace("_", " ").replace("-", " "))
    text_words = _words((text or "")[:2000])
    ext = os.path.splitext(filename or "")[1].lower()
    best = ("OTHER", None, 0)
    for doc_type in REGISTRY:
        if doc_type.code == "OTHER" or context_kind not in doc_type.contexts:
            continue
        score = 0
        rule = None
        for keyword in doc_type.keywords:
            words = set(keyword)
            if words <= name_words:
                score += 3
                rule = rule or f"{doc_type.code}:{'+'.join(keyword)}"
            elif text_words and words <= text_words:
                score += 1
                rule = rule or f"{doc_type.code}:text:{'+'.join(keyword)}"
        hint = doc_type.extension_hints.get(ext)
        if hint:
            score += hint
            rule = rule or f"{doc_type.code}:ext{ext}"
        if score > best[2]:
            best = (doc_type.code, rule, score)
    if best[2] >= 2:  # a name keyword (3), or two keyword groups found in the text
        return best[0], best[1]
    return "OTHER", None


def default_sensitivity(type_code: str, context_kind: str) -> str:
    """Known from the context, not inferred: person-context documents are PEOPLE; invoices are FINANCIAL."""
    from app.models.documents import CONTEXT_PERSON

    if context_kind == CONTEXT_PERSON:
        return SENSITIVITY_PEOPLE
    sensitivity = get_type(type_code).sensitivity
    return SENSITIVITY_STANDARD if sensitivity == SENSITIVITY_PEOPLE else sensitivity
