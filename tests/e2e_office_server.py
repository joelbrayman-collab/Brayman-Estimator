"""Local office for the end-to-end contractor workflow browser check.

The database is built by the real migrations (as the hosted office was), on a new
temporary file. It never reads the hosted database. One office user is added.
"""

from __future__ import annotations

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
from tests.auth_fixtures import ensure_office_user  # noqa: E402

FIELD_WORKER = ("kevin.field@example.invalid", "field-test-password", "Kevin Field (synthetic crew)")


def main():
    database = tempfile.NamedTemporaryFile(prefix="e2e-office-", suffix=".db", delete=False)
    database.close()
    uri = f"sqlite:///{database.name}"
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "e2e-secret-key"}
    # The job-lifecycle walk reads captured mail (a supplier's choose-a-password link) from here.
    if os.environ.get("E2E_MAIL_CAPTURE_ROOT"):
        config["MAIL_CAPTURE_ROOT"] = os.environ["E2E_MAIL_CAPTURE_ROOT"]
    application = create_app(config)
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        user = ensure_office_user()
        db.session.commit()
        # The office user owns the company, as Joel does on the hosted office, so the
        # owner-only steps (closing a project) are part of the walk.
        from app.models.user import UserMembership
        from app.services.instance_authority import set_instance_owner
        from app.services.organizations import DEFAULT_ORGANIZATION_ID

        membership = UserMembership.query.filter_by(user_id=user.id, organization_id=DEFAULT_ORGANIZATION_ID).one()
        set_instance_owner(DEFAULT_ORGANIZATION_ID, membership.id, user.id)
        db.session.commit()
        if os.environ.get("E2E_LIFECYCLE") == "1":
            # Operator set-up the hosted office already has, done here as the operator does it (the
            # flask commands), not from a page: a crew member marked field-only, and the Ontario Brayman V1 interim contract package
            # (flask legal-content install-brayman-v1-interim).
            from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package

            kevin = ensure_office_user(email=FIELD_WORKER[0], password=FIELD_WORKER[1], display_name=FIELD_WORKER[2])
            # Kevin is crew: marked field-only (flask auth set-field-only), so he reaches Field and his
            # own account only, and cannot change the schedule (Joel, 21 Oct 2026).
            from app.services.access_domains import set_field_only

            set_field_only(UserMembership.query.filter_by(user_id=kevin.id).one(), True, user)
            ensure_brayman_v1_interim_ontario_package()
            db.session.commit()
    port = int(os.environ["E2E_OFFICE_PORT"])
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
