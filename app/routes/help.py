"""Help question adapter. Presentation only. No mutation. No second knowledge base."""

from flask import Blueprint, jsonify, request

from app.presentation.help_content import answer_help_question

help_bp = Blueprint("help", __name__, url_prefix="/help")


@help_bp.route("/ask", methods=["POST"])
def ask_help():
    data = request.get_json(silent=True) or {}
    surface = str(data.get("surface") or "").strip()
    key = str(data.get("key") or "").strip()
    question = str(data.get("question") or "").strip()[:400]
    return jsonify(answer_help_question(surface, key, question))
