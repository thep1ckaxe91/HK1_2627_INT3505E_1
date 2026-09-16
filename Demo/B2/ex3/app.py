from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

books = [
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 2, "title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"id": 3, "title": "1984", "author": "George Orwell"},
    {"id": 4, "title": "Pride and Prejudice", "author": "Jane Austen"},
    {"id": 5, "title": "The Catcher in the Rye", "author": "J.D. Salinger"},
]

DEFAULT_SIZE, MAX_SIZE = 20, 100


@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify(error="Page and size must be int"), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)
    flt = books
    a = request.args.get("author")
    if a:
        flt = [b for b in flt if b["author"].lower() == a.lower()]
    q = (request.args.get("q", "")).lower()
    if q:
        flt = [b for b in flt if q.lower() in b["title"].lower()]
    total = len(flt)
    start = (page - 1) * size
    end = start + size
    items = flt[start:end]
    last = (total + size - 1) // size

    def u(p):
        return f"/books?page={p}&size={size}"

    links = {
        "self": {"href": u(page)},
        "first": {"href": u(1)},
        "last": {"href": u(max(last, 1))},
    }
    if page > 1:
        links["prev"] = {"href": u(page - 1)}
    if end < total:
        links["next"] = {"href": u(page + 1)}
    body = {
        "data": items,
        "pagination": {"page": page, "size": size, "total": total, "total_pages": last},
        "_links": links,
    }

    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp


if __name__ == "__main__":
    app.run()
