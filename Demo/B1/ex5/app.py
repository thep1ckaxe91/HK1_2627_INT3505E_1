from flask import Flask, jsonify, request
from uuid import uuid4

app = Flask(__name__)


orders = {}


@app.route("/orders/<id>", methods=["DELETE"])
def delete_order(order_id):
    order = orders.get(order_id)
    if order is None:
        return {"error": "not found"}, 404
    if order["status"] in ("shipped", "delivered"):
        return {"error": "cannot delete"}, 409
    orders.pop(order_id, None)

    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
