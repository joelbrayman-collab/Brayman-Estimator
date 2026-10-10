"""Local office page for the concrete calculator browser test.

This server uses a temporary database. It does not read the hosted database.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from tests.auth_fixtures import ensure_office_user


def main():
    database = tempfile.NamedTemporaryFile(prefix="concrete-page-", suffix=".db", delete=False)
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
    port = int(os.environ["CONCRETE_PAGE_PORT"])
    print(f"READY {port}", flush=True)
    application.run(host="127.0.0.1", port=port, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
