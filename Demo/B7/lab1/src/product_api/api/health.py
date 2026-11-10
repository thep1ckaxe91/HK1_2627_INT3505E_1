from flask import Blueprint, jsonify
from sqlalchemy import text
from product_api.extensions import db

health_bp = Blueprint("health", __name__, url_prefix="")


@health_bp.get("/healthz")
def liveness():
    """Liveness probe: verifies process event loop is alive (no DB overhead)."""
    return jsonify({"status": "ok"}), 200


@health_bp.get("/ready")
def readiness():
    """Readiness probe: verifies database connection pool is operational."""
    checks = {}
    try:
        db.session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "err"

    is_ok = all(v == "ok" for v in checks.values())
    return (
        jsonify({"status": "ok" if is_ok else "degraded", "checks": checks}),
        200 if is_ok else 503,
    )
