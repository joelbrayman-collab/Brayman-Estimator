# QuickBooks Time: approved hours for payroll (22 Oct 2026)

CalibraytAI is the one place crew enter hours (Field → Time). When the office approves time, each approved
entry is sent to **QuickBooks Time** (formerly TSheets) once, as a timesheet, so Suzanne's existing QuickBooks
Online payroll uses the same hours with no retyping. Hours only: no rate, wage or money is sent.

**Status: built and tested against a fake QuickBooks Time account. Switched off.** Nothing is sent to Intuit
until Joel approves it and the two settings below are put in the server's environment.

Projects' job codes (one per job, one Shop / Company Work) are made and kept in step by the project sync,
`docs/operations/quickbooks-online-receipts.md` (off until `QBO_PROJECT_SYNC_ENABLED=1`).

Plain instructions for Suzanne: `docs/operations/payroll-suzanne.md`. Crew and office screens:
`docs/operations/field-time.md`.

## What Intuit's documentation confirms (read 22 Oct 2026)

| Fact | Source |
|---|---|
| Base URL `https://rest.tsheets.com/api/v1`, TLS only. | QuickBooks Time API Reference, Welcome |
| Auth is OAuth 2.0 bearer tokens. A company admin can instead create an access token in the web UI: **Feature Add-ons → API → Add a new application → Add Token** (the "API Add-On"); its expiry can be extended there, so no refresh flow is needed. "Treat them just like passwords." OAuth tokens expire after `expires_in` (example 864000 s = 10 days) and are refreshed with a refresh token. | API Reference, Authentication; Walkthroughs → Obtaining an API Access Token |
| `POST /timesheets` creates timesheets. Required for every timesheet: `user_id`, `jobcode_id`, `type`. A **manual** timesheet needs `date` (YYYY-MM-DD) and `duration` (seconds; stored as hours rounded to 2 decimals). `notes` is optional. Each item comes back with `_status_code` / `_status_message` (200/201 created; 403 TS-1006 user may not track time; 406 conflict with another timesheet; 417 something missing or wrong). | API Reference, Timesheets → Create Timesheets |
| `PUT /timesheets` edits by `id` (`jobcode_id`, `notes`, `date`, `duration` optional). Per-item 404 = deleted; 409 = not modified because of a conflict; 417 = bad properties. | Timesheets → Update Timesheets |
| `DELETE /timesheets?ids=` deletes permanently (timesheets cannot be archived). | Timesheets → Delete Timesheets |
| Batches: at most **50 timesheets** per request (else HTTP 413). | Create / Update / Delete Timesheets |
| `GET /timesheets` needs `ids`, `start_date` or a `modified_*` filter; filters `user_ids`, `jobcode_ids`, `end_date`; pages of up to 200 with `more`. | Timesheets → Retrieve Timesheets |
| Rate limit: **300 calls in any 5 minutes per access token**; above it, HTTP 429 until the window ends. | Welcome → Request Throttling |
| `locked` > 0 means locked (exported, invoiced…). Approval is separate: the user's `approved_to` / `submitted_to` dates (Approvals add-on). "Only use payroll entries where the user's time has been approved." | Timesheets object; Users / Reports |
| Users have `payroll_id` ("usually used for linking with external systems"); jobcodes have `type` regular / pto / paid_break / unpaid_break, `parent_id`, `billable`. | Users and Jobcodes objects |
| There is **no idempotency key** in the API. CalibraytAI therefore marks each timesheet's notes with `[CT-T<entry>]` and reads that person's timesheets for those dates before any create. | (design consequence of the above) |
| QuickBooks Online imports employees, customers/jobs, service items and payroll items into QuickBooks Time automatically; "Use QuickBooks Online for payroll" is an integration preference; payroll items map to time types. | Intuit help: Integrate QuickBooks Time and QuickBooks Online |
| Approving in QuickBooks Time: Approve → **Approve and lock time**. "No one can edit approved timesheets unless you unapprove them." "Once you approve time, you can use it for payroll, invoicing, and reporting in QuickBooks." | Intuit help: Use QuickBooks Time in QuickBooks Online or QuickBooks Online Payroll (CA edition) |
| QuickBooks Online Payroll **Premium and Elite include QuickBooks Time**; "QuickBooks Time can be used with any of our QuickBooks Online Payroll products." | Intuit help (CA): Set up QuickBooks Time in QuickBooks Online Payroll; Timesheet setup: QuickBooks Online and QuickBooks Time |
| Intuit also lists a newer "Time API with payroll compensation" as one of its **Premium APIs**, for Gold and Platinum Intuit App Partners only. Its pages did not render for reading here; CalibraytAI does not use it. | Intuit Developer blog |

**Not confirmed by the documentation, and therefore a check Suzanne makes in her own account before switching
on:** that QuickBooks Online Payroll (Canada) pre-fills each employee's paycheque hours from the QuickBooks Time
timesheets CalibraytAI creates. Intuit's Canadian articles say approved time "can be used" for payroll and that
pay hours are calculated automatically from timesheets, but do not spell out the mechanism for timesheets
created through the API. The test is in "Switching on", step 5.

Sources:
- QuickBooks Time API Reference — https://tsheetsteam.github.io/api_docs/ (source:
  https://github.com/tsheetsteam/api_docs, `source/includes/APIReference/Timesheets/*`,
  `Overview/_authentication.md.erb`, `Overview/_welcome.md.erb`, `Overview/_walkthroughs.md.erb`, last commit 18 Jan 2024)
- Intuit Developer, QuickBooks Time / payroll-time pages (JavaScript-only; listed for reference):
  https://developer.intuit.com/app/developer/payroll-time/docs/workflows/track-time-legacy,
  https://developer.intuit.com/app/developer/qbo/docs/workflows/track-time/develop-time
- Integrate QuickBooks Time and QuickBooks Online —
  https://quickbooks.intuit.com/learn-support/en-us/help-article/manage-integrations/integrate-quickbooks-time-quickbooks-online/L1TenpapO_US_en_US
- Use QuickBooks Time in QuickBooks Online or QuickBooks Online Payroll (Canada) —
  https://quickbooks.intuit.com/learn-support/en-ca/help-article/track-worker-hours/use-quickbooks-time-quickbooks-online-quickbooks/L5NIFCKG6_CA_en_CA
- Set up QuickBooks Time in QuickBooks Online or QuickBooks Online Payroll (Canada) —
  https://quickbooks.intuit.com/learn-support/en-ca/help-article/process-payroll/set-tsheets-account-quickbooks-online-payroll/L2DxYHusM_CA_en_CA
- Timesheet setup: QuickBooks Online and QuickBooks Time (Canada) —
  https://quickbooks.intuit.com/learn-support/en-ca/help-article/payroll-processes/timesheet-setup-quickbooks-online-quickbooks-time/L7vJEVKaw_CA_en_CA
- About QuickBooks integration preferences in QuickBooks Time —
  https://quickbooks.intuit.com/learn-support/en-us/help-article/manage-integrations/quickbooks-integration-preferences-quickbooks-time/L2dFpl2W5_US_en_US
- Time API with payroll compensation (Premium APIs) —
  https://blogs.intuit.com/category/quickbooks-online-api/time-api-with-payroll-compensation

## How CalibraytAI uses it

- **One transfer per approved entry** (`qbtime_transfers`, unique per entry). Created in the same database
  transaction as the approval, so an approval and its transfer record exist together or not at all.
- **Sent right after approval** (Approve, Approve selected, Correct approved time), and by **Send waiting and
  retry failed** / **Retry** on Company → Accounting → QuickBooks Time transfers (`/time/quickbooks-time`).
  A send that fails never undoes the approval.
- **Manual timesheets**: `user_id` (the linked QuickBooks Time person), `jobcode_id` (the linked job code),
  `type: manual`, `date`, `duration` = hours × 3600, `notes` = kind of work, work item — work, job, and
  `[CT-T<first entry of the correction chain>]`. No money.
- **No duplicates**: before creating, CalibraytAI reads `GET /timesheets?user_ids=…&start_date=…&end_date=…`
  (all dates in the correction chain) and adopts an existing timesheet carrying the same mark (then updates it).
  If that read fails, nothing is sent ("Could not check QuickBooks Time before sending"). Transfers are claimed
  with `UPDATE … WHERE status IN (…)` before sending. Batches of at most 50.
- **Corrections** (Correct approved time) send `PUT /timesheets` with the same QuickBooks Time timesheet id.
  A correction made before the first send cancels the first transfer; only the correction is sent.
- **Hand-entry file and connector never both**: once anything was tried for an entry, it leaves the
  "Approved time (hours to enter by hand)" file; an entry already in a hand-entry file is held back ("In a
  hand-entry file (not sent)") until the office presses **Send anyway** with a reason.
- **Failures** stay on the page with the reason and **Retry**: 401 token refused; 403 access refused; 429 slow
  down; 409 "the week may be approved or locked there — unapprove it in QuickBooks Time, then Retry"; 417
  missing/wrong person, job code, date or hours; 404 on update = deleted there (Retry creates it again);
  a lost answer = outcome unknown (Retry checks first).
- **Links** (`/time/quickbooks-time/links`): each crew member → QuickBooks Time person; each customer job → job
  code; each Shop / Company Work category → a job code that belongs to no customer. When switched on, the
  page lists QuickBooks Time's people and job codes to choose from. Only the owner or a System Administrator
  changes a link; each change (old → new) is in the history. A QuickBooks Time person can be linked to one
  worker only.
- **Check QuickBooks Time** (`/time/quickbooks-time/check`, reads only): match; different there (hours, date
  or job code); sent but no longer there; in QuickBooks Time more than once; entered directly in QuickBooks
  Time; approved here but not sent yet.
- **History**: every queue, link, send, update, failure, retry, release and check is in `qbtime_events`.

## Credentials

- **Never** in Git, the database, logs or pages. The token is read from the environment only, sent as
  `Authorization: Bearer`, and never printed (`HttpTransport.__repr__` hides it).
- `QBT_SYNC_ENABLED=1` and `QBT_ACCESS_TOKEN=<token>` (Render environment of the CalibraytAI service, or the
  HostPapa server's environment). Optional `QBT_BASE_URL` (default `https://rest.tsheets.com/api/v1`).
  Either setting alone does nothing.
- The token chosen for V1 is the **admin-created API Add-On access token** (one company, one token, expiry
  extendable in QuickBooks Time). It needs no token table and no OAuth callback. A full OAuth app (client id /
  secret, redirect URI, refresh-token storage) would be needed only for several companies; that would need
  its own approved migration, following `app/services/quickbooks_online_connector.py`'s plan (encrypted
  refresh token per organization).

## Switching on (each step needs Joel's approval)

What Joel or Suzanne must provide:
1. **A QuickBooks Time account connected to the company's QuickBooks Online** (included with QuickBooks Online
   Payroll Premium or Elite), with employees and customers/jobs imported from QuickBooks Online and
   "Use QuickBooks Online for payroll" chosen in QuickBooks Time's QuickBooks integration preferences.
2. **The API Add-On access token**: a QuickBooks Time admin installs the API Add-On (Feature Add-ons → Manage
   Add-ons → API → Install), Add a new application (name "CalibraytAI", any redirect URI), **Add Token**, and
   gives the token to Joel privately (not by email or text in clear; it is a password). Extend its expiry.
3. Claude puts `QBT_ACCESS_TOKEN` and `QBT_SYNC_ENABLED=1` in the server environment (never in Git).
4. Links: Accounting → QuickBooks Time transfers → People and job links: each person and job, and each Shop /
   Company Work category (create matching non-customer job codes in QuickBooks Time first, e.g. "Shop").
5. **Payroll test with one real but harmless week, or Intuit's sandbox first**: approve one crew member's hours,
   see "In QuickBooks Time", open QuickBooks Time and QuickBooks Online Payroll's next pay run, and confirm the
   hours appear on that employee's paycheque. If they do not, Suzanne uses QuickBooks Time's own
   approval/export to payroll as she does today; CalibraytAI still removed the retyping.
6. Decide whether time is also approved in QuickBooks Time (the Approvals add-on) or only in CalibraytAI.
   If both, Suzanne approves the week in QuickBooks Time after CalibraytAI sends it; after that, corrections
   from CalibraytAI fail with "unapprove that week in QuickBooks Time, then Retry" (Intuit locks approved time).

## Questions for Joel and Suzanne

- Which QuickBooks Online Payroll plan is in use (Core / Premium / Elite)? QuickBooks Time comes with Premium
  and Elite.
- Does Suzanne want to approve again in QuickBooks Time, or treat CalibraytAI's approval as final?
- Overtime and banked hours in payroll: if hours over the week are banked (see the hours policy), QuickBooks
  Time's own overtime settings must not also pay them as overtime. Which does payroll follow?
- Banked time taken off: should it go to QuickBooks Time as a PTO job code (so payroll pays it), or does
  Suzanne enter it in payroll herself from the Banked hours page? (Not sent today.)
- Are any crew paid by salary rather than by the hour (their hours would still go, for job costing)?

## Tests

`tests/test_time_payroll_handoff.py` (fake QuickBooks Time account, no network): enter once → approve →
one timesheet; repeated sends and a lost answer never duplicate; corrections update the same timesheet;
429/409/401/417 failures shown and retried; a failed look-up sends nothing; switched off by default and the
token never shown; hand-file entries held back; reconciliation; owner-only, audited links; organization
isolation. Browser walk: `tools/release/evidence_time_payroll.mjs`.
