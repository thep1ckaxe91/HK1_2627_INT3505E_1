from flask.views import MethodView
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_smorest import Blueprint, abort

from schemas.error import ErrorResponseSchema, ValidationErrorSchema
from schemas.post import PostResponseSchema

posts_bp = Blueprint("posts", "posts", url_prefix="/posts", description="Post management operations")

# Mock post database
MOCK_POSTS = {
    1: {
        "id": 1,
        "author_id": "1",  # Alice
        "title": "Welcome to Service-Oriented Architecture (B6)",
        "content": "Designing bulletproof APIs with OpenAPI, JWT, and fine-grained scopes.",
        "is_private": False,
        "created_at": "2026-10-27T00:00:00Z",
    },
    2: {
        "id": 2,
        "author_id": "1",  # Alice
        "title": "Alice's Secret Journal",
        "content": "Confidential post containing internal architecture notes.",
        "is_private": True,
        "created_at": "2026-10-27T00:01:00Z",
    },
    3: {
        "id": 3,
        "author_id": "2",  # Bob
        "title": "Bob's Public Post",
        "content": "OpenAPI specifications eliminate documentation drift.",
        "is_private": False,
        "created_at": "2026-10-27T00:02:00Z",
    },
}


@posts_bp.route("/<int:id>")
class PostByIdResource(MethodView):
    """Retrieve post by identifier with scope and BOLA checks."""

    @jwt_required()
    @posts_bp.response(200, PostResponseSchema, description="Post retrieved successfully.")
    @posts_bp.alt_response(401, schema=ErrorResponseSchema, description="Missing or invalid Bearer access token.")
    @posts_bp.alt_response(
        403,
        schema=ErrorResponseSchema,
        description="Forbidden. Insufficient scope ('posts:read') or BOLA violation on private post.",
    )
    @posts_bp.alt_response(404, schema=ErrorResponseSchema, description="Post not found.")
    @posts_bp.alt_response(422, schema=ValidationErrorSchema, description="Validation error on post ID parameter.")
    @posts_bp.doc(
        summary="Get Post by ID",
        description=(
            "### Specification Details\n"
            "- **Scope Required**: `posts:read` (Bearer access token containing `posts:read` scope).\n"
            "- **Potential Errors**:\n"
            "  - `401 Unauthorized`: Missing, expired, or signature-invalid Bearer token.\n"
            "  - `403 Forbidden`: Token lacks `posts:read` scope OR caller fails object-level ownership check (BOLA / OWASP API1:2023) on private post.\n"
            "  - `404 Not Found`: Post with requested ID does not exist.\n"
            "  - `422 Unprocessable Entity`: Invalid post ID format.\n"
            "- **Status Codes**:\n"
            "  - `200 OK`: Post metadata and body.\n"
            "  - `401`, `403`, `404`, `422`."
        ),
        security=[{"BearerAuth": []}, {"OAuth2": ["posts:read"]}],
    )
    def get(self, id: int):
        claims = get_jwt()
        caller_id = get_jwt_identity()

        # 1. Scope Verification (AuthZ)
        granted_scopes = claims.get("scopes", [])
        if "posts:read" not in granted_scopes:
            abort(403, message="Insufficient scope: 'posts:read' is required to access posts.")

        # 2. Resource Lookup
        post = MOCK_POSTS.get(id)
        if not post:
            abort(404, message=f"Post with ID {id} was not found.")

        # 3. Object-Level Authorization (BOLA Defense - Slide 24-26)
        # Private posts are only viewable by their author or an administrator
        if post["is_private"]:
            is_author = str(post["author_id"]) == str(caller_id)
            is_admin = claims.get("role") == "admin"
            if not (is_author or is_admin):
                abort(
                    403,
                    message="Forbidden: You do not have permission to view this private post (BOLA violation).",
                )

        return post
