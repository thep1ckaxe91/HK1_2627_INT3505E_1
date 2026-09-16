from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

books = []

_next_id = 1
@app.get("/books")
def list_books():
  return jsonify(
    {
      "data": books,
      "total": len(books)
    }
  ), 200

@app.post("/books")
def create_books():
  global _next_id

  if not request.is_json:
    print(request.get_data())
    return jsonify(error="expected JSON"), 415

  p = request.get_json(silent=True) or {}
  t = (p.get("title") or "").strip()
  a = (p.get("author") or "").strip()

  if not t or not a:
    return jsonify(error="title & author required"), 422

  book = {
    "id": _next_id,
    "title": t,
    "author": a,
  }

  books.append(book); _next_id+=1

  resp = make_response(jsonify(book), 201)
  resp.headers["Location"] = f"/books/{book["id"]}"

  return resp

if __name__ == "__main__":
  app.run()