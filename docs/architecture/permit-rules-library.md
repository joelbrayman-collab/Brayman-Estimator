# Architecture — Permit Rules Library V1 (Ontario / Ottawa POC)

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTED** ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)) / **LIVE MIGRATION PENDING**. Architecture **Accepted** ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical Feature Gate | [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| Source inventory | [permit-rules-ontario-ottawa-sources.md](permit-rules-ontario-ottawa-sources.md) |
| Related | [permit-and-approvals-report.md](permit-and-approvals-report.md) · [jurisdiction-resolution.md](jurisdiction-resolution.md) · [legal-content-and-templates.md](../governance/legal-content-and-templates.md) |
| Code | `app/models/permit_intelligence.py` (`PermitRule`, `PERMIT_RULE_SEED`) · `app/services/permit_intelligence.py` |
| Schema | Graph head `f8a9b0c1d2e3`. Live current remains `e7f8a9b0c1d2`. |

**Current vs intended:** V1 tables and **10 APPROVED** bounded Ontario / City of Ottawa / coach-house rules exist in the repository seed and additive migration. They are **not** live-migrated onto the development/UAT database in the FG-016 implementation pass. This is **not** a national legal CMS. It is **not** the Contract / Warranty Legal Content Gate.

---

## Purpose

A governed **Permit / Planning / Approval Rules Library** is required for meaningful Pass 2 analysis ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)).

It is **not** the Contract / Warranty Legal Content Gate.

It is **not** org commercial intelligence. Records are **platform-governed**. Ordinary office UX has **no** rule CRUD.

---

## V1 record

Implemented on `permit_rules`: code, version_number, jurisdiction_id, issuing_authority, source_title, source_citation, source_url, document_reference, rule_category, statement, evaluation_kind, thresholds, applicability_notes, coverage_scope, required_permit_context, effective_from, effective_to, reviewed_at, reviewed_by, provenance, approval_state.

---

## Authority

Operational rules: **authoritative governmental / AHJ sources only**. Inventory: [permit-rules-ontario-ottawa-sources.md](permit-rules-ontario-ottawa-sources.md).

Not governing authority: ChatGPT, Cursor, blogs, contractor websites, search snippets, generic summaries.

AI **cannot** mark regulatory content **APPROVED**. Seed reviewer is `FG-016-GOVERNANCE-SEED`.

---

## States

DRAFT → REVIEWED → APPROVED → SUPERSEDED

Only **APPROVED** and currently effective rules participate in a new analysis. Superseded rows remain for history. New analyses pin the rule versions they used. Old reports do not float to a mutable current rule.

---

## Ingestion

```text
DEVELOPMENT / GOVERNANCE RESEARCH
→ AUTHORITATIVE SOURCE
→ HUMAN REVIEW
→ GOVERNED RULE RECORD
→ PRODUCT USE
```

No product-runtime scrape. No automatic ingestion. No external AI.

---

## Coverage (V1)

```text
ONTARIO / CITY OF OTTAWA
COACH HOUSE / ADDITIONAL DWELLING
RURAL / NORTH GOWER REFERENCE CASE
```

Unknown / unimplemented jurisdictions: **RULE COVERAGE NOT AVAILABLE**. No Ottawa fallback.

Populated families: permit application, same-lot applicability, dual-compliance VERIFY, private servicing / 0.4 ha, footprint ceiling, height ceiling, setbacks, OSSO/RVCA, grading plan, bounded site-plan completeness.

---

## This architecture does not authorize

- Runtime web lookup
- A national library
- Reuse of contract/warranty templates as zoning/permit rules
- Live-migrating `f8a9b0c1d2e3` in the FG-016 implementation pass
