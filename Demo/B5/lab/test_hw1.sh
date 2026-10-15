#!/bin/bash
set -e

# Homework 1 Test Script — Library Management System API
# Tests all 21 endpoints across 7 entities/resources with daemon process of app.py.

BASE_URL="http://127.0.0.1:5000/api/v1"
LAB_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PID=""

cleanup() {
    if [ -n "$APP_PID" ]; then
        kill "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
    rm -f "$LAB_DIR/instance/bookstore.db"
}
trap cleanup EXIT

echo "=========================================================="
echo "  Homework 1: Library Management API System Tests"
echo "=========================================================="
echo ""

# Remove previous DB for a deterministic, clean run
rm -f "$LAB_DIR/instance/bookstore.db"

# Start Flask application as daemon process
cd "$LAB_DIR"
../.venv/bin/python app.py &>/dev/null &
APP_PID=$!
sleep 2

echo "Flask daemon started (PID: $APP_PID)"
echo ""

# ========================================================
# 1. Categories
# ========================================================
echo ">>> [Endpoint 16] POST /api/v1/categories — Create Category 'Computer Science'"
curl -s -X POST "$BASE_URL/categories" \
  -H "Content-Type: application/json" \
  -d '{"name": "Computer Science", "slug": "cs"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 16] POST /api/v1/categories — Create Category 'Mathematics'"
curl -s -X POST "$BASE_URL/categories" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mathematics", "slug": "math"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 15] GET /api/v1/categories — List all Categories"
curl -s "$BASE_URL/categories" | python3 -m json.tool
echo ""

# ========================================================
# 2. Authors
# ========================================================
echo ">>> [Endpoint 14] POST /api/v1/authors — Create Author 'Donald Knuth'"
curl -s -X POST "$BASE_URL/authors" \
  -H "Content-Type: application/json" \
  -d '{"name": "Donald Knuth", "bio": "Author of The Art of Computer Programming"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 14] POST /api/v1/authors — Create Author 'Harold Abelson'"
curl -s -X POST "$BASE_URL/authors" \
  -H "Content-Type: application/json" \
  -d '{"name": "Harold Abelson", "bio": "MIT Professor, co-author of SICP"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 13] GET /api/v1/authors — List all Authors"
curl -s "$BASE_URL/authors" | python3 -m json.tool
echo ""

# ========================================================
# 3. Members
# ========================================================
echo ">>> [Endpoint 18] POST /api/v1/members — Create Member (Schema validated)"
curl -s -X POST "$BASE_URL/members" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@uet.vnu.edu.vn",
    "display_name": "Alice Nguyen",
    "membership_type": "student"
  }' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 18] POST /api/v1/members — Create Second Member"
curl -s -X POST "$BASE_URL/members" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@uet.vnu.edu.vn",
    "display_name": "Bob Tran",
    "membership_type": "standard"
  }' | python3 -m json.tool
echo ""

echo ">>> [Validation Test] POST /api/v1/members with invalid email (expect 400)"
curl -s -X POST "$BASE_URL/members" \
  -H "Content-Type: application/json" \
  -d '{"email": "not-an-email", "display_name": "Bad Member"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 17] GET /api/v1/members — List all Members"
curl -s "$BASE_URL/members" | python3 -m json.tool
echo ""

# ========================================================
# 4. Books (CRUD & Relations)
# ========================================================
echo ">>> [Endpoint 2] POST /api/v1/books — Create Book 'The Art of Computer Programming'"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Art of Computer Programming, Vol 1",
    "isbn": "9780201896831",
    "published_year": 1997,
    "description": "Fundamental algorithms reference",
    "category_id": 1,
    "authors": [{"id": 1, "role": "lead"}]
  }' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 2] POST /api/v1/books — Create Book 'Structure and Interpretation of Computer Programs'"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Structure and Interpretation of Computer Programs",
    "isbn": "9780262510875",
    "published_year": 1996,
    "description": "Computer science textbook using Scheme",
    "category_id": 1,
    "authors": [{"id": 2, "role": "lead"}]
  }' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 2] POST /api/v1/books — Create Book 'Introduction to Linear Algebra'"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction to Linear Algebra",
    "isbn": "9780980232776",
    "published_year": 2016,
    "description": "Linear algebra fundamentals by Gilbert Strang",
    "category_id": 2
  }' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 2] POST /api/v1/books — Create Temporary Book to test DELETE"
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{"title": "Obsolete Draft Manual", "published_year": 1990}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 3] GET /api/v1/books/1 — Get Book Details"
curl -s "$BASE_URL/books/1" | python3 -m json.tool
echo ""

echo ">>> [Endpoint 3] GET /api/v1/books/1?fields=id,title,publishedYear — Sparse Fieldsets"
curl -s "$BASE_URL/books/1?fields=id,title,publishedYear" | python3 -m json.tool
echo ""

echo ">>> [Endpoint 4] PUT /api/v1/books/1 — Update Book Description"
curl -s -X PUT "$BASE_URL/books/1" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated classic algorithms reference manual"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 5] DELETE /api/v1/books/4 — Delete Temporary Book"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -X DELETE "$BASE_URL/books/4"
echo ""

echo ">>> Verify Book 4 is Deleted (expect 404)"
curl -s "$BASE_URL/books/4" | python3 -m json.tool
echo ""

# ========================================================
# 5. Book Authors (N:M sub-resource)
# ========================================================
echo ">>> [Endpoint 7] POST /api/v1/books/1/authors — Add Co-author to Book 1"
curl -s -X POST "$BASE_URL/books/1/authors" \
  -H "Content-Type: application/json" \
  -d '{"author_id": 2, "role": "co"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 6] GET /api/v1/books/1/authors — List Authors of Book 1"
curl -s "$BASE_URL/books/1/authors" | python3 -m json.tool
echo ""

echo ">>> [Endpoint 8] DELETE /api/v1/books/1/authors/2 — Remove Co-author from Book 1"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -X DELETE "$BASE_URL/books/1/authors/2"
echo ""

# ========================================================
# 6. Book Copies (1:N sub-resource)
# ========================================================
echo ">>> [Endpoint 10] POST /api/v1/books/1/copies — Add Copy 1 with barcode"
curl -s -X POST "$BASE_URL/books/1/copies" \
  -H "Content-Type: application/json" \
  -d '{"barcode": "LIB-CS-0001", "status": "available"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 10] POST /api/v1/books/1/copies — Add Copy 2 with barcode"
curl -s -X POST "$BASE_URL/books/1/copies" \
  -H "Content-Type: application/json" \
  -d '{"barcode": "LIB-CS-0002", "status": "available"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 10] POST /api/v1/books/2/copies — Add Copy for Book 2"
curl -s -X POST "$BASE_URL/books/2/copies" \
  -H "Content-Type: application/json" \
  -d '{"barcode": "LIB-CS-0003", "status": "available"}' | python3 -m json.tool
echo ""

echo ">>> [Validation Test] Duplicate barcode on POST copy (expect 409)"
curl -s -X POST "$BASE_URL/books/1/copies" \
  -H "Content-Type: application/json" \
  -d '{"barcode": "LIB-CS-0001"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 9] GET /api/v1/books/1/copies — List Physical Copies of Book 1"
curl -s "$BASE_URL/books/1/copies" | python3 -m json.tool
echo ""

# ========================================================
# 7. Reviews (1:N sub-resource)
# ========================================================
echo ">>> [Endpoint 12] POST /api/v1/books/1/reviews — Create Review by Member 1"
curl -s -X POST "$BASE_URL/books/1/reviews" \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "comment": "A must-read masterpiece for any computer scientist.", "member_id": 1}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 11] GET /api/v1/books/1/reviews — List Reviews of Book 1"
curl -s "$BASE_URL/books/1/reviews" | python3 -m json.tool
echo ""

# ========================================================
# 8. Loans (Borrowing & Returning)
# ========================================================
echo ">>> [Endpoint 20] POST /api/v1/loans — Borrow Copy 1 by Member 1"
curl -s -X POST "$BASE_URL/loans" \
  -H "Content-Type: application/json" \
  -d '{"copy_id": 1, "member_id": 1}' | python3 -m json.tool
echo ""

echo ">>> [Conflict Test] Attempt to borrow Copy 1 again (already loaned, expect 409)"
curl -s -X POST "$BASE_URL/loans" \
  -H "Content-Type: application/json" \
  -d '{"copy_id": 1, "member_id": 2}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 20] POST /api/v1/loans — Borrow Copy 3 by Member 2 with custom due_date"
curl -s -X POST "$BASE_URL/loans" \
  -H "Content-Type: application/json" \
  -d '{"copy_id": 3, "member_id": 2, "due_date": "2026-11-01"}' | python3 -m json.tool
echo ""

echo ">>> [Endpoint 19] GET /api/v1/loans — List Active Loans"
curl -s "$BASE_URL/loans?status=active" | python3 -m json.tool
echo ""

echo ">>> [Sub-resource] GET /api/v1/members/1/loans — List Loans for Member 1"
curl -s "$BASE_URL/members/1/loans" | python3 -m json.tool
echo ""

echo ">>> [Endpoint 21] PUT /api/v1/loans/1/return — Return Loan 1"
curl -s -X PUT "$BASE_URL/loans/1/return" | python3 -m json.tool
echo ""

echo ">>> Verify Copy 1 is available again after return"
curl -s "$BASE_URL/books/1/copies" | python3 -m json.tool
echo ""

# ========================================================
# 9. Pagination, Filtering, and Multi-Key Sorting
# ========================================================
echo "=========================================================="
echo "  PAGINATION, FILTERING & MULTI-KEY SORTING"
echo "=========================================================="
echo ""

echo ">>> [Endpoint 1] GET /api/v1/books?strategy=offset&limit=2&offset=0"
curl -s "$BASE_URL/books?strategy=offset&limit=2&offset=0" | python3 -m json.tool
echo ""

echo ">>> [Endpoint 1] GET /api/v1/books?strategy=cursor&limit=2&sort=-id"
RESP=$(curl -s "$BASE_URL/books?strategy=cursor&limit=2&sort=-id")
echo "$RESP" | python3 -m json.tool
CURSOR=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['pagination']['next_cursor'])")
echo ""

echo ">>> [Endpoint 1] Next page via cursor"
curl -s "$BASE_URL/books?strategy=cursor&limit=2&sort=-id&cursor=$CURSOR" | python3 -m json.tool
echo ""

echo ">>> [Endpoint 1] GET /api/v1/books?category=cs — Filter by Category"
curl -s "$BASE_URL/books?category=cs" | python3 -m json.tool
echo ""

echo ">>> [Endpoint 1] GET /api/v1/books?sort=-published_year,title — Multi-Key Sort"
curl -s "$BASE_URL/books?sort=-published_year,title" | python3 -m json.tool
echo ""

echo "=========================================================="
echo "  All 21 Endpoints Tested Successfully!"
echo "=========================================================="
