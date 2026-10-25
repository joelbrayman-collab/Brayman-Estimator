"""Local office for the Magnificent Seven browser walk (tools/release/evidence_magnificent_seven.mjs).

Built by the real migrations on an empty temporary SQLite database, CSRF on for the walk. Seeds the synthetic
Brayman Construction of tests/magnificent_seven_support.py (Ben, Suzanne, Kevin and Liam, another company, the
Harbour Lane job with Kevin booked today, Shop / Company Work, BMR Winchester with Darcy's sign-in, a confirmed
purchase order due today) and connects the office to the in-memory test QuickBooks Online company through the same
service the OAuth callback uses (no browser can reach Intuit from a test, and none should). End-of-day reminders are
due all day on every day, so the walk can make them at any hour. Synthetic data only; never reads a hosted database.
Prints ``FACTS <json>`` and ``READY <port>``.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app import create_app, db  # noqa: E402


def main():
    workdir = tempfile.mkdtemp(prefix="mag7-walk-")
    uri = f"sqlite:///{workdir}/office.db"
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "mag7-walk-secret", "WTF_CSRF_ENABLED": True,
                              "TRANSACTIONAL_EMAIL_PROVIDER": "local",
                              "DECK_TAKEOFF_ROOT": os.path.join(workdir, "deck_takeoff"),
                              "BUILD_ORIGINAL_ROOT": os.path.join(workdir, "build")})
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        from app.models.field_operations import OperationsSettings
        from app.services import quickbooks_online as qbo
        from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
        from tests.magnificent_seven_support import PEOPLE, build

        facts = build(application)
        fake = facts["fake"]
        qbo.complete_authorization(ORG, facts["ben"], code=fake.issue_code(), realm_id=fake.realm_id)
        conn = qbo.connection(ORG)
        accounts = {r["Name"]: r["Id"] for r in fake.entities["Account"].values()}
        codes = {r["Name"]: r["Id"] for r in fake.entities["TaxCode"].values()}
        conn.expense_account_id, conn.expense_account_name = accounts["Job Materials"], "Job Materials"
        conn.payment_account_id, conn.payment_account_name = accounts["Company Visa"], "Company Visa"
        conn.payment_type = "CreditCard"
        conn.tax_code_id, conn.tax_code_name = codes["HST ON"], "HST ON"
        conn.no_tax_code_id, conn.no_tax_code_name = codes["Exempt"], "Exempt"
        from app.services.local_time import local_today

        hand_entered = fake.add("Purchase", PaymentType="CreditCard", TxnDate=local_today().isoformat(), TotalAmt=56.5,
                                EntityRef={"value": fake.by_name("Vendor", "Home Hardware Kemptville (synthetic)")["Id"],
                                           "type": "Vendor", "name": "Home Hardware Kemptville (synthetic)"},
                                PrivateNote="Entered by hand (synthetic)")
        db.session.add(OperationsSettings(organization_id=ORG, reminder_time="00:00", latest_time="23:59",
                                          working_days="0,1,2,3,4,5,6"))
        db.session.commit()
        out = {"people": PEOPLE, "project_id": facts["project"].id, "second_id": facts["second"].id,
               "company_id": facts["company"].id, "order_id": facts["order"].id, "order_number": facts["order"].number,
               "account_id": facts["account"].id, "supplier_id": facts["supplier"].id,
               "activity_id": facts["activity"].id, "element_id": facts["element"].id,
               "hand_entered_purchase": hand_entered["Id"]}
    application.config["MAG7_FAKE_QBO"] = fake
    port = int(os.environ["MAG7_PAGE_PORT"])
    print("FACTS " + json.dumps(out), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
