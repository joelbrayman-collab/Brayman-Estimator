# Architecture — Permit Rules Library V1 (Ontario / Ottawa POC)

| Attribute | Value |
|-----------|--------|
| Status | **APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md). Architecture **Accepted** ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical Feature Gate | [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) |
| Related | [permit-and-approvals-report.md](permit-and-approvals-report.md) · [jurisdiction-resolution.md](jurisdiction-resolution.md) · [legal-content-and-templates.md](../governance/legal-content-and-templates.md) |

**Current vs intended:** The library has **no tables and no rows**. FG-015 did not create it. FG-016 authorizes the smallest V1 library for the Ontario / City of Ottawa / coach-house POC. Population happens only in the **implementation** prompt, as human-reviewed curated records. This document does **not** populate rules.

---

## Purpose

A governed **Permit / Planning / Approval Rules Library** is required for meaningful Pass 2 analysis ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)).

It is **not** the Contract / Warranty Legal Content Gate.

It is **not** org commercial intelligence. Records are **platform-governed**.

---

## V1 record (conceptual)

A rule/reference must be able to preserve:

- jurisdiction (FG-015 platform definition; not free-text AHJ invention)
- issuing authority
- source title
- rule category
- concise governed rule statement
- source citation / URL / document reference
- `effective_from`
- `effective_to` / superseded
- `reviewed_at`
- provenance
- applicability
- approval / review state
- active / superseded state

Exact column names are an implementation detail. Do not overbuild a national legal CMS.

---

## Authority

Operational rules: **authoritative governmental / AHJ sources only**.

Not governing authority: ChatGPT, Cursor, blogs, contractor websites, search snippets, generic summaries. Secondary sources may assist research; they must not become the approved source.

AI **cannot** mark regulatory content **APPROVED**.

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

Ordinary org office UX has **no** rule CRUD (same fail-closed spirit as FG-015 jurisdiction definitions).

---

## Coverage (V1)

```text
ONTARIO / CITY OF OTTAWA
COACH HOUSE / ADDITIONAL DWELLING
RURAL / NORTH GOWER REFERENCE CASE
```

Unknown / unimplemented jurisdictions: **RULE COVERAGE NOT AVAILABLE**. No Ottawa fallback.

---

## This architecture does not authorize (until FG-016 implementation)

- Creating tables or migrations in this documentation pass
- Populating Pratt-specific conclusions
- Runtime web lookup
- A national library
- Reuse of contract/warranty templates as zoning/permit rules
