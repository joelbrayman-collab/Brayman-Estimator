"""QuickBooks workflow acceptance (Joel, 21 Oct 2026, V1 Onboarding). Synthetic data only.

customer → estimate → accepted proposal → invoices (deposit by percent, final remainder, change order)
→ export files → export again gives nothing new → reconciliation (one paid, one amount differs,
one missing, one unknown, one duplicate) → correction recorded → field crew refused everywhere.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.accounting import AccountingEvent, AccountingExportRecord, CustomerInvoice
from app.project_controls.services import add_change_order_item, create_change_order, update_change_order_status
from app.services import accounting as svc
from app.services import create_estimate
from app.services import quickbooks_online_connector as qbo
from app.services.access_domains import set_field_only
from app.services.estimate_builder import add_manual_line, create_section, update_version_pricing
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.proposals import create_proposal, create_proposal_template, update_proposal_status
from app.models.user import UserMembership
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.proposal_issue_support import make_issuable

pytestmark = pytest.mark.no_office_auth
ORG = DEFAULT_ORGANIZATION_ID
OFFICE = ("ben.office@example.invalid", "office-test-password", "Ben Office (synthetic)")
CREW = ("kev.crew@example.invalid", "crew-test-password", "Kev Crew (synthetic)")


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "test-secret-accounting", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def people(app):
    ben = ensure_office_user(email=OFFICE[0], password=OFFICE[1], display_name=OFFICE[2])
    membership = UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one()
    set_instance_owner(ORG, membership.id, ben.id)
    kev = ensure_office_user(email=CREW[0], password=CREW[1], display_name=CREW[2])
    set_field_only(UserMembership.query.filter_by(user_id=kev.id, organization_id=ORG).one(), True, ben)
    return {"ben": ben, "kev": kev}


@pytest.fixture
def job(app, people):
    customer = Client(name="Marsh Family (synthetic)", email="marsh@example.invalid", organization_id=ORG)
    db.session.add(customer)
    db.session.flush()
    project = Project(name="Marsh Deck (synthetic)", client_id=customer.id, organization_id=ORG, status="Active",
                      address="1 Test Lane, Ottawa ON")
    db.session.add(project)
    db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-QB-0001", title="Deck", organization_id=ORG)
    version = estimate.current_version
    section = create_section(version, name="Deck")
    add_manual_line(section, line_type="Custom", description="Deck framing", quantity=1, unit="ls",
                    unit_cost=10000, markup_percent=0)
    update_version_pricing(version, overhead_percent=10, profit_percent=10, tax_percent=13)
    make_issuable(version)
    template = create_proposal_template(organization_id=ORG, name="QB Template", company_name="x", is_default=True,
                                        is_active=True)
    proposal = create_proposal(estimate=estimate, version=version, template=template, title="Deck proposal",
                               status="Draft", valid_until=date(2026, 12, 31), organization_id=ORG)
    update_proposal_status(proposal, "Accepted")
    co = create_change_order(project=project, title="Add stairs", markup_percent=10, tax_percent=13)
    add_change_order_item(co, description="Stair stringers", quantity=1, unit="ls", unit_price="1000.00")
    update_change_order_status(co, "Approved")
    return {"customer": customer, "project": project, "proposal": proposal, "co": co}


def _rows(content: bytes):
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))


def test_quickbooks_acceptance(app, people, job):
    ben, proposal, project = people["ben"], job["proposal"], job["project"]
    before_tax = Decimal(proposal.total) - Decimal(proposal.tax_amount)
    assert before_tax == Decimal("11764.71")  # the company's pricing on 10,000 of cost, before HST
    q = lambda v: v.quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")  # noqa: E731

    deposit = svc.create_invoice(ORG, project, user=ben, proposal_id=proposal.id, kind="DEPOSIT", percent="30")
    assert deposit.number == f"INV-{date.today().year}-0001"
    assert deposit.subtotal == q(before_tax * Decimal("0.30")) == Decimal("3529.41")
    assert deposit.tax_amount == Decimal("458.82") and deposit.total == Decimal("3988.23")
    assert deposit.tax_code == "HST ON" and deposit.percent_of_contract == Decimal("30")
    with pytest.raises(svc.AccountingError, match="more than is left"):
        svc.create_invoice(ORG, project, user=ben, proposal_id=proposal.id, kind="PROGRESS", amount="9000")
    final = svc.create_invoice(ORG, project, user=ben, proposal_id=proposal.id, kind="FINAL")
    assert final.subtotal == before_tax - deposit.subtotal == Decimal("8235.30")  # what was left
    assert final.total == Decimal("9305.89")
    co_invoice = svc.create_invoice(ORG, project, user=ben, change_order_id=job["co"].id)
    assert co_invoice.subtotal == Decimal("1100.00")  # 1,000 + 10 % markup
    assert co_invoice.tax_amount == Decimal(job["co"].tax) == Decimal("143.00")
    with pytest.raises(svc.AccountingError, match="already invoiced"):
        svc.create_invoice(ORG, project, user=ben, change_order_id=job["co"].id)

    # Files for QuickBooks.
    _, customers, outcome = svc.export(ORG, "customers", user=ben)
    assert outcome == {"new": 1, "again": 0}
    assert _rows(customers)[0]["Name"] == "Marsh Family (synthetic)"
    name, content, outcome = svc.export(ORG, "invoices", user=ben)
    assert name.endswith(".csv") and outcome == {"new": 3, "again": 0}
    rows = _rows(content)
    assert [r["InvoiceNo"] for r in rows] == [deposit.number, final.number, co_invoice.number]
    assert rows[0]["ItemAmount"] == "3529.41" and rows[0]["ItemTaxCode"] == "HST ON"
    assert "Marsh Deck (synthetic)" in rows[0]["Memo"]  # the job travels with the invoice
    assert db.session.get(CustomerInvoice, deposit.id).status == "EXPORTED"

    # Exporting again gives nothing new: no duplicate in QuickBooks.
    with pytest.raises(svc.AccountingError, match="Nothing new"):
        svc.export(ORG, "invoices", user=ben)
    with pytest.raises(svc.AccountingError, match="Say why"):
        svc.export(ORG, "invoices", user=ben, include_exported=True)
    _, _, again = svc.export(ORG, "invoices", user=ben, include_exported=True, reason="QuickBooks import failed")
    assert again == {"new": 0, "again": 3}
    assert AccountingExportRecord.query.filter_by(record_type="INVOICE").count() == 3
    assert AccountingExportRecord.query.filter_by(record_key=deposit.number).one().export_count == 2

    # Reconciliation with QuickBooks' Invoice List.
    report = ("Invoice List\nMarsh test company\n\n"
              "Date,Transaction type,Num,Customer,Due date,Amount,Open balance\n"
              f"21/10/2026,Invoice,{deposit.number},Marsh Family (synthetic),20/11/2026,\"3,988.23\",0.00\n"
              f"21/10/2026,Invoice,{final.number},Marsh Family (synthetic),20/11/2026,9500.00,9500.00\n"
              "21/10/2026,Invoice,1043,Someone Else,20/11/2026,250.00,250.00\n"
              "21/10/2026,Invoice,1043,Someone Else,20/11/2026,250.00,250.00\n").encode()
    result = svc.reconcile(ORG, filename="InvoiceList.csv", content=report, user=ben)
    assert result["matched"] == [deposit.number] and result["paid"] == [deposit.number]
    assert result["differs"] == [{"number": final.number, "ours": "9305.89", "quickbooks": "9500.00"}]
    assert result["missing_in_quickbooks"] == [co_invoice.number]
    assert result["unknown_in_calibraytai"] == [{"number": "1043", "amount": "250.00"}]
    assert result["duplicates"] == [{"number": "1043", "count": 2}]
    db.session.expire_all()
    assert db.session.get(CustomerInvoice, deposit.id).status == "PAID"
    assert db.session.get(CustomerInvoice, deposit.id).amount_paid == Decimal("3988.23")

    svc.record_correction(ORG, db.session.get(CustomerInvoice, final.id), user=ben,
                          note="QuickBooks line had the wrong amount; corrected to 9,305.89 in QuickBooks.")
    kinds = [e.kind for e in AccountingEvent.query.order_by(AccountingEvent.id).all()]
    assert kinds.count("INVOICE") == 3 and kinds.count("EXPORT") == 3 and kinds[-2:] == ["IMPORT", "CORRECTION"]
    with pytest.raises(svc.AccountingError, match="Say what"):
        svc.record_correction(ORG, final, user=ben, note=" ")
    assert qbo.status()["connected"] is False
    with pytest.raises(qbo.QuickBooksNotConnected):
        qbo.push()


def test_bills_and_purchase_orders_files(app, people, job):
    from app.models.supplier_catalogue import Supplier

    preview = svc.preview(ORG, "bills")
    assert preview["rows"] == []  # no confirmed orders, no bills
    assert svc.preview(ORG, "suppliers")["rows"] == []
    assert Supplier is not None


def test_pages_office_and_crew(app, people, job):
    office = app.test_client()
    assert login_office_user(office, OFFICE[0], OFFICE[1]).status_code == 302
    for path in ("/accounting", "/accounting/invoices", f"/accounting/projects/{job['project'].id}/invoices/new",
                 "/accounting/export/customers", "/accounting/export/invoices", "/accounting/reconcile"):
        assert office.get(path).status_code == 200, path
    made = office.post(f"/accounting/projects/{job['project'].id}/invoices/new",
                       data={"proposal_id": job["proposal"].id, "kind": "DEPOSIT", "percent": "10"})
    assert made.status_code == 302
    inv = CustomerInvoice.query.one()
    page = office.get(f"/accounting/invoices/{inv.id}").get_data(as_text=True)
    assert "$1,176.47" in page and "$152.94" in page and "$1,329.41" in page
    download = office.post("/accounting/export/invoices")
    assert download.status_code == 200 and download.mimetype == "text/csv"
    assert inv.number in download.get_data(as_text=True)
    again = office.post("/accounting/export/invoices", follow_redirects=True)
    assert "Nothing new to export" in again.get_data(as_text=True)
    bad = office.post("/accounting/reconcile", data={"report": (io.BytesIO(b"a,b\n1,2\n"), "x.csv")},
                      content_type="multipart/form-data")
    assert "does not look like a QuickBooks invoice list" in bad.get_data(as_text=True)
    assert "Accounting" in office.get("/").get_data(as_text=True)

    from flask import g

    g.pop("_login_user", None)  # the tests share one app context; forget the office sign-in
    crew = app.test_client()
    assert login_office_user(crew, CREW[0], CREW[1]).status_code == 302
    for path in ("/accounting", "/accounting/invoices", f"/accounting/invoices/{inv.id}", "/accounting/reconcile"):
        g.pop("_login_user", None)
        response = crew.get(path)
        assert response.status_code in (302, 403), path
        if response.status_code == 302:
            assert response.headers["Location"].endswith("/field/today")
    assert crew.post("/accounting/export/invoices").status_code in (302, 403)
    assert crew.post(f"/accounting/invoices/{inv.id}/void", data={"reason": "x"}).status_code in (302, 403)
    db.session.expire_all()
    assert db.session.get(CustomerInvoice, inv.id).status != "VOID"


def test_other_company_cannot_see_invoice(app, people, job):
    from app.models import Organization

    inv = svc.create_invoice(ORG, job["project"], user=people["ben"], proposal_id=job["proposal"].id,
                             kind="DEPOSIT", percent="5")
    other = Organization(id="org-other-synthetic", legal_name="Other Co (synthetic)", display_name="Other Co (synthetic)", is_active=True)
    db.session.add(other)
    db.session.commit()
    with pytest.raises(svc.AccountingError):
        svc.record_correction("org-other-synthetic", inv, user=people["ben"], note="x")
    assert svc.invoices("org-other-synthetic") == []


# ------------------------------------------------------------------ migration qb7c2e9a4d1f


def test_the_v1_onboarding_revisions_each_add_empty_tables_and_keep_every_row(tmp_path):
    """pr6b3d8e0f1c → pa7c4e9f1d2b (people_access_events) → ob7c2e9a4d1f (organization_onboarding_steps)
    → qb7c2e9a4d1f (customer_invoices, accounting_export_records, accounting_events)."""
    import sqlalchemy as sa
    from alembic import command
    from alembic.script import ScriptDirectory

    from tests.test_supplier_po_cancel_delivered import _config, _rows as _db_rows, _seed

    steps = [("pa7c4e9f1d2b", {"people_access_events"}), ("ob7c2e9a4d1f", {"organization_onboarding_steps"}),
             ("qb7c2e9a4d1f", {"customer_invoices", "accounting_export_records", "accounting_events"})]
    db_path = tmp_path / "v1rel5.db"
    cfg = _config(db_path)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["qb7c2e9a4d1f"]
    prior = "pr6b3d8e0f1c"
    for revision, _ in steps:
        assert script.get_revision(revision).down_revision == prior
        prior = revision
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        command.upgrade(cfg, "pr6b3d8e0f1c")
        _seed(db.engine)
        original_tables, original_rows = set(sa.inspect(db.engine).get_table_names()), _db_rows(db.engine)
        tables, rows_before = set(original_tables), original_rows
        for revision, new in steps:
            command.upgrade(cfg, revision)
            after = set(sa.inspect(db.engine).get_table_names())
            assert after - tables == new, revision
            rows = _db_rows(db.engine)
            for table in new:
                assert rows.pop(table) == []
                assert {c["name"] for c in sa.inspect(db.engine).get_columns(table)} == \
                    {c.name for c in db.metadata.tables[table].columns}, table
            for table in tables - original_tables:
                rows.pop(table)
            assert rows == original_rows, revision
            tables = after
        with db.engine.begin() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
        command.downgrade(cfg, "pr6b3d8e0f1c")
        assert set(sa.inspect(db.engine).get_table_names()) == original_tables
        assert _db_rows(db.engine) == original_rows
