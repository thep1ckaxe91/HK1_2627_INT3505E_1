from typing import Generator
import pytest
from sqlalchemy import event
from product_api.config import TestConfig
from product_api.factory import create_app
from product_api.extensions import db


class QueryCounter:
    """SQL query interceptor used to detect 1+N query regressions."""

    def __init__(self):
        self.count = 0
        self.statements = []

    def __call__(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self.statements.append(statement)

    def reset(self):
        self.count = 0
        self.statements.clear()


@pytest.fixture(scope="session")
def app():
    """Session-scoped application configured for in-memory SQLite testing."""
    connexion_app = create_app(TestConfig)
    return connexion_app


@pytest.fixture(autouse=True)
def db_session(app):
    """Function-scoped database isolation: clean tables per test."""
    with app.app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client executing against Connexion's ASGI middleware stack."""
    return app.test_client()


@pytest.fixture
def query_counter(app):
    """Context manager fixture to count SQL queries during a test block."""
    counter = QueryCounter()
    with app.app.app_context():
        engine = db.engine
        event.listen(engine, "before_cursor_execute", counter)
        yield counter
        event.remove(engine, "before_cursor_execute", counter)
