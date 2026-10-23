"""Local office for the payroll-handoff browser walk (tools/release/evidence_time_payroll.mjs, 22 Oct 2026).

The same synthetic office as tests/field_time_server.py (Ben, the owner, on a desktop; Kevin, field-only, on his
phone; one customer job with estimated work and Kevin scheduled on it), built by the real migrations, plus a
FAKE QuickBooks Time account (app/services/quickbooks_time_transport.py) holding Kevin as a person and job codes
for the job and for shop work. Nothing goes to Intuit. Everything else (the hours policy, Shop / Company Work, the
links, Kevin's time, approval, the transfer, the correction, the check, banked hours) happens in the browser.
CSRF is on. Synthetic data only.
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

from tests.field_time_server import _migrate, _seed  # noqa: E402  (imports the app the usual way first)

from app import create_app  # noqa: E402


def main():
    workdir = tempfile.mkdtemp(prefix="time-payroll-")
    uri = f"sqlite:///{workdir}/time_payroll.db"
    import app.models  # noqa: F401  (models before services, as create_app does)
    from app.services.quickbooks_time_transport import FakeQuickBooksTimeTransport

    fake = FakeQuickBooksTimeTransport()
    kevin_qbt = fake.add_user("Kevin", "Fieldhand (synthetic)")
    job_code = fake.add_jobcode("Mill Pond Road deck (synthetic)")
    shop_code = fake.add_jobcode("Shop (synthetic)")
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "time-payroll-secret-key", "WTF_CSRF_ENABLED": True,
              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": os.path.join(workdir, "mail"),
              "QBT_TEST_TRANSPORT": fake}
    application = create_app(config)
    with application.app_context():
        _migrate(uri)
        facts = _seed()
        from app.models.user import User

        facts["kevin_id"] = User.query.filter_by(email=facts["kevin"][0]).one().id
    facts.update(workdir=workdir, qbt_kevin=str(kevin_qbt), qbt_job=str(job_code), qbt_shop=str(shop_code))
    port = int(os.environ["TIME_PAYROLL_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=False)


if __name__ == "__main__":
    main()
