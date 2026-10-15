#!/bin/bash
set -e

# Lab 1 Test Script — Bookstore CRUD API
# Starts the Flask server, runs curl tests, then stops the server.

BASE_URL="http://127.0.0.1:5000/api/v1"
LAB_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PID=""

cleanup() {
    if [ -n "$APP_PID" ]; then
        kill "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
    # Clean up test DB
    rm -f "$LAB_DIR/instance/bookstore.db"
}
trap cleanup EXIT

echo "=== Lab 1: Bookstore CRUD API Test ==="
echo ""

# Remove old DB for clean state
rm -f "$LAB_DIR/instance/bookstore.db"

# Start Flask server as daemon
cd "$LAB_DIR"
../.venv/bin/python app.py &>/dev/null &
APP_PID=$!
sleep 2

echo "Server started (PID: $APP_PID)"
echo ""

# ------ Categories ------
echo ">>> 1. Create Category (tech)"
curl -s -X POST "$BASE_URL/categories" \
  -H "Content-Type: application/json" \
  -d '{"name": "Technology", "slug": "tech"}' | python3 -m json.tool
echo ""

echo ">>> 2. Create Category (fiction)"
curl -s -X POST "$BASE_URL/categories" \
  -H "Content-Type: application/json" \
  -d '{"name": "Fiction", "slug": "fiction"}' | python3 -m json.tool
echo ""

echo ">>> 3. List Categories"
curl -s "$BASE_URL/categories" | python3 -m json.tool
echo ""

# ------ Authors ------
echo ">>> 4. Create Author (Robert C. Martin)"
curl -s -X POST "$BASE_URL/authors" \
  -H "Content-Type: application/json" \
  -d '{"name": "Robert C. Martin", "bio": "Software engineer and author"}' | python3 -m json.tool
echo ""

echo ">>> 5. Create Author (Martin Fowler)"
curl -s -X POST "$BASE_URL/authors" \
  -H "Content-Type: application/json" \
  -d '{"name": "Martin Fowler", "bio": "Software development thought leader"}' | python3 -m json.tool
echo ""

echo ">>> 6. List Authors"
curl -s "$BASE_URL/authors" | python3 -m json.tool
echo ""

# ------ Users ------
echo ">>> 7. Create User"
curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "an@example.com", "display_name": "An Nguyen"}' | python3 -m json.tool
echo ""

# ------ Books (CRUD) ------
echo ">>> 8. Create Book (Clean Code) — with author & category"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "isbn": "9780132350884",
    "price": {"amount": 450000, "currency": "VND"},
    "stock": 25,
    "category_id": 1,
    "authors": [{"id": 1, "role": "lead"}]
  }' | python3 -m json.tool
echo ""

echo ">>> 9. Create Book (Refactoring)"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Refactoring",
    "isbn": "9780134757599",
    "price": {"amount": 520000, "currency": "VND"},
    "stock": 10,
    "category_id": 1,
    "authors": [{"id": 2, "role": "lead"}]
  }' | python3 -m json.tool
echo ""

echo ">>> 10. Create Book (no ISBN, minimal)"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{"title": "Draft Book"}' | python3 -m json.tool
echo ""

echo ">>> 11. List Books"
curl -s "$BASE_URL/books" | python3 -m json.tool
echo ""

echo ">>> 12. Get Book by ID"
curl -s "$BASE_URL/books/1" | python3 -m json.tool
echo ""

echo ">>> 13. Update Book (change stock)"
curl -s -X PUT "$BASE_URL/books/1" \
  -H "Content-Type: application/json" \
  -d '{"stock": 30}' | python3 -m json.tool
echo ""

echo ">>> 14. Delete Book 3 (Draft Book)"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -X DELETE "$BASE_URL/books/3"
echo ""

echo ">>> 15. Verify Book 3 deleted (expect 404)"
curl -s "$BASE_URL/books/3" | python3 -m json.tool
echo ""

# ------ Book ↔ Author N:M ------
echo ">>> 16. Add co-author to Book 1"
curl -s -X POST "$BASE_URL/books/1/authors" \
  -H "Content-Type: application/json" \
  -d '{"author_id": 2, "role": "co"}' | python3 -m json.tool
echo ""

echo ">>> 17. List authors of Book 1"
curl -s "$BASE_URL/books/1/authors" | python3 -m json.tool
echo ""

echo ">>> 18. List books by Author 2"
curl -s "$BASE_URL/authors/2/books" | python3 -m json.tool
echo ""

echo ">>> 19. Remove co-author (author 2) from Book 1"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -X DELETE "$BASE_URL/books/1/authors/2"
echo ""

# ------ Reviews (sub-resource) ------
echo ">>> 20. Create Review for Book 1"
curl -s -X POST "$BASE_URL/books/1/reviews" \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "comment": "Excellent book!", "user_id": 1}' | python3 -m json.tool
echo ""

echo ">>> 21. Create Review (rating out of range, expect 400)"
curl -s -X POST "$BASE_URL/books/1/reviews" \
  -H "Content-Type: application/json" \
  -d '{"rating": 6, "comment": "Too high", "user_id": 1}' | python3 -m json.tool
echo ""

echo ">>> 22. List Reviews for Book 1"
curl -s "$BASE_URL/books/1/reviews" | python3 -m json.tool
echo ""

# ------ Validation ------
echo ">>> 23. Create Book with invalid JSON (expect 400)"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{"price": {"amount": -1, "currency": "VND"}}' | python3 -m json.tool
echo ""

echo ">>> 24. Get non-existent book (expect 404)"
curl -s "$BASE_URL/books/9999" | python3 -m json.tool
echo ""

echo ""
echo "=== Lab 1 Tests Complete ==="
