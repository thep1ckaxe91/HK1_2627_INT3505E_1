import os
from pathlib import Path
from typing import Any, Optional
import connexion

from product_api.config import DefaultConfig
from product_api.extensions import db, migrate
from product_api.errors import register_error_handlers
from product_api.logging_config import configure_logging
from product_api.api.health import health_bp
import product_api.models  # noqa: F401 - register models on db.metadata


def create_app(config: Optional[Any] = None) -> connexion.FlaskApp:
    """Application factory for Connexion/Flask backend service."""
    # Resolve absolute path to openapi specifications directory
    spec_dir = Path(__file__).resolve().parent.parent.parent / "openapi"

    connexion_app = connexion.FlaskApp(
        __name__,
        specification_dir=str(spec_dir),
    )
    flask_app = connexion_app.app

    # Load configuration hierarchy (DefaultConfig / TestConfig / ProductionConfig)
    cfg = config or os.environ.get("APP_CONFIG", DefaultConfig)
    flask_app.config.from_object(cfg)
    flask_app.config.from_prefixed_env("APP")

    # Bind extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    # Configure structured logging & error handling
    configure_logging(flask_app)
    register_error_handlers(connexion_app)

    # Register core health probes via lightweight Flask Blueprint (Slide 37)
    flask_app.register_blueprint(health_bp)

    # Register modular OpenAPI specs for domain business services
    connexion_app.add_api("products.yaml", base_path="/api/v1", name="products_api", validate_responses=True)
    connexion_app.add_api("orders.yaml", base_path="/api/v1", name="orders_api", validate_responses=True)

    return connexion_app
