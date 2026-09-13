# FG-024 Slice C — Contract generation + immutable project snapshot preflight

| Attribute | Value |
|-----------|--------|
| Status | **PREFLIGHT COMPLETE.** Product **NOT AUTHORIZED / NOT IMPLEMENTED.** Do **not** begin Slice C product. Do **not** begin Slice D. |
| Date | 2026-09-13 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) Slice C only |
| Parent | Slice A **CLOSED / OPERATIONAL FOR UAT**. Slice B **CLOSED / OPERATIONAL FOR UAT**. [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. Live current **`c2d3e4f5a6b7 (head)`**. Library **empty**. |
| Alembic | Live current **`c2d3e4f5a6b7 (head)`**. Repository head **`c2d3e4f5a6b7`**. One graph head. This preflight creates **no** migration. |
| Product | CalibraytAI (formerly CalibAi) |
| Tenant | Brayman Construction Inc. / ORG-001 |
| Parent SHA | `a176db36034af17309fd3f3e7e8c9a58043d6f56` (`docs: close FG-024 Slice B after live UAT`) |

```text
FG-024 SLICE C PREFLIGHT:
COMPLETE
PRODUCT NOT AUTHORIZED
PRODUCT NOT IMPLEMENTED
NO MIGRATION
NO LIVE DB MUTATION
NO LEGAL DRAFTING
NO ONTARIO / U.S. POPULATION
NO CONTRACT ISSUANCE
NO NATIVE SIGNING
NO SLICE D
NO V1 RESCORE
LEGAL CONTENT GATE: EMPTY
APPROVED != ACTIVE
GENERATED != EXECUTED
ADR-051 §6: DEFERRED / FAIL-CLOSED ON THAT BRANCH
NEW ADR: NOT REQUIRED
SCHEMA: REQUIRED LATER (ADDITIVE / NOT CREATED)
V1 REMAINS 60% / 4 OF 11
```

This document freezes Slice C **generation + immutable project-snapshot architecture** for a later bounded product prompt. It does **not** authorize that prompt. It does **not** reopen Slice A, Slice B, ADR-050, or ADR-051.

**Subsequent status (2026-09-13, documentation close):** Full suite **809 passed**, 2738 warnings, **545.74s**, exit **0**. Product remains **NOT AUTHORIZED / NOT IMPLEMENTED**. Legal Content Gate remains **empty**.

**Out of this preflight:** Slice C product code; Alembic; live DB mutation; Ontario/U.S. legal population; Family 05 legal approval; Native Signing product; Slice D watchers/alerts; V1 rescore; website; HostPapa; AiRIA.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Slice A library + selector **live / empty / fail-closed**. Slice B source/update foundation **live**. Legal Content Gate **empty**. Family 05 **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. Outputs 1–3 exist. Output 4 does **not**. No generated-contract tables. No generator. Fail-closed for contracts is coded at selection and by absence of generation. |
| **Intended (Slice C later product)** | Assemble an ACTIVE counsel-approved jurisdiction package with governed commercial/project facts and an approved presentation master; generate a project contract artifact; freeze an immutable project snapshot with provenance. Still **no** live Legal Content Gate population. Still **no** Native Signing. Still **no** customer issuance as execution. |
| **Future** | 06D Ontario counsel content. V1-07 Native Signing handoff. Slice D live monitoring (recommended POST-V1). Additional jurisdictions POST-V1 (06J). |

---

## 2. Slice C ownership (verified)

The expected proposition is **correct** under existing [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) authority.

Slice C owns:

```text
PROJECT JURISDICTION
→ ACTIVE COUNSEL-APPROVED JURISDICTION PACKAGE
→ ORGANIZATION-APPROVED COMMERCIAL CONTENT
→ GOVERNED CONTRACT TEMPLATE
→ GENERATED CONTRACT
→ FROZEN CONTRACT SNAPSHOT
```

Concretely:

- consume Slice A selection / fail-closed (`select_legal_content_package_for_project`);
- assemble governed legal objects from the selected **ACTIVE** package;
- assemble commercial/project variables from existing authoritative records;
- apply an approved presentation master as **visual/structure only**;
- generate the contract / execution-package artifact;
- freeze an immutable project snapshot with enough provenance to prove exactly what was generated.

### What Slice C does **not** own

| Track | Owner | Do not move into Slice C |
|-------|--------|--------------------------|
| Legal-content `APPROVED` | Legal Content Gate | AI/tools cannot approve |
| Library persistence / selection / fail-closed lookup | Slice A / ADR-050 | Reuse; do not fork |
| Source/update / candidate / review | Slice B / ADR-051 | Reuse provenance; do not become a second library |
| Live source monitoring / alerts | Slice D | Out |
| Jurisdiction **identity** | ADR-037 / FG-015 | Reuse resolver only |
| Permit Rules / AHJ | ADR-038 / FG-016 | Not contract clauses |
| Presentation-master bytes / family identity | FG-022 | Visual only |
| Brand overlay | FG-017 / ADR-040 | Lawful commercial presentation only |
| Native Signing UI, capture, verification, signer identity, signing audit | V1-07 | Separate process track |
| Four-output **scorekeeping** | V1-04 register | Tracks Output 4; does not own the engine |
| A second contract library | Forbidden | One FG-024 library |

Do not reopen Slice A selector behaviour. Do not reopen Slice B source-class / `APPROVED` ≠ `ACTIVE` rules.

---

## 3. Generation preconditions (fail-closed)

Generation may succeed **only** when **all** of the following are true. Any missing condition → **FAIL CLOSED**. No silent substitute.

| # | Condition | Authority |
|---|-----------|-----------|
| A | Project jurisdiction **resolved** (ADR-037) | Slice A selector already BLOCK on `JURISDICTION_UNRESOLVED` |
| B | Slice A selector returns **AVAILABLE** | Live `select_legal_content_package_for_project` |
| C | Selected package `library_state` is **ACTIVE** | ADR-050 / FG-024; `APPROVED` ≠ `ACTIVE` |
| D | Package is inside its **effective-date** window for the generation date | FG-024 date model; unresolved conflict → BLOCK |
| E | Required legal-content objects in that package are **APPROVED** as content versions **and** included in the **ACTIVE** package | Legal Content Gate + Slice A objects |
| F | Required approved **presentation master** exists for the document family | FG-022; Family 05 is presentation only |
| G | Authoritative `Project` / `EstimateVersion` exists and is org-valid | project-document-package source-contract principle |
| H | Required commercial/project variables are complete enough to fill governed slots | Do not invent missing legal or commercial facts |
| I | Organization / project ownership is valid (tenant isolation) | ADR-041 / existing org scope |
| J | No other fail-closed condition exists (LIMITED marketed as full; SUPERSEDED with no ACTIVE replacement; pending-generation branch — see §8) | Slice A fail-closed matrix |

### Empty library today (must be preserved)

```text
Ontario project
→ Slice A selector
→ BLOCK (JURISDICTION_NOT_SUPPORTED / empty library)
→ NO contract generation
```

A generation engine **must never** cause:

- generic North American fallback;
- Family 05 legal fallback;
- Permit Rules legal fallback;
- draft / PROPOSED / COUNSEL_REVIEW legal-content fallback;
- cross-jurisdiction substitution;
- AI-created legal content marked APPROVED or ACTIVE.

This invariant is already live at selection. Slice C must not weaken it.

---

## 4. Contract assembly inputs

Do not invent fields the repository does not already govern.

### A. Legal content

From the **ACTIVE** counsel-approved jurisdiction package selected by Slice A. Object bodies, versions, and package identity. Warranty content attaches as a schedule **when the jurisdiction package requires it** ([legal-content-and-templates.md](../governance/legal-content-and-templates.md)). Slice B provenance may be **cited** (source/version/effective dates); Slice B candidates are **not** legal authority.

### B. Presentation master

From FG-022 approved reusable master identity / version / SHA. Family 05 is the Ontario-contract **visual** family. It is **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED / NOT FOR EXECUTION / NOT FOR SIGNATURE**. Presentation controls structure. It does **not** create legal authority.

### C. Commercial / project facts (existing records only)

| Fact | Existing owner |
|------|----------------|
| Organization | `Organization` / Brand Profile (FG-017) overlay **only where lawful** |
| Customer | `Client` |
| Project | `Project` |
| Project location / jurisdiction identity | `ProjectLocation` / ADR-037 |
| Estimate / version | `Estimate` / `EstimateVersion` |
| Scope, exclusions, allowances, price, tax | EstimateVersion lines + pricing snapshot when present |
| Schedule/date facts | Only where already stored on Project / commercial context; do not invent |

Do not treat Permit findings, Family 05 draft clauses, or EST-2026-0019 occupancy as legal-content fixtures.

### D. Provenance (minimum freeze set)

Enough to prove:

- project / customer / organization identity;
- resolved jurisdiction node;
- jurisdiction-package id + `library_state` + effective-date window;
- legal-content object ids/versions;
- Slice B source/version citations **where used**;
- presentation master identity / version / SHA;
- `EstimateVersion` id (+ pricing/costing snapshot ids when those snapshots governed the totals);
- generation timestamp;
- generating organization / project;
- generation actor (human identifier, not AI);
- generated-document hash where supported.

---

## 5. Immutable snapshot

This is a **mandatory** Slice C requirement. Analogue: Constitution Article 5, [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md), [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md).

Freeze at generation (and retain through issue/sign) so later legal-content updates, template updates, estimate edits, or source changes **cannot silently alter** an already-generated project contract.

| Must freeze | Why |
|-------------|-----|
| Project / customer / organization identity | Provenance |
| Resolved jurisdiction | ADR-037 pin |
| Jurisdiction-package id/version / ACTIVE window | Legal authority |
| Legal-content object ids/versions | Clause identity |
| Rendered legal text **or** a deterministic content snapshot sufficient to reconstruct | Audit |
| Presentation master identity/version/hash | Visual authority |
| `EstimateVersion` id and commercial variables used | Commercial authority |
| Generated document hash | Integrity |
| Generation timestamp / actor / process | Audit |
| Status of the generated instance | Lifecycle |

**Do not** duplicate Slice A library rows as a second library. Snapshot **copies/pins** what was used. Issued or signed snapshots remain immutable; new approved library versions apply **prospectively** only via a **new** generation.

An old snapshot must **never** silently update.

---

## 6. EstimateVersion / commercial freeze

Existing authority:

- [project-document-package.md](project-document-package.md): generated **only from an APPROVED estimate**, and only from an ACTIVE jurisdiction package.
- [legal-content-and-templates.md](../governance/legal-content-and-templates.md): generated only from **APPROVED** estimate with provenance preserved.
- Live `EstimateVersion.status` values: `Draft` / `In Review` / `Issued` / `Accepted` / `Rejected` / `Superseded`. There is **no** `Approved` enum on `EstimateVersion`. Auto-lock statuses: `Issued`, `Accepted`, `Rejected`, `Superseded`.
- Proposal statuses include `Draft` / `Issued` / `Accepted`. ADR-002 freezes **Accepted** proposals.

Frozen from that authority (do not guess beyond it):

| Question | Answer |
|----------|--------|
| Can a **Draft** EstimateVersion generate a contract? | **No.** FAIL CLOSED. |
| Must generation pin a specific EstimateVersion? | **Yes.** Source-contract principle. |
| If EstimateVersion changes after generation? | Existing snapshot **unchanged**. A later commercial revision requires a **new** snapshot if generation is repeated. |
| Can an old snapshot silently update? | **No.** |

### JOEL / CHATGPT ARCHITECT DECISION REQUIRED

Map document-package “APPROVED estimate” onto live statuses before **production** generation UX:

1. Is EstimateVersion `Issued` and/or `Accepted` sufficient?
2. Is an **Issued or Accepted Proposal** also required (output 2 freeze), or is locked EstimateVersion enough?
3. May `In Review` generate? (Preflight recommendation: **No** — not auto-locked.)

This mapping does **not** block a later smallest engine that fail-closes Draft and pins a synthetic locked EstimateVersion in tests. It **does** block claiming a real customer contract may be generated from EST-2026-0019 (Draft / not issued).

---

## 7. Presentation master / Family 05

| Rule | State |
|------|--------|
| Family 05 legal status | **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED / NOT FOR EXECUTION / NOT FOR SIGNATURE** |
| Family 05 presentation status | **APPROVED REUSABLE PRESENTATION MASTER** (FG-022 closed) |
| Slice C role | Visual/document **shell** only, and **only** after ACTIVE legal content exists |
| May Family 05 create legal authority? | **No** |
| Is another governed Ontario-contract master required? | **No second master exists.** Family 05 is the presentation family. Legal body comes from the ACTIVE package, not from Family 05 clauses. |

Do **not** mark Family 05 legally approved. Do **not** silently promote it. Draft presentation viewed **outside** product generation with NOT FOR EXECUTION labels remains allowed as FG-022 presentation only.

---

## 8. Generated-document states

Reuse the existing instance lifecycle. Do **not** invent a second gate.

```text
PROPOSED → APPROVED → GENERATED → VERIFIED → SENT FOR SIGNATURE → SIGNED → SUPERSEDED
```

| Distinction | Rule |
|-------------|------|
| GENERATED DOCUMENT | Slice C artifact + frozen snapshot |
| EXECUTED CONTRACT | Native Signing / customer signature — **not** Slice C |
| Generation equals execution? | **No.** |

`VOID` is not a current document-package state. Do not add it in this preflight. Native Signing recon already has VOIDED/EXPIRED on **signing requests**, not on Slice C generation.

Slice C product may implement through **GENERATED** (and test **VERIFIED** as a human flag if a later prompt includes it). `SENT FOR SIGNATURE` / `SIGNED` remain V1-07.

---

## 9. Native Signing boundary

Slice C **handoff** to V1-07 is: a frozen generated artifact + snapshot identity + hash + provenance.

Slice C does **not** implement: signing UI; signature capture; signature verification; signed-artifact storage; signer identity; signing audit trail.

[contract-esignature-and-signed-change-order.md](contract-esignature-and-signed-change-order.md) remains **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED**. Change Orders are the intended first signing use case. Contract signing stays behind the Legal Content Gate.

Do **not** absorb V1-07.

---

## 10. ADR-051 §6 deferred-policy impact

§6 (generation while an ACTIVE package has `UPDATE_PENDING_REVIEW`) remains **DEFERRED**. This preflight does **not** choose ALLOW, BLOCK, or WARN.

**Does §6 block Slice C engine product?** **No**, if the pending-candidate branch is left **unimplemented and fail-closed**.

Bounded approach for a later product prompt:

1. Prove generation only against an ACTIVE package with **no** pending candidate / `UPDATE_PENDING_REVIEW`.
2. If `UPDATE_PENDING_REVIEW` or an open candidate exists for that ACTIVE package: **do not generate**; do **not** encode ALLOW or WARN as policy. Treat as an unresolved fail-closed branch until Joel decides §6.
3. Empty library remains BLOCK.
4. Do not auto-SUPERSEDE or deactivate ACTIVE (Slice B already forbids this).

§6 remains required before **generation UX against live pending-review packages**. It does not require a new ADR.

---

## 11. Schema decision

**SCHEMA REQUIRED** for later Slice C product. **This pass: no file. No `flask db upgrade`. No live DB mutation.**

Conceptual ownership (names not created):

| Concept | Role |
|---------|------|
| Generated contract instance | Org-scoped, project-tied artifact record and lifecycle state |
| Contract snapshot | Immutable pin of legal + commercial + presentation + provenance used at generation |
| Contract-content snapshot | Frozen legal-text / object-version set (or deterministic equivalent) |
| Generation provenance | Actor, timestamps, hashes, package/object/EstimateVersion/master identities |

Generated project contracts are **organization-scoped and project-tied** (ADR-050). Do not pool one contractor’s generated contracts as another’s legal templates.

A later product prompt that requires schema **must include Joel-approved migration**. Do not generate Alembic casually.

---

## 12. ADR decision

**NEW ADR NOT REQUIRED** before Slice C product code.

Existing sufficient authority:

- [ADR-050](../adr/ADR-050-north-american-legal-content-library-ownership.md) — library ownership / fail-closed; generated snapshots org-scoped;
- [ADR-051](../adr/ADR-051-legal-content-source-and-update-lifecycle.md) — source/update; `APPROVED` ≠ `ACTIVE`; §6 deferred;
- [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) — jurisdiction identity;
- [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) / [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) / Constitution Article 5 — freeze analogues;
- FG-024 Slice C flow and immutability section;
- project-document-package Output 4 rules;
- FG-022 Family 05 presentation boundary.

Remaining open items are **Joel decisions on existing records** (commercial-status mapping; ADR-051 §6), not a new ownership ADR.

---

## 13. V1-04 Output 4 completion contract

V1-04 **tracks** four-output consistency. V1-06 / FG-024 **owns** library + generation. Do **not** rescore now.

| Layer | Completes Output 4? |
|-------|---------------------|
| ENGINE IMPLEMENTED (Slice C product, empty/synthetic) | **No.** Advances 06E/06F implementation. Output 4 remains unimplemented for real use. |
| REAL JURISDICTIONAL CONTENT AVAILABLE (06D ACTIVE Ontario package) | **Required** for production Output 4. |
| REAL CONTRACT GENERATED from an APPROVED estimate + ACTIVE package | **Required** for Output 4 evidence. |
| EXECUTION / SIGNING AVAILABLE | **V1-07.** Generation ≠ execution. Output 4 is the generated execution **package**, not a signed instrument. |

V1-04 Output 4 **COMPLETE** therefore requires V1-06 generation **and** real ACTIVE legal content. Slice C engine alone is insufficient. Signing is a separate completeness track.

---

## 14. Ontario-first path (after engine)

Before a **real** Ontario contract may be generated:

1. Counsel-approved Ontario package (06D) in the Legal Content Gate;
2. Legal Content Gate `APPROVED` on required objects;
3. Platform `ACTIVE` + effective date;
4. Approved presentation master (Family 05 visual; legal body from the package);
5. Complete/frozen project commercial facts (locked EstimateVersion; Proposal rule per Joel decision);
6. Slice C generation engine + snapshot;
7. Later signing path (V1-07) where execution is required.

Do **not** draft Ontario content in this preflight. EST-2026-0019 remains Draft / not issued and is **not** a generation fixture.

---

## 15. Smallest Slice C product (not authorized)

Permitted by current governance **if** a later Joel prompt says so: pytest/synthetic fixtures only; **do not** populate the live Legal Content Gate (same pattern as Slice A/B isolated tests).

Smallest bounded implementation:

1. Additive generated-contract + snapshot tables (Joel-approved migration).
2. Generation service that **reuses** Slice A selector + Slice B provenance citations.
3. Deterministic FAIL CLOSED: empty library; unresolved jurisdiction; Draft EstimateVersion; non-ACTIVE package; §6 pending branch.
4. Synthetic ACTIVE package + synthetic locked EstimateVersion in tests: assembly, immutable snapshot, provenance, document hash, no silent mutation on re-generation with changed library.
5. No UI required. No Native Signing. No Ontario seed. No EST-2026-0019 mutation.

That slice would advance 06E / 06F **engine** without 06D. It would **not** complete V1-04 Output 4. It would **not** mark Family 05 legally approved.

---

## 16. Joel / ChatGPT Architect decisions required

| ID | Decision | Blocks smallest engine? |
|----|----------|-------------------------|
| C1 | Map “APPROVED estimate” to live EstimateVersion / Proposal statuses for **production** generation | **No** if tests use a synthetic locked version and Draft fail-closes |
| C2 | ADR-051 §6 ALLOW / BLOCK / WARN for generation against ACTIVE + pending candidate | **No** if that branch stays unimplemented / fail-closed |
| C3 | Whether warranty schedule is in the smallest engine or a later Slice C increment | **No** if tests pin “required objects” without live warranty language |

Do **not** resolve these in this preflight.

---

## 17. Out of Slice C

- Legal drafting; Ontario or U.S. statutory language
- Marking Family 05 legally approved
- Native Signing product or production activation
- Slice D live monitoring / alerts
- Encoding §6 as ALLOW or WARN
- Second contract system; generic NA fallback
- Website; HostPapa; AiRIA; V1 rescore
- Live Legal Content Gate population
- Customer contract issuance from EST-2026-0019
