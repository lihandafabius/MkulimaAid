# models.py
from mkulimaaid import db  # Import db from mkulimaaid where it is initialized
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):  # Use db.Model for SQLAlchemy models
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), nullable=False, default="MkulimaAid")
    site_logo = db.Column(db.String(100), nullable=True)  # Store logo file path
    contact_email = db.Column(db.String(100), nullable=False, default="info@mkulimaaid.com")
    contact_phone = db.Column(db.String(20), nullable=False, default="123-456-7890")
    address = db.Column(db.Text, nullable=True, default="123 Main St, City, Country")
    maintenance_mode = db.Column(db.Boolean, default=False)


    @staticmethod
    def get_settings():
        # Singleton pattern to ensure only one settings record
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
        return settings


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self):
        return f'<Subscriber {self.email}>'