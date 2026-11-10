#!/usr/bin/env bash
set -euo pipefail

PORT=5002
BASE_URL="http://127.0.0.1:${PORT}"
export LOG_LEVEL="WARNING"
unset DB_URL

echo "=== Starting background test server on port ${PORT} ==="
uv run uvicorn wsgi:app --port "${PORT}" --host 127.0.0.1 --log-level warning &
SERVER_PID=$!

cleanup() {
    echo "=== Shutting down test server (PID ${SERVER_PID}) ==="
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
}
trap cleanup EXIT

# Wait for server readiness
echo "Waiting for service to boot..."
for i in {1..30}; do
    if curl -s -f "${BASE_URL}/healthz" > /dev/null 2>&1; then
        echo "Service is live!"
        break
    fi
    sleep 0.2
done

echo ""
echo "--- 1. Testing GET /healthz ---"
curl -s -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/healthz"

echo ""
echo "--- 2. Testing GET /ready ---"
curl -s -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/ready"

echo ""
echo "--- 3. Testing POST /api/v1/products (Create) ---"
RANDOM_SKU="CURL-$(date +%s%N | cut -b1-10)"
CREATE_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/products" \
  -H "Content-Type: application/json" \
  -d "{\"sku\": \"${RANDOM_SKU}\", \"name\": \"Curl Test Keyboard\", \"price_cents\": 9900, \"qty_in_stock\": 10}")

echo "${CREATE_RESP}" | sed '/HTTP_STATUS/d'
STATUS=$(echo "${CREATE_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "201" ]; then
    echo "FAILED: Expected 201, got ${STATUS}"
    exit 1
fi

echo ""
echo "--- 4. Testing POST /api/v1/products (Duplicate SKU -> 409 Conflict) ---"
DUP_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/products" \
  -H "Content-Type: application/json" \
  -d "{\"sku\": \"${RANDOM_SKU}\", \"name\": \"Duplicate\", \"price_cents\": 500}")
echo "${DUP_RESP}" | sed '/HTTP_STATUS/d'
STATUS=$(echo "${DUP_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "409" ]; then
    echo "FAILED: Expected 409, got ${STATUS}"
    exit 1
fi

echo ""
echo "--- 5. Testing POST /api/v1/products (Invalid Schema -> 422 Unprocessable) ---"
INV_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/products" \
  -H "Content-Type: application/json" \
  -d "{\"sku\": \"X\", \"name\": \"Too Short\", \"price_cents\": -50}")
echo "${INV_RESP}" | sed '/HTTP_STATUS/d'
STATUS=$(echo "${INV_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "422" ]; then
    echo "FAILED: Expected 422, got ${STATUS}"
    exit 1
fi

echo ""
echo "--- 6. Testing GET /api/v1/products (List Paginated) ---"
curl -s -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/api/v1/products?page=1&size=5"

echo ""
echo "=== All integration curl tests passed successfully! ==="
