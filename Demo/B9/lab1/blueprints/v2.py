from flask import Blueprint, request
from .users_data import create_user, get_user

bp = Blueprint("v2", __name__)
users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/<int:uid>", methods=["GET"])
def get(uid: int):
    """Fetch user with split first_name/last_name schema."""
    u = get_user(uid)
    if not u:
        return {"error": "not found"}, 404
    return {
        "id": uid,
        "first_name": u["first_name"],
        "last_name": u["last_name"],
        "email": u["email"],
    }, 200


@users_bp.route("", methods=["POST"])
@users_bp.route("/", methods=["POST"])
def create():
    """Create a new user under the v2 schema."""
    data = request.get_json(silent=True) or {}
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip()
    if not first_name or not last_name or not email:
        return {"error": "first_name, last_name, and email are required"}, 400

    uid, user = create_user(first_name, last_name, email)
    return {
        "id": uid,
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
    }, 201


bp.register_blueprint(users_bp)
