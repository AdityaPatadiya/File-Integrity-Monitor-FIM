# src/api/main.py
import os
from flask import Flask, jsonify
from src.api.routes.auth_routes import auth_bp
from src.api.routes.fim_routes import fim_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("API_SECRET_KEY", "replace_this_secret")

    # register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(fim_bp, url_prefix="/api/v1/fim")

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("API_PORT", 5000)), debug=True)
    