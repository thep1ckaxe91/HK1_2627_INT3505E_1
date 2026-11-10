from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from product_api.extensions import db


class Product(db.Model):
    """
    Persistence model for products.
    Follows typed Declarative Mapping (SQLAlchemy 2.0+ / Flask-SQLAlchemy 3.x).
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_in_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    archived: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        """Serialize model state to JSON-compliant dictionary matching ProductOut."""
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "price_cents": self.price_cents,
            "qty_in_stock": self.qty_in_stock,
            "archived": self.archived,
        }
