# FG-024 Slice B — Legal-content source / update lifecycle preflight

| Attribute | Value |
|-----------|--------|
| Status | **PREFLIGHT COMPLETE.** [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (architecture only). Product **NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Do **not** begin Slice B product code. |
| Date | 2026-09-13 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) Slice B only |
| Parent | Slice A **CLOSED / OPERATIONAL FOR UAT**. [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. Live current **`b1c2d3e4f5a6 (head)`**. Library **empty**. |
| Alembic | Unchanged. Live current = repository head **`b1c2d3e4f5a6`**. One graph head. **No migration in this pass.** |
| Product | CalibraytAI (formerly CalibAi) |
| Tenant | Brayman Construction Inc. / ORG-001 |

```text
FG-024 SLICE B PREFLIGHT:
COMPLETE
PRODUCT NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NO MIGRATION
NO LIVE DB MUTATION
NO LEGAL DRAFTING
NO ONTARIO / U.S. POPULATION
NO CONTRACT GENERATION
NO SIGNING
NO V1 RESCORE
ADR-051 ACCEPTED / ARCHITECTURE ONLY
LEGAL CONTENT GATE: EMPTY
LIVE MONITORING: SLICE D / NOT SLICE B
APPROVED != ACTIVE
AI CANNOT APPROVE OR ACTIVATE
ACTIVE-PACKAGE GENERATION-WHILE-PENDING: DEFERRED
V1 REMAINS 60% / 4 OF 11
```

This document freezes Slice B **source / update lifecycle architecture** for a later bounded product prompt. It does **not** authorize that prompt. It does **not** reopen Slice A.

**Subsequent status (2026-09-13):** Existing-governance reconciliation. Preflight **validated** against FG-024 / ADR-050 / Legal Content Gate. [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (architecture only). §6 generation-while-`UPDATE_PENDING_REVIEW` **deferred** — not option B. Product remains **NOT AUTHORIZED / NOT IMPLEMENTED**. V1 remains **60% / 4 of 11**. Legal Content Gate remains **empty**.

**Out of this preflight:** Slice B product code; Slice C generation; Slice D live watchers/alerts; Ontario/U.S. legal population; Family 05 legal approval; Native Signing product; V1-04 product work; V1 rescore.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Slice A library tables live and **empty**. Selection + coded fail-closed **operational**. Legal Content Gate **empty**. Family 05 **COMMERCIAL_DRAFT**. No source register. No candidate-update records. No contract generation. |
| **Intended (Slice B later product)** | Manual/counsel-driven source registration, snapshot custody, candidate change records, human/counsel review routing, and provenance sufficient to answer FG-024’s update questions. Still **no** legal-language population. Still **no** executable contract. Still **no** live web monitoring. |
| **Future** | Slice C generation + freeze. 06D Ontario counsel content. Slice D automated source monitoring / alerts (**V1 register recommendation: POST-V1**). Native Signing (separate track). |

---

## 2. Slice B ownership (verified)

The expected proposition is **correct** under existing FG-024 authority:

> Slice B owns the governed **SOURCE / UPDATE LIFECYCLE** that can identify and record potential changes to jurisdictional legal content while preserving human/counsel approval authority.

[FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) names Slice B the **Contract Update Engine**:

```text
SOURCE CHANGE DETECTED
→ CANDIDATE LEGAL UPDATE
→ IMPACT ASSESSMENT
→ HUMAN / COUNSEL REVIEW
→ APPROVED NEW CONTENT VERSION
→ EFFECTIVE-DATE CONTROL
→ JURISDICTION PACKAGE ACTIVATION
```

The Update Engine **maintains** the Legal Content Library. It must **not** independently override the Legal Content Gate.

[v1-completion-register.md](../v1-completion-register.md) §9.2: Slice B V1 is **manual/counsel-driven** update + supersession. Automated live monitoring is Slice D / recommended POST-V1.

### What Slice B does **not** own

| Track | Owner | Do not move into Slice B |
|-------|--------|--------------------------|
| Persistence, jurisdiction selection, fail-closed lookup | Slice A / [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) | Already closed / operational |
| Contract generation, project snapshot/freeze, executable output | Slice C | Out |
| Automated/live source watchers, stale-jurisdiction alerts, unsigned-document impact alerts | Slice D | Out |
| Native Signing process | V1-07 | Separate |
| Permit Rules / AHJ determinations | ADR-038 / FG-016 | Separate legal/regulatory domain |
| Presentation masters | FG-022 | Visual only |
| Brand overlay | FG-017 / ADR-040 | Not legal approval |
| Jurisdiction **identity** | ADR-037 / FG-015 | Reuse; do not duplicate |

Do not reopen Slice A schema or fail-closed selection.

---

## 3. Legal source classes

No source class may silently become **APPROVED** legal content. AI cannot mark any class APPROVED or ACTIVE.

| Class | What it is | What repository authority permits | What it must not do |
|-------|------------|-----------------------------------|---------------------|
| **A. Official primary source** | Legislation, regulations, official government / regulatory-authority publications | May be **recorded as evidence**. Supplies “authoritative source” identity for FG-024 provenance questions. Analogous in spirit to Permit Rules “authoritative governmental / AHJ sources only” ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)) — **do not reuse permit_rules rows**. | Must not auto-APPROVE, auto-ACTIVE, or auto-SUPERSEDE an ACTIVE package. Do **not** inventory Ontario/U.S. statutes in this preflight. |
| **B. Counsel-supplied source / interpretation** | Counsel memorandum, marked-up clause set, or other human legal work product submitted into the gate | May become a **candidate**. After **human/counsel** action it may become **APPROVED** (content version). Activation remains a separate human action (`APPROVED` ≠ `ACTIVE`). | Counsel text is not ACTIVE until governed activation. AI restating counsel is not approval. |
| **C. Organization-supplied commercial content** | Org-approved commercial overlay (Brand Profile / FG-017 commercial presentation; later org templates) | Slice C may combine org commercial content with an ACTIVE jurisdiction package **only where lawful** and **not in conflict** with jurisdiction authority ([ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) §5). | Must not become jurisdiction legal authority. Must not fill an empty Legal Content Gate. |
| **D. Secondary / informational source** | Commentary, blogs, ChatGPT/tool research, Family 05 presentation draft, unofficial summaries | May be stored as **informational evidence** attached to a candidate for reviewers. Legal Content Gate: AI/tool output is **not** an approved legal/commercial source. | Must not be treated as primary legal authority. Must not APPROVE, ACTIVE, or replace Class A/B. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. |

Do not invent jurisdiction-specific source inventories here.

---

## 4. Provenance model (minimum)

FG-024 requires the update engine to answer:

WHAT CHANGED? WHO ISSUED THE CHANGE? WHAT IS THE AUTHORITATIVE SOURCE? WHEN WAS IT PUBLISHED? WHEN DOES IT BECOME EFFECTIVE? WHICH JURISDICTION IS AFFECTED? WHICH CONTENT OBJECTS ARE AFFECTED? WHICH CONTRACT / WARRANTY / NOTICE TEMPLATES ARE AFFECTED? WHICH CURRENT JURISDICTION PACKAGE IS SUPERSEDED? HAS COUNSEL REVIEWED THE CANDIDATE? WHICH VERSION WAS APPROVED? WHEN DOES THE NEW VERSION BECOME ACTIVE?

Slice A `provenance` text on packages is **not** sufficient for those questions. Slice B needs structured records. Reuse existing date vocabulary; do not invent a second date model.

| Concept | Existing term / home | Required on Slice B candidate path? |
|---------|----------------------|-------------------------------------|
| Jurisdiction | ADR-037 node / package `jurisdiction_definition_id` | **Yes** |
| Source identity | New (source register) | **Yes** |
| Source class | A / B / C / D above | **Yes** |
| Source citation / URL / document reference | Permit analogue `source_citation` / `source_url`; object `source_citation` | **Yes** where applicable |
| Source publication date | FG-024 “Source publication date” | **Yes** when known |
| Source retrieval / received date | FG-024 “Source retrieval date” | **Yes** |
| Legal effective date | FG-024 “Legal effective date”; package `effective_from` / `effective_to` | **Yes** when claimed; unresolved → FAIL CLOSED at generation |
| Source version / revision | Permit analogue `version_number` | **Yes** when known |
| Source snapshot hash / fingerprint | FG-024 immutability “document identity/hash where supported” | **Yes** for stored snapshots |
| Affected package / content object | Slice A package + object ids | **Yes** |
| Change summary | New (candidate) | **Yes** |
| Previous version | `superseded_by_id` / object `version_number` | **Yes** when replacing |
| Proposed replacement | Candidate → new PROPOSED object/package version | **Yes** (may be empty body until counsel drafts) |
| Reviewer / review status | `COUNSEL_REVIEW`; `counsel_approved_by` is a **human identifier, not AI** | **Yes** |
| Approval authority | Legal Content Gate | **Human/counsel only** |
| Counsel approval date / platform activation date | FG-024 date table; package `counsel_approved_at` / `activated_at` | **Yes** at those transitions |
| Timestamps | `created_at` pattern | **Yes** |

Do not create schema in this pass.

---

## 5. Candidate-change lifecycle

Tested against FG-024 library states. Preserve **`APPROVED` ≠ `ACTIVE`**.

```text
SOURCE EVIDENCE (Class A–D recorded; none is APPROVED by recording)
    ↓
CHANGE DETECTED / CANDIDATE CREATED   → library_state PROPOSED
    ↓
ROUTED                                → COUNSEL_REVIEW
    ↓
HUMAN / COUNSEL ACTION                → APPROVED  (content version only)
    ↓
SEPARATE HUMAN ACTIVATION             → ACTIVE    (effective-date rules)
    ↓
LATER APPROVED REPLACEMENT            → prior version SUPERSEDED
```

| Actor | May create | Must not |
|-------|------------|----------|
| Automation / human ingest | Source register rows; source snapshots; **PROPOSED** candidates; impact-assessment **draft** fields; route-to-review flags | APPROVED, ACTIVE, SUPERSEDE of an ACTIVE package, generation |
| AI (later, only if a later prompt + ADR-010 path allows) | Difference identification; summaries; mapping evidence → candidate objects; flags of potentially affected objects; review-prep material; **PROPOSED** candidate text labelled as candidate | Legal advice as system authority; APPROVED; ACTIVE; silent rewrite of approved clauses; convert Class D into Class A; bypass the Legal Content Gate |
| Human office actor | Ingest sources; create/route candidates; record impact notes | Mark counsel-APPROVED unless they are the governed approval authority |
| Counsel / Legal Content Gate authority | APPROVED on a **content version**; refuse/return | Be replaced by AI. Activation is still a separate governed action |
| Platform activation actor (human, governed) | ACTIVE under effective-date rules after APPROVED | Activate PROPOSED / COUNSEL_REVIEW / unapproved AI text |

Empty-library fail-closed remains: no ACTIVE package → BLOCK (already live).

---

## 6. AI authority boundary (frozen)

From FG-024 and the Legal Content Gate. This preflight does **not** authorize a real external AI provider ([ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) remains **Proposed**).

**AI MAY** (architecture only; not product-authorized here):

- identify differences between source snapshots
- summarize source changes
- map source evidence to candidate objects
- flag potentially affected content
- prepare review material
- propose **candidate** revisions labelled PROPOSED

**AI MUST NOT:**

- mark content APPROVED
- mark content ACTIVE
- issue legal advice as system authority
- silently rewrite approved clauses
- activate a candidate because a source changed
- replace counsel
- convert secondary commentary into primary legal authority
- bypass the Legal Content Gate
- rewrite issued or signed contracts

Smallest later Slice B product must enforce the MUST NOT list **without** requiring an AI provider.

---

## 7. ACTIVE-package / update behaviour

**DEFERRED.** Joel Brayman / ChatGPT Architect, 13 Sep 2026 Slice B governance reconciliation: do **not** invent a new generation policy. Acceptance of ADR-051 does **not** choose option B.

Existing authority **does** freeze these fragments:

| Fragment | Authority | Meaning |
|----------|-----------|---------|
| Support status `UPDATE_PENDING_REVIEW` | FG-024; Slice A `SUPPORT_STATUSES` | “An approved package exists, but a candidate update is in COUNSEL REVIEW.” Mere candidate creation is **not** “no package.” |
| Unresolved effective-date conflict | FG-024 / ADR-050 / Slice A `effective_date_unresolved` | Generation **FAIL CLOSED** |
| Package SUPERSEDED with no ACTIVE replacement | FG-024 / ADR-050 | Generation **FAIL CLOSED** |
| Required counsel review incomplete | FG-024 fail-closed list | Blocks using **unapproved** content as if approved. Does **not** by itself define whether an existing ACTIVE package stays usable. |
| Issued/signed contracts | Constitution Article 5; FG-024 immutability | Later updates apply **prospectively**. Historical snapshots do not mutate. |
| `APPROVED` ≠ `ACTIVE` | ADR-050 / FG-024 | Source change must not skip activation. |

Prompt options versus authority:

| Option | Immediate effect of source evidence | Verdict |
|--------|-------------------------------------|---------|
| **A** | Existing ACTIVE package immediately unavailable | **Not supported** as an automatic rule. Contradicts `UPDATE_PENDING_REVIEW`. |
| **B** | Review flag; existing ACTIVE remains usable | **Compatible** with `UPDATE_PENDING_REVIEW`, but **not fully frozen** as the only rule. |
| **C** | Depends on effective date / severity / human determination | **Partially already true** for unresolved effective-date conflict (FAIL CLOSED). Severity / human withdrawal of ACTIVE **before** a replacement is APPROVED+ACTIVE is **not** frozen. |
| **D** | Another governed rule | None beyond the fragments above. |

**This preflight does not choose B as product policy.** Generation behaviour while `UPDATE_PENDING_REVIEW` is set, when the ACTIVE package is still inside its `effective_from`/`effective_to` window, remains **deferred** until a later Joel decision required before Slice C / generation UX.

Until that later decision: a later Slice B product must **not** auto-SUPERSEDE or auto-deactivate ACTIVE merely because a candidate exists.

---

## 8. Live-monitoring boundary

| Capability | Slice | V1 register |
|------------|-------|-------------|
| Source registration | **B** | V1 (manual) |
| Manual source ingestion | **B** | V1 |
| Source snapshot storage | **B** | V1 |
| Deterministic comparison of stored snapshots | **B** (optional in smallest product) | V1 |
| AI-assisted comparison | **B architecture**; product only if later authorized | Not authorized now (ADR-010 Proposed) |
| Continuous / automated web monitoring, watchers, stale-jurisdiction alerts, unsigned-document impact alerts | **D** | Recommended **POST-V1** (register §9.2 / §13 #3) |

**Live monitoring is not included in Slice B.** Do not assume continuous web monitoring belongs here.

---

## 9. Schema decision

**SCHEMA REQUIRED** for a later authorized Slice B product. **This pass: no file. No Alembic. No live DB mutation.**

Slice A already owns packages + objects. Slice A preflight already reserved “update-engine candidate tables (Slice B)” and “legal-source watcher tables (Slice D).”

Conceptual objects only (do not create):

| Object | Role |
|--------|------|
| Legal source | Platform-governed source identity: class A–D, jurisdiction node, citation/URL, issuing identity |
| Source snapshot | Immutable retrieved/received copy or hash + retrieval date + publication date when known |
| Candidate change | PROPOSED / COUNSEL_REVIEW record linking snapshot → affected package/object → change summary → proposed replacement id |
| Review event | Append-only human/counsel actions (route, return, approve-version, refuse). Approver identifier must not be an AI actor |
| Provenance relationship | Source snapshot ↔ candidate ↔ content-object version ↔ package version |

Do **not** add watcher/cron/alert tables in Slice B (Slice D). Do **not** add generated-contract snapshot tables (Slice C). Do **not** seed legal language. Do **not** mutate `permit_rules`.

If a later product prompt requires schema, that prompt must include **Joel-approved migration**.

---

## 10. ADR decision

| Decision | Value |
|----------|--------|
| Required before Slice B product code? | **YES** |
| This pass | [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (architecture only) |
| Accept now? | **Yes** (13 Sep 2026 existing-governance reconciliation). Product still **No**. |
| Implement from Accepted? | **No** until a bounded product prompt |
| ADR-050 still governs? | **Yes** — library ownership, fail-closed selection, no generic fallback, `APPROVED` ≠ `ACTIVE`. Do not reopen. |

Constitution Article 8: new source-class authority, candidate-update ownership, and Slice B/D monitoring boundary are durable architecture. They are **not** fully inside ADR-050 (library ownership / fail-closed lookup).

Open decision **inside** Accepted ADR-051: ACTIVE-package usability during `UPDATE_PENDING_REVIEW` when effective dates still cover is **deferred**. Acceptance did **not** silently choose option B.

---

## 11. Empty Legal Content Gate

This preflight **does not** populate the gate. No Ontario clauses, Ontario package, U.S. clauses/package, or generic Canada / USA / North America package.

The architecture must work on an empty library: candidates may exist with empty bodies; generation remains BLOCK until an ACTIVE counsel-approved package exists.

---

## 12. Ontario-first implications (not product scope)

Ontario remains the **first expected** Brayman real-life package. Ontario is **not** the architectural scope of CONTRACT.

Before counsel-approved Ontario content can be safely loaded, Slice B infrastructure must exist to:

1. record the official and counsel sources that justify the package;
2. retain snapshots / hashes so later updates are comparable;
3. create PROPOSED candidates without marking them APPROVED;
4. route counsel review;
5. keep `APPROVED` ≠ `ACTIVE`;
6. supersede rather than silently overwrite;
7. leave Slice A fail-closed in force until activation.

Do **not** draft Ontario content in this pass.

---

## 13. Smallest Slice B product (not authorized)

**Source / provenance / review foundation only. No generation. No live monitoring. No legal seed.**

A later Joel-authorized prompt, **after ADR-051 is Accepted**, could implement:

1. Additive empty tables for legal source, source snapshot, candidate change, and review event (Joel-approved migration).
2. Manual source registration and snapshot ingest (no scraper, no watcher).
3. Create **PROPOSED** candidates linked to provenance; optional deterministic snapshot diff. **Do not** auto-deactivate ACTIVE.
4. Human route to `COUNSEL_REVIEW`. Counsel/human may mark a **content version** APPROVED. Activation remains a separate human action (Slice A states).
5. Tests: AI/service helpers cannot set APPROVED or ACTIVE; candidate ≠ generatable package; empty library still BLOCK; Family 05 / Permit Rules not consulted; no generic fallback; no legal-language seed; no Slice D watcher.
6. No Hub CONTRACT generation UI. Optional later read-only “update pending” display is **out** unless the ACTIVE-policy decision is settled.

That slice would advance 06H **engine** without 06D, 06E, 06F, or Slice D. It would **not** complete V1-04 or V1-06. It would **not** flip BMR DEMO READY.

Do **not** begin that slice from this document.

---

## 14. V1 scoring (unchanged)

| Package | Status | Factor | Contribution |
|---------|--------|--------|--------------|
| V1-04 | PARTIAL | 0.50 | 4.0 |
| V1-06 | PARTIAL | 0.25 | 4.0 |
| Readiness | **60% / 4 of 11** | — | — |

Do **not** rescore because a Slice B preflight now exists. 06H remains **ARCHITECTURE COMPLETE / NOT IMPLEMENTED** until product exists.

---

## 15. Prohibited scope (this pass)

Application code · models · routes · services · templates · CSS/JS · behavioural Slice B tests · Alembic revision · live DB mutation · legal-content population · Family 05 legal-status change · Native Signing product · Slice C/D product · accepting ADR-008 or ADR-010 · website · HostPapa · rescore V1

**Subsequent (2026-09-13):** [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. The original preflight prohibition on accepting ADR-051 is closed. Slice B **product** remains prohibited until a bounded implementation prompt.
