from typing import Any, Dict, Tuple


def list_products(page: int = 1, size: int = 20) -> Tuple[Dict[str, Any], int]:
    """Stub handler for listing products with pagination."""
    return {"items": [], "page": page, "size": size, "total": 0}, 200


def create_product(body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Stub handler for creating a product."""
    return {"id": 1, **body, "archived": False}, 201


def get_product(id: int) -> Tuple[Dict[str, Any], int]:
    """Stub handler for fetching a product by ID."""
    return {
        "id": id,
        "sku": f"PROD-{id}",
        "name": f"Product {id}",
        "price_cents": 1000,
        "qty_in_stock": 10,
        "archived": False,
    }, 200


def patch_product(id: int, body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Stub handler for updating a product."""
    return {
        "id": id,
        "sku": f"PROD-{id}",
        "name": body.get("name", f"Product {id}"),
        "price_cents": body.get("price_cents", 1000),
        "qty_in_stock": 10,
        "archived": False,
    }, 200


def delete_product(id: int) -> Tuple[str, int]:
    """Stub handler for deleting a product."""
    return "", 204


def reserve_product(id: int, body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Stub handler for reserving inventory."""
    return {
        "id": id,
        "sku": f"PROD-{id}",
        "name": f"Product {id}",
        "price_cents": 1000,
        "qty_in_stock": 10 - body.get("qty", 1),
        "archived": False,
    }, 200
