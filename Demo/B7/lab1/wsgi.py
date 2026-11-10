from product_api.factory import create_app

# ASGI application for Uvicorn / Connexion 3 runtime
app = create_app()

# WSGI application proxy for Flask CLI (e.g. flask db migrate)
flask_app = app.app

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0")
