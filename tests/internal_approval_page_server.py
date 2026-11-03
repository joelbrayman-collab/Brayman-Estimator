"""Local office and signing pages for the CaliSIGN internal-approval browser walk
(tools/release/evidence_internal_approval.mjs). Temporary database, mail captured to a temporary folder, synthetic
data only.

Seeds only what exists before the walk: the synthetic company (labour at $80, materials at 15 %), its owner (the
people administrator), two employees with cost profiles, and a priced siding job with its crew. Nothing is frozen,
sent or signed here: the walk freezes REV1, sends it for internal approval and signs it in the browser, reading the
invitation link from the captured email.
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

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401

OWNER = ("owner.walk@example.invalid", "owner-walk-password-1", "Owner Synthetic")
APPROVER = ("Approver Synthetic", "approver.walk@example.invalid")


def seed(application) -> dict:
    from app.services import guided_estimating as G
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
    from tests.auth_fixtures import ensure_office_user, login_office_user
    from tests.guided_support import Driver, seed_company
    from tests.test_internal_financial_summary import (
        WORKER_A,
        WORKER_B,
        _add_employee,
        _brayman_pricing,
        _job_with_labour,
        _membership,
    )

    application.config["WTF_CSRF_ENABLED"] = False  # seed only; the browser walk runs with CSRF on
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        seed_company()
        _brayman_pricing()
        owner = ensure_office_user(email=OWNER[0], password=OWNER[1], display_name=OWNER[2])
        set_instance_owner(ORG, _membership(owner).id, owner.id)
        db.session.commit()
        driver = Driver(application.test_client())
        login_office_user(driver.http, email=OWNER[0], password=OWNER[1])
        project, guided = _job_with_labour(driver)
        a = _add_employee(driver, WORKER_A)
        b = _add_employee(driver, WORKER_B)
        driver.post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id), str(b.id)]})
        stage = G.get_guided(ORG, project.id).top_stages[0]
        facts = {"project_id": project.id, "stage_id": stage.id}
    application.config["WTF_CSRF_ENABLED"] = True
    return facts


def main():
    workdir = tempfile.mkdtemp(prefix="internal-approval-")
    port = int(os.environ["INTERNAL_APPROVAL_PAGE_PORT"])
    mail = os.path.join(workdir, "mail")
    os.makedirs(mail, exist_ok=True)
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{workdir}/internal-approval.db",
                              "SECRET_KEY": "test-secret-key", "TRANSACTIONAL_EMAIL_PROVIDER": "local",
                              "MAIL_CAPTURE_ROOT": mail, "PUBLIC_BASE_URL": f"http://127.0.0.1:{port}",
                              "DOCUMENT_ROOT": os.path.join(workdir, "documents")})
    facts = seed(application)
    facts.update({"owner": [OWNER[0], OWNER[1]], "approver": list(APPROVER), "mail": mail})
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
