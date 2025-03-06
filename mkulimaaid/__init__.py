from flask import Flask
from flask_migrate import Migrate
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ckeditor import CKEditor  # Import CKEditor

# Initialize extensions
csrf = CSRFProtect()
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
ckeditor = CKEditor()  # Initialize CKEditor

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app
    csrf.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_message = "Please log in to access MkulimaAid."
    migrate.init_app(app, db)
    ckeditor.init_app(app)  # Initialize CKEditor with the app

    # Configure CKEditor file uploader endpoint
    app.config['CKEDITOR_FILE_UPLOADER'] = 'main.upload'  # Set the correct endpoint

    # Set the login view
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Import and register blueprints after initialization
    from mkulimaaid.routes import main
    app.register_blueprint(main)

    return app
