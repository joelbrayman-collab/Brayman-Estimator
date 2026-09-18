# CORE CLOSE / Project lifecycle — owner decision freeze

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Date | 2026-09-18 |
| Surface | Future contractor-facing **Project Close** operating lifecycle, including **Punch List** → **Project Completion Sign-Off** → **Close Project** |
| Owner | **Projects** owns Project operating lifecycle (`ACTIVE` / `CLOSED`) and the Punch List / Completion Sign-Off product direction. Native Signing remains an overlay (do **not** reopen [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md)). BUILD Time / Field / Extra Work **consume** lifecycle; they do not own it. PERF-C **consumes** shared current-operating-Project authority without reopening sealed fact types. |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. Decisions O–P remain the historical **LEARN Closeout** record. **No new ADR in this freeze.** CORE CLOSE is a subsequent owner decision, not a rewrite of ADR-053 Closeout. [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** (`Project` remains the lifecycle hub). |
| Parent gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. Historical FG-035 **CLOSE** heading remains **Closeout review and LEARN evidence quality** / **NOT AUTHORIZED**. This freeze records **CORE CLOSE** as a **distinct** current product authority. Do **not** rewrite that historical heading destructively. |
| People & Access | [people-and-access-product-direction.md](people-and-access-product-direction.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Close / Reopen authority is Instance Owner or System Administrator. Do **not** invent another access domain. Do **not** implement People & Access from this file. |
| PERF-C | [fg-035-perf-c-product-definition.md](fg-035-perf-c-product-definition.md) **SEALED**. Live UAT organization-wide occupancy noise is **VALID**. Future PERF-C may consume shared current-operating-Project authority **without** reopening PERF-A/B/C fact types. Do **not** invent a PERF-C-only filter. |
| Home Office | [v1-desktop-contractor-experience-product-direction.md](v1-desktop-contractor-experience-product-direction.md) **RECORDED / NOT IMPLEMENTED**. Home Office must later consume the same current-operating-Project authority. Do **not** implement Home Office from this file. |
| Schema | **NONE in this freeze.** Future implementation will require an approved additive Project operating-lifecycle field. Do **not** reuse `Project.status`. Do **not** add `ARCHIVED` as a third operating state in V1. Do **not** add `is_uat` / `demo_project` / `synthetic_project`. |
| Baseline | HEAD / `origin/main` **`9765c7da56d96a3dafd431fef5901e0d821c3393`**. Live Alembic **`a0b1c2d3e4f5 (head)`**. Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved. |
| V1 | **NOT RESCORED** (official **65% / 4 of 11**; secondary Functional V1 Build **79% / 22 of 28**). |
| Prompt completeness | Freeze prompt §§0–35 **ACCEPTED**. Heading **§36 DESKTOP** arrived with **no body**. This freeze does **not** invent additional desktop-shell redesign or a Field Punch List product. Presentation already frozen in §§21–24 is recorded below. |

**Subsequent status (2026-09-18 CORE CLOSE Slice A):** **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NOT PUSHED.** Revision **`b2c3d4e5f6a7`** (down_revision **`a0b1c2d3e4f5`**). Live Alembic remains **`a0b1c2d3e4f5`**. `Project.operating_state` **ACTIVE / CLOSED**. `ProjectOperatingStateEvent`. `list_current_operating_projects`. No Close/Reopen action. No consumer switches. CORE CLOSE overall remains **PARTIAL / NOT OPERATIONAL**.

**Subsequent Current vs Intended (Slice A working tree):** Shared query `list_current_operating_projects` exists in `app/services/shared_api.py` and returns `operating_state=ACTIVE` only. `list_organization_projects` still returns all organization Projects and remains the live consumer path. Live DB is **not** migrated. Close / Reopen / Punch List / Completion Sign-Off remain **NOT IMPLEMENTED**.

**Subsequent owner decisions (2026-09-18 Slice A authorization; later slices only):**

1. **CLOSED PROJECT DISCOVERY.** Future Projects UI: **Current | Closed**. Default **Current**. Closed provides historical discovery. No Archive product.
2. **RETURNED TIME AFTER CLOSE.** Existing Time submitted before Close and later RETURNED may be corrected/resubmitted after Close as administrative completion of an existing record. NEW Time remains blocked.
3. **EXISTING CHANGE ORDER / PUNCH LIST AFTER CLOSE.** This subsequent freeze **supersedes** any earlier Slice A authorization note that would have allowed substantive Draft Change Order scope / line-item edits after Close.

```text
PHYSICAL WORK COMPLETION
is not the same thing as:
ADMINISTRATIVE CHANGE ORDER COMPLETION.

A Project must NOT reach an executable Project Completion Sign-Off
while known physical work associated with Original Scope or an
existing Change Order remains incomplete.

If an existing Change Order contains physical work that has NOT been
completed:
- the incomplete work must be represented on the Project Punch List;
- the Punch List remains OPEN until that work is completed;
- Project Completion Sign-Off remains NOT ELIGIBLE FOR SIGNATURE while
  that Punch List item remains open.

OPEN PUNCH LIST
=
HARD GATE ON PROJECT COMPLETION SIGN-OFF SIGNATURE ELIGIBILITY.

Once the physical work associated with an existing Change Order has
been completed, remaining ADMINISTRATIVE processing of that already-
existing Change Order may continue as necessary to preserve an honest
Project record.

Examples of administrative completion may include:
- approval/rejection of an already-existing Change Order;
- completion of an already-authorized signing ceremony;
- completion of an existing governed status workflow;
- other non-scope-changing administrative processing of that existing
  record.

Do NOT broadly authorize substantive editing of Draft Change Order
scope or line items after Project Close.

If the scope, pricing, quantities, or substantive work definition of a
Change Order still needs to be created or materially changed, the
Project should not be treated as operationally complete.

A CLOSED Project may NOT receive a NEW Change Order.

If genuinely new Change Order scope is required after Project Close:
REOPEN PROJECT FIRST.
Then normal governed Change Order workflow may resume.

CLOSE BLOCKS NEW OPERATIONAL RECORDS.
IT DOES NOT STRAND LEGITIMATE ADMINISTRATIVE COMPLETION OF RECORDS
THAT ALREADY EXIST.

BUT:
INCOMPLETE PHYSICAL WORK IS NOT ADMINISTRATIVE COMPLETION.
INCOMPLETE PHYSICAL WORK MUST BE COMPLETED THROUGH THE PUNCH LIST
BEFORE PROJECT COMPLETION SIGN-OFF MAY BE EXECUTED.

Do not infer physical completion merely from Change Order status.
Change Order administrative status and physical completion are
different facts.
```

This decision does **not** authorize Punch List, Change Order, Close, Reopen, or Completion Sign-Off implementation in Slice A.

This file is the frozen **owner product-direction** contract for CORE CLOSE / Project operating lifecycle, Punch List, and Project Completion Sign-Off. It is **not** an implementation prompt. It supersedes unexecuted Close / archive-filter discussion, including the PERF-C live-UAT note that treated lifecycle as an unspecified Active/Archived future.

Do **not** implement CORE CLOSE, Punch List, Completion Sign-Off, Native Signing changes, People & Access, Home Office, LEARN, QB-T, UAT Project Close, filtering, or schema from this file.

```text
CORE CLOSE / PROJECT LIFECYCLE:
RECORDED MANDATORY PRODUCT DIRECTION
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NO SCHEMA
NO MIGRATION
NO NEW ADR
NO NEW FEATURE GATE
NO UI
V1 NOT RESCORED

V1 OPERATING LIFECYCLE:
ACTIVE / CLOSED
NO ARCHIVED THIRD STATE
DO NOT REUSE Project.status

CORE CLOSE ≠ LEARN CLOSEOUT
CORE CLOSE ≠ FINANCIAL CLOSE
CORE CLOSE ≠ MEDIA ARCHIVE
CORE CLOSE ≠ DELETION

CLOSE MUST NOT REWRITE HISTORY
CLOSE MUST NOT DELETE HISTORY
CLOSE IS A STATE CHANGE, NOT A PURGE

WARNINGS INFORM.
HUMANS DECIDE.

OPEN PUNCH LIST = HARD GATE ON COMPLETION SIGN-OFF
UNSIGNED COMPLETION SIGN-OFF AFTER PUNCH LIST COMPLETE =
STRONG WARNING ON CLOSE, NOT A HARD CLOSE GATE
```

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Every organization Project is in the de facto operating set via `list_organization_projects` (`app/services/shared_api.py`). `Project.status` is an unconstrained CRM / pipeline label (default `Lead`; create-form options include Lead, Estimating, Proposal Sent, Contracted, Active, Completed, Archived). **Never filtered.** No Close / Reopen product. No Punch List. No Project Completion Sign-Off. No Project delete product. PERF-C enumerates all organization Projects. |
| **Intended (this freeze)** | Owner decisions in §§2–32 **ACCEPTED** as product direction. CORE CLOSE distinguishes **current operating work** from **completed / historical work**. Punch List → Project Completion Sign-Off → Close Project is the governed closeout sequence. **Not implementation-authorized.** |
| **Future (not this freeze)** | Bounded implementation (separate prompt; Rule 7 migration approval if schema is chosen). People & Access Instance Owner / Sys Admin product. Home Office current-work briefing consuming the same authority. LEARN Closeout. Media Closed Project Archive. Financial / QB-T. Field Punch List (not frozen here). |

---

## 2. CORE CLOSE is distinct from LEARN Closeout

**V1 CORE CLOSE** is the operating Project lifecycle required to distinguish:

```text
CURRENT OPERATING WORK
from
COMPLETED / HISTORICAL WORK
```

CORE CLOSE is **not**:

- LEARN evidence-quality Closeout
- financial close
- accounting close
- media archive
- deletion
- contract termination

Historical FG-035 **CLOSE** language remains associated with **LEARN Closeout** and stays **NOT AUTHORIZED**. ADR-053 O–P remains: Closeout establishes learning evidence quality; Project Complete does **not** automatically mean LEARN-eligible.

LEARN remains separately unauthorized. CORE CLOSE can occur without LEARN.

---

## 3. Project lifecycle model

V1 operating lifecycle has **exactly**:

```text
ACTIVE
CLOSED
```

Do **not** add **ARCHIVED** as a third operating lifecycle state in V1.

Do **not** reuse existing `Project.status` for operating lifecycle.

Existing `Project.status` remains the CRM / pipeline label. Those values do **not** determine current operating-set membership.

---

## 4. ACTIVE Project

**ACTIVE** means the Project belongs to the contractor's current operating work.

ACTIVE Projects are eligible for normal current-work surfaces and new operational activity according to existing product authority.

---

## 5. CLOSED Project

**CLOSED** means the Project is no longer part of current operating work.

CLOSED does **not** mean: deleted; purged; rewritten; financially settled; LEARN eligible; legally released; media archived.

CLOSED is an operating lifecycle state.

---

## 6. Shared current-operating-Project authority

There must be **one** governed shared authority for **CURRENT OPERATING PROJECTS**.

Do **not** create independent lifecycle filters in PERF-C, Home Office, Schedule, Field, Time, or Projects.

Expected future concept: `list_current_operating_projects(...)` or a repository-consistent equivalent. The **exact implementation name is not frozen. The authority is.**

Historical / direct Project reads continue to use organization + id identity (today `get_organization_project`), not the current-operating list.

---

## 7. Current-work surfaces

CLOSED Projects leave normal **CURRENT** operating selections/views, including as applicable:

- default Projects operating list
- Schedule Project pickers / current operating schedule
- Field Project pickers / current operating work
- Time **NEW-entry** Project picker
- API current Project listing where used for operating selection
- PERF-C / Company Attention
- future Home Office current-work briefing

Exact presentation of historical Projects remains separately handled within the relevant surface. Do **not** implement here.

---

## 8. Historical Project access

Closing a Project must **not** make its history disappear.

A CLOSED Project remains historically accessible through governed historical navigation / direct access.

Preserve access to applicable:

- Project Hub
- estimates and estimate versions
- customer Proposals
- contracts
- executed artifacts
- Project Work
- Change Orders
- Time
- Schedule history
- MONITOR
- PERF
- attachments
- Field originals
- audit / history records
- Project documents
- Completion Sign-Off

Historical MONITOR and Project-level PERF remain viewable on a CLOSED Project. Closing removes the Project from current organization-level attention / current-work enumeration. It does **not** rewrite or destroy historical Project performance facts. PERF-A/B/C fact authority remains **SEALED**.

---

## 9. History law

Freeze explicitly:

```text
CLOSE MUST NOT REWRITE HISTORY.
CLOSE MUST NOT DELETE HISTORY.
CLOSE IS A STATE CHANGE, NOT A PURGE.
```

Do **not** use hard Project deletion as the mechanism for removing a Project from current work.

**No Delete Project product is authorized here.**

People & Access law remains analogous: **DELETE USER = REMOVE ACCESS, NOT REMOVE HISTORY.**

---

## 10. Post-Close new operational work

Once a Project is CLOSED, **no NEW operational work** may be created until the Project is reopened.

This includes:

- new Project Work
- new Extra Work
- new Change Order
- new Time
- new Schedule item
- moving / creating future Schedule work
- new Field operational capture
- new active work assignment

Exact implementation guards remain future implementation work.

---

## 11. In-flight administrative completion

Closing a Project does **not** prevent legitimate administrative completion of records already in flight.

After Close, authorized office users may continue to complete / review existing items where necessary to preserve an honest record.

At minimum directionally permit:

- review / approve / return existing submitted Time
- approve / reject / finalize an already-existing pending Change Order
- view existing documents
- view historical Project records

Those actions must **not** become a route for creating **NEW** operational work.

Exact service-level guard matrix is implementation design.

**Subsequent owner freeze (2026-09-18, supersedes any Draft-CO line-item-edit-after-Close reading of this section):** incomplete physical work on Original Scope or an existing Change Order is **Punch List work**, not administrative Change Order completion. Do **not** infer physical completion from Change Order administrative status. Do **not** broadly authorize substantive Draft Change Order scope / pricing / quantity / work-definition edits after Close. NEW Change Order after Close requires Reopen. Remaining administrative processing of an already-existing Change Order (approval/rejection, existing signing ceremony, governed status workflow) may continue after physical work is complete. This does **not** implement Punch List, Change Order, Close, Reopen, or Completion Sign-Off.

---

## 12. Reopen Project

**REOPEN PROJECT is permitted.**

Reopen returns a CLOSED Project to **ACTIVE** and therefore to the shared current operating set.

Reopen must **not**:

- rewrite history
- recreate deleted data
- create new Project identity
- reset Time
- reset Change Orders
- reset Schedule history
- reset MONITOR
- reset PERF

Existing history remains continuous.

Existing pending / inactive / current records may become operationally relevant again after Reopen. Implementation must **not** silently recreate work. Reopen restores Project eligibility for future operating work. It does **not** manufacture new work.

---

## 13. Close trigger

**CLOSE PROJECT is a MANUAL HUMAN ACTION.**

Do **not** automatically Close a Project because:

- Schedule appears complete
- contract is generated
- contract is signed
- final invoice exists
- money is paid
- accounting is synchronized
- MONITOR reaches a threshold
- LEARN becomes eligible

The authorized human decides when the Project should leave current operating work.

---

## 14. Close / Reopen authority

Only **CONTRACTOR INSTANCE OWNER** or **SYSTEM ADMINISTRATOR** may Close or Reopen a Project.

Ordinary Project / Operational users may **not** Close / Reopen.

Ordinary Company / Management access alone must **not** automatically confer Close / Reopen authority.

System Administrator product is **not yet implemented**. Instance Owner / Sys Admin authority is already frozen in People & Access product direction.

Do **not** invent another access domain. Do **not** implement permission architecture in this freeze. Record the authority requirement for future implementation.

Preserve People & Access law: Instance Owner is protected root authority. System Administrator is an Owner-appointed broad / full administrator. Only the Instance Owner appoints Sys Admin. Sys Admin may never impair Instance Owner authority. CORE CLOSE must consume those authorities when they are implemented. Do **not** reopen People & Access.

---

## 15. Existing Project migration default

When the operating lifecycle field is introduced, **ALL existing Projects default to ACTIVE**.

This preserves existing behaviour.

Do **not** infer CLOSED from:

- Project name
- Project ID
- current `Project.status`
- synthetic / UAT-looking naming
- Schedule completion
- Estimate status
- Contract status

Any later Close of existing Projects is an explicit governed action.

---

## 16. UAT / synthetic Projects

Synthetic / UAT Projects do **not** require a separate Project lifecycle architecture merely because they are test Projects.

They may use the same **ACTIVE / CLOSED** operating lifecycle.

Do **not** add `is_uat`, `demo_project`, `synthetic_project`, or equivalent solely to clean current operating lists.

Do **not** infer UAT identity from names for migration.

Existing UAT Projects remain **ACTIVE** until separately governed Close actions are authorized.

---

## 17. Punch List — core closeout workflow

Freeze a future contractor-facing **PUNCH LIST** as part of Project Close.

Intended closeout sequence:

```text
WORK SUBSTANTIALLY COMPLETE
→ CUSTOMER WALKTHROUGH
→ PUNCH LIST
→ ALL PUNCH LIST ITEMS COMPLETE
→ PROJECT COMPLETION SIGN-OFF ELIGIBLE FOR SIGNATURE
→ CUSTOMER + CONTRACTOR SIGNATURES WHERE OBTAINED
→ PROJECT COMPLETION SIGN-OFF RETAINED AS PROJECT DOCUMENT
→ CLOSE PROJECT
```

Punch List is part of **CLOSE**. It is **not** LEARN.

Punch List records incomplete / deficiency items identified before final Project Completion Sign-Off.

Future Punch List should be: contractor-facing; simple; clean; easy to read; easy to complete; associated with the Project; historically retained.

Do **not** design full implementation / schema in this freeze.

---

## 18. Punch List completion gate

**PROJECT COMPLETION SIGN-OFF CANNOT BE SIGNED WHILE ANY PUNCH LIST ITEM REMAINS OPEN.**

This is a **HARD DOCUMENT-ELIGIBILITY RULE**. This is not merely a warning.

If Punch List has open items, Completion Sign-Off remains **NOT ELIGIBLE FOR SIGNATURE**. The contractor must complete the Punch List first.

OPEN PUNCH LIST ITEMS DO NOT BELONG ON AN EXECUTED DOCUMENT SAYING THE PROJECT IS COMPLETE.

Punch List must first reach **NO OPEN ITEMS**. Only then is Project Completion Sign-Off signable.

This supersedes any earlier discussion suggesting that the signed Completion Sign-Off should list unfinished Punch List items as exceptions.

---

## 19. Project Completion Sign-Off

Freeze a future customer-facing Project document: **PROJECT COMPLETION SIGN-OFF** (or repository-consistent equivalent final product label).

The document is intended to provide a clear record that Project work has been completed following completion of the Punch List.

It should be: clean; simple; highly legible; checkbox-oriented; appropriate for desktop / tablet review; appropriate as a generated PDF / frozen artifact.

Do **not** turn it into a dense legal contract.

Directionally include:

**PROJECT INFORMATION**

- Project name / number
- Customer
- Project address
- Completion date

**COMPLETION CHECKLIST** (examples; do not freeze unnecessary generic items that do not apply to every contractor / project):

- Original contracted work completed
- Approved Change Orders completed
- Customer walkthrough completed
- Punch List completed
- required closeout documents provided where applicable

Prefer Project-derived governed content where possible.

Future Completion Sign-Off should derive appropriate content from the governed Project record rather than forcing the contractor to recreate the Project manually. Relevant future sources may include: Original Scope / Project Work; approved Change Orders; Punch List; Project / customer identity; governed Project documents.

Do **not** reopen those authorities. Do **not** implement generation here.

---

## 20. Completion acknowledgement — not automatic release

Project Completion Sign-Off is a **completion acknowledgement / sign-off**.

Do **not** characterize it as: release; waiver; final legal release — unless separately approved legal content later establishes that language.

Any jurisdiction-specific legal effect or release language requires separate legal-content governance / counsel approval.

---

## 21. Signatures and executed artifact

Future Project Completion Sign-Off should support:

```text
CUSTOMER SIGNATURE + DATE
CONTRACTOR SIGNATURE + DATE
```

Reuse existing Native Signing / executed-artifact infrastructure where architecturally appropriate.

Do **not** reopen Native Signing or implement signing changes here.

Once executed, Project Completion Sign-Off becomes a frozen historical Project artifact. It belongs in **PROJECT DOCUMENTS** or repository-consistent Project document custody. It must remain accessible after Project Close. It must not be rewritten by Close / Reopen.

---

## 22. Customer refuses / fails to sign

A customer may **not** indefinitely prevent the contractor from administratively Closing their own Project.

If Punch List = **COMPLETE** but Project Completion Sign-Off = **NOT EXECUTED**, then Close Project remains available to the authorized Instance Owner / System Administrator.

CalibraytAI must provide a **STRONG WARNING** before proceeding.

Conceptual warning (exact copy is not frozen here):

```text
No signed Project Completion Sign-Off is on file.
Closing this Project will remove it from current operating work
without an executed customer completion acknowledgement.
```

The authorized human may **CANCEL** or **CLOSE PROJECT ANYWAY**.

---

## 23. Warning vs hard gate

```text
OPEN PUNCH LIST:
HARD GATE ON COMPLETION SIGN-OFF SIGNATURE ELIGIBILITY.

NO EXECUTED COMPLETION SIGN-OFF AFTER PUNCH LIST COMPLETE:
STRONG WARNING ON PROJECT CLOSE.
NOT A HARD CLOSE GATE.
```

Preserve:

```text
WARNINGS INFORM.
HUMANS DECIDE.
```

The Punch List eligibility rule protects the truthfulness of the completion document. The Close warning preserves contractor control over the internal operating lifecycle.

Pending Time, pending Change Orders, unresolved warnings, or other non-Punch-List administrative conditions should **not** automatically become hard Close blockers unless separately governed. The implementation should surface relevant warnings. The Instance Owner / Sys Admin decides whether to proceed. Do **not** design all warning types here.

The Punch List hard gate is a **document-eligibility** exception to “warnings never block.” It does **not** authorize a general blocking-warning engine. Validation / integrity failures remain fail-closed.

---

## 24. Close does not require financial completion

Project Close does **not** require:

- paid in full
- zero balance
- final invoice
- QuickBooks synchronization
- Sensitive Financial completion

No financial hard gate. Sensitive Financial remains separate. QB-T remains separate.

---

## 25. Close does not require LEARN

CORE CLOSE can occur without LEARN.

Project Close does **not** automatically mean LEARN eligible.

LEARN remains a later separately governed intelligence / evidence-quality capability. Preserve ADR-053 O–P.

---

## 26. Desktop / Field (prompt §36 truncated)

The freeze prompt ended at heading **§36 DESKTOP** with no body.

Already frozen presentation (do not expand):

- Punch List: contractor-facing, simple, clean, easy to read and complete
- Project Completion Sign-Off: clean, simple, highly legible, checkbox-oriented, appropriate for **desktop / tablet** review and generated PDF / frozen artifact
- People & Access desktop UX law remains: **USE AVAILABLE SPACE GENEROUSLY, NOT DENSELY**

This freeze does **not**:

- redesign the existing desktop shell
- freeze a Field Punch List or Field Close product
- invent Print / Help / Voice surfaces for Close

Field current-work pickers remain in the current-operating-Project authority (§7). Field Punch List product is **not frozen** and is **not implementation-authorized**.

---

## 27. Feature Gate answers (governance; not implementation authorization)

These answers record the freeze. They do **not** authorize code, schema, or tests.

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Contractors cannot keep current operating work honest. All organization Projects currently feed operating lists, including PERF-C. CORE CLOSE distinguishes current work from historical work without deleting history. Punch List + Completion Sign-Off give a truthful closeout document path before Close. |
| 2 | Who is the user? | Instance Owner / future Sys Admin Close and Reopen. Contractor office Punch List and Completion Sign-Off preparation. Customer signs Completion Sign-Off. Ordinary operational users continue current work on ACTIVE Projects only. |
| 3 | Which module owns it? | **Projects** owns operating lifecycle, Punch List direction, and Completion Sign-Off as a Project document. Native Signing overlay is reused, not reopened. BUILD / Time / Field / Schedule / PERF-C consume shared current-operating authority. |
| 4 | What data does it own? | **None in this freeze.** Future: additive Project operating-lifecycle field; Punch List records; Completion Sign-Off artifact identity. Exact schema is not frozen. |
| 5 | What data does it reference? | Project identity; Project Work / Original Scope; Change Orders; Time; Schedule; MONITOR; PERF; Field originals; existing documents; Native Signing executed artifacts; People & Access Instance Owner / Sys Admin. |
| 6 | What may it change? | **Nothing in this freeze.** Later implementation may persist operating state; introduce shared current-operating queries; guard new operational writes after Close; add Punch List and Completion Sign-Off. |
| 7 | What must it not change? | Sealed PERF-A/B/C fact types. `Project.status` CRM meaning. Estimate / Proposal / contract / CO / Time / Schedule history rewrite. LEARN. Financial / QB-T. People & Access product. Native Signing reopen. Media Closed Project Archive. Hard Project delete. UAT inference from names. |
| 8 | What are the acceptance criteria? | Deferred to a later implementation prompt. Directionally: ACTIVE/CLOSED persistence; shared current-operating query; historical Hub remains; no new work after Close; in-flight admin completion remains; Reopen restores eligibility without rewriting history; Punch List hard-gates Completion Sign-Off; unsigned Completion Sign-Off warns on Close; existing Projects migrate ACTIVE. |
| 9 | What tests are required? | None in this freeze. Later implementation tests are separately governed. |
| 10 | What documentation must be updated? | This freeze plus FG-035 subsequent status, indexes, current-state, session-handoff, chat-workflow-log, roadmap, modules/projects, architecture.md, project-state-report, milestones, Manual Impact, v1-completion-register subsequent status. |
| 11 | Does it require an ADR? | **No new ADR in this freeze.** ADR-053 Closeout remains LEARN. CORE CLOSE is subsequent owner decision. |
| 12 | Does it require a database migration? | **Not in this freeze.** Future implementation will require explicit Rule 7 approval for an additive operating-lifecycle field. |

---

## 28. STOP

```text
DOCS-ONLY OWNER DECISION FREEZE.
NOT IMPLEMENTED.
DO NOT IMPLEMENT CORE CLOSE FROM THIS FILE.
DO NOT IMPLEMENT PUNCH LIST.
DO NOT IMPLEMENT COMPLETION SIGN-OFF.
DO NOT IMPLEMENT NATIVE SIGNING CHANGES.
DO NOT IMPLEMENT PEOPLE & ACCESS.
DO NOT IMPLEMENT HOME OFFICE.
DO NOT IMPLEMENT LEARN.
DO NOT IMPLEMENT QB-T.
DO NOT CREATE A MIGRATION.
DO NOT CLOSE ANY LIVE PROJECT.
DO NOT CLASSIFY UAT PROJECTS FROM NAMES.
DO NOT ADD ARCHIVED AS A THIRD OPERATING STATE.
DO NOT REUSE Project.status.
DO NOT REOPEN PERF.
DO NOT RESCORE V1.
RETURN TO CHATGPT ARCHITECT.
```
