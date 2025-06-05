from flask import Flask, request, session
from flask_migrate import Migrate
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_mail import Mail
from flask_babel import Babel, _

# Initialize extensions
csrf = CSRFProtect()
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
ckeditor = CKEditor()
mail = Mail()

def get_locale():
    return session.get('lang') or request.accept_languages.best_match(Config.LANGUAGES)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    csrf.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    ckeditor.init_app(app)
    mail.init_app(app)

    # Initialize Babel with the locale selector
    babel = Babel(app, locale_selector=get_locale)

    # Login configuration
    login_manager.login_view = 'main.login'
    login_manager.login_message = _("Please log in to access MkulimaAid.")  # Translatable
    login_manager.login_message_category = 'info'

    # CKEditor file uploader endpoint
    app.config['CKEDITOR_FILE_UPLOADER'] = 'main.upload'

    # Blueprint registration
    from mkulimaaid.routes import main
    app.register_blueprint(main)

    return app
