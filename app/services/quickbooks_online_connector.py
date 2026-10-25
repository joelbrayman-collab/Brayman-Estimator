"""QuickBooks Online direct connection: prepared, not switched on (Joel, 21 Oct 2026).

No credential is stored in the code, the database or the logs. The connection would use Intuit's OAuth 2.0
(the contractor signs in on Intuit's own page and approves access; CalibraytAI never sees the QuickBooks
password). Until Joel authorises it, this module makes no network call and every operation says so.

Remaining steps to switch it on (each needs Joel's authorisation):
1. Create a production app at developer.intuit.com (scope com.intuit.quickbooks.accounting) with the
   redirect URI https://<live host>/accounting/quickbooks/callback.
2. Put its Client ID and Client Secret in Render as QBO_CLIENT_ID and QBO_CLIENT_SECRET (environment
   variables, never in Git), and QBO_ENVIRONMENT=production.
3. Approve the token storage migration (encrypted refresh token per organisation) and the sync rules:
   which records go to QuickBooks, and that nothing is posted automatically without an office action.
4. Set QBO_CONNECTION_ENABLED=1 only after the above is tested against an Intuit sandbox company.
Until then the file exports on the Accounting page are the supported way in and out of QuickBooks.
"""

from __future__ import annotations

import os

AUTHORIZE_URL = "https://appcenter.intuit.com/connect/oauth2"
SCOPE = "com.intuit.quickbooks.accounting"
REQUIRED_SETTINGS = ("QBO_CLIENT_ID", "QBO_CLIENT_SECRET", "QBO_ENVIRONMENT")


class QuickBooksNotConnected(RuntimeError):
    pass


def status() -> dict:
    present = [name for name in REQUIRED_SETTINGS if os.environ.get(name)]
    enabled = os.environ.get("QBO_CONNECTION_ENABLED") == "1"
    # Invoices, bills, customers and suppliers still go by file. Receipts have their own QuickBooks Online
    # connection since 25 Oct 2026 (app/services/quickbooks_online.py, Accounting → QuickBooks Online).
    message = "Invoices, bills, customers and suppliers go to QuickBooks by the files below."
    return {"connected": False, "enabled_flag": enabled, "settings_present": present,
            "settings_missing": [n for n in REQUIRED_SETTINGS if n not in present], "message": message}


def connect(*_args, **_kwargs):
    raise QuickBooksNotConnected("The direct QuickBooks connection is not switched on.")


def push(*_args, **_kwargs):
    raise QuickBooksNotConnected("Nothing is sent to QuickBooks automatically. Export the file and import it.")
