# QuickBooks Online with CalibraytAI

CalibraytAI keeps the jobs, proposals, change orders and purchase orders. QuickBooks Online keeps the books.
They meet through files you download from CalibraytAI and import in QuickBooks, and one report you export
from QuickBooks and upload back. CalibraytAI never asks for your QuickBooks password and never posts
anything to QuickBooks by itself.

Where: **Company → Accounting** (office people only; crew on Field never see it).

## Once, when you start

1. Accounting → **Customers** → Download the file. In QuickBooks: gear icon → **Import data** → **Customers**
   → choose the file → map the columns (they have the same names) → Import.
2. Accounting → **Suppliers (vendors)** → Download. QuickBooks: Import data → **Suppliers**.
3. In QuickBooks, check that the tax code **HST ON** (13 %) exists: Taxes → Sales tax settings. It is there
   by default for an Ontario company.
4. In QuickBooks, make one Product/Service called **Construction services** (Service, income account of
   your choice). Every invoice line uses it.

## Each invoice

1. Open the project → **Make an invoice** (beside Related Change Orders).
   - From the accepted proposal: Deposit, Progress or Final, as a percent of the proposal before HST or an
     amount. The Final invoice with no amount is what is left. You cannot invoice more than the proposal.
   - From an approved change order: the whole change order, once.
   - HST is the rate on the proposal or change order. The invoice number is INV-year-0001 and onward.
2. Accounting → **Invoices** → Download the file (only invoices not already sent to QuickBooks).
3. QuickBooks: gear icon → **Import data** → **Invoices** → choose the file. When asked:
   - Date format: **dd/MM/yyyy**
   - Amounts are: **Exclusive of tax**
   - Map InvoiceNo → Invoice number, Customer, InvoiceDate, DueDate, Item(Product/Service), ItemDescription,
     ItemQuantity, ItemRate, ItemAmount, ItemTaxCode.
   QuickBooks imports up to 100 invoices in one file; CalibraytAI never puts more in one file.

The job name is in each invoice's memo and line description, so QuickBooks reports can be filtered by job.
For full job costing, each estimate's **QuickBooks entry package** (Project → Workflow documents →
QuickBooks entry) lists the cost classes to enter.

## Supplier bills and purchase orders

- Accounting → **Bills from purchase orders**: a draft bill for each confirmed or delivered order, at the
  order amount before tax plus 13 % HST. **Check each against the supplier's own invoice** before
  importing (QuickBooks: Import data → Bills). Cancelled orders never appear.
- Accounting → **Purchase orders**: QuickBooks has no purchase-order import. The file is a list to enter
  by hand (+ New → Purchase order) if you track POs in QuickBooks.

## No duplicates

A record goes into a file once. The next file leaves it out. If an import failed and you need a record
again, choose **Include those again** and say why; the reason is kept in the history.

## Check that QuickBooks matches (weekly)

1. QuickBooks: **Reports → Invoice List** → set the dates → **Export → Export to CSV**.
2. Accounting → **Check QuickBooks** → choose that file → Check.
3. CalibraytAI shows:
   - **match**: same number and total;
   - **amount differs**: fix it in QuickBooks, then open the invoice here → Record a correction;
   - **exported but not in QuickBooks**: import the invoice file again (Include those again);
   - **in QuickBooks but not in CalibraytAI**: an invoice made directly in QuickBooks;
   - **in QuickBooks more than once**: delete the extra one in QuickBooks.
   Paid and partly paid come from the open balance and show on the invoice.

Every file, check and correction is in the Accounting history with who did it and when.

## A direct connection (not switched on)

A live QuickBooks connection is prepared but off. It would use Intuit's own sign-in page (OAuth); no
QuickBooks password would ever be stored. Remaining steps, each needing Joel's approval:

1. Create the app at developer.intuit.com (scope `com.intuit.quickbooks.accounting`), redirect URI
   `https://<live host>/accounting/quickbooks/callback`.
2. Add `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET` and `QBO_ENVIRONMENT` in Render's environment (never in Git).
3. Approve the token-storage migration and the sync rules (nothing posted without an office action).
4. Test against an Intuit sandbox company, then set `QBO_CONNECTION_ENABLED=1`.

Until then the files above are the supported way.
