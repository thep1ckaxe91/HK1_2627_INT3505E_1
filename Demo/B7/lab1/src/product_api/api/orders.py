from typing import Any, Dict, Tuple
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from product_api.extensions import db
from product_api.models.order import Order, OrderItem
from product_api.models.product import Product
from product_api.errors import NotFound, OutOfStock


def list_orders(page: int = 1, size: int = 20) -> Tuple[Dict[str, Any], int]:
    """
    Retrieve paginated orders.
    Uses selectinload(Order.items) to eliminate the 1+N query penalty.
    """
    page = max(1, page)
    size = min(100, max(1, size))

    stmt = (
        db.select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    orders = db.session.execute(stmt).scalars().all()

    total = db.session.scalar(db.select(func.count()).select_from(Order)) or 0

    return {
        "items": [order.to_dict() for order in orders],
        "page": page,
        "size": size,
        "total": total,
    }, 200


def create_order(body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Atomically place an order, decrementing stock and snapshotting prices.
    Executes within a single ACID transaction.
    """
    items_data = body["items"]

    order = Order(total_price_cents=0)
    db.session.add(order)

    total_price = 0

    for item in items_data:
        pid = item["product_id"]
        qty = item["quantity"]

        # Atomic reservation on Product
        stmt = (
            db.update(Product)
            .where(Product.id == pid, Product.archived.is_(False), Product.qty_in_stock >= qty)
            .values(qty_in_stock=Product.qty_in_stock - qty)
            .returning(Product)
        )
        updated_product = db.session.execute(stmt).scalar_one_or_none()

        if updated_product is None:
            # Check why it failed
            p = db.session.get(Product, pid)
            if p is None or p.archived:
                db.session.rollback()
                raise NotFound(f"product with id {pid} not found")
            db.session.rollback()
            raise OutOfStock(f"insufficient stock for product {pid}: requested {qty}, available {p.qty_in_stock}")

        line_item = OrderItem(
            order=order,
            product_id=pid,
            name=updated_product.name,
            price_cents=updated_product.price_cents,
            quantity=qty,
        )
        db.session.add(line_item)
        total_price += updated_product.price_cents * qty

    order.total_price_cents = total_price
    db.session.commit()

    return order.to_dict(), 201


def get_order(id: int) -> Tuple[Dict[str, Any], int]:
    """Retrieve an order by ID with its line items eagerly loaded."""
    stmt = (
        db.select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == id)
    )
    order = db.session.execute(stmt).scalar_one_or_none()

    if order is None:
        raise NotFound(f"order with id {id} not found")

    return order.to_dict(), 200
