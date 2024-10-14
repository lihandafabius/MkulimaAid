from flask import Flask
from mkulimaaid.routes import main
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(main)

    return app
