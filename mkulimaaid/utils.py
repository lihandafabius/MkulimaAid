# utils.py
import os
from werkzeug.utils import secure_filename
from config import Config  # Import Config directly

def save_avatar(file):
    filename = secure_filename(file.filename)
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)  # Use Config.UPLOAD_FOLDER
    file.save(file_path)
    return filename
