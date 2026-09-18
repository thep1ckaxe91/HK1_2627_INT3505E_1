from flask import Flask, jsonify, request, make_response, g
import sqlite3

app = Flask(__name__)

db_path = __file__.removesuffix("app.py") + "data.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(db_path)
    return db


def init_db():
    with app.app_context():
        cs = get_db().cursor()

        cs.execute("""--sql
        CREATE TABLE IF NOT EXISTS books (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           title VARCHAR(255) NOT NULL,
           author VARCHAR(255) NOT NULL
        )""")
        cs.execute("""--sql
        CREATE TABLE IF NOT EXISTS orders (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           price FLOAT NOT NULL,
           bid INTEGER NOT NULL,
           FOREIGN KEY (bid) REFERENCES books(id)
        )""")
        get_db().commit()


@app.teardown_appcontext
def _close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


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

    a = request.args.get("author", "%")
    q = (request.args.get("q", "")).lower()

    cur = get_db().cursor()
    cur.execute(
        """--sql
    SELECT
        b.id, 
        b.title, 
        b.author 
    FROM books b
    WHERE LOWER(b.author) LIKE ? AND b.title LIKE ? 
    ORDER BY b.id
    LIMIT ? OFFSET ? 
    """,
        (a, f"%{q}%", size, (page - 1) * size),
    )

    flt = cur.fetchall()

    cur.execute(
        """--sql
    SELECT
        COUNT(*)
    FROM books b
    WHERE LOWER(b.author) LIKE ? AND b.title LIKE ?
    """,
        (a, f"%{q}%"),
    )
    total = int(cur.fetchone()[0])
    start = (page - 1) * size
    end = start + size
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
        "data": flt,
        "pagination": {"page": page, "size": size, "total": total, "total_pages": last},
        "_links": links,
    }

    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp


@app.get("/order/<int:oid>")
def get_order(oid: int):

    cs = get_db().cursor()

    cs.execute(
        f"""--sql
    SELECT 
        b.id, 
        b.title, 
        b.author,
        o.price
    FROM orders o
    JOIN books b ON b.id = o.bid
    WHERE o.id = ?
    """,
        (oid,),
    )

    row = cs.fetchone()

    if row is None:
        return jsonify(error="Not found"), 404

    bid, t, a, p = row

    res = make_response(
        jsonify({"book_id": bid, "title": t, "author": a, "price": p}), 200
    )
    res.headers["Cache-Control"] = "public, max-age=30"

    return res


if __name__ == "__main__":
    init_db()
    app.run()
