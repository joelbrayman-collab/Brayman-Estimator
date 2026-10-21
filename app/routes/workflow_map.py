"""Workflow Guide in the contractor office (Joel, 21 Oct 2026).

/workflow                  the Contractor Workflow Map (?stage=<id> shows a stage, ?project_id=<id> uses a
                           project of this company for the links and shows the stage the project is in)
/workflow/definition.json  the governed definition as plain data, versioned (read-only; for checking a
                           separately hosted copy against this one)

Office pages: behind the office sign-in and the field-only wall (a Field sign-in uses /field/workflow).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from app.workflow_map import definition as D
from app.workflow_map.build import build
from app.workflow_map.pages import office_viewer

workflow_map_bp = Blueprint("workflow_map", __name__, url_prefix="/workflow")


@workflow_map_bp.route("")
def contractor():
    viewer = office_viewer(request.args.get("project_id", type=int))
    wf = build(D.MAP_CONTRACTOR, viewer, current=request.args.get("stage"), stage_endpoint="workflow_map.contractor")
    return render_template("workflow_map/office.html", wf=wf)


@workflow_map_bp.route("/definition.json")
def definition_json():
    response = jsonify(D.export())
    response.headers["Cache-Control"] = "no-store"
    return response
