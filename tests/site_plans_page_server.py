"""Local office for the Site Plans browser walk (tools/release/evidence_site_plans.mjs, 23 Oct 2026).

Temporary database and plan folder, synthetic data only (tests/site_plans_support.py): an owner, Kevin (Field-only,
booked on Harbour Lane), Lee (Field-only, booked on nothing), two jobs with plans, a generated drawing set, a priced
estimate, and another organization with its own project and plan. Prints FACTS <json> and READY <port>.
It never reads the hosted database.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402


def main():
    workdir = tempfile.mkdtemp(prefix="site-plans-office-")
    uri = f"sqlite:///{workdir}/site_plans.db"
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "site-plans-walk-secret", "WTF_CSRF_ENABLED": False,
              "PLAN_UPLOAD_ROOT": os.path.join(workdir, "plans"), "TRANSACTIONAL_EMAIL_PROVIDER": "local",
              "MAIL_CAPTURE_ROOT": os.path.join(workdir, "mail"), "BRAND_LOGO_ROOT": os.path.join(workdir, "logos")}
    application = create_app(config)
    with application.app_context():
        db.create_all()
        from tests.site_plans_support import seed

        facts = seed()
    application.config["WTF_CSRF_ENABLED"] = True  # seed only; the walk runs with CSRF on
    facts.update({"database_uri": uri, "workdir": workdir})
    port = int(os.environ["SITE_PLANS_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
