from flask import Flask, jsonify, request
import base64
import json

app = Flask(__name__)

orders = [
    {"id": 1, "customer_id": 101, "status": "paid", "product_id": 201, "total": 150.0},
    {"id": 2, "customer_id": 102, "status": "shipped", "product_id": 202, "total": 45.5},
    {"id": 3, "customer_id": 101, "status": "pending", "product_id": 203, "total": 300.0},
    {"id": 4, "customer_id": 103, "status": "paid", "product_id": 201, "total": 85.0},
    {"id": 5, "customer_id": 104, "status": "cancelled", "product_id": 204, "total": 120.0},
    {"id": 6, "customer_id": 102, "status": "paid", "product_id": 205, "total": 510.0},
    {"id": 7, "customer_id": 105, "status": "shipped", "product_id": 202, "total": 65.0},
    {"id": 8, "customer_id": 101, "status": "paid", "product_id": 206, "total": 210.0},
    {"id": 9, "customer_id": 103, "status": "pending", "product_id": 207, "total": 95.0},
    {"id": 10, "customer_id": 106, "status": "paid", "product_id": 208, "total": 400.0},
]


def encode_cursor(last_id):
    cursor_data = json.dumps({"id": last_id})
    return base64.urlsafe_b64encode(cursor_data.encode()).decode()


def decode_cursor(cursor_string):
    try:
        decoded_bytes = base64.urlsafe_b64decode(cursor_string.encode())
        return json.loads(decoded_bytes.decode()).get("id")
    except Exception:
        return None


@app.get("/orders")
def list_orders():
    # 1. Parse and validate limit
    limit_raw = request.args.get("limit", default="10")
    try:
        limit = int(limit_raw)
        if limit <= 0:
            return jsonify({"error": "limit must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    query = list(orders)

    # 2. Filter: status, customer_id
    status_filter = request.args.get("status")
    if status_filter:
        query = [o for o in query if o.get("status") == status_filter]

    customer_id_filter = request.args.get("customer_id")
    if customer_id_filter:
        try:
            cid = int(customer_id_filter)
            query = [o for o in query if o.get("customer_id") == cid]
        except ValueError:
            return jsonify({"error": "customer_id must be an integer"}), 400

    # 3. Sort
    sort_param = request.args.get("sort", default="id")
    order_param = request.args.get("order", default=request.args.get("direction", "asc"))
    reverse = order_param.lower() == "desc"

    if sort_param.startswith("-"):
        sort_key = sort_param[1:]
        reverse = True
    elif sort_param.startswith("+"):
        sort_key = sort_param[1:]
    elif ":" in sort_param:
        parts = sort_param.split(":", 1)
        sort_key = parts[0]
        reverse = parts[1].lower() == "desc"
    else:
        sort_key = sort_param

    valid_keys = {"id", "customer_id", "status", "product_id", "total"}
    if sort_key not in valid_keys:
        return jsonify({"error": f"Invalid sort key '{sort_key}'. Allowed: {sorted(list(valid_keys))}"}), 400

    # Primary sort by sort_key, secondary tie-breaker by id for deterministic cursor pagination
    query.sort(key=lambda o: (o.get(sort_key), o.get("id")), reverse=reverse)

    # 4. Cursor pagination
    cursor_str = request.args.get("cursor", default=None)
    if cursor_str:
        last_id = decode_cursor(cursor_str)
        if last_id is None:
            return jsonify({"error": "Invalid cursor format"}), 400

        # Locate the cursor position in the sorted, filtered sequence
        cursor_idx = next((i for i, o in enumerate(query) if o.get("id") == last_id), None)
        if cursor_idx is not None:
            query = query[cursor_idx + 1 :]
        else:
            query = []

    results = query[: limit + 1]
    has_next = len(results) > limit
    if has_next:
        paged_items = results[:limit]
        next_cursor = encode_cursor(paged_items[-1]["id"])
    else:
        paged_items = results
        next_cursor = None

    # 5. Sparse fieldsets
    fields_param = request.args.get("fields")
    if fields_param:
        requested_fields = [f.strip() for f in fields_param.split(",") if f.strip()]
        data = [{k: item[k] for k in requested_fields if k in item} for item in paged_items]
    else:
        data = [dict(item) for item in paged_items]

    return jsonify(
        {
            "data": data,
            "pagination": {
                "limit": limit,
                "next_cursor": next_cursor,
                "has_next": has_next,
            },
        }
    )


if __name__ == "__main__":
    app.run()
