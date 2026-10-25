# Everyday operations: the Magnificent Seven (25 Oct 2026)

Joel's approved everyday package (brief: Magnificent Seven), plus two approved additions: projects into QuickBooks
(item A) and Sunday My Week (item B). One additive migration, `m7s3r5q8b2c4` (down `w2z9r4d7k1m6`): fourteen new
tables, no existing table changed; its downgrade refuses while any new table has a row.

| # | Workflow | Field (crew) | Office | Code |
|---|---|---|---|---|
| 1 | Receipts | Field Today → Add Receipt (photo through Field capture, offline retry) · My receipts | Project Hub → Receipts; Accounting → Receipts Inbox (office financial access) → QuickBooks Online | `app/services/receipts.py`, `quickbooks_online.py`; `docs/operations/quickbooks-online-receipts.md` |
| 2 | WHAT NEEDS MY ATTENTION? | — | Home (first, compact, above the wizards' What do you need to do?) and `/operations/attention` | `app/services/needs_attention.py` (live from the records; nothing stored) |
| 3 | Extra Work | Field → Extra Work (photo, notes) · My extra work (answer the office's question) | `/operations/extra-work` → question / the existing change-order form / decline | `app/services/extra_work_reports.py` |
| 4 | Need Materials | Field → Need Materials · My requests (status in plain words, no money) | `/operations/material-requests` → correct, approve, send through the existing supplier request → quote → purchase order. Nothing is sent or ordered automatically. | `app/services/material_requests.py` |
| 5 | Confirm Delivery | Field → Confirm Delivery: Received / Short / Damaged, counts, note, photo | `/operations/deliveries`: exceptions → The rest is coming / Replacement / Accept and close. Purchase-order lines are never changed; a full Received marks the order delivered (the existing path). | `app/services/delivery_confirmations.py` |
| 6 | Job Update | Field → Job Update, prefilled from the day's records; three questions | `/operations/job-updates`, the project history; a problem goes to the attention list. No time or cost is created. | `app/services/daily_summaries.py` |
| 7 | End-of-day reminders | Field Today "Before you finish today" (texts only if chosen, consented and switched on) | Owner counts; settings `/operations/reminders` | `app/services/reminders.py`; `docs/operations/end-of-day-reminders.md` |
| A | Projects into QuickBooks | — | Accounting → QuickBooks Online connection → Projects in QuickBooks | `app/services/accounting_project_sync.py`; `docs/operations/quickbooks-online-receipts.md` |
| B | Sunday My Week | Field → This week: on Sunday the coming Mon–Sun; Previous week / This (Coming) week / Next week (`?start=YYYY-MM-DD`) | — | `app/services/schedule.field_week_start` |

## Permissions

- Field-only crew reach only `field.*` pages (the new Field pages are on the Field blueprint and listed in
  `tests/test_security_route_sweep.py`); they see their own receipts and requests only, and never money.
- Receipts Inbox, receipt review, QuickBooks Online and Projects in QuickBooks: office financial access
  (`require_office_financial_access`). Connecting / disconnecting QuickBooks and changing reminder settings: the owner
  or a System Administrator only.
- `/operations/*` (material requests, extra work, deliveries, job updates, attention): office scheduling authority.
- Every record is scoped to its company; another company sees nothing (404).

## Company decisions left as settings (safe empty defaults)

- QuickBooks Online mapping: expense account, payment account and type, tax codes, class (optional) — empty; sending
  refuses until chosen. Create vendors automatically — off. Send on approval — on (nothing is sent while off/unmapped).
- Project sync — off (`QBO_PROJECT_SYNC_ENABLED`); `QBT_JOBCODES_FROM_QBO` — off.
- Reminders — 16:30 to 20:00, Monday to Friday, crew and owner on; texts per person — off.

## Scheduled jobs (document only; Render cron jobs are not created by this build)

`flask reminders send-due` every 15 minutes; `flask quickbooks-online send-waiting` every 15 minutes;
`flask quickbooks-online sync-projects` hourly. Details in the two linked documents.

## Training and evidence

Training Centre: contractor module 16 "Every day: what needs my attention" (owner, office) and Field Crew module 9
"Field quick actions", with acceptance tests (`uat-c16-*`, `uat-f09-*`), Workflow Map stages, Tutor answers and real
screenshots (`app/static/training/shots/m7-*.png`). Getting started step 16 and Ben's First Day manual
(`docs/operations/bens-first-day.pdf`, "Every day after that"). Tests: `tests/test_magnificent_seven.py`,
`tests/test_quickbooks_project_sync.py`; browser: `tools/release/evidence_magnificent_seven.mjs` (in
`release_gate.sh`).
