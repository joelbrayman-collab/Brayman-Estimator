"""Server-to-server API for the office Mac's Sync export puller (Joel, 16 Nov 2026).

PUBLIC (security route sweep): no sign-in, no CSRF token. Every request must carry `Authorization: Bearer <token>`
matching PROJECT_EXPORT_TOKEN (compared in constant time); 404 while that is not configured, 401 otherwise. It only
lists queued files, hands out their bytes, and records the Mac's result (done with the written file's hash, or failed).
"""

import hmac
import os

from flask import Blueprint, Response, abort, jsonify, request

from app import csrf
from app.models import Project
from app.models.estimating_assistant import ProjectExport
from app.services import project_export as PX
from app.services.organizations import DEFAULT_ORGANIZATION_ID

project_export_api_bp = Blueprint("project_export_api", __name__)


def _guard():
    token = os.environ.get("PROJECT_EXPORT_TOKEN", "")
    if not token:
        abort(404)
    sent = (request.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(sent.encode(), token.encode()):
        abort(Response("", status=401))


def _row(export_id):
    row = ProjectExport.query.filter_by(id=export_id, organization_id=DEFAULT_ORGANIZATION_ID).first()
    if row is None:
        abort(404)
    return row


@project_export_api_bp.route("/sync-export/pending")
@csrf.exempt
def pending():
    _guard()
    out = []
    for row in PX.pending(DEFAULT_ORGANIZATION_ID):
        project = Project.query.get(row.project_id)
        customer = getattr(getattr(project, "client", None), "name", None) or "Customer"
        out.append({"id": row.id, "target_name": row.target_name, "sha256": row.sha256,
                    "folder": PX.FOLDERS[row.folder_code],
                    "project_folder": f"{project.project_number} - {customer}"})
    return jsonify(out)


@project_export_api_bp.route("/sync-export/<int:export_id>/file")
@csrf.exempt
def file(export_id):
    _guard()
    return Response(PX.read(_row(export_id)), mimetype="application/octet-stream")


@project_export_api_bp.route("/sync-export/<int:export_id>/done", methods=["POST"])
@csrf.exempt
def done(export_id):
    _guard()
    try:
        PX.mark_exported(_row(export_id), sha256=(request.get_json(silent=True) or {}).get("sha256", ""))
    except PX.ExportError:
        return jsonify({"result": "hash mismatch"}), 409
    return jsonify({"result": "exported"})


@project_export_api_bp.route("/sync-export/<int:export_id>/failed", methods=["POST"])
@csrf.exempt
def failed(export_id):
    _guard()
    PX.mark_failed(_row(export_id), (request.get_json(silent=True) or {}).get("error", ""))
    return jsonify({"result": "recorded"})
