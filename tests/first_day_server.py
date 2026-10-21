"""Local office for Ben's First Day browser walk (tools/release/evidence_first_day.mjs, 21 Oct 2026).

A brand-new contractor office on a temporary SQLite database, built by the real migrations as the hosted
office was, so it holds exactly the reference data a new company starts with (the default organization,
its jurisdiction, permit and material reference rows, the baseline work catalog). On top of that, only:

* one sign-in: Ben Brayman (synthetic), the Instance Owner (operator command ``flask auth`` does this on
  the hosted office);
* the Ontario Brayman V1 interim contract package (operator command
  ``flask legal-content install-brayman-v1-interim``), so an accepted proposal makes its contract;
* one supplier already on the platform: its own company, store location and store sign-in, with NO
  account at Ben's company. Ben adds it from Suppliers in the walk, as a new contractor finds their
  supplier on the platform.

Everything else (brand, pricing, people, calendars, suppliers, customers, estimate, proposal, invoice,
purchase order, crew schedule) is done in the browser. Outgoing mail is captured to files (``mail_dir``)
so the walk can open the set-password link. CSRF is on, as in production. Synthetic data only; it never
reads the hosted database.
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

BEN = ("ben.first-day@example.invalid", "Synthetic-ben-first-day-1", "Ben Brayman (synthetic)")
SUPPLIER_NAME = "Riverbend Synthetic Supply"
SUPPLIER_LOCATION = "Riverbend yard (synthetic)"
STORE_USER = ("Sky Storeperson (synthetic)", "sky.store@example.invalid", "Synthetic-store-pass-1")


def supplier_code(name: str) -> str:
    """The code the Suppliers page derives from a typed supplier name (supplier_office.create_supplier_account)."""
    return "".join(ch if ch.isalnum() else "-" for ch in name.upper()).strip("-")[:60] or "SUPPLIER"


def _migrate(uri: str) -> None:
    cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    command.upgrade(cfg, "head")


def _ben():
    from app.models.user import UserMembership
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from tests.auth_fixtures import ensure_office_user

    ben = ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
    db.session.commit()
    membership = UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one()
    set_instance_owner(ORG, membership.id, ben.id)
    db.session.commit()
    return ben


def _platform_supplier():
    """A supplier company already on the platform with its own store sign-in, not yet Ben's supplier."""
    from app.models.supplier_portal import MEMBERSHIP_ACTIVE, SupplierUserMembership
    from app.models.user import User
    from app.services.auth import hash_password
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from app.services.supplier_catalogue import create_supplier, create_supplier_location

    supplier = create_supplier(code=supplier_code(SUPPLIER_NAME), legal_name=SUPPLIER_NAME, demo_synthetic=True)
    create_supplier_location(supplier_id=supplier.id, code="MAIN", display_name=SUPPLIER_LOCATION, demo_synthetic=True)
    user = User(email=STORE_USER[1], display_name=STORE_USER[0], password_hash=hash_password(STORE_USER[2]), is_active=True)
    db.session.add(user)
    db.session.flush()
    db.session.add(SupplierUserMembership(user_id=user.id, supplier_id=supplier.id, status=MEMBERSHIP_ACTIVE,
                                          created_by_name="Platform set-up (synthetic)", created_by_organization_id=ORG))
    db.session.commit()
    return supplier


def main():
    workdir = tempfile.mkdtemp(prefix="first-day-")
    mail = os.path.join(workdir, "mail")
    uri = f"sqlite:///{workdir}/first_day.db"
    config = {"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
              "SECRET_KEY": "first-day-secret-key", "WTF_CSRF_ENABLED": True,
              "TRANSACTIONAL_EMAIL_PROVIDER": "local", "MAIL_CAPTURE_ROOT": mail,
              "CONTRACT_ARTIFACT_ROOT": os.path.join(workdir, "contracts"),
              "SIGNING_ARTIFACT_ROOT": os.path.join(workdir, "signing"),
              "BRAND_LOGO_ROOT": os.path.join(workdir, "logos"),
              "DECK_TAKEOFF_ROOT": os.path.join(workdir, "deck_takeoff")}
    application = create_app(config)
    with application.app_context():
        _migrate(uri)
        from app.services.brayman_v1_interim_contract import ensure_brayman_v1_interim_ontario_package
        from app.services.work_structure import ensure_baseline_work_catalog

        ensure_baseline_work_catalog()
        ben = _ben()
        ensure_brayman_v1_interim_ontario_package()
        db.session.commit()
        supplier = _platform_supplier()
        facts = {"ben": [BEN[0], BEN[1]], "ben_name": BEN[2], "ben_user_id": ben.id,
                 "supplier_name": SUPPLIER_NAME, "supplier_id": supplier.id, "supplier_location": SUPPLIER_LOCATION,
                 "store": [STORE_USER[1], STORE_USER[2]], "store_name": STORE_USER[0],
                 "mail_dir": mail, "database_uri": uri, "workdir": workdir}
    port = int(os.environ["FIRST_DAY_PORT"])
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
