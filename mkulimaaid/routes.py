import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from PIL import Image
import torch
from config import Config
from .forms import UploadForm
from werkzeug.utils import secure_filename

# Create blueprint
main = Blueprint('main', __name__)

# Route for the home page
@main.route('/')
def home():
    form = UploadForm()
    return render_template('home.html', form=form)

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()

    if form.validate_on_submit():  # Check if the form is valid
        if 'image' not in request.files:
            flash('No image part')
            return redirect(request.url)

        file = request.files['image']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)  # Secure the filename
            if not os.path.exists(Config.UPLOAD_FOLDER):
                os.makedirs(Config.UPLOAD_FOLDER)

            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Pass the filename to render the uploaded image
            return render_template('home.html', form=form, image_filename=filename)

    return render_template('home.html', form=form)

@main.route('/predict', methods=['POST'])
def predict():
    task = request.form.get('model')
    image_filename = request.form.get('image_filename')

    if not image_filename:
        flash('No image uploaded for prediction.')
        return redirect(request.url)

    filepath = os.path.join(Config.UPLOAD_FOLDER, image_filename)
    img = Image.open(filepath).convert("RGB")

    predicted_class = None

    if task == 'pest':
        img_tensor = Config.pest_transform(img).unsqueeze(0)
        with torch.no_grad():
            output = Config.pest_model(img_tensor)
            _, predicted = torch.max(output, 1)
            predicted_class = Config.CLASS_NAMES[predicted.item()]
    elif task == 'disease':
        inputs = Config.disease_processor(images=img, return_tensors="pt")
        with torch.no_grad():
            outputs = Config.disease_model(**inputs)
        logits = outputs.logits
        predicted_label_idx = logits.argmax(-1).item()
        predicted_class = Config.disease_model.config.id2label[predicted_label_idx]

    if not predicted_class:
        flash('Invalid task selected or prediction failed.')
        return redirect(request.url)

    return render_template('home.html',
                           prediction=predicted_class,
                           image_filename=image_filename)
