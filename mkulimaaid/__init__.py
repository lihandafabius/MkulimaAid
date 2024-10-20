from flask import Flask
from flask_migrate import Migrate
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager  # Import LoginManager


# Initialize extensions
csrf = CSRFProtect()
db = SQLAlchemy()  # Initialize db here
bcrypt = Bcrypt()
login_manager = LoginManager()  # Initialize LoginManager
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app
    csrf.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)  # Initialize login_manager with the app
    migrate.init_app(app, db)

    # Set the login view (this is where users will be redirected if not authenticated)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Import and register blueprints after initialization
    from mkulimaaid.routes import main
    app.register_blueprint(main)

    return app
