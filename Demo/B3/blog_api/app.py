from flask import Flask, jsonify, request, make_response, Blueprint
from uuid import uuid4, UUID
from faker import Faker

fake = Faker()
def generate_blogs(count: int = 5) -> dict[str, dict]:
    Faker.seed(123)
    
    blogs = {}
    for _ in range(count):
        views = fake.random_int(min=50, max=100_000)
        blogs[str(uuid4())] = {
            "title": fake.sentence(nb_words=6).rstrip("."),
            "body": fake.paragraph(nb_sentences=5),
            "author": fake.name(),
            "views": views,
            "likes": fake.random_int(min=0, max=views),
        }
    return blogs

app = Flask(__name__)
DEFAULT_SIZE = 20
MAX_SIZE = 100
posts: dict[str,dict] = generate_blogs(100)


v1_bp = Blueprint("v1", __name__)

@v1_bp.get("/posts")
def list_posts():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", DEFAULT_SIZE))
    except ValueError:
        return jsonify(error="Page and size must be int"), 400

    page = max(page, 1)
    per_page = max(min(per_page, MAX_SIZE), 1)

    sort_by = request.args.get("sort", None)
    sort_dir = request.args.get("direction","asc")
    direction = False if sort_dir == "asc" else True 
    res = [p for p in posts.values()]

    if len(res) != 0 and sort_by:
        if sort_by not in res[0].keys():
            return jsonify(error=f"Sort key must be in list {res[0].keys()}"), 400
        res.sort(key=lambda p : p[sort_by], reverse=direction)

    start = page*per_page
    end = start + per_page
    res = res[start:end]

    return jsonify(res), 200

app.register_blueprint(v1_bp, url_prefix="/api/v1")

if __name__ == "__main__":
    app.run()
