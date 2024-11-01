import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, g, current_app
from werkzeug.utils import secure_filename
from mkulimaaid.forms import UploadForm, LoginForm, RegistrationForm, AdminForm, DiseaseForm, ProfileForm, ChangePasswordForm, CommentForm, VideoForm, TopicForm, DeleteForm, AnswerForm, QuestionForm
from config import Config
from PIL import Image
import torch
from flask_login import login_user, login_required, current_user, logout_user
from mkulimaaid.models import User, Subscriber, Settings, Diseases, Comments, Video, TopicComment, Topic, Question, Answer
from mkulimaaid import db, bcrypt, login_manager
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import bleach
from datetime import datetime
from mkulimaaid.utils import save_avatar
import re


main = Blueprint('main', __name__)


# Define allowed extensions for uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# Use the login_manager instance to define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.before_request
def load_settings():
    # Assuming Settings is a model that stores the title and logo
    g.settings = Settings.query.first()



# Home page and file upload handling
@main.route('/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    image_filename = None
    prediction = None
    trending_diseases = Diseases.query.filter_by(is_trending=True).all()

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

    return render_template('home.html', form=form, image_filename=image_filename, prediction=prediction, diseases=trending_diseases)


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
        flash('You are already logged in!', 'info')
        return redirect(url_for('main.upload'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')  # Flash message for successful login
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
        # Password validation handled by form validator
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(fullname=form.fullname.data, username=form.username.data, email=form.email.data,
                    phone=form.phone.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    # Render registration with error messages
    return render_template('register.html', form=form)


# Dashboard route
@main.route('/dashboard')
@login_required
def dashboard():
    # Check if the user is an admin
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.upload'))

    # Instantiate the form
    form = AdminForm()

    diseases = Diseases.query.all()  # Get all diseases
    users = User.query.all()  # Get all users

    # Pass the form, diseases, and users to the template
    return render_template('dashboard.html', form=form, diseases=diseases, users=users)


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


# Helper function to get or create settings
def get_settings():
    settings = Settings.query.first()
    if not settings:
        # If settings do not exist, create default settings
        settings = Settings(maintenance_mode=False)
        db.session.add(settings)
        db.session.commit()
    return settings


@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = AdminForm()

    # Set the settings into the global `g` object
    g.settings = get_settings()

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

    settings = get_settings()  # Fetch settings for template rendering
    return render_template('settings.html', form=form, admins=admins, settings=settings)


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

    return redirect(url_for('main.settings'))

@main.before_request
def check_maintenance_mode():
    # Get current settings from the database
    settings = get_settings()

    # Store settings globally for access in templates
    g.settings = settings

    # If maintenance mode is enabled and the user is not an admin, show the maintenance page
    if settings.maintenance_mode and (not current_user.is_authenticated or not current_user.is_admin):
        return render_template('maintenance.html'), 503  # 503 Service Unavailable

@main.route('/toggle_maintenance', methods=['POST'])
@login_required
def toggle_maintenance():
    maintenance_mode = 'maintenance_mode' in request.form

    # Get the current settings
    settings = get_settings()

    # Update the maintenance mode in the database
    settings.maintenance_mode = maintenance_mode

    try:
        db.session.commit()
        flash('Maintenance mode updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating maintenance mode: {str(e)}', 'danger')

    return redirect(url_for('main.settings'))
@main.route('/update_contact_info', methods=['POST'])
@login_required
def update_contact_info():
    contact_email = request.form.get('contact_email')
    contact_phone = request.form.get('contact_phone')
    address = request.form.get('address')

    # Get the current settings (singleton pattern)
    settings = Settings.get_settings()

    # Update the contact information if provided
    if contact_email:
        settings.contact_email = contact_email
    if contact_phone:
        settings.contact_phone = contact_phone
    if address:
        settings.address = address

    # Commit changes to the database
    try:
        db.session.commit()
        flash('Contact information updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating contact information: {str(e)}', 'danger')

    return redirect(url_for('main.settings'))


@main.route('/update_branding', methods=['POST'])
@login_required
def update_branding():
    if not current_user.is_admin:
        flash("You do not have the required permissions to perform this action.", 'danger')
        return redirect(url_for('main.settings'))

    site_title = request.form.get('site_title')
    logo = request.files.get('site_logo')

    # Get the current settings (singleton pattern)
    settings = Settings.get_settings()

    # Update the site title if provided
    if site_title:
        settings.site_title = site_title

    # Handle file upload and save logic for the logo
    if logo and allowed_file(logo.filename):
        filename = secure_filename(logo.filename)
        logo_path = os.path.join(Config.UPLOAD_FOLDER, filename)

        # Save the logo to the upload folder
        logo.save(logo_path)

        # Store the relative path or filename in the database
        settings.site_logo = filename

    # Commit changes to the database
    try:
        db.session.commit()
        flash('Branding updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating branding: {str(e)}', 'danger')

    return redirect(url_for('main.settings'))

@main.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        # Check if already subscribed
        if Subscriber.query.filter_by(email=email).first():
            flash('You are already subscribed.', 'info')
        else:
            subscriber = Subscriber(email=email)
            db.session.add(subscriber)
            db.session.commit()
            flash('You have successfully subscribed!', 'success')
    else:
        flash('Please provide a valid email.', 'danger')
    return redirect(url_for('main.upload'))





@main.route('/send_newsletter', methods=['POST'])
@login_required
def send_newsletter():
    content = request.form.get('content')
    subscribers = Subscriber.query.all()

    for subscriber in subscribers:
        message = Mail(
            from_email='your-email@example.com',
            to_emails=subscriber.email,
            subject='New Trending Crop Disease Detected!',
            plain_text_content=content
        )
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
        except Exception as e:
            print(f"Error: {e}")

    flash('Notification sent to subscribers successfully!', 'success')
    return redirect(url_for('main.diseases'))


# Routes related to Disease Management
# Route to add a new crop disease
@main.route("/add_disease", methods=["GET", "POST"])
@login_required
def add_disease():
    form = DiseaseForm()

    if form.validate_on_submit():
        disease_name = form.name.data
        scientific_name = form.scientific_name.data
        symptoms = form.symptoms.data
        causes = form.causes.data
        description = bleach.clean(form.description.data, tags=[], strip=True)  # Sanitize the description
        organic_control = form.organic_control.data
        chemical_control = form.chemical_control.data
        preventive_measures = form.preventive_measures.data

        # Handle image upload
        image_file = 'default.jpg'  # Default image if none uploaded
        if form.image.data:
            image_file = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(Config.UPLOAD_FOLDER, image_file))

        # Add the disease to the database
        new_disease = Diseases(
            name=disease_name,
            scientific_name=scientific_name,
            symptoms=symptoms,
            causes=causes,
            description=description,
            organic_control=organic_control,
            chemical_control=chemical_control,
            preventive_measures=preventive_measures,
            image=image_file
        )

        db.session.add(new_disease)
        db.session.commit()

        flash(f'Disease "{disease_name}" added successfully!', 'success')
        return redirect(url_for('main.diseases'))

    return render_template('add_disease.html', form=form)

# Route to edit an existing crop disease
@main.route("/disease/edit/<int:disease_id>", methods=["GET", "POST"])
@login_required
def edit_disease(disease_id):
    disease = Diseases.query.get_or_404(disease_id)
    form = DiseaseForm()

    if form.validate_on_submit():
        # Update disease details
        disease.name = form.name.data
        disease.scientific_name = form.scientific_name.data
        disease.symptoms = form.symptoms.data
        disease.causes = form.causes.data
        disease.description = bleach.clean(form.description.data, tags=[], strip=True)  # Sanitize description
        disease.organic_control = form.organic_control.data
        disease.chemical_control = form.chemical_control.data
        disease.preventive_measures = form.preventive_measures.data

        # Handle new image upload if there is a new file
        if form.image.data:
            image_file = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(Config.UPLOAD_FOLDER, image_file))
            disease.image = image_file

        db.session.commit()
        flash(f'Disease "{disease.name}" updated successfully!', 'success')
        return redirect(url_for('main.diseases'))

    # Pre-fill the form with existing disease data
    elif request.method == 'GET':
        form.name.data = disease.name
        form.scientific_name.data = disease.scientific_name
        form.symptoms.data = disease.symptoms
        form.causes.data = disease.causes
        form.description.data = disease.description
        form.organic_control.data = disease.organic_control
        form.chemical_control.data = disease.chemical_control
        form.preventive_measures.data = disease.preventive_measures

    return render_template('edit_disease.html', form=form, disease=disease)

# Route to delete a disease
@main.route("/disease/delete/<int:disease_id>", methods=["POST"])
@login_required
def delete_disease(disease_id):
    disease = Diseases.query.get_or_404(disease_id)
    db.session.delete(disease)
    db.session.commit()

    flash(f'Disease "{disease.name}" deleted successfully!', 'success')
    return redirect(url_for('main.diseases'))

@main.route('/diseases')
@login_required
def diseases():
    diseases = Diseases.query.all()
    form = AdminForm()  # or any form that you want to use
    return render_template('diseases.html', diseases=diseases, form=form)

# Route to post disease to homepage
@main.route('/post_disease/<int:disease_id>', methods=['POST'])
def post_disease_to_homepage(disease_id):
    disease = Diseases.query.get_or_404(disease_id)

    # Mark the disease as trending (posted to homepage)
    disease.is_trending = True
    db.session.commit()

    flash(f'{disease.name} has been posted to the homepage.', 'success')
    return redirect(url_for('main.diseases'))

# Route to toggle "is_trending" status
@main.route('/toggle_trending/<int:disease_id>', methods=['POST'])
def toggle_trending(disease_id):
    disease = Diseases.query.get_or_404(disease_id)

    # Toggle the "is_trending" status
    disease.is_trending = not disease.is_trending
    db.session.commit()

    if disease.is_trending:
        flash(f'{disease.name} is now marked as trending.', 'success')
    else:
        flash(f'{disease.name} is no longer marked as trending.', 'info')

    return redirect(url_for('main.diseases'))


@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    comment_form = CommentForm()
    comments = Comments.query.order_by(Comments.timestamp.desc()).all()  # Fetch all comments

    if form.validate_on_submit():
        # Update profile information
        current_user.fullname = form.fullname.data
        current_user.username = form.username.data
        current_user.phone = form.phone.data

        # Handle avatar upload
        if form.avatar.data:
            avatar_filename = secure_filename(form.avatar.data.filename)
            avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], avatar_filename)
            form.avatar.data.save(avatar_path)
            current_user.avatar = avatar_filename

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile'))

    elif request.method == "GET":
        # Populate form fields with current user data
        form.fullname.data = current_user.fullname
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone.data = current_user.phone

    return render_template('profile.html', form=form, comment_form=comment_form, comments=comments)



@main.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Update the user's password
        hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        current_user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('change_password.html', form=form)


@main.route("/add_comment", methods=["POST"])
@login_required
def add_comment():
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        comment = Comments(
            comment=comment_form.comment.data,
            user_id=current_user.id,
            timestamp=datetime.utcnow()
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
    else:
        flash('Failed to add comment. Please try again.', 'danger')

    return redirect(url_for('main.profile'))


@main.route("/remove_avatar", methods=["POST"])
@login_required
def remove_avatar():
    # Check if the user has an avatar to remove
    if current_user.avatar:
        avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.avatar)
        if os.path.exists(avatar_path):
            os.remove(avatar_path)  # Delete the existing avatar file

        current_user.avatar = None  # Set avatar to None to use the default
        db.session.commit()
        flash('Your profile picture has been removed.', 'success')

    return redirect(url_for('main.profile'))



@main.route("/videos")
def videos():
    page = request.args.get('page', 1, type=int)
    # Only fetch videos that are marked as published
    videos = Video.query.filter_by(published=True).order_by(Video.date_posted.desc()).paginate(page=page, per_page=6)

    # Extract YouTube ID from each video URL
    for video in videos.items:
        video.youtube_id = video.url.split("v=")[-1]

    return render_template("videos.html", videos=videos)

# Route to manage videos in the dashboard
@main.route('/dashboard/videos', methods=['GET', 'POST'])
@login_required
def dashboard_videos():
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.upload'))

    videos = Video.query.order_by(Video.date_posted.desc()).all()
    return render_template('dashboard_videos.html', videos=videos)

# Route to add a new video
@main.route('/dashboard/videos/add', methods=['GET', 'POST'])
@login_required
def add_video():
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.upload'))

    form = VideoForm()
    if form.validate_on_submit():
        # Extract YouTube ID from the URL
        youtube_id = re.search(r'v=([^&]+)', form.url.data)
        if youtube_id:
            youtube_id = youtube_id.group(1)
        else:
            flash("Invalid YouTube URL.", 'danger')
            return redirect(url_for('main.add_video'))

        # Determine if the video should be published
        is_published = 'published' in request.form

        # Create new video entry
        new_video = Video(
            title=form.title.data,
            description=form.description.data,
            url=form.url.data,
            date_posted=datetime.utcnow(),
            published=is_published
        )
        db.session.add(new_video)
        db.session.commit()
        flash('Video added successfully!', 'success')
        return redirect(url_for('main.dashboard_videos'))

    return render_template('add_video.html', form=form)

# Route to edit an existing video
@main.route('/dashboard/videos/edit/<int:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.upload'))

    video = Video.query.get_or_404(video_id)
    form = VideoForm(obj=video)
    if form.validate_on_submit():
        youtube_id = re.search(r'v=([^&]+)', form.url.data)
        if youtube_id:
            youtube_id = youtube_id.group(1)
        else:
            flash("Invalid YouTube URL.", 'danger')
            return redirect(url_for('main.edit_video', video_id=video_id))

        # Update video details and published status
        video.title = form.title.data
        video.description = form.description.data
        video.url = form.url.data
        video.published = 'published' in request.form
        db.session.commit()
        flash(f'Video "{video.title}" updated successfully!', 'success')
        return redirect(url_for('main.dashboard_videos'))

    return render_template('edit_video.html', form=form, video=video)

# Route to delete a video
@main.route('/dashboard/videos/delete/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.upload'))

    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    flash(f'Video "{video.title}" deleted successfully!', 'success')
    return redirect(url_for('main.dashboard_videos'))


@main.route('/dashboard/videos/post/<int:video_id>', methods=['POST'])
@login_required
def post_video_to_homepage(video_id):
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.dashboard_videos'))

    video = Video.query.get_or_404(video_id)
    video.published = not video.published  # Toggle published status
    db.session.commit()

    if video.published:
        flash(f'Video "{video.title}" is now published on the homepage.', 'success')
    else:
        flash(f'Video "{video.title}" has been removed from the homepage.', 'warning')

    return redirect(url_for('main.dashboard_videos'))


@main.route('/topics')
@login_required
def topics():
    topics = Topic.query.order_by(Topic.date_posted.desc()).all()
    return render_template('topics.html', topics=topics)

# Route to view details of a single topic
@main.route('/topics/view/<int:topic_id>')
@login_required
def view_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    form = CommentForm()
    return render_template('view_topic.html', topic=topic, form=form)


@main.route('/topics/<int:topic_id>/comment', methods=['POST'])
@login_required
def add_topic_comment(topic_id):
    form = CommentForm()
    if form.validate_on_submit():
        new_comment = TopicComment(
            content=form.comment.data,
            topic_id=topic_id,
            author_id=current_user.id,
            date_posted=datetime.utcnow()
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
    return redirect(url_for('main.view_topic', topic_id=topic_id))


# Dashboard route for topics management
@main.route('/dashboard/topics')
@login_required
def dashboard_topics():
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.dashboard'))
    form = DeleteForm()

    topics = Topic.query.order_by(Topic.date_posted.desc()).all()
    return render_template('dashboard_topics.html', topics=topics, form=form)

# Route to add a new topic
@main.route('/dashboard/topics/add', methods=['GET', 'POST'])
@login_required
def add_topic():
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.dashboard'))

    form = TopicForm()
    if form.validate_on_submit():
        new_topic = Topic(
            title=form.title.data,
            content=form.content.data,
            date_posted=datetime.utcnow(),
            is_trending=form.is_trending.data,
            author_id = current_user.id
        )
        db.session.add(new_topic)
        db.session.commit()
        flash('Topic added successfully!', 'success')
        return redirect(url_for('main.dashboard_topics'))

    return render_template('add_topic.html', form=form)

# Route to edit an existing topic
@main.route('/dashboard/topics/edit/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def edit_topic(topic_id):
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.dashboard'))

    topic = Topic.query.get_or_404(topic_id)
    form = TopicForm(obj=topic)
    if form.validate_on_submit():
        topic.title = form.title.data
        topic.content = form.content.data
        topic.is_trending = form.is_trending.data
        db.session.commit()
        flash('Topic updated successfully!', 'success')
        return redirect(url_for('main.dashboard_topics'))

    return render_template('edit_topic.html', form=form, topic=topic)

# Route to delete a topic
@main.route('/dashboard/topics/delete/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic(topic_id):
    if not current_user.is_admin:
        flash("You do not have access to this page.", 'danger')
        return redirect(url_for('main.dashboard'))

    topic = Topic.query.get_or_404(topic_id)
    db.session.delete(topic)
    db.session.commit()
    flash('Topic deleted successfully!', 'success')
    return redirect(url_for('main.dashboard_topics'))


@main.route('/forum')
def forum():
    questions = Question.query.order_by(Question.timestamp.desc()).all()
    return render_template('forum.html', questions=questions)

@main.route('/forum/question/<int:question_id>', methods=['GET', 'POST'])
def view_question(question_id):
    question = Question.query.get_or_404(question_id)
    answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.timestamp.desc()).all()
    answer_form = AnswerForm()

    if answer_form.validate_on_submit():
        answer = Answer(content=answer_form.content.data, author_id=current_user.id, question_id=question_id)
        db.session.add(answer)
        db.session.commit()
        flash("Your answer has been posted!", "success")
        return redirect(url_for('main.view_question', question_id=question_id))

    return render_template('view_question.html', question=question, answers=answers, answer_form=answer_form)

@main.route('/forum/new_question', methods=['GET', 'POST'])
@login_required
def new_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(title=form.title.data, content=form.content.data, author_id=current_user.id)
        db.session.add(question)
        db.session.commit()
        flash("Your question has been posted!", "success")
        return redirect(url_for('main.forum'))

    return render_template('new_question.html', form=form)


@main.route("/about")
def about():
    return render_template("about.html")
