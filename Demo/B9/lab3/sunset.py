from datetime import datetime, timezone
from email.utils import format_datetime
from functools import wraps
import logging
from flask import jsonify, request

log = logging.getLogger("sunset")


def http_date(dt: datetime) -> str:
    """Format a timezone-aware datetime as an RFC 7231 GMT HTTP-date string."""
    return format_datetime(dt, usegmt=True)


def deprecate_at(sunset_date: datetime, replacement: str | None = None):
    """Attach RFC 8594 Sunset/Deprecation headers before sunset, or return 410 Gone after."""
    def wrap(fn):
        @wraps(fn)
        def inner(*a, **kw):
            now = datetime.now(timezone.utc)
            if now >= sunset_date:
                log.warning("sunset_gone %s %s", request.path, request.remote_addr)
                return jsonify({
                    "error": "gone",
                    "sunset": http_date(sunset_date),
                    "use_instead": replacement,
                }), 410

            result = fn(*a, **kw)
            body, status = result if isinstance(result, tuple) else (result, 200)
            r = jsonify(body)
            r.status_code = status
            r.headers["Sunset"] = http_date(sunset_date)
            r.headers["Deprecation"] = "true"
            if replacement:
                r.headers["Link"] = f'<{replacement}>; rel="successor-version"'
            log.warning("deprecated_call %s %s", request.path, request.remote_addr)
            return r

        return inner

    return wrap
