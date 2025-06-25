import os
from datetime import timedelta
from flask import Flask, request, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_mail import Mail
from flask_babel import Babel, _

# Initialize extensions without the app object first
csrf = CSRFProtect()
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
ckeditor = CKEditor()
mail = Mail()
babel = Babel()


# This function is used by Babel to select a language
@babel.localeselector
def get_locale():
    # Use 'lang' from the user's session if available
    # Otherwise, try to find the best match from the browser's request headers
    return session.get('lang') or request.accept_languages.best_match(
        # The list of supported languages needs to be available
        ['en', 'sw', 'luo', 'luy', 'kik', 'kam', 'ksb', 'ksm', 'mer', 'mas', 'kln', 'teo', 'dav', 'ebu', 'saq', 'guz',
         'rw']
    )


def create_app():
    """
    Application factory function. This is where we configure and create the Flask app.
    """
    app = Flask(__name__)

    # --- START OF DIRECT CONFIGURATION ---
    # We are now loading all configuration from environment variables.
    # The 'config.py' file is no longer needed for deployment.

    # Security Keys
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "a-strong-default-secret-key-for-dev")
    app.config['RECAPTCHA_PUBLIC_KEY'] = os.environ.get("RECAPTCHA_PUBLIC_KEY")
    app.config['RECAPTCHA_PRIVATE_KEY'] = os.environ.get("RECAPTCHA_PRIVATE_KEY")
    app.config['RECAPTCHA_USE_SSL'] = True
    app.config['RECAPTCHA_OPTIONS'] = {'theme': 'light'}

    # Kindwise API
    app.config['KINDWISE_API_KEY'] = os.environ.get('KINDWISE_API_KEY')
    app.config['KINDWISE_API_URL'] = 'https://crop.kindwise.com/api/v1'

    # Database Configuration
    # On Render, the DATABASE_URL environment variable will be set automatically
    # when you link a PostgreSQL database.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Editor Configuration
    app.config['CKEDITOR_ENABLE_CSRF'] = True
    app.config['CKEDITOR_HEIGHT'] = 400
    app.config['CKEDITOR_FILE_UPLOADER'] = 'main.upload'  # Set endpoint for file uploads

    # Email Configuration (using Gmail as an example)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MKULIMAAID_MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MKULIMAAID_MAIL_PASSWORD')  # Use an App Password for Gmail
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MKULIMAAID_MAIL_USERNAME')

    # SendGrid API Key (if you prefer SendGrid over SMTP)
    app.config['SENDGRID_API_KEY'] = os.environ.get('SENDGRID_API_KEY')

    # Login Session Configuration
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

    # Multilingual Support Configuration for Babel
    app.config['LANGUAGES'] = {
        'en': 'English', 'sw': 'Swahili', 'luo': 'Dholuo', 'luy': 'Luhya',
        'kik': 'Kikuyu', 'kam': 'Kamba', 'ksb': 'Shambala', 'ksm': 'Kisii (Ekegusii)',
        'mer': 'Meru', 'mas': 'Maasai', 'kln': 'Kalenjin', 'teo': 'Teso',
        'dav': 'Taita', 'ebu': 'Embu', 'saq': 'Samburu', 'guz': 'Gusii',
        'rw': 'Kinyarwanda',
    }
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'mkulimaaid/translations'

    # --- END OF DIRECT CONFIGURATION ---

    # Initialize extensions with the newly configured app
    csrf.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    ckeditor.init_app(app)
    mail.init_app(app)
    babel.init_app(app)  # Initialize Babel here

    # Login Manager Configuration
    login_manager.login_view = 'main.login'
    login_manager.login_message = _("Please log in to access MkulimaAid.")
    login_manager.login_message_category = 'info'

    # Blueprint Registration
    # It's good practice to import blueprints inside the factory
    # to avoid circular import issues.
    from mkulimaaid.routes import main
    app.register_blueprint(main)

    return app
