from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def create_app(config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "development-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///brayman_estimator.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PLAN_UPLOAD_MAX_BYTES"] = 25 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_MAX_BYTES"] = 25 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_ZIP_MAX_UNCOMPRESSED"] = 80 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_ZIP_MAX_MEMBER"] = 40 * 1024 * 1024
    app.config["HISTORICAL_UPLOAD_ZIP_MAX_FILES"] = 200
    app.config["HISTORICAL_UPLOAD_ACTOR"] = "Joel Brayman"

    if config:
        app.config.update(config)

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
    from app.project_controls import project_controls_bp
    from app.plan_intelligence import plan_intelligence_bp

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
    app.register_blueprint(project_controls_bp)
    app.register_blueprint(plan_intelligence_bp)

    from app.shell import register_shell_context

    register_shell_context(app)

    return app
