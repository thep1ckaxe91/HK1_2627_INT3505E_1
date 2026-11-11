"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""

from jsonschema import validate, ValidationError
import pytest
from tools import get_book_schema

def test_empty_db(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.get_json() == []

def test_not_found(client):
    resp = client.get("/books/9999")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["code"] == "NOT_FOUND"

def test_fail_validation(client):
    res = client.post("/books", json={"author": "Someone"})
    assert res.status_code == 400
    data = res.get_json()
    assert any(err["field"] == "title" for err in data["errors"])

def test_life_cycle(client):
    res = client.post("/books", json={"title":"T", "author": "A", "year": 2020})
    bid = res.get_json()['id']
    del_res = client.delete(f"/books/{bid}")
    assert del_res.status_code == 200 | del_res.status_code == 204
    assert client.get(f"/books/{bid}").status_code == 404
