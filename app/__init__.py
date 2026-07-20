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

    if config:
        app.config.update(config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models
    from app.routes.assemblies import assemblies_bp
    from app.routes.clients import clients_bp
    from app.routes.cost_library import cost_library_bp
    from app.routes.main import main_bp
    from app.routes.projects import projects_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(cost_library_bp)
    app.register_blueprint(assemblies_bp)

    return app
