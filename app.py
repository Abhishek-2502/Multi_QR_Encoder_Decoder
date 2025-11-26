from flask import Flask
from blueprints.web import web_bp
from blueprints.api import api_bp

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
