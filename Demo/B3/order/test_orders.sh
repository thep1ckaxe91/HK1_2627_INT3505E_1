#!/usr/bin/env bash
set -euo pipefail

VENV_PYTHON="/mnt/New_Volume/Repos/HK1_2627_INT3505E_1/.venv/bin/python"
PORT=5000
BASE_URL="http://127.0.0.1:${PORT}"

# Start Flask app in background
$VENV_PYTHON app.py > /dev/null 2>&1 &
SERVER_PID=$!

cleanup() {
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Wait for server to be responsive (up to 5 seconds)
for i in {1..10}; do
    if curl -s "${BASE_URL}/orders" > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo "========================================="
echo "TEST 1: Filter by status (status=paid)"
echo "curl '${BASE_URL}/orders?status=paid'"
echo "========================================="
curl -s "${BASE_URL}/orders?status=paid" | python3 -m json.tool

echo -e "\n========================================="
echo "TEST 2: Cursor pagination limit (limit=5)"
echo "curl '${BASE_URL}/orders?limit=5'"
echo "========================================="
PAGE1=$(curl -s "${BASE_URL}/orders?limit=5")
echo "$PAGE1" | python3 -m json.tool

NEXT_CURSOR=$(echo "$PAGE1" | python3 -c 'import sys, json; print(json.load(sys.stdin)["pagination"]["next_cursor"])')

echo -e "\n========================================="
echo "TEST 2b: Cursor follow-up using next_cursor"
echo "curl '${BASE_URL}/orders?limit=5&cursor=${NEXT_CURSOR}'"
echo "========================================="
curl -s "${BASE_URL}/orders?limit=5&cursor=${NEXT_CURSOR}" | python3 -m json.tool

echo -e "\n========================================="
echo "TEST 3: Sparse fieldsets (fields=id,total)"
echo "curl '${BASE_URL}/orders?fields=id,total'"
echo "========================================="
curl -s "${BASE_URL}/orders?fields=id,total" | python3 -m json.tool

echo -e "\n========================================="
echo "TEST 4: Filter by customer_id (customer_id=101)"
echo "curl '${BASE_URL}/orders?customer_id=101'"
echo "========================================="
curl -s "${BASE_URL}/orders?customer_id=101" | python3 -m json.tool

echo -e "\n========================================="
echo "TEST 5: Sort descending by total (sort=-total&limit=3)"
echo "curl '${BASE_URL}/orders?sort=-total&limit=3'"
echo "========================================="
curl -s "${BASE_URL}/orders?sort=-total&limit=3" | python3 -m json.tool

echo -e "\n========================================="
echo "All tests completed successfully."
echo "========================================="
