# V1 Desktop Contractor Experience — product-direction record

| Attribute | Value |
|-----------|--------|
| Status | **RECORDED V1 PRODUCT DIRECTION / MANDATORY V1 / MANDATORY PRE-BEN/TEAM REAL-WORLD UAT / IMPLEMENTATION SEQUENCED AFTER PERF ATTENTION / NOT IMPLEMENTED** |
| Recorded | 2026-09-17 |
| Authority | Joel Brayman / ChatGPT Architect |
| Centrepiece | Context-aware **Home Office** — a calm operational briefing, not a static dashboard |
| Does not interrupt | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. PERF-A **SEALED**. PERF-B / PERF-C **NOT AUTHORIZED**. |
| Siblings | [interactive-help-voice-and-user-manual-future-record.md](interactive-help-voice-and-user-manual-future-record.md) · [project-element-authority-future-record.md](project-element-authority-future-record.md) (Print + warning law) · [calibraytai-v1-user-guide-framework.md](calibraytai-v1-user-guide-framework.md) |

This is **not** an ADR, Feature Gate, preflight, schema, or product implementation. Do **not** implement Home Office, dashboard changes, PERF-B/C, Needs Attention, notifications, payroll, cash-flow product, banking, QuickBooks connection, QB-T, Print, Help, Voice, or the Manual from this file. Do **not** invent FG-036. Do **not** rescore V1 (**60% / 4 of 11**).

**Governed baseline at this recording:** HEAD / `origin/main` **`618dfaefbff1d5926bafa39c438075dc9c26055b`** (`docs: pin FG-035 PERF-A SHA`). Product PERF-A **`7a4b7000e2650eadf68b4ea44d48f75c65830c1f`**. Alembic **`f9b0c1d2e3f4 (head)`**. Working tree was **CLEAN** before this docs-only recording.

```text
V1 DESKTOP CONTRACTOR EXPERIENCE:
RECORDED
MANDATORY V1
MANDATORY BEFORE BEN/TEAM REAL-WORLD UAT
IMPLEMENTATION SEQUENCED AFTER PERF ATTENTION
NOT IMPLEMENTED
NO NEW ADR
NO NEW FEATURE GATE
V1 NOT RESCORED

CONTEXT-AWARE HOME OFFICE:
RECORDED
NOT IMPLEMENTED
CALM OPERATIONAL BRIEFING
NOT A STATIC DASHBOARD
CONTEXT CHANGES EMPHASIS
CONTEXT NEVER CHANGES ACCESS, AUTHORITY, OR FUNCTIONALITY

PERF-A: SEALED
PERF-B / PERF-C: NOT AUTHORIZED
```

---

## 1. This is not a beautification project

The V1 Desktop Contractor Experience is **not** merely a visual redesign.

The current/future desktop must not finish V1 looking like a collection of feature cards or dashboard boxes accumulated during development.

The objective is a coherent contractor operating environment that is:

- functional
- practical
- easy to use
- professional
- well thought out
- easy to navigate
- visually attractive
- pleasant to work in

Visual design must improve comprehension and workflow.

## 2. AiRIA inspiration (not a copy)

AiRIA is accepted inspiration for hierarchy, clarity, confidence, focus, breathing room, and purposeful presentation.

Do **not** copy AiRIA’s legal-product interface literally.

CalibraytAI remains purpose-built for contractors, construction companies, and suppliers.

Target feeling:

- This is organized.
- I know what is going on.
- I know what needs me.
- I know where to go next.
- This makes running the company easier.
- I like working in this.

## 3. Home Office is the centrepiece

Home Office is **not** a static dashboard.

It is a **calm operational briefing**.

Core question: **What is most useful to this contractor right now?**

When Ben opens CalibraytAI, Home Office should help him understand the business and decide what to do next without hunting through the platform.

Do **not** design the exact screen in this recording.

## 4. Context-aware Home Office law

**Context changes emphasis.**

**Context never changes access, authority, or functionality.**

CalibraytAI may bring information forward because it is timely or relevant.

It must not hide ordinary functionality merely because the platform believes another task is more appropriate at that time.

The contractor remains in control.

Context may eventually include time of day, day of week, upcoming work, Schedule conditions, payroll timing, known financial obligations, Project conditions, user role/context, and other governed facts.

Do **not** invent unsupported context signals.

## 5. Morning briefing

Morning emphasis: **Today · Needs Attention · Immediate readiness.**

The contractor should quickly understand:

- what jobs are happening today
- who is going where
- job-site locations
- crews / assignments
- immediate Schedule gaps
- important readiness facts supported by the platform
- what genuinely needs attention

Morning answers:

- Where are the boys?
- What is happening today?
- Is anything missing before everyone gets moving?
- What needs me?

Keep it calm. Do **not** manufacture urgency.

## 6. Daytime briefing

Daytime emphasis: **What is happening · What changed · What needs attention.**

Potential future governed facts may include Time submitted, Extra Work recorded, site observations / photos, Schedule changes, and tomorrow readiness emerging.

Do **not** implement a change-feed engine now.

Do **not** promise facts the platform cannot yet prove.

## 7. Evening briefing

Evening is a major V1 experience requirement.

Primary questions:

- Are we ready for tomorrow?
- What still needs me?
- What does the rest of the week look like?

Evening emphasis:

- Tomorrow
- Tomorrow readiness
- Review + notify team
- Week Ahead
- contextually relevant cash / payroll awareness

The evening experience should help the contractor finish the day with confidence rather than create another list of things to worry about.

## 8. Tomorrow readiness

Future Home Office should support a clear readiness conclusion such as:

**Tomorrow is ready**

or:

**2 things still need your attention**

Readiness may eventually consume only governed facts such as Schedule, worker / Crew assignments, job-site locations, team-notification state, and known delivery/readiness facts where supported.

Do **not** infer readiness from information the platform does not possess.

Do **not** implement readiness now.

## 9. Review + notify team

Mandatory V1 workflow direction:

**Review tomorrow → confirm who is going where → notify the team.**

Future worker notice should be concise and practical. Potential information: tomorrow/date, Project, start time where governed, work, job-site address, Directions.

The delivery mechanism is **not frozen** here. Possible future delivery could include text, email, or other governed channels.

Do **not** implement notification delivery.

Do **not** automatically send notices because the clock reaches a particular time.

Human review/send remains the expected direction unless separately changed.

## 10. Week Ahead

Evening Home Office should provide a clean visual understanding of the coming days.

Purpose: **Where are we headed?**

Potential compact facts: jobs per day, people / crews, assignment gaps, important readiness facts.

Then provide access to **View full Schedule**.

Do **not** reproduce the entire desktop Schedule on Home Office.

Do **not** design exact components now.

## 11. Cash is operational information

Cash flow is an important operating concern for a construction business.

Cash/payroll awareness belongs in the future Home Office information set.

Cash must **not** become the dominant emotional character of the platform.

Governing UX principle: **Cash awareness, not cash anxiety.**

## 12. Cash prominence is contextual

On a normal day, cash information may remain compact.

Before payroll, Payroll / Cash may become a prominent part of the evening briefing.

Before a material known payment, elevate appropriately.

A potential material shortfall based on governed facts should be presented clearly and neutrally.

A healthy / comfortable known position should summarize positively and allow cash information to recede.

Cash should be **prominent when relevant**, but **not the driving concern of Home Office**.

## 13. Payroll example / product intent only

A future evening briefing might truthfully present:

- Payroll tomorrow
- Estimated payroll: $X
- Latest available operating balance: $Y
- Known payments: $Z
- Estimated difference / position: $N

The purpose is to help the contractor see the facts before payroll.

Do **not** implement these calculations.

Do **not** freeze exact formulas here.

Do **not** invent current banking authority.

## 14. Financial language law

CalibraytAI must distinguish **fact**, **estimate**, and **unknown**.

Do **not** say “you can afford payroll” unless sufficient governed evidence actually supports that conclusion.

Prefer factual presentation such as:

- Latest available operating balance
- Estimated payroll
- Known payments
- Estimated position after known items

The contractor decides.

## 15. Positive states

CalibraytAI must not communicate only when something is wrong.

If tomorrow is ready: **say so.**

If no immediate cash item needs attention: **say so.**

If no material attention item exists: **do not manufacture one.**

Healthy / ready states are useful operational information.

## 16. Attention budget

**The interface has a limited attention budget.**

Not everything that can be surfaced deserves equal prominence.

Information earns prominence because it is time-relevant, actionable, material, or unusual.

Avoid a wall of alerts, badges, red/yellow/green states, tiles, and warnings.

If everything is urgent, nothing is useful.

## 17. CalibraytAI earns attention

**CalibraytAI earns the contractor’s attention.**

The platform should not constantly demand attention merely to appear intelligent.

Warnings remain subject to the existing platform Warning Law: **informational only / non-blocking**.

Contextual emphasis is also non-controlling.

## 18. QuickBooks / banking firewall

Future payroll/cash awareness may require governed data from QuickBooks, banking, payroll, or other sources.

Do **not** assume these integrations exist.

Real QuickBooks integration remains a separately governed future pre-Ben/team real-world-UAT gate.

Future integration investigation should consider:

- CalibraytAI → QuickBooks
- useful governed read-only awareness: QuickBooks / accounting data → CalibraytAI

Bank balance may require a separate banking-data source.

This recording does **not** authorize QuickBooks connection, bank connection, OAuth, banking plugin, accounting writes, QB-T, or financial implementation.

## 19. Desktop contractor UX audit

This V1 gate is broader than Home Office.

Before Ben/team real-world UAT, perform a bounded contractor UX audit of principal desktop workflows:

Home Office · Projects · Project Hub · Estimate / PRICE · Schedule · Time / Labour · Contracts · MONITOR · navigation · contractor language · visual consistency.

Ask:

- Can a contractor understand where they are?
- Can they find the next action?
- Is important information surfaced appropriately?
- Are repeated controls / clutter / dead space creating friction?
- Does the interface feel like one coherent professional product?

## 20. Visual standard

CalibraytAI should feel professional, serious, confident, clean, modern, purpose-built, and premium without being fancy.

Use established CalibraytAI brand direction.

Visual design should reinforce hierarchy and comprehension.

Avoid decorative complexity.

Avoid the feeling that boxes were slapped onto a dashboard.

## 21. Ben test

Future desktop acceptance standard:

**Could Ben sit down with minimal instruction and comfortably run the business from this desktop experience?**

The Desktop Contractor Experience must be tested before Ben/team real-world UAT.

Do **not** claim PASS now.

## 22. Relationship to PERF

Do **not** implement Home Office before the platform has factual attention information to make it useful.

Current sequence:

1. PERF-A — **SEALED**
2. PERF-B — **FUTURE**
3. PERF-C / company attention — **FUTURE**
4. then V1 Desktop Contractor Experience

The Desktop pass should consume real Needs Attention facts rather than invent hypothetical dashboard content.

This recording does **not** authorize PERF-B.

## 23. Print

Print remains separately recorded / sequenced later ([project-element-authority-future-record.md](project-element-authority-future-record.md)).

The future Desktop UX audit should consider Print where useful.

Do **not** implement Print here.

## 24. Manual

The Desktop Contractor Experience must align with the Manual Audience Law ([calibraytai-v1-user-guide-framework.md](calibraytai-v1-user-guide-framework.md)).

Contractor / supplier language.

The eventual User Guide should reflect the final accepted desktop workflow after this UX pass.

Do **not** write final Manual now.

## 25. V1 gate

**V1 Desktop Contractor Experience** is **mandatory V1** and **mandatory before Ben/team real-world UAT**.

This does **not** rescore V1.

Official: **60% / 4 of 11**. **NO RESCORE**.

## 26. STOP

```text
DOCS-ONLY PRODUCT-DIRECTION RECORDING.
NOT IMPLEMENTED.
DO NOT IMPLEMENT HOME OFFICE FROM THIS FILE.
DO NOT BEGIN PERF-B FROM THIS FILE.
DO NOT CONNECT QUICKBOOKS.
DO NOT RESCORE V1.
RETURN TO CHATGPT ARCHITECT.
```
