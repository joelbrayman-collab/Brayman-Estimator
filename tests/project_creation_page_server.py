"""Local office for the Project Creation UX browser walk (tools/release/evidence_project_creation.mjs).

Built by the real migrations on an empty temporary SQLite database, CSRF on. Seeds Ben (owner, synthetic) and the one
customer the office already has — Marc Bouliion (synthetic), with P27's slab project — exactly the situation the
Linda Bushel Production failure started from. Synthetic data only; never reads any hosted database. Prints
``FACTS <json>`` and ``READY <port>``.
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

PEOPLE = {"ben": ("ben.creation@example.invalid", "Synthetic-ben-creation-1", "Ben Brayman (synthetic)")}
MARC = "Marc Bouliion (synthetic)"


def main():
    workdir = tempfile.mkdtemp(prefix="project-creation-walk-")
    uri = f"sqlite:///{workdir}/office.db"
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "project-creation-walk-secret", "WTF_CSRF_ENABLED": True,
                              "TRANSACTIONAL_EMAIL_PROVIDER": "local"})
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        from app.models import Client, Project
        from app.models.user import UserMembership
        from app.services.instance_authority import set_instance_owner
        from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
        from tests.auth_fixtures import ensure_office_user

        ben = ensure_office_user(email=PEOPLE["ben"][0], password=PEOPLE["ben"][1], display_name=PEOPLE["ben"][2])
        set_instance_owner(ORG, UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one().id, ben.id)
        marc = Client(organization_id=ORG, name=MARC, company="Solid Steel Management (synthetic)")
        db.session.add(marc)
        db.session.flush()
        db.session.add(Project(organization_id=ORG, name="40x80 Thickened-Edge Concrete Slab (synthetic)",
                               client_id=marc.id, status="Estimating"))
        db.session.commit()
        facts = {"people": PEOPLE, "marc_id": marc.id}
    port = int(os.environ["PROJECT_CREATION_PAGE_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
