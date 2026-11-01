"""Browser walks only: start a wizard run in a walk's own temporary database, as a run started before the
retirement (Task-First UX, Slice C, 1 Nov 2026).

The contractor wizards' web start now opens the Guided Task and starts nothing (app/routes/wizards.py). A run that
already exists keeps working through every step, so the walks that check the runner open such a run instead of
pressing the retired start: this script makes it with the same service the start used, for the same company, person
and (optional) project, and prints ``RUN <id>``. It refuses anything but a local sqlite:/// database.

    python tests/wizard_run_seed.py <sqlite-uri> <WIZARD_KEY> <email> [project_id]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app import create_app, db  # noqa: E402


def main(argv):
    uri, key, email = argv[1], argv[2], argv[3]
    project_id = int(argv[4]) if len(argv) > 4 and argv[4] else None
    if not uri.startswith("sqlite:///"):
        raise SystemExit("only a walk's local sqlite database")
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "wizard-run-seed"})
    with application.app_context():
        from app.models.user import User, UserMembership
        from app.wizards import service as S

        user = User.query.filter_by(email=email).one()
        membership = UserMembership.query.filter_by(user_id=user.id, is_active=True).first()
        run = S.start_contractor_run(key, organization_id=membership.organization_id, actor=user.display_name,
                                     user_id=user.id, project_id=project_id)
        db.session.commit()
        print(f"RUN {run.id}", flush=True)


if __name__ == "__main__":
    main(sys.argv)
