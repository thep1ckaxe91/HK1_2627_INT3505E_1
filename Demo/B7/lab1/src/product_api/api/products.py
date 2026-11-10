from typing import Any, Dict, Tuple
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from product_api.extensions import db
from product_api.models.product import Product
from product_api.errors import Conflict, NotFound, OutOfStock


def list_products(page: int = 1, size: int = 20) -> Tuple[Dict[str, Any], int]:
    """Retrieve paginated non-archived products."""
    page = max(1, page)
    size = min(100, max(1, size))

    base_query = db.select(Product).where(Product.archived.is_(False))
    rows = (
        db.session.execute(
            base_query.order_by(Product.id)
            .offset((page - 1) * size)
            .limit(size)
        )
        .scalars()
        .all()
    )

    total = db.session.scalar(
        db.select(func.count()).select_from(Product).where(Product.archived.is_(False))
    ) or 0

    return {
        "items": [p.to_dict() for p in rows],
        "page": page,
        "size": size,
        "total": total,
    }, 200


def create_product(body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Create a new product record."""
    product = Product(**body)
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict("sku already exists")

    return product.to_dict(), 201


def get_product(id: int) -> Tuple[Dict[str, Any], int]:
    """Retrieve a single non-archived product by ID."""
    product = db.session.get(Product, id)
    if product is None or product.archived:
        raise NotFound(f"product with id {id} not found")

    return product.to_dict(), 200


def patch_product(id: int, body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Partially update non-archived product attributes."""
    product = db.session.get(Product, id)
    if product is None or product.archived:
        raise NotFound(f"product with id {id} not found")

    for key, value in body.items():
        setattr(product, key, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict("update violated database constraint")

    return product.to_dict(), 200


def delete_product(id: int) -> Tuple[str, int]:
    """Soft delete product by setting archived = True."""
    product = db.session.get(Product, id)
    if product is None or product.archived:
        raise NotFound(f"product with id {id} not found")

    product.archived = True
    db.session.commit()
    return "", 204


def reserve_product(id: int, body: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Atomically reserve stock quantity using conditional UPDATE.
    Eliminates TOCTOU race conditions under concurrent execution.
    """
    qty = body["qty"]

    # Atomic decrement: executed directly in DB engine
    stmt = (
        db.update(Product)
        .where(Product.id == id, Product.archived.is_(False), Product.qty_in_stock >= qty)
        .values(qty_in_stock=Product.qty_in_stock - qty)
        .returning(Product)
    )
    res = db.session.execute(stmt).scalar_one_or_none()

    if res is not None:
        db.session.commit()
        return res.to_dict(), 200

    # If row was not updated, inspect state to determine precise error
    product = db.session.get(Product, id)
    if product is None or product.archived:
        raise NotFound(f"product with id {id} not found")

    raise OutOfStock(f"only {product.qty_in_stock} left, cannot reserve {qty}")
