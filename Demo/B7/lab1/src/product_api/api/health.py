from typing import Any, Dict, Tuple
from sqlalchemy import text
from product_api.extensions import db


def liveness() -> Tuple[Dict[str, Any], int]:
    """Lightweight in-memory probe: verifies process event loop is alive."""
    return {"status": "ok"}, 200


def readiness() -> Tuple[Dict[str, Any], int]:
    """Dependency probe: verifies database connection pool is operational."""
    checks = {}
    try:
        db.session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "err"

    is_healthy = all(status == "ok" for status in checks.values())
    return (
        {
            "status": "ok" if is_healthy else "degraded",
            "checks": checks,
        },
        200 if is_healthy else 503,
    )
