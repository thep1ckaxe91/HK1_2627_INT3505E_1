import hashlib
import hmac
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_smorest import Blueprint, abort

from schemas.auth import (
    LoginRequestSchema,
    LoginResponseSchema,
    TokenRefreshResponseSchema,
)
from schemas.error import ErrorResponseSchema, ValidationErrorSchema

auth_bp = Blueprint("auth", "auth", url_prefix="/auth", description="Authentication operations")

# Predefined mock users: email -> {id, password_hash, scopes, role}
# Passwords hashed with SHA256 for demo (in production Argon2id per slide 27)
MOCK_USERS = {
    "alice@vnu.edu.vn": {
        "id": "1",
        "password_hash": hashlib.sha256(b"alice123").hexdigest(),
        "scopes": ["posts:read", "posts:write"],
        "role": "author",
    },
    "bob@vnu.edu.vn": {
        "id": "2",
        "password_hash": hashlib.sha256(b"bob123").hexdigest(),
        "scopes": ["posts:read"],
        "role": "viewer",
    },
}


@auth_bp.route("/login")
class LoginResource(MethodView):
    """User authentication and JWT token issuance endpoint."""

    @auth_bp.arguments(LoginRequestSchema)
    @auth_bp.response(200, LoginResponseSchema, description="Login successful. Returns access and refresh JWT tokens.")
    @auth_bp.alt_response(400, schema=ErrorResponseSchema, description="Malformed JSON request.")
    @auth_bp.alt_response(401, schema=ErrorResponseSchema, description="Authentication failed. Invalid email or password.")
    @auth_bp.alt_response(422, schema=ValidationErrorSchema, description="Input validation failure.")
    @auth_bp.alt_response(429, schema=ErrorResponseSchema, description="Too many requests. Rate limit exceeded.")
    @auth_bp.doc(
        summary="User Login",
        description=(
            "### Specification Details\n"
            "- **Scope Required**: `None` (Public authentication boundary).\n"
            "- **Potential Errors**:\n"
            "  - `400 Bad Request`: Malformed JSON or unparseable payload.\n"
            "  - `401 Unauthorized`: Invalid credentials (fail-closed, constant-time compare to mitigate user enumeration).\n"
            "  - `422 Unprocessable Entity`: Schema validation failure (missing required fields or malformed email format).\n"
            "  - `429 Too Many Requests`: Triggered when credential stuffing or brute-force threshold is exceeded.\n"
            "- **Status Codes**:\n"
            "  - `200 OK`: Successful authentication returning short-lived access JWT and long-lived refresh JWT.\n"
            "  - `400`, `401`, `422`, `429`."
        ),
        security=[],
    )
    def post(self, login_data):
        email = login_data.get("email")
        password = login_data.get("password")

        user = MOCK_USERS.get(email)
        # Constant-time comparison to prevent timing attacks (Slide 7, 29)
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        expected_hash = user["password_hash"] if user else "0" * 64

        is_valid = hmac.compare_digest(pwd_hash, expected_hash)
        if not user or not is_valid:
            abort(401, message="Invalid email or password.")

        # Mint tokens
        uid = str(user["id"])
        scopes = user["scopes"]
        access_token = create_access_token(
            identity=uid,
            additional_claims={"scopes": scopes, "role": user["role"]},
        )
        refresh_token = create_refresh_token(
            identity=uid,
            additional_claims={"scopes": ["auth:refresh"]},
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 900,
            "scopes": scopes,
        }


@auth_bp.route("/refresh")
class RefreshResource(MethodView):
    """Token rotation and refresh endpoint."""

    @jwt_required(refresh=True)
    @auth_bp.response(200, TokenRefreshResponseSchema, description="Token refreshed successfully.")
    @auth_bp.alt_response(401, schema=ErrorResponseSchema, description="Missing, invalid, or expired refresh token.")
    @auth_bp.alt_response(403, schema=ErrorResponseSchema, description="Revoked token or insufficient refresh scope.")
    @auth_bp.alt_response(422, schema=ValidationErrorSchema, description="Malformed authorization header.")
    @auth_bp.doc(
        summary="Refresh Access Token",
        description=(
            "### Specification Details\n"
            "- **Scope Required**: `auth:refresh` (Dedicated Refresh Token required; Access Tokens will be rejected).\n"
            "- **Potential Errors**:\n"
            "  - `401 Unauthorized`: Missing Bearer header, expired token, or signature verification failure.\n"
            "  - `403 Forbidden`: Token has been revoked in blocklist or does not contain `auth:refresh` scope.\n"
            "  - `422 Unprocessable Entity`: Malformed token structure or unparseable Bearer format.\n"
            "- **Status Codes**:\n"
            "  - `200 OK`: Newly issued access token.\n"
            "  - `401`, `403`, `422`."
        ),
        security=[{"BearerAuth": []}],
    )
    def post(self):
        identity = get_jwt_identity()
        claims = get_jwt()

        # Scope validation: ensure token carries refresh privilege
        scopes = claims.get("scopes", [])
        if "auth:refresh" not in scopes:
            abort(403, message="Insufficient scope. Dedicated refresh token required.")

        user_scopes = ["posts:read", "posts:write"] if identity == "1" else ["posts:read"]
        role = "author" if identity == "1" else "viewer"

        new_access_token = create_access_token(
            identity=identity,
            additional_claims={"scopes": user_scopes, "role": role},
        )
        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": 900,
        }

