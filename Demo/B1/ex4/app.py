from flask import Flask, jsonify, request
from uuid import uuid4

app = Flask(__name__)

books = [
    {
        "id": "18f1a14a87e3",
        "t": "Systems Performance: Enterprise and the Cloud",
        "author": "Brendan Gregg",
    },
    {
        "id": "1a2f643e2b34",
        "t": "Quantitative Trading: How to Build Your Own Algorithmic Trading Business",
        "author": "Ernest P. Chan",
    },
    {
        "id": "14bc1b54a3a6",
        "t": "C++ High Performance: Master the art of optimizing the core of your C++ applications",
        "author": "Björn Andrist, Viktor Sehr",
    },
]


def find_by_id(id: str) -> dict | None:
    for book in books:
        if book["id"] == id:
            return book
    return None


@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200


@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id: int):
    return jsonify({"id": item_id}), 200


@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    q = request.args.get("q", "").strip().lower()
    items = [b for b in books if q in b["t"].lower()]
    return jsonify({"items": items}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
