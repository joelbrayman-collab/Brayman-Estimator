# Feature Gate FG-024: North American Contract Intelligence & Legal Content Lifecycle

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-024` |
| Feature Name | North American Contract Intelligence & Legal Content Lifecycle |
| Target Milestone | **None.** FG-024 is the governing identifier. Do not assign a new M0xx number. Roadmap Item 15 (contract/warranty when Legal Content Gate is satisfied) is the sequence home. |
| Module | **CONTRACT** stage of PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN. The existing [Legal Content Gate](../governance/legal-content-and-templates.md) remains the approval authority for legal templates and jurisdiction packages. **Projects** owns `ProjectLocation` / jurisdiction identity ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)). Permit Rules Library remains a **separate** domain ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). Native Signing remains a **separate** process track ([contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md)). |
| Date | 2026-09-07 |
| Status | **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** This recording is **not** Feature Gate approval for implementation. Slices A–D are **not** authorized. |
| Architecture | [legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [project-document-package.md](../architecture/project-document-package.md) · [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** · [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) **Accepted** · [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted** · [FG-022](FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1** (presentation only) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |
| Related ADRs | **None new in this recording pass.** A later implementation authorization may require an ADR for library schema / package ownership. Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | Active implementation stream remains [FG-023](FG-023-monitor-v1-estimated-versus-actual.md). This gate does **not** jump the queue. Legal Content Gate remains **empty**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. Native Signing production remains blocked pending counsel process approval. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **RECORDED.** **NOT APPROVED FOR IMPLEMENTATION.** |
| Slice A — Jurisdictional Legal Content Library | **NOT AUTHORIZED** |
| Slice B — Contract Update Engine | **NOT AUTHORIZED** |
| Slice C — Contract generation + frozen snapshot | **NOT AUTHORIZED** |
| Slice D — Legal change monitoring + alerts | **NOT AUTHORIZED** |
| Schema / Alembic | **None.** Do not create a migration from this recording. |
| Legal content population | **None.** Ontario and U.S. packages remain unpopulated. |
| Product code | **None.** |

```text
FG-024:
FUTURE
RECORDED
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NOT FOUR SEPARATE FEATURE GATES
SLICES A–D: NOT AUTHORIZED
LEGAL CONTENT GATE: PRESERVED / STILL EMPTY
FG-023: UNCHANGED ACTIVE IMPLEMENTATION STREAM
ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION
```

Joel/ChatGPT recorded this gate on **2026-09-07** as durable product/governance authority only. Recording is **not** implementation approval. Do **not** draft an implementation preflight from this document.

---

## Purpose

CalibAi shall ultimately provide a governed North American **CONTRACT**-stage capability that:

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

CalibAi is intended for commercialization in **Canada** and the **United States**.

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

FG-024 is **one** linked Feature Gate. Do **not** split these into FG-025 / FG-026 / FG-027.

### Slice A — Jurisdictional Legal Content Library

Future foundation for jurisdiction packages; contract clauses/content objects; warranties; notices/disclosures; prescribed forms where applicable; provenance; source authority; effective dates; counsel-review state; approved versions; supersession; jurisdiction support status.

**Not authorized now.**

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

**Not authorized now.**

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

**Not authorized now.**

### Slice D — Legal change monitoring + alerts

Future capability for authoritative-source monitoring; candidate change detection; effective-date alerts; stale-jurisdiction warnings; counsel-review queue; approved replacement notification; impact alerts for generated-but-unsigned documents where governed.

**Not authorized now.**

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | CalibAi cannot yet generate, version, or keep current jurisdiction-compliant construction contracts. Ontario is documented as a one-jurisdiction Legal Content Gate with an empty register. Hard-coding Ontario, or generating “generic North American” contracts, would not support Canada + U.S. commercialization. |
| 2 | Who is the user? | Office estimator / principal generating customer contracts; counsel/human reviewers of legal-content versions; later, customers who receive/sign frozen contracts. Not Field Web. Not MONITOR. |
| 3 | Which module owns it? | **CONTRACT** stage. Legal Content Gate owns approval of legal content. Projects owns location/jurisdiction facts. Permit Intelligence owns permit rules, not contract clauses. Native Signing owns signing process, not template legal text. Organization Brand Profile / FG-022 own presentation, not legal approval. |
| 4 | What data does it own? | **Future, not created:** jurisdiction legal-content packages and versioned content objects; update-engine candidates and review records; frozen contract-generation snapshots. **This recording owns no schema.** |
| 5 | What data does it reference? | `Project` / `ProjectLocation` / jurisdiction resolver ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)); approved estimate/proposal commercial facts; Organization-approved commercial content ([ADR-040](../adr/ADR-040-organization-brand-profile.md) / FG-017) only where lawful; FG-022 presentation masters (visual only). **Not** Permit Rules as contract clauses. **Not** Field Evidence as legal content. |
| 6 | What may it change? | **This recording:** documentation and discoverability pins listed in this gate. **Later implementation slices:** only what a later approved Cursor prompt allows. |
| 7 | What must it not change? | FG-023 MONITOR product meaning or sequence; Permit Rules Library; FG-022 presentation-master bytes; Native Signing process spec; live DB; models; migrations; issued/signed commercial snapshots; Ontario Family 05 legal status. |
| 8 | What are the acceptance criteria? | **This recording:** FG-024 exists; FUTURE / NOT IMPLEMENTATION-AUTHORIZED; slices A–D pinned; Legal Content Gate preserved; FG-023 unchanged as active stream. **Implementation acceptance:** later, per authorized slice. |
| 9 | What tests are required? | **None** for this docs-only recording. Later slices require dedicated tests before implementation close. |
| 10 | What documentation must be updated? | This Feature Gate; feature-gates README; Legal Content Gate subsequent status; project-document-package pin; platform-roadmap Item 15 / future-programs; docs README; Projects module future line; current-state / session-handoff / chat-workflow-log / milestones / project-state-report as required for discoverability **without** implying product code. |
| 11 | Does it require an ADR? | **Not in this recording pass.** ADR-037 already pins one jurisdiction resolver for later contract consumers. ADR-002 / Constitution Article 5 already pin historical-record immutability. A later implementation prompt may require an ADR for library schema or package ownership. |
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
| Source retrieval date | When CalibAi obtained the source |
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

CalibAi must **not** silently generate a supposedly jurisdiction-compliant contract from generic content in these states.

---

## Relation to CalibAi lifecycle

FG-024 belongs principally to **CONTRACT**.

It may consume Project jurisdiction from **PLAN** and approved commercial/project data from **PRICE**. It remains the governed legal/document authority for CONTRACT.

It does **not** own MONITOR, LEARN, BUILD actuals, Permit Intelligence conclusions, or Native Signing production activation.

Active implementation stream remains **FG-023 MONITOR V1**. This recording does **not** authorize jumping the queue.

---

## Out of scope (this recording and until a later implementation prompt)

- Product code, schema, migrations, routes, forms
- Ontario or U.S. legal-content drafting or population
- Legal advice
- AI-generated clauses marked APPROVED
- Counsel approval of any template
- Native Signing implementation or production activation
- Signed Change Order product work
- FG-023 interruption or expansion
- QuickBooks / payroll / GL / AP / AR
- LEARN
- Generic North American fallback contracts

---

## Approval

| Role | State |
|------|--------|
| Joel / ChatGPT | **Recorded** 2026-09-07 as FUTURE product/governance authority. **Not** implementation-approved. |
| Cursor | Docs recording only. No product code. No migration. No legal-content population. |
| Implementation | **NOT AUTHORIZED** until Joel/ChatGPT later approve this gate **for implementation** and issue a bounded slice prompt. |

**Next governed action for the platform remains FG-023 Slice C execution.** Do **not** start FG-024 Slice A from this recording.
