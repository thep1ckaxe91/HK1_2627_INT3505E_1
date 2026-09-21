import random
import sqlite3
import string
import sys
from pathlib import Path

# Ensure Demo/B2/hw1 is on sys.path for direct imports
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from app import app, init_db, db_path  # noqa: E402


def generate_random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters, k=length))


def seed_database(num_rows: int = 5):
    print(f"[*] Initializing database schema at: {db_path}")
    init_db()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sample_titles = [
        "Designing Data-Intensive Applications",
        "High Performance Browser Networking",
        "Computer Systems: A Programmer's Perspective",
        "Operating Systems: Three Easy Pieces",
        "Database Internals",
        "C++ Concurrency in Action",
        "Modern Operating Systems",
    ]
    sample_authors = [
        "Martin Kleppmann",
        "Ilya Grigorik",
        "Randal Bryant",
        "Remzi Arpaci-Dusseau",
        "Alex Petrov",
        "Anthony Williams",
        "Andrew Tanenbaum",
    ]

    print(f"[*] Injecting {num_rows} random rows into 'books'...")
    book_ids = []
    for _ in range(num_rows):
        title = f"{random.choice(sample_titles)} ({generate_random_string(4)})"
        author = f"{random.choice(sample_authors)} {generate_random_string(3)}"
        cur.execute(
            "INSERT INTO books (title, author) VALUES (?, ?)", (title, author)
        )
        book_ids.append(cur.lastrowid)

    print(f"    Inserted book IDs: {book_ids}")

    print(f"[*] Injecting {num_rows} random rows into 'orders'...")
    order_ids = []
    for _ in range(num_rows):
        price = round(random.uniform(15.5, 120.0), 2)
        bid = random.choice(book_ids)
        cur.execute(
            "INSERT INTO orders (price, bid) VALUES (?, ?)", (price, bid)
        )
        order_ids.append(cur.lastrowid)

    print(f"    Inserted order IDs: {order_ids}")

    conn.commit()
    conn.close()
    print("[+] Database seeding successfully committed.\n")
    return book_ids, order_ids


def test_endpoints(book_ids: list[int], order_ids: list[int]):
    print("[*] Initiating URL integration test suite via Flask WSGI test client...")
    client = app.test_client()

    # 1. Test GET /books baseline
    print("\n--- Test 1: GET /books (default pagination) ---")
    res = client.get("/books")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.get_json()
    assert "data" in body and "pagination" in body and "_links" in body
    print(f"[PASS] Status: {res.status_code}, Total Books: {body['pagination']['total']}, Page Items: {len(body['data'])}")

    # 2. Test GET /books pagination (size=2, page=1)
    print("\n--- Test 2: GET /books?page=1&size=2 (custom pagination) ---")
    res = client.get("/books?page=1&size=2")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.get_json()
    assert body["pagination"]["size"] == 2
    assert len(body["data"]) == min(2, body["pagination"]["total"])
    assert "next" in body["_links"] if body["pagination"]["total"] > 2 else True
    print(f"[PASS] Status: {res.status_code}, Returned items: {len(body['data'])}, Links: {list(body['_links'].keys())}")

    # 3. Test GET /books validation failure (invalid page/size)
    print("\n--- Test 3: GET /books?page=invalid&size=bad (invalid query handling) ---")
    res = client.get("/books?page=invalid&size=bad")
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    body = res.get_json()
    assert "error" in body
    print(f"[PASS] Status: {res.status_code}, Error payload: {body}")

    # 4. Test GET /order/<oid> (valid order)
    test_oid = order_ids[0]
    print(f"\n--- Test 4: GET /order/{test_oid} (valid order join) ---")
    res = client.get(f"/order/{test_oid}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.get_json()
    assert body["book_id"] in book_ids
    assert "title" in body and "author" in body and "price" in body
    assert res.headers.get("Cache-Control") == "public, max-age=30"
    print(f"[PASS] Status: {res.status_code}, Payload: {body}, Cache-Control: {res.headers.get('Cache-Control')}")

    # 5. Test GET /order/<oid> (non-existent order)
    print("\n--- Test 5: GET /order/999999 (non-existent order 404) ---")
    res = client.get("/order/999999")
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    body = res.get_json()
    assert body.get("error") == "Not found"
    print(f"[PASS] Status: {res.status_code}, Error payload: {body}")

    print("\n[+] All endpoint assertion checks passed successfully.")


if __name__ == "__main__":
    b_ids, o_ids = seed_database(5)
    test_endpoints(b_ids, o_ids)
