from typing import Any, Dict, Tuple


def list_orders(page: int = 1, size: int = 20) -> Tuple[Dict[str, Any], int]:
    """Stub handler for listing orders."""
    return {"items": [], "page": page, "size": size, "total": 0}, 200


def create_order(body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Stub handler for placing an order."""
    return {
        "id": 1,
        "items": [
            {
                "id": 1,
                "product_id": item["product_id"],
                "name": "Stub Item",
                "price_cents": 1000,
                "quantity": item["quantity"],
            }
            for item in body.get("items", [])
        ],
        "total_price_cents": 1000 * sum(i["quantity"] for i in body.get("items", [])),
    }, 201


def get_order(id: int) -> Tuple[Dict[str, Any], int]:
    """Stub handler for fetching an order by ID."""
    return {
        "id": id,
        "items": [],
        "total_price_cents": 0,
    }, 200
