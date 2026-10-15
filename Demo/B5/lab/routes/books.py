from jsonschema import validate, ValidationError
from flask import request, jsonify, Blueprint
from models import Book, Author, Category, BookAuthor, db
import json
import os

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "schemas", "book.json")))

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")


@bp.get("")
def list_books():
    """Lab 1: basic list with limit. Lab 2 will add pagination strategies."""
    limit = min(request.args.get("limit", 20, type=int), 100)
    rows = db.session.query(Book).order_by(Book.id.desc()).limit(limit).all()
    return jsonify({
        "data": [b.to_dict() for b in rows],
    })


@bp.get("/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found", "message": f"Book {book_id} not found"}), 404
    return jsonify(book.to_dict())


@bp.post("")
def create_book():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "bad_request", "message": "JSON body required"}), 400
    try:
        validate(payload, SCHEMA)
    except ValidationError as e:
        return jsonify({
            "error": "validation_failed",
            "field": list(e.path),
            "message": e.message,
        }), 400

    # Resolve category
    cat = None
    if "category_id" in payload:
        cat = db.session.get(Category, payload["category_id"])

    book = Book(
        title=payload["title"],
        isbn=payload.get("isbn"),
        price_vnd=payload.get("price", {}).get("amount", 0),
        stock=payload.get("stock", 0),
        category_id=cat.id if cat else None,
    )
    db.session.add(book)
    db.session.flush()  # get book.id

    # Handle authors
    for a_data in payload.get("authors", []):
        author = None
        if "id" in a_data:
            author = db.session.get(Author, a_data["id"])
        if not author and "name" in a_data:
            author = Author(name=a_data["name"])
            db.session.add(author)
            db.session.flush()
        if author:
            ba = BookAuthor(
                book_id=book.id,
                author_id=author.id,
                role=a_data.get("role", "co"),
            )
            db.session.add(ba)

    db.session.commit()
    return jsonify(book.to_dict()), 201


@bp.put("/<int:book_id>")
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found", "message": f"Book {book_id} not found"}), 404
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "bad_request", "message": "JSON body required"}), 400
    if "title" in payload:
        book.title = payload["title"]
    if "isbn" in payload:
        book.isbn = payload["isbn"]
    if "price" in payload:
        book.price_vnd = payload["price"].get("amount", book.price_vnd)
    if "stock" in payload:
        book.stock = payload["stock"]
    if "category_id" in payload:
        book.category_id = payload["category_id"]
    db.session.commit()
    return jsonify(book.to_dict())


@bp.delete("/<int:book_id>")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found", "message": f"Book {book_id} not found"}), 404
    db.session.delete(book)
    db.session.commit()
    return "", 204


# --- Sub-resource: /books/{id}/authors (N:M with metadata) ---

@bp.get("/<int:book_id>/authors")
def list_book_authors(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    rows = (
        db.session.query(Author, BookAuthor.role)
        .join(Author, Author.id == BookAuthor.author_id)
        .filter(BookAuthor.book_id == book_id)
        .all()
    )
    return jsonify([{"id": a.id, "name": a.name, "role": r} for a, r in rows])


@bp.post("/<int:book_id>/authors")
def add_book_author(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    req = request.get_json(silent=True) or {}
    if "author_id" not in req:
        return jsonify({"error": "bad_request", "message": "author_id required"}), 400
    author = db.session.get(Author, req["author_id"])
    if not author:
        return jsonify({"error": "not_found", "message": "Author not found"}), 404
    ba = BookAuthor(
        book_id=book_id,
        author_id=req["author_id"],
        role=req.get("role", "co"),
    )
    db.session.add(ba)
    db.session.commit()
    return jsonify({"id": ba.id, "book_id": book_id, "author_id": author.id, "role": ba.role}), 201


@bp.delete("/<int:book_id>/authors/<int:author_id>")
def remove_book_author(book_id, author_id):
    ba = db.session.query(BookAuthor).filter_by(
        book_id=book_id, author_id=author_id
    ).first()
    if not ba:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(ba)
    db.session.commit()
    return "", 204


# --- Sub-resource: /books/{id}/reviews (1:N strong containment) ---

@bp.get("/<int:book_id>/reviews")
def list_book_reviews(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    from models import Review
    reviews = db.session.query(Review).filter_by(book_id=book_id).all()
    return jsonify([r.to_dict() for r in reviews])


@bp.post("/<int:book_id>/reviews")
def create_book_review(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    req = request.get_json(silent=True) or {}
    if "rating" not in req or "user_id" not in req:
        return jsonify({"error": "bad_request", "message": "rating and user_id required"}), 400
    if not (1 <= req["rating"] <= 5):
        return jsonify({"error": "validation_failed", "message": "rating must be 1-5"}), 400
    from models import Review, User
    user = db.session.get(User, req["user_id"])
    if not user:
        return jsonify({"error": "not_found", "message": "User not found"}), 404
    review = Review(
        rating=req["rating"],
        comment=req.get("comment", ""),
        book_id=book_id,
        user_id=req["user_id"],
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.to_dict()), 201