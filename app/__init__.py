import os
import re
import tempfile

from flask import Flask, abort, g, request, send_from_directory
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

DEVELOPMENT_SECRET_KEY = "development-secret-key"
TESTING_FALLBACK_SECRET_KEY = "test-secret-key"


class SecretKeyConfigError(RuntimeError):
    """Non-development SECRET_KEY is missing or is the committed development value."""


def _env_flag(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def _apply_secret_key(app: Flask) -> None:
    testing = bool(app.config.get("TESTING"))
    debug = bool(app.debug) or bool(app.config.get("DEBUG")) or _env_flag("FLASK_DEBUG")
    secret = app.config.get("SECRET_KEY")
    if secret is None or secret == "":
        env_secret = os.environ.get("SECRET_KEY")
        secret = env_secret if env_secret else None

    if testing:
        app.config["SECRET_KEY"] = secret or TESTING_FALLBACK_SECRET_KEY
        return

    if debug:
        app.config["SECRET_KEY"] = secret or DEVELOPMENT_SECRET_KEY
        return

    if not secret:
        raise SecretKeyConfigError(
            "SECRET_KEY must be supplied for non-development operation."
        )
    if secret == DEVELOPMENT_SECRET_KEY:
        raise SecretKeyConfigError(
            "SECRET_KEY must not be the committed development secret "
            "in non-development operation."
        )
    app.config["SECRET_KEY"] = secret


_BUILD_API_POST_RE = re.compile(
    r"^/api/v1/projects/\d+/field-events"
    r"(/\d+/(originals|derived/\d+/(confirm|reject)))?$"
)


def _is_api_request() -> bool:
    path = request.path or ""
    return path == "/api" or path.startswith("/api/")


def _is_allowed_build_api_post() -> bool:
    if request.method != "POST":
        return False
    return bool(_BUILD_API_POST_RE.fullmatch(request.path or ""))


def _register_office_auth(app: Flask) -> None:
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access the office application."

    @login_manager.user_loader
    def load_user(user_id):
        from app.services.auth import load_user_for_session

        return load_user_for_session(user_id)

    @app.before_request
    def reject_api_mutating_methods():
        from app.services.shared_api import ERROR_METHOD_NOT_ALLOWED, api_error

        if _is_api_request() and request.method not in ("GET", "HEAD", "OPTIONS"):
            if _is_allowed_build_api_post():
                return None
            return api_error(ERROR_METHOD_NOT_ALLOWED, 405)
        return None

    csrf.init_app(app)

    from app.cli.auth import auth_cli
    from app.cli.build import build_cli
    from app.cli.legal_content import legal_content_cli
    from app.cli.signing import signing_cli
    from app.routes.auth import auth_bp

    app.register_blueprint(auth_bp)
    app.cli.add_command(auth_cli)
    app.cli.add_command(build_cli)
    app.cli.add_command(legal_content_cli)
    app.cli.add_command(signing_cli)

    @app.before_request
    def protect_office_routes():
        from app.services.organizations import (
            OrganizationAccessError,
            resolve_membership_organization_id,
        )
        from app.services.shared_api import (
            ERROR_AUTHENTICATION_REQUIRED,
            ERROR_ORGANIZATION_CONTEXT,
            api_error,
        )

        endpoint = request.endpoint
        if request.path == "/favicon.ico" or endpoint in (
            "static",
            "auth.login",
            "auth.logout",
            "auth.forgot_password",
            "auth.forgot_password_sent",
            "auth.reset_password",
            "auth.reset_password_complete",
            "favicon",
        ):
            return None
        if endpoint is not None and endpoint.startswith("sign."):
            return None
        if _is_api_request():
            if not current_user.is_authenticated:
                return api_error(ERROR_AUTHENTICATION_REQUIRED, 401)
            try:
                g.organization_id = resolve_membership_organization_id(current_user)
            except OrganizationAccessError:
                return api_error(ERROR_ORGANIZATION_CONTEXT, 403)
            return None
        if endpoint is None:
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            return None
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        try:
            g.organization_id = resolve_membership_organization_id(current_user)
        except OrganizationAccessError:
            abort(403)
        return None

    @app.errorhandler(404)
    def handle_404(err):
        from app.services.shared_api import ERROR_NOT_FOUND, api_error

        if _is_api_request():
            return api_error(ERROR_NOT_FOUND, 404)
        return err.get_response()

    @app.errorhandler(405)
    def handle_405(err):
        from app.services.shared_api import ERROR_METHOD_NOT_ALLOWED, api_error

        if _is_api_request():
            return api_error(ERROR_METHOD_NOT_ALLOWED, 405)
        return err.get_response()


def create_app(config=None):
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///brayman_estimator.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PLAN_UPLOAD_MAX_BYTES"] = 25 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_MAX_BYTES"] = 25 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_ZIP_MAX_UNCOMPRESSED"] = 80 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_ZIP_MAX_MEMBER"] = 40 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_ZIP_MAX_FILES"] = 200
    app.config["HISTORICAL_UPLOAD_ACTOR"] = "Joel Brayman"
    app.config["BRAND_LOGO_MAX_BYTES"] = 5 * 1024 * 1024
    app.config["BUILD_ORIGINAL_MAX_BYTES"] = 25 * 1024 * 1024

    if config:
        app.config.update(config)

    _apply_secret_key(app)

    if app.config.get("TESTING"):
        app.config.setdefault("WTF_CSRF_ENABLED", False)

    if app.config.get("TESTING") and not app.config.get("BRAND_LOGO_ROOT"):
        app.config["BRAND_LOGO_ROOT"] = tempfile.mkdtemp(prefix="calibai-brand-logos-")
    if app.config.get("TESTING") and not app.config.get("BUILD_ORIGINAL_ROOT"):
        app.config["BUILD_ORIGINAL_ROOT"] = tempfile.mkdtemp(
            prefix="calibai-build-originals-"
        )
    if app.config.get("TESTING") and not app.config.get("BUILD_RENDITION_ROOT"):
        app.config["BUILD_RENDITION_ROOT"] = tempfile.mkdtemp(
            prefix="calibai-build-renditions-"
        )
    if app.config.get("TESTING") and not app.config.get("QUICKBOOKS_PACKAGE_ROOT"):
        app.config["QUICKBOOKS_PACKAGE_ROOT"] = tempfile.mkdtemp(
            prefix="calibai-quickbooks-packages-"
        )
    if app.config.get("TESTING") and not app.config.get("CONTRACT_ARTIFACT_ROOT"):
        app.config["CONTRACT_ARTIFACT_ROOT"] = tempfile.mkdtemp(
            prefix="calibai-generated-contracts-"
        )
    if app.config.get("TESTING") and not app.config.get("SIGNING_ARTIFACT_ROOT"):
        app.config["SIGNING_ARTIFACT_ROOT"] = tempfile.mkdtemp(
            prefix="calibai-signing-artifacts-"
        )
    if app.config.get("TESTING") and not app.config.get("MAIL_CAPTURE_ROOT"):
        app.config["MAIL_CAPTURE_ROOT"] = tempfile.mkdtemp(prefix="calibai-mail-capture-")
    app.config.setdefault("SIGNING_TOKEN_FAIL_LIMIT", 8)
    app.config.setdefault("SIGNING_TOKEN_FAIL_WINDOW_SECONDS", 900)
    app.config.setdefault("SIGNING_SOFFICE_PATH", None)
    app.config.setdefault("SIGNING_SOFFICE_TIMEOUT_SECONDS", 60)
    app.config.setdefault("SIGNING_DOCX_TO_PDF", None)
    app.config.setdefault(
        "TRANSACTIONAL_EMAIL_PROVIDER",
        os.environ.get("TRANSACTIONAL_EMAIL_PROVIDER") or "local",
    )
    app.config.setdefault("POSTMARK_SERVER_TOKEN", os.environ.get("POSTMARK_SERVER_TOKEN") or "")
    app.config.setdefault(
        "TRANSACTIONAL_FROM_EMAIL",
        os.environ.get("TRANSACTIONAL_FROM_EMAIL") or "noreply@localhost",
    )
    app.config.setdefault(
        "TRANSACTIONAL_FROM_NAME",
        os.environ.get("TRANSACTIONAL_FROM_NAME") or "CalibraytAI",
    )
    app.config.setdefault("TRANSACTIONAL_REPLY_TO", os.environ.get("TRANSACTIONAL_REPLY_TO") or "")
    app.config.setdefault(
        "TRANSACTIONAL_UAT_ALLOWLIST",
        os.environ.get("TRANSACTIONAL_UAT_ALLOWLIST") or "",
    )
    app.config.setdefault("PUBLIC_BASE_URL", os.environ.get("PUBLIC_BASE_URL") or "")
    app.config.setdefault("TRANSACTIONAL_EMAIL_TRANSPORT", None)
    app.config.setdefault("POSTMARK_HTTP_SEND", None)
    app.config.setdefault("PASSWORD_RESET_TOKEN_TTL_SECONDS", 3600)
    app.config.setdefault("PASSWORD_RESET_REQUEST_IP_LIMIT", 5)
    app.config.setdefault("PASSWORD_RESET_REQUEST_IP_WINDOW_SECONDS", 3600)
    app.config.setdefault("PASSWORD_RESET_REQUEST_EMAIL_LIMIT", 3)
    app.config.setdefault("PASSWORD_RESET_REQUEST_EMAIL_WINDOW_SECONDS", 3600)
    app.config.setdefault("PASSWORD_RESET_PRESENT_FAIL_LIMIT", 8)
    app.config.setdefault("PASSWORD_RESET_PRESENT_FAIL_WINDOW_SECONDS", 900)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models
    from app.routes.assemblies import assemblies_bp
    from app.routes.clients import clients_bp
    from app.routes.cost_library import cost_library_bp
    from app.routes.estimates import estimates_bp
    from app.routes.main import main_bp
    from app.routes.projects import projects_bp
    from app.routes.proposal_templates import proposal_templates_bp
    from app.routes.proposals import proposals_bp
    from app.routes.historical_estimates import bp as historical_estimates_bp
    from app.routes.labour_engine import labour_engine_bp
    from app.routes.pricing_engine import pricing_engine_bp
    from app.routes.material_catalogue import material_catalogue_bp
    from app.project_controls import project_controls_bp
    from app.plan_intelligence import plan_intelligence_bp
    from app.routes.settings import settings_bp
    from app.routes.api_v1 import api_v1_bp
    from app.routes.build import build_bp
    from app.routes.field import field_bp
    from app.routes.supplier_package import supplier_package_bp
    from app.routes.scope_delivery import scope_delivery_bp
    from app.routes.estimate_quickbooks import estimate_quickbooks_bp
    from app.routes.sign import sign_bp
    from app.routes.signing import signing_office_bp
    from app.routes.work_structure import work_structure_bp
    from app.routes.time_entry import time_entry_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(cost_library_bp)
    app.register_blueprint(assemblies_bp)
    app.register_blueprint(estimates_bp)
    app.register_blueprint(proposal_templates_bp)
    app.register_blueprint(proposals_bp)
    app.register_blueprint(historical_estimates_bp)
    app.register_blueprint(labour_engine_bp)
    app.register_blueprint(pricing_engine_bp)
    app.register_blueprint(material_catalogue_bp)
    app.register_blueprint(project_controls_bp)
    app.register_blueprint(plan_intelligence_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(build_bp)
    app.register_blueprint(field_bp)
    app.register_blueprint(supplier_package_bp)
    app.register_blueprint(scope_delivery_bp)
    app.register_blueprint(estimate_quickbooks_bp)
    app.register_blueprint(sign_bp)
    app.register_blueprint(signing_office_bp)
    app.register_blueprint(work_structure_bp)
    app.register_blueprint(time_entry_bp)

    @app.route("/favicon.ico")
    def favicon():
        # Safari requests this while showing a /sign PDF. It must not 302 to office login.
        return send_from_directory(
            os.path.join(app.static_folder, "branding"),
            "calibraytai-logo-v2.png",
            mimetype="image/png",
        )

    _register_office_auth(app)

    from app.shell import register_shell_context

    register_shell_context(app)

    return app
