from flask import Flask, jsonify
from errors import ApiProblem
user = [
    {
        "id" : 1000,
        "name" : "ok"
    }
]

app = Flask(__name__)

def find_user(id):
    return next((u for u in user if u["id"] == id), None)

@app.errorhandler(ApiProblem)
@app.get("/users/<int:id>")
def get_user(id):
    user = find_user(id)
    if not user:
        raise ApiProblem(
            status=404,
            title="User not found",
            type_path="user-not-found",
            resource_id=id
        )
    return jsonify(user)

if __name__ == "__main__":
    app.run()
