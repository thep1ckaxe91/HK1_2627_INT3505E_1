from jsonschema import validate, ValidationError
from flask import request, jsonify, Blueprint
from sqlalchemy import select, func, tuple_
from models import Book, Author, Category, BookAuthor, db
import json
import os
import base64

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "schemas", "book.json")))

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

# --- Lab 2: Sort whitelist, pagination helpers ---

SORT_WHITELIST = {
    "id": Book.id,
    "price": Book.price_vnd,
    "title": Book.title,
    "stock": Book.stock,
}

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _parse_sort(raw):
    """Parse multi-key sort string like '-price,title'.
    Returns list of SQLAlchemy order_by clauses, the primary sort column,
    and whether primary is descending. Returns error tuple on bad input."""
    keys = []
    primary_col = None
    primary_desc = False
    for i, s in enumerate(raw.split(",")):
        s = s.strip()
        if not s:
            continue
        desc = s.startswith("-")
        name = s.lstrip("-")
        if name not in SORT_WHITELIST:
            return None, None, None, f"unknown sort key: {name}"
        col = SORT_WHITELIST[name]
        keys.append(col.desc() if desc else col.asc())
        if i == 0:
            primary_col = col
            primary_desc = desc
    # Always tie-break with id
    if primary_col is not None:
        id_already = any(name == "id" for s in raw.split(",") if (name := s.strip().lstrip("-")))
        if not id_already:
            keys.append(Book.id.desc() if primary_desc else Book.id.asc())
    else:
        # Default sort
        keys = [Book.id.desc()]
        primary_col = Book.id
        primary_desc = True
    return keys, primary_col, primary_desc, None


def _encode_cursor(data):
    return base64.urlsafe_b64encode(
        json.dumps(data).encode()
    ).decode().rstrip("=")


def _decode_cursor(raw):
    pad = "=" * (-len(raw) % 4)
    return json.loads(base64.urlsafe_b64decode(raw + pad))


def _offset_pagination(q, limit):
    """Offset/limit pagination strategy."""
    offset = request.args.get("offset", 0, type=int)
    total = db.session.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.session.scalars(q.offset(offset).limit(limit)).all()
    return jsonify({
        "data": [b.to_dict() for b in rows],
        "pagination": {
            "strategy": "offset",
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_next": offset + limit < total,
        }
    })


def _cursor_pagination(q, limit, sort_raw, primary_col, primary_desc):
    """Cursor-based pagination strategy with composite (sort_value, id) cursor."""
    cursor_raw = request.args.get("cursor")
    if cursor_raw:
        try:
            c = _decode_cursor(cursor_raw)
        except Exception:
            return jsonify({"error": "bad_cursor", "message": "Invalid cursor"}), 400
        if c.get("s") != sort_raw:
            return jsonify({"error": "sort_changed", "message": "Sort changed since cursor was issued"}), 400
        v, i = c["v"], c["i"]
        op = "<" if primary_desc else ">"
        condition = tuple_(primary_col, Book.id).op(op)((v, i))
        q = q.filter(condition)

    rows = db.session.scalars(q.limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = None
    if rows and has_more:
        last = rows[-1]
        next_cursor = _encode_cursor({
            "s": sort_raw,
            "v": getattr(last, primary_col.key),
            "i": last.id,
        })

    return jsonify({
        "data": [b.to_dict() for b in rows],
        "pagination": {
            "strategy": "cursor",
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    })


@bp.get("")
def list_books():
    """Lab 2: list with dual pagination (offset/cursor), genre filter, multi-key sort.

    Query params:
      ?strategy=offset|cursor  (default: cursor)
      ?sort=-price,title       (multi-key, - for desc, whitelist enforced)
      ?genre=<slug>            (filter by category slug)
      ?limit=20                (max 100)
      ?offset=0                (offset strategy only)
      ?cursor=<token>          (cursor strategy only)
    """
    strategy = request.args.get("strategy", "cursor")
    if strategy not in ("offset", "cursor"):
        return jsonify({"error": "bad_request", "message": "strategy must be 'offset' or 'cursor'"}), 400

    limit = min(request.args.get("limit", DEFAULT_LIMIT, type=int), MAX_LIMIT)
    sort_raw = request.args.get("sort", "-id")

    order_clauses, primary_col, primary_desc, err = _parse_sort(sort_raw)
    if err:
        return jsonify({"error": "bad_sort", "message": err}), 400

    q = select(Book).order_by(*order_clauses)

    # Genre filter (by category slug)
    genre = request.args.get("genre")
    if genre:
        q = q.join(Category, Book.category_id == Category.id).filter(Category.slug == genre)

    if strategy == "offset":
        return _offset_pagination(q, limit)
    else:
        return _cursor_pagination(q, limit, sort_raw, primary_col, primary_desc)


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