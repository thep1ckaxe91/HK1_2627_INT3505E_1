USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"},
}


def get_user(uid: int) -> dict | None:
    """Return user record by 1-based integer ID, or None if missing."""
    return USERS.get(uid)


def create_user(first_name: str, last_name: str, email: str) -> tuple[int, dict]:
    """Insert a new user record and return its allocated (id, record)."""
    uid = max(USERS.keys(), default=0) + 1
    record = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
    }
    USERS[uid] = record
    return uid, record
