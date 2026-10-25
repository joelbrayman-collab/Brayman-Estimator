"""Transports for the QuickBooks Time API (formerly TSheets). See docs/operations/quickbooks-time.md.

``HttpTransport`` is the only code that talks to Intuit. It is built only when QBT_SYNC_ENABLED=1 and
QBT_ACCESS_TOKEN are present in the environment (app/services/quickbooks_time.py get_transport). The token
is sent as ``Authorization: Bearer`` and is never logged, stored or shown.

``FakeQuickBooksTimeTransport`` is an in-memory stand-in with the documented request and response shapes
(POST/PUT/DELETE /timesheets with per-item ``_status_code``; GET with ``more`` paging). Tests and the release
walk use it; it can be told to fail in the ways the real API fails (HTTP 401/429/5xx, per-item 409/417, a lost
response after the timesheet was created). It is never selected from the environment.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from copy import deepcopy
from typing import Optional

DEFAULT_BASE_URL = "https://rest.tsheets.com/api/v1"
TIMEOUT_SECONDS = 20


class TransportError(RuntimeError):
    """The request may or may not have reached QuickBooks Time (network failure, timeout)."""


class HttpTransport:
    def __init__(self, token: str, base_url: str = DEFAULT_BASE_URL, timeout: int = TIMEOUT_SECONDS):
        if not token:
            raise ValueError("No QuickBooks Time access token.")
        self._token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def __repr__(self):  # never print the token
        return f"<HttpTransport {self.base_url}>"

    def request(self, method: str, path: str, *, params: Optional[dict] = None, body: Optional[dict] = None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self._token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (fixed https base URL)
                raw = resp.read()
                return resp.status, (json.loads(raw.decode("utf-8")) if raw else {})
        except urllib.error.HTTPError as exc:
            raw = exc.read() or b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except ValueError:
                payload = {}
            return exc.code, payload
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise TransportError(f"QuickBooks Time could not be reached ({exc.__class__.__name__}).") from None


class FakeQuickBooksTimeTransport:
    """In-memory QuickBooks Time account for tests and the release walk. Synthetic data only."""

    def __init__(self):
        self.users = {}
        self.jobcodes = {}
        self.timesheets = {}
        self.calls = []
        self._next_id = 9000
        self.fail_http = []  # queue of HTTP status codes to answer with before doing anything
        self.fail_items = []  # queue of per-item (_status_code, _status_message) for the next items written
        self.lose_response_after_write = 0  # this many writes succeed but the caller sees a network error

    # -- set-up helpers
    def add_user(self, first_name, last_name, *, user_id=None, payroll_id=""):
        uid = user_id or self._new_id()
        self.users[uid] = {"id": uid, "first_name": first_name, "last_name": last_name, "active": True,
                           "payroll_id": payroll_id}
        return uid

    def add_jobcode(self, name, *, jobcode_id=None, parent_id=0, jtype="regular"):
        jid = jobcode_id or self._new_id()
        self.jobcodes[jid] = {"id": jid, "name": name, "parent_id": parent_id, "type": jtype, "active": True}
        return jid

    def _new_id(self):
        self._next_id += 1
        return self._next_id

    # -- the API
    def request(self, method, path, *, params=None, body=None):
        self.calls.append((method, path, deepcopy(params), deepcopy(body)))
        if self.fail_http:
            code = self.fail_http.pop(0)
            if code == "network":
                raise TransportError("QuickBooks Time could not be reached (fake network failure).")
            return code, {"error": {"code": code, "message": "Synthetic failure"}}
        path = path.strip("/")
        if method == "GET" and path == "users":
            return 200, {"results": {"users": {str(k): v for k, v in self.users.items()}}, "more": False}
        if method == "GET" and path == "jobcodes":
            rows = dict(self.jobcodes)
            p = params or {}
            if p.get("ids"):
                wanted = {int(x) for x in str(p["ids"]).split(",") if x.strip().isdigit()}
                rows = {k: v for k, v in rows.items() if int(k) in wanted}
            if p.get("name"):
                rows = {k: v for k, v in rows.items() if v["name"] == p["name"]}
            if p.get("active") in ("true", "false"):
                rows = {k: v for k, v in rows.items() if bool(v.get("active")) == (p["active"] == "true")}
            elif not p.get("ids"):  # QuickBooks Time lists active job codes unless asked (active=both)
                if p.get("active") != "both":
                    rows = {k: v for k, v in rows.items() if v.get("active")}
            return 200, {"results": {"jobcodes": {str(k): v for k, v in rows.items()}}, "more": False}
        if method in ("POST", "PUT") and path == "jobcodes":
            return self._write_jobcodes(body, create=method == "POST")
        if method == "GET" and path == "timesheets":
            return 200, {"results": {"timesheets": {str(k): v for k, v in self._filter(params or {}).items()}},
                         "more": False}
        if method == "POST" and path == "timesheets":
            return self._write(body, create=True)
        if method == "PUT" and path == "timesheets":
            return self._write(body, create=False)
        if method == "DELETE" and path == "timesheets":
            out = {}
            for i, raw in enumerate(str((params or {}).get("ids", "")).split(","), 1):
                tid = int(raw) if raw.strip().isdigit() else None
                if tid in self.timesheets:
                    del self.timesheets[tid]
                    out[str(i)] = {"_status_code": 200, "_status_message": "OK", "id": tid}
                else:
                    out[str(i)] = {"_status_code": 404, "_status_message": "Not Found", "id": tid}
            return 200, {"results": {"timesheets": out}}
        return 404, {"error": {"code": 404, "message": "Not found"}}

    def _write_jobcodes(self, body, *, create):
        """POST/PUT /jobcodes with per-item _status_code, as documented (job codes are never deleted)."""
        items = (body or {}).get("data") or []
        out = {}
        for i, item in enumerate(items, 1):
            if self.fail_items:
                code, message = self.fail_items.pop(0)
                out[str(i)] = {"_status_code": code, "_status_message": message, "_status_extra": "Synthetic"}
                continue
            if create:
                name = (item.get("name") or "").strip()
                parent = int(item.get("parent_id") or 0)
                if not name:
                    out[str(i)] = {"_status_code": 417, "_status_message": "Expectation Failed",
                                   "_status_extra": "name is required"}
                    continue
                if any(j["name"] == name and int(j.get("parent_id") or 0) == parent for j in self.jobcodes.values()):
                    out[str(i)] = {"_status_code": 409, "_status_message": "Conflict",
                                   "_status_extra": "A jobcode with that name already exists"}
                    continue
                jid = self._new_id()
                row = {"id": jid, "name": name, "parent_id": parent, "type": item.get("type") or "regular",
                       "active": True, "billable": bool(item.get("billable")),
                       "assigned_to_all": bool(item.get("assigned_to_all")), "short_code": item.get("short_code", "")}
                self.jobcodes[jid] = row
                out[str(i)] = dict(row, _status_code=200, _status_message="Created")
            else:
                jid = int(item.get("id") or 0)
                if jid not in self.jobcodes:
                    out[str(i)] = {"_status_code": 404, "_status_message": "Not Found", "id": jid}
                    continue
                row = self.jobcodes[jid]
                for key in ("name", "active", "short_code"):
                    if key in item:
                        row[key] = item[key]
                out[str(i)] = dict(row, _status_code=200, _status_message="OK")
        if self.lose_response_after_write > 0:
            self.lose_response_after_write -= 1
            raise TransportError("QuickBooks Time could not be reached (fake: answer lost after the write).")
        return 200, {"results": {"jobcodes": out}}

    def _filter(self, params):
        rows = dict(self.timesheets)
        if params.get("ids"):
            wanted = {int(x) for x in str(params["ids"]).split(",") if x.strip().isdigit()}
            rows = {k: v for k, v in rows.items() if k in wanted}
        if params.get("user_ids"):
            wanted = {int(x) for x in str(params["user_ids"]).split(",") if x.strip().isdigit()}
            rows = {k: v for k, v in rows.items() if int(v["user_id"]) in wanted}
        if params.get("start_date"):
            rows = {k: v for k, v in rows.items() if v["date"] >= params["start_date"]}
        if params.get("end_date"):
            rows = {k: v for k, v in rows.items() if v["date"] <= params["end_date"]}
        return rows

    def _write(self, body, *, create):
        items = (body or {}).get("data") or []
        if len(items) > 50:
            return 413, {"error": {"code": 413, "message": "Request entity too large"}}
        out = {}
        for i, item in enumerate(items, 1):
            if self.fail_items:
                code, message = self.fail_items.pop(0)
                out[str(i)] = {"_status_code": code, "_status_message": message, "_status_extra": "Synthetic"}
                continue
            if create:
                missing = [k for k in ("user_id", "jobcode_id", "type", "date", "duration") if item.get(k) in (None, "")]
                if missing or int(item["user_id"]) not in self.users or int(item["jobcode_id"]) not in self.jobcodes:
                    out[str(i)] = {"_status_code": 417, "_status_message": "Expectation Failed",
                                   "_status_extra": "Missing or unknown " + ", ".join(missing or ["user or jobcode"])}
                    continue
                tid = self._new_id()
                row = {"id": tid, "user_id": int(item["user_id"]), "jobcode_id": int(item["jobcode_id"]),
                       "type": "manual", "date": item["date"], "duration": int(item["duration"]),
                       "notes": item.get("notes", ""), "locked": 0, "start": "", "end": ""}
                self.timesheets[tid] = row
                out[str(i)] = dict(row, _status_code=200, _status_message="Created")
            else:
                tid = int(item.get("id") or 0)
                if tid not in self.timesheets:
                    out[str(i)] = {"_status_code": 404, "_status_message": "Not Found", "id": tid}
                    continue
                row = self.timesheets[tid]
                for key in ("jobcode_id", "date", "duration", "notes"):
                    if key in item:
                        row[key] = int(item[key]) if key in ("jobcode_id", "duration") else item[key]
                out[str(i)] = dict(row, _status_code=200, _status_message="OK")
        if self.lose_response_after_write > 0:
            self.lose_response_after_write -= 1
            raise TransportError("QuickBooks Time could not be reached (fake: answer lost after the write).")
        return 200, {"results": {"timesheets": out}}
