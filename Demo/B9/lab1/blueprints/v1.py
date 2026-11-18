from datetime import datetime, timezone
from email.utils import format_datetime
from flask import Blueprint
from .users_data import get_user

bp = Blueprint("v1", __name__)
users_bp = Blueprint("users", __name__, url_prefix="/users")

V1_SUNSET = format_datetime(
    datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    usegmt=True,
)


@users_bp.route("/<int:uid>", methods=["GET"])
def get(uid: int):
    """Fetch user with legacy full_name schema."""
    u = get_user(uid)
    if not u:
        return {"error": "not found"}, 404
    return {
        "id": uid,
        "full_name": f"{u['first_name']} {u['last_name']}",
        "email": u["email"],
    }, 200


@bp.after_request
def add_sunset_headers(response):
    """Attach RFC 8594 Sunset and deprecation headers to all v1 responses."""
    response.headers["Sunset"] = V1_SUNSET
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/v2/users>; rel="successor-version"'
    return response


bp.register_blueprint(users_bp)
