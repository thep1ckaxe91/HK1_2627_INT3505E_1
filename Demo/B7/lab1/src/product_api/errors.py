import json
import logging
from typing import Optional
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
import connexion
from connexion.exceptions import ProblemException
from connexion.lifecycle import ConnexionRequest, ConnexionResponse

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Base exception for all business domain errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str = "",
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class OutOfStock(ApiError):
    status_code = 409
    code = "out_of_stock"


class ValidationFailed(ApiError):
    status_code = 422
    code = "validation_error"


def _handle_connexion_problem(
    request: ConnexionRequest, exc: ProblemException
) -> ConnexionResponse:
    # Map Connexion 400 requestBody/parameter schema violations to 422 per Slide/OpenAPI contract
    status = 422 if exc.status == 400 else (exc.status or 400)
    error_code = (
        "validation_error"
        if status == 422
        else (exc.title or "error").lower().replace(" ", "_")
    )

    payload = {
        "error": error_code,
        "detail": exc.detail or str(exc),
    }

    return ConnexionResponse(
        status_code=status,
        mimetype="application/json",
        body=json.dumps(payload),
    )


def register_error_handlers(connexion_app: connexion.FlaskApp) -> None:
    """Register uniform RFC-compliant error handlers across Flask and Connexion layers."""
    flask_app: Flask = connexion_app.app

    # Connexion-level ASGI middleware errors (OpenAPI validation / parsing)
    connexion_app.add_error_handler(ProblemException, _handle_connexion_problem)

    # Business domain exceptions
    @flask_app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return jsonify({"error": err.code, "detail": err.message}), err.status_code

    # Standard HTTP exceptions (e.g. 404, 405 from Flask/Werkzeug)
    @flask_app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        code = err.name.lower().replace(" ", "_") if err.name else "http_error"
        return jsonify({"error": code, "detail": err.description or ""}), err.code

    # Fallback for unhandled 500 exceptions
    @flask_app.errorhandler(Exception)
    def handle_unhandled_exception(err: Exception):
        flask_app.logger.exception("Unhandled server exception: %s", str(err))
        return jsonify({
            "error": "internal_error",
            "detail": "An internal server error occurred.",
        }), 500
