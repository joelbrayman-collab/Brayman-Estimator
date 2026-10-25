#!/usr/bin/env python3
"""Check the project sync calls against an Intuit SANDBOX company (never production). Run by hand only.

It has NOT been run as part of the Magnificent Seven build: no sandbox credentials were available. The tests use the
in-memory fakes and Intuit's documented response shapes (tests/fixtures/intuit), and make no network call.

What it does, with the same transports the application uses:
  QuickBooks Online (sandbox-quickbooks.api.intuit.com, minorversion 75):
    1. refresh the access token (oauth.platform.intuit.com tokens/bearer, grant_type=refresh_token);
    2. read CompanyInfo;
    3. query Customer by DisplayName; create a test customer and a sub-customer (Job=true, ParentRef) with requestid;
    4. repeat the sub-customer create with the SAME requestid and check the same Id comes back (no duplicate);
    5. sparse-update the sub-customer to Active=false (nothing is deleted).
  QuickBooks Time (only when QBT_SANDBOX_ACCESS_TOKEN is set; use a TEST QuickBooks Time account):
    6. GET /jobcodes?name=...; POST /jobcodes; PUT /jobcodes active=false.

Needs (environment only; nothing is stored or printed):
  QBO_ENVIRONMENT=sandbox  QBO_CLIENT_ID  QBO_CLIENT_SECRET  QBO_SANDBOX_REALM_ID  QBO_SANDBOX_REFRESH_TOKEN
  optional QBT_SANDBOX_ACCESS_TOKEN
Intuit rotates the refresh token on use; the new one is written (mode 600) to QBO_SANDBOX_TOKEN_OUT when that is set.

Exit codes: 0 all checks passed, 1 a check failed, 2 not run (missing settings or not a sandbox).
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REQUIRED = ("QBO_CLIENT_ID", "QBO_CLIENT_SECRET", "QBO_SANDBOX_REALM_ID", "QBO_SANDBOX_REFRESH_TOKEN")


def _not_run(reason: str) -> int:
    print(f"SANDBOX_CHECK=not-run ({reason})")
    return 2


def _check(ok: bool, label: str) -> bool:
    print(("PASS " if ok else "FAIL ") + label)
    return ok


def main() -> int:
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        return _not_run("missing " + ", ".join(missing))
    if os.environ.get("QBO_ENVIRONMENT", "") != "sandbox":
        return _not_run("QBO_ENVIRONMENT must be sandbox; this script never touches production")
    from app.services.quickbooks_online_transport import MINOR_VERSION, HttpTransport

    qbo = HttpTransport("sandbox")
    cid, secret, realm = (os.environ[k] for k in ("QBO_CLIENT_ID", "QBO_CLIENT_SECRET", "QBO_SANDBOX_REALM_ID"))
    status, tokens = qbo.token({"grant_type": "refresh_token", "refresh_token": os.environ["QBO_SANDBOX_REFRESH_TOKEN"]},
                               client_id=cid, client_secret=secret)
    if not _check(status == 200 and "access_token" in tokens, "token refresh"):
        return 1
    out = os.environ.get("QBO_SANDBOX_TOKEN_OUT")
    if out and tokens.get("refresh_token"):
        Path(out).write_text(tokens["refresh_token"])
        os.chmod(out, 0o600)
    at = tokens["access_token"]
    ok = True

    def call(method, path, **kw):
        params = {"minorversion": MINOR_VERSION, **kw.pop("params", {})}
        return qbo.api(method, realm, path, access_token=at, params=params, **kw)

    status, info, _ = call("GET", f"companyinfo/{realm}")
    ok &= _check(status == 200 and "CompanyInfo" in info, "CompanyInfo read")
    tag = secrets.token_hex(4)
    parent_name, job_name = f"CT sandbox check customer {tag}", f"CT sandbox check job {tag}"
    status, found, _ = call("POST", "query", text_body=f"select * from Customer where DisplayName = '{parent_name}'")
    ok &= _check(status == 200 and not (found.get("QueryResponse") or {}).get("Customer"), "Customer query (none yet)")
    status, made, _ = call("POST", "customer", params={"requestid": f"CT-SBX-C-{tag}"},
                           json_body={"DisplayName": parent_name, "Notes": "[CT-SANDBOX]"})
    if not _check(status == 200 and made.get("Customer", {}).get("Id"), "customer create"):
        return 1
    parent = made["Customer"]
    body = {"DisplayName": job_name, "Job": True, "ParentRef": {"value": parent["Id"]}, "BillWithParent": True}
    status, job, _ = call("POST", "customer", params={"requestid": f"CT-SBX-P-{tag}"}, json_body=body)
    if not _check(status == 200 and job.get("Customer", {}).get("Job") is True, "sub-customer (project) create"):
        return 1
    job = job["Customer"]
    ok &= _check(job.get("ParentRef", {}).get("value") == parent["Id"], "sub-customer ParentRef")
    status, again, _ = call("POST", "customer", params={"requestid": f"CT-SBX-P-{tag}"}, json_body=body)
    ok &= _check(status == 200 and again.get("Customer", {}).get("Id") == job["Id"], "same requestid -> same Id")
    status, upd, _ = call("POST", "customer", json_body={"Id": job["Id"], "SyncToken": job["SyncToken"],
                                                         "sparse": True, "Active": False})
    ok &= _check(status == 200 and upd.get("Customer", {}).get("Active") is False, "sparse update Active=false")

    qbt_token = os.environ.get("QBT_SANDBOX_ACCESS_TOKEN")
    if qbt_token:
        from app.services.quickbooks_time_transport import HttpTransport as QbtTransport

        qbt = QbtTransport(qbt_token)
        name = f"CT sandbox check {tag}"[:64]
        status, got = qbt.request("GET", "jobcodes", params={"name": name, "active": "both"})
        ok &= _check(status == 200, "QuickBooks Time jobcodes GET")
        status, posted = qbt.request("POST", "jobcodes", body={"data": [{"name": name, "type": "regular"}]})
        rows = list(((posted.get("results") or {}).get("jobcodes") or {}).values())
        ok &= _check(status == 200 and rows and rows[0].get("_status_code") == 200, "QuickBooks Time jobcode create")
        if rows and rows[0].get("id"):
            status, put = qbt.request("PUT", "jobcodes", body={"data": [{"id": rows[0]["id"], "active": False}]})
            ok &= _check(status == 200, "QuickBooks Time jobcode inactive")
    else:
        print("SKIP QuickBooks Time (QBT_SANDBOX_ACCESS_TOKEN not set)")
    print("SANDBOX_CHECK=" + ("passed" if ok else "failed"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
