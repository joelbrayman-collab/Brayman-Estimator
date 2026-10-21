"""Operator steps for the roles walk (tools/release/evidence_roles.mjs), run against its temporary database.

This runs the ``flask auth`` operator commands (through Flask's CLI runner) for one person named by email,
so the walk proves the commands still work. Since 21 Oct 2026 the owner can do the same from the People &
Access pages (/settings/people), which the walk also exercises. ``deactivate-user`` / ``reactivate-user``
set the account's ``is_active`` flag directly (the same flag the People & Access page uses).

Usage: python tests/roles_operator.py <database-uri> <action> <email>
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402

COMMANDS = {
    "grant-management": ["grant-access-domain", "--domain", "COMPANY_MANAGEMENT"],
    "revoke-management": ["revoke-access-domain", "--domain", "COMPANY_MANAGEMENT"],
    "appoint-administrator": ["appoint-system-administrator"],
    "remove-administrator": ["remove-system-administrator"],
}


def main(uri: str, action: str, email: str) -> int:
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri, "SECRET_KEY": "roles-operator"})
    with application.app_context():
        from app.models.user import User, UserMembership
        from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

        user = User.query.filter_by(email=email).one()
        owner = User.query.filter_by(email="office@example.com").one()
        membership = UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()
        if action in ("deactivate-user", "reactivate-user"):
            user.is_active = action == "reactivate-user"
            db.session.commit()
            print(f"{action} {email}")
            return 0
        args = ["auth", *COMMANDS[action][:1], "--membership-id", str(membership.id), *COMMANDS[action][1:]]
        if action.endswith("administrator"):
            args += ["--organization-id", ORG, "--actor-user-id", str(owner.id)]
        result = application.test_cli_runner().invoke(args=args)
        print(result.output.strip())
        return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:4]))
