"""Costs & pricing landing. Presentation only."""

from flask import Blueprint, render_template

costs_and_pricing_bp = Blueprint(
    "costs_and_pricing",
    __name__,
    url_prefix="/costs-and-pricing",
)


@costs_and_pricing_bp.route("/")
def index():
    return render_template("costs_and_pricing/index.html")
