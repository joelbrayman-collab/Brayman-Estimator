from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.services.brand_logo_storage import BrandLogoStorageError, max_logo_bytes
from app.services.brand_profile import (
    BrandProfileServiceError,
    brand_logo_filesystem_path,
    brand_logo_mimetype,
    brand_render_context_from_profile,
    ensure_current_brand_profile,
    get_current_brand_profile,
    save_brand_profile,
)
from app.services.organizations import get_current_organization_id

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def _form_values(profile=None):
    if request.method == "POST":
        return {
            "legal_name": request.form.get("legal_name", "").strip(),
            "customer_facing_name": request.form.get(
                "customer_facing_name", ""
            ).strip(),
            "address": request.form.get("address", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "email": request.form.get("email", "").strip(),
            "website": request.form.get("website", "").strip(),
            "primary_color": request.form.get("primary_color", "").strip(),
            "accent_color": request.form.get("accent_color", "").strip(),
        }
    if profile is None:
        return {
            "legal_name": "",
            "customer_facing_name": "",
            "address": "",
            "phone": "",
            "email": "",
            "website": "",
            "primary_color": "",
            "accent_color": "",
        }
    return {
        "legal_name": profile.legal_name or "",
        "customer_facing_name": profile.customer_facing_name or "",
        "address": profile.address or "",
        "phone": profile.phone or "",
        "email": profile.email or "",
        "website": profile.website or "",
        "primary_color": profile.primary_color or "",
        "accent_color": profile.accent_color or "",
    }


@settings_bp.route("/")
@settings_bp.route("")
def settings_index():
    return redirect(url_for("settings.brand_profile"))


@settings_bp.route("/brand-profile", methods=["GET", "POST"])
def brand_profile():
    org_id = get_current_organization_id()
    try:
        profile = ensure_current_brand_profile(org_id, commit=True)
    except BrandProfileServiceError as exc:
        flash(str(exc), "error")
        profile = get_current_brand_profile(org_id)

    if request.method == "POST":
        form = _form_values()
        upload = request.files.get("logo")
        logo_bytes = None
        logo_filename = None
        if upload and upload.filename:
            logo_filename = upload.filename
            logo_bytes = upload.read()
        try:
            profile = save_brand_profile(
                org_id,
                legal_name=form["legal_name"],
                customer_facing_name=form["customer_facing_name"],
                address=form["address"],
                phone=form["phone"],
                email=form["email"],
                website=form["website"],
                primary_color=form["primary_color"],
                accent_color=form["accent_color"],
                logo_bytes=logo_bytes,
                logo_filename=logo_filename,
                commit=True,
            )
            flash("Brand Profile saved.", "success")
            return redirect(url_for("settings.brand_profile"))
        except (BrandProfileServiceError, BrandLogoStorageError) as exc:
            flash(str(exc), "error")
            return render_template(
                "settings/brand_profile.html",
                form=form,
                profile=profile,
                max_logo_bytes=max_logo_bytes(),
            )

    form = _form_values(profile)
    return render_template(
        "settings/brand_profile.html",
        form=form,
        profile=profile,
        max_logo_bytes=max_logo_bytes(),
    )


@settings_bp.route("/brand-logo")
def current_brand_logo():
    org_id = get_current_organization_id()
    try:
        profile = ensure_current_brand_profile(org_id, commit=True)
    except BrandProfileServiceError:
        abort(404)
    if profile.organization_id != org_id:
        abort(404)
    context = brand_render_context_from_profile(profile)
    path = brand_logo_filesystem_path(context)
    if path is None:
        abort(404)
    return send_file(
        path,
        mimetype=brand_logo_mimetype(context),
        as_attachment=False,
        max_age=0,
    )
