"""FG-035 SCH-B Organization Crew office routes.

Dedicated /settings/crews. Not Brand Profile settings.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.organization_crew import (
    CrewError,
    CrewNotFoundError,
    add_crew_member,
    close_crew_membership,
    create_crew,
    get_crew,
    list_crews,
    list_org_people,
    retire_crew,
)
from app.services.organizations import get_current_organization

organization_crew_bp = Blueprint(
    "organization_crew",
    __name__,
    url_prefix="/settings/crews",
)


def _org():
    return get_current_organization()


@organization_crew_bp.route("")
def index():
    organization = _org()
    return render_template(
        "settings/crews/index.html",
        crews=list_crews(organization.id, include_inactive=True),
    )


@organization_crew_bp.route("/new", methods=["GET", "POST"])
def new():
    organization = _org()
    if request.method == "POST":
        try:
            create_crew(name=request.form.get("name"), organization_id=organization.id)
            flash("Crew saved.", "success")
            return redirect(url_for("organization_crew.index"))
        except (CrewError, CrewNotFoundError) as exc:
            flash(str(exc), "error")
    return render_template("settings/crews/form.html")


@organization_crew_bp.route("/<int:crew_id>")
def detail(crew_id):
    organization = _org()
    try:
        crew = get_crew(crew_id, organization_id=organization.id)
    except CrewNotFoundError as exc:
        flash(str(exc), "error")
        return redirect(url_for("organization_crew.index"))
    return render_template(
        "settings/crews/detail.html",
        crew=crew,
        people=list_org_people(organization.id),
    )


@organization_crew_bp.route("/<int:crew_id>/retire", methods=["POST"])
def retire(crew_id):
    organization = _org()
    try:
        retire_crew(crew_id, organization_id=organization.id)
        flash("Crew retired.", "success")
    except (CrewError, CrewNotFoundError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("organization_crew.index"))


@organization_crew_bp.route("/<int:crew_id>/members", methods=["POST"])
def add_member(crew_id):
    organization = _org()
    try:
        add_crew_member(
            crew_id,
            user_id=int((request.form.get("user_id") or "").strip()),
            effective_from=request.form.get("effective_from"),
            effective_to=request.form.get("effective_to") or None,
            organization_id=organization.id,
        )
        flash("Crew dates saved.", "success")
        return redirect(url_for("organization_crew.detail", crew_id=crew_id))
    except (TypeError, ValueError):
        flash("Choose a person and dates.", "error")
        return redirect(url_for("organization_crew.detail", crew_id=crew_id))
    except CrewNotFoundError as exc:
        flash(str(exc), "error")
        return redirect(url_for("organization_crew.index"))
    except CrewError as exc:
        flash(str(exc), "error")
        return redirect(url_for("organization_crew.detail", crew_id=crew_id))


@organization_crew_bp.route("/<int:crew_id>/members/<int:member_id>/close", methods=["POST"])
def close_member(crew_id, member_id):
    organization = _org()
    try:
        get_crew(crew_id, organization_id=organization.id)
        close_crew_membership(
            member_id,
            effective_to=request.form.get("effective_to"),
            organization_id=organization.id,
        )
        flash("Crew dates closed.", "success")
        return redirect(url_for("organization_crew.detail", crew_id=crew_id))
    except CrewNotFoundError as exc:
        flash(str(exc), "error")
        return redirect(url_for("organization_crew.index"))
    except CrewError as exc:
        flash(str(exc), "error")
        return redirect(url_for("organization_crew.detail", crew_id=crew_id))
