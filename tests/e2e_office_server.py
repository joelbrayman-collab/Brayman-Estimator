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


def main():
    database = tempfile.NamedTemporaryFile(prefix="e2e-office-", suffix=".db", delete=False)
    database.close()
    uri = f"sqlite:///{database.name}"
    application = create_app({"TESTING": True, "CALIBRAYTAI_HOSTED": "0", "SQLALCHEMY_DATABASE_URI": uri,
                              "SECRET_KEY": "e2e-secret-key"})
    with application.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", uri)
        command.upgrade(cfg, "head")
        ensure_office_user()
        db.session.commit()
    port = int(os.environ["E2E_OFFICE_PORT"])
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
