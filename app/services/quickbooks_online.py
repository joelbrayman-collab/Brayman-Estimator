"""QuickBooks Online receipt synchronization (Joel, 25 Oct 2026: mandatory Magnificent Seven functionality).

QuickBooks Online is the accounting authority. An approved receipt (app/services/receipts.py) gets ONE transfer
with a stable sync id. Sending it:

1. never twice: the transfer is claimed with UPDATE ... WHERE status before any call; every create carries Intuit's
   ``requestid`` (the sync id), so a repeated request returns QuickBooks' first answer instead of a second record;
2. checks first: a transaction Suzanne named (Expense or Bill), the Bill of a linked purchase order (its BillNo is
   the PO number), and every Expense or Bill within three days for the same total. One clear match (same vendor,
   same date window, same total) → the receipt image is ATTACHED to it and no new expense is made. Our own earlier
   expense (its memo carries [CT-R<id>]) is recognised and adopted. Anything ambiguous → Needs review for Suzanne;
3. otherwise creates one Expense (Purchase, AccountBasedExpenseLineDetail) with the vendor, date, subtotal, tax,
   total, the job (CustomerRef) and the company's chosen accounts, then uploads the original image as an Attachable
   linked to it (AttachableRef → EntityRef);
4. says "Confirmed" (receipt: Synced) only when QuickBooks has answered with the transaction's Id and the
   attachment's Id. A lost answer is "Sent — not known yet"; Retry is safe because of 1 and 2.

Vendors are looked up by name and never made unless the company switched on "Create missing vendors". The job is
the QuickBooks customer named like CalibraytAI's job reference (or the one Suzanne linked). Accounts, payment type,
tax codes and class are the company's mapping; nothing is sent until the mapping is complete.

Switched off unless activated: QBO_SYNC_ENABLED=1, QBO_CLIENT_ID, QBO_CLIENT_SECRET, QBO_REDIRECT_URI,
QBO_ENVIRONMENT (sandbox | production) and QBO_TOKEN_KEY on the server (never in Git, the database or the logs),
then an owner or System Administrator presses Connect to QuickBooks and approves on Intuit's page. Tests use
QBO_TEST_TRANSPORT (an in-memory QuickBooks company); no test reaches Intuit.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from flask import current_app, has_app_context
from sqlalchemy import update

from app import db
from app.models import Project
from app.models.field_operations import (
    QBO_CONNECTED,
    QBO_DISCONNECTED,
    QBO_LINK_CUSTOMER,
    QBO_LINK_VENDOR,
    QBO_NEEDS_RECONNECT,
    QBO_NOT_CONNECTED,
    QBO_OP_ATTACH_EXISTING,
    QBO_OP_CREATE_PURCHASE,
    QBO_PAYMENT_TYPES,
    QBO_T_CONFIRMED,
    QBO_T_FAILED,
    QBO_T_NEEDS_REVIEW,
    QBO_T_PENDING,
    QBO_T_SENT,
    RECEIPT_NEEDS_ATTENTION,
    RECEIPT_READY,
    RECEIPT_SYNC_FAILED,
    RECEIPT_SYNCED,
    RECORD_RECEIPT,
    SCOPE_COMPANY,
    FieldReceipt,
    QuickBooksOnlineConnection,
    QuickBooksOnlineEvent,
    QuickBooksOnlineLink,
    QuickBooksOnlineTransfer,
)
from app.services import secret_box
from app.services.field_operations import actor_label, record
from app.services.quickbooks_online_transport import (
    AUTHORIZE_URL,
    MINOR_VERSION,
    SCOPE,
    HttpTransport,
    TransportError,
    multipart_upload,
)

ENV_ENABLED = "QBO_SYNC_ENABLED"
ENV_CLIENT_ID = "QBO_CLIENT_ID"
ENV_CLIENT_SECRET = "QBO_CLIENT_SECRET"
ENV_REDIRECT = "QBO_REDIRECT_URI"
ENV_ENVIRONMENT = "QBO_ENVIRONMENT"
MATCH_DAYS = 3
STATE_SESSION_KEY = "qbo_oauth_state"
UNKNOWN_OUTCOME = ("QuickBooks Online could not be reached, so it is not known whether this arrived. Retry is safe: "
                   "CalibraytAI sends the same request id and checks QuickBooks first, so nothing is entered twice.")
HTTP_MESSAGES = {
    401: "QuickBooks refused the connection (signed out or access removed). An owner or System Administrator "
         "presses Reconnect on Accounting → QuickBooks Online, then Retry.",
    403: "QuickBooks refused access to this company. Check that the connected user may enter expenses.",
    429: "QuickBooks asked CalibraytAI to slow down. Retry in a few minutes.",
}


class QuickBooksOnlineError(ValueError):
    pass


def _setting(name: str) -> str:
    value = ""
    if has_app_context():
        value = str(current_app.config.get(name) or "")
    return (value or os.environ.get(name, "")).strip()


def _test_transport():
    if has_app_context() and current_app.testing:
        return current_app.config.get("QBO_TEST_TRANSPORT")
    return None


def environment() -> str:
    value = _setting(ENV_ENVIRONMENT).lower()
    return value if value in ("sandbox", "production") else "sandbox"


def activation() -> dict:
    """What the server has for switching the connection on (names and yes/no only, never values)."""
    fake = _test_transport()
    redirect = _setting(ENV_REDIRECT)
    items = [
        (ENV_ENABLED + "=1", _setting(ENV_ENABLED) == "1"),
        (ENV_CLIENT_ID, bool(_setting(ENV_CLIENT_ID))),
        (ENV_CLIENT_SECRET, bool(_setting(ENV_CLIENT_SECRET))),
        (ENV_REDIRECT + " (https://…/accounting/quickbooks/callback)",
         redirect.startswith("https://") and redirect.endswith("/accounting/quickbooks/callback")),
        (ENV_ENVIRONMENT + " (sandbox or production)", _setting(ENV_ENVIRONMENT).lower() in ("sandbox", "production")),
        ("QBO_TOKEN_KEY (encrypts the stored tokens)", secret_box.key_present()),
    ]
    if fake is not None:
        return {"mode": "test", "ready": True, "items": items, "missing": []}
    missing = [name for name, ok in items if not ok]
    return {"mode": "live" if not missing else "off", "ready": not missing, "items": items, "missing": missing}


def get_transport():
    fake = _test_transport()
    if fake is not None:
        return fake
    if activation()["ready"]:
        return HttpTransport(environment())
    return None


def _client():
    fake = _test_transport()
    if fake is not None:
        return fake.client_id, fake.client_secret, _setting(ENV_REDIRECT) or "https://office.test/accounting/quickbooks/callback"
    return _setting(ENV_CLIENT_ID), _setting(ENV_CLIENT_SECRET), _setting(ENV_REDIRECT)


# ------------------------------------------------------------------------------------------------- connection
def connection(organization_id: str, *, create: bool = False) -> Optional[QuickBooksOnlineConnection]:
    row = QuickBooksOnlineConnection.query.filter_by(organization_id=organization_id).first()
    if row is None and create:
        row = QuickBooksOnlineConnection(organization_id=organization_id, environment=environment(),
                                         status=QBO_NOT_CONNECTED)
        db.session.add(row)
        db.session.flush()
    return row


def _event(org, kind, message, *, transfer=None, receipt_id=None, actor=None, detail=None):
    db.session.add(QuickBooksOnlineEvent(
        organization_id=org, transfer_id=getattr(transfer, "id", None),
        receipt_id=receipt_id if receipt_id is not None else getattr(transfer, "receipt_id", None),
        kind=kind[:30], message=message[:4000], detail_json=detail, actor_user_id=getattr(actor, "id", None),
        actor_name=actor_label(actor) if actor is not None else "CalibraytAI"))


def events(organization_id: str, *, receipt_id: Optional[int] = None, limit: int = 50) -> list:
    query = QuickBooksOnlineEvent.query.filter_by(organization_id=organization_id)
    if receipt_id is not None:
        query = query.filter_by(receipt_id=receipt_id)
    return query.order_by(QuickBooksOnlineEvent.id.desc()).limit(limit).all()


MAPPING_FIELDS = (("expense_account_id", "the expense account for receipts"),
                  ("payment_account_id", "the account the receipts were paid from"),
                  ("payment_type", "how the receipts were paid (cash, cheque or credit card)"),
                  ("tax_code_id", "the tax code for receipts with tax (HST)"),
                  ("no_tax_code_id", "the tax code for receipts without tax"))


def mapping_missing(conn: Optional[QuickBooksOnlineConnection]) -> list:
    if conn is None:
        return [label for _f, label in MAPPING_FIELDS]
    return [label for field, label in MAPPING_FIELDS if not getattr(conn, field)]


def is_connected(organization_id: str) -> bool:
    conn = connection(organization_id)
    return conn is not None and conn.status == QBO_CONNECTED and bool(conn.refresh_token_encrypted)


def can_send(organization_id: str) -> bool:
    return get_transport() is not None and is_connected(organization_id)


def connection_auto_send(organization_id: str) -> bool:
    conn = connection(organization_id)
    return conn is not None and bool(conn.auto_send)


def status(organization_id: str) -> dict:
    conn = connection(organization_id)
    act = activation()
    connected = is_connected(organization_id)
    missing = mapping_missing(conn)
    if connected and act["mode"] == "test":
        message = f"Connected to a TEST QuickBooks Online company ({conn.company_name or 'synthetic'})."
    elif connected:
        message = f"Connected to QuickBooks Online: {conn.company_name or conn.realm_id}."
    elif conn is not None and conn.status == QBO_NEEDS_RECONNECT:
        message = "QuickBooks Online needs to be reconnected (the sign-in expired or was removed)."
    elif not act["ready"]:
        message = ("Not switched on. Approved receipts wait here, nothing is sent to QuickBooks Online. Switching on "
                   "needs Joel's approval and the Intuit app settings listed below.")
    else:
        message = "Not connected. An owner or System Administrator presses Connect to QuickBooks."
    return {"connected": connected, "connection": conn, "activation": act, "message": message,
            "mapping_missing": missing, "mapping_complete": not missing, "environment": environment(),
            "can_connect": act["ready"]}


def _access_token(conn: QuickBooksOnlineConnection, transport, *, force: bool = False) -> str:
    now = datetime.utcnow()
    if not force and conn.access_token_encrypted and conn.access_token_expires_at and \
            conn.access_token_expires_at > now + timedelta(minutes=2):
        return secret_box.open_sealed(conn.access_token_encrypted)
    client_id, client_secret, _redirect = _client()
    refresh = secret_box.open_sealed(conn.refresh_token_encrypted)
    status_code, payload = transport.token({"grant_type": "refresh_token", "refresh_token": refresh},
                                           client_id=client_id, client_secret=client_secret)
    if status_code != 200 or not payload.get("access_token"):
        conn.status = QBO_NEEDS_RECONNECT
        conn.last_error = "QuickBooks refused to renew the connection. Reconnect on Accounting → QuickBooks Online."
        _event(conn.organization_id, "TOKEN_REFRESH_FAILED", conn.last_error, detail={"status": status_code})
        db.session.commit()
        raise QuickBooksOnlineError(conn.last_error)
    _store_tokens(conn, payload)
    db.session.commit()
    return payload["access_token"]


def _store_tokens(conn, payload):
    now = datetime.utcnow()
    conn.access_token_encrypted = secret_box.seal(payload["access_token"])
    conn.access_token_expires_at = now + timedelta(seconds=int(payload.get("expires_in") or 3600))
    if payload.get("refresh_token"):  # Intuit may rotate it; always keep the newest
        conn.refresh_token_encrypted = secret_box.seal(payload["refresh_token"])
        conn.refresh_token_expires_at = now + timedelta(seconds=int(payload.get("x_refresh_token_expires_in") or 0))


def _call(conn, transport, method, path, **kwargs):
    kwargs["params"] = {"minorversion": MINOR_VERSION, **(kwargs.get("params") or {})}
    token = _access_token(conn, transport)
    status_code, payload, _tid = transport.api(method, conn.realm_id, path, access_token=token, **kwargs)
    if status_code == 401:
        token = _access_token(conn, transport, force=True)
        status_code, payload, _tid = transport.api(method, conn.realm_id, path, access_token=token, **kwargs)
    return status_code, payload or {}


def _fault_text(payload) -> str:
    errors = ((payload or {}).get("Fault") or {}).get("Error") or []
    if not errors:
        return ""
    first = errors[0]
    detail = first.get("Detail") or ""
    message = first.get("Message") or "QuickBooks refused it"
    return f"QuickBooks: {message}" + (f" ({detail})" if detail and detail != message else "") + \
        (f" [code {first.get('code')}]" if first.get("code") else "")


def require_connect_authority(organization_id: str, user):
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    if not (is_instance_owner(user, organization_id) or is_system_administrator(user, organization_id)):
        raise QuickBooksOnlineError("Only the owner or a System Administrator connects or disconnects QuickBooks.")


def authorization_url(organization_id: str, user) -> tuple[str, str]:
    import urllib.parse

    require_connect_authority(organization_id, user)
    if get_transport() is None:
        raise QuickBooksOnlineError("QuickBooks Online is not switched on for this server yet.")
    client_id, _secret, redirect = _client()
    state = secrets.token_urlsafe(24)
    url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(
        {"client_id": client_id, "response_type": "code", "scope": SCOPE, "redirect_uri": redirect, "state": state})
    return url, state


def state_digest(state: str) -> str:
    return hashlib.sha256((state or "").encode()).hexdigest()


def complete_authorization(organization_id: str, user, *, code: str, realm_id: str) -> QuickBooksOnlineConnection:
    require_connect_authority(organization_id, user)
    transport = get_transport()
    if transport is None:
        raise QuickBooksOnlineError("QuickBooks Online is not switched on for this server yet.")
    if not code or not realm_id or not realm_id.isdigit():
        raise QuickBooksOnlineError("QuickBooks did not send the company back. Press Connect to QuickBooks again.")
    if not secret_box.key_present():
        raise QuickBooksOnlineError("The server has no QBO_TOKEN_KEY, so the connection cannot be kept safely.")
    client_id, client_secret, redirect = _client()
    status_code, payload = transport.token({"grant_type": "authorization_code", "code": code,
                                            "redirect_uri": redirect}, client_id=client_id,
                                           client_secret=client_secret)
    if status_code != 200 or not payload.get("refresh_token"):
        raise QuickBooksOnlineError("QuickBooks did not accept the sign-in. Press Connect to QuickBooks again.")
    conn = connection(organization_id, create=True)
    conn.environment = environment()
    conn.realm_id = realm_id
    _store_tokens(conn, payload)
    conn.status = QBO_CONNECTED
    conn.connected_by_name = actor_label(user)
    conn.connected_at = datetime.utcnow()
    conn.disconnected_at = None
    conn.last_error = None
    db.session.flush()
    info_status, info = _call(conn, transport, "GET", f"companyinfo/{realm_id}")
    if info_status == 200:
        conn.company_name = ((info.get("CompanyInfo") or {}).get("CompanyName") or "")[:200] or None
    _event(organization_id, "CONNECTED", f"Connected to QuickBooks Online company {conn.company_name or realm_id} "
           f"({conn.environment}).", actor=user, detail={"realm_id": realm_id})
    db.session.commit()
    return conn


def disconnect(organization_id: str, user) -> None:
    require_connect_authority(organization_id, user)
    conn = connection(organization_id)
    if conn is None or not conn.refresh_token_encrypted:
        raise QuickBooksOnlineError("QuickBooks Online is not connected.")
    transport = get_transport()
    if transport is not None:
        try:
            client_id, client_secret, _r = _client()
            transport.revoke(secret_box.open_sealed(conn.refresh_token_encrypted), client_id=client_id,
                             client_secret=client_secret)
        except (TransportError, secret_box.SecretBoxError):
            pass  # the stored tokens are removed below either way
    conn.refresh_token_encrypted = None
    conn.access_token_encrypted = None
    conn.access_token_expires_at = None
    conn.status = QBO_DISCONNECTED
    conn.disconnected_at = datetime.utcnow()
    _event(organization_id, "DISCONNECTED", "Disconnected from QuickBooks Online; the stored sign-in was removed.",
           actor=user)
    db.session.commit()


def _query(conn, transport, text) -> list:
    status_code, payload = _call(conn, transport, "POST", "query", text_body=text)
    if status_code != 200:
        raise QuickBooksOnlineError(_fault_text(payload) or HTTP_MESSAGES.get(status_code)
                                    or f"QuickBooks answered {status_code}.")
    response = payload.get("QueryResponse") or {}
    for key, value in response.items():
        if isinstance(value, list):
            return value
    return []


def _q(value: str) -> str:
    return (value or "").replace("\\", "\\\\").replace("'", "\\'")


def lists(organization_id: str) -> dict:
    """Accounts, tax codes and classes from the connected company, for the mapping form."""
    conn = connection(organization_id)
    transport = get_transport()
    if conn is None or transport is None or not is_connected(organization_id):
        return {"accounts": [], "tax_codes": [], "classes": []}
    try:
        return {"accounts": _query(conn, transport, "select * from Account maxresults 1000"),
                "tax_codes": _query(conn, transport, "select * from TaxCode"),
                "classes": _query(conn, transport, "select * from Class")}
    except (QuickBooksOnlineError, TransportError):
        return {"accounts": [], "tax_codes": [], "classes": []}


def save_mapping(organization_id: str, user, form) -> QuickBooksOnlineConnection:
    conn = connection(organization_id, create=True)
    known = lists(organization_id)

    def name_for(rows, value, key="Name"):
        return next((r.get(key) or r.get("FullyQualifiedName") for r in rows if str(r.get("Id")) == str(value)), None)

    for field, rows in (("expense_account_id", known["accounts"]), ("payment_account_id", known["accounts"]),
                        ("tax_code_id", known["tax_codes"]), ("no_tax_code_id", known["tax_codes"]),
                        ("class_id", known["classes"])):
        value = (form.get(field) or "").strip()[:40] or None
        if value and rows and name_for(rows, value) is None:
            raise QuickBooksOnlineError("Choose from the lists read from QuickBooks.")
        setattr(conn, field, value)
        setattr(conn, field.replace("_id", "_name"), name_for(rows, value) if value else None)
    payment_type = (form.get("payment_type") or "").strip() or None
    if payment_type and payment_type not in QBO_PAYMENT_TYPES:
        raise QuickBooksOnlineError("Choose how the receipts were paid.")
    conn.payment_type = payment_type
    conn.allow_vendor_create = form.get("allow_vendor_create") == "1"
    values = form.getlist("auto_send") if hasattr(form, "getlist") else [form.get("auto_send", "1")]
    conn.auto_send = "1" in values
    conn.settings_updated_by_name = actor_label(user)
    conn.settings_updated_at = datetime.utcnow()
    _event(organization_id, "MAPPING_SAVED", "QuickBooks mapping saved: expense "
           f"{conn.expense_account_name or '—'}, paid from {conn.payment_account_name or '—'} ({conn.payment_type or '—'}), "
           f"tax {conn.tax_code_name or '—'} / no tax {conn.no_tax_code_name or '—'}, class {conn.class_name or 'none'}, "
           f"create missing vendors {'yes' if conn.allow_vendor_create else 'no'}, send on approval "
           f"{'yes' if conn.auto_send else 'no'}.", actor=user)
    db.session.commit()
    return conn


# ------------------------------------------------------------------------------------------------- transfers
def sync_id_for(receipt: FieldReceipt) -> str:
    salt = hashlib.sha256(receipt.organization_id.encode()).hexdigest()[:8]
    return f"CT-RCPT-{salt}-{receipt.id}"  # stable, at most 50 characters (Intuit's requestid limit)


def receipt_mark(receipt: FieldReceipt) -> str:
    return f"[CT-R{receipt.id}]"


def ensure_transfer(receipt: FieldReceipt) -> QuickBooksOnlineTransfer:
    transfer = QuickBooksOnlineTransfer.query.filter_by(receipt_id=receipt.id).first()
    if transfer is None:
        transfer = QuickBooksOnlineTransfer(organization_id=receipt.organization_id, receipt_id=receipt.id,
                                            sync_id=sync_id_for(receipt), status=QBO_T_PENDING)
        db.session.add(transfer)
        db.session.flush()
        _event(receipt.organization_id, "QUEUED", "Approved receipt queued for QuickBooks Online.", transfer=transfer)
    elif transfer.status in (QBO_T_FAILED, QBO_T_NEEDS_REVIEW):
        transfer.status = QBO_T_PENDING
        _event(receipt.organization_id, "QUEUED", "Approved again; queued for QuickBooks Online.", transfer=transfer)
    return transfer


def reset_for_changes(receipt: FieldReceipt, actor) -> None:
    """The office changed the receipt: anything not confirmed waits for approval again (the sync id stays)."""
    transfer = QuickBooksOnlineTransfer.query.filter_by(receipt_id=receipt.id).first()
    if transfer is None or transfer.status == QBO_T_CONFIRMED:
        return
    if transfer.status != QBO_T_PENDING or transfer.match_json:
        transfer.status = QBO_T_PENDING
        transfer.match_json = None
        transfer.last_error = "Changed after review; approve again to send."
        _event(receipt.organization_id, "RESET", "Receipt changed; transfer waits for approval again.",
               transfer=transfer, actor=actor)


def _receipt_status_from(transfer, receipt):
    if transfer.status == QBO_T_CONFIRMED:
        receipt.status = RECEIPT_SYNCED
        receipt.attention_reason = None
    elif transfer.status in (QBO_T_FAILED, QBO_T_SENT):
        receipt.status = RECEIPT_SYNC_FAILED
        receipt.attention_reason = transfer.last_error
    elif transfer.status == QBO_T_NEEDS_REVIEW:
        receipt.status = RECEIPT_NEEDS_ATTENTION
        receipt.attention_reason = transfer.last_error
    elif transfer.status == QBO_T_PENDING and receipt.approved_at is not None:
        receipt.status = RECEIPT_READY


def outcome_message(receipt: FieldReceipt) -> str:
    transfer = QuickBooksOnlineTransfer.query.filter_by(receipt_id=receipt.id).first()
    if transfer is None:
        return ""
    if transfer.status == QBO_T_CONFIRMED:
        kind = "expense" if transfer.qbo_txn_type == "Purchase" else "bill"
        how = "attached to the existing" if transfer.operation == QBO_OP_ATTACH_EXISTING else "entered as a new"
        return f"In QuickBooks: {how} {kind} {transfer.qbo_txn_id}, with the receipt image (attachment {transfer.qbo_attachable_id})."
    if transfer.status == QBO_T_PENDING:
        return "Approved. " + (transfer.last_error or "Waiting to send to QuickBooks Online.")
    return transfer.last_error or transfer.status_label


def _claim(transfer, statuses) -> bool:
    now = datetime.utcnow()
    result = db.session.execute(
        update(QuickBooksOnlineTransfer)
        .where(QuickBooksOnlineTransfer.id == transfer.id, QuickBooksOnlineTransfer.status.in_(statuses))
        .values(status=QBO_T_SENT, attempts=QuickBooksOnlineTransfer.attempts + 1, sent_at=now, updated_at=now)
        .execution_options(synchronize_session=False))
    db.session.commit()
    db.session.refresh(transfer)
    return result.rowcount == 1


def _finish(transfer, receipt, status_value, message, *, actor=None, kind=None, detail=None, code=None):
    transfer.status = status_value
    transfer.last_error = message if status_value != QBO_T_CONFIRMED else None
    transfer.last_status_code = code
    if status_value == QBO_T_CONFIRMED:
        transfer.confirmed_at = datetime.utcnow()
    _receipt_status_from(transfer, receipt)
    _event(receipt.organization_id, kind or status_value, message, transfer=transfer, actor=actor, detail=detail)
    record(receipt.organization_id, RECORD_RECEIPT, receipt.id, f"QBO_{kind or status_value}"[:40], actor=actor,
           project_id=receipt.project_id, detail=message)
    db.session.commit()
    return transfer


def _link(org, kind, key) -> Optional[QuickBooksOnlineLink]:
    return QuickBooksOnlineLink.query.filter_by(organization_id=org, kind=kind, local_key=key).first()


def vendor_key(name: str) -> str:
    return " ".join((name or "").lower().split())[:200]


def customer_key(project_id: int) -> str:
    return f"project:{int(project_id)}"


def link_vendor(organization_id: str, actor, vendor_name: str, qbo_name: str) -> QuickBooksOnlineLink:
    conn, transport = _ready(organization_id)
    rows = _query(conn, transport, f"select * from Vendor where DisplayName = '{_q(qbo_name.strip())}'")
    if len(rows) != 1:
        raise QuickBooksOnlineError(f"QuickBooks has no vendor named exactly '{qbo_name.strip()}'.")
    return _save_link(organization_id, actor, QBO_LINK_VENDOR, vendor_key(vendor_name), rows[0])


def link_customer(organization_id: str, actor, project, qbo_name: str) -> QuickBooksOnlineLink:
    conn, transport = _ready(organization_id)
    rows = _query(conn, transport, f"select * from Customer where DisplayName = '{_q(qbo_name.strip())}'")
    if len(rows) != 1:
        raise QuickBooksOnlineError(f"QuickBooks has no customer or project named exactly '{qbo_name.strip()}'.")
    return _save_link(organization_id, actor, QBO_LINK_CUSTOMER, customer_key(project.id), rows[0])


def _save_link(org, actor, kind, key, row):
    link = _link(org, kind, key)
    if link is None:
        link = QuickBooksOnlineLink(organization_id=org, kind=kind, local_key=key, qbo_id=str(row["Id"]),
                                    linked_by_name=actor_label(actor))
        db.session.add(link)
    link.qbo_id = str(row["Id"])
    link.qbo_name = (row.get("DisplayName") or row.get("Name") or "")[:200]
    link.linked_by_name = actor_label(actor)
    link.linked_at = datetime.utcnow()
    _event(org, "LINKED", f"{kind.title()} '{key}' linked to QuickBooks {link.qbo_name} ({link.qbo_id}).", actor=actor)
    db.session.commit()
    return link


def _ready(organization_id):
    conn = connection(organization_id)
    transport = get_transport()
    if transport is None or conn is None or not is_connected(organization_id):
        raise QuickBooksOnlineError("QuickBooks Online is not connected.")
    return conn, transport


def _resolve_vendor(conn, transport, receipt, transfer, actor):
    link = _link(receipt.organization_id, QBO_LINK_VENDOR, vendor_key(receipt.vendor_name))
    if link is not None:
        return link.qbo_id, None
    rows = _query(conn, transport, f"select * from Vendor where DisplayName = '{_q(receipt.vendor_name)}'")
    if len(rows) == 1:
        _save_link(receipt.organization_id, actor, QBO_LINK_VENDOR, vendor_key(receipt.vendor_name), rows[0])
        return str(rows[0]["Id"]), None
    if len(rows) > 1:
        return None, f"More than one QuickBooks vendor is named '{receipt.vendor_name}'. Choose the vendor."
    if not conn.allow_vendor_create:
        return None, (f"'{receipt.vendor_name}' is not a vendor in QuickBooks. Add it in QuickBooks or type the "
                      "QuickBooks vendor name below, then Retry. (CalibraytAI does not create vendors unless the "
                      "company switched that on.)")
    status_code, payload = _call(conn, transport, "POST", "vendor", params={"requestid": transfer.sync_id + "-V"},
                                 json_body={"DisplayName": receipt.vendor_name})
    if status_code != 200 or "Vendor" not in payload:
        return None, _fault_text(payload) or f"QuickBooks did not create the vendor (answer {status_code})."
    _save_link(receipt.organization_id, actor, QBO_LINK_VENDOR, vendor_key(receipt.vendor_name), payload["Vendor"])
    _event(receipt.organization_id, "VENDOR_CREATED", f"Vendor '{receipt.vendor_name}' created in QuickBooks "
           f"({payload['Vendor']['Id']}).", transfer=transfer, actor=actor)
    return str(payload["Vendor"]["Id"]), None


def _resolve_customer(conn, transport, receipt, actor):
    if receipt.expense_scope == SCOPE_COMPANY:
        return None, None
    link = _link(receipt.organization_id, QBO_LINK_CUSTOMER, customer_key(receipt.project_id))
    if link is not None:
        return link.qbo_id, None
    from app.services.accounting import job_reference

    project = db.session.get(Project, receipt.project_id)
    name = job_reference(project)
    rows = _query(conn, transport, f"select * from Customer where DisplayName = '{_q(name)}'")
    if len(rows) == 1:
        _save_link(receipt.organization_id, actor, QBO_LINK_CUSTOMER, customer_key(project.id), rows[0])
        return str(rows[0]["Id"]), None
    return None, (f"QuickBooks has no customer or project named '{name}' for this job. Type the QuickBooks customer "
                  "or project name below, then Retry.")


def _candidates(conn, transport, receipt):
    start = (receipt.receipt_date - timedelta(days=MATCH_DAYS)).isoformat()
    end = (receipt.receipt_date + timedelta(days=MATCH_DAYS)).isoformat()
    out = []
    for entity in ("Purchase", "Bill"):
        for row in _query(conn, transport,
                          f"select * from {entity} where TxnDate >= '{start}' and TxnDate <= '{end}' maxresults 1000"):
            if Decimal(str(row.get("TotalAmt") or "0")).quantize(Decimal("0.01")) != receipt.total:
                continue
            ref = row.get("EntityRef") if entity == "Purchase" else row.get("VendorRef")
            out.append({"type": entity, "id": str(row["Id"]), "date": row.get("TxnDate"),
                        "total": str(row.get("TotalAmt")), "vendor_id": str((ref or {}).get("value") or ""),
                        "vendor": (ref or {}).get("name") or "", "doc": row.get("DocNumber") or "",
                        "ours": receipt_mark(receipt) in (row.get("PrivateNote") or "")})
    return out


def _purchase_body(conn, receipt, vendor_id, customer_id):
    from app.services.accounting import job_reference

    project = db.session.get(Project, receipt.project_id)
    tax = receipt.tax_amount or Decimal("0.00")
    where = "Shop / Company expense" if receipt.expense_scope == SCOPE_COMPANY else f"Job: {job_reference(project)}"
    detail = {"AccountRef": {"value": conn.expense_account_id},
              "TaxCodeRef": {"value": conn.tax_code_id if tax > 0 else conn.no_tax_code_id},
              "BillableStatus": "NotBillable"}
    if customer_id:
        detail["CustomerRef"] = {"value": customer_id}
    if conn.class_id:
        detail["ClassRef"] = {"value": conn.class_id}
    po = receipt.purchase_order
    body = {
        "PaymentType": conn.payment_type,
        "AccountRef": {"value": conn.payment_account_id},
        "EntityRef": {"value": vendor_id, "type": "Vendor"},
        "TxnDate": receipt.receipt_date.isoformat(),
        "GlobalTaxCalculation": "TaxExcluded",
        "TxnTaxDetail": {"TotalTax": float(tax)},
        "PrivateNote": (f"CalibraytAI receipt {receipt.number} {receipt_mark(receipt)} · {where}"
                        + (f" · PO {po.number}" if po is not None else ""))[:4000],
        "Line": [{"DetailType": "AccountBasedExpenseLineDetail", "Amount": float(receipt.subtotal),
                  "Description": f"Receipt {receipt.number}: {receipt.vendor_name} ({where})"[:4000],
                  "AccountBasedExpenseLineDetail": detail}],
    }
    return body


def _attach(conn, transport, transfer, receipt, actor):
    from app.services.build import BuildServiceError, open_original_file

    original = receipt.image
    try:
        path = open_original_file(original)
    except BuildServiceError:
        path = None
    if path is None:
        return _finish(transfer, receipt, QBO_T_FAILED, "The receipt's original image file is missing on the server.",
                       actor=actor)
    meta = {"AttachableRef": [{"EntityRef": {"type": transfer.qbo_txn_type, "value": transfer.qbo_txn_id},
                               "IncludeOnSend": False}],
            "FileName": original.original_filename or f"receipt-{receipt.number}.jpg",
            "ContentType": original.mime_type, "Note": f"CalibraytAI receipt {receipt.number}"}
    body, ctype = multipart_upload(meta, meta["FileName"], original.mime_type, path.read_bytes())
    try:
        status_code, payload = _call(conn, transport, "POST", "upload", params={"requestid": transfer.sync_id + "-A"},
                                     raw_body=body, content_type=ctype)
    except TransportError:
        return _finish(transfer, receipt, QBO_T_SENT, UNKNOWN_OUTCOME, actor=actor, kind="UNKNOWN")
    item = ((payload or {}).get("AttachableResponse") or [{}])[0]
    attachable = item.get("Attachable") or {}
    if status_code != 200 or not attachable.get("Id"):
        message = _fault_text(item) or _fault_text(payload) or HTTP_MESSAGES.get(status_code) or \
            f"QuickBooks did not take the receipt image (answer {status_code})."
        return _finish(transfer, receipt, QBO_T_FAILED, "The transaction is in QuickBooks but the image was not "
                       "attached: " + message + " Retry attaches it (no second expense).", actor=actor, code=status_code)
    transfer.qbo_attachable_id = str(attachable["Id"])
    how = "attached to the existing" if transfer.operation == QBO_OP_ATTACH_EXISTING else "entered as a new"
    kind = "expense" if transfer.qbo_txn_type == "Purchase" else "bill"
    return _finish(transfer, receipt, QBO_T_CONFIRMED,
                   f"Confirmed by QuickBooks: {how} {kind} {transfer.qbo_txn_id}, receipt image attachment "
                   f"{transfer.qbo_attachable_id}.", actor=actor, kind="CONFIRMED",
                   detail={"txn_type": transfer.qbo_txn_type, "txn_id": transfer.qbo_txn_id,
                           "attachable_id": transfer.qbo_attachable_id, "operation": transfer.operation})


def note_waiting(transfer: QuickBooksOnlineTransfer) -> None:
    """Say plainly why an approved receipt is waiting (it is never called sent or synced)."""
    org = transfer.organization_id
    if get_transport() is None:
        transfer.last_error = "Waiting: QuickBooks Online is not switched on for this server."
    elif not is_connected(org):
        transfer.last_error = "Waiting: QuickBooks Online is not connected."
    elif not connection_auto_send(org):
        transfer.last_error = "Waiting: press Send waiting receipts now on the QuickBooks Online page."
    db.session.commit()


def send_transfer(transfer: QuickBooksOnlineTransfer, *, actor=None, retry: bool = False):
    """Send one transfer. Every outcome is recorded; nothing here raises to the page."""
    receipt = db.session.get(FieldReceipt, transfer.receipt_id)
    org = transfer.organization_id
    if receipt.approved_at is None:
        return transfer
    conn = connection(org)
    transport = get_transport()
    if transport is None or conn is None or not is_connected(org):
        transfer.last_error = "Waiting: QuickBooks Online is not connected." if transport is not None else \
            "Waiting: QuickBooks Online is not switched on for this server."
        db.session.commit()
        return transfer
    missing = mapping_missing(conn)
    if missing:
        transfer.last_error = "Waiting: choose " + ", ".join(missing) + " (Accounting → QuickBooks Online)."
        db.session.commit()
        return transfer
    statuses = (QBO_T_PENDING, QBO_T_FAILED, QBO_T_SENT) if retry else (QBO_T_PENDING,)
    if not _claim(transfer, statuses):
        return transfer
    try:
        return _send_claimed(conn, transport, transfer, receipt, actor)
    except TransportError:
        db.session.rollback()
        transfer = db.session.get(QuickBooksOnlineTransfer, transfer.id)
        receipt = db.session.get(FieldReceipt, transfer.receipt_id)
        return _finish(transfer, receipt, QBO_T_SENT, UNKNOWN_OUTCOME, actor=actor, kind="UNKNOWN")
    except (QuickBooksOnlineError, secret_box.SecretBoxError) as exc:
        db.session.rollback()
        transfer = db.session.get(QuickBooksOnlineTransfer, transfer.id)
        receipt = db.session.get(FieldReceipt, transfer.receipt_id)
        return _finish(transfer, receipt, QBO_T_FAILED, str(exc), actor=actor)


def _needs_review(transfer, receipt, message, actor, candidates=None):
    transfer.match_json = {"candidates": candidates or [], "reason": message}
    return _finish(transfer, receipt, QBO_T_NEEDS_REVIEW, message, actor=actor, kind="NEEDS_REVIEW")


def _send_claimed(conn, transport, transfer, receipt, actor):
    if transfer.qbo_txn_id:  # the transaction is known (made earlier, or chosen): only the image is missing
        return _attach(conn, transport, transfer, receipt, actor)
    match = transfer.match_json or {}
    # 1. A transaction Suzanne named.
    chosen_type = match.get("chosen_type") or receipt.existing_qbo_txn_type
    chosen_id = match.get("chosen_id") or receipt.existing_qbo_txn_id
    if chosen_id:
        status_code, payload = _call(conn, transport, "GET", f"{chosen_type.lower()}/{chosen_id}")
        if status_code != 200 or chosen_type not in payload:
            return _finish(transfer, receipt, QBO_T_FAILED, f"QuickBooks has no {chosen_type} {chosen_id}. Check the "
                           "number (it is in the transaction's web address) and Retry.", actor=actor, code=status_code)
        transfer.operation, transfer.qbo_txn_type, transfer.qbo_txn_id = QBO_OP_ATTACH_EXISTING, chosen_type, chosen_id
        _event(receipt.organization_id, "MATCHED", f"Using the existing {chosen_type} {chosen_id} named by the office.",
               transfer=transfer, actor=actor)
        db.session.commit()
        return _attach(conn, transport, transfer, receipt, actor)
    # 2. The bill of the linked purchase order (its bill number is the PO number).
    if receipt.purchase_order_id and not match.get("create_anyway"):
        po = receipt.purchase_order
        bills = _query(conn, transport, f"select * from Bill where DocNumber = '{_q(po.number)}'")
        if len(bills) == 1:
            transfer.operation, transfer.qbo_txn_type, transfer.qbo_txn_id = \
                QBO_OP_ATTACH_EXISTING, "Bill", str(bills[0]["Id"])
            _event(receipt.organization_id, "MATCHED", f"Bill {po.number} for purchase order {po.number} is already in "
                   f"QuickBooks ({bills[0]['Id']}); the receipt is attached to it, no new expense.",
                   transfer=transfer, actor=actor)
            db.session.commit()
            return _attach(conn, transport, transfer, receipt, actor)
        if len(bills) > 1:
            return _needs_review(transfer, receipt, f"QuickBooks has {len(bills)} bills numbered {po.number}. Choose "
                                 "the one this receipt belongs to.", actor,
                                 [{"type": "Bill", "id": str(b["Id"]), "date": b.get("TxnDate"),
                                   "total": str(b.get("TotalAmt")), "vendor": (b.get("VendorRef") or {}).get("name", ""),
                                   "doc": b.get("DocNumber") or "", "ours": False} for b in bills])
    vendor_id, problem = _resolve_vendor(conn, transport, receipt, transfer, actor)
    if problem:
        return _needs_review(transfer, receipt, problem, actor)
    customer_id, problem = _resolve_customer(conn, transport, receipt, actor)
    if problem:
        return _needs_review(transfer, receipt, problem, actor)
    transfer.qbo_vendor_id, transfer.qbo_customer_id = vendor_id, customer_id
    # 3. Anything already in QuickBooks for the same total around the same date.
    if not match.get("create_anyway"):
        found = _candidates(conn, transport, receipt)
        ours = [c for c in found if c["ours"]]
        if ours:
            c = ours[0]
            transfer.operation, transfer.qbo_txn_type, transfer.qbo_txn_id = QBO_OP_CREATE_PURCHASE, c["type"], c["id"]
            _event(receipt.organization_id, "ADOPTED", f"QuickBooks already has this receipt's expense {c['id']} "
                   "(made by an earlier attempt); not entered again.", transfer=transfer, actor=actor)
            db.session.commit()
            return _attach(conn, transport, transfer, receipt, actor)
        same_vendor = [c for c in found if c["vendor_id"] == vendor_id]
        if len(found) == 1 and len(same_vendor) == 1:
            c = same_vendor[0]
            transfer.operation, transfer.qbo_txn_type, transfer.qbo_txn_id = QBO_OP_ATTACH_EXISTING, c["type"], c["id"]
            transfer.match_json = {"candidates": found, "reason": "One matching transaction"}
            _event(receipt.organization_id, "MATCHED", f"QuickBooks already has this purchase: {c['type']} {c['id']} "
                   f"({c['vendor']}, {c['date']}, ${c['total']}). The receipt is attached to it; no second expense.",
                   transfer=transfer, actor=actor)
            db.session.commit()
            return _attach(conn, transport, transfer, receipt, actor)
        if found:
            return _needs_review(transfer, receipt, f"QuickBooks already has {len(found)} transaction(s) for "
                                 f"${receipt.total} within {MATCH_DAYS} days. Choose the one this receipt belongs to, "
                                 "or Enter as a new expense.", actor, found)
    # 4. A new expense, once (requestid = sync id).
    body = _purchase_body(conn, receipt, vendor_id, customer_id)
    status_code, payload = _call(conn, transport, "POST", "purchase", params={"requestid": transfer.sync_id},
                                 json_body=body)
    purchase = (payload or {}).get("Purchase") or {}
    if status_code != 200 or not purchase.get("Id"):
        message = _fault_text(payload) or HTTP_MESSAGES.get(status_code) or f"QuickBooks answered {status_code}."
        return _finish(transfer, receipt, QBO_T_FAILED, message + " Correct it and Retry.", actor=actor,
                       code=status_code)
    transfer.operation, transfer.qbo_txn_type, transfer.qbo_txn_id = QBO_OP_CREATE_PURCHASE, "Purchase", str(purchase["Id"])
    _event(receipt.organization_id, "CREATED", f"Expense {purchase['Id']} entered in QuickBooks "
           f"(${purchase.get('TotalAmt')}).", transfer=transfer, actor=actor,
           detail={"purchase_id": purchase["Id"], "sync_id": transfer.sync_id})
    db.session.commit()
    return _attach(conn, transport, transfer, receipt, actor)


def choose_candidate(transfer: QuickBooksOnlineTransfer, actor, *, txn_type: str, txn_id: str):
    match = dict(transfer.match_json or {})
    if not any(c["type"] == txn_type and c["id"] == txn_id for c in match.get("candidates") or []):
        raise QuickBooksOnlineError("Choose one of the QuickBooks transactions listed.")
    match.update(chosen_type=txn_type, chosen_id=txn_id)
    transfer.match_json = match
    transfer.status = QBO_T_PENDING
    receipt = db.session.get(FieldReceipt, transfer.receipt_id)
    receipt.status = RECEIPT_READY
    receipt.attention_reason = None
    _event(transfer.organization_id, "CHOSEN", f"The office chose {txn_type} {txn_id}: the receipt is attached to it.",
           transfer=transfer, actor=actor)
    db.session.commit()
    return send_transfer(transfer, actor=actor)


def create_anyway(transfer: QuickBooksOnlineTransfer, actor, reason: str):
    text = " ".join((reason or "").split())
    if not text:
        raise QuickBooksOnlineError("Say why this receipt is a different purchase from the ones listed.")
    match = dict(transfer.match_json or {})
    match.update(create_anyway=True, create_anyway_by=actor_label(actor), create_anyway_reason=text[:500])
    transfer.match_json = match
    transfer.status = QBO_T_PENDING
    receipt = db.session.get(FieldReceipt, transfer.receipt_id)
    receipt.status = RECEIPT_READY
    receipt.attention_reason = None
    _event(transfer.organization_id, "CREATE_ANYWAY", f"The office confirmed a new expense: {text}",
           transfer=transfer, actor=actor)
    db.session.commit()
    return send_transfer(transfer, actor=actor)


def retry(transfer: QuickBooksOnlineTransfer, actor):
    if transfer.status == QBO_T_CONFIRMED:
        raise QuickBooksOnlineError("This receipt is already confirmed in QuickBooks.")
    receipt = db.session.get(FieldReceipt, transfer.receipt_id)
    if receipt.approved_at is None:
        raise QuickBooksOnlineError("Approve the receipt first.")
    if transfer.status == QBO_T_NEEDS_REVIEW:
        transfer.status = QBO_T_PENDING
        db.session.commit()
    _event(transfer.organization_id, "RETRY", "Retry pressed.", transfer=transfer, actor=actor)
    db.session.commit()
    return send_transfer(transfer, actor=actor, retry=True)


def send_waiting(organization_id: Optional[str] = None, actor=None) -> dict:
    """Send every pending approved receipt (CLI and the office's Send waiting button)."""
    query = QuickBooksOnlineTransfer.query.filter_by(status=QBO_T_PENDING)
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    summary = {"tried": 0, "confirmed": 0, "waiting": 0, "failed": 0, "review": 0}
    for transfer in query.order_by(QuickBooksOnlineTransfer.id).all():
        if not can_send(transfer.organization_id):
            summary["waiting"] += 1
            continue
        summary["tried"] += 1
        send_transfer(transfer, actor=actor)
        db.session.refresh(transfer)
        key = {QBO_T_CONFIRMED: "confirmed", QBO_T_NEEDS_REVIEW: "review", QBO_T_PENDING: "waiting"}.get(
            transfer.status, "failed")
        summary[key] += 1
    return summary


def transfer_counts(organization_id: str) -> dict:
    rows = db.session.query(QuickBooksOnlineTransfer.status, db.func.count(QuickBooksOnlineTransfer.id)).filter(
        QuickBooksOnlineTransfer.organization_id == organization_id).group_by(QuickBooksOnlineTransfer.status).all()
    out = {s: 0 for s in (QBO_T_PENDING, QBO_T_SENT, QBO_T_CONFIRMED, QBO_T_FAILED, QBO_T_NEEDS_REVIEW)}
    out.update({s: n for s, n in rows})
    return out


def reconciliation(organization_id: str) -> list:
    """Every confirmed receipt with its QuickBooks transaction and attachment ids, newest first."""
    return (QuickBooksOnlineTransfer.query.filter_by(organization_id=organization_id, status=QBO_T_CONFIRMED)
            .order_by(QuickBooksOnlineTransfer.confirmed_at.desc()).all())
