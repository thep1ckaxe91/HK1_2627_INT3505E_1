from datetime import datetime, timezone
from flask import Flask
from sunset import deprecate_at

app = Flask(__name__)
V1_SUNSET = datetime(2026, 12, 31, 23, 59, 59,
                     tzinfo=timezone.utc)


@app.route("/api/v1/users/<int:uid>")
@deprecate_at(V1_SUNSET, replacement="/api/v2/users")
def get_v1(uid):
    return {"id": uid, "full_name": "Nguyễn Văn A"}
