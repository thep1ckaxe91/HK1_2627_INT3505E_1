#!/bin/bash

URL="http://127.0.0.1:5000"

function run_request() {
  local method=$1
  local path=$2
  local data=$3
  
  if [ -n "$data" ]; then
    res=$(curl -s -w "\n%{http_code}" -X "$method" "$URL$path" -H "Content-Type: application/json" -d "$data")
  else
    res=$(curl -s -w "\n%{http_code}" -X "$method" "$URL$path")
  fi
  
  body=$(echo "$res" | sed '$d')
  status=$(echo "$res" | tail -n 1)
  
  # Print the HTTP Status explicitly before returning the body (which we capture)
  echo "HTTP Status: $status" >&2
  echo "$body"
}

echo "=== 1. POST /books (Valid data) ==="
body=$(run_request "POST" "/books" '{"title": "Whitebox Book 1", "author": "Author A"}')
echo "$body" | jq 2>/dev/null || echo "$body"
id1=$(echo "$body" | jq -r '.id')

body=$(run_request "POST" "/books" '{"title": "Whitebox Book 2", "author": "Author B"}')
echo "$body" | jq 2>/dev/null || echo "$body"
id2=$(echo "$body" | jq -r '.id')

echo -e "\n=== 2. Edge Case: Missing parameters (400) ==="
body=$(run_request "POST" "/books" '{"title": "Incomplete Book"}')
echo "POST without author:"
echo "$body" | jq 2>/dev/null || echo "$body"

body=$(run_request "POST" "/books" '{"author": "Incomplete Author"}')
echo "POST without title:"
echo "$body" | jq 2>/dev/null || echo "$body"

body=$(run_request "POST" "/books" '{}')
echo "POST with empty JSON:"
echo "$body" | jq 2>/dev/null || echo "$body"


echo -e "\n=== 3. Whitebox: Pagination ==="
echo "GET /books?page=0&page_size=2"
body=$(run_request "GET" "/books?page=0&page_size=2")
echo "$body" | jq 2>/dev/null || echo "$body"

echo "GET /books?page=1&page_size=2"
body=$(run_request "GET" "/books?page=1&page_size=2")
echo "$body" | jq 2>/dev/null || echo "$body"

echo "GET /books?page=99&page_size=10 (Out of bounds)"
body=$(run_request "GET" "/books?page=99&page_size=10")
echo "$body" | jq 2>/dev/null || echo "$body"


echo -e "\n=== 4. GET /books/:id (Happy Path) ==="
body=$(run_request "GET" "/books/$id1")
echo "$body" | jq 2>/dev/null || echo "$body"

echo -e "\n=== 5. GET /books/:id (Non-existent 404) ==="
body=$(run_request "GET" "/books/999999")
echo "$body" | jq 2>/dev/null || echo "$body"

echo -e "\n=== 6. PUT /books/:id (Valid partial update) ==="
body=$(run_request "PUT" "/books/$id1" '{"title": "Whitebox Book 1 (Updated Title)"}')
echo "$body" | jq 2>/dev/null || echo "$body"

echo -e "\n=== 7. PUT /books/:id (Non-existent 404) ==="
body=$(run_request "PUT" "/books/999999" '{"title": "Should Fail"}')
echo "$body" | jq 2>/dev/null || echo "$body"

echo -e "\n=== 8. DELETE /books/:id (Happy Path) ==="
# Delete id1
run_request "DELETE" "/books/$id1"
echo "Deleted Book ID $id1"

echo -e "\n=== 9. DELETE /books/:id (Non-existent 404) ==="
body=$(run_request "DELETE" "/books/999999")
echo "$body" | jq 2>/dev/null || echo "$body"

echo -e "\n=== 10. GET /books/:id (Verification of deletion) ==="
body=$(run_request "GET" "/books/$id1")
echo "$body" | jq 2>/dev/null || echo "$body"
