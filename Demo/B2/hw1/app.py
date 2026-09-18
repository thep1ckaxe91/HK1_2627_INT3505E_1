from flask import Flask, jsonify, request, make_response, g
import sqlite3

app = Flask(__name__)

db_path = __file__.removesuffix("app.py") + "data.db"

def get_db():
    db = getattr(g, '_database', None)
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
        CREATE TABKE IF NOT EXISTS orders (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           bid INTEGER NOT NULL,
           FOREIGN KEY bid REFERENCES books(id)
        )""")
        get_db().commit()

@app.teardown_appcontext
def _close_connection(exception):
    db = getattr(g, '_database', None)
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

    with app.app_context():        
        cur = get_db().cursor()
        cur.execute('SELECT id, title, author FROM books')

        flt = cur.fetchall()

    a = request.args.get("author")
    if a:
        flt = [b for b in flt if b[2].lower() == a.lower()]
    q = (request.args.get("q", "")).lower()
    if q:
        flt = [b for b in flt if q.lower() in b[1].lower()]
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

@app.get('/order/<int:oid>')
def get_order(oid : int) :
    with app.app_context():
        pass


if __name__ == "__main__":
    init_db()
    app.run()
