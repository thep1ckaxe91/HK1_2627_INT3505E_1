from jsonschema import validate, ValidationError
from flask import request, jsonify, Blueprint
from sqlalchemy import select, func, tuple_
from models import Book, Author, Category, BookAuthor, BookCopy, Review, Member, db
import json
import os
import base64

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "schemas", "book.json")))
COPY_SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "schemas", "book_copy.json")))

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

SORT_WHITELIST = {
    "id": Book.id,
    "title": Book.title,
    "published_year": Book.published_year,
    "year": Book.published_year,
    "total_copies": Book.total_copies,
}

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _parse_sort(raw):
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
    if primary_col is not None:
        id_already = any(name == "id" for s in raw.split(",") if (name := s.strip().lstrip("-")))
        if not id_already:
            keys.append(Book.id.desc() if primary_desc else Book.id.asc())
    else:
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


def _offset_pagination(q, limit, fields=None):
    offset = request.args.get("offset", 0, type=int)
    total = db.session.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.session.scalars(q.offset(offset).limit(limit)).all()
    return jsonify({
        "data": [b.to_dict(fields=fields) for b in rows],
        "pagination": {
            "strategy": "offset",
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_next": offset + limit < total,
        }
    })


def _cursor_pagination(q, limit, sort_raw, primary_col, primary_desc, fields=None):
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
        "data": [b.to_dict(fields=fields) for b in rows],
        "pagination": {
            "strategy": "cursor",
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    })


@bp.get("")
def list_books():
    strategy = request.args.get("strategy", "cursor")
    if strategy not in ("offset", "cursor"):
        return jsonify({"error": "bad_request", "message": "strategy must be 'offset' or 'cursor'"}), 400

    limit = min(request.args.get("limit", DEFAULT_LIMIT, type=int), MAX_LIMIT)
    sort_raw = request.args.get("sort", "-id")

    order_clauses, primary_col, primary_desc, err = _parse_sort(sort_raw)
    if err:
        return jsonify({"error": "bad_sort", "message": err}), 400

    q = select(Book).order_by(*order_clauses)

    cat_slug = request.args.get("category") or request.args.get("genre")
    if cat_slug:
        q = q.join(Category, Book.category_id == Category.id).filter(Category.slug == cat_slug)

    year = request.args.get("year", type=int) or request.args.get("published_year", type=int)
    if year:
        q = q.filter(Book.published_year == year)

    fields_raw = request.args.get("fields")
    fields = [f.strip() for f in fields_raw.split(",") if f.strip()] if fields_raw else None

    if strategy == "offset":
        return _offset_pagination(q, limit, fields=fields)
    else:
        return _cursor_pagination(q, limit, sort_raw, primary_col, primary_desc, fields=fields)


@bp.get("/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found", "message": f"Book {book_id} not found"}), 404
    fields_raw = request.args.get("fields")
    fields = [f.strip() for f in fields_raw.split(",") if f.strip()] if fields_raw else None
    return jsonify(book.to_dict(fields=fields))


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

    cat = None
    if "category_id" in payload:
        cat = db.session.get(Category, payload["category_id"])

    book = Book(
        title=payload["title"],
        isbn=payload.get("isbn"),
        published_year=payload.get("published_year"),
        description=payload.get("description", ""),
        total_copies=payload.get("total_copies", 0),
        category_id=cat.id if cat else None,
    )
    db.session.add(book)
    db.session.flush()

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
    if "published_year" in payload:
        book.published_year = payload["published_year"]
    if "description" in payload:
        book.description = payload["description"]
    if "total_copies" in payload:
        book.total_copies = payload["total_copies"]
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


# --- Sub-resource: /books/{id}/copies (1:N strong containment) ---

@bp.get("/<int:book_id>/copies")
def list_book_copies(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    copies = db.session.query(BookCopy).filter_by(book_id=book_id).all()
    return jsonify([c.to_dict() for c in copies])


@bp.post("/<int:book_id>/copies")
def add_book_copy(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    req = request.get_json(silent=True) or {}
    try:
        validate(req, COPY_SCHEMA)
    except ValidationError as e:
        return jsonify({
            "error": "validation_failed",
            "field": list(e.path),
            "message": e.message
        }), 400

    if db.session.query(BookCopy).filter_by(barcode=req["barcode"]).first():
        return jsonify({"error": "conflict", "message": "Barcode already exists"}), 409

    copy = BookCopy(
        barcode=req["barcode"],
        status=req.get("status", "available"),
        book_id=book_id,
    )
    book.total_copies = (book.total_copies or 0) + 1
    db.session.add(copy)
    db.session.commit()
    return jsonify(copy.to_dict()), 201


# --- Sub-resource: /books/{id}/reviews (1:N strong containment) ---

@bp.get("/<int:book_id>/reviews")
def list_book_reviews(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    reviews = db.session.query(Review).filter_by(book_id=book_id).all()
    return jsonify([r.to_dict() for r in reviews])


@bp.post("/<int:book_id>/reviews")
def create_book_review(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "not_found"}), 404
    req = request.get_json(silent=True) or {}
    if "rating" not in req or "member_id" not in req:
        return jsonify({"error": "bad_request", "message": "rating and member_id required"}), 400
    if not (1 <= req["rating"] <= 5):
        return jsonify({"error": "validation_failed", "message": "rating must be 1-5"}), 400
    member = db.session.get(Member, req["member_id"])
    if not member:
        return jsonify({"error": "not_found", "message": "Member not found"}), 404
    review = Review(
        rating=req["rating"],
        comment=req.get("comment", ""),
        book_id=book_id,
        member_id=req["member_id"],
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.to_dict()), 201