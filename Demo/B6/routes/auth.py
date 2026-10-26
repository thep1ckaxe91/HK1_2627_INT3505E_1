import hashlib
import hmac
from flask.views import MethodView
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_smorest import Blueprint, abort

from schemas.auth import LoginRequestSchema, LoginResponseSchema
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
