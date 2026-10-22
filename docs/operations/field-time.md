# Field time: screens, buttons, statuses and messages (22 Oct 2026)

This is a plain record of what the crew and the office see, for Field Crew training and UAT to follow.
There is one timekeeping system: Time Entry (FG-035). Synthetic names below.

## Statuses

| Status shown | Meaning |
|---|---|
| Submitted | Sent by the worker, waiting for approval. Not yet actual labour. |
| Returned | The office sent it back with a reason. The worker fixes it and sends it again. |
| Approved | Counts as actual labour hours and cost, and goes to the QuickBooks time file. |
| Replaced | An approved entry the office corrected later. The original is kept; the correction is a new entry. |

History on each entry (office: Time review → open the entry → History): Submitted, Returned (with the
reason and the hours at that time), Sent again, Approved, Replaced. Nothing is deleted.

## Crew, on the phone (Field)

**Today** (`/field/today`)
- Each scheduled job card has **Enter time**.
- Without a chosen job: **Choose Project** and **My time**. With a chosen job: Capture, **Time**, Extra work,
  **My time**, Change project.
- When time was returned: a red line at the top, "1 time entry was returned to you. Fix and send again on
  My time." It opens My time.

**Time** (`/field/projects/<job>/time`)
- Date (today by default; future dates are refused).
- **Scheduled today**: one button per piece of work the office scheduled for the person today. If the
  office scheduled a work item with several works under it, the button opens the **Work** box with only
  that item's works; choose one. If it has one work, it is filled in.
- **Recent work**: the last works the person used on this job.
- **Choose different work** opens **Work item** and **Work**.
- **Hours** (0.25 steps, at most 16 on one entry, at most 24 in a day). **Note** (optional).
- **+ Extra work** (customer jobs only): "What did the customer ask for?" — records the hours as extra work.
- **Send time**. Message: "Time sent for approval." (after a fix: "Time sent again for approval.").
- Messages when something is missing: "Choose the work you did.", "Choose the work you did on
  <work item>.", "Enter the hours worked.", "Time cannot be recorded for a future date.",
  "Hours for one day cannot be more than 24.00."

**My time** (`/field/time`)
- "This week (from Mon …): N hours · Approved · Waiting · Returned".
- **Time** for the chosen job (or **Choose a job for time**), and **Shop / company time** once the office
  has set it up.
- Each entry: date · status, job, work item — work, hours · kind of work (Original work, Change order work
  · CO number, Extra work, Company time), note.
- Submitted: "Waiting for approval. Ask the office if something is wrong; they can return it to you."
- Returned: "Returned: <reason>" and **Fix and send again** (opens Time with the entry filled in).
- Crew never see rates, costs, prices or pay. Field-only crew cannot open office pages.

**Shop / company time**: the Time page for "Shop and company time" ("Company time: not a customer's job,
never billed to a customer."). Works: Shop and yard, Equipment and vehicle upkeep, Material pickup and
deliveries, Safety meetings and training, Office and estimating. No Extra work button. It does not change
the job the person is on today.

## Office (desktop)

**Time review** (`/time`; from a job's Project page → Time → **Review time**, or ask Cal for time review)
- Filters: From, To, Worker, Project, Status. Default: the last seven days.
- "Hours in this view": by status, and by kind of work (Original work, Change order work · CO, Extra work,
  Company time).
- **Set up shop and company time** (once): "Shop and company time is ready. Crew choose Shop / company time
  on My Time; it is never billed to a customer."
- Tick Submitted rows and **Approve selected** ("Approved 1 time entry."). Click a date to open one entry.

**One entry** (`/time/<id>`)
- **Approve** → "Time approved."
- **Return reason** + **Return** → "Time returned." (a reason is required: "Say why the time is being returned.")
- Approved entries: **Correct approved time** (hours, date, reason) → "Approved time corrected. The
  original entry is kept."
- Nobody can approve or return their own time: "You cannot approve or return your own time."

**Project page → Labour** (`/projects/<job>#hub-labour-cost`): "Estimated and actual labour": one row each
for Original work, each change order, Extra work (not on an approved change order) and, on the company-time
project, Company time; then All labour. Columns: Estimated hours, Actual hours, Difference, Estimated cost,
Actual cost, Difference, Waiting for approval. Actual = approved hours × the company costing rate on the
Labour rates page in force on the work date (work before the first rate uses that first rate). Wages and
payroll are never used. Estimated cost uses the estimate's own labour rate where the work came from an
estimate.

**Company → Accounting → Approved time (hours to enter by hand)** and **Check time in QuickBooks**: see
`docs/operations/quickbooks.md`.

## UAT exercise (what the release walk does: `tools/release/evidence_field_time.mjs`)

1. Kevin (phone): Today → Enter time → Scheduled today → choose Forms → 8 → Send time; then Stair landing
   framing 3 hours. My time shows both Submitted, 11.00 this week.
2. Ben (desktop): Project page → Review time → open the 8-hour entry → Return with a reason; open the 3-hour
   entry → Approve.
3. Kevin: Today shows the returned line → My time → Fix and send again → 7.5 → Send time.
4. Ben approves; History shows Submitted 8.00, Returned 8.00 (reason), Sent again 7.50, Approved 7.50.
5. Ben: Set up shop and company time. Kevin: My time → Shop / company time → Equipment and vehicle upkeep
   1.5. Ben: tick it → Approve selected.
6. Project page: Original 40.00 estimated / 7.50 actual, $2,600.00 / $487.50; the change order 10.00 / 3.00,
   $650.00 / $195.00. Shop time is not on the customer's job.
7. Kevin cannot open the project page, Time review, Accounting or Labour rates.
8. Ben: Accounting → Approved time → Download the file (12.00 hours); the next file has nothing new;
   Check time in QuickBooks with the report → matches.
