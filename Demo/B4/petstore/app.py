import functools
import hmac
import logging
import os
import threading
from typing import Any, Optional

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
)
logger = logging.getLogger("petstore")

API_KEY = os.environ.get("API_KEY", "test-key")


class PetDatastore:
    """Thread-safe in-memory datastore for Pet entities."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pets: dict[int, dict[str, Any]] = {
            1: {"id": 1, "name": "Shiba Inu", "tag": "dog"},
            2: {"id": 2, "name": "Scottish Fold", "tag": "cat"},
            3: {"id": 3, "name": "Goldfish", "tag": "fish"},
        }
        self._next_id: int = 4

    def list_pets(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._pets.values())[:limit]
            return [pet.copy() for pet in items]

    def get_pet(self, pet_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            pet = self._pets.get(pet_id)
            return pet.copy() if pet else None

    def create_pet(self, name: str, tag: Optional[str] = None) -> dict[str, Any]:
        with self._lock:
            pet_id = self._next_id
            self._next_id += 1
            pet: dict[str, Any] = {"id": pet_id, "name": name}
            if tag is not None:
                pet["tag"] = tag
            self._pets[pet_id] = pet
            return pet.copy()

    def update_pet(
        self,
        pet_id: int,
        name: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            pet = self._pets.get(pet_id)
            if pet is None:
                return None
            if name is not None:
                pet["name"] = name
            if tag is not None:
                pet["tag"] = tag
            return pet.copy()

    def delete_pet(self, pet_id: int) -> bool:
        with self._lock:
            if pet_id in self._pets:
                del self._pets[pet_id]
                return True
            return False


datastore = PetDatastore()


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, expose_headers=["X-Rate-Limit"])

    def require_api_key(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            key = request.headers.get("X-API-KEY")
            if not key or not hmac.compare_digest(key, API_KEY):
                return jsonify({"code": 401, "message": "Unauthorized"}), 401
            return f(*args, **kwargs)

        return decorated_function

    @app.after_request
    def inject_rate_limit(response: Response) -> Response:
        if response.status_code in (200, 201):
            response.headers["X-Rate-Limit"] = "60"
        return response

    @app.errorhandler(400)
    def handle_bad_request(err):
        message = err.description if isinstance(err.description, str) else "Bad Request"
        return jsonify({"code": 400, "message": message}), 400

    @app.errorhandler(401)
    def handle_unauthorized(err):
        message = err.description if isinstance(err.description, str) else "Unauthorized"
        return jsonify({"code": 401, "message": message}), 401

    @app.errorhandler(404)
    def handle_not_found(err):
        message = err.description if isinstance(err.description, str) else "Not Found"
        return jsonify({"code": 404, "message": message}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({"code": 405, "message": "Method Not Allowed"}), 405

    @app.errorhandler(500)
    def handle_internal_server_error(err):
        return jsonify({"code": 500, "message": "Internal Server Error"}), 500

    def _dispatch_callback(callback_url: str, pet_data: dict[str, Any]) -> None:
        try:
            resp = requests.post(callback_url, json=pet_data, timeout=5)
            logger.info(
                "Dispatched callback to %s: status %s",
                callback_url,
                resp.status_code,
            )
        except Exception as exc:
            logger.warning("Callback execution failed for %s: %s", callback_url, exc)

    @app.route("/pets", methods=["GET"])
    @app.route("/api/pets", methods=["GET"])
    def list_pets():
        raw_limit = request.args.get("limit", default=20)
        try:
            limit = int(raw_limit)
            if limit < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return (
                jsonify(
                    {
                        "code": 400,
                        "message": "Limit parameter must be a non-negative integer",
                    }
                ),
                400,
            )

        pets = datastore.list_pets(limit=limit)
        return jsonify(pets), 200

    @app.route("/pets", methods=["POST"])
    @app.route("/api/pets", methods=["POST"])
    @require_api_key
    def create_pet():
        if not request.is_json:
            return jsonify({"code": 400, "message": "Expected JSON payload"}), 400

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "Malformed JSON object"}), 400

        name = data.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            return (
                jsonify(
                    {
                        "code": 400,
                        "message": "Field 'name' is required and must be a non-empty string",
                    }
                ),
                400,
            )

        tag = data.get("tag")
        if tag is not None and not isinstance(tag, str):
            return jsonify({"code": 400, "message": "Field 'tag' must be a string"}), 400

        callback_url = data.get("callbackUrl")
        if callback_url is not None and not isinstance(callback_url, str):
            return (
                jsonify({"code": 400, "message": "Field 'callbackUrl' must be a string"}),
                400,
            )

        created_pet = datastore.create_pet(name=name.strip(), tag=tag)

        if callback_url:
            threading.Thread(
                target=_dispatch_callback,
                args=(callback_url, created_pet),
                daemon=True,
                name=f"callback-pet-{created_pet['id']}",
            ).start()

        return jsonify(created_pet), 201

    @app.route("/pets/<int:pet_id>", methods=["GET"])
    @app.route("/api/pets/<int:pet_id>", methods=["GET"])
    def get_pet_by_id(pet_id: int):
        pet = datastore.get_pet(pet_id)
        if pet is None:
            return jsonify({"code": 404, "message": "Pet not found"}), 404
        return jsonify(pet), 200

    @app.route("/pets/<int:pet_id>", methods=["PATCH"])
    @app.route("/api/pets/<int:pet_id>", methods=["PATCH"])
    @require_api_key
    def patch_pet_by_id(pet_id: int):
        if datastore.get_pet(pet_id) is None:
            return jsonify({"code": 404, "message": "Pet not found"}), 404

        if not request.is_json:
            return jsonify({"code": 400, "message": "Expected JSON payload"}), 400

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "Malformed JSON object"}), 400

        name = data.get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            return (
                jsonify(
                    {
                        "code": 400,
                        "message": "Field 'name' must be a non-empty string",
                    }
                ),
                400,
            )

        tag = data.get("tag")
        if tag is not None and not isinstance(tag, str):
            return jsonify({"code": 400, "message": "Field 'tag' must be a string"}), 400

        updated_pet = datastore.update_pet(
            pet_id=pet_id,
            name=name.strip() if name is not None else None,
            tag=tag,
        )
        return jsonify(updated_pet), 200

    @app.route("/pets/<int:pet_id>", methods=["DELETE"])
    @app.route("/api/pets/<int:pet_id>", methods=["DELETE"])
    @require_api_key
    def delete_pet_by_id(pet_id: int):
        deleted = datastore.delete_pet(pet_id)
        if not deleted:
            return jsonify({"code": 404, "message": "Pet not found"}), 404
        return "", 204

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
