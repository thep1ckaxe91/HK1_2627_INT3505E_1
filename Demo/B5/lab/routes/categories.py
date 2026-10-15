from flask import request, jsonify, Blueprint
from models import Category, db

bp = Blueprint("categories", __name__, url_prefix="/api/v1/categories")


@bp.get("")
def list_categories():
    rows = db.session.query(Category).order_by(Category.id).all()
    return jsonify([c.to_dict() for c in rows])


@bp.get("/<int:cat_id>")
def get_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": "not_found"}), 404
    return jsonify(cat.to_dict())


@bp.post("")
def create_category():
    req = request.get_json(silent=True) or {}
    if "name" not in req or "slug" not in req:
        return jsonify({"error": "bad_request", "message": "name and slug required"}), 400
    cat = Category(name=req["name"], slug=req["slug"])
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@bp.put("/<int:cat_id>")
def update_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": "not_found"}), 404
    req = request.get_json(silent=True) or {}
    if "name" in req:
        cat.name = req["name"]
    if "slug" in req:
        cat.slug = req["slug"]
    db.session.commit()
    return jsonify(cat.to_dict())


@bp.delete("/<int:cat_id>")
def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(cat)
    db.session.commit()
    return "", 204
