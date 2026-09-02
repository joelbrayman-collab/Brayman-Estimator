import os
import re
import tempfile

from flask import Flask, abort, g, request
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
        from app.models.user import User

        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            return None
        user = db.session.get(User, uid)
        if user is None or not user.is_active:
            return None
        return user

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
    from app.routes.auth import auth_bp

    app.register_blueprint(auth_bp)
    app.cli.add_command(auth_cli)
    app.cli.add_command(build_cli)

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
        if endpoint in ("static", "auth.login", "auth.logout"):
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

    _register_office_auth(app)

    from app.shell import register_shell_context

    register_shell_context(app)

    return app
