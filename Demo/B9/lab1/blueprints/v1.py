from flask import Blueprint
from .users_data import get_user
bp = Blueprint("v1", __name__, url_prefix="/users")

@bp.route("/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u: 
        return {"error": "not found"}, 404
    return {
        "id": uid,
        "full_name": f"{u['f']} {u['l']}",
        "email": u["email"]
    }, 200

