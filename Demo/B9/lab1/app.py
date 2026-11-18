from flasj import Flask
from blueprints.v1 import bp as v1_bp
from blueprints.v2 import bp as v2_bp

app = Flask(__name__)
app.register_blueprint(v1_bp, url_prefix="/api/v1")
app.register_blueprint(v2_bp, url_prefix="/api/v2")
