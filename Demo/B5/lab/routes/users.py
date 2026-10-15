from flask import request, jsonify, Blueprint
from models import User, db

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@bp.get("")
def list_users():
    rows = db.session.query(User).order_by(User.id).all()
    return jsonify([u.to_dict() for u in rows])


@bp.get("/<int:user_id>")
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404
    return jsonify(user.to_dict())


@bp.post("")
def create_user():
    req = request.get_json(silent=True) or {}
    if "email" not in req or "display_name" not in req:
        return jsonify({"error": "bad_request", "message": "email and display_name required"}), 400
    user = User(email=req["email"], display_name=req["display_name"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201
