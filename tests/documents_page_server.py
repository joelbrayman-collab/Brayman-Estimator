"""Local office for the Documents browser walk (tools/release/evidence_documents.mjs, 31 Oct 2026).

Temporary database and document folder, synthetic data only (tests/documents_support.py): an owner, an office member,
a Field-only crew member booked on one job, a subcontractor, a supplier account, and another organization. Writes a
WSIB clearance PDF (expiring in 20 days) and its renewal to the work folder. Prints FACTS <json> and READY <port>.
It never reads the hosted database.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402


def main():
    workdir = tempfile.mkdtemp(prefix="documents-office-")
    uri = f"sqlite:///{workdir}/documents.db"
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "documents-walk-secret", "WTF_CSRF_ENABLED": False,
              "DOCUMENT_ROOT": os.path.join(workdir, "documents"), "PLAN_UPLOAD_ROOT": os.path.join(workdir, "plans"),
              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": os.path.join(workdir, "mail"),
              "BRAND_LOGO_ROOT": os.path.join(workdir, "logos")}
    application = create_app(config)
    with application.app_context():
        db.create_all()
        from app.services.local_time import local_today
        from app.services.organizations import ensure_default_organization
        from tests.documents_support import CREW, STAFF, make_world, text_pdf

        ensure_default_organization()
        world = make_world(crew=True)
        expires = local_today() + timedelta(days=20)
        wsib = Path(workdir) / "WSIB clearance Acme.pdf"
        wsib.write_bytes(text_pdf("Workplace Safety and Insurance Board", "Clearance certificate",
                                  f"Valid until {expires.isoformat()}"))
        renewal = Path(workdir) / "WSIB clearance Acme renewed.pdf"
        renewal.write_bytes(text_pdf("Workplace Safety and Insurance Board", "Clearance certificate (renewed)",
                                     f"Valid until {(expires + timedelta(days=90)).isoformat()}"))
        facts = {"staff": list(STAFF[:2]), "crew": list(CREW[:2]), "sub_id": world["sub"].id,
                 "project_id": world["project"].id, "wsib_pdf": str(wsib), "renewal_pdf": str(renewal),
                 "expires": expires.isoformat()}
    application.config["WTF_CSRF_ENABLED"] = True  # seed only; the walk runs with CSRF on
    port = int(os.environ["DOCUMENTS_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    from tests import server_cleanup

    server_cleanup.install()  # its temporary files go when it stops
    main()
