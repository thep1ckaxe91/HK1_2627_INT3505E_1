from pathlib import Path
from flask import Flask, send_from_directory
from blueprints.v1 import bp as v1_bp
from blueprints.v2 import bp as v2_bp

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.register_blueprint(v1_bp, url_prefix="/api/v1")
app.register_blueprint(v2_bp, url_prefix="/api/v2")


@app.route("/openapi.yaml", methods=["GET"])
def openapi_spec():
    """Serve OpenAPI 3.0 specification for v1 and v2 user endpoints."""
    return send_from_directory(BASE_DIR, "openapi.yaml", mimetype="application/yaml")


if __name__ == "__main__":
    app.run()
