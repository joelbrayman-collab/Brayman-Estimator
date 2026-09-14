"""FG-033 SIGN-C smallest authenticated office executed-artifact retrieval.

Not a signing dashboard. SIGN-D owns Hub experience.
"""

from __future__ import annotations

from flask import Blueprint, Response, abort, g

from app.services.signing import (
    SigningServiceError,
    get_signing_request,
    retrieve_executed_artifact_bytes,
)

signing_office_bp = Blueprint("signing_office", __name__, url_prefix="/signing-requests")


@signing_office_bp.route("/<int:request_id>/executed", methods=["GET"])
def download_executed(request_id):
    organization_id = getattr(g, "organization_id", None)
    if not organization_id:
        abort(404)
    try:
        pdf = retrieve_executed_artifact_bytes(request_id, organization_id)
        request = get_signing_request(request_id, organization_id)
    except SigningServiceError:
        abort(404)
    filename = f"{request.request_number}-executed.pdf"
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
