"""Cal Assistant, Phase 1 — Find It. One read-only GET endpoint. No mutation."""

from flask import Blueprint, jsonify, request

from app.services.cal_find import MAX_QUERY, find

cal_bp = Blueprint("cal_assistant", __name__, url_prefix="/cal")


@cal_bp.route("/find", methods=["GET"])
def find_it():
    query = str(request.args.get("q") or "")[:MAX_QUERY]
    here = str(request.args.get("here") or "")[:500]
    response = jsonify(find(query, here=here))
    response.headers["Cache-Control"] = "no-store"
    return response
