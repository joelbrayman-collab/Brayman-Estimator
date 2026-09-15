# Interactive Help, Voice, and Professional User Manual — future record

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / RECORDED / MANDATORY PRE-UAT V1 / NOT IMPLEMENTATION-AUTHORIZED / NOT A PREFLIGHT / NOT A FEATURE GATE / NOT AN ADR.** |
| Updated | 2026-09-15 |
| Authority | Joel Brayman / ChatGPT Architect. Product decision: Interactive in-product Help, Voice assistance, and a professional CalibraytAI User Guide are **mandatory** before opening CalibraytAI to Ben, Ben’s father-in-law, and Kevin for real-world / independent UAT. |
| Does not interrupt | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**; [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**; [project-element-authority-future-record.md](project-element-authority-future-record.md). TAX/WBS remains **IMPLEMENTED**. Later FG-035 slices remain **NOT AUTHORIZED** from this record. |

This file is the **single consolidated future record** for Help / Voice / User Manual. It is **not** an ADR, not a Feature Gate, and not a preflight. Nothing in this file is implemented. Do **not** invent FG-036 or ADR-054 from this recording.

**Actual governed baseline at this recording:** starting HEAD / `origin/main` **`3d3a225edeac276e681ee18dd43ab18fff81d466`** (`docs: pin FG-035 TAX/WBS SHA`). Product TAX/WBS **`c8c01269ecbb30f6920c44af9c503eb73eec6e92`**. [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. TAX/WBS **IMPLEMENTED**. SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md) **CLOSED / OPERATIONAL FOR UAT**. Live Postmark **DEFERRED**. V1 **not rescored** (**60% / 4 of 11**). Alembic **`f3b4c5d6e7f8 (head)`**. EST-2026-0019 **untouched**. PRODUCTION packages **0**.

```text
MANDATORY PRE-UAT V1:
INTERACTIVE IN-PRODUCT HELP
VOICE HELP / ASSISTANCE
PROFESSIONAL END-TO-END USER MANUAL

ONE GOVERNED USER HELP CONTENT AUTHORITY.

NOT FEATURE-COMPLETE ALONE.
UNDERSTANDABLE. SELF-EXPLAINING. CONTRACTOR-FACING.
SUPPORTED. DOCUMENTED.
USABLE WITHOUT JOEL / DEVELOPMENT TEAM COACHING THE USER.

NOT AUTHORIZED. NOT IMPLEMENTED.
DO NOT IMPLEMENT FROM THIS RECORD.
DO NOT BEGIN FG-035 LATER SLICES FROM THIS RECORD.
DO NOT RESCORE V1 FROM THIS RECORD.
```

The originating Cursor prompt recorded **§§0–25 complete**. **§26** arrived truncated after “Avoid giving a long developer-led demonstration that teaches them”. Remainder of §26 is **not invented**. An open question about a short task-based pre-UAT test script was received and is **not decided**.

---

## Completeness principle

Joel’s objective is not merely **FEATURE COMPLETE**.

V1 must be:

- **UNDERSTANDABLE**
- **SELF-EXPLAINING**
- **CONTRACTOR-FACING**
- **SUPPORTED**
- **DOCUMENTED**
- **USABLE WITHOUT JOEL / DEVELOPMENT TEAM COACHING THE USER**

Core acceptance principle:

A competent contractor should be able to learn and operate CalibraytAI without needing a developer beside them.

These requirements do **not** change current FG-035 implementation scope.

---

## Interactive in-product Help (V1 requirement)

CalibraytAI must provide interactive in-product Help on normal contractor-facing surfaces.

The user should be able to ask questions such as:

- What can I do on this page?
- How do I create an estimate?
- How do I record Extra Work?
- How do I approve time?
- How do I move a project on the Schedule?
- Why is this project showing Needs Attention?
- How do I send this for signature?
- How do I reset my password?

### Context-aware Help

Help should understand the user’s current product context. Recorded examples:

Project Hub · Estimate · Schedule · Time Entry · Time Approval · Change Order · MONITOR · Closeout · LEARN · Native Signing · Account Recovery

If the user asks “What do I do here?”, Help should explain **that** workflow.

Do **not** expose technical route/model terminology to the user.

### Grounded Help

Interactive Help must be grounded in authoritative CalibraytAI product documentation.

It must **not** invent product behavior.

If authoritative help content does not support an answer: say so, or direct the user to the documented workflow.

Do not hallucinate buttons, states, workflows, or capabilities.

### Help UX (exact UX deferred)

Future design should evaluate one simple **Help** entry point available throughout the platform.

Do not create intrusive help overlays.

Potential experience: Help → How can I help? with contextual suggestions such as:

- What can I do on this page?
- Show me how to...
- Why am I seeing this?
- What should I do next?

Exact UX is deferred.

### Desktop + iPhone

Interactive Help must work on **DESKTOP** and **IPHONE / MOBILE**.

**ONE help system.**

Desktop may use a side panel / help drawer where appropriate. Mobile should use a simple full-width / bottom-sheet / conversational presentation according to later UX design.

Do not create separate knowledge systems.

---

## Voice (V1 requirement)

CalibraytAI must include practical Voice assistance in V1. Voice is particularly relevant to field/mobile contractor use.

Initial V1 voice objective:

**ASK → UNDERSTAND → ANSWER / EXPLAIN → SURFACE / NAVIGATE**

Examples:

- How do I enter Extra Work?
- What’s happening next week?
- How do I approve these hours?
- Where do I create a Change Order?

Voice Help must use the **same** governed User Help Content authority as written Help, the User Manual, and contextual Help.

Do **not** create a separate voice knowledge base.

### Bounded read-only product questions

Future architecture should evaluate whether Voice may answer bounded **read-only** product questions such as:

- What’s happening today?
- What’s happening next week?
- Which projects need attention?
- How many hours are left on this Element?

Such answers must use governed product services/data.

Do not let Voice invent operational state.

### Voice mutation boundary

V1 must **not** casually introduce an unrestricted voice command system that can mutate Project data.

Examples requiring special governance:

- Record three hours against Speakeasy.
- Move Smith Garage to Thursday.
- Create a Change Order.
- Approve these hours.

Voice mutation creates ambiguity, confirmation, audit, authorization, and wrong-project risk.

Therefore initial V1 Voice should prioritize:

- **HELP**
- **READ-ONLY INFORMATION**
- **NAVIGATION / SURFACING**

If any voice mutation is later included in V1, it must:

- require explicit confirmation
- use normal governed product services
- preserve audit/actor
- respect tenant/authorization boundaries
- fail closed on ambiguity

Do not create a second mutation path.

### Voice desktop + mobile

Voice capability should be available where practical on desktop and iPhone / mobile. Mobile is likely the higher-value environment.

Exact browser/device/runtime support must be determined during the later Voice preflight.

Do not assume browser speech APIs are sufficient without testing.

---

## Professional User Manual (required V1 deliverable)

Before external / real-world UAT, produce a professional **CALIBRAYTAI USER GUIDE** for contractors.

This is **not** an engineering manual.

Audience:

- contractor
- project manager
- field worker
- office user
- non-technical construction professional

### Design

The User Guide must be:

- professional
- visually clean
- lots of white space
- highly readable
- contractor-facing
- screenshot-rich
- step-by-step
- end-to-end

Avoid dense walls of text.

Use: clear headings; short paragraphs; numbered procedures where useful; screenshots; callouts; tips; warnings only where necessary; ample white space.

### Product structure (evaluate; final follows completed V1)

The final manual should follow the way a contractor uses CalibraytAI. Evaluate a structure such as:

- **GETTING STARTED** — Sign In; Forgot Password; Home; Navigation
- **PLAN** — Create / open Project; Project Hub; documents / project information
- **PRICE** — Estimate; labour; materials; review; Construction Estimate
- **CONTRACT** — Contract; Change Orders; Native Signing
- **SCHEDULE** — Company Month; Project Schedule; move/resize work; crew assignments; conflicts; iPhone Today / Week / Month
- **BUILD** — Field workflow; observations; photos / evidence; Extra Work
- **TIME** — Record Time; Project → Work → Hours; Extra Work; Submit; Approve
- **MONITOR** — labour status; schedule status; Needs Attention; forecast
- **CLOSEOUT** — complete Project; review exceptions; resolve Extra Work; performance review
- **LEARN** — recommendations; comparable work; accept / reject calibration
- **EVERYDAY TASKS / REFERENCE** — Reset password; Find a Project; Record Extra Work; Approve Time; Move scheduled work; Create Change Order; Send for Signature; View completed document; Resolve Needs Attention

Final structure must follow the **actual completed V1 product**.

### Field discipline in the manual

The manual must explicitly teach important operational disciplines.

**EXTRA WORK example:** if a customer asks you to ADD, REMOVE, MOVE, or CHANGE something that was not part of the work you were sent to perform: **USE EXTRA WORK**. Do not bury those hours in the original Project work.

Explain WHY in simple contractor language: so the Project stays accurate; so Change Orders are not lost; so future estimates improve.

Do not expose LEARN architecture jargon.

### Screenshots

Screenshots should come from the final/current product.

Do not create screenshots before the relevant UI is stable.

Use representative synthetic/demo data.

Do not expose: real customer confidential data; secrets; tokens; internal technical identifiers.

Screenshots should cover **DESKTOP** and, where useful, **IPHONE / MOBILE**.

### Outputs

Final V1 deliverables should include at minimum:

- professional PDF
- an editable source format according to repository/documentation workflow

The manual should be versioned with **CalibraytAI V1** and a revision/date.

Exact artifact custody/versioning will be decided during the documentation workstream.

---

## One User Help Content authority

Do **not** create:

- one manual
- plus a separate chatbot knowledge base
- plus separate voice scripts

Future architecture must establish **ONE** governed **USER HELP CONTENT AUTHORITY** that can feed:

- professional User Manual
- in-product Help
- contextual Help
- Voice Help

This prevents documentation/help drift.

The Help authority must describe the **actual finished product**.

Therefore final Help content is created/refined **AFTER**:

1. remaining functional V1 work
2. the already-recorded **Contractor Language + UX E2E Audit**

Help content must use the same contractor-facing vocabulary as the product.

The manual and Interactive Help must be generated/maintained from the same governed content authority where practical.

Do not copy/paste independent prose into multiple systems without a mechanism to keep them synchronized.

A product change should have one authoritative Help update.

The already-recorded platform-wide Contractor Language + UX E2E Audit remains mandatory. Final User Manual content should be produced **AFTER** that audit so it documents the final contractor-facing terminology.

Do not document technical jargon and then teach users to work around it.

Do **not** start another FG-025 slice from this record.

---

## Pre-UAT review group

Joel plans to provide the completed User Guide and platform to:

- **BEN**
- **BEN’S FATHER-IN-LAW**
- **KEVIN**

These users provide different and useful perspectives.

### Ben — operational UAT

Ben’s role: **REAL CONTRACTOR / OPERATIONAL USER**.

Primary question: can Ben actually run Project work through CalibraytAI?

His UAT should exercise real contractor workflows across desktop and iPhone.

### Ben’s father-in-law — construction domain review

Ben’s father-in-law has approximately 40 years of construction experience.

His role should emphasize:

- construction-domain logic
- workflow naturalness
- terminology
- missing practical steps
- whether the platform reflects how contractors actually work

He should review the User Guide **BEFORE** platform introduction / UAT.

### Kevin — non-technical usability UAT

Kevin is not an IT/technical user. That is valuable.

His role should emphasize:

- discoverability
- clarity
- navigation
- Help usefulness
- manual usefulness
- whether normal workflows can be completed without technical understanding

Do not coach him through every action.

The objective is to test whether CalibraytAI explains itself.

### Manual-first UAT (§26 received / truncated)

Before introducing the platform in detail: provide the completed User Guide. Allow reviewers to read it. Then provide bounded UAT tasks.

Avoid giving a long developer-led demonstration that teaches them

**Truncation:** the originating prompt ended here. Remainder of §26 is **not invented**.

### Open question (received / not decided)

Would the pre-UAT package include a short task-based test script for Ben, his father-in-law, and Kevin, with the same core workflows but different evaluation focus for each person?

This question is **recorded as received**. It is **not** a Joel decision in this file. Do **not** invent the script from this record.

---

## Sequencing (recorded; not authorization)

Help / Voice / Manual **do not interrupt** the already-approved FG-035 architecture.

Recorded order of later work (not a Cursor implementation prompt):

1. Remaining functional V1 work, including authorized FG-035 slices when separately assigned.
2. Platform-wide Contractor Language + UX E2E Audit.
3. Final User Help Content authority + User Guide + in-product Help + Voice, from that one authority.
4. Manual-first review (father-in-law reads the Guide first).
5. Bounded independent UAT (Ben / Kevin), without developer coaching.

Do **not** implement Help, Voice, or the Manual from this record.

Do **not** create screenshots against unstable UI.

Do **not** treat this record as BRAYMAN REAL-LIFE UAT READY.

---

## Explicitly not authorized from this record

- Interactive Help product
- Voice runtime / speech APIs
- User Manual PDF / screenshot capture
- A chatbot knowledge base
- A second mutation path
- FG-036 / ADR-054 invention
- FG-035 SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T
- Another FG-025 slice
- FG-024 Slice D
- Live Postmark
- V1 rescore
- EST-2026-0019 mutation
