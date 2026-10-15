from flask import Flask
from models import db


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Register blueprints
    from routes.books import bp as books_bp
    from routes.authors import bp as authors_bp
    from routes.categories import bp as categories_bp
    from routes.users import bp as users_bp

    app.register_blueprint(books_bp)
    app.register_blueprint(authors_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(users_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
