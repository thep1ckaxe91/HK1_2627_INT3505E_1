from datetime import datetime, timezone
import logging
from flask import Flask
from sunset import deprecate_at

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

app = Flask(__name__)

V0_SUNSET = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
V1_SUNSET = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


@app.route("/api/v0/users/<int:uid>")
@deprecate_at(V0_SUNSET, replacement="/api/v2/users")
def get_v0(uid: int):
    """Expired endpoint past sunset (returns 410 Gone)."""
    return {"id": uid, "name": "Legacy V0"}


@app.route("/api/v1/users/<int:uid>")
@deprecate_at(V1_SUNSET, replacement="/api/v2/users")
def get_v1(uid: int):
    """Deprecated endpoint before sunset (returns 200 + Sunset/Deprecation headers)."""
    return {"id": uid, "full_name": "Nguyễn Văn A"}


@app.route("/api/v2/users/<int:uid>")
def get_v2(uid: int):
    """Active successor endpoint."""
    return {"id": uid, "first_name": "Văn A", "last_name": "Nguyễn"}


if __name__ == "__main__":
    app.run()
