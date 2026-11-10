def test_create_order_success(client):
    """Verify order creation with multiple items, price snapshotting, and stock decrement."""
    # Create two products
    p1 = client.post(
        "/api/v1/products",
        json={"sku": "ORD-P1", "name": "Item 1", "price_cents": 1000, "qty_in_stock": 10},
    ).json()
    p2 = client.post(
        "/api/v1/products",
        json={"sku": "ORD-P2", "name": "Item 2", "price_cents": 2500, "qty_in_stock": 5},
    ).json()

    # Place order: 2 of Item 1 ($20.00) + 1 of Item 2 ($25.00) = $45.00 (4500 cents)
    order_payload = {
        "items": [
            {"product_id": p1["id"], "quantity": 2},
            {"product_id": p2["id"], "quantity": 1},
        ]
    }
    r = client.post("/api/v1/orders", json=order_payload)
    assert r.status_code == 201
    order = r.json()
    assert order["id"] == 1
    assert order["total_price_cents"] == 4500
    assert len(order["items"]) == 2

    # Verify inventory was decremented
    assert client.get(f"/api/v1/products/{p1['id']}").json()["qty_in_stock"] == 8
    assert client.get(f"/api/v2/products/{p2['id']}").status_code in [200, 404]
    assert client.get(f"/api/v1/products/{p2['id']}").json()["qty_in_stock"] == 4


def test_create_order_insufficient_stock_rollback(client):
    """Verify ACID transaction rollback if one item exceeds available stock."""
    p1 = client.post(
        "/api/v1/products",
        json={"sku": "ROLL-P1", "name": "Available Item", "price_cents": 1000, "qty_in_stock": 10},
    ).json()
    p2 = client.post(
        "/api/v1/products",
        json={"sku": "ROLL-P2", "name": "Scarce Item", "price_cents": 5000, "qty_in_stock": 1},
    ).json()

    # Attempt to order 1 of Item 1 and 5 of Item 2 (Item 2 only has 1 in stock)
    r = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {"product_id": p1["id"], "quantity": 1},
                {"product_id": p2["id"], "quantity": 5},
            ]
        },
    )
    assert r.status_code == 409
    assert r.json()["error"] == "out_of_stock"

    # Crucial: verify that Item 1 was NOT decremented due to transaction rollback
    assert client.get(f"/api/v1/products/{p1['id']}").json()["qty_in_stock"] == 10


def test_orders_eager_loading_n_plus_one_prevention(client, query_counter):
    """
    Slide 42 Requirement 5:
    Prove that fetching orders with related items avoids the 1+N query problem.
    """
    # 1. Setup products
    prod = client.post(
        "/api/v1/products",
        json={"sku": "N1-ITEM", "name": "N1 Test Item", "price_cents": 500, "qty_in_stock": 100},
    ).json()

    # 2. Seed 5 distinct orders with items
    for _ in range(5):
        client.post(
            "/api/v1/orders",
            json={"items": [{"product_id": prod["id"], "quantity": 1}]},
        )

    # 3. Query orders with query counting enabled
    query_counter.reset()
    resp = client.get("/api/v1/orders?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5

    # With selectinload, the query pattern must be strictly bounded:
    # 1 query for orders (SELECT orders.*)
    # 1 query for order_items batch (SELECT order_items.* WHERE order_id IN (...))
    # 1 query for total count (SELECT count(*) FROM orders)
    # TOTAL = 3 queries. (Without eager loading, this would be 1 + 5 + 1 = 7 queries).
    assert query_counter.count == 3, (
        f"Expected 3 queries (orders, selectinload items, count), got {query_counter.count}: "
        f"{query_counter.statements}"
    )
