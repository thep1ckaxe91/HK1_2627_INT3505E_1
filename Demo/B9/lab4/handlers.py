from itertools import count

_ORDER_SEQ = count(1000)


def v1_create_order(body: dict) -> dict:
    """Handle order creation using the legacy v1 response schema."""
    return {
        "order_id": f"ord_{next(_ORDER_SEQ)}",
        "account_id": body.get("account_id", ""),
        "status": "created",
        "version": "v1",
    }


def v2_create_order(body: dict) -> dict:
    """Handle order creation using the v2 response schema."""
    return {
        "order_id": f"ord_{next(_ORDER_SEQ)}",
        "account_id": body.get("account_id", ""),
        "items": body.get("items", []),
        "currency": body.get("currency", "VND"),
        "status": "created",
        "version": "v2",
    }
