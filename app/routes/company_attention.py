"""FG-035 PERF-C Company Attention office surface.

Requires COMPANY_MANAGEMENT. Informational only. No mutation.
"""

from flask import Blueprint, render_template

from app.services.access_domains import (
    ACCESS_DOMAIN_COMPANY_MANAGEMENT,
    require_access_domain,
)
from app.services.company_attention import assemble_company_attention
from app.services.organizations import get_current_organization_id

company_attention_bp = Blueprint(
    "company_attention", __name__, url_prefix="/company-attention"
)


@company_attention_bp.route("")
def index():
    gate = require_access_domain(ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    if gate is not None:
        return gate
    view = assemble_company_attention(get_current_organization_id())
    return render_template("company_attention/index.html", view=view)
