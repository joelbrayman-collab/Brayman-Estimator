"""Standalone contractor calculators.

The Concrete page renders the preserved Website engine in the browser.
This module does not calculate a slab and does not write an estimate.
"""

from flask import Blueprint, render_template

calculators_bp = Blueprint(
    "calculators",
    __name__,
    url_prefix="/calculators",
)


@calculators_bp.get("/concrete")
def concrete():
    return render_template("calculators/concrete.html")
