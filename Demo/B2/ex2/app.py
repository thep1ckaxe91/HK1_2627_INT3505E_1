from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

books = []

_next_id = 1


@app.get("/books/<int:bid>")
def fetch(bid: int):
    i = next((k for k, b in enumerate(books) if b["id"] == bid), None)
    if i is None:
        return jsonify(error="Not found"), 404

    resp = make_response(jsonify(books[i]), 200)
    resp.headers["Cache-Control"] = "max-age=60"
    return resp


@app.put("/books/<int:bid>")
def put(bid: int):
    i = next((k for k, b in enumerate(books) if b["id"] == bid), None)
    if i is None:
        return jsonify(error="not found"), 404
    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")
    if not t or not a:
        return jsonify(error="need title+author"), 422
    books[i] = {
        "id": bid,
        "title": t.strip(),
        "author": a.strip(),
        "isbn": p.get("isbn"),
        "price": p.get("price"),
    }
    return jsonify(books[i]), 200


@app.patch("/books/<int:bid>")
def patch(bid:int):
    i = next((k for k,b in enumerate(books) if b["id"]==bid), None)
    if i is None: return jsonify(error="not found"), 404
    p = request.get_json(silent=True) or {}
    if p.get("price", 0) < 0:
        return jsonify(error="price must be positive"), 422
    for k in "title author isbn price".split():
        if k in p: 
            books[i][k] = p[k]
    return jsonify(books[i]), 200

@app.delete("/books/<int:bid>")
def delete(bid:int):
    i = next((k for k,b in enumerate(books) if b["id"]==bid), None)
    if i is None: 
        return jsonify(error="not found"), 404
    books.pop(i); return"", 204


if __name__ == "__main__":
    app.run()
