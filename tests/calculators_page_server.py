"""Local office pages for the calculator browser tests (Link to a project, the new design).

Temporary database with one office user and two synthetic projects. Never reads the hosted database.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import Client, Project
from tests.auth_fixtures import DEFAULT_ORGANIZATION_ID as ORG, ensure_office_user

PROJECTS = ("Synthetic Harbour Lane Pool Deck", "Synthetic Garage Slab")


def main():
    database = tempfile.NamedTemporaryFile(prefix="calculators-page-", suffix=".db", delete=False)
    database.close()
    application = create_app(
        {
            "TESTING": True,
            "CALIBRAYTAI_HOSTED": "0",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.name}",
            "SECRET_KEY": "test-secret-key",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_office_user()
        client = Client(name="Synthetic Client", organization_id=ORG)
        db.session.add(client)
        db.session.flush()
        for name in PROJECTS:
            db.session.add(Project(name=name, client_id=client.id, organization_id=ORG, status="Estimating"))
        db.session.commit()
    port = int(os.environ["CALCULATORS_PAGE_PORT"])
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
