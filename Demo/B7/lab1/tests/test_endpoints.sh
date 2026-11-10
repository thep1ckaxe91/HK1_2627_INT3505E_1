#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-${TEST_URL:-}}"

if [ -z "${TARGET_URL}" ]; then
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

    echo "Waiting for service to boot..."
    for i in {1..30}; do
        if curl -s -f "${BASE_URL}/healthz" > /dev/null 2>&1; then
            echo "Service is live!"
            break
        fi
        sleep 0.2
    done
else
    BASE_URL="${TARGET_URL}"
    echo "=== Testing live server at ${BASE_URL} ==="
fi

echo ""
echo "--- 1. Testing GET /healthz ---"
curl -s -f -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/healthz"

echo ""
echo "--- 2. Testing GET /ready ---"
curl -s -f -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/ready"

echo ""
echo "--- 3. Testing POST /api/v1/products (Create) ---"
RANDOM_SKU="CURL-$(date +%s%N | cut -b1-10)"
CREATE_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/products" \
  -H "Content-Type: application/json" \
  -d "{\"sku\": \"${RANDOM_SKU}\", \"name\": \"Curl Mechanical Keyboard\", \"price_cents\": 9900, \"qty_in_stock\": 10}")

echo "${CREATE_RESP}" | sed '/HTTP_STATUS/d'
STATUS=$(echo "${CREATE_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "201" ]; then
    echo "FAILED: Expected 201, got ${STATUS}"
    exit 1
fi
PRODUCT_ID=$(echo "${CREATE_RESP}" | sed '/HTTP_STATUS/d' | grep -o '"id": *[0-9]*' | head -n1 | tr -dc '0-9')

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
curl -s -f -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/api/v1/products?page=1&size=5"

echo ""
echo "--- 7. Testing GET /api/v1/products/${PRODUCT_ID} ---"
curl -s -f -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/api/v1/products/${PRODUCT_ID}"

echo ""
echo "--- 8. Testing PATCH /api/v1/products/${PRODUCT_ID} (Update price) ---"
PATCH_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X PATCH "${BASE_URL}/api/v1/products/${PRODUCT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"price_cents": 12500}')
echo "${PATCH_RESP}" | sed '/HTTP_STATUS/d'
STATUS=$(echo "${PATCH_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "200" ]; then
    echo "FAILED: Expected 200, got ${STATUS}"
    exit 1
fi

echo ""
echo "--- 9. Testing POST /api/v1/products/${PRODUCT_ID}/reserve (Atomic Reservation) ---"
RESERVE_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/products/${PRODUCT_ID}/reserve" \
  -H "Content-Type: application/json" \
  -d '{"qty": 2}')
echo "${RESERVE_RESP}" | sed '/HTTP_STATUS/d'
STATUS=$(echo "${RESERVE_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "200" ]; then
    echo "FAILED: Expected 200, got ${STATUS}"
    exit 1
fi

echo ""
echo "--- 10. Testing POST /api/v1/orders (Place Order) ---"
ORDER_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d "{\"items\": [{\"product_id\": ${PRODUCT_ID}, \"quantity\": 3}]}")
echo "${ORDER_RESP}" | sed '/HTTP_STATUS/d'
STATUS=$(echo "${ORDER_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "201" ]; then
    echo "FAILED: Expected 201, got ${STATUS}"
    exit 1
fi
ORDER_ID=$(echo "${ORDER_RESP}" | sed '/HTTP_STATUS/d' | grep -o '"id": *[0-9]*' | head -n1 | tr -dc '0-9')

echo ""
echo "--- 11. Testing GET /api/v1/orders/${ORDER_ID} (Verify Eager Loaded Order) ---"
curl -s -f -w "\nHTTP Status: %{http_code}\n" "${BASE_URL}/api/v1/orders/${ORDER_ID}"

echo ""
echo "--- 12. Testing DELETE /api/v1/products/${PRODUCT_ID} (Soft Delete) ---"
DEL_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X DELETE "${BASE_URL}/api/v1/products/${PRODUCT_ID}")
STATUS=$(echo "${DEL_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "204" ]; then
    echo "FAILED: Expected 204, got ${STATUS}"
    exit 1
fi
echo "Deleted product ${PRODUCT_ID} (HTTP 204)"

echo ""
echo "--- 13. Testing GET /api/v1/products/${PRODUCT_ID} after delete (Should 404) ---"
DEL_CHECK_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${BASE_URL}/api/v1/products/${PRODUCT_ID}")
STATUS=$(echo "${DEL_CHECK_RESP}" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
if [ "${STATUS}" != "404" ]; then
    echo "FAILED: Expected 404, got ${STATUS}"
    exit 1
fi
echo "Confirmed 404 for soft-deleted product"

echo ""
echo "=== All 13 integration endpoints passed successfully! ==="
