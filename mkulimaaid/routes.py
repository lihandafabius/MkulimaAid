import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from mkulimaaid.forms import UploadForm, LoginForm, RegistrationForm, AdminForm
from config import Config
from PIL import Image
import torch
from flask_login import login_user, login_required, current_user, logout_user
from mkulimaaid.models import User, Subscriber, Settings
from mkulimaaid import db, bcrypt, login_manager

main = Blueprint('main', __name__)


# Define allowed extensions for uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# Use the login_manager instance to define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Home page and file upload handling
@main.route('/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    image_filename = None
    prediction = None

    if form.validate_on_submit():
        if form.image.data and allowed_file(form.image.data.filename):
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)

            # Save uploaded image to the uploads folder
            form.image.data.save(file_path)

            try:
                # Open the uploaded image and convert it to RGB
                image = Image.open(file_path).convert("RGB")

                # Prepare the image for the model
                inputs = Config.disease_processor(images=image, return_tensors="pt")

                # Make prediction using the model
                with torch.no_grad():
                    outputs = Config.disease_model(**inputs)

                # Get the predicted class index
                predicted_label_idx = torch.argmax(outputs.logits, dim=-1).item()

                # Map the predicted class index to its corresponding label
                predicted_class = Config.disease_model.config.id2label[predicted_label_idx]
                prediction = predicted_class

                # Save the image filename for display
                image_filename = filename

            except Exception as e:
                flash(f"Error processing the image: {e}", 'danger')
        else:
            flash("Invalid file type. Please upload a valid image (jpg, jpeg, png, jfif).", 'warning')

    return render_template('home.html', form=form, image_filename=image_filename, prediction=prediction)


# Serve the uploaded files
@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


# Predict route
@main.route('/predict', methods=['POST'])
def predict():
    model = request.form.get('model')
    image_filename = request.form.get('image_filename')

    if model == 'disease' and image_filename:
        file_path = os.path.join(Config.UPLOAD_FOLDER, image_filename)

        try:
            # Open the uploaded image and convert it to RGB
            image = Image.open(file_path).convert("RGB")

            # Prepare the image for the model
            inputs = Config.disease_processor(images=image, return_tensors="pt")

            # Make prediction using the model
            with torch.no_grad():
                outputs = Config.disease_model(**inputs)

            # Get the predicted class index
            predicted_label_idx = torch.argmax(outputs.logits, dim=-1).item()

            # Map the predicted class index to its corresponding label
            predicted_class = Config.disease_model.config.id2label[predicted_label_idx]
            prediction = predicted_class

            return redirect(url_for('main.upload', prediction=prediction, image_filename=image_filename))

        except Exception as e:
            flash(f"Error processing the image: {e}", 'danger')
    else:
        flash('Please select a valid model and upload an image.', 'warning')

    return redirect(url_for('main.upload'))


# Login route
@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.upload'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.upload'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html', form=form)


# Register route
@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.upload'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(fullname=form.fullname.data, username=form.username.data, email=form.email.data,
                    phone=form.phone.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


# Dashboard route
@main.route('/dashboard')
@login_required
def dashboard():
    users = User.query.all()  # Fetch all users
    # messages = ContactMessage.query.all()  # Fetch all contact form messages
    # Only admins can access this route
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.upload'))
    return render_template('dashboard.html')


# Logout route
@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))

@main.route('/farmers')
@login_required
def customers():
    return render_template('farmers.html')

@main.route('/reports')
@login_required
def reports():
    # Logic for displaying reports
    return render_template('reports.html')

@main.route('/integrations')
@login_required
def integrations():
    # Logic for displaying integrations
    return render_template('integrations.html')


@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = AdminForm()

    # Handle the form submission to add an admin
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            if not user.is_admin:
                user.is_admin = True
                db.session.commit()
                flash(f'{user.email} is now an admin!', 'success')
            else:
                flash(f'{user.email} is already an admin.', 'warning')
        else:
            flash('No user found with that email.', 'danger')

    # Retrieve all admins from the database
    admins = User.query.filter_by(is_admin=True).all()

    return render_template('settings.html', form=form, admins=admins)

# Route to remove admin privileges
@main.route('/remove_admin/<int:admin_id>', methods=['POST'])
@login_required
def remove_admin(admin_id):
    user = User.query.get_or_404(admin_id)

    if user.is_admin:
        user.is_admin = False
        db.session.commit()
        flash(f'{user.email} is no longer an admin.', 'success')
    else:
        flash(f'{user.email} is not an admin.', 'warning')

    return redirect(url_for('settings'))


@main.route('/toggle_maintenance', methods=['POST'])
@login_required
def toggle_maintenance():
    maintenance_mode = 'maintenance_mode' in request.form

    # Get the current settings
    settings = Settings.get_settings()

    # Update the maintenance mode in the database
    settings.maintenance_mode = maintenance_mode

    try:
        db.session.commit()
        flash('Maintenance mode updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating maintenance mode: {str(e)}', 'danger')

    return redirect(url_for('settings'))
