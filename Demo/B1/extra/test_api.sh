#!/bin/bash

URL="http://127.0.0.1:5000"

echo "=== Testing POST /books (Creating a book) ==="
curl -s -X POST "$URL/books" -H "Content-Type: application/json" -d '{"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"}' | jq
echo -e "\n"

echo "=== Testing POST /books (Creating another book) ==="
curl -s -X POST "$URL/books" -H "Content-Type: application/json" -d '{"title": "1984", "author": "George Orwell"}' | jq
echo -e "\n"

echo "=== Testing GET /books (Listing all books) ==="
curl -s -X GET "$URL/books" | jq
echo -e "\n"

echo "=== Testing GET /books/1 (Getting book 1) ==="
curl -s -X GET "$URL/books/1" | jq
echo -e "\n"

echo "=== Testing PUT /books/1 (Updating book 1) ==="
curl -s -X PUT "$URL/books/1" -H "Content-Type: application/json" -d '{"title": "The Great Gatsby (Revised)"}' | jq
echo -e "\n"

echo "=== Testing GET /books/1 (Getting book 1 after update) ==="
curl -s -X GET "$URL/books/1" | jq
echo -e "\n"

echo "=== Testing DELETE /books/1 (Deleting book 1) ==="
curl -s -X DELETE "$URL/books/1" -w "Status Code: %{http_code}\n"
echo -e "\n"

echo "=== Testing GET /books (Listing all books after delete) ==="
curl -s -X GET "$URL/books" | jq
echo -e "\n"
