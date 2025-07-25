from flask import Flask, request, session
from flask_migrate import Migrate
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_mail import Mail

# Initialize extensions
csrf = CSRFProtect()
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
ckeditor = CKEditor()
mail = Mail()

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

    # Login configuration
    login_manager.login_view = 'main.login'
    login_manager.login_message = ("Please log in to access MkulimaAid.")
    login_manager.login_message_category = 'info'

    # CKEditor file uploader endpoint
    app.config['CKEDITOR_FILE_UPLOADER'] = 'main.upload'

    # Blueprint registration
    from mkulimaaid.routes import main
    app.register_blueprint(main)

    # ✅ Automatically create tables and insert default Settings row
    with app.app_context():
        db.create_all()
        from mkulimaaid.models import Settings
        if not Settings.query.first():
            default_settings = Settings()
            db.session.add(default_settings)
            db.session.commit()

    return app
