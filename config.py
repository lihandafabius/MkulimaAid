import os
from datetime import timedelta


class Config:
    # Security Keys
    SECRET_KEY = os.environ.get("SECRET_KEY", "you-should-set-this-in-env")
    RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY", "set-in-env")
    RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY", "set-in-env")

    #kindwise Api
    KINDWISE_API_KEY = os.getenv('KINDWISE_API_KEY')
    KINDWISE_API_URL = 'https://crop.kindwise.com/api/v1'

    # Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'mkulimaaid', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # Editor config
    CKEDITOR_ENABLE_CSRF = True
    CKEDITOR_HEIGHT = 400
    CKEDITOR_WIDTH = '100%'
    CKEDITOR_FILE_UPLOADER = 'upload'

    # Email config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MKULIMAAID_MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MKULIMAAID_MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MKULIMAAID_MAIL_USERNAME')

    # SendGrid
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

    # reCAPTCHA
    RECAPTCHA_USE_SSL = True
    RECAPTCHA_OPTIONS = {'theme': 'light'}

    # Login session
    REMEMBER_COOKIE_DURATION = timedelta(days=30)



