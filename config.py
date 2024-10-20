import os
from transformers import AutoImageProcessor, AutoModelForImageClassification

class Config:
    SECRET_KEY = "supersecretkey"
    UPLOAD_FOLDER = './static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}

    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # For SQLite (you can replace with PostgreSQL or MySQL URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # To suppress SQLAlchemy warning about event notifications

    # Model paths
    DISEASE_MODEL_PATH = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"

    # Load disease model (Plant Disease Identification)
    disease_processor = AutoImageProcessor.from_pretrained(DISEASE_MODEL_PATH)
    disease_model = AutoModelForImageClassification.from_pretrained(DISEASE_MODEL_PATH)
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

