from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from datetime import datetime, timezone

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = "categories"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    slug = mapped_column(String(100), unique=True, nullable=False)
    books = relationship("Book", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
        }


class BookAuthor(db.Model):
    __tablename__ = "book_authors"
    id = mapped_column(Integer, primary_key=True)
    book_id = mapped_column(Integer, ForeignKey("books.id"), nullable=False)
    author_id = mapped_column(Integer, ForeignKey("authors.id"), nullable=False)
    role = mapped_column(String(10), default="co")  # lead, co, ed


class Author(db.Model):
    __tablename__ = "authors"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    bio = mapped_column(Text, default="")
    books = relationship("Book", secondary="book_authors", back_populates="authors")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
        }


class Book(db.Model):
    __tablename__ = "books"
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(200), nullable=False)
    isbn = mapped_column(String(13), unique=True, nullable=True)
    price_vnd = mapped_column(Integer, default=0)
    stock = mapped_column(Integer, default=0)
    category_id = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    category = relationship("Category", back_populates="books")
    authors = relationship("Author", secondary="book_authors", back_populates="books")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self, fields=None):
        full = {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "price": {"amount": self.price_vnd, "currency": "VND"},
            "stock": self.stock,
            "category": self.category.to_dict() if self.category else None,
            "authors": [],
            "createdAt": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
        # Populate authors with role from junction table
        if self.authors:
            from sqlalchemy import select
            for a in self.authors:
                ba = db.session.execute(
                    select(BookAuthor).filter_by(book_id=self.id, author_id=a.id)
                ).scalar_one_or_none()
                full["authors"].append({
                    "id": a.id,
                    "name": a.name,
                    "role": ba.role if ba else "co",
                })
        if fields is None:
            return full
        return {k: v for k, v in full.items() if k in fields}


class User(db.Model):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(255), unique=True, nullable=False)
    display_name = mapped_column(String(120), nullable=False)
    reviews = relationship("Review", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "displayName": self.display_name,
        }


class Review(db.Model):
    __tablename__ = "reviews"
    id = mapped_column(Integer, primary_key=True)
    rating = mapped_column(Integer, nullable=False)
    comment = mapped_column(Text, default="")
    book_id = mapped_column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "rating": self.rating,
            "comment": self.comment,
            "bookId": self.book_id,
            "user": self.user.to_dict() if self.user else None,
            "createdAt": self.created_at.isoformat() + "Z" if self.created_at else None,
        }