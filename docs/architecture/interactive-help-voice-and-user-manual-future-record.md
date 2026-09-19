# Interactive Help, Voice, and Professional User Manual — future record

| Attribute | Value |
|-----------|--------|
| Status | **OPEN / PARTIAL FOR HELP PRODUCT.** D1 Project Hub contextual Help **IMPLEMENTED**. D3 office Help **IMPLEMENTED**. Voice, User Guide, Field Help remain **NOT IMPLEMENTED**. User Guide / Help Content **FRAMEWORK START NOW** ([calibraytai-v1-user-guide-framework.md](calibraytai-v1-user-guide-framework.md)). **Manual Audience Law** is controlling. Not a Feature Gate. Not an ADR. Task-based pre-UAT script **REQUIRED**. Voice mutation **NOT REQUIRED** for V1 Voice completion. Subsequent **2026-09-16:** **Manual Impact** capture required at each material feature/slice close ([manual-impact-log.md](manual-impact-log.md)). Completed User Guide is given to Kevin and Ben **BEFORE** platform access. Do **not** implement Print, Voice, Field Help, or the finished Manual from this record. |
| Updated | 2026-09-19 |
| Authority | Joel Brayman / ChatGPT Architect. Product decision: Interactive in-product Help, Voice assistance, and a professional CalibraytAI User Guide are **mandatory** before opening CalibraytAI to Ben, Ben’s father-in-law, and Kevin for real-world / independent UAT. |
| Does not interrupt | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**; [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**; [project-element-authority-future-record.md](project-element-authority-future-record.md). TAX/WBS remains **IMPLEMENTED**. Later FG-035 slices remain **NOT AUTHORIZED** from this record. |

This file is the **single consolidated future record** for Help / Voice / User Manual. It is **not** an ADR, not a Feature Gate, and not a preflight. Do **not** invent FG-036 or ADR-054 from this recording.

**Subsequent status (2026-09-19 D3 OFFICE HELP):** D3 **IMPLEMENTED / TESTED / NOT COMMITTED**. Same Help authority as D1. Native `<details>` Help on high-value office screens. `help_payload()` is the later Voice seam. Field Help empty. LEARN Future. No schema. No Voice. Help product overall **PARTIAL**. Official V1 **not rescored**.

**Subsequent status (2026-09-19 D2 BOUNDED CONTRACTOR-LANGUAGE RESIDUALS):** D2 **IMPLEMENTED**. Presentation/language/navigation only. D1 Hub Help preserved. LEARN Future. No schema. No Voice. Help product overall **PARTIAL**. Official V1 **not rescored**.

**Subsequent status (2026-09-19 D1 PROJECT HUB CONTEXTUAL HELP):** D1 **IMPLEMENTED**. Static Help content authority `app/presentation/help_content.py`. Native `<details>` Help on Project Hub PLAN / PRICE / CONTRACT / BUILD / MONITOR. LEARN Help is Future-only. Informational GET-only. No schema. No Voice. No office/Field Help. Help product overall remains **PARTIAL**. Official V1 **not rescored**.

**Actual governed baseline at this recording:** starting HEAD / `origin/main` **`3d3a225edeac276e681ee18dd43ab18fff81d466`** (`docs: pin FG-035 TAX/WBS SHA`). Product TAX/WBS **`c8c01269ecbb30f6920c44af9c503eb73eec6e92`**. [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. TAX/WBS **IMPLEMENTED**. SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md) **CLOSED / OPERATIONAL FOR UAT**. Live Postmark **DEFERRED**. V1 **not rescored** (**60% / 4 of 11**). Alembic **`f3b4c5d6e7f8 (head)`**. EST-2026-0019 **untouched**. PRODUCTION packages **0**.

```text
MANDATORY PRE-UAT V1:
INTERACTIVE IN-PRODUCT HELP
VOICE HELP / ASSISTANCE
PROFESSIONAL END-TO-END USER MANUAL

ONE GOVERNED USER HELP CONTENT AUTHORITY.

CALIBRAYTAI V1 SHOULD NOT REQUIRE JOEL OR A DEVELOPER
TO EXPLAIN HOW TO USE THE PLATFORM.

NOT FEATURE-COMPLETE ALONE.
UNDERSTANDABLE. SELF-EXPLAINING. CONTRACTOR-FACING.
SUPPORTED. DOCUMENTED.
USABLE WITHOUT JOEL / DEVELOPMENT TEAM COACHING THE USER.

COMPLETE FOR PRODUCT-DIRECTION RECORDING.
NOT AUTHORIZED. NOT IMPLEMENTED.
DO NOT IMPLEMENT FROM THIS RECORD.
DO NOT BEGIN FG-035 LATER SLICES FROM THIS RECORD.
DO NOT RESCORE V1 FROM THIS RECORD.
```

The originating Cursor prompt recorded **§§0–25 complete**. Subsequent **2026-09-15** continuation recorded **§§26–39**. This continuation recorded **§§40–60** and **closes** the product-direction record. **§26 task-based pre-UAT script = REQUIRED.** Nothing in this file is implemented.

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
- How do I see my Banked Hours?
- How are Banked Hours earned?
- How do I use Banked Hours?
- Why did my Banked Hours balance change?
- How do I enter Shop time?
- What if the work was for a customer job, not general Shop work?
- What if Ben sends me to another job?
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

---

## 26. Task-based pre-UAT script — DECIDED

**JOEL / CHATGPT ARCHITECT DECISION: YES.**

A task-based pre-UAT script is **REQUIRED**.

The objective is to give reviewers realistic contractor tasks and determine whether:

**PRODUCT + USER GUIDE + INTERACTIVE HELP + VOICE**

are sufficient for them to complete the work.

Do **not** give step-by-step answers inside the test task.

The final script must reflect the **ACTUAL completed V1**.

Do **not** invent the script from this record. Write it only after the product and Help authority exist.

## 27. Common core tasks

Final UAT should evaluate realistic tasks such as:

- Sign in
- Recover a forgotten password
- Find a Project
- Understand Project Hub
- Review Project work
- Review an Estimate
- Find Company Schedule
- Determine what is happening this week
- Determine what is coming over the next month
- Record normal Time
- Record Extra Work
- Submit Time
- Approve Time where role permits
- Identify labour approaching/exceeding allowance
- Find Needs Attention
- Review/Create Change Order where role permits
- Send document for signature
- Find signing status
- Retrieve completed documentation
- Review Project Closeout
- Resolve/explain material variance
- Review LEARN recommendation
- Use Interactive Help
- Ask a Voice Help question
- Ask a supported read-only Voice product question

Final task list must match actual V1.

## 28. No-coaching principle

For selected tasks give **THE TASK**, not **THE NAVIGATION PATH**.

Good: Find out what work is scheduled for next week.

Bad: Click Schedule → Month → Next Week.

We are testing: discoverability, terminology, navigation, Manual usefulness, Help usefulness, Voice usefulness.

Do not mask UX problems with coaching.

## 29. Manual-first UAT

Before detailed product demonstration: provide the completed **CALIBRAYTAI V1 USER GUIDE**.

Allow the reviewer to read it.

Then provide task-based UAT.

A brief access/login orientation is permitted.

Do not provide a long developer-led walkthrough that teaches every workflow before UAT.

## 30. Ben — operational UAT

Ben is the primary operational contractor user.

Primary question: **CAN BEN ACTUALLY RUN PROJECT WORK THROUGH CALIBRAYTAI?**

Focus on: Project Hub; Estimate; Schedule; Time; Extra Work; Time Approval; Change Orders; Native Signing; MONITOR; Needs Attention; Closeout; LEARN; desktop/iPhone relationship; Help; Voice.

## 31. Ben’s father-in-law — construction domain review

Ben’s father-in-law brings approximately 40 years of construction experience.

Focus on: construction workflow validity; terminology; missing practical steps; Schedule usefulness; Time / Extra Work; Change Orders; MONITOR usefulness; User Guide clarity; whether the product reflects how contractors actually work.

He should read the User Guide before product UAT.

## 32. Kevin — non-technical usability review

Kevin is intentionally useful because he is not an IT/technical user.

Focus on: discoverability; clarity; navigation; Help usefulness; Manual usefulness; Voice usefulness; ability to recover from mistakes; ability to complete normal tasks without technical knowledge.

Do not coach Kevin through every action.

Where he becomes stuck is useful product evidence.

## 33. UAT observation

Where practical observe:

- where the reviewer first looks
- where the reviewer hesitates
- what they misunderstand
- what terminology confuses them
- what action they expected
- whether they use Help
- whether Help solves the issue
- whether they use Manual
- whether Manual solves the issue
- whether they use Voice
- whether Voice solves the issue

Look for repeated/material friction.

## 34. Simple UAT evidence

Capture at minimum:

Reviewer · Role/focus · Device · Task · PASS / FAIL / PARTIAL · Observed difficulty · Confusion point · Manual used? · Help used? · Voice used? · Defect/observation · Severity · Follow-up.

Do not make reviewers write engineering bug reports.

## 35. Device coverage

Independent UAT must cover **DESKTOP** and **IPHONE / MOBILE** where the product is intended for both.

Previously deferred physical-iPhone checks should be resolved here.

Do **not** claim physical-device PASS from automated responsive tests.

## 36. Interactive Help UAT

Test Help with questions such as:

- What can I do here?
- How do I record Extra Work?
- How do I approve Time?
- How do I move a Project?
- Why is this Project showing Needs Attention?
- How do I send this for signature?
- What should I do next?

Help must describe actual V1.

Hallucinated product instructions are a **V1 defect**.

## 37. Context-aware Help UAT

Test “What do I do here?” from different surfaces such as:

Project Hub · Schedule · Time Entry · MONITOR · Closeout.

The answer must reflect current context.

Do not expose technical route/model names.

## 38. Voice UAT

Test Voice on actual supported hardware/browser combinations.

At minimum:

- Voice Help question
- Voice navigation/surfacing
- supported read-only operational question

Examples:

- How do I enter Extra Work?
- What’s happening next week?
- Show me the Schedule.

Physical Voice PASS requires physical supported-device evidence.

## 39. Voice mutation boundary

Initial V1 Voice remains:

**HELP · READ-ONLY INFORMATION · NAVIGATION / SURFACING.**

Voice mutation is **NOT required** for V1 Voice completion.

If later proposed, mutation requires separate governed acceptance criteria, explicit confirmation, normal service boundaries, and fail-closed ambiguity.

---

## 40. User Help Content authority — quality

The future governed User Help Content authority must support sufficient structure for:

- topic identity
- contractor-facing title
- summary
- step-by-step procedure where useful
- applicable product context / surface
- related topics
- manual placement
- Interactive Help retrieval
- Voice retrieval
- version / current state
- retirement / supersession

Exact storage format is deferred to the later Help architecture/preflight.

Do **not** assume this requires a database.

A governed documentation/content structure may be preferable.

## 41. Help content versioning

Help content must match the actual V1 product version.

When a product workflow, action, or contractor-facing label changes materially: the related Help content must be reviewed.

Do not allow obsolete instructions to remain active merely because they still retrieve successfully.

## 42. Help source priority

For questions about operating CalibraytAI:

**CURRENT GOVERNED CALIBRAYTAI HELP CONTENT WINS.**

Interactive Help and Voice must use governed product authority before generic model knowledge.

General model knowledge must not override actual CalibraytAI behavior.

## 43. Help uncertainty

If Interactive Help cannot confidently ground an answer in current product authority:

**DO NOT FABRICATE.**

Use contractor-friendly behavior meaning: I don’t have a reliable answer for that yet.

Then, where possible: surface the closest relevant Help topic, or provide the future governed support path.

Exact final wording belongs to the Contractor Language + UX E2E Audit.

## 44. Professional User Manual standard

The final CalibraytAI V1 User Guide is a real product deliverable.

It must look appropriate to send directly to a contractor, a Project Manager, a field worker, or a construction business owner.

It must **not** look like developer documentation, repository notes, raw AI output, or an internal technical specification.

## 45. User Manual visual design

The User Guide must use: generous white space; clear visual hierarchy; large readable headings; short sections; consistent screenshot sizing; clean captions; simple callouts; logical page breaks; professional cover; table of contents; page numbers; revision / version identification.

Avoid: dense walls of text; tiny screenshots; excessive borders; technical metadata; unnecessary dense tables.

## 46. Screenshot standard

Screenshots must be: **CURRENT**; **LEGIBLE**; **INTENTIONALLY CROPPED**; **LARGE ENOUGH TO UNDERSTAND**; **FREE OF SENSITIVE REAL CUSTOMER DATA**.

Where a workflow is primarily mobile: show iPhone/mobile.

Where primarily desktop: show desktop.

Where desktop/mobile differ materially: explain the distinction simply.

Use representative synthetic/demo data.

Never expose: passwords; reset links; signing secrets; API keys; confidential customer information; unnecessary internal technical identifiers.

## 47. Procedure standard

A normal User Guide procedure should answer:

- **WHAT DOES THIS DO?**
- **WHEN WOULD I USE IT?**
- **HOW DO I DO IT?**
- **WHAT HAPPENS NEXT?**

Do not explain architecture unless the contractor genuinely needs to know it.

Keep procedures practical.

## 48. Practical tips

Use short contractor tips where they improve behavior.

**EXTRA WORK:** if a customer asks you to add, move, remove, or change something outside the work you were sent to do: record it as Extra Work.

Explain simply: this keeps the Project accurate, helps make sure changed work is not lost, and gives CalibraytAI better information for future estimates.

Do not overwhelm the manual with callout boxes.

## 49. Manual / product cross-check

Before User Guide release: walk **EVERY** major documented procedure against the actual final V1 build.

Verify: button names; navigation; status names; screens; workflow sequence; result.

If the Guide says “click X”, then X must exist and use that contractor-facing name.

Do not publish aspirational documentation.

Manual/product mismatch is a **PRE-UAT blocker**.

## 50. Help / product cross-check

Likewise, test governed Interactive Help topics against the actual V1.

Do not rely only on prose review.

Help must describe **CURRENT PRODUCT**, **CURRENT TERMINOLOGY**, and **CURRENT WORKFLOW**.

It must not present future features, deferred features, or obsolete labels as available functionality.

## 51. Voice / product cross-check

Voice Help/read-only answers must use the same current product authority.

If Voice contradicts the User Guide, Interactive Help, or the actual product: that discrepancy is a defect.

Voice must not bypass: authorization; approval; tenant boundaries; fail-closed behavior.

## 52. Pre-UAT release gate

CalibraytAI must **NOT** be opened to Ben, Ben’s father-in-law, or Kevin for independent UAT until:

1. remaining V1 functional work is complete
2. runtime hardening required for UAT is complete
3. Platform-Wide Contractor Language + UX E2E Audit is complete
4. final User Help Content authority is complete
5. professional CalibraytAI V1 User Guide is complete
6. Interactive Help is implemented / validated
7. Voice Help / read-only assistance is implemented / validated
8. internal E2E regression is **PASS**

This is a mandatory **PRE-UAT RELEASE GATE**.

## 53. Updated final V1 sequence

The governing later sequence (not a Cursor implementation prompt) is:

1. Complete FG-035 (TAX/WBS, SCOPE, TIME, SCH, PERF, CLOSE, LEARN, QB-T)
2. Complete any remaining BUILD / Closeout integration required by the loop
3. Complete remaining V1 functionality / runtime hardening
4. Platform-wide Contractor Language + UX E2E Audit
5. Establish final User Help Content authority
6. Create professional CalibraytAI V1 User Guide
7. Implement / validate Interactive Help
8. Implement / validate Voice Help + read-only assistance
9. Internal final E2E regression
10. Prepare Manual-first task-based UAT package
11. Provide User Guide to Ben, Ben’s father-in-law, and Kevin
12. Independent / real-world UAT (desktop; iPhone/mobile; Help; Voice; construction-domain review; non-technical usability)
13. Correct defects / language / workflow issues
14. Retest affected workflows
15. Complete final E2E regression
16. Complete final V1 governance / completion audit
17. Rescore V1
18. Complete final production readiness review
19. V1 close

This sequence **does not** authorize any of those steps from this record.

TAX/WBS is already **IMPLEMENTED**. Later FG-035 slices remain **NOT AUTHORIZED** from this record.

## 54. V1 completeness definition

Do not declare V1 complete merely because application code exists.

V1 must be: functionally complete; documented; self-supporting; contractor-facing; desktop-ready; iPhone / mobile-ready; internally validated; independently UAT-tested; operationally ready.

## 55. Product law

```text
CALIBRAYTAI V1 SHOULD NOT REQUIRE JOEL OR A DEVELOPER
TO EXPLAIN HOW TO USE THE PLATFORM.

THE PRODUCT, USER GUIDE, INTERACTIVE HELP AND VOICE
ASSISTANCE SHOULD WORK TOGETHER SO A COMPETENT
CONTRACTOR CAN LEARN AND OPERATE IT.

INDEPENDENT UAT EXISTS TO PROVE THAT CLAIM.
```

## 56. Record status

This file is:

**FUTURE / RECORDED / COMPLETE FOR PRODUCT-DIRECTION RECORDING / MANDATORY PRE-UAT V1 / NOT IMPLEMENTATION-AUTHORIZED.**

It is product direction.

It is **not**: a Feature Gate; an ADR; implementation authorization; schema authorization; migration authorization; proof Help exists; proof Voice exists; proof Manual exists; a V1 rescore.

## 57. FG-035 status (preserved)

[FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) remains **OPEN / PARTIAL**.

TAX/WBS remains **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**.

SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T remain **NOT AUTHORIZED**.

Do **not** implement any FG-035 slice from this record.

## 58–60. Recording close

This product-direction recording is **closed**. Do not invent §§61+.

FG-035 SCOPE is the next product slice in the recorded sequence. It is **NOT AUTHORIZED** by this docs prompt.

Return to ChatGPT Architect.

---

## Sequencing (historical five-step list; superseded by §53)

The five-step list recorded with §§26–39 is **superseded** by **§53**. It is retained only as earlier recording, not as competing sequence.

Help / Voice / Manual **do not interrupt** the already-approved FG-035 architecture.

Do **not** implement Help, Voice, or the Manual from this record.

Do **not** create screenshots against unstable UI.

Do **not** treat this record as BRAYMAN REAL-LIFE UAT READY.

---

## Subsequent 2026-09-16 — User Guide / Help Content framework START NOW (not finished Manual)

Framework recorded in [calibraytai-v1-user-guide-framework.md](calibraytai-v1-user-guide-framework.md).

**Manual Audience Law** is **CONTROLLING** and sits at the start of that framework. The contractor User Guide is for people who build, sell, supply, estimate, and manage construction work. It is not written for software developers. Internal architecture stays out of the Manual unless a user needs that fact to do the job.

```text
MANUAL FRAMEWORK: START NOW
FINAL AUTHORING: AFTER FUNCTIONAL V1 + CONTRACTOR LANGUAGE / UX AUDIT
BEN / KEVIN ACCESS: AFTER COMPLETED USER GUIDE / PRE-UAT GATE
V1: 60% / 4 OF 11 / NO RESCORE
```

Do **not** write finished Manual chapters from this addendum. Do **not** capture screenshots now. Do **not** implement Help / Voice. Do **not** rescore V1.

---

## Subsequent 2026-09-16 — Manual Impact capture + Guide-before-access (not implemented)

Joel / ChatGPT Architect product decision (16 Sep 2026): the professional CALIBRAYTAI USER GUIDE will be provided to **Kevin** and **Ben** **BEFORE** they receive independent platform access. Ben’s father-in-law remains in the already-recorded review group and still reviews the Guide **before** platform introduction.

This does **not** conflict with existing §29 Manual-first UAT, §52 PRE-UAT RELEASE GATE, or §53. It **refines** §53 steps 11–12:

1. Give the completed User Guide to Kevin, Ben, and Ben’s father-in-law.
2. Allow them to review / use the Guide.
3. Then provide platform access and realistic task-based UAT.
4. Do not coach them through every workflow.
5. Record where the product, Manual, Help, or Voice fails to explain itself.

**MANUAL IMPACT:** beginning with current development, each material feature/slice close appends a lightweight impact entry to [manual-impact-log.md](manual-impact-log.md). First entry: **MANUAL IMPACT — SCH-C**. Do not write final Manual prose during feature implementation. Do not capture unstable screenshots.

Manual status: **MANDATORY PRE-UAT V1 / FRAMEWORK / IMPACT CAPTURE NOW / FINAL AUTHORING AFTER FUNCTIONAL V1 + CONTRACTOR LANGUAGE/UX AUDIT.**

Kevin / Ben platform access: **NOT YET**.

This addendum does **not** interrupt FG-035 SCH-C. Do **not** implement Help, Voice, or the Manual from this addendum. V1 **not rescored**.

---

## Subsequent 2026-09-16 — Print in Help / User Guide (not implemented)

The platform-wide desktop **Print / paper workflow** is recorded in [project-element-authority-future-record.md](project-element-authority-future-record.md). Future User Guide and Interactive Help should explain Print where useful. Recorded examples:

- How do I print this month’s Schedule?
- How do I print today’s work?
- How do I print a Project Schedule?

Do **not** implement Help, Voice, the Manual, or Print from this addendum. This addendum does **not** authorize SCH-C or SCH-D. V1 **not rescored**.

---

## Explicitly not authorized from this record

- Interactive Help product
- Voice runtime / speech APIs
- User Manual PDF / screenshot capture
- A chatbot knowledge base
- Voice mutation as a V1 Voice completion requirement (explicitly **not required**)
- FG-036 / ADR-054 invention
- The actual UAT script (write only after completed V1 + Help authority)
- FG-035 SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T
- Desktop Print / print CSS
- Another FG-025 slice
- FG-024 Slice D
- Live Postmark
- V1 rescore
- EST-2026-0019 mutation
- Opening CalibraytAI to Ben / father-in-law / Kevin before the §52 PRE-UAT RELEASE GATE, including any access before they have the completed User Guide
