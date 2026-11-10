import json
import logging
import sys
import time
from typing import Any, Dict
from flask import Flask, has_request_context, request


class JsonFormatter(logging.Formatter):
    """Outputs single-line JSON formatted log events with tracing context."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }

        if has_request_context():
            payload["rid"] = request.headers.get("X-Request-Id", "-")
            payload["path"] = request.path
            payload["method"] = request.method

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(app: Flask) -> None:
    """Configure structured logging and request latency monitoring."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    app.logger.handlers = [handler]
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))

    @app.before_request
    def record_start_time() -> None:
        request._t0 = time.perf_counter()

    @app.after_request
    def log_response_latency(response):
        if hasattr(request, "_t0"):
            ms = round((time.perf_counter() - request._t0) * 1000, 2)
            app.logger.info(
                "request_completed",
                extra={
                    "status": response.status_code,
                    "ms": ms,
                },
            )
        return response
