"""Local office for the Guided Estimating browser walk (tools/release/evidence_guided_estimating.mjs, 23 Oct 2026).

Built by the real migrations on an empty temporary SQLite database (so the seeded $65/h labour rate and the 15 %
true-gross-margin policy are the ones the office has), CSRF on. Adds: Ben (owner), Kevin (Field-only crew), an
owner of another synthetic company, a customer, and the company costs the estimate review matches by unit.
Synthetic data only; never reads any hosted database. Prints ``FACTS <json>`` and ``READY <port>``.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app import create_app, db  # noqa: E402

PEOPLE = {
    "ben": ("ben.walk@example.invalid", "Synthetic-ben-guided-1", "Ben Brayman (synthetic)"),
    "kevin": ("kevin.walk@example.invalid", "Synthetic-kevin-guided-1", "Kevin Field (synthetic crew)"),
    "other": ("other.walk@example.invalid", "Synthetic-other-guided-1", "Other Builder Owner (synthetic)"),
}


def main():
    workdir = tempfile.mkdtemp(prefix="guided-walk-")
    uri = f"sqlite:///{workdir}/office.db"
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "guided-walk-secret", "WTF_CSRF_ENABLED": True,
                              "DECK_TAKEOFF_ROOT": os.path.join(workdir, "deck_takeoff")})
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        from app.models import Client, CostItem
        from app.models.organization import Organization
        from app.models.user import UserMembership
        from app.services.access_domains import set_field_only
        from app.services.instance_authority import set_instance_owner
        from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
        from tests.auth_fixtures import ensure_office_user
        from tests.guided_support import COST_ITEMS

        ben = ensure_office_user(email=PEOPLE["ben"][0], password=PEOPLE["ben"][1], display_name=PEOPLE["ben"][2])
        set_instance_owner(ORG, UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one().id, ben.id)
        kevin = ensure_office_user(email=PEOPLE["kevin"][0], password=PEOPLE["kevin"][1], display_name=PEOPLE["kevin"][2])
        set_field_only(UserMembership.query.filter_by(user_id=kevin.id).one(), True, ben)
        db.session.add(Organization(id="ORG-WALK-OTHER", legal_name="Other Synthetic Builder",
                                    display_name="Other Synthetic Builder", is_active=True))
        db.session.commit()
        ensure_office_user(email=PEOPLE["other"][0], password=PEOPLE["other"][1], display_name=PEOPLE["other"][2],
                           organization_id="ORG-WALK-OTHER")
        db.session.add(Client(name="Jordan Avery (synthetic)", organization_id=ORG, email="jordan.avery@example.invalid"))
        for code, name, unit, cost in COST_ITEMS:
            db.session.add(CostItem(code=code, name=name, category="Material", unit=unit, unit_cost=Decimal(cost),
                                    default_markup_percent=Decimal("0"), organization_id=ORG, is_active=True))
        db.session.commit()
        if os.environ.get("GUIDED_PROPOSAL_TEMPLATE"):  # the selected-work walk goes on to the proposal
            from app.services.proposals import create_proposal_template

            create_proposal_template(name="Synthetic standard", organization_id=ORG, is_default=True)
            db.session.commit()
    port = int(os.environ["GUIDED_PAGE_PORT"])
    print("FACTS " + json.dumps({"people": PEOPLE, "database_uri": uri}), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
