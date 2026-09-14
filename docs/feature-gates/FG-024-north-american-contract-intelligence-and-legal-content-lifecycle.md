# Feature Gate FG-024: North American Contract Intelligence & Legal Content Lifecycle

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-024` |
| Feature Name | North American Contract Intelligence & Legal Content Lifecycle |
| Target Milestone | **None.** FG-024 is the governing identifier. Do not assign a new M0xx number. Roadmap Item 15 (contract/warranty when Legal Content Gate is satisfied) is the sequence home. |
| Module | **CONTRACT** stage of PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN. The existing [Legal Content Gate](../governance/legal-content-and-templates.md) remains the approval authority for legal templates and jurisdiction packages. **Projects** owns `ProjectLocation` / jurisdiction identity ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)). Permit Rules Library remains a **separate** domain ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). Native Signing remains a **separate** process track ([contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md)). |
| Date | 2026-09-07 |
| Status | **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / OVERALL OPEN / PARTIAL.** Live current **`d3e4f5a6b7c8 (head)`**. Repository Alembic head **`d3e4f5a6b7c8`**. Slice A architecture preflight: [fg-024-slice-a-legal-content-library-preflight.md](../architecture/fg-024-slice-a-legal-content-library-preflight.md). Slice B architecture preflight: [fg-024-slice-b-legal-content-source-lifecycle-preflight.md](../architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md). Slice C architecture preflight: [fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md). Evidence [testing/fg024-slice-a-live-migrate-bounded-uat-record.md](../testing/fg024-slice-a-live-migrate-bounded-uat-record.md) · [testing/fg024-slice-b-live-migrate-bounded-uat-record.md](../testing/fg024-slice-b-live-migrate-bounded-uat-record.md) · [testing/fg024-slice-c-live-migrate-bounded-uat-record.md](../testing/fg024-slice-c-live-migrate-bounded-uat-record.md). |
| Architecture | [legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [project-document-package.md](../architecture/project-document-package.md) · [fg-024-slice-a-legal-content-library-preflight.md](../architecture/fg-024-slice-a-legal-content-library-preflight.md) · [fg-024-slice-b-legal-content-source-lifecycle-preflight.md](../architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md) · [fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) · [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** · [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) **Accepted** · [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted** · [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted** · [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** · [FG-022](FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1** (presentation only) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |
| Related ADRs | [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted** 13 Sep 2026. [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** 13 Sep 2026. Slice A **CLOSED / OPERATIONAL FOR UAT** 13 Sep 2026. Slice B **CLOSED / OPERATIONAL FOR UAT** 13 Sep 2026. Slice C **CLOSED / OPERATIONAL FOR UAT** 13 Sep 2026. Live current **`d3e4f5a6b7c8 (head)`**. Repository head **`d3e4f5a6b7c8`**. Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | Active implementation stream remains [FG-023](FG-023-monitor-v1-estimated-versus-actual.md). This gate does **not** jump the queue. Legal Content Gate remains **empty**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. Native Signing production remains blocked pending counsel process approval. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED / OVERALL OPEN / PARTIAL.** Slice A **CLOSED / OPERATIONAL FOR UAT**. Slice B **CLOSED / OPERATIONAL FOR UAT**. Slice C **CLOSED / OPERATIONAL FOR UAT**. |
| Slice A — Jurisdictional Legal Content Library | **CLOSED / OPERATIONAL FOR UAT** |
| Slice B — Contract Update Engine | **CLOSED / OPERATIONAL FOR UAT** |
| Slice C — Contract generation + frozen snapshot | **CLOSED / OPERATIONAL FOR UAT** |
| Slice D — Legal change monitoring + alerts | **NOT AUTHORIZED** |
| Schema / Alembic | Live current **`d3e4f5a6b7c8 (head)`**. Repository head **`d3e4f5a6b7c8`**. One graph head. Slice C **applied live**. |
| Legal content population | **None.** Live library **empty**. Ontario and U.S. packages remain unpopulated. Labeled Slice B UAT source/snapshot/candidate rows and labeled Slice C generated-contract rows are synthetic evidence, not legal content and not real customer contracts. |
| Product code | Slice A models + selection service (live / empty). Slice B source / snapshot / candidate / review foundation (live). Slice C generation + immutable snapshot (live / synthetic-UAT proven). Hub CONTRACT fail-closed status (selector result only; no generation control; no legal-admin UI). No Native Signing. |

```text
FG-024:
FUTURE
RECORDED
OVERALL OPEN / PARTIAL
SLICE A CLOSED / OPERATIONAL FOR UAT
SLICE B CLOSED / OPERATIONAL FOR UAT
SLICE C CLOSED / OPERATIONAL FOR UAT
SLICE D: NOT AUTHORIZED
ADR-050: ACCEPTED
ADR-051: ACCEPTED
LEGAL CONTENT GATE: EMPTY
NORTH AMERICAN LIBRARY: PERSISTENCE + RESOLVER SELECTION + CODED FAIL-CLOSED / LIVE / EMPTY
UPDATE FOUNDATION: LIVE
CONTRACT GENERATION: ENGINE LIVE / SYNTHETIC-UAT PROVEN / NO REAL JURISDICTIONAL CONTENT
CONTRACT HUB UX: FAIL-CLOSED STATUS EXPOSED / NO GENERATION CONTROL
V1 SCORE UNCHANGED
ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION
```

Joel/ChatGPT recorded this gate on **2026-09-07** as durable product/governance authority only. Recording is **not** implementation approval.

**Subsequent status (2026-09-12, Slice A preflight):** Architecture preflight **COMPLETE**. [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) drafted **Proposed**. Product implementation remains **NOT AUTHORIZED**. Do **not** begin Slice A product code from the preflight.

**Subsequent status (2026-09-13):** [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted** by Joel Brayman / ChatGPT Architect (architecture / fail-closed ownership only). Slice A architecture prerequisite **satisfied**. Product implementation remains **NOT AUTHORIZED / NOT IMPLEMENTED**. Do **not** rescore V1.

**Subsequent status (2026-09-13, Slice A product):** Empty-library persistence, ADR-037-backed selection, and coded fail-closed are **implemented in the repository**. Alembic **`b1c2d3e4f5a6`** created. Live migration **not** run. Legal Content Gate remains **empty**. No Ontario/U.S. population. No UI. No contract generation. V1 score **unchanged**. Do **not** begin Slice B/C/D.

**Subsequent status (2026-09-13, Slice B architecture):** Existing-governance reconciliation **validated** the Slice B source/update preflight against this gate / ADR-050 / Legal Content Gate. [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted** (architecture only). Slice B **PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED / NOT IMPLEMENTED**. Generation-while-`UPDATE_PENDING_REVIEW` **deferred**. V1 score **unchanged**. Do **not** begin Slice B product.

**Subsequent status (2026-09-13, Slice A live migrate + bounded office UAT):** Live `flask db upgrade` **PASS**. Live current **`b1c2d3e4f5a6 (head)`**. Empty library **PASS**. Commercial continuity **PASS**. Fail-closed UAT **PASS**. Focused **17 passed**. Full **782 passed**. Slice A **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. Evidence [fg024-slice-a-live-migrate-bounded-uat-record.md](../testing/fg024-slice-a-live-migrate-bounded-uat-record.md). V1 score **unchanged**. Do **not** begin Slice B/C/D.

**Subsequent status (2026-09-13, Slice B product foundation):** Source / snapshot / candidate / review foundation **implemented in the repository**. Additive Alembic **`c2d3e4f5a6b7`** created. Live `flask db upgrade` **not** run. Live current remains **`b1c2d3e4f5a6 (head)`**. Legal Content Gate remains **empty**. No Ontario/U.S. population. No live monitoring. No contract generation. No Native Signing. Generation-while-`UPDATE_PENDING_REVIEW` remains **deferred**. Slice B **NOT LIVE-MIGRATED / NOT OFFICE-UAT / NOT CLOSED**. Slice C/D **NOT AUTHORIZED**. V1 score **unchanged** (**60% / 4 of 11**).

**Subsequent status (2026-09-13, Slice B live migrate + bounded office UAT):** Live `flask db upgrade` **PASS**. Live current **`c2d3e4f5a6b7 (head)`**. Empty Slice-B tables **PASS**. Commercial continuity **PASS**. Source/snapshot/candidate/AI-boundary/Slice-A regression UAT **PASS**. Focused Slice B **16 passed**. Focused Slice A **17 passed**. Full **809 passed**. Slice B **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. Evidence [fg024-slice-b-live-migrate-bounded-uat-record.md](../testing/fg024-slice-b-live-migrate-bounded-uat-record.md). Legal Content Gate remains **empty**. V1 score **unchanged**. Do **not** begin Slice C/D.

**Subsequent status (2026-09-13, Slice C preflight):** Architecture preflight **COMPLETE**. Product **NOT AUTHORIZED / NOT IMPLEMENTED**. No migration. No live DB mutation. No legal drafting. ADR-051 §6 remains **deferred**. New ADR **not** required. Evidence [fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md). V1 score **unchanged**. Do **not** begin Slice C product or Slice D.

**Subsequent status (2026-09-13, Slice C product foundation):** Generation + immutable snapshot **implemented in the repository**. Additive Alembic **`d3e4f5a6b7c8`**. Live `flask db upgrade` **not** run at that commit. Live current remained **`c2d3e4f5a6b7 (head)`**. Dedicated Slice C **16 passed**. Slice A **17 passed**. Slice B **16 passed**. Full **825 passed**. Legal Content Gate remains **empty**. Synthetic generation only. No Ontario/U.S. population. No Native Signing. No warranty schedule. C1/C2/C3 unresolved. Slice C was **NOT LIVE-MIGRATED / NOT OFFICE-UAT / NOT CLOSED** at that commit. Slice D **NOT AUTHORIZED**. V1 score **unchanged** (**60% / 4 of 11**).

**Subsequent status (2026-09-13, Slice C live migrate + bounded office UAT):** Live `flask db upgrade` **PASS**. Live current **`d3e4f5a6b7c8 (head)`**. Immediate empty Slice-C tables **PASS**. Commercial continuity **PASS**. Fail-closed / no-fallback / synthetic generation / immutability / pinning / Native Signing boundary / Slice A+B regression UAT **PASS**. Dedicated Slice C **16 passed**. Slice A **17 passed**. Slice B **16 passed**. Full **825 passed**. Slice C **CLOSED / OPERATIONAL FOR UAT**. Gate overall **OPEN / PARTIAL**. Evidence [fg024-slice-c-live-migrate-bounded-uat-record.md](../testing/fg024-slice-c-live-migrate-bounded-uat-record.md). Legal Content Gate remains **empty**. No real jurisdictional content. No real customer contract. C1/C2/C3 remain unresolved. Slice D **NOT AUTHORIZED**. V1 score **unchanged** (**60% / 4 of 11**).

**Subsequent status (2026-09-14, fail-closed CONTRACT Hub UX):** Office Project Hub `#hub-contract` exposes the existing Slice A selector result. Ontario + no ACTIVE counsel-approved package → **BLOCK** with office-safe copy. Selector `select_legal_content_package_for_project` remains authority. No generation control. No override. No Family 05 fallback. No Ontario legal-content population. No activation service. No Native Signing. No schema/migration. Dedicated Hub UX **9 passed**. Focused Hub + Hub UX **22 passed**. Full **838 passed**. Gate overall remains **OPEN / PARTIAL**. Slice D **NOT AUTHORIZED**. FG-024 **not closed**. V1 score **unchanged** (**60% / 4 of 11**).

**Recorded production decisions (2026-09-14; not implemented in this slice):**

- **C1:** Production contract generation requires an Issued Proposal tied to a locked / non-Draft EstimateVersion. A Draft estimate cannot generate a production contract. Generation UX is **not** implemented here.
- **C2:** When an ACTIVE legal package exists and a newer candidate is pending counsel review, production policy is **WARN**. The existing ACTIVE counsel-approved package remains authority until an approved successor is activated. If the ACTIVE package is itself invalid, expired, superseded without a valid replacement, or otherwise fails existing effective-date rules, **BLOCK**. The existing selector does **not** currently return WARN; this slice does not add WARN UI.
- **C3:** Warranty is required for the first Ontario production contract package. Warranty generation is **not** implemented here.
- **Activation:** ACTIVE requires an explicit human-authorized administrative action. AI cannot APPROVE or ACTIVE. Activation is **not** built here.

---

## Purpose

CalibraytAI shall ultimately provide a governed North American **CONTRACT**-stage capability that:

1. maintains jurisdiction-aware approved construction legal content;
2. detects and assesses changes to authoritative legal sources;
3. routes proposed legal-content changes through governed human/counsel review and approval;
4. selects the appropriate approved legal-content package based on Project jurisdiction;
5. generates contracts using approved jurisdiction and organization content;
6. freezes the exact content/version/provenance used for every issued or signed contract;
7. never silently rewrites historical issued or signed contracts when legal content later changes.

Ontario must **not** become a one-off hard-coded contract implementation.

---

## Commercial / product context

CalibraytAI is intended for commercialization in **Canada** and the **United States**.

Architecture must support:

- Canadian provinces and territories
- United States states
- other jurisdictions only where later explicitly required

without requiring architectural redesign for each jurisdiction.

Legal-content population is **incremental**.

| Rollout pin | Value |
|-------------|--------|
| First expected Canadian jurisdiction package | **Ontario** |
| United States packages | Prioritize by commercial demand and sales activity |
| Immediate population of all states/provinces | **Forbidden** |
| This pass | **Do not populate** any jurisdiction |

Architecture first. Counsel-approved content incrementally.

---

## One Feature Gate — four internal slices

FG-024 is **one** linked Feature Gate. Do **not** split these four slices into separate Feature Gates. [FG-025](FG-025-contractor-facing-ux-language-and-terminology-standardization.md) is a **different** product gate (contractor-facing UX language), not a contract-intelligence slice.

### Slice A — Jurisdictional Legal Content Library

Future foundation for jurisdiction packages; contract clauses/content objects; warranties; notices/disclosures; prescribed forms where applicable; provenance; source authority; effective dates; counsel-review state; approved versions; supersession; jurisdiction support status.

**Historical recording fence (2026-09-07):** Preflight complete. Product not authorized then.

**Subsequent status:** Slice A is **CLOSED / OPERATIONAL FOR UAT**. Live library remains **empty**. Slice D remains **Not authorized now**.

### Slice B — Contract Update Engine

Future flow:

```text
SOURCE CHANGE DETECTED
→ CANDIDATE LEGAL UPDATE
→ IMPACT ASSESSMENT
→ HUMAN / COUNSEL REVIEW
→ APPROVED NEW CONTENT VERSION
→ EFFECTIVE-DATE CONTROL
→ JURISDICTION PACKAGE ACTIVATION
```

The Update Engine **maintains** the Legal Content Library. It must **not** independently override Legal Content Gate approval authority.

**Historical recording fence:** Architecture preflight COMPLETE. Product **NOT AUTHORIZED** at that recording.

**Subsequent status:** Slice B is **CLOSED / OPERATIONAL FOR UAT**. [fg-024-slice-b-legal-content-source-lifecycle-preflight.md](../architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md). [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. Live monitoring remains Slice D.

### Slice C — Contract generation + frozen snapshot

Future CONTRACT workflow:

```text
PROJECT JURISDICTION
→ ACTIVE COUNSEL-APPROVED JURISDICTION PACKAGE
→ ORGANIZATION-APPROVED COMMERCIAL CONTENT
→ GOVERNED CONTRACT TEMPLATE
→ GENERATED CONTRACT
→ FROZEN CONTRACT SNAPSHOT
```

If no approved jurisdiction package exists: **FAIL CLOSED.** No silent fallback to a generic North American contract.

**Historical product-foundation fence:** Architecture preflight COMPLETE. Subsequent product foundation was **IMPLEMENTED IN REPOSITORY / NOT LIVE-MIGRATED** at that commit. Alembic **`d3e4f5a6b7c8`** was not applied live at that commit.

**Subsequent status:** Slice C is **CLOSED / OPERATIONAL FOR UAT**. Live current / repository head **`d3e4f5a6b7c8 (head)`**. [fg-024-slice-c-contract-generation-snapshot-preflight.md](../architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md). Service `app/services/contract_generation.py`. Models `GeneratedProjectContract`, `ProjectContractSnapshot`, `ProjectContractSnapshotObject`. ADR-051 §6 remains **deferred**; pending-candidate generation stays unimplemented / fail-closed. GENERATED ≠ EXECUTED. Family 05 remains presentation shell only. No real jurisdictional content. Slice D remains **Not authorized now**.

### Slice D — Legal change monitoring + alerts

Future capability for authoritative-source monitoring; candidate change detection; effective-date alerts; stale-jurisdiction warnings; counsel-review queue; approved replacement notification; impact alerts for generated-but-unsigned documents where governed.

**Not authorized now.**

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | CalibraytAI cannot yet generate, version, or keep current jurisdiction-compliant construction contracts. Ontario is documented as a one-jurisdiction Legal Content Gate with an empty register. Hard-coding Ontario, or generating “generic North American” contracts, would not support Canada + U.S. commercialization. |
| 2 | Who is the user? | Office estimator / principal generating customer contracts; counsel/human reviewers of legal-content versions; later, customers who receive/sign frozen contracts. Not Field Web. Not MONITOR. |
| 3 | Which module owns it? | **CONTRACT** stage. Legal Content Gate owns approval of legal content. Projects owns location/jurisdiction facts. Permit Intelligence owns permit rules, not contract clauses. Native Signing owns signing process, not template legal text. Organization Brand Profile / FG-022 own presentation, not legal approval. |
| 4 | What data does it own? | **Future, not created:** jurisdiction legal-content packages and versioned content objects; update-engine candidates and review records; frozen contract-generation snapshots. **This recording owns no schema.** |
| 5 | What data does it reference? | `Project` / `ProjectLocation` / jurisdiction resolver ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)); approved estimate/proposal commercial facts; Organization-approved commercial content ([ADR-040](../adr/ADR-040-organization-brand-profile.md) / FG-017) only where lawful; FG-022 presentation masters (visual only). **Not** Permit Rules as contract clauses. **Not** Field Evidence as legal content. |
| 6 | What may it change? | **This recording:** documentation and discoverability pins listed in this gate. **Later implementation slices:** only what a later approved Cursor prompt allows. |
| 7 | What must it not change? | FG-023 MONITOR product meaning or sequence; Permit Rules Library; FG-022 presentation-master bytes; Native Signing process spec; live DB; models; migrations; issued/signed commercial snapshots; Ontario Family 05 legal status. |
| 8 | What are the acceptance criteria? | **This recording:** FG-024 exists; FUTURE / NOT IMPLEMENTATION-AUTHORIZED; slices A–D pinned; Legal Content Gate preserved; FG-023 unchanged as active stream. **Implementation acceptance:** later, per authorized slice. |
| 9 | What tests are required? | **None** for this docs-only recording. Later slices require dedicated tests before implementation close. |
| 10 | What documentation must be updated? | This Feature Gate; feature-gates README; Legal Content Gate subsequent status; project-document-package pin; platform-roadmap Item 15 / future-programs; docs README; Projects module future line; current-state / session-handoff / chat-workflow-log / milestones / project-state-report as required for discoverability **without** implying product code. |
| 11 | Does it require an ADR? | **Yes before Slice A product code.** [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) is **Accepted** (13 Sep 2026; architecture only). **Yes before Slice B product code.** [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) is **Accepted** (13 Sep 2026; architecture only). **No new ADR before Slice C product code.** ADR-037 already pins one jurisdiction resolver. ADR-002 / Constitution Article 5 already pin historical-record immutability. Acceptance does **not** authorize product. |
| 12 | Does it require a database migration? | **No** in this recording. Later slices may require additive migrations only after implementation authorization. |

---

## Legal Content Gate (preserved)

FG-024 **extends** [legal-content-and-templates.md](../governance/legal-content-and-templates.md). It does **not** replace it.

Existing rules remain in force:

- AI or tools **cannot independently** set legal content to **APPROVED**
- approved versions are **superseded**, not silently overwritten
- no production use without governed approval
- Family 05 / Allen Jacques document 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**

### Library / package lifecycle (content authority)

Evaluate against existing document-instance lifecycle rather than inventing a second gate.

Existing **generated contract/warranty instance** states ([project-document-package.md](../architecture/project-document-package.md)) remain:

`PROPOSED → APPROVED → GENERATED → VERIFIED → SENT FOR SIGNATURE → SIGNED → SUPERSEDED`

For **library packages and content objects**, FG-024 records these conceptual states (not implemented):

| State | Meaning |
|-------|---------|
| PROPOSED | Candidate content exists; not counsel-approved |
| COUNSEL REVIEW | Routed for human/counsel review (named extension of the existing gate; sits before APPROVED) |
| APPROVED | Counsel/human authorized that **content version** |
| ACTIVE | Platform-activated for generation under governed effective-date rules |
| SUPERSEDED | Replaced by a later approved version; retained for provenance |

`APPROVED` and `ACTIVE` are **not** the same date. See effective-date model.

AI may later assist with identifying potential changes, comparing sources, summarizing, identifying affected objects, proposing **candidate** revisions, impact assessment, and routing review.

AI must **not**: declare legal compliance; provide final legal approval; mark content counsel-approved; activate unapproved content; silently modify approved legal authority; rewrite issued or signed contracts.

Human/counsel approval remains authoritative.

---

## North American Legal Content Library (Slice A contract)

Architecturally support jurisdiction-specific content **where applicable**, without assuming every jurisdiction needs the same objects:

- construction contract provisions
- home-improvement requirements
- consumer protection provisions
- cancellation rights
- payment requirements
- construction lien / mechanic's lien notices
- warranty requirements
- prescribed notices
- statutory disclosures
- mandatory forms
- other counsel-approved legal content

Do **not** draft legal language in this recording.

Presentation (FG-022) is **not** legal approval. Organization commercial content is allowed only where lawful and **not** in conflict with jurisdiction authority.

---

## Contract Update Engine (Slice B contract)

The future engine must preserve enough provenance to answer:

WHAT CHANGED? WHO ISSUED THE CHANGE? WHAT IS THE AUTHORITATIVE SOURCE? WHEN WAS IT PUBLISHED? WHEN DOES IT BECOME EFFECTIVE? WHICH JURISDICTION IS AFFECTED? WHICH CONTENT OBJECTS ARE AFFECTED? WHICH CONTRACT / WARRANTY / NOTICE TEMPLATES ARE AFFECTED? WHICH CURRENT JURISDICTION PACKAGE IS SUPERSEDED? HAS COUNSEL REVIEWED THE CANDIDATE? WHICH VERSION WAS APPROVED? WHEN DOES THE NEW VERSION BECOME ACTIVE?

No untraceable legal-content changes.

Impact assessment must be capable of identifying: affected jurisdiction; content objects; contract/warranty/notice templates; currently active package; proposed replacement version; effective-date impact; future projects affected; generated-but-not-issued documents requiring regeneration; issued-but-not-signed documents requiring review **where governed**. Signed historical contracts remain immutable.

---

## Effective-date / version model

These dates are **not** assumed identical:

| Date | Role |
|------|------|
| Source publication date | When the issuing authority published the change |
| Source retrieval date | When CalibraytAI obtained the source |
| Legal effective date | When the legal change governs |
| Counsel approval date | When the content version was APPROVED |
| Platform activation date | When the version became ACTIVE for generation |
| Contract generation date | When a project document was generated |
| Contract issue date | When it was issued to the customer |
| Contract signing date | When it was signed |

The system must deterministically select the appropriate **APPROVED** content version according to governed effective-date rules. Unresolved effective-date conflict → **FAIL CLOSED**.

---

## Immutability (mandatory invariant)

Once a contract is **issued or signed**, freeze at least:

- Project jurisdiction
- Legal Content Package identity
- legal-content versions
- organization content/template version
- effective-date authority
- generation timestamp
- provenance
- document identity/hash where supported

Later legal updates **must not** mutate issued contracts, signed contracts, their frozen snapshots, or their provenance. New approved versions apply **prospectively** under governed rules.

This is the CONTRACT analogue of Constitution Article 5, [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md), and issued Permit snapshot immutability ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

---

## Jurisdiction support status

Reuse existing vocabulary where it already exists. For **jurisdiction packages**, the platform must distinguish states equivalent to:

| State | Meaning |
|-------|---------|
| SUPPORTED / COUNSEL-APPROVED | ACTIVE approved package sufficient to generate |
| LIMITED | Partial approved coverage; must not be displayed as fully supported |
| UPDATE PENDING REVIEW | An approved package exists, but a candidate update is in COUNSEL REVIEW |
| NOT YET SUPPORTED | No approved package |

A jurisdiction containing only draft, candidate, or AI-generated material must **never** be marketed or displayed as fully supported.

---

## Project jurisdiction boundary

Reuse existing ProjectLocation / jurisdiction resolution ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md); [FG-015](FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md)). Do **not** duplicate jurisdiction identity.

| Domain | Authority |
|--------|-----------|
| Location / jurisdiction **identity** | Projects / one resolver |
| Permit **rules** content | Permit Rules Library / ADR-038 |
| Contract **legal** content | Legal Content Gate / FG-024 |

A Project jurisdiction may select **both** permit rules and contract packages. The content authorities remain independent. Do not treat permit findings as contract clauses.

---

## Failure mode

FG-024 must **FAIL CLOSED** where legal authority is insufficient, including:

- unsupported jurisdiction
- no approved package
- package expired/superseded without approved replacement
- unresolved effective-date conflict
- required counsel review incomplete

CalibraytAI must **not** silently generate a supposedly jurisdiction-compliant contract from generic content in these states.

---

## Relation to CalibraytAI lifecycle

FG-024 belongs principally to **CONTRACT**.

It may consume Project jurisdiction from **PLAN** and approved commercial/project data from **PRICE**. It remains the governed legal/document authority for CONTRACT.

It does **not** own MONITOR, LEARN, BUILD actuals, Permit Intelligence conclusions, or Native Signing production activation.

**Historical recording (2026-09-07):** Active implementation stream remained **FG-023 MONITOR V1**. That recording did **not** authorize jumping the queue.

**Subsequent status:** [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) is **CLOSED / OPERATIONAL FOR UAT**. FG-024 overall remains **OPEN / PARTIAL**. Slice D remains **Not authorized now**.

---

## Out of scope (this recording and until a later implementation prompt)

The 2026-09-07 recording excluded product code. Slice A, Slice B, and Slice C product and live-migrate are **done**. Still out of scope:

- Hub / CONTRACT UI
- Ontario or U.S. legal-content drafting or population
- Legal advice
- AI-generated clauses marked APPROVED
- Counsel approval of any template
- Native Signing implementation or production activation
- Signed Change Order product work
- Slice D product
- QuickBooks / payroll / GL / AP / AR
- LEARN
- Generic North American fallback contracts

---

## Approval

| Role | State |
|------|--------|
| Joel / ChatGPT | **Recorded** 2026-09-07. Slice A product authorized 13 Sep 2026. Slice A live-migrate + UAT authorized 13 Sep 2026. Gate overall **OPEN / PARTIAL**. |
| Cursor | Slice A live `flask db upgrade` **PASS**. Bounded office UAT **PASS**. No UI. No legal seed. |
| Implementation | Slice A **CLOSED / OPERATIONAL FOR UAT**. |

**Next governed action for the platform is STOP.** Slice A is **CLOSED / OPERATIONAL FOR UAT**. Slice B is **CLOSED / OPERATIONAL FOR UAT**. Slice C is **CLOSED / OPERATIONAL FOR UAT**. Do **not** begin Slice D, counsel drafting, or Native Signing from this UAT close.
