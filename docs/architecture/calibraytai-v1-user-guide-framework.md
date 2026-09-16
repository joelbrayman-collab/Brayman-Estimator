# CalibraytAI V1 User Guide / Help Content — framework

| Attribute | Value |
|-----------|--------|
| Status | **MANUAL FRAMEWORK: START NOW.** Final authoring **AFTER** remaining functional V1 **and** the Contractor Language + UX E2E Audit. Not the finished User Guide. Not Interactive Help. Not Voice. **NOT IMPLEMENTATION-AUTHORIZED** for Help / Voice / Manual product. |
| Updated | 2026-09-16 |
| Authority | Joel Brayman / ChatGPT Architect |
| Governing product-direction | [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md) |
| Impact capture | [manual-impact-log.md](manual-impact-log.md) |
| V1 | **60% / 4 of 11. NO RESCORE.** |
| Ben / Kevin access | **AFTER** the completed User Guide **and** the PRE-UAT gate. **NOT YET.** |

**This file is internal scaffolding.** It is **not** the contractor User Guide. Do not ship this file to Kevin or Ben. The **Manual Audience Law** below controls every future contractor-facing page, Help topic, and Voice answer.

Do **not** capture screenshots against unfinished surfaces.
Do **not** write finished Manual chapters in this file.
Do **not** implement in-product Help or Voice from this file.

```text
MANUAL FRAMEWORK: START NOW
FINAL AUTHORING: AFTER FUNCTIONAL V1 + CONTRACTOR LANGUAGE / UX AUDIT
BEN / KEVIN ACCESS: AFTER COMPLETED USER GUIDE / PRE-UAT GATE
V1: 60% / 4 OF 11 / NO RESCORE
```

---

# MANUAL AUDIENCE LAW — CONTROLLING

THE CALIBRAYTAI USER GUIDE IS WRITTEN FOR PEOPLE WHO BUILD, SELL,
SUPPLY, ESTIMATE AND MANAGE CONSTRUCTION WORK.

PRIMARY AUDIENCE INCLUDES:

- contractors
- construction business owners
- project managers
- estimators
- building-supply / building-store owners
- building-store staff
- field workers
- other normal construction-industry users

THE USER GUIDE IS NOT WRITTEN FOR:

- software developers
- architects of the software platform
- database engineers
- repository maintainers
- AI engineers

Assume the reader may be highly experienced in construction and have
ZERO interest in how CalibraytAI works under the hood.

That reader should be able to use CalibraytAI successfully without
learning its technical architecture.

---

# ABSOLUTE CONTENT RULE

DO NOT PUT INTERNAL SOFTWARE ARCHITECTURE INTO THE CONTRACTOR MANUAL
UNLESS A USER GENUINELY NEEDS THAT FACT TO PERFORM THEIR JOB.

The final contractor-facing Manual must not teach or expose concepts
such as:

- Feature Gates
- FG numbers
- ADRs
- repository governance
- Git
- commits / SHAs
- Alembic
- migrations
- database tables
- schemas
- models
- services
- APIs
- routes
- DTOs
- implementation slices
- internal module ownership
- internal authority hierarchy
- internal system-of-record terminology
- data lineage architecture
- internal IDs
- engineering test terminology

Those belong in INTERNAL DEVELOPMENT DOCUMENTATION.

They do not belong in the CalibraytAI User Guide.

---

# JOB-FIRST WRITING LAW

Every Manual topic begins with:

WHAT IS THE CONTRACTOR TRYING TO DO?

Not:

HOW IS CALIBRAYTAI ENGINEERED?

Write from the user's job outward.

Examples:

WRONG:

"WorkScheduleAssignment creates a USER XOR Crew relationship against an
ACTIVE WorkScheduleItem."

RIGHT:

"Assign someone to scheduled work

Open the Schedule, select the work, and choose the person or crew doing
the job."

WRONG:

"Sequence conflicts are deterministic non-persisted warning
projections."

RIGHT:

"Schedule warnings

CalibraytAI may warn you when work looks out of sequence or someone is
booked in two places. The warning helps you spot a possible problem.
It will not stop you from continuing."

---

# FIVE MANUAL WRITING TESTS

Every contractor-facing Manual section must pass:

1. JOB FIRST

Does this begin with what the contractor / supplier is trying to
accomplish?

2. PLAIN LANGUAGE

Would a normal contractor, estimator, supplier or field worker use and
understand these words?

3. ACTION ORIENTED

Does it explain what the user should do rather than how the software is
built?

4. VISUAL

Where a screenshot can explain the task faster and more clearly, plan
to use the screenshot.

5. SHORT

Use the fewest words necessary to make the user successful.

Do not turn simple workflows into technical essays.

---

# THE BEN / BUILDING-STORE TEST

Before accepting any final Manual content ask:

WOULD BEN ACTUALLY NEED OR WANT TO KNOW THIS TO DO HIS JOB?

AND:

COULD A BUILDING-STORE OWNER OR NORMAL CONSTRUCTION USER UNDERSTAND
THIS WITHOUT JOEL OR A DEVELOPER EXPLAINING IT?

If NO:

rewrite it or remove it.

Technical accuracy is necessary.

TECHNICAL EXPOSURE IS NOT.

---

# TERMINOLOGY TRANSLATION

Internal architecture may be necessary to BUILD CalibraytAI.

The Manual translates that architecture into normal construction
language.

Examples:

ProjectWorkElement
→ major work / phase / work item according to final contractor UX

WorkScheduleAssignment
→ assigned person / crew

ProjectWorkDependency
→ work sequencing / comes after / must follow

sequence conflict
→ Schedule warning

LabourTimeEntry
→ Time entry

scope_origin
→ explain Original Work / Change Order / Extra Work only where useful

Do not expose the internal term merely because it is technically
precise.

---

# SUPPLIER / BUILDING-STORE USERS

Do not assume every CalibraytAI user operates exactly like Brayman
Construction.

The Manual must remain understandable to building suppliers and other
construction businesses using the same platform.

Where workflows differ:

explain the PURPOSE and ACTION.

Do not explain tenant architecture or configuration machinery.

Organization-specific behavior should appear simply as the user's
configured CalibraytAI experience.

---

# FINAL QUALITY STANDARD

The finished User Guide should feel like:

A PROFESSIONAL PRACTICAL CONSTRUCTION SOFTWARE GUIDE.

It should NOT feel like:

developer documentation
a technical specification
repository documentation
an architecture report
an AI-generated engineering summary

A competent construction-industry user should be able to pick it up,
find what they need, perform the task, and get back to work.

---

## One Help Content authority (framework)

Final Manual, in-product Help, contextual Help, and Voice answers must come from **one** governed topic set.

Each future topic uses the same contractor job, the same words, and the same next step.

Until the language audit, this outline is a **plan**, not finished wording.

Core procedure shape for every later topic:

1. What does this do?
2. When would I use it?
3. How do I do it?
4. What happens next?

---

## Planned Manual parts

Final names follow the finished product and the language audit. Likely parts:

| Part | Contractor job this part should serve |
|------|----------------------------------------|
| Getting started | Sign in, find home, get around, reset password |
| Plan | Open a Project, see the Project Hub, find project information |
| Price | Build and review a priced estimate / Construction Estimate |
| Contract | Contract, Change Orders, send for signature |
| Schedule | See what is happening, set dates, assign people/crews, work order / comes after, Schedule warnings |
| Build | Field work, photos, Extra Work |
| Time | Record hours, submit, approve |
| Monitor | See how the job is tracking |
| Closeout | Finish the job cleanly |
| Learn | Improve future estimates from completed work |
| Everyday tasks | Short how-tos: reset password, find a Project, print when Print exists |

Do not treat this table as a promise that every later slice already exists.

---

## Screenshot / Print plan (later only)

Capture **after** remaining functional V1 and the language audit, from the actual finished product.

Plan screenshots where a picture is faster than prose: sign-in, Project Hub, Schedule, Time, Extra Work, Schedule warning that does not block continuing.

Desktop and iPhone where the work is actually done that way.

Print examples wait for the recorded Print workflow.

Do **not** capture screenshots now.

---

## Manual Impact

Close-time notes live in [manual-impact-log.md](manual-impact-log.md). They are **not** Manual chapters. Translate them with this Audience Law when final authoring starts.

---

## Explicitly not this framework

- Finished User Guide PDF or pages for Kevin / Ben
- In-product Help product
- Voice product
- Screenshot capture
- Language-audit execution
- Independent UAT
- V1 rescore
- Platform access for Kevin / Ben
