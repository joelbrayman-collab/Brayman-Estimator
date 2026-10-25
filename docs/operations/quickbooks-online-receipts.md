# QuickBooks Online: receipts, the connection, and projects (25 Oct 2026)

Part of the Magnificent Seven everyday operations (`docs/operations/everyday-operations.md`).

- **Receipts**: a receipt photographed on Field (Add Receipt) is reviewed by Suzanne in Accounting → Receipts Inbox
  and, once approved, entered in QuickBooks Online **once**: as a new expense (Purchase) with the original image
  attached, or attached to the expense or bill already there.
- **Projects** (approved item A): a CalibraytAI project becomes a QuickBooks Online customer + project
  (sub-customer) and a QuickBooks Time job code, once. CalibraytAI owns the operational project; QuickBooks owns the
  accounting.

**Status: built and tested against an in-memory test QuickBooks company and Intuit's documented response shapes.
Switched off.** No test and no release walk reaches Intuit. Nothing is sent until Joel authorizes it and the
settings below are on the server. The sandbox check script (`tools/quickbooks/sandbox_check.py`) has **not been
run**: no sandbox credentials were available while building.

The file-based exports in `docs/operations/quickbooks.md` (customers, suppliers, invoices, bills) are unchanged and
keep working whether or not this connection is on.

## Switching it on (Joel's authorization required)

Environment settings on the server (never in the database, Git or logs):

| Setting | What it is |
|---|---|
| `QBO_SYNC_ENABLED=1` | Turns the QuickBooks Online connection on. Default off. |
| `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET` | The Intuit developer app's keys (developer.intuit.com → the app → Keys & credentials). |
| `QBO_REDIRECT_URI` | `https://<office host>/accounting/quickbooks/callback`, entered exactly the same in the Intuit app's Redirect URIs. |
| `QBO_ENVIRONMENT` | `sandbox` or `production`. |
| `QBO_TOKEN_KEY` | At least 32 random bytes, URL-safe base64. Encrypts the stored access and refresh tokens (`app/services/secret_box.py`). Without it nothing is stored and the connection refuses. Make one: `python -c "import secrets,base64;print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"` |
| `QBO_PROJECT_SYNC_ENABLED=1` | Projects into QuickBooks Online and QuickBooks Time. Default off; needs the connection above (and, for job codes, `QBT_SYNC_ENABLED=1` + `QBT_ACCESS_TOKEN`, `docs/operations/quickbooks-time.md`). |
| `QBT_JOBCODES_FROM_QBO=1` (optional) | Use when the company's QuickBooks Time imports customers and jobs from QuickBooks Online (Intuit's own integration). CalibraytAI then never makes a job code for a project; it waits for the imported one and Suzanne confirms it once. Default off (CalibraytAI makes the job code, as instructed). |

`flask quickbooks-online status` prints which of these the server has (names and yes/no only).

Then the owner (or a System Administrator; nobody else) opens Accounting → **QuickBooks Online connection** →
**Connect to QuickBooks**, signs in at Intuit and chooses the company. The page then shows the company name and the
mapping, which must be set before anything is sent:

| Mapping (company decision; empty until chosen) | Used for |
|---|---|
| Expense account | The Purchase line's account (e.g. Job Materials). |
| Payment account and payment type (Cash / Cheque / Credit card) | The Purchase's AccountRef and PaymentType. |
| Tax code (taxable) and tax code (no tax) | The line's TaxCodeRef. |
| Class (optional) | The line's ClassRef. |
| Create a vendor when QuickBooks has none (off by default) | Otherwise an unknown vendor stops the receipt at Needs Attention. |
| Send on approval (on by default; nothing is sent while the connection is off or the mapping is empty) | When off, approved receipts wait for Send now or the scheduled `flask quickbooks-online send-waiting`. |

While any required mapping is empty, sending refuses with the reason.

## Receipts: what happens

1. Field → **Add Receipt**: the photo goes up through the existing Field capture (with the phone's retry queue), then
   the receipt is registered against the capture (idempotent: the same capture never makes two receipts). Status
   **New**.
2. Suzanne (office financial access; Field-only crew never) reviews: supplier, date, subtotal + tax = total, the job or
   Shop / Company Expense, an optional purchase order. **Reviewed**, then **Approve for QuickBooks** → **Ready for
   QuickBooks**.
3. Sending (`app/services/quickbooks_online.py`), each receipt has a stable sync id `CT-RCPT-<company salt>-<id>`:
   - an expense already linked to the receipt, or a bill whose DocNumber is the linked purchase order, is used;
   - the vendor: the stored link, else a query by DisplayName, else (only if allowed) created; otherwise Needs Attention;
   - the customer / project: the project's QuickBooks project (item A) or its job reference;
   - existing Purchases / Bills for that vendor within 3 days with the same total: CalibraytAI's own (memo mark
     `[CT-R<id>]`) is adopted; exactly one other match → the image is attached to it; several → **Needs Attention**,
     Suzanne chooses one or enters it as new with a reason;
   - otherwise a Purchase is created with `requestid=<sync id>`, then the image uploaded with `requestid=<sync id>-A`.
   - Transfer states Pending → Sent → Confirmed / Failed. **Synced only when QuickBooks returned the record's Id.** A
     lost answer stays Sent; Retry sends the same request ids, so Intuit returns the first answer, not a second record.
4. Accounting → QuickBooks Online → **Reconciliation** lists each receipt and its QuickBooks Id once.

## Projects: what happens (approved item A)

`app/services/accounting_project_sync.py`; review screen Accounting → QuickBooks Online connection → **Projects in
QuickBooks** (`/accounting/quickbooks-online/projects`, Suzanne or the owner).

- **When**: after a project is created, after its proposal is accepted, after it is closed or reopened, and by
  `flask quickbooks-online sync-projects` (scheduler) or **Check all projects now**.
- **QuickBooks Online**: the customer (the CalibraytAI client) and the project as a sub-customer: `Customer` with
  `Job: true`, `ParentRef` → the customer, `BillWithParent: true`, DisplayName = the job reference
  ("BC-2026-014 Harbour Lane Pool Deck"). Creates carry `requestid` `CT-CUST-<salt>-<client>` /
  `CT-PROJ-<salt>-<project>`; Notes carry `[CT-C<client>]` / `[CT-P<project>]`.
- **QuickBooks Time**: a job code with the same name (`POST /jobcodes`), linked through the existing
  QuickBooks Time links so approved time goes to it. **Shop / Company Work is one fixed job code** linked to every
  shop / company category. QuickBooks Online gets no customer for Shop.
- **Never a duplicate**: the stored id first (read again for its current SyncToken); else an exact-name query
  (including inactive). A record CalibraytAI made itself (its mark, or a lost QuickBooks Time answer followed by a
  look-up) is adopted. **Any other record with that name is an existing job: it waits on the review screen until
  Suzanne or the owner presses "This is the same customer / project / job code"** — matched once, stored, used from
  then on (receipts too). It is on WHAT NEEDS MY ATTENTION? until then.
- **Renames and closures**: sparse updates (`Id`, `SyncToken`, `sparse: true`, `DisplayName`, `Active`) only;
  QuickBooks Time `PUT /jobcodes` with `name` / `active`. A closed project becomes **inactive**; nothing is deleted.
  No accounting field (balance, terms, tax, contact details…) is sent, and **no financial transaction is created**.
- Stored per project (`accounting_project_links`): QuickBooks Online customer and project Id + SyncToken, QuickBooks
  Time job code id, status (Off / Pending / Sent / Synced / Confirm the match / Failed) for each, last error, candidates,
  attempts, who confirmed and when. Every step is in the QuickBooks history (`quickbooks_online_events`, with the
  project). Failures and mismatches are on WHAT NEEDS MY ATTENTION? with **Retry** on the review screen.

## Scheduled jobs (to create on Render when switched on; not created by this build)

| Render cron job | Command | Schedule |
|---|---|---|
| End-of-day reminders | `flask reminders send-due` | every 15 minutes (`*/15 * * * *`) |
| Receipts waiting for QuickBooks | `flask quickbooks-online send-waiting` | every 15 minutes |
| Projects into QuickBooks | `flask quickbooks-online sync-projects` | hourly (`0 * * * *`) |

Each is safe to run as often as wanted (nothing is sent twice) and prints counts only. Same environment group as the
web service (database, `QBO_*`, `QBT_*`, Twilio settings).

## Checking against an Intuit sandbox (by hand)

`tools/quickbooks/sandbox_check.py` uses the application's own transports against a **sandbox** company only
(it refuses unless `QBO_ENVIRONMENT=sandbox`): token refresh, CompanyInfo, Customer query, customer + sub-customer
create with requestid, the same requestid again (same Id expected), sparse Active=false; and, with
`QBT_SANDBOX_ACCESS_TOKEN`, QuickBooks Time job code GET / POST / PUT. Needs `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`,
`QBO_SANDBOX_REALM_ID`, `QBO_SANDBOX_REFRESH_TOKEN` (Intuit rotates it; set `QBO_SANDBOX_TOKEN_OUT` to save the new
one with mode 600). Exit 0 passed, 1 failed, 2 not run. **It has not been run.**

## Tests

- `tests/test_magnificent_seven.py` (receipts: capture, review, approve, sent once, match → attach, ambiguous → Needs
  Attention, lost reply → retry without a second record, refresh on 401, tokens encrypted, owner-only connect,
  Field-only and other-company isolation).
- `tests/test_quickbooks_project_sync.py` (projects: off by default; create once; existing job matched once after
  confirmation; renames / closure sparse and never deleted; no transaction; Shop one job code; lost answers and
  failures retried without a second copy; QuickBooks Time importing from QuickBooks Online; Intuit's documented
  response shapes replayed from `tests/fixtures/intuit/` — documented shapes, **not** recorded from a live sandbox).
- `tools/release/evidence_magnificent_seven.mjs` (browser, desktop and phone).

## Intuit references

Read 25 Oct 2026. developer.intuit.com's API explorer pages are a single-page application that could not be fetched
from the build environment, so the shapes were taken from Intuit's own SDKs and Intuit's published posts:

| Fact | Source |
|---|---|
| OAuth 2.0 endpoints: authorize `https://appcenter.intuit.com/connect/oauth2`, tokens `https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer` (HTTP Basic client id : secret), revoke `https://developer.api.intuit.com/v2/oauth2/tokens/revoke`; scope `com.intuit.quickbooks.accounting`; refresh tokens rotate. | Intuit's Python OAuth client, `intuitlib/config.py`, `client.py`, `utils.py` — https://github.com/intuit/oauth-pythonclient |
| API base `https://quickbooks.api.intuit.com/v3/company/<realmId>/` (sandbox `https://sandbox-quickbooks.api.intuit.com`); `minorversion` (SDK default 75); `/query` POST with `Content-Type: application/text`. | Intuit's PHP SDK, `src/Core/CoreConstants.php` — https://github.com/intuit/QuickBooks-V3-PHP-SDK |
| `requestid` query parameter (at most 50 characters): a repeated request with the same id returns the first response instead of repeating the operation. | Intuit Developer blog, "Idempotency / requestid" — https://blogs.a.intuit.com/2015/04/06/15346/ |
| `/upload`: multipart with `file_metadata_01` (Attachable JSON with `AttachableRef` → `EntityRef`) and `file_content_01` (base64); answer `AttachableResponse`. | PHP SDK `DataService::Upload`; python-quickbooks `client.py` — https://github.com/ej2/python-quickbooks |
| Purchase: `PaymentType`, `AccountRef`, `EntityRef` (Vendor), `TxnDate`, `Line` of `AccountBasedExpenseLineDetail` (`AccountRef`, `CustomerRef`, `ClassRef`, `TaxCodeRef`, `BillableStatus`), `TxnTaxDetail.TotalTax`, `PrivateNote`, `DocNumber`. | python-quickbooks `objects/purchase.py`, `detailline.py`; Intuit API reference Purchase (developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/purchase) |
| Customer as a project/sub-customer: `Job: true`, `ParentRef`, `BillWithParent`; updates with `Id`, `SyncToken`, `sparse: true`; names unique across customers, vendors and employees (Fault 6240 Duplicate Name Exists); inactive records are hidden from queries unless asked for (`Active IN (true, false)`). | python-quickbooks `objects/customer.py`; Intuit API reference Customer (developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/customer) |
| Errors: `{"Fault": {"Error": [{"Message", "Detail", "code"}], "type"}}`; 401 → refresh the access token. | PHP SDK / python-quickbooks error handling |
| QuickBooks Time `/jobcodes`: GET with `ids`, `name`, `active` (yes / no / both); POST / PUT `{"data": [...]}`, per-item `_status_code`; `parent_id`, `type`, `assigned_to_all`. QuickBooks Online imports customers / jobs into QuickBooks Time when the integration is on. | QuickBooks Time API Reference, Jobcodes; see `docs/operations/quickbooks-time.md` |
