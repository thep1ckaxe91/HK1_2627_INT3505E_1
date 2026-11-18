import logging
from flask import Flask, jsonify, request
from gateway import dispatch

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

app = Flask(__name__)


@app.route("/orders", methods=["POST"])
def create_order():
    """Route POST /orders to v1 or v2 handler and tag X-Order-Handler."""
    body = request.get_json()
    if not isinstance(body, dict):
        return jsonify({"error": "JSON object body required"}), 400
    which, result = dispatch(body)
    resp = jsonify(result)
    resp.headers["X-Order-Handler"] = which
    return resp, (201 if which == "v2" else 200)


if __name__ == "__main__":
    app.run()
