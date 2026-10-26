import datetime
import os
import sys

# Ensure current module directory is in python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_smorest import Api

# In-memory mock token blocklist for revocation demonstrations
revoked_tokens = set()


def create_app(test_config=None):
    app = Flask(__name__)

    # Base configuration
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Social Network Service API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/api-docs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # JWT Configuration (Aligned with Lecture B6 security guidelines)
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY", "b6-super-secure-production-grade-secret-key-at-least-256-bits!"
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=30)
    app.config["JWT_ALGORITHM"] = "HS256"

    # OpenAPI Security Schemes Configuration
    app.config["API_SPEC_OPTIONS"] = {
        "info": {
            "description": (
                "OpenAPI specification for Social Network Service Auth and Post Subsystems.\n"
                "Demonstrates Scope-based Access Control, BOLA prevention, and Token Lifecycles."
            ),
            "contact": {"email": "dev@uet.vnu.edu.vn"},
        },
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Standard Bearer JWT header: 'Authorization: Bearer <token>'",
                },
                "OAuth2": {
                    "type": "oauth2",
                    "description": "OAuth 2.0 Authorization framework with scope delegation",
                    "flows": {
                        "password": {
                            "tokenUrl": "/auth/login",
                            "scopes": {
                                "posts:read": "Read permissions for public and authorized posts",
                                "posts:write": "Create and modify posts",
                            },
                        }
                    },
                },
            }
        },
    }

    if test_config:
        app.config.update(test_config)

    # Initialize Extensions
    jwt = JWTManager(app)
    api = Api(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        return jti in revoked_tokens

    # Blueprint registrations
    from routes.auth import auth_bp
    from routes.posts import posts_bp

    api.register_blueprint(auth_bp)
    api.register_blueprint(posts_bp)

    return app, api


if __name__ == "__main__":
    app, _ = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
