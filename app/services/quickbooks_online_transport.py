"""Transports for the QuickBooks Online Accounting API (Intuit). See docs/operations/quickbooks-online-receipts.md.

``HttpTransport`` is the only code that talks to Intuit. It is built only when the connection is switched on
(QBO_SYNC_ENABLED=1 with the Intuit app keys; app/services/quickbooks_online.py get_transport). Tokens and the
client secret travel only in the Authorization header and are never logged, stored in plain text or shown.

Endpoints and shapes (Intuit's documentation and its own SDKs, cited in the operations guide):
- OAuth 2.0 authorization code flow: https://appcenter.intuit.com/connect/oauth2 (scope com.intuit.quickbooks.
  accounting); tokens from https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer (HTTP Basic client_id:secret,
  grant_type=authorization_code with code + redirect_uri, or grant_type=refresh_token); revoke at
  https://developer.api.intuit.com/v2/oauth2/tokens/revoke.
- Accounting API: https://quickbooks.api.intuit.com/v3/company/<realmId>/<entity> (sandbox:
  https://sandbox-quickbooks.api.intuit.com), ``minorversion`` on every call, ``requestid`` (at most 50 characters)
  so a repeated create returns the first answer instead of making a second record; ``/query`` takes the query as
  text (Content-Type application/text); ``/upload`` takes multipart/form-data with ``file_metadata_01`` (JSON
  Attachable with AttachableRef → EntityRef) and ``file_content_01`` (the file) and answers ``AttachableResponse``.
- Errors come back as ``{"Fault": {"Error": [{"Message", "Detail", "code"}], "type"}}``.

``FakeQuickBooksOnline`` is an in-memory QuickBooks company with those request and response shapes. Tests and the
release walk use it; it can fail the ways the real API fails (HTTP 401/429/5xx, a validation Fault, a lost reply
after the record was made). It is never selected from the environment. No test reaches Intuit.
"""

from __future__ import annotations

import base64
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from copy import deepcopy
from typing import Optional

AUTHORIZE_URL = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
SCOPE = "com.intuit.quickbooks.accounting"
API_BASE = {"sandbox": "https://sandbox-quickbooks.api.intuit.com/v3",
            "production": "https://quickbooks.api.intuit.com/v3"}
MINOR_VERSION = "75"
TIMEOUT_SECONDS = 30


class TransportError(RuntimeError):
    """The request may or may not have reached QuickBooks Online (network failure, timeout)."""


def basic_auth(client_id: str, client_secret: str) -> str:
    return "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")


def multipart_upload(metadata: dict, filename: str, content_type: str, data: bytes):
    """The /upload body exactly as Intuit's SDKs send it: JSON metadata, then the file in base64."""
    boundary = "CalibraytAI-" + secrets.token_hex(12)
    safe_name = re.sub(r'[\r\n"]', "_", filename or "receipt.jpg")
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file_metadata_01\"\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit\r\n\r\n"
        f"{json.dumps(metadata)}\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file_content_01\"; filename=\"{safe_name}\"\r\n"
        f"Content-Type: {content_type}\r\nContent-Transfer-Encoding: base64\r\n\r\n"
        f"{base64.b64encode(data).decode('ascii')}\r\n",
        f"--{boundary}--\r\n",
    ]
    return "".join(parts).encode("utf-8"), f"multipart/form-data; boundary={boundary}"


def parse_multipart(body: bytes, content_type: str) -> dict:
    """Split a multipart body into {name: (headers, payload)} (the fake's half of multipart_upload)."""
    boundary = content_type.split("boundary=", 1)[1]
    out = {}
    for chunk in body.split(f"--{boundary}".encode()):
        chunk = chunk.strip(b"\r\n")
        if not chunk or chunk == b"--":
            continue
        head, _, payload = chunk.partition(b"\r\n\r\n")
        headers = {}
        for line in head.decode("utf-8").split("\r\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        name = re.search(r'name="([^"]+)"', headers.get("content-disposition", ""))
        out[name.group(1) if name else ""] = (headers, payload)
    return out


class HttpTransport:
    def __init__(self, environment: str = "sandbox", timeout: int = TIMEOUT_SECONDS):
        if environment not in API_BASE:
            raise ValueError("QBO_ENVIRONMENT must be sandbox or production.")
        self.environment = environment
        self.api_base = API_BASE[environment]
        self.timeout = timeout

    def __repr__(self):
        return f"<QBO HttpTransport {self.environment}>"

    def _send(self, req):
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (fixed https Intuit URLs)
                raw = resp.read()
                return resp.status, (json.loads(raw.decode("utf-8")) if raw else {}), resp.headers.get("intuit_tid")
        except urllib.error.HTTPError as exc:
            raw = exc.read() or b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except ValueError:
                payload = {}
            return exc.code, payload, exc.headers.get("intuit_tid") if exc.headers else None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TransportError(f"QuickBooks Online could not be reached ({exc.__class__.__name__}).") from None

    def token(self, form: dict, *, client_id: str, client_secret: str):
        req = urllib.request.Request(TOKEN_URL, data=urllib.parse.urlencode(form).encode(), method="POST")
        req.add_header("Authorization", basic_auth(client_id, client_secret))
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/json")
        return self._send(req)[:2]

    def revoke(self, token: str, *, client_id: str, client_secret: str):
        req = urllib.request.Request(REVOKE_URL, data=json.dumps({"token": token}).encode(), method="POST")
        req.add_header("Authorization", basic_auth(client_id, client_secret))
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        return self._send(req)[:2]

    def api(self, method: str, realm_id: str, path: str, *, access_token: str, params: Optional[dict] = None,
            json_body=None, text_body: Optional[str] = None, raw_body: Optional[bytes] = None,
            content_type: Optional[str] = None):
        query = {"minorversion": MINOR_VERSION, **(params or {})}  # the service sends it too; never twice
        url = f"{self.api_base}/company/{urllib.parse.quote(realm_id)}/{path.lstrip('/')}?" + urllib.parse.urlencode(query)
        data, ctype = None, None
        if json_body is not None:
            data, ctype = json.dumps(json_body).encode("utf-8"), "application/json"
        elif text_body is not None:
            data, ctype = text_body.encode("utf-8"), "application/text"
        elif raw_body is not None:
            data, ctype = raw_body, content_type
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Accept", "application/json")
        if ctype:
            req.add_header("Content-Type", ctype)
        return self._send(req)


# ====================================================================================================== the fake
def _fault(message, code="2020", detail=""):
    return {"Fault": {"Error": [{"Message": message, "Detail": detail or message, "code": str(code)}],
                      "type": "ValidationFault"}, "time": "2026-10-25T12:00:00.000-07:00"}


class FakeQuickBooksOnline:
    """An in-memory QuickBooks Online company for tests and the release walk. Synthetic data only."""

    def __init__(self, realm_id: str = "9341455555555555", company_name: str = "Brayman Construction (sandbox)"):
        self.realm_id = realm_id
        self.company_name = company_name
        self.client_id = "fake-client-id"
        self.client_secret = "fake-client-secret"
        self.entities = {k: {} for k in ("Vendor", "Customer", "Account", "TaxCode", "Class", "Purchase", "Bill",
                                         "Attachable")}
        self.requests_seen = {}  # requestid -> (status, payload): Intuit replays the first answer
        self.codes = {}  # authorization code -> realm
        self.access_tokens = set()
        self.refresh_tokens = set()
        self.revoked = []
        self.calls = []
        self.uploads = []
        self._next = 100
        self.fail_http = []  # status codes (or "network") answered before doing anything
        self.lose_reply_after_write = 0  # this many writes succeed but the caller sees a network failure
        self.fail_refresh = False

    # ---------------------------------------------------------------- set-up helpers
    def _id(self):
        self._next += 1
        return str(self._next)

    def add(self, entity: str, **fields):
        row = {"Id": self._id(), "SyncToken": "0", "domain": "QBO", "sparse": False, **fields}
        self.entities[entity][row["Id"]] = row
        return row

    def seed_standard(self):
        """Accounts, tax codes and a class like a small Canadian contractor's sandbox company."""
        self.add("Account", Name="Job Materials", AccountType="Cost of Goods Sold", Active=True)
        self.add("Account", Name="Shop Supplies", AccountType="Expense", Active=True)
        self.add("Account", Name="Chequing", AccountType="Bank", Active=True)
        self.add("Account", Name="Company Visa", AccountType="Credit Card", Active=True)
        self.add("TaxCode", Name="HST ON", Description="HST Ontario 13%", Active=True)
        self.add("TaxCode", Name="Exempt", Description="Exempt", Active=True)
        self.add("Class", Name="Residential", Active=True)
        return self

    def issue_code(self) -> str:
        code = "code-" + secrets.token_hex(6)
        self.codes[code] = self.realm_id
        return code

    def by_name(self, entity, name):
        return next((r for r in self.entities[entity].values()
                     if r.get("Name") == name or r.get("DisplayName") == name), None)

    # ---------------------------------------------------------------- OAuth
    def _tokens(self):
        access, refresh = "at-" + secrets.token_hex(8), "rt-" + secrets.token_hex(8)
        self.access_tokens.add(access)
        self.refresh_tokens.add(refresh)
        return 200, {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "expires_in": 3600,
                     "x_refresh_token_expires_in": 8726400}

    def token(self, form, *, client_id, client_secret):
        self.calls.append(("TOKEN", form.get("grant_type")))
        if (client_id, client_secret) != (self.client_id, self.client_secret):
            return 401, {"error": "invalid_client"}
        if form.get("grant_type") == "authorization_code":
            if form.get("code") not in self.codes or not form.get("redirect_uri"):
                return 400, {"error": "invalid_grant"}
            del self.codes[form["code"]]
            return self._tokens()
        if form.get("grant_type") == "refresh_token":
            if self.fail_refresh or form.get("refresh_token") not in self.refresh_tokens:
                return 400, {"error": "invalid_grant"}
            self.refresh_tokens.discard(form["refresh_token"])
            return self._tokens()
        return 400, {"error": "unsupported_grant_type"}

    def revoke(self, token, *, client_id, client_secret):
        self.revoked.append(token)
        self.refresh_tokens.discard(token)
        self.access_tokens.discard(token)
        return 200, {}

    def expire_access_tokens(self):
        self.access_tokens.clear()

    # ---------------------------------------------------------------- the API
    def api(self, method, realm_id, path, *, access_token, params=None, json_body=None, text_body=None,
            raw_body=None, content_type=None):
        params = dict(params or {})
        self.calls.append((method, path, deepcopy(params), deepcopy(json_body), text_body))
        if self.fail_http:
            code = self.fail_http.pop(0)
            if code == "network":
                raise TransportError("QuickBooks Online could not be reached (fake network failure).")
            return code, {"Fault": {"Error": [{"Message": "Synthetic failure", "code": str(code)}],
                                    "type": "SystemFault"}}, "fake-tid"
        if access_token not in self.access_tokens:
            return 401, {"Fault": {"Error": [{"Message": "AuthenticationFailed", "code": "3200"}],
                                   "type": "AUTHENTICATION"}}, "fake-tid"
        if realm_id != self.realm_id:
            return 403, _fault("Wrong company", "403"), "fake-tid"
        rid = params.get("requestid")
        if rid and rid in self.requests_seen:
            status, payload = self.requests_seen[rid]
            return status, deepcopy(payload), "fake-tid"
        status, payload, wrote = self._route(method, path.strip("/"), json_body, text_body, raw_body, content_type)
        if rid and wrote:
            self.requests_seen[rid] = (status, deepcopy(payload))
        if wrote and status == 200 and self.lose_reply_after_write > 0:
            self.lose_reply_after_write -= 1
            raise TransportError("QuickBooks Online could not be reached (fake lost reply).")
        return status, payload, "fake-tid"

    def _route(self, method, path, body, text, raw, ctype):
        parts = path.split("/")
        if method == "GET" and parts[0] == "companyinfo":
            return 200, {"CompanyInfo": {"Id": "1", "CompanyName": self.company_name}}, False
        if method == "POST" and path == "query":
            return 200, {"QueryResponse": self._query(text or ""), "time": "2026-10-25"}, False
        if method == "GET" and len(parts) == 2 and parts[0] in ("purchase", "bill", "vendor", "customer"):
            entity = parts[0].capitalize()
            row = self.entities[entity].get(parts[1])
            if row is None:
                return 400, _fault("Object Not Found", "610", f"{entity} {parts[1]} not found"), False
            return 200, {entity: deepcopy(row)}, False
        if method == "POST" and path == "vendor":
            name = (body or {}).get("DisplayName", "").strip()
            if not name:
                return 400, _fault("Required param missing", "2020", "DisplayName"), False
            if self.by_name("Vendor", name):
                return 400, _fault("Duplicate Name Exists Error", "6240", name), False
            return 200, {"Vendor": self.add("Vendor", DisplayName=name, Active=True)}, True
        if method == "POST" and path == "customer":
            return self._customer(body or {})
        if method == "POST" and path == "purchase":
            return self._purchase(body or {})
        if method == "POST" and path == "upload":
            return self._upload(raw or b"", ctype or "")
        return 400, _fault("Unsupported operation", "500", path), False

    def _customer(self, body):
        """Customer create, or a sparse update (Id + SyncToken + sparse=true): only the fields sent change."""
        if body.get("Id"):
            row = self.entities["Customer"].get(str(body["Id"]))
            if row is None:
                return 400, _fault("Object Not Found", "610", f"Customer {body['Id']}"), False
            if str(body.get("SyncToken")) != row["SyncToken"]:
                return 400, _fault("Stale Object Error", "5010", "You and someone else are editing the same thing"), False
            name = body.get("DisplayName")
            if name and name != row.get("DisplayName") and self.by_name("Customer", name):
                return 400, _fault("Duplicate Name Exists Error", "6240", name), False
            for key, value in body.items():
                if key not in ("Id", "SyncToken", "sparse"):
                    row[key] = deepcopy(value)
            row["SyncToken"] = str(int(row["SyncToken"]) + 1)
            return 200, {"Customer": deepcopy(row), "time": "2026-10-25"}, True
        name = (body.get("DisplayName") or "").strip()
        if not name:
            return 400, _fault("Required param missing", "2020", "DisplayName"), False
        if self.by_name("Customer", name) or self.by_name("Vendor", name):
            return 400, _fault("Duplicate Name Exists Error", "6240", f"The name supplied already exists. : {name}"), False
        if body.get("Job") and (body.get("ParentRef") or {}).get("value") not in self.entities["Customer"]:
            return 400, _fault("Invalid Reference Id", "2500", "ParentRef"), False
        fields = deepcopy(body)
        fields.setdefault("Active", True)
        if body.get("Job"):
            parent = self.entities["Customer"][body["ParentRef"]["value"]]
            fields["FullyQualifiedName"] = f"{parent['DisplayName']}:{name}"
            fields["Level"] = int(parent.get("Level", 0)) + 1
        row = self.add("Customer", **fields)
        return 200, {"Customer": deepcopy(row), "time": "2026-10-25"}, True

    def _purchase(self, body):
        for field in ("PaymentType", "AccountRef", "Line"):
            if not body.get(field):
                return 400, _fault("Required param missing, need to supply the required value for the API", "2020",
                                   field), False
        for ref in [body["AccountRef"]] + [l["AccountBasedExpenseLineDetail"]["AccountRef"] for l in body["Line"]]:
            if ref.get("value") not in self.entities["Account"]:
                return 400, _fault("Invalid Reference Id", "2500", f"Account {ref.get('value')}"), False
        entity = body.get("EntityRef") or {}
        if entity and entity.get("value") not in self.entities["Vendor"]:
            return 400, _fault("Invalid Reference Id", "2500", f"Vendor {entity.get('value')}"), False
        lines_total = sum(float(l["Amount"]) for l in body["Line"])
        tax = float((body.get("TxnTaxDetail") or {}).get("TotalTax") or 0)
        row = self.add("Purchase", **deepcopy(body), TotalAmt=round(lines_total + tax, 2))
        return 200, {"Purchase": deepcopy(row), "time": "2026-10-25"}, True

    def _upload(self, raw, ctype):
        parts = parse_multipart(raw, ctype)
        if "file_metadata_01" not in parts or "file_content_01" not in parts:
            return 400, _fault("Upload needs file_metadata_01 and file_content_01", "2020"), False
        meta = json.loads(parts["file_metadata_01"][1].decode("utf-8"))
        headers, payload = parts["file_content_01"]
        data = base64.b64decode(payload) if headers.get("content-transfer-encoding") == "base64" else payload
        for ref in meta.get("AttachableRef") or []:
            entity = ref["EntityRef"]
            if entity["value"] not in self.entities.get(entity["type"], {}):
                return 200, {"AttachableResponse": [{"Fault": {"Error": [
                    {"Message": "Invalid Reference Id", "code": "2500"}]}}]}, True
        row = self.add("Attachable", FileName=meta.get("FileName"), ContentType=meta.get("ContentType"),
                       Size=len(data), AttachableRef=meta.get("AttachableRef"))
        self.uploads.append({"id": row["Id"], "bytes": data, "meta": meta})
        return 200, {"AttachableResponse": [{"Attachable": deepcopy(row)}], "time": "2026-10-25"}, True

    def attachments_for(self, entity_type, entity_id):
        return [u for u in self.uploads if any(r["EntityRef"] == {"type": entity_type, "value": entity_id}
                                                for r in u["meta"].get("AttachableRef") or [])]

    _WHERE = re.compile(r"(\w+(?:\.\w+)?)\s*(=|>=|<=|<|>)\s*'((?:[^'\\]|\\.)*)'")

    def _query(self, text):
        match = re.match(r"\s*select \* from (\w+)(?: where (.*?))?(?: (?:startposition|maxresults) .*)?\s*$", text,
                         re.I | re.S)
        if not match:
            return {}
        entity = match.group(1).capitalize()
        entity = {"Taxcode": "TaxCode"}.get(entity, entity)
        rows = list(self.entities.get(entity, {}).values())
        where = match.group(2) or ""
        if entity in ("Customer", "Vendor") and not re.search(r"Active\s+IN", where, re.I):
            rows = [r for r in rows if r.get("Active", True)]  # QuickBooks lists active names unless asked
        for field, op, value in self._WHERE.findall(where):
            value = value.replace("\\'", "'")

            def keep(row, field=field, op=op, value=value):
                current = row
                for part in field.split("."):
                    current = (current or {}).get(part) if isinstance(current, dict) else None
                current = "" if current is None else str(current)
                return {"=": current == value, ">=": current >= value, "<=": current <= value,
                        "<": current < value, ">": current > value}[op]
            rows = [r for r in rows if keep(r)]
        out = {"startPosition": 1, "maxResults": len(rows)}
        if rows:
            out[entity] = deepcopy(rows)
        return out
