"""Standalone contractor calculators.

The pages render the preserved Website engines in the browser.
This module does not calculate and does not write an estimate.
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


@calculators_bp.get("/stairs")
def stairs():
    return render_template("calculators/stairs.html")
