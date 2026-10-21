"""Supplier training: 10 modules for supplier owners, administrators and PRO Desk staff.

Example: BMR Winchester (training), Darcy at the store and Pat at the PRO Desk, following the same
Harbour Lane Pool Deck job from the supplier's side. BMR sells concrete to the contractor; Tomlinson
Ready-Mix supplies it to BMR upstream.
"""

from app.models.training import PATHWAY_SUPPLIER as P
from app.training.content import ALL_SUPPLIER, APP_SUPPLIER, Lesson, Module, Step, UatCase

MODULES = (
    Module(
        key="s01", pathway=P, number=1, title="Welcome, registration and supplier sign-in",
        summary="Sign in to the Supplier Hub and register for training.",
        roles=ALL_SUPPLIER,
        lessons=(
            Lesson(
                key="s01-sign-in", title="Sign in to the Supplier Hub",
                what="Sign in to the Supplier Hub with the email and password from your invitation.",
                why="The Supplier Hub is where your contractors' requests, orders and deliveries arrive.",
                steps=(
                    Step(title="Open the supplier sign-in", app=APP_SUPPLIER, where="The training site address, then Supplier sign-in",
                         do="Type your email and password, then press Sign in",
                         enter="Your email and the password from your invitation",
                         expect="Your Supplier Hub home opens with your store's name at the top.",
                         if_wrong="Check the email. If the password does not work, ask the contractor who added you to send a new link.",
                         endpoint="supplier_portal.login"),
                ),
                exercise="Sign in to the Supplier Hub on the training site.",
            ),
        ),
    ),
)

UAT_CASES = (
    UatCase(key="uat-s01-sign-in", pathway=P, module_key="s01", title="Supplier sign-in",
            start="The training site's supplier sign-in page", action="Sign in with your training email and password.",
            expected="Your store's Supplier Hub opens; no contractor office pages are shown.", roles=ALL_SUPPLIER),
)
