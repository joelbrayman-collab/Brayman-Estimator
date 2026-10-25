"""The Magnificent Seven everyday operations (Joel, 25 Oct 2026) — automated acceptance. Synthetic data only.

Receipt capture → Project Receipts → Suzanne's Receipts Inbox → review → QuickBooks Online (an in-memory test
company with Intuit's request and response shapes; nothing reaches Intuit) → Confirmed → reconciliation; a repeated
receipt makes no second expense; a receipt matching an existing QuickBooks transaction is attached, not entered again;
ambiguous matches go to Suzanne; WHAT NEEDS MY ATTENTION? from real records (shown, opened, resolved, gone); Extra Work
→ the existing change order → customer approval; Need Materials → office approval → the existing supplier request,
quote and purchase order → the worker's status; Confirm Delivery Received / Short / Damaged → exception → resolution →
order status; Job Update prefilled from records; end-of-day reminders without duplicates; permissions and company
isolation; the company time zone; the audit history; and no duplicate labour or material cost.
"""

from __future__ import annotations

import io
import json
import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from flask import g

from app import create_app, db
from app.models.field_operations import (
    DailyJobSummary,
    DeliveryConfirmation,
    ExtraWorkReport,
    FieldMaterialRequest,
    FieldOperationEvent,
    FieldReceipt,
    OperationsReminder,
    QuickBooksOnlineConnection,
    QuickBooksOnlineEvent,
    QuickBooksOnlineTransfer,
)
from app.services.local_time import local_today
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.magnificent_seven_support import (
    PEOPLE,
    build,
    connect_fake_qbo,
    map_fake_accounts,
    receipt_jpeg,
)

pytestmark = pytest.mark.no_office_auth


class Person:
    """One signed-in person's browser (the test client), with the signed-in user looked up on every request."""

    def __init__(self, application, key):
        self.http = application.test_client()
        g.pop("_login_user", None)
        email, password, _name = PEOPLE[key]
        login_url = "/supplier/login" if key == "darcy" else "/login"
        response = self.http.post(login_url, data={"email": email, "password": password})
        assert response.status_code == 302, (key, response.get_data(as_text=True)[:300])

    def get(self, url, status=200):
        g.pop("_login_user", None)
        response = self.http.get(url)
        assert response.status_code == status, (url, response.status_code, response.get_data(as_text=True)[-1200:])
        return response.get_data(as_text=True)

    def post(self, url, data=None, status=302, **kw):
        g.pop("_login_user", None)
        response = self.http.post(url, data=data, **kw)
        assert response.status_code == status, (url, response.status_code, response.get_data(as_text=True)[-1200:])
        return response

    def flash_after(self, url, data=None, **kw):
        g.pop("_login_user", None)
        response = self.http.post(url, data=data, follow_redirects=True, **kw)
        return response.get_data(as_text=True)


@pytest.fixture()
def env(tmp_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "m7",
                              "WTF_CSRF_ENABLED": False, "DECK_TAKEOFF_ROOT": str(tmp_path / "deck"),
                              "BUILD_ORIGINAL_ROOT": str(tmp_path / "build")})
    context = application.app_context()
    context.push()
    db.create_all()
    facts = build(application)
    yield application, facts
    db.session.remove()
    db.drop_all()
    context.pop()


def _fresh(model, row_id):
    db.session.expire_all()
    return db.session.get(model, row_id)


def _capture_receipt(person, project_id, *, image=None, supplier="", amount="", note="", capture_uuid=None):
    """What field.js does: the capture (event + original photo), then registering the receipt."""
    capture_uuid = capture_uuid or str(uuid.uuid4())
    g.pop("_login_user", None)
    event = person.http.post(f"/api/v1/projects/{project_id}/field-events", json={"client_capture_uuid": capture_uuid})
    assert event.status_code in (200, 201), event.get_data(as_text=True)
    event_id = event.get_json()["id"]
    g.pop("_login_user", None)
    original = person.http.post(f"/api/v1/projects/{project_id}/field-events/{event_id}/originals", data={
        "kind": "image", "client_original_uuid": str(uuid.uuid4()),
        "file": (io.BytesIO(image or receipt_jpeg()), "receipt.jpg")}, content_type="multipart/form-data")
    assert original.status_code in (200, 201), original.get_data(as_text=True)
    g.pop("_login_user", None)
    registered = person.http.post("/field/receipts/register", json={
        "client_capture_uuid": capture_uuid, "supplier": supplier, "amount": amount, "note": note})
    return capture_uuid, registered


def _review(person, receipt_id, **values):
    data = {"action": "review", "vendor_name": "BMR Winchester (synthetic)",
            "receipt_date": local_today().isoformat(), "subtotal": "100.00", "tax_amount": "13.00", "total": "113.00"}
    data.update(values)
    return person.flash_after(f"/accounting/receipts/{receipt_id}", data)


def _connected(app, facts):
    ben = Person(app, "ben")
    connect_fake_qbo(ben.http, facts["fake"])
    map_fake_accounts(ben.http, facts["fake"])
    return ben


# ====================================================================================================== 1. receipts
def test_receipt_capture_to_inbox_review_quickbooks_confirmed_and_reconciliation(env):
    app, facts = env
    project, fake = facts["project"], facts["fake"]
    kevin = Person(app, "kevin")
    page = kevin.get(f"/field/receipt?project_id={project.id}")
    assert 'data-capture-kind="receipt"' in page and "Shop / Company Expense" in page
    assert f'value="{project.id}" selected' in page  # opened from the job: the job is chosen
    uid, registered = _capture_receipt(kevin, project.id, supplier="BMR", amount="113.00", note="Deck screws")
    assert registered.status_code == 201
    receipt = FieldReceipt.query.one()
    assert receipt.status == "NEW" and receipt.expense_scope == "PROJECT" and receipt.entered_amount == Decimal("113.00")
    assert receipt.image_original_id is not None and receipt.submitted_by_name == PEOPLE["kevin"][2]
    # The worker sees it saved and can open it again.
    assert "Sent to the office" in kevin.get("/field/receipt")
    assert "Receipt R-" in kevin.get(f"/field/receipts/{receipt.id}")
    # Project Hub Receipts and the inbox (Suzanne: office with accounting access).
    ben = _connected(app, facts)
    hub = ben.get(f"/projects/{project.id}")
    assert 'id="hub-receipts"' in hub and f'data-hub-receipt="{receipt.id}"' in hub
    suzanne = Person(app, "suzanne")
    inbox = suzanne.get("/accounting/receipts?status=NEW")
    assert f'data-receipt="{receipt.id}"' in inbox
    detail = suzanne.get(f"/accounting/receipts/{receipt.id}")
    assert "Original receipt" in detail and "data-open-original" in detail
    # Approve is refused until the review is saved; a wrong total is refused.
    assert "Before approving" in suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "approve"})
    assert "is not the total" in _review(suzanne, receipt.id, total="120.00")
    _review(suzanne, receipt.id)
    assert _fresh(FieldReceipt, receipt.id).status == "REVIEWED"
    out = suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "approve"})
    assert "In QuickBooks: entered as a new expense" in out
    receipt = _fresh(FieldReceipt, receipt.id)
    transfer = receipt.qbo_transfer
    assert receipt.status == "SYNCED" and transfer.status == "CONFIRMED" and transfer.operation == "CREATE_PURCHASE"
    purchase = fake.entities["Purchase"][transfer.qbo_txn_id]
    assert purchase["EntityRef"]["value"] == fake.by_name("Vendor", "BMR Winchester (synthetic)")["Id"]
    assert purchase["TxnDate"] == local_today().isoformat() and purchase["TotalAmt"] == 113.0
    assert purchase["TxnTaxDetail"]["TotalTax"] == 13.0 and purchase["PaymentType"] == "CreditCard"
    line = purchase["Line"][0]
    assert line["Amount"] == 100.0 and line["AccountBasedExpenseLineDetail"]["CustomerRef"]["value"] == \
        fake.by_name("Customer", "BC-2026-014 Harbour Lane Pool Deck (synthetic)")["Id"]
    assert f"[CT-R{receipt.id}]" in purchase["PrivateNote"]
    # The original image went up as an Attachable linked to the expense, byte for byte.
    attachments = fake.attachments_for("Purchase", transfer.qbo_txn_id)
    assert len(attachments) == 1 and attachments[0]["id"] == transfer.qbo_attachable_id
    from app.services.build import open_original_file

    assert attachments[0]["bytes"] == open_original_file(receipt.image).read_bytes()
    # The create carried the stable sync id as Intuit's requestid.
    creates = [c for c in fake.calls if c[0] == "POST" and c[1] == "purchase"]
    assert len(creates) == 1 and creates[0][2]["requestid"] == transfer.sync_id and len(transfer.sync_id) <= 50
    assert creates[0][2]["minorversion"] == "75"
    # Reconciliation lists it with both QuickBooks ids; the worker sees "In QuickBooks".
    rec = suzanne.get("/accounting/quickbooks-online/reconciliation")
    assert f'data-reconciled="{receipt.id}"' in rec and transfer.qbo_txn_id in rec and transfer.qbo_attachable_id in rec
    assert "In QuickBooks" in kevin.get("/field/receipt")
    # Audit history: submitted, reviewed, approved, confirmed — who and when.
    events = [e.event for e in FieldOperationEvent.query.filter_by(record_type="RECEIPT", record_id=receipt.id)]
    assert events[:3] == ["SUBMITTED", "REVIEWED", "APPROVED"] and "QBO_CONFIRMED" in events
    # A synced receipt cannot be changed here (QuickBooks is the accounting authority).
    assert "already in QuickBooks" in _review(suzanne, receipt.id, total="200.00", subtotal="187.00")


def test_a_repeated_receipt_never_makes_a_second_expense(env):
    app, facts = env
    project, fake = facts["project"], facts["fake"]
    kevin = Person(app, "kevin")
    uid, first = _capture_receipt(kevin, project.id)
    # The phone sends the same capture again (lost answer): the same receipt comes back.
    g.pop("_login_user", None)
    again = kevin.http.post("/field/receipts/register", json={"client_capture_uuid": uid})
    assert first.status_code == 201 and again.status_code == 200 and again.get_json()["id"] == first.get_json()["id"]
    assert FieldReceipt.query.count() == 1
    suzanne = _connected(app, facts)
    receipt = FieldReceipt.query.one()
    _review(suzanne, receipt.id)
    # QuickBooks made the expense but the answer was lost: Sent, not Synced.
    fake.lose_reply_after_write = 1
    suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "approve"})
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.qbo_transfer.status == "SENT" and receipt.status == "SYNC_FAILED"
    assert "not known whether this arrived" in receipt.attention_reason
    assert len(fake.entities["Purchase"]) == 1
    # Retry: the same requestid returns the first answer; still one expense, now confirmed with its image.
    suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "retry"})
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.status == "SYNCED" and len(fake.entities["Purchase"]) == 1 and len(fake.uploads) == 1
    # A second Retry or send changes nothing.
    assert "already confirmed" in suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "retry"})
    from app.services.quickbooks_online import send_waiting

    send_waiting(ORG)
    assert len(fake.entities["Purchase"]) == 1 and len(fake.uploads) == 1
    # A second photo of the same purchase (new receipt record) finds our own expense and only attaches.
    _uid2, _ = _capture_receipt(kevin, project.id)
    second = FieldReceipt.query.order_by(FieldReceipt.id.desc()).first()
    _review(suzanne, second.id)
    out = suzanne.flash_after(f"/accounting/receipts/{second.id}", {"action": "approve"})
    second = _fresh(FieldReceipt, second.id)
    assert second.status == "SYNCED" and second.qbo_transfer.operation == "ATTACH_EXISTING"
    assert len(fake.entities["Purchase"]) == 1 and "attached to the existing expense" in out


def test_a_receipt_for_an_existing_quickbooks_transaction_is_attached_not_entered_again(env):
    app, facts = env
    project, fake = facts["project"], facts["fake"]
    vendor = fake.by_name("Vendor", "Home Hardware Kemptville (synthetic)")
    existing = fake.add("Purchase", PaymentType="CreditCard", TxnDate=local_today().isoformat(), TotalAmt=56.5,
                        EntityRef={"value": vendor["Id"], "type": "Vendor", "name": vendor["DisplayName"]},
                        PrivateNote="Entered by hand last week (synthetic)")
    kevin = Person(app, "kevin")
    _capture_receipt(kevin, facts["company"].id, supplier="Home Hardware")
    receipt = FieldReceipt.query.one()
    assert receipt.expense_scope == "COMPANY"
    suzanne = _connected(app, facts)
    _review(suzanne, receipt.id, vendor_name="Home Hardware Kemptville (synthetic)", subtotal="50.00",
            tax_amount="6.50", total="56.50")
    out = suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "approve"})
    receipt = _fresh(FieldReceipt, receipt.id)
    t = receipt.qbo_transfer
    assert receipt.status == "SYNCED" and t.operation == "ATTACH_EXISTING" and t.qbo_txn_id == existing["Id"]
    assert len(fake.entities["Purchase"]) == 1 and fake.attachments_for("Purchase", existing["Id"])
    assert "attached to the existing expense" in out
    # A purchase order whose bill is in QuickBooks: the receipt goes on that bill.
    order = facts["order"]
    bill = fake.add("Bill", DocNumber=order.number, TxnDate=local_today().isoformat(), TotalAmt=1412.5,
                    VendorRef={"value": fake.by_name("Vendor", "BMR Winchester (synthetic)")["Id"]})
    _capture_receipt(kevin, project.id)
    by_po = FieldReceipt.query.order_by(FieldReceipt.id.desc()).first()
    _review(suzanne, by_po.id, purchase_order_id=str(order.id), subtotal="1250.00", tax_amount="162.50",
            total="1412.50")
    suzanne.flash_after(f"/accounting/receipts/{by_po.id}", {"action": "approve"})
    by_po = _fresh(FieldReceipt, by_po.id)
    assert by_po.qbo_transfer.qbo_txn_type == "Bill" and by_po.qbo_transfer.qbo_txn_id == bill["Id"]
    assert len(fake.entities["Purchase"]) == 1  # no expense made for a purchase already billed


def test_ambiguous_matches_and_unknown_vendors_go_to_suzanne(env):
    app, facts = env
    project, fake = facts["project"], facts["fake"]
    bmr = fake.by_name("Vendor", "BMR Winchester (synthetic)")
    for _ in range(2):
        fake.add("Purchase", PaymentType="Cash", TxnDate=local_today().isoformat(), TotalAmt=113.0,
                 EntityRef={"value": bmr["Id"], "type": "Vendor"})
    kevin = Person(app, "kevin")
    _capture_receipt(kevin, project.id)
    receipt = FieldReceipt.query.one()
    suzanne = _connected(app, facts)
    _review(suzanne, receipt.id)
    suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "approve"})
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.status == "NEEDS_ATTENTION" and receipt.qbo_transfer.status == "NEEDS_REVIEW"
    assert len(receipt.qbo_transfer.match_json["candidates"]) == 2 and len(fake.entities["Purchase"]) == 2
    page = suzanne.get(f"/accounting/receipts/{receipt.id}")
    assert "data-qbo-candidates" in page and "Attach to this one" in page
    # It is on Ben's list until handled.
    assert f"/accounting/receipts/{receipt.id}" in Person(app, "ben").get("/operations/attention")
    chosen = receipt.qbo_transfer.match_json["candidates"][1]
    suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "choose", "txn_type": "Purchase",
                                                               "txn_id": chosen["id"]})
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.status == "SYNCED" and receipt.qbo_transfer.qbo_txn_id == chosen["id"]
    assert len(fake.entities["Purchase"]) == 2
    assert f"/accounting/receipts/{receipt.id}" not in Person(app, "ben").get("/operations/attention")
    # Unknown vendor: never created unless switched on; Suzanne links the QuickBooks vendor and retries.
    _capture_receipt(kevin, project.id)
    unknown = FieldReceipt.query.order_by(FieldReceipt.id.desc()).first()
    _review(suzanne, unknown.id, vendor_name="Lumber Yard Nobody Knows (synthetic)", subtotal="10.00",
            tax_amount="1.30", total="11.30")
    suzanne.flash_after(f"/accounting/receipts/{unknown.id}", {"action": "approve"})
    unknown = _fresh(FieldReceipt, unknown.id)
    assert unknown.status == "NEEDS_ATTENTION" and "not a vendor in QuickBooks" in unknown.attention_reason
    assert fake.by_name("Vendor", "Lumber Yard Nobody Knows (synthetic)") is None
    assert "data-link-vendor" in suzanne.get(f"/accounting/receipts/{unknown.id}")
    suzanne.flash_after(f"/accounting/receipts/{unknown.id}", {"action": "link_vendor",
                                                               "qbo_name": "Home Hardware Kemptville (synthetic)"})
    suzanne.flash_after(f"/accounting/receipts/{unknown.id}", {"action": "retry"})
    assert _fresh(FieldReceipt, unknown.id).status == "SYNCED"


def test_failures_say_why_retry_works_and_nothing_is_called_synced_without_quickbooks(env):
    app, facts = env
    project, fake = facts["project"], facts["fake"]
    kevin = Person(app, "kevin")
    _capture_receipt(kevin, project.id)
    receipt = FieldReceipt.query.one()
    suzanne = Person(app, "suzanne")
    _review(suzanne, receipt.id)
    # Not connected: approved and waiting, never synced.
    out = suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "approve"})
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.status == "READY" and receipt.qbo_transfer.status == "PENDING" and "not connected" in out
    assert fake.calls == []
    # Connected but the accounts are not chosen: the transfer still refuses.
    ben = Person(app, "ben")
    connect_fake_qbo(ben.http, fake)
    from app.services.quickbooks_online import send_waiting

    send_waiting(ORG)
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.qbo_transfer.status == "PENDING" and "choose the expense account" in receipt.qbo_transfer.last_error
    assert not fake.entities["Purchase"]
    map_fake_accounts(ben.http, fake)
    # QuickBooks refuses (a validation fault): Sync Failed with QuickBooks' reason; Retry after it is fixed.
    fake.fail_http = [400]
    suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "retry"})
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.status == "SYNC_FAILED" and receipt.qbo_transfer.status == "FAILED"
    assert "QuickBooks" in receipt.attention_reason and "data-retry-transfer" in suzanne.get(f"/accounting/receipts/{receipt.id}")
    # The access token expired: refreshed (rotated refresh token kept encrypted), then sent.
    fake.expire_access_tokens()
    suzanne.flash_after(f"/accounting/receipts/{receipt.id}", {"action": "retry"})
    receipt = _fresh(FieldReceipt, receipt.id)
    assert receipt.status == "SYNCED"
    assert [c[1] for c in fake.calls if c[0] == "TOKEN"].count("refresh_token") >= 1
    events = [e.kind for e in QuickBooksOnlineEvent.query.filter_by(receipt_id=receipt.id)]
    assert "FAILED" in events and "CONFIRMED" in events


def test_tokens_are_encrypted_never_shown_and_the_oauth_state_is_checked(env):
    app, facts = env
    fake = facts["fake"]
    ben = Person(app, "ben")
    # A callback that was not started here is refused.
    out = ben.http.get(f"/accounting/quickbooks/callback?code={fake.issue_code()}&realmId={fake.realm_id}&state=forged",
                       follow_redirects=True).get_data(as_text=True)
    assert "was not started here" in out and QuickBooksOnlineConnection.query.count() == 0
    connect_fake_qbo(ben.http, fake)
    conn = QuickBooksOnlineConnection.query.one()
    assert conn.status == "CONNECTED" and conn.realm_id == fake.realm_id and conn.company_name
    stored = conn.refresh_token_encrypted + conn.access_token_encrypted
    for token in fake.refresh_tokens | fake.access_tokens:
        assert token not in stored
        assert token not in ben.get("/accounting/quickbooks-online")
    assert conn.refresh_token_encrypted.startswith("cbx1:")
    from app.services.secret_box import SecretBoxError, open_sealed

    assert open_sealed(conn.refresh_token_encrypted) in fake.refresh_tokens
    tampered = conn.refresh_token_encrypted[:-4] + ("AAAA" if not conn.refresh_token_encrypted.endswith("AAAA") else "BBBB")
    with pytest.raises(SecretBoxError):
        open_sealed(tampered)
    for event in QuickBooksOnlineEvent.query.all():
        for token in fake.refresh_tokens | fake.access_tokens:
            assert token not in (event.message + json.dumps(event.detail_json or {}))
    # Office staff may use the inbox but not connect or disconnect QuickBooks.
    suzanne = Person(app, "suzanne")
    assert "Only the owner or a System Administrator" in suzanne.get("/accounting/quickbooks-online")
    assert "Only the owner or a System Administrator" in suzanne.flash_after("/accounting/quickbooks-online",
                                                                             {"action": "disconnect"})
    ben.flash_after("/accounting/quickbooks-online", {"action": "disconnect"})
    conn = _fresh(QuickBooksOnlineConnection, conn.id)
    assert conn.status == "DISCONNECTED" and conn.refresh_token_encrypted is None and fake.revoked


def test_production_sync_is_off_unless_activated(env, monkeypatch):
    app, facts = env
    app.config.pop("QBO_TEST_TRANSPORT")
    from app.services import quickbooks_online as qbo

    for name in ("QBO_SYNC_ENABLED", "QBO_CLIENT_ID", "QBO_CLIENT_SECRET", "QBO_REDIRECT_URI", "QBO_ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)
    assert qbo.get_transport() is None and qbo.activation()["mode"] == "off"
    ben = Person(app, "ben")
    page = ben.get("/accounting/quickbooks-online")
    assert "Not switched on" in page and "QBO_SYNC_ENABLED=1: not set" in page and "data-qbo-connect>" not in page
    assert "not switched on" in ben.flash_after("/accounting/quickbooks-online/connect")
    # With every setting present it would build the real transport (no call is made here).
    for name, value in (("QBO_SYNC_ENABLED", "1"), ("QBO_CLIENT_ID", "id"), ("QBO_CLIENT_SECRET", "secret"),
                        ("QBO_REDIRECT_URI", "https://office.example.invalid/accounting/quickbooks/callback"),
                        ("QBO_ENVIRONMENT", "sandbox")):
        monkeypatch.setenv(name, value)
    transport = qbo.get_transport()
    assert transport is not None and "sandbox-quickbooks.api.intuit.com" in transport.api_base


def test_field_only_crew_never_see_the_inbox_other_receipts_or_quickbooks(env):
    app, facts = env
    kevin, liam = Person(app, "kevin"), Person(app, "liam")
    _capture_receipt(kevin, facts["project"].id, amount="113.00")
    receipt = FieldReceipt.query.one()
    for url in ("/accounting/receipts", f"/accounting/receipts/{receipt.id}", "/accounting/quickbooks-online",
                "/operations/attention", "/operations/material-requests"):
        g.pop("_login_user", None)
        response = liam.http.get(url)
        assert response.status_code == 302 and "/field/today" in response.headers["Location"], url
    g.pop("_login_user", None)
    assert liam.http.post(f"/accounting/receipts/{receipt.id}", data={"action": "approve"}).status_code == 403
    # Another crew member cannot open or claim Kevin's receipt.
    liam.get(f"/field/receipts/{receipt.id}", status=404)
    g.pop("_login_user", None)
    stolen = liam.http.post("/field/receipts/register", json={"client_capture_uuid": receipt.client_capture_uuid})
    assert stolen.status_code == 400
    # Liam is not booked on the job: he cannot file a receipt against it.
    assert facts["project"].name not in liam.get("/field/receipt")
    # Another company sees nothing.
    other = Person(app, "other")
    other.get(f"/accounting/receipts/{receipt.id}", status=404)
    assert f'data-receipt="{receipt.id}"' not in other.get("/accounting/receipts")


# ============================================================================================= 2. needs my attention
def test_needs_my_attention_lifecycle_from_real_records(env):
    app, facts = env
    ben = Person(app, "ben")
    home = ben.get("/")
    assert "WHAT NEEDS MY ATTENTION?" in home and "What do you need to do?" in home
    assert home.index("WHAT NEEDS MY ATTENTION?") < home.index("What do you need to do?")
    kevin = Person(app, "kevin")
    # Kevin enters time: an approval item appears with a one-click link to the time page for Kevin.
    kevin.post(f"/field/projects/{facts['project'].id}/time", data={
        "project_work_activity_id": str(facts["activity"].id), "hours": "7.5", "work_date": local_today().isoformat()})
    page = ben.get("/operations/attention")
    assert "time entry to approve (7.5 h)" in page and f"/time?status=SUBMITTED&amp;worker_user_id={facts['kevin'].id}" in page
    from app.models.time_entry import LabourTimeEntry

    entry = LabourTimeEntry.query.one()
    ben.post(f"/time/{entry.id}/approve")
    assert "time entry to approve" not in ben.get("/operations/attention")
    # Delivery shortage → exception → resolve → gone.
    order = facts["order"]
    kevin.post(f"/field/projects/{facts['project'].id}/deliveries/{order.id}", data={
        "outcome": "SHORT", "received_1": "30", "received_2": "60", "note": "10 boards missing"})
    row = DeliveryConfirmation.query.one()
    assert f"/operations/deliveries/{row.id}" in ben.get("/")
    ben.post(f"/operations/deliveries/{row.id}", data={"resolution": "REST_COMING", "note": "Darcy sends Friday"})
    assert f"/operations/deliveries/{row.id}" not in ben.get("/operations/attention")
    # Empty state when nothing is left (after the remaining items are handled).
    from app.services.needs_attention import assemble

    view = assemble(ORG, facts["ben"])
    assert all(i["href"] for i in view["items"]) and all(i["what"] and i["status"] for i in view["items"])


def test_the_attention_list_is_empty_and_hidden_where_it_should_be(env):
    app, facts = env
    from app.services.needs_attention import assemble

    # Field-only crew never get the list.
    assert assemble(ORG, facts["kevin"])["hidden"] is True
    other = Person(app, "other")
    home = other.get("/")
    assert "Nothing needs your attention right now." in home


# ====================================================================================================== 3. extra work
def test_extra_work_from_field_to_change_order_and_customer_approval(env):
    app, facts = env
    project = facts["project"]
    kevin = Person(app, "kevin")
    kevin.get(f"/field/projects/{project.id}/job-update")  # confirms the job in Field
    out = kevin.flash_after(f"/field/projects/{project.id}/extra-work", data={
        "description": "Customer asked for a second set of stairs to the yard", "requested_by": "Morgan Ellis",
        "work_date": local_today().isoformat(), "client_uuid": str(uuid.uuid4()),
        "photos": (io.BytesIO(receipt_jpeg((200, 210, 220))), "stairs.jpg")}, content_type="multipart/form-data")
    assert "Extra work recorded" in out
    report = ExtraWorkReport.query.one()
    assert report.requested_by == "Morgan Ellis" and report.field_event_id and report.activity.scope_origin == "EXTRA_WORK"
    # Field cannot price or approve anything.
    g.pop("_login_user", None)
    assert kevin.http.get(f"/project-controls/change-orders/new?extra_work_activity_id={report.activity_id}").status_code == 302
    ben = Person(app, "ben")
    assert f"/operations/extra-work/{report.id}" in ben.get("/operations/attention")
    ben.post(f"/operations/extra-work/{report.id}", data={"action": "ask", "question": "Same width as the main stairs?"})
    assert "Same width" in kevin.get("/field/extra-work/mine")
    kevin.post(f"/field/extra-work/{report.id}/answer", data={"answer": "Yes, 4 ft wide"})
    assert _fresh(ExtraWorkReport, report.id).status == "ANSWERED"
    page = ben.get(f"/operations/extra-work/{report.id}")
    assert "data-prepare-change-order" in page and "4 ft wide" in page
    # Prepare the existing change order with the extra work linked; nothing is billed until approved.
    created = ben.post(f"/project-controls/change-orders/new?project_id={project.id}&extra_work_activity_id="
                       f"{report.activity_id}", data={
                           "project_id": str(project.id), "title": "Second stairs to the yard",
                           "description": "Extra stairs as asked on site", "requested_by": "Morgan Ellis",
                           "requested_date": local_today().isoformat(), "markup_percent": "0", "tax_percent": "13",
                           "status": "Draft", "approved_internal_direct_cost": "850.00"})
    from app.project_controls.models import ChangeOrder

    co = ChangeOrder.query.one()
    assert _fresh(ExtraWorkReport, report.id).activity.change_order_id == co.id
    ben.get(f"/operations/extra-work/{report.id}")
    report = _fresh(ExtraWorkReport, report.id)
    assert report.status == "IN_CHANGE_ORDER"
    from app.services.extra_work_reports import outcome_label

    assert "waiting for the customer" in outcome_label(report)
    # Customer approval through the existing change-order status.
    co.status = "Approved"
    db.session.commit()
    assert "Approved by the customer" in outcome_label(_fresh(ExtraWorkReport, report.id))
    assert "Approved by the customer" in kevin.get("/field/requests")
    # The project's history keeps every step.
    events = [e.event for e in FieldOperationEvent.query.filter_by(record_type="EXTRA_WORK", record_id=report.id)]
    assert events[:3] == ["REPORTED", "QUESTION", "ANSWERED"] and "CHANGE_ORDER" in events


def test_declined_extra_work_is_never_charged_and_leaves_the_list(env):
    app, facts = env
    project = facts["project"]
    kevin = Person(app, "kevin")
    kevin.get(f"/field/projects/{project.id}/materials")
    kevin.post(f"/field/projects/{project.id}/extra-work", data={"description": "Move the gate (synthetic)"})
    report = ExtraWorkReport.query.one()
    ben = Person(app, "ben")
    ben.post(f"/operations/extra-work/{report.id}", data={"action": "decline", "note": "Customer changed their mind"})
    report = _fresh(ExtraWorkReport, report.id)
    assert report.status == "DECLINED" and report.activity.status == "INACTIVE"
    assert f"/operations/extra-work/{report.id}" not in ben.get("/operations/attention")
    from app.project_controls.models import ChangeOrder

    assert ChangeOrder.query.count() == 0


# ================================================================================================ 4. need materials
def test_material_request_to_supplier_quote_order_and_worker_status(env):
    app, facts = env
    project, account = facts["project"], facts["account"]
    from app.models.canonical_material import CanonicalMaterial

    material = CanonicalMaterial.query.filter_by(status="ACTIVE", canonical_uom="EA").order_by(CanonicalMaterial.id).first()
    kevin = Person(app, "kevin")
    form = {"canonical_material_id": str(material.id), "description": "", "quantity": "24", "unit": "EA",
            "needed_by": (local_today() + timedelta(days=2)).isoformat(), "note": "For the stairs",
            "client_request_uuid": str(uuid.uuid4())}
    assert "sent to the office" in kevin.flash_after(f"/field/projects/{project.id}/materials", form)
    assert "was already sent" in kevin.flash_after(f"/field/projects/{project.id}/materials", form)  # double tap
    row = FieldMaterialRequest.query.one()
    assert row.status == "SUBMITTED" and row.description == material.display_name
    assert "Sent to the office" in kevin.get("/field/requests")
    ben = Person(app, "ben")
    assert f"/operations/material-requests/{row.id}" in ben.get("/")
    ben.post(f"/operations/material-requests/{row.id}", data={"action": "approve", "approved_quantity": "30",
                                                              "approved_unit": "EA"})
    row = _fresh(FieldMaterialRequest, row.id)
    assert row.status == "APPROVED" and row.approved_quantity == Decimal("30") and row.quantity == Decimal("24")
    out = ben.flash_after(f"/operations/material-requests/{row.id}", {"action": "send", "account_id": str(account.id)})
    assert "sent to BMR Winchester (synthetic)" in out
    row = _fresh(FieldMaterialRequest, row.id)
    share = row.share
    assert row.status == "REQUESTED" and share.source_kind == "FIELD_REQUEST" and share.status == "SENT"
    assert share.shared_json["lines"][0]["qty"] == "30" and "Sent to the supplier" in kevin.get("/field/requests")
    # Sending again makes nothing new.
    assert "not approved yet (or was already sent)" in ben.flash_after(
        f"/operations/material-requests/{row.id}", {"action": "send", "account_id": str(account.id)})
    from app.models.supplier_portal import SupplierPurchaseOrder, SupplierRequestShare

    assert SupplierRequestShare.query.filter_by(source_kind="FIELD_REQUEST").count() == 1
    # Darcy prices it in the Supplier Hub; Ben records and approves the cost, then orders — the existing path.
    darcy = Person(app, "darcy")
    darcy.get(f"/supplier/{account.supplier_id}/requests/{share.id}")
    darcy.post(f"/supplier/{account.supplier_id}/requests/{share.id}/quote", data={
        "sku_01": "MAG7-SKU", "unit_cost_01": "4.00", "discount_01": "0", "bmr_contact": "Darcy",
        "response_date": local_today().isoformat(), "valid_until": (local_today() + timedelta(days=30)).isoformat(),
        "minutes_reported": "5"})
    share = _fresh(SupplierRequestShare, share.id)
    assert share.status == "RETURNED"
    assert "The supplier answered" in kevin.get("/field/requests")
    ben.post(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}/record", data={})
    from app.services.deck_takeoff import storage

    follow = next(r for r in storage.list_responses(ORG, project.id) if r.get("records_response") == share.response_ref)
    for result in follow["results"]:
        if result.get("recorded"):
            ben.post(f"/projects/{project.id}/deck-takeoff/responses/{share.response_ref}/approve",
                     data={"canonical_material_id": result["canonical_material_id"], "status": "APPROVED"})
    ben.post(f"/projects/{project.id}/supplier-requests/{share.id}/order",
             data={"delivery_date": (local_today() + timedelta(days=2)).isoformat(), "site_contact": "Kevin"})
    order = SupplierPurchaseOrder.query.filter_by(share_id=share.id).one()
    assert order.total == Decimal("120.00") and "Ordered" in kevin.get("/field/requests")
    # The worker never sees a price anywhere in Field.
    for url in ("/field/requests", f"/field/projects/{project.id}/materials", f"/field/projects/{project.id}/deliveries",
                f"/field/projects/{project.id}/deliveries/{order.id}"):
        assert "4.00" not in kevin.get(url) and "$" not in kevin.get(url), url


def test_declined_material_request_shows_the_reason_and_nothing_is_sent(env):
    app, facts = env
    project = facts["project"]
    kevin = Person(app, "kevin")
    kevin.post(f"/field/projects/{project.id}/materials", data={"description": "Pink paint (synthetic)",
                                                                "quantity": "2", "unit": "pails"})
    row = FieldMaterialRequest.query.one()
    ben = Person(app, "ben")
    assert "Say why" in ben.flash_after(f"/operations/material-requests/{row.id}", {"action": "decline"})
    ben.post(f"/operations/material-requests/{row.id}", data={"action": "decline", "decline_reason": "We have some"})
    assert "Declined: We have some" in kevin.get("/field/requests")
    from app.models.supplier_portal import SupplierRequestShare

    assert SupplierRequestShare.query.filter_by(source_kind="FIELD_REQUEST").count() == 0


# ===================================================================================================== 5. deliveries
def test_delivery_received_short_and_damaged_with_exception_resolution_and_order_status(env):
    app, facts = env
    project, order = facts["project"], facts["order"]
    lines_before = json.dumps(order.lines_json, sort_keys=True)
    kevin = Person(app, "kevin")
    page = kevin.get(f"/field/projects/{project.id}/deliveries")
    assert "PO-MAG7-1" in page and "$" not in page
    form_page = kevin.get(f"/field/projects/{project.id}/deliveries/{order.id}")
    assert "2x8 PT 12 ft" in form_page and "18.50" not in form_page and "1250" not in form_page
    assert "Choose Short or Damaged" in kevin.flash_after(f"/field/projects/{project.id}/deliveries/{order.id}", {
        "outcome": "RECEIVED", "received_1": "35"})
    assert "Add a short note" in kevin.flash_after(f"/field/projects/{project.id}/deliveries/{order.id}", {
        "outcome": "SHORT", "received_1": "35"})
    kevin.post(f"/field/projects/{project.id}/deliveries/{order.id}", data={
        "outcome": "SHORT", "received_1": "35", "received_2": "60", "note": "5 boards short",
        "photos": (io.BytesIO(receipt_jpeg()), "pile.jpg")}, content_type="multipart/form-data")
    short = DeliveryConfirmation.query.one()
    order = _fresh(type(order), order.id)
    assert short.exception_status == "OPEN" and order.status == "CONFIRMED"  # not complete while short
    assert json.dumps(order.lines_json, sort_keys=True) == lines_before  # the order itself never changes
    assert short.confirmed_by_name == PEOPLE["kevin"][2] and short.field_event_id
    from app.services.delivery_confirmations import order_state, outstanding

    assert [l["outstanding"] for l in outstanding(order)] == [Decimal("5")]
    ben = Person(app, "ben")
    ben.post(f"/operations/deliveries/{short.id}", data={"resolution": "REST_COMING", "note": "Friday"})
    # The rest arrives, one damaged: Damaged exception; the office accepts and closes with a note.
    kevin.post(f"/field/projects/{project.id}/deliveries/{order.id}", data={
        "outcome": "DAMAGED", "received_1": "5", "damaged_1": "1", "received_2": "0", "note": "1 board split"})
    damaged = DeliveryConfirmation.query.order_by(DeliveryConfirmation.id.desc()).first()
    assert damaged.outcome == "DAMAGED" and damaged.exception_status == "OPEN"
    assert order_state(_fresh(type(order), order.id)) == "Delivery problem — waiting for the office"
    assert "Say why the order is closed" in ben.flash_after(f"/operations/deliveries/{damaged.id}",
                                                            {"resolution": "ACCEPT_CLOSE"})
    ben.post(f"/operations/deliveries/{damaged.id}", data={"resolution": "ACCEPT_CLOSE", "note": "Credit agreed"})
    order = _fresh(type(order), order.id)
    assert order.status == "DELIVERED" and json.dumps(order.lines_json, sort_keys=True) == lines_before
    from app.services.supplier_hub import order_closure

    assert "Credit agreed" in (order_closure(order)["note"] or "")


def test_a_full_delivery_marks_the_order_delivered_through_the_existing_action(env):
    app, facts = env
    project, order = facts["project"], facts["order"]
    kevin = Person(app, "kevin")
    kevin.post(f"/field/projects/{project.id}/deliveries/{order.id}", data={"outcome": "RECEIVED"})
    order = _fresh(type(order), order.id)
    assert order.status == "DELIVERED" and DeliveryConfirmation.query.one().exception_status == "NONE"
    from app.models.supplier_portal import SupplierRequestEvent

    assert SupplierRequestEvent.query.filter_by(share_id=order.share_id, event_type="ORDER_DELIVERED").count() == 1
    assert "already closed" in kevin.flash_after(f"/field/projects/{project.id}/deliveries/{order.id}",
                                                 {"outcome": "RECEIVED"})


# ===================================================================================================== 6. job update
def test_job_update_is_prefilled_from_records_saved_to_history_and_problems_reach_ben(env):
    app, facts = env
    project = facts["project"]
    kevin = Person(app, "kevin")
    kevin.post(f"/field/projects/{project.id}/time", data={
        "project_work_activity_id": str(facts["activity"].id), "hours": "8", "work_date": local_today().isoformat()})
    _capture_receipt(kevin, project.id)  # a photo today
    from app.models.time_entry import LabourTimeEntry

    hours_before = LabourTimeEntry.query.count()
    page = kevin.get(f"/field/projects/{project.id}/job-update")
    assert "From CalibraytAI records" in page and "Deck framing" in page and PEOPLE["kevin"][2] in page
    assert "8 h (submitted)" in page and "Photos today: 1" in page and "PO-MAG7-1" in page
    assert "Answer at least one" in kevin.flash_after(f"/field/projects/{project.id}/job-update", {})
    out = kevin.flash_after(f"/field/projects/{project.id}/job-update", {
        "completed_text": "Framed the north side", "problems_text": "Rain stopped us at 2 pm", "needs_text": "Hangers"})
    assert "Job update saved" in out and "office&#39;s list" in out
    summary = DailyJobSummary.query.one()
    assert summary.problem_status == "OPEN" and summary.facts_json["time_total_hours"] == "8"
    assert LabourTimeEntry.query.count() == hours_before  # no time created
    ben = Person(app, "ben")
    assert f"/operations/job-updates/{summary.id}" in ben.get("/operations/attention")
    detail = ben.get(f"/operations/job-updates/{summary.id}")
    assert "From CalibraytAI records (verified)" in detail and "observations, not checked" in detail
    assert "Rain stopped us" in ben.get(f"/projects/{project.id}")
    ben.post(f"/operations/job-updates/{summary.id}", data={"note": "Moved framing to Monday"})
    assert f"/operations/job-updates/{summary.id}" not in ben.get("/operations/attention")
    # A second save the same day replaces the answers and keeps the first in the history.
    kevin.post(f"/field/projects/{project.id}/job-update", data={"completed_text": "Framed both sides"})
    summary = _fresh(DailyJobSummary, summary.id)
    assert summary.revision == 2 and DailyJobSummary.query.count() == 1
    assert any("Framed the north side" in (e.detail or "") for e in FieldOperationEvent.query.filter_by(
        record_type="JOB_UPDATE", record_id=summary.id))


# ======================================================================================================= 7. reminders
def _at(monkeypatch, hour, minute=0, day=None):
    from app.services import local_time

    day = day or local_today()
    local = datetime(day.year, day.month, day.day, hour, minute, tzinfo=local_time.company_timezone())
    from datetime import timezone

    stamp = local.astimezone(timezone.utc).replace(tzinfo=None)
    monkeypatch.setattr(local_time, "utc_now", lambda: stamp)


def _every_day():
    from app.models.field_operations import OperationsSettings

    db.session.add(OperationsSettings(organization_id=ORG, working_days="0,1,2,3,4,5,6"))
    db.session.commit()


def test_end_of_day_reminders_are_real_once_in_company_time_and_never_called_sent_without_the_provider(env, monkeypatch):
    app, facts = env
    from app.services.reminders import send_due

    today = local_today()
    _every_day()  # the synthetic company works every day, so the test runs the same on a weekend
    _at(monkeypatch, 15, 0)
    assert send_due()["not_due"] >= 1 and OperationsReminder.query.count() == 0  # before 16:30 Toronto
    _at(monkeypatch, 16, 45)
    summary = send_due()
    kevin_r = OperationsReminder.query.filter_by(user_id=facts["kevin"].id).one()
    keys = [i["key"] for i in kevin_r.items_json]
    assert "time" in keys and any(k.startswith("update-") for k in keys)
    assert kevin_r.sms_status == "NOT_REQUESTED"
    ben_r = OperationsReminder.query.filter_by(user_id=facts["ben"].id).one()
    assert ben_r.audience == "OWNER"
    # Running again (cron every 15 minutes, or twice at once) makes nothing new.
    again = send_due()
    assert again["already"] >= 2 and OperationsReminder.query.count() == summary["crew"] + summary["owner"]
    # In the app: Field Today lists what is still outstanding; done items drop off; texting is off.
    kevin = Person(app, "kevin")
    today_page = kevin.get("/field/today")
    assert "Before you finish today" in today_page and "Texts not switched on" in today_page
    kevin.post(f"/field/projects/{facts['project'].id}/time", data={
        "project_work_activity_id": str(facts["activity"].id), "hours": "8", "work_date": today.isoformat()})
    kevin.post(f"/field/projects/{facts['project'].id}/job-update", data={"completed_text": "Done"})
    assert "Before you finish today" not in kevin.get("/field/today")
    # Reminder texts: chosen and agreed, but texting is not switched on → "not switched on", never "sent".
    from app.services.text_messages import save_contact

    save_contact(facts["liam"], mobile_phone="613-555-0142", opt_in=True, organization_id=ORG)
    liam = Person(app, "liam")
    liam.post("/field/reminders/preference", data={"sms": "1"})
    from app.services.reminders import _make, _text

    row = _make(ORG, facts["liam"], "CREW", today, [{"key": "time", "text": "Enter your hours", "sms": "your hours",
                                                     "href": "/field/time"}])
    _text(row, facts["liam"], row.items_json)
    assert _fresh(OperationsReminder, row.id).sms_status == "NOT_SWITCHED_ON"
    # With the provider accepting (test transport), the text is recorded as sent, without any job details.
    sent = []
    app.config["TEXT_TRANSPORT"] = lambda phone, body: sent.append(body) or "SM-fake-1"
    db.session.delete(_fresh(OperationsReminder, row.id))
    db.session.commit()
    row = _make(ORG, facts["liam"], "CREW", today, [{"key": "time", "text": "Enter your hours", "sms": "your hours",
                                                     "href": "/field/time"}])
    _text(row, facts["liam"], row.items_json)
    assert _fresh(OperationsReminder, row.id).sms_status == "SENT" and len(sent) == 1
    assert "Harbour" not in sent[0] and "Morgan" not in sent[0] and "$" not in sent[0]


def test_reminders_respect_working_days_latest_time_and_settings(env, monkeypatch):
    app, facts = env
    from app.services.reminders import send_due, window

    _at(monkeypatch, 21, 30)  # after the latest time
    assert window(ORG)["open"] is False and send_due()["not_due"] >= 1
    ben = Person(app, "ben")
    day = local_today().weekday()
    ben.post("/operations/reminders", data={"action": "settings", "reminders_enabled": "1", "crew_reminders": "1",
                                            "owner_summary": "1", "reminder_time": "21:00", "latest_time": "22:00",
                                            "working_days": [str(day)]})
    assert window(ORG)["open"] is True
    suzanne = Person(app, "suzanne")
    assert "Only the owner or a System Administrator" in suzanne.flash_after("/operations/reminders", {
        "action": "settings", "reminder_time": "05:00", "latest_time": "06:00", "working_days": ["0"]})


# ================================================================================== Field quick actions, isolation
def test_field_today_has_the_seven_quick_actions_with_the_job_kept(env):
    app, facts = env
    kevin = Person(app, "kevin")
    page = kevin.get("/field/today")
    for key in ("hours", "receipt", "materials", "extra_work", "delivery", "job_update", "schedule"):
        assert f'data-quick-action="{key}"' in page, key
    labels = re.findall(r'data-quick-action="[a-z_]+">([^<]+)<', page)
    assert labels == ["My Hours", "Add Receipt", "Need Materials", "Extra Work", "Confirm Delivery", "Job Update",
                      "My Schedule"]
    # Kevin is booked on one job: choosing goes straight to it, and the job stays chosen.
    g.pop("_login_user", None)
    response = kevin.http.get("/field/choose/materials")
    assert response.status_code == 302 and f"/field/projects/{facts['project'].id}/materials" in response.headers["Location"]
    kevin.get(f"/field/projects/{facts['project'].id}/materials")
    page = kevin.get("/field/today")
    assert f'href="/field/projects/{facts["project"].id}/deliveries"' in page
    # A job he is not booked on is not his.
    g.pop("_login_user", None)
    assert kevin.http.get(f"/field/projects/{facts['second'].id}/materials").status_code == 302
    assert FieldMaterialRequest.query.count() == 0


def test_another_company_cannot_reach_any_of_it(env):
    app, facts = env
    kevin = Person(app, "kevin")
    _capture_receipt(kevin, facts["project"].id)
    kevin.post(f"/field/projects/{facts['project'].id}/materials", data={"description": "Nails", "quantity": "1",
                                                                         "unit": "PKG"})
    kevin.post(f"/field/projects/{facts['project'].id}/deliveries/{facts['order'].id}", data={
        "outcome": "SHORT", "received_1": "1", "received_2": "1", "note": "short"})
    other = Person(app, "other")
    other.get(f"/operations/material-requests/{FieldMaterialRequest.query.one().id}", status=404)
    other.get(f"/operations/deliveries/{DeliveryConfirmation.query.one().id}", status=404)
    page = other.get("/operations/attention")
    assert "Harbour Lane Pool Deck" not in page and "Nothing needs your attention right now." in page


def test_company_time_zone_decides_today_for_reminders_and_job_updates(env, monkeypatch):
    app, facts = env
    from app.services import local_time
    from app.services.daily_summaries import utc_bounds

    # 9 pm in Toronto is already tomorrow in UTC: the office's "today" is still today.
    _at(monkeypatch, 21, 0)
    assert local_time.local_today() == local_time.local_now().date()
    start, end = utc_bounds(local_time.local_today())
    assert (end - start) in (timedelta(hours=23), timedelta(hours=24), timedelta(hours=25))
    assert start.hour in (4, 5)  # Toronto midnight is 04:00 or 05:00 UTC


def test_no_duplicate_labour_or_material_cost(env):
    """A receipt, a material request, a delivery and a job update never add a cost or hours to the job."""
    app, facts = env
    from app.models.direct_cost_actual import ProjectDirectCostActual
    from app.models.time_entry import LabourTimeEntry

    kevin = Person(app, "kevin")
    project = facts["project"]
    _capture_receipt(kevin, project.id, amount="500")
    kevin.post(f"/field/projects/{project.id}/materials", data={"description": "Screws", "quantity": "3", "unit": "PKG"})
    kevin.post(f"/field/projects/{project.id}/deliveries/{facts['order'].id}", data={"outcome": "RECEIVED"})
    kevin.post(f"/field/projects/{project.id}/job-update", data={"completed_text": "Framing"})
    assert ProjectDirectCostActual.query.count() == 0 and LabourTimeEntry.query.count() == 0


def test_the_migration_adds_exactly_the_thirteen_tables(tmp_path):
    """m7s3r5q8b2c4 is the release's only migration: thirteen new tables, nothing else. Every existing table, its
    columns, indexes and rows are unchanged. Downgrade refuses while a new table holds a row."""
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    from app.models.field_operations import NEW_TABLES

    root = Path(__file__).resolve().parents[1]
    uri = f"sqlite:///{tmp_path}/m.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    ctx = application.app_context()
    ctx.push()
    cfg = Config(str(root / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["m7s3r5q8b2c4"]
    assert script.get_revision("m7s3r5q8b2c4").down_revision == "w2z9r4d7k1m6"
    command.upgrade(cfg, "w2z9r4d7k1m6")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO organizations (id, legal_name, display_name, currency, is_active, created_at, "
                             "updated_at) VALUES ('ORG-M', 'M', 'M', 'CAD', 1, '2026-10-25', '2026-10-25')"))
        conn.execute(sa.text("INSERT INTO clients (id, name, organization_id, created_at) "
                             "VALUES (3, 'Synthetic Client', 'ORG-M', '2026-10-25')"))
    inspector = sa.inspect(engine)
    before = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
              for t in inspector.get_table_names()}
    before_indexes = {t: sorted(i["name"] for i in inspector.get_indexes(t)) for t in before}
    with engine.connect() as conn:
        rows = {t: conn.execute(sa.text(f'SELECT * FROM "{t}" ORDER BY rowid')).fetchall() for t in before
                if t != "alembic_version"}
    engine.dispose()
    command.upgrade(cfg, "m7s3r5q8b2c4")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    after = {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)]
             for t in inspector.get_table_names()}
    assert set(after) - set(before) == set(NEW_TABLES) and len(NEW_TABLES) == 13
    for table in before:
        assert after[table] == before[table], table
        assert sorted(i["name"] for i in inspector.get_indexes(table)) == before_indexes[table], table
    for table in NEW_TABLES:
        assert {c["name"] for c in inspector.get_columns(table)} == set(db.metadata.tables[table].columns.keys())
        with engine.connect() as conn:
            assert conn.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar() == 0
    with engine.connect() as conn:
        for table, kept in rows.items():
            assert conn.execute(sa.text(f'SELECT * FROM "{table}" ORDER BY rowid')).fetchall() == kept, table
    with engine.begin() as conn:
        conn.execute(sa.text("INSERT INTO operations_settings (organization_id, reminders_enabled, crew_reminders, "
                             "owner_summary, reminder_time, latest_time, working_days, updated_at) VALUES "
                             "('ORG-M', 1, 1, 1, '16:30', '20:00', '0,1,2,3,4', '2026-10-25')"))
    engine.dispose()
    with pytest.raises(RuntimeError, match="Downgrade refused"):
        command.downgrade(cfg, "w2z9r4d7k1m6")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("DELETE FROM operations_settings"))
    engine.dispose()
    command.downgrade(cfg, "w2z9r4d7k1m6")
    assert not set(NEW_TABLES) & set(sa.inspect(sa.create_engine(uri)).get_table_names())
    ctx.pop()
