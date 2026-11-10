from datetime import datetime
from typing import List
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from product_api.extensions import db


class Order(db.Model):
    """
    Persistence model for customer orders.
    Has a 1-to-Many relationship with OrderItem.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    total_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # 1-to-Many relationship with OrderItem
    # cascade="all, delete-orphan" guarantees that orphaned items are purged on order deletion
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self) -> dict:
        """Serialize Order aggregate to dictionary matching OrderOut schema."""
        return {
            "id": self.id,
            "items": [item.to_dict() for item in self.items],
            "total_price_cents": self.total_price_cents,
        }


class OrderItem(db.Model):
    """
    Associative entity linking Order and Product.
    Captures snapshot product pricing at execution time.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product")

    def to_dict(self) -> dict:
        """Serialize OrderItem to dictionary matching OrderItemOut schema."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "name": self.name,
            "price_cents": self.price_cents,
            "quantity": self.quantity,
        }
