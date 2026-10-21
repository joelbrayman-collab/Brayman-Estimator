"""Give the training site's Harbour Lane Pool Deck (training) its synthetic construction model (21 Oct 2026).

Used only by tools/training/capture_supplier_shots.mjs, against the temporary database that
tests/training_page_server.py made. CalibraytAI has no office page that creates a construction model (it
comes with the estimate's source drawings), so this one record is added here; everything after it (product
facts, the supplier request, sending it to BMR Winchester (training)) is done through the real office pages.
The geometry is the synthetic pool-deck fixture used by the takeoff tests. Refuses anything but the training
site. Synthetic data only.

    venv/bin/python tools/training/seed_harbour_lane_model.py <sqlite database uri>
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402


def main(uri: str) -> None:
    if not uri.startswith("sqlite:///") or "training-site-" not in uri:
        raise SystemExit("Refused: only the temporary training-site database from tests/training_page_server.py.")
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "training-seed", "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        from app.models import Project
        from app.services.project_construction_model import save_construction_model_revision
        from app.training.environment import JOB
        from tests.fixtures.construction_model.linda_j1_takeoff_fixture import model

        project = Project.query.filter_by(name=JOB).one()
        save_construction_model_revision(organization_id=project.organization_id, project_id=project.id,
                                         content=model(), source_kind="source_document",
                                         source_reference="Harbour Lane Pool Deck (training) — synthetic training drawing",
                                         actor_display_name="Training site set-up")
        db.session.commit()
        print(f"MODEL {project.id}")


if __name__ == "__main__":
    main(sys.argv[1])
