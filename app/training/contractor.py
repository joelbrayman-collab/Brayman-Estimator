"""Contractor training: 12 modules for the contractor owner, office staff and field workers.

Ben's First Day (app/services/onboarding.py, Company → Getting started) is the foundation of the owner's
pathway. A field worker gets only the Field lessons. Connected example: see app/training/content.py.
"""

from app.models.training import PATHWAY_CONTRACTOR as P
from app.models.training import ROLE_FIELD, ROLE_OFFICE, ROLE_OWNER
from app.training.content import (
    ALL_CONTRACTOR,
    APP_EMAIL,
    APP_FIELD,
    APP_OFFICE,
    OFFICE_ROLES,
    Lesson,
    Module,
    Step,
    UatCase,
)

MODULES = (
    Module(
        key="c01", pathway=P, number=1, title="Welcome, registration and first sign-in",
        summary="Sign in to CalibraytAI, find your way around and register for training.",
        roles=ALL_CONTRACTOR,
        lessons=(
            Lesson(
                key="c01-sign-in", title="Sign in for the first time",
                what="Sign in with the email and password from your invitation and change the password to your own.",
                why="Your own sign-in keeps your work under your name, and only you know your password.",
                steps=(
                    Step(title="Open the sign-in page", app=APP_OFFICE, where="The training site address Joel sent you",
                         do="Type your email and password, then press Sign in",
                         enter="Your email and the password from your invitation",
                         expect="Home opens (field workers: My Work on Field opens).",
                         if_wrong="Check the email is typed exactly. Press Forgot password to get a new link by email.",
                         endpoint="auth.login"),
                    Step(title="Change your password", app=APP_OFFICE, where="The key button at the top right (Change password)",
                         do="Type the old password once and your new password twice, then press Change password",
                         enter="A password only you know, at least 12 characters",
                         expect="A green message says the password was changed.",
                         if_wrong="If it says the old password is wrong, sign out and use Forgot password.",
                         endpoint="auth.change_password"),
                ),
                exercise="Sign in to the training site and change your password.",
            ),
        ),
    ),
)

UAT_CASES = (
    UatCase(key="uat-c01-sign-in", pathway=P, module_key="c01", title="Sign in and change the password",
            start="The training site's sign-in page", action="Sign in with your training email and password, then change the password.",
            expected="You are signed in under your own name and the new password works the next time you sign in.",
            roles=ALL_CONTRACTOR),
)
_ = (ROLE_FIELD, ROLE_OFFICE, ROLE_OWNER, APP_EMAIL, APP_FIELD, OFFICE_ROLES)
