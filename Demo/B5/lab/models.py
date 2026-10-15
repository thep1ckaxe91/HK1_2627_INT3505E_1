from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Date
from datetime import datetime, timezone, timedelta

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
    role = mapped_column(String(20), default="co")  # lead, co, translator


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
    title = mapped_column(String(300), nullable=False)
    isbn = mapped_column(String(13), unique=True, nullable=True)
    published_year = mapped_column(Integer, nullable=True)
    description = mapped_column(Text, default="")
    total_copies = mapped_column(Integer, default=0)
    category_id = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    category = relationship("Category", back_populates="books")
    authors = relationship("Author", secondary="book_authors", back_populates="books")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self, fields=None):
        full = {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "publishedYear": self.published_year,
            "description": self.description,
            "totalCopies": self.total_copies,
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


class Member(db.Model):
    __tablename__ = "members"
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(255), unique=True, nullable=False)
    display_name = mapped_column(String(120), nullable=False)
    membership_type = mapped_column(String(20), default="standard")  # standard, premium, student
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    loans = relationship("Loan", back_populates="member")
    reviews = relationship("Review", back_populates="member")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "displayName": self.display_name,
            "membershipType": self.membership_type,
            "createdAt": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class BookCopy(db.Model):
    __tablename__ = "book_copies"
    id = mapped_column(Integer, primary_key=True)
    barcode = mapped_column(String(30), unique=True, nullable=False)
    status = mapped_column(String(20), default="available")  # available, loaned, damaged, lost
    book_id = mapped_column(Integer, ForeignKey("books.id"), nullable=False)
    book = relationship("Book", back_populates="copies")
    loans = relationship("Loan", back_populates="copy")

    def to_dict(self):
        return {
            "id": self.id,
            "barcode": self.barcode,
            "status": self.status,
            "bookId": self.book_id,
        }


class Loan(db.Model):
    __tablename__ = "loans"
    id = mapped_column(Integer, primary_key=True)
    loan_date = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = mapped_column(DateTime, nullable=False)
    return_date = mapped_column(DateTime, nullable=True)
    status = mapped_column(String(20), default="active")  # active, returned, overdue
    copy_id = mapped_column(Integer, ForeignKey("book_copies.id"), nullable=False)
    member_id = mapped_column(Integer, ForeignKey("members.id"), nullable=False)
    copy = relationship("BookCopy", back_populates="loans")
    member = relationship("Member", back_populates="loans")

    def to_dict(self):
        return {
            "id": self.id,
            "loanDate": self.loan_date.isoformat() + "Z" if self.loan_date else None,
            "dueDate": self.due_date.isoformat() + "Z" if self.due_date else None,
            "returnDate": self.return_date.isoformat() + "Z" if self.return_date else None,
            "status": self.status,
            "copyId": self.copy_id,
            "memberId": self.member_id,
            "copy": self.copy.to_dict() if self.copy else None,
        }


class Review(db.Model):
    __tablename__ = "reviews"
    id = mapped_column(Integer, primary_key=True)
    rating = mapped_column(Integer, nullable=False)
    comment = mapped_column(Text, default="")
    book_id = mapped_column(Integer, ForeignKey("books.id"), nullable=False)
    member_id = mapped_column(Integer, ForeignKey("members.id"), nullable=False)
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    book = relationship("Book", back_populates="reviews")
    member = relationship("Member", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "rating": self.rating,
            "comment": self.comment,
            "bookId": self.book_id,
            "member": self.member.to_dict() if self.member else None,
            "createdAt": self.created_at.isoformat() + "Z" if self.created_at else None,
        }