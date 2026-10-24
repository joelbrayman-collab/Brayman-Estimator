"""Local office and Supplier Hub for the Guided Workflow Wizards browser walk (tools/release/evidence_wizards.mjs).

Built by the real migrations on an empty temporary SQLite database, CSRF on for the walk. Seeds, through the same
routes and services a person uses: Ben (owner), Kevin (Field-only crew), an owner of another synthetic company, a
customer and the company costs; one New Home already estimated stage by stage (every stage costed, not yet
priced) for Guided Estimating; one already accepted with its work plan for Manage a Project; and a synthetic store
with its price file and standard building for the Supplier Pro Desk, plus a rival store. Synthetic data only;
never reads any hosted database. Prints ``FACTS <json>`` and ``READY <port>``.
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

PEOPLE = {
    "ben": ("ben.wizard@example.invalid", "Synthetic-ben-wizard-1", "Ben Brayman (synthetic)"),
    "kevin": ("kevin.wizard@example.invalid", "Synthetic-kevin-wizard-1", "Kevin Field (synthetic crew)"),
    "other": ("other.wizard@example.invalid", "Synthetic-other-wizard-1", "Other Builder Owner (synthetic)"),
}


def _seed_estimates(application):
    """Two New Homes costed through the guided-estimating pages, the second accepted and handed to the build."""
    from flask import g

    from app.services import guided_estimating as G
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
    from tests.auth_fixtures import login_office_user
    from tests.guided_support import Driver
    from tests.test_guided_estimating import _cost_new_home

    application.config["WTF_CSRF_ENABLED"] = False  # seed only; the browser walk runs with CSRF on
    http = application.test_client()
    g.pop("_login_user", None)
    login_office_user(http, email=PEOPLE["ben"][0], password=PEOPLE["ben"][1])
    d = Driver(http)
    from tests.guided_support import NEW_HOME_SCOPE

    out = {}
    for key, name in (("estimate", "Avery New Home (synthetic)"), ("manage", "Lindqvist New Home (synthetic)")):
        project, _loc = d.new_project(name, "NEW_HOME", "GENERAL_CONTRACTOR")
        d.scope(project, NEW_HOME_SCOPE, action="finalize")
        _cost_new_home(d, project)
        out[key] = project.id
    # The second one: priced, proposed, accepted, locked and seeded into the work plan (existing services).
    from app.models import Project
    from app.services.estimates import lock_version
    from app.services.proposals import create_proposal, create_proposal_template, update_proposal_status
    from app.services.work_structure import seed_project_work_structure

    project = db.session.get(Project, out["manage"])
    version = G.current_version(G.get_guided(ORG, project.id))
    d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/approve-all-costing", data={})
    d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/apply-org-pricing", data={})
    db.session.expire_all()
    version = G.current_version(G.get_guided(ORG, project.id))
    template = create_proposal_template(name="Synthetic standard", organization_id=ORG, is_default=True)
    proposal = create_proposal(estimate=version.estimate, version=version, template=template, organization_id=ORG)
    update_proposal_status(proposal, "Issued")
    update_proposal_status(proposal, "Accepted")
    lock_version(version)
    seed_project_work_structure(project_id=project.id, estimate_version_id=version.id, seeded_by=PEOPLE["ben"][2],
                                organization_id=ORG)
    application.config["WTF_CSRF_ENABLED"] = True
    return out


def main():
    workdir = tempfile.mkdtemp(prefix="wizards-walk-")
    uri = f"sqlite:///{workdir}/office.db"
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "wizards-walk-secret", "WTF_CSRF_ENABLED": True,
                              "TRANSACTIONAL_EMAIL_PROVIDER": "local",
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
        from tests.guided_support import seed_company

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
        db.session.commit()
        seed_company()
        projects = _seed_estimates(application)
        from tests.pro_desk_page_server import QUICK_FORM, STORE, RIVAL, seed as seed_store

        store = seed_store()
        _ = CostItem
    port = int(os.environ["WIZARDS_PAGE_PORT"])
    facts = {"people": PEOPLE, "projects": projects, "store": store, "store_login": list(STORE),
             "rival_login": list(RIVAL), "quick": QUICK_FORM}
    print("FACTS " + json.dumps(facts), flush=True)
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
