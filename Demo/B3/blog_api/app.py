from flask import Flask, jsonify, request, make_response, Blueprint
from uuid import uuid4, UUID

app = Flask(__name__)
DEFAULT_SIZE = 20
MAX_SIZE = 100
posts = {}
tags = set()
users = {}
users_follow: dict[UUID, set] = {}
comments = {}

v1_bp = Blueprint("v1", __name__)

@v1_bp.get("/posts")
def get_posts():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify(error="Page and size must be int"), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)

    posts

@v1_bp.get("/posts/<id:UUID>")
def get_post(id : UUID):
  pass
    

@v1_bp.get("/comments")
def list_comments():
    pass

app.register_blueprint(v1_bp, url_prefix="/api/v1")

if __name__ == "__main__":
    app.run()
