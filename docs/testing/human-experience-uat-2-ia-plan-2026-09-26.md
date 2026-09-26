# Human Experience UAT 2 — information architecture plan

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-26 |
| Status | **ACCEPTED / NOT YET IMPLEMENTED** at this checkpoint |
| Baseline | `ae37c0fa52b986ebc5a628f19bc8ccc3de2bb2bb` live as `dep-darrc4jncjis73eqcr5g` |
| Prior audit | [contractor-ux-e2e-audit-2026-09-26.md](contractor-ux-e2e-audit-2026-09-26.md) |
| Prior Wave 1 | **NOT AUTHORIZED.** Superseded by this plan. |

Joel’s live pass takes precedence. No product code in this record.

## Acceptance — 26 Sep 2026

ChatGPT Architect accepted this plan. Joel resolved the three open choices:

1. Estimates and Proposals leave the permanent left navigation. Routes, Home counts, and project access stay.
2. Projects stays in the permanent left navigation.
3. The cost area is named Costs & pricing. Not Company costs.

Waves A and B are the next implementation, together, so Company Calendar is not a renamed Schedule page. Wave C is not started. The earlier Wave 1 stays superseded.

## What he said

Home is much cleaner. He likes the calendar. It was too dominant on Home, and now he cannot find it. Home should name the company, list the existing counts vertically, and show a clear Company Calendar. Schedule, as a page, does not make sense to him. Cost items, Materials, Assemblies, Labour rates, and Pricing still expose the internal model. Previous estimates belong in a company library. Proposal templates do not belong with costs.

## Schedule versus the calendar

The month calendar he used was the Home planning view (`app/services/home_planning.py`, previously `app/templates/dashboard.html`). It was removed from Home. It was not placed on Schedule.

Schedule (`app/templates/schedule/company.html`, `assemble_schedule`) is a date-range list of the same scheduled work: unscheduled project work, per-project bars, dates, assigned people, and move-by-days. Same records. Different screen. That is why the menu item feels pointless.

Recommended contractor concept: **Company Calendar**. One page. Month first, then the day, then work still waiting for dates. The current Schedule tools stay on that page. The word Schedule does not need its own destination.

## Costs, in the product

A cost item is the company’s unit cost. Categories already include Labour, Material, Equipment, Subcontractor, Allowance, and Other. A material catalogue row is what the thing is. It stores no price. An assembly is a reusable bundle of cost items. A labour task, a production rate, and an hourly labour cost are a second labour path used when an estimate records labour. A pricing policy turns an estimate’s cost into the customer price. Past estimates are uploaded workbooks. They are evidence. They are not live estimates. A person must approve a suggested rate or speed before it becomes the company’s rate.

A future supplier feed would update what the company pays on a cost item. It would not replace the material’s identity.

## Proposed shape

Company name at the top, from the current brand profile’s customer-facing name, otherwise the organization display name. Not a hard-coded company name.

Home. Company Calendar. Projects. Clients.

Costs & pricing: what we pay, reusable work, how cost becomes price. Materials and labour learning sit behind that, not as five peers.

Company library: past jobs, and proposal templates if they are not kept under Proposals.

Hidden from daily navigation: calibration, mappings, purchase orders, job costing, reports, AI, and the parked decision tool.

## Waves

Not authorized. A navigation and names. B Home and Company Calendar. C the costs first screen. D labour daily view versus suggestions waiting for approval. E company library pages. F the project page. Do not repeat the earlier list-pattern Wave 1.
