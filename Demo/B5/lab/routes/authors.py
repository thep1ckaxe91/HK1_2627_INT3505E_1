from flask import request, jsonify, Blueprint
from models import Author, db

bp = Blueprint("authors", __name__, url_prefix="/api/v1/authors")


@bp.get("")
def list_authors():
    rows = db.session.query(Author).order_by(Author.id).all()
    return jsonify([a.to_dict() for a in rows])


@bp.get("/<int:author_id>")
def get_author(author_id):
    author = db.session.get(Author, author_id)
    if not author:
        return jsonify({"error": "not_found"}), 404
    return jsonify(author.to_dict())


@bp.post("")
def create_author():
    req = request.get_json(silent=True) or {}
    if "name" not in req:
        return jsonify({"error": "bad_request", "message": "name required"}), 400
    author = Author(name=req["name"], bio=req.get("bio", ""))
    db.session.add(author)
    db.session.commit()
    return jsonify(author.to_dict()), 201


@bp.put("/<int:author_id>")
def update_author(author_id):
    author = db.session.get(Author, author_id)
    if not author:
        return jsonify({"error": "not_found"}), 404
    req = request.get_json(silent=True) or {}
    if "name" in req:
        author.name = req["name"]
    if "bio" in req:
        author.bio = req["bio"]
    db.session.commit()
    return jsonify(author.to_dict())


@bp.delete("/<int:author_id>")
def delete_author(author_id):
    author = db.session.get(Author, author_id)
    if not author:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(author)
    db.session.commit()
    return "", 204


# /authors/{id}/books — list books by this author
@bp.get("/<int:author_id>/books")
def list_author_books(author_id):
    author = db.session.get(Author, author_id)
    if not author:
        return jsonify({"error": "not_found"}), 404
    return jsonify([b.to_dict() for b in author.books])
