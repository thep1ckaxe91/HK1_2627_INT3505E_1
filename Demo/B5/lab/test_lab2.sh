#!/bin/bash
set -e

# Lab 2 Test Script — Pagination, Filter, Multi-key Sort
# Seeds data, then tests offset/cursor pagination, genre filter, and multi-key sort.

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

echo "=== Lab 2: Pagination, Filter & Sort Test ==="
echo ""

# Clean start
rm -f "$LAB_DIR/instance/bookstore.db"

cd "$LAB_DIR"
../.venv/bin/python app.py &>/dev/null &
APP_PID=$!
sleep 2

echo "Server started (PID: $APP_PID)"
echo ""

# --- Seed data ---
echo ">>> Seeding categories..."
curl -s -X POST "$BASE_URL/categories" -H "Content-Type: application/json" \
  -d '{"name": "Technology", "slug": "tech"}' > /dev/null
curl -s -X POST "$BASE_URL/categories" -H "Content-Type: application/json" \
  -d '{"name": "Fiction", "slug": "fiction"}' > /dev/null
curl -s -X POST "$BASE_URL/categories" -H "Content-Type: application/json" \
  -d '{"name": "Science", "slug": "science"}' > /dev/null

echo ">>> Seeding authors..."
curl -s -X POST "$BASE_URL/authors" -H "Content-Type: application/json" \
  -d '{"name": "Robert C. Martin"}' > /dev/null
curl -s -X POST "$BASE_URL/authors" -H "Content-Type: application/json" \
  -d '{"name": "Martin Fowler"}' > /dev/null

echo ">>> Seeding 8 books..."
for i in $(seq 1 8); do
  PRICE=$((100000 + i * 50000))
  STOCK=$((i * 3))
  if [ $i -le 3 ]; then CAT=1;
  elif [ $i -le 5 ]; then CAT=2;
  else CAT=3; fi
  curl -s -X POST "$BASE_URL/books" -H "Content-Type: application/json" \
    -d "{\"title\": \"Book $i\", \"price\": {\"amount\": $PRICE, \"currency\": \"VND\"}, \"stock\": $STOCK, \"category_id\": $CAT, \"authors\": [{\"id\": 1, \"role\": \"lead\"}]}" > /dev/null
done
echo "Seeded 8 books (3 tech, 2 fiction, 3 science)"
echo ""

# --- Offset pagination ---
echo "========================================="
echo "  OFFSET PAGINATION"
echo "========================================="
echo ""

echo ">>> 1. Offset page 1 (limit=3)"
curl -s "$BASE_URL/books?strategy=offset&limit=3&offset=0&sort=-id" | python3 -m json.tool
echo ""

echo ">>> 2. Offset page 2 (limit=3, offset=3)"
curl -s "$BASE_URL/books?strategy=offset&limit=3&offset=3&sort=-id" | python3 -m json.tool
echo ""

echo ">>> 3. Offset page 3 (limit=3, offset=6)"
curl -s "$BASE_URL/books?strategy=offset&limit=3&offset=6&sort=-id" | python3 -m json.tool
echo ""

# --- Cursor pagination ---
echo "========================================="
echo "  CURSOR PAGINATION"
echo "========================================="
echo ""

echo ">>> 4. Cursor page 1 (limit=3, default sort=-id)"
RESP=$(curl -s "$BASE_URL/books?strategy=cursor&limit=3&sort=-id")
echo "$RESP" | python3 -m json.tool
CURSOR=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['pagination']['next_cursor'])")
echo ""

echo ">>> 5. Cursor page 2 (using cursor from page 1)"
RESP2=$(curl -s "$BASE_URL/books?strategy=cursor&limit=3&sort=-id&cursor=$CURSOR")
echo "$RESP2" | python3 -m json.tool
CURSOR2=$(echo "$RESP2" | python3 -c "import sys,json; c=json.load(sys.stdin)['pagination']['next_cursor']; print(c if c else '')")
echo ""

if [ -n "$CURSOR2" ]; then
  echo ">>> 6. Cursor page 3 (using cursor from page 2)"
  curl -s "$BASE_URL/books?strategy=cursor&limit=3&sort=-id&cursor=$CURSOR2" | python3 -m json.tool
  echo ""
fi

# --- Sort changed error ---
echo ">>> 7. Cursor with changed sort (expect 400)"
curl -s "$BASE_URL/books?strategy=cursor&limit=3&sort=price&cursor=$CURSOR" | python3 -m json.tool
echo ""

# --- Genre filter ---
echo "========================================="
echo "  GENRE FILTER"
echo "========================================="
echo ""

echo ">>> 8. Filter genre=tech (cursor)"
curl -s "$BASE_URL/books?genre=tech&sort=-id" | python3 -m json.tool
echo ""

echo ">>> 9. Filter genre=fiction (offset)"
curl -s "$BASE_URL/books?strategy=offset&genre=fiction&sort=-id" | python3 -m json.tool
echo ""

echo ">>> 10. Filter genre=science (cursor)"
curl -s "$BASE_URL/books?genre=science&sort=-id" | python3 -m json.tool
echo ""

# --- Multi-key sort ---
echo "========================================="
echo "  MULTI-KEY SORT"
echo "========================================="
echo ""

echo ">>> 11. Sort by price ascending"
curl -s "$BASE_URL/books?sort=price" | python3 -m json.tool
echo ""

echo ">>> 12. Sort by -price,title (descending price, then title asc)"
curl -s "$BASE_URL/books?sort=-price,title" | python3 -m json.tool
echo ""

echo ">>> 13. Sort by stock descending"
curl -s "$BASE_URL/books?sort=-stock" | python3 -m json.tool
echo ""

# --- Bad sort key ---
echo ">>> 14. Invalid sort key (expect 400)"
curl -s "$BASE_URL/books?sort=foobar" | python3 -m json.tool
echo ""

# --- Bad strategy ---
echo ">>> 15. Invalid strategy (expect 400)"
curl -s "$BASE_URL/books?strategy=magic" | python3 -m json.tool
echo ""

# --- Combined: filter + sort + offset pagination ---
echo ">>> 16. Combined: genre=tech + sort=price + offset pagination"
curl -s "$BASE_URL/books?strategy=offset&genre=tech&sort=price&limit=2&offset=0" | python3 -m json.tool
echo ""

echo ""
echo "=== Lab 2 Tests Complete ==="
