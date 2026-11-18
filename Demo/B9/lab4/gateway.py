import hashlib
import logging
import os
from flask import request
from handlers import v1_create_order, v2_create_order

# Config: flip V2_PERCENT via environment or dashboard (default 5%)
V2_PERCENT = int(os.getenv("V2_PERCENT", "5"))
V2_COHORTS = {"beta", "internal"}
V2_FORCE_ACCOUNTS = {"acct_42", "acct_99"}

log = logging.getLogger("gateway")


def route_to_v2(body: dict) -> tuple[bool, str]:
    """Evaluate 3-tier blue-green routing rules and return (use_v2, reason)."""
    # 1. Explicit cohort has highest priority
    cohort = request.headers.get("X-Cohort", "").lower()
    if cohort in V2_COHORTS:
        return True, f"cohort:{cohort}"

    # 2. Allow-listed account
    acct = body.get("account_id", "")
    if acct in V2_FORCE_ACCOUNTS:
        return True, "allowlist"

    # 3. Deterministic percentage bucket
    if V2_PERCENT <= 0:
        return False, "percent:0"
    bucket = int(hashlib.md5(acct.encode()).hexdigest(), 16) % 100
    use_v2 = bucket < V2_PERCENT
    return use_v2, f"bucket:{bucket}<{V2_PERCENT}"


def dispatch(body: dict) -> tuple[str, dict]:
    """Dispatch order payload to v1 or v2 handler based on routing decision."""
    use_v2, reason = route_to_v2(body)
    which = "v2" if use_v2 else "v1"
    log.info("dispatch account=%s target=%s reason=%s", body.get("account_id", ""), which, reason)
    if use_v2:
        return "v2", v2_create_order(body)
    return "v1", v1_create_order(body)
