from functools import wraps
from flask import Flask, jsonify, request

LATEST = "2"
SUPPORTED = {"1", "2", "2024-06-20"}
USERS = {
    1: {"f": "Văn", "l": "Nguyễn", "e": "a@vnu.vn"},
    2: {"f": "Trang", "l": "Trần", "e": "b@vnu.vn"},
}
app = Flask(__name__)


def api_version(supported=SUPPORTED, default=LATEST):
    """Validate X-API-Version header and tag responses with X-API-Version-Served."""
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            v = request.headers.get("X-API-Version", default)
            if v not in supported:
                return jsonify(error="unsupported version"), 400
            result = fn(v, *args, **kwargs)
            body, status = result if isinstance(result, tuple) else (result, 200)
            response = jsonify(body)
            response.status_code = status
            response.headers["X-API-Version-Served"] = v
            return response
        return wrapper
    return decorate


@app.route("/users/<int:uid>")
@api_version()
def get_user(version, uid):
    """Return user payload formatted according to requested API version."""
    u = USERS.get(uid)
    if not u:
        return {"error": "not found"}, 404
    if version == "1":
        return {"id": uid, "full_name": f"{u['f']} {u['l']}"}
    if version == "2024-06-20":
        return {
            "id": uid,
            "first_name": u["f"],
            "last_name": u["l"],
            "display_name": f"{u['f']} {u['l']}",
            "email": u["e"],
            "api_revision": "2024-06-20",
        }
    return {
        "id": uid,
        "first_name": u["f"],
        "last_name": u["l"],
        "email": u["e"],
    }


if __name__ == "__main__":
    app.run()
