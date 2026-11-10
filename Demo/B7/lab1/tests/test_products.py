def test_health_probes(client):
    """Verify unauthenticated liveness and readiness probes."""
    r_live = client.get("/healthz")
    assert r_live.status_code == 200
    assert r_live.json() == {"status": "ok"}

    r_ready = client.get("/ready")
    assert r_ready.status_code == 200
    assert r_ready.json() == {"status": "ok", "checks": {"db": "ok"}}


def test_create_product_success(client):
    """Verify standard product creation returns 201 Created and correct schema."""
    payload = {
        "sku": "KB-MECH-01",
        "name": "Custom Mechanical Keyboard",
        "description": "Hot-swappable switches",
        "price_cents": 12500,
        "qty_in_stock": 15,
    }
    resp = client.post("/api/v1/products", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == 1
    assert data["sku"] == payload["sku"]
    assert data["name"] == payload["name"]
    assert data["price_cents"] == payload["price_cents"]
    assert data["qty_in_stock"] == 15
    assert data["archived"] is False


def test_create_product_validation_errors(client):
    """Verify OpenAPI schema contract rejection with HTTP 422."""
    # 1. Missing required field 'sku'
    r1 = client.post("/api/v1/products", json={"name": "No SKU", "price_cents": 100})
    assert r1.status_code == 422
    assert r1.json()["error"] == "validation_error"

    # 2. Invalid price (negative)
    r2 = client.post("/api/v1/products", json={"sku": "NEG-01", "name": "Negative", "price_cents": -10})
    assert r2.status_code == 422

    # 3. SKU too short (min length 3)
    r3 = client.post("/api/v1/products", json={"sku": "A", "name": "Short SKU", "price_cents": 100})
    assert r3.status_code == 422


def test_create_product_conflict_duplicate_sku(client):
    """Verify 409 Conflict when attempting to insert identical SKU."""
    payload = {"sku": "DUP-SKU-99", "name": "Item A", "price_cents": 500}
    r1 = client.post("/api/v1/products", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/products", json=payload)
    assert r2.status_code == 409
    assert r2.json()["error"] == "conflict"


def test_get_product_by_id_and_404(client):
    """Verify single product retrieval and 404 behavior."""
    resp = client.post(
        "/api/v1/products",
        json={"sku": "FIND-ME", "name": "Found Product", "price_cents": 200},
    )
    prod_id = resp.json()["id"]

    # Existing ID
    r_get = client.get(f"/api/v1/products/{prod_id}")
    assert r_get.status_code == 200
    assert r_get.json()["sku"] == "FIND-ME"

    # Non-existent ID
    r_not_found = client.get("/api/v1/products/9999")
    assert r_not_found.status_code == 404
    assert r_not_found.json()["error"] == "not_found"


def test_list_products_pagination_and_archived_filtering(client):
    """Verify pagination envelope and soft-deleted product filtering."""
    # Seed 5 products
    for i in range(1, 6):
        client.post(
            "/api/v1/products",
            json={"sku": f"LIST-P{i:02d}", "name": f"Product {i}", "price_cents": i * 100},
        )

    # Page 1 with size 2
    r_page1 = client.get("/api/v1/products?page=1&size=2")
    assert r_page1.status_code == 200
    data1 = r_page1.json()
    assert data1["page"] == 1
    assert data1["size"] == 2
    assert data1["total"] == 5
    assert len(data1["items"]) == 2
    assert data1["items"][0]["sku"] == "LIST-P01"

    # Soft delete item 1
    r_del = client.delete("/api/v1/products/1")
    assert r_del.status_code == 204

    # List again: item 1 should be excluded from items and total count
    r_page_after = client.get("/api/v1/products?page=1&size=10")
    data_after = r_page_after.json()
    assert data_after["total"] == 4
    assert all(item["id"] != 1 for item in data_after["items"])


def test_patch_product(client):
    """Verify partial updates via PATCH."""
    r = client.post(
        "/api/v1/products",
        json={"sku": "PATCH-01", "name": "Original Name", "price_cents": 1000},
    )
    prod_id = r.json()["id"]

    # Patch only name
    r_patch = client.patch(f"/api/v1/products/{prod_id}", json={"name": "Updated Name"})
    assert r_patch.status_code == 200
    assert r_patch.json()["name"] == "Updated Name"
    assert r_patch.json()["price_cents"] == 1000

    # Non-existent ID
    assert client.patch("/api/v1/products/8888", json={"name": "Ghost"}).status_code == 404


def test_reserve_product_concurrency_and_out_of_stock(client):
    """Verify stock reservation decrements correctly and rejects overselling with 409."""
    r = client.post(
        "/api/v1/products",
        json={"sku": "RES-01", "name": "Limited Stock", "price_cents": 5000, "qty_in_stock": 3},
    )
    prod_id = r.json()["id"]

    # Reserve 2 items
    r_res1 = client.post(f"/api/v1/products/{prod_id}/reserve", json={"qty": 2})
    assert r_res1.status_code == 200
    assert r_res1.json()["qty_in_stock"] == 1

    # Attempt to reserve 2 items when only 1 is left (409 Conflict / OutOfStock)
    r_res2 = client.post(f"/api/v1/products/{prod_id}/reserve", json={"qty": 2})
    assert r_res2.status_code == 409
    assert r_res2.json()["error"] == "out_of_stock"

    # Stock should remain 1
    r_check = client.get(f"/api/v1/products/{prod_id}")
    assert r_check.json()["qty_in_stock"] == 1
