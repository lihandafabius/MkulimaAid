
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, g, current_app, \
    session, abort, make_response
from werkzeug.utils import secure_filename
from mkulimaaid.forms import (UploadForm, LoginForm, RegistrationForm, AdminForm, DiseaseForm, ProfileForm,
                              ChangePasswordForm, CommentForm, VideoForm, TopicForm, DeleteForm, AnswerForm,
                              QuestionForm, ContactForm, EmptyForm, TeamForm, FarmersForm, NotificationForm,
                              NotificationSettingsForm)
from config import Config
from PIL import Image
import torch
from flask_login import login_user, login_required, current_user, logout_user
from mkulimaaid.models import (User, Subscriber, Settings, Diseases, Comments, Video, TopicComment, Topic, Question,
                               Answer, ContactMessage, TeamMember, IdentifiedDisease, Farmer, Notification,
                               UserNotificationSetting, UserNotification, Report)
from mkulimaaid import db, bcrypt, login_manager
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import bleach
from datetime import datetime, timedelta
from collections import Counter
from mkulimaaid.utils import save_avatar
from mkulimaaid.decorators import admin_required
import re
from flask import jsonify
from sqlalchemy import func
from weasyprint import HTML


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


@main.before_request
def check_session_timeout():
    if current_user.is_authenticated:
        # Retrieve 'last_active' timestamp
        last_active_str = session.get('last_active')

        # Ensure 'last_active' exists and is a valid string before processing
        if isinstance(last_active_str, str):
            try:
                last_active = datetime.fromisoformat(last_active_str)  # Convert from string
            except ValueError:
                # Handle cases where the string is not in the correct ISO format
                last_active = datetime.now()

            # Calculate time elapsed since last activity
            time_elapsed = datetime.now() - last_active

            if time_elapsed > current_app.permanent_session_lifetime:
                logout_user()
                session.clear()
                flash("Your session has expired. Please log in again.", "warning")
                return redirect(url_for('main.login'))

        # Update 'last_active' timestamp as an ISO format string
        session['last_active'] = datetime.now().isoformat()


def update_trending_status():
    # Update trending status for IdentifiedDisease
    distinct_identified_diseases = db.session.query(IdentifiedDisease.disease_name).distinct().all()

    for disease_tuple in distinct_identified_diseases:
        disease_name = disease_tuple[0]

        # Count occurrences of the disease
        disease_count = IdentifiedDisease.query.filter_by(disease_name=disease_name).count()

        # Update is_trending status for all rows of this disease
        is_trending = disease_count > 10
        IdentifiedDisease.query.filter_by(disease_name=disease_name).update({
            IdentifiedDisease.is_trending: is_trending
        })
    #
    # # Update trending status for Diseases
    # diseases = Diseases.query.all()
    # for disease in diseases:
    #     # Check if the disease appears more than 10 times in IdentifiedDisease
    #     count_in_identified = IdentifiedDisease.query.filter_by(disease_name=disease.name).count()
    #     disease.is_trending = count_in_identified > 10

    # Commit changes to the database
    db.session.commit()


# Home page and file upload handling
@main.route('/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    image_filename = None
    prediction = None
    farmers_form = FarmersForm()

    # Fetch trending diseases
    trending_identified_diseases = IdentifiedDisease.query.filter_by(is_trending=True).all()
    trending_diseases = Diseases.query.filter_by(is_trending=True).all()

    if form.validate_on_submit():
        if form.image.data and allowed_file(form.image.data.filename):
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)

            # Save uploaded image to the uploads folder
            form.image.data.save(file_path)

            try:
                # Process the image and make a prediction
                image = Image.open(file_path).convert("RGB")
                inputs = Config.disease_processor(images=image, return_tensors="pt")

                with torch.no_grad():
                    outputs = Config.disease_model(**inputs)

                predicted_label_idx = torch.argmax(outputs.logits, dim=-1).item()
                predicted_class = Config.disease_model.config.id2label[predicted_label_idx]
                prediction = predicted_class

                image_filename = filename

                # Save the identified disease
                identified_disease = IdentifiedDisease(
                    user_id=current_user.id,
                    disease_name=prediction,
                    image_filename=filename,
                    confidence=float(outputs.logits[0][predicted_label_idx].item())
                )
                db.session.add(identified_disease)
                db.session.commit()

                # Update trending diseases
                update_trending_status()

            except Exception as e:
                flash(f"Error processing the image: {e}", 'danger')
        else:
            flash("Invalid file type. Please upload a valid image (jpg, jpeg, png, jfif).", 'warning')

    return render_template(
        'home.html',
        form=form,
        image_filename=image_filename,
        prediction=prediction,
        diseases=trending_diseases,
        trending_identified_diseases=trending_identified_diseases,
        farmers_form=farmers_form
    )


# Serve the uploaded files
@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@main.route('/clear_results', methods=['POST'])
@login_required
def clear_results():
    # Redirect back to the upload page without any data
    return redirect(url_for('main.upload'))


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


@main.route('/disease/<int:disease_id>')
@login_required
def disease_detail(disease_id):
    farmers_form = FarmersForm()
    disease = Diseases.query.get_or_404(disease_id)
    return render_template('disease_detail.html', disease=disease, farmers_form=farmers_form)


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
            session['last_active'] = datetime.now()
            flash('Login successful!', 'success')
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
@admin_required
def dashboard():

    # Instantiate the form
    form = AdminForm()
    farmers_form = FarmersForm()

    # Get all diseases and users
    diseases = Diseases.query.all()
    users = User.query.all()

    # Count unseen messages
    unread_count = ContactMessage.query.filter_by(seen=False).count()

    # Pass form, diseases, users, and unread_count to the template
    return render_template('dashboard.html', form=form, diseases=diseases, users=users, unread_count=unread_count, farmers_form=farmers_form)


# Logout route
@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))


@main.route('/farmers')
@login_required
@admin_required
def farmers():
    form = FarmersForm()
    farmers_form = FarmersForm()
    # Query all users
    farmers = User.query.all()
    return render_template('farmers.html', farmers=farmers, form=form, farmers_form=farmers_form)


# View Farmer details
@main.route('/farmers/view/<int:id>', methods=['GET'])
@login_required
@admin_required
def view_farmer(id):
    farmers_form = FarmersForm()
    farmer = User.query.get_or_404(id)
    farmer_details = Farmer.query.filter_by(user_id=farmer.id).first()

    # Calculate totals
    total_questions = len(farmer.questions)
    total_answers = len(farmer.answers)
    total_comments = len(farmer.comments)
    total_messages = len(farmer.contact_messages)

    # Data for questions and answers over time
    questions_dates = [q.timestamp.strftime('%Y-%m-%d') for q in farmer.questions]
    answers_dates = [a.timestamp.strftime('%Y-%m-%d') for a in farmer.answers]

    question_counts = Counter(questions_dates)
    answer_counts = Counter(answers_dates)

    if question_counts:
        questions_labels, questions_values = zip(*question_counts.items())
    else:
        questions_labels, questions_values = [], []

    if answer_counts:
        answers_labels, answers_values = zip(*answer_counts.items())
    else:
        answers_labels, answers_values = [], []

    # Data for messages over time
    messages_dates = [m.date_sent.strftime('%Y-%m-%d') for m in farmer.contact_messages]
    messages_counts = Counter(messages_dates)

    if messages_counts:
        messages_labels, messages_values = zip(*messages_counts.items())
    else:
        messages_labels, messages_values = [], []

    # Data for topics interacted with
    topic_names = [t.title for t in farmer.topics]
    topic_interactions = Counter(topic_names)

    if topic_interactions:
        topics_labels, topics_values = zip(*topic_interactions.items())
    else:
        topics_labels, topics_values = [], []

    # Prepare data for rendering
    return render_template(
        'view_farmer.html',
        farmer=farmer,
        total_questions=total_questions,
        total_answers=total_answers,
        total_comments=total_comments,
        total_messages=total_messages,
        questions_labels=questions_labels,
        questions_values=questions_values,
        answers_labels=answers_labels,
        answers_values=answers_values,
        messages_labels=messages_labels,
        messages_values=messages_values,
        topics_labels=topics_labels,
        topics_values=topics_values,
        farmers_form=farmers_form,
        farmer_details=farmer_details
    )


# Delete Farmer
@main.route('/farmers/delete/<int:farmer_id>', methods=['POST'])
@login_required
@admin_required
def delete_farmer(farmer_id):

    farmer = User.query.get_or_404(farmer_id)

    # Only allow admins to delete farmers
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'warning')
        return redirect(url_for('main.farmers'))

    db.session.delete(farmer)
    db.session.commit()
    flash('Farmer deleted successfully.', 'success')
    return redirect(url_for('main.farmers'))


@main.route('/reports', methods=['GET'])
@login_required
@admin_required
def list_reports():
    """List all generated reports with pagination."""
    farmers_form = FarmersForm()

    # Get the current page number from query parameters, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Define the number of reports per page

    # Fetch paginated reports sorted by date
    pagination = Report.query.order_by(Report.generated_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    reports = pagination.items  # Get reports for the current page

    return render_template(
        'reports.html',
        reports=reports,
        pagination=pagination,
        farmers_form=farmers_form
    )


def calculate_avg_answers_per_question():
    total_answers = db.session.query(func.count(Answer.id)).scalar()  # Replace `Answer` with your actual Answer model
    total_questions = db.session.query(func.count(Question.id)).scalar()  # Replace `Question` with your actual Question model

    # Avoid division by zero
    if total_questions == 0:
        return 0

    return total_answers / total_questions


def get_report_insights():
    """Fetch insights for the report."""
    # Fetch data for the report
    top_diseases = db.session.query(
        IdentifiedDisease.disease_name,
        db.func.count(IdentifiedDisease.id).label('count')
    ).group_by(IdentifiedDisease.disease_name).order_by(db.desc('count')).limit(5).all()

    # Average detection confidence for diseases
    avg_confidence = db.session.query(
        IdentifiedDisease.disease_name,
        db.func.avg(IdentifiedDisease.confidence).label('avg_confidence')
    ).group_by(IdentifiedDisease.disease_name).order_by(db.desc('avg_confidence')).limit(5).all()

    # Forum insights
    active_questions = Question.query.count()
    active_answers = Answer.query.count()

    popular_crops = db.session.query(
        Farmer.crop_types, db.func.count(Farmer.id).label('count')
    ).group_by(Farmer.crop_types).order_by(db.desc('count')).limit(5).all()

    regional_disease_distribution = db.session.query(
        Farmer.location, db.func.count(IdentifiedDisease.id).label('count')
    ).join(IdentifiedDisease, Farmer.user_id == IdentifiedDisease.user_id).group_by(Farmer.location).all()

    top_questions = db.session.query(
        Question.title, db.func.count(Answer.id).label('answers_count')
    ).join(Answer, Question.id == Answer.question_id).group_by(Question.id).order_by(db.desc('answers_count')).limit(5).all()

    most_active_users = db.session.query(
        User.username, db.func.count(Question.id + Answer.id).label('activity_count')
    ).outerjoin(Question, Question.author_id == User.id).outerjoin(Answer, Answer.author_id == User.id).group_by(
        User.username).order_by(db.desc('activity_count')).limit(5).all()

    avg_answers_per_question = db.session.query(
        db.func.avg(db.func.count(Answer.id)).over()
    ).scalar() or 0

    return {
        "top_diseases": top_diseases,
        "active_questions":active_questions,
        "active_answers": active_answers,
        "avg_confidence": avg_confidence,
        "popular_crops": popular_crops,
        "regional_disease_distribution": regional_disease_distribution,
        "top_questions": top_questions,
        "most_active_users": most_active_users,
        "avg_answers_per_question": avg_answers_per_question
    }


@main.route('/reports/<int:report_id>/view', methods=['GET'])
@login_required
@admin_required
def view_report(report_id):
    """View a detailed report with insights."""
    report = Report.query.get_or_404(report_id)
    farmers_form = FarmersForm()

    # Fetch insights using the helper function
    insights = get_report_insights()

    return render_template(
        'report_view.html',
        report=report,
        farmers_form=farmers_form,
        **insights,  # Pass the insights as keyword arguments
        title=report.title,  # Use the report's title
        description=report.description  # Use the report's description
    )


@main.route('/reports/<int:report_id>/download', methods=['GET'])
@login_required
def download_report(report_id):
    """Download a report as a PDF."""
    report = Report.query.get_or_404(report_id)
    farmers_form = FarmersForm()

    # Fetch insights using the helper function
    insights = get_report_insights()

    # Render the report HTML
    report_html = render_template(
        'report_template.html',
        report=report,
        farmers_form=farmers_form,
        download=True,
        datetime=datetime,  # Pass the datetime module
        **insights,  # Pass the insights as keyword arguments
        title=report.title,  # Use the report's title
        description=report.description  # Use the report's description
    )

    # Generate the PDF
    pdf = HTML(string=report_html).write_pdf()

    # Prepare the response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={report.filename}.pdf'

    return response


@main.route('/reports/<int:report_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_report(report_id):
    """Delete a report."""
    report = Report.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash('Report deleted successfully.', 'success')
    return redirect(url_for('main.list_reports'))


@main.route('/reports/<int:report_id>/post', methods=['POST'])
@login_required
@admin_required
def post_to_homepage(report_id):
    """Feature or unfeature a report on the homepage."""
    report = Report.query.get_or_404(report_id)

    # Toggle the `is_featured` flag for the selected report
    report.is_featured = not report.is_featured
    db.session.commit()

    status = "featured" if report.is_featured else "removed from the homepage"
    flash(f'Report "{report.title}" has been {status}!', 'success')
    return redirect(url_for('main.list_reports'))


@main.route('/generate_report', methods=['POST'])
@login_required
@admin_required
def generate_report():
    """Generate a new report dynamically based on admin input."""
    # Get custom title and description from the form
    title = request.form.get('title', f"Report {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    description = request.form.get('description', "An auto-generated report summarizing key platform insights.")

    # Fetch data for the report
    top_diseases = db.session.query(
        IdentifiedDisease.disease_name,
        db.func.count(IdentifiedDisease.id).label('count')
    ).group_by(IdentifiedDisease.disease_name).order_by(db.desc('count')).limit(5).all()

    # User-focused insights
    popular_crops = db.session.query(
        Farmer.crop_types, db.func.count(Farmer.id).label('count')
    ).group_by(Farmer.crop_types).order_by(db.desc('count')).limit(5).all()

    regional_disease_distribution = db.session.query(
        Farmer.location, db.func.count(IdentifiedDisease.id).label('count')
    ).join(IdentifiedDisease, Farmer.user_id == IdentifiedDisease.user_id).group_by(Farmer.location).all()

    top_questions = db.session.query(
        Question.title, db.func.count(Answer.id).label('answers_count')
    ).join(Answer, Question.id == Answer.question_id).group_by(Question.id).order_by(db.desc('answers_count')).limit(5).all()

    most_active_users = db.session.query(
        User.username, db.func.count(Question.id + Answer.id).label('activity_count')
    ).outerjoin(Question, Question.author_id == User.id).outerjoin(Answer, Answer.author_id  == User.id).group_by(
        User.username).order_by(db.desc('activity_count')).limit(5).all()

    avg_answers_per_question = db.session.query(
        db.func.avg(db.func.count(Answer.id)).over()
    ).scalar()


    farmers_form = FarmersForm()

    # Render the HTML content for the report
    report_html = render_template(
        'report_template.html',
        title=title,
        description=description,
        top_diseases=top_diseases,
        popular_crops=popular_crops,
        regional_disease_distribution=regional_disease_distribution,
        top_questions=top_questions,
        most_active_users=most_active_users,
        avg_answers_per_question=avg_answers_per_question,
        datetime=datetime,
        farmers_form=farmers_form
    )

    # Generate PDF
    pdf = HTML(string=report_html).write_pdf()

    # Save the PDF file
    filename = f'report_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.pdf'
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    with open(file_path, 'wb') as f:
        f.write(pdf)

    # Save report metadata
    new_report = Report(
        title=title,
        description=description,
        generated_by=current_user.id,
        filename=filename
    )
    db.session.add(new_report)
    db.session.commit()

    flash('Report generated successfully!', 'success')
    return redirect(url_for('main.list_reports'))


@main.route('/homepage/reports', methods=['GET'])
def homepage_reports():
    """List all reports marked as featured on the homepage with pagination."""
    # Get the current page from the query parameters
    page = request.args.get('page', 1, type=int)

    # Paginate the featured reports
    pagination = Report.query.filter_by(is_featured=True) \
        .order_by(Report.generated_at.desc()) \
        .paginate(page=page, per_page=6)  # Adjust `per_page` as needed

    featured_reports = pagination.items  # Get the reports for the current page
    farmers_form = FarmersForm()

    return render_template(
        'homepage_reports.html',
        featured_reports=featured_reports,
        pagination=pagination,  # Pass the pagination object to the template
        farmers_form=farmers_form
    )

@main.route('/user_reports/<int:report_id>/view', methods=['GET'])
@login_required
def view_homepage_report(report_id):
    """View a detailed report with insights."""
    report = Report.query.get_or_404(report_id)
    farmers_form = FarmersForm()

    # Fetch insights using the helper function
    insights = get_report_insights()

    return render_template(
        'homepage_report_view.html',
        report=report,
        farmers_form=farmers_form,
        **insights,  # Pass the insights as keyword arguments
        title=report.title,  # Use the report's title
        description=report.description  # Use the report's description
    )


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
@admin_required
def settings():
    form = AdminForm()
    farmers_form = FarmersForm()

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
    return render_template('settings.html', form=form, admins=admins, settings=settings, farmers_form=farmers_form)


# Route to remove admin privileges
@main.route('/remove_admin/<int:admin_id>', methods=['POST'])
@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
    return redirect(url_for('main.dashboard_notifications'))


# Routes related to Disease Management
# Route to add a new crop disease
@main.route("/add_disease", methods=["GET", "POST"])
@login_required
@admin_required
def add_disease():
    form = DiseaseForm()
    farmers_form = FarmersForm()

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

    return render_template('add_disease.html', form=form, farmers_form=farmers_form)


# Route to edit an existing crop disease
@main.route("/disease/edit/<int:disease_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_disease(disease_id):
    disease = Diseases.query.get_or_404(disease_id)
    form = DiseaseForm()
    farmers_form = FarmersForm()

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

    return render_template('edit_disease.html', form=form, disease=disease, farmers_form=farmers_form)


# Route to delete a disease
@main.route("/disease/delete/<int:disease_id>", methods=["POST"])
@login_required
@admin_required
def delete_disease(disease_id):
    disease = Diseases.query.get_or_404(disease_id)
    db.session.delete(disease)
    db.session.commit()

    flash(f'Disease "{disease.name}" deleted successfully!', 'success')
    return redirect(url_for('main.diseases'))


@main.route('/diseases')
@login_required
@admin_required
def diseases():
    page = request.args.get('page', 1, type=int)  # Get the current page number from the request
    per_page = 4  # Number of diseases per page
    pagination = Diseases.query.paginate(page=page, per_page=per_page, error_out=False)
    diseases = pagination.items  # Get the current page's items
    form = AdminForm()  # or any form that you want to use
    farmers_form = FarmersForm()
    return render_template(
        'diseases.html',
        diseases=diseases,
        pagination=pagination,
        form=form,
        farmers_form=farmers_form
    )


# Route to post disease to homepage
@main.route('/post_disease/<int:disease_id>', methods=['POST'])
@login_required
@admin_required
def post_disease_to_homepage(disease_id):
    disease = Diseases.query.get_or_404(disease_id)

    # Mark the disease as trending (posted to homepage)
    disease.is_trending = True
    db.session.commit()

    flash(f'{disease.name} has been posted to the homepage.', 'success')
    return redirect(url_for('main.diseases'))


# Route to toggle "is_trending" status
@main.route('/toggle_trending/<int:disease_id>', methods=['POST'])
@login_required
@admin_required
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
    farmers_form = FarmersForm()

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

    return render_template('profile.html', form=form, comment_form=comment_form, comments=comments, farmers_form=farmers_form)


@main.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    farmers_form = FarmersForm()

    if form.validate_on_submit():
        # Update the user's password
        hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        current_user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('change_password.html', form=form, farmers_form=farmers_form)


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
@login_required
def videos():
    farmers_form = FarmersForm()
    page = request.args.get('page', 1, type=int)
    # Only fetch videos that are marked as published
    videos = Video.query.filter_by(published=True).order_by(Video.date_posted.desc()).paginate(page=page, per_page=6)

    # Extract YouTube ID for each video and build the embed URL
    for video in videos.items:
        match = re.search(r'(?:v=|/|embed/|youtu\.be/)([a-zA-Z0-9_-]{11})', video.url)
        video.youtube_id = match.group(1) if match else None
        video.embed_url = f"https://www.youtube.com/embed/{video.youtube_id}" if video.youtube_id else None

    return render_template("videos.html", videos=videos, farmers_form=farmers_form)


# Route to manage videos in the dashboard
@main.route('/dashboard/videos', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard_videos():
    farmers_form = FarmersForm()
    videos = Video.query.order_by(Video.date_posted.desc()).all()
    return render_template('dashboard_videos.html', videos=videos, farmers_form=farmers_form)


# Route to add a new video
@main.route('/dashboard/videos/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_video():
    farmers_form = FarmersForm()
    form = VideoForm()
    if form.validate_on_submit():
        match = re.search(r'(?:v=|/|embed/|youtu\.be/)([a-zA-Z0-9_-]{11})', form.url.data)
        youtube_id = match.group(0) if match else None
        if not youtube_id:
            flash("Invalid YouTube URL.", 'danger')
            return redirect(url_for('main.add_video'))

        is_published = 'published' in request.form

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

    return render_template('add_video.html', form=form, farmers_form=farmers_form)


# Route to edit an existing video
@main.route('/dashboard/videos/edit/<int:video_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_video(video_id):
    farmers_form = FarmersForm()
    video = Video.query.get_or_404(video_id)
    form = VideoForm(obj=video)
    if form.validate_on_submit():
        match = re.search(r'(?:v=|/|embed/|youtu\.be/)([a-zA-Z0-9_-]{11})', form.url.data)
        youtube_id = match.group(0) if match else None
        if not youtube_id:
            flash("Invalid YouTube URL.", 'danger')
            return redirect(url_for('main.edit_video', video_id=video_id))

        video.title = form.title.data
        video.description = form.description.data
        video.url = form.url.data
        video.published = 'published' in request.form
        db.session.commit()
        flash(f'Video "{video.title}" updated successfully!', 'success')
        return redirect(url_for('main.dashboard_videos'))

    return render_template('edit_video.html', form=form, video=video, farmers_form=farmers_form)


# Route to delete a video
@main.route('/dashboard/videos/delete/<int:video_id>', methods=['POST'])
@login_required
@admin_required
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    flash(f'Video "{video.title}" deleted successfully!', 'success')
    return redirect(url_for('main.dashboard_videos'))


@main.route('/dashboard/videos/post/<int:video_id>', methods=['POST'])
@login_required
@admin_required
def post_video_to_homepage(video_id):
    video = Video.query.get_or_404(video_id)
    video.published = not video.published
    db.session.commit()

    if video.published:
        flash(f'Video "{video.title}" is now published on the homepage.', 'success')
    else:
        flash(f'Video "{video.title}" has been removed from the homepage.', 'warning')

    return redirect(url_for('main.dashboard_videos'))


@main.route('/topics')
@login_required
def topics():
    farmers_form = FarmersForm()
    page = request.args.get('page', 1, type=int)
    topics = Topic.query.order_by(Topic.date_posted.desc()).paginate(page=page, per_page=6)
    return render_template('topics.html', topics=topics, farmers_form=farmers_form)


# Route to view details of a single topic
@main.route('/topics/view/<int:topic_id>')
@login_required
def view_topic(topic_id):
    farmers_form = FarmersForm()
    topic = Topic.query.get_or_404(topic_id)
    form = CommentForm()
    return render_template('view_topic.html', topic=topic, form=form, farmers_form=farmers_form)


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
@admin_required
def dashboard_topics():
    farmers_form = FarmersForm()
    form = DeleteForm()

    topics = Topic.query.order_by(Topic.date_posted.desc()).all()
    return render_template('dashboard_topics.html', topics=topics, form=form, farmers_form=farmers_form)


# Route to add a new topic
@main.route('/dashboard/topics/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_topic():
    form = TopicForm()
    farmers_form = FarmersForm()

    if form.validate_on_submit():
        image_filename = None
        if form.image.data and hasattr(form.image.data, 'filename'):
            image_file = form.image.data
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)

        new_topic = Topic(
            title=form.title.data,
            content=form.content.data,
            date_posted=datetime.utcnow(),
            is_trending=form.is_trending.data,
            image=image_filename,
            author_id=current_user.id
        )
        db.session.add(new_topic)
        db.session.commit()
        flash('Topic added successfully!', 'success')
        return redirect(url_for('main.dashboard_topics'))

    return render_template('add_topic.html', form=form, farmers_form=farmers_form)


@main.route('/dashboard/topics/edit/<int:topic_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    farmers_form = FarmersForm()
    form = TopicForm(obj=topic)
    if form.validate_on_submit():
        if form.image.data and hasattr(form.image.data, 'filename'):
            image_file = form.image.data
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)
            topic.image = image_filename

        topic.title = form.title.data
        topic.content = form.content.data
        topic.is_trending = form.is_trending.data
        db.session.commit()
        flash('Topic updated successfully!', 'success')
        return redirect(url_for('main.dashboard_topics'))

    return render_template('edit_topic.html', form=form, topic=topic, farmers_form=farmers_form)


@main.route('/dashboard/topics/delete/<int:topic_id>', methods=['POST'])
@login_required
@admin_required
def delete_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    db.session.delete(topic)
    db.session.commit()
    flash('Topic deleted successfully!', 'success')
    return redirect(url_for('main.dashboard_topics'))


@main.route('/forum')
@login_required
def forum():
    farmers_form = FarmersForm()
    # Get the current page number from query parameters, default is 1
    page = request.args.get('page', 1, type=int)

    # Paginate the Question query; 5 questions per page
    questions = Question.query.order_by(Question.timestamp.desc()).paginate(page=page, per_page=5)

    # Render the template with paginated questions
    return render_template('forum.html', questions=questions, farmers_form=farmers_form)


@main.route('/forum/question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def view_question(question_id):
    question = Question.query.get_or_404(question_id)
    answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.timestamp.desc()).all()
    answer_form = AnswerForm()
    farmers_form = FarmersForm()

    if answer_form.validate_on_submit():
        answer = Answer(content=answer_form.content.data, author_id=current_user.id, question_id=question_id)
        db.session.add(answer)
        db.session.commit()
        flash("Your answer has been posted!", "success")
        return redirect(url_for('main.view_question', question_id=question_id))

    return render_template('view_question.html', question=question, answers=answers,
                           answer_form=answer_form, farmers_form=farmers_form)


@main.route('/forum/new_question', methods=['GET', 'POST'])
@login_required
def new_question():
    form = QuestionForm()
    farmers_form = FarmersForm()
    if form.validate_on_submit():
        question = Question(title=form.title.data, content=form.content.data, author_id=current_user.id)
        db.session.add(question)
        db.session.commit()
        flash("Your question has been posted!", "success")
        return redirect(url_for('main.forum'))

    return render_template('new_question.html', form=form, farmers_form=farmers_form)


@main.route("/about")
def about():
    farmers_form = FarmersForm()
    return render_template("about.html", farmers_form=farmers_form)


@main.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    farmers_form = FarmersForm()
    if form.validate_on_submit():
        message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data,
            user_id=current_user.id if current_user.is_authenticated else None  # Associate user if logged in
        )
        db.session.add(message)
        db.session.commit()
        flash('Your message has been sent successfully. We will get back to you soon!', 'success')
        return redirect(url_for('main.contact'))
    return render_template("contact.html", form=form, farmers_form=farmers_form)


@main.route('/dashboard/messages', methods=['GET'])
@login_required
@admin_required
def view_messages():
    # Pagination (10 messages per page)
    page = request.args.get('page', 1, type=int)
    messages = ContactMessage.query.order_by(ContactMessage.date_sent.desc()).paginate(page=page, per_page=10)

    # Retrieve all messages, ordered by date
    form = DeleteForm()
    farmers_form = FarmersForm()
    notification_form = NotificationForm()

    # Mark all messages as seen
    for message in messages:
        if not message.seen:
            message.seen = True
    db.session.commit()  # Save changes to the database

    # Since all messages are now seen, the unread count should be zero
    unread_count = 0

    return render_template('messages.html', messages=messages, form=form, unread_count=unread_count, farmers_form=farmers_form, notification_form=notification_form)


@main.route('/dashboard/messages/delete/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def delete_message(message_id):
    # Find the message by ID
    message = ContactMessage.query.get_or_404(message_id)

    # Delete the message from the database
    db.session.delete(message)
    db.session.commit()

    flash('Message deleted successfully!', 'success')
    return redirect(url_for('main.view_messages'))


# Route to render the privacy policy page
@main.route('/privacy-policy')
@login_required
def privacy_policy():
    farmers_form = FarmersForm()
    return render_template('privacy_policy.html', farmers_form=farmers_form)


@main.route("/donate")
@login_required
def donate():
    farmers_form = FarmersForm()
    return render_template("donate.html", farmers_form=farmers_form)


@main.route("/faqs")
@login_required
def faqs():
    farmers_form = FarmersForm()
    return render_template("faqs.html", farmers_form=farmers_form)


# Display all published team members on the main team page
@main.route("/team")
def team():
    farmers_form = FarmersForm()
    page = request.args.get('page', 1, type=int)
    members = TeamMember.query.filter_by(published=True).order_by(TeamMember.date_joined.desc()).paginate(page=page, per_page=6)
    return render_template("team.html", members=members, farmers_form=farmers_form)



@main.route('/dashboard/team', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard_team():
    farmers_form = FarmersForm()
    form = EmptyForm()
    members = TeamMember.query.order_by(TeamMember.date_joined.desc()).all()
    return render_template('dashboard_team.html', members=members, form=form, farmers_form=farmers_form)


# Route to add a new team member
@main.route('/dashboard/team/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_member():
    farmers_form = FarmersForm()
    form = TeamForm()

    if form.validate_on_submit():
        photo = form.photo.data
        filename = None
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)

        new_member = TeamMember(
            name=form.name.data,
            role=form.role.data,
            bio=form.bio.data,
            photo=filename,
            contact_info=form.contact_info.data,
            date_joined=datetime.now(),
            published=form.publish.data
        )

        try:
            db.session.add(new_member)
            db.session.commit()
            flash('Team member added successfully!', 'success')
            return redirect(url_for('main.dashboard_team'))
        except Exception as e:
            db.session.rollback()
            print("Database error:", e)  # Debug database errors
            flash('An error occurred while adding the team member. Please try again.', 'danger')

    # Debugging the form validation and data
    if form.errors:
        print("Form errors:", form.errors)

    return render_template('add_member.html', form=form, farmers_form=farmers_form)


# Route to edit an existing team member
@main.route('/dashboard/team/edit/<int:member_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_member(member_id):
    farmers_form = FarmersForm()
    member = TeamMember.query.get_or_404(member_id)
    form = TeamForm(obj=member)


    if form.validate_on_submit():
        member.name = form.name.data
        member.role = form.role.data
        member.bio = form.bio.data
        member.published = 'published' in request.form

        # Handle file upload if a new photo is provided
        photo = form.photo.data
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            member.photo = filename  # Update only the filename in the database

        db.session.commit()
        flash(f'Team member "{member.name}" updated successfully!', 'success')
        return redirect(url_for('main.dashboard_team'))

    return render_template('edit_member.html', form=form, member=member, farmers_form=farmers_form)


# Route to delete a team member
@main.route('/dashboard/team/delete/<int:member_id>', methods=['POST'])
@login_required
@admin_required
def delete_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash(f'Team member "{member.name}" deleted successfully!', 'success')
    return redirect(url_for('main.dashboard_team'))


# Route to publish/unpublish a team member
@main.route('/dashboard/team/publish/<int:member_id>', methods=['POST'])
@login_required
@admin_required
def publish_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    member.published = not member.published  # Toggle published status
    db.session.commit()

    if member.published:
        flash(f'Team member "{member.name}" is now published on the team page.', 'success')
    else:
        flash(f'Team member "{member.name}" has been unpublished.', 'warning')

    return redirect(url_for('main.dashboard_team'))


@main.route('/api/top-crop-diseases', methods=['GET'])
@login_required
@admin_required
def get_top_crop_diseases():
    time_filter = request.args.get('filter', 'week')
    query = db.session.query(
        IdentifiedDisease.disease_name,
        db.func.count(IdentifiedDisease.id).label('count')
    ).group_by(IdentifiedDisease.disease_name)

    if time_filter == 'week':
        start_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(IdentifiedDisease.date_identified >= start_date)
    elif time_filter == 'month':
        start_date = datetime.utcnow() - timedelta(days=30)
        query = query.filter(IdentifiedDisease.date_identified >= start_date)

    data = [{'name': disease.disease_name, 'count': disease.count} for disease in query.order_by(db.desc('count')).limit(10)]
    return jsonify(data)


@main.route('/api/users-joined', methods=['GET'])
@login_required
@admin_required
def get_users_joined():
    time_filter = request.args.get('filter', 'week')
    query = db.session.query(
        db.func.date(User.date_joined).label('date'),
        db.func.count(User.id).label('count')
    ).group_by(db.func.date(User.date_joined))

    if time_filter == 'week':
        start_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(User.date_joined >= start_date)
    elif time_filter == 'month':
        start_date = datetime.utcnow() - timedelta(days=90)
        query = query.filter(User.date_joined >= start_date)

    data = [{'date': str(result.date), 'count': result.count} for result in query.order_by('date')]
    return jsonify(data)


@main.route('/api/crop-diseases-by-location', methods=['GET'])
@login_required
@admin_required
def get_crop_diseases_by_location():
    time_filter = request.args.get('filter', 'week')
    query = db.session.query(
        Farmer.location,
        IdentifiedDisease.disease_name,
        db.func.count(IdentifiedDisease.id).label('count')
    ).join(Farmer, Farmer.user_id == IdentifiedDisease.user_id) \
      .group_by(Farmer.location, IdentifiedDisease.disease_name)

    if time_filter == 'week':
        start_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(IdentifiedDisease.date_identified >= start_date)
    elif time_filter == 'month':
        start_date = datetime.utcnow() - timedelta(days=90)
        query = query.filter(IdentifiedDisease.date_identified >= start_date)

    data = {}
    for row in query:
        location = row.location
        if location not in data:
            data[location] = []
        data[location].append({'name': row.disease_name, 'count': row.count})

    response = [{'location': loc, 'diseases': diseases} for loc, diseases in data.items()]
    return jsonify(response)


@main.route('/api/disease-confidence', methods=['GET'])
@login_required
@admin_required
def get_disease_confidence():
    # Query the IdentifiedDisease table to get disease names and their average confidence
    disease_confidences = (
        db.session.query(
            IdentifiedDisease.disease_name,
            func.avg(IdentifiedDisease.confidence).label('avg_confidence')
        )
        .group_by(IdentifiedDisease.disease_name)
        .all()
    )

    # Prepare the data for the API response
    data = [
        {"disease_name": disease_name, "avg_confidence": avg_confidence}
        for disease_name, avg_confidence in disease_confidences
    ]

    return jsonify(data)


@main.route('/submit_farm_info', methods=['GET', 'POST'])
@login_required
def submit_farm_info():
    # Fetch the current user's farmer profile, if it exists
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    form = FarmersForm(obj=farmer)  # Populate the form with existing data if available

    if form.validate_on_submit():
        if farmer:
            # Update existing record
            farmer.location = form.location.data
            farmer.farm_size = form.farm_size.data
            farmer.crop_types = form.crop_types.data
            farmer.description = form.description.data
            farmer.contact_info = form.contact_info.data
        else:
            # Create a new Farmer record
            farmer = Farmer(
                location=form.location.data,
                farm_size=form.farm_size.data,
                crop_types=form.crop_types.data,
                description=form.description.data,
                contact_info=form.contact_info.data,
                user_id=current_user.id,
                has_additional_info=True
            )
            db.session.add(farmer)

        db.session.commit()
        flash('Your farm information has been successfully saved!', 'success')
        return redirect(url_for('main.upload'))  # Redirect to homepage or desired location

    return redirect(url_for('main.upload'))  # Redirect immediately if the form is not submitted


# Route for displaying notifications
@main.route('/notifications', methods=['GET'])
@login_required
def view_notifications():
    filter_type = request.args.get('filter', 'all').strip().lower()
    search_query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)  # Get current page number, default to 1
    per_page = 10  # Number of notifications per page

    # Validate filter type
    valid_filters = ['all', 'active', 'archived']
    if filter_type not in valid_filters:
        abort(400, description="Invalid filter type.")

    # Sanitize and validate search query
    search_query = re.sub(r'[^\w\s]', '', search_query)  # Remove special characters
    search_query = search_query.lower()

    # Base query
    query = (
        db.session.query(Notification, UserNotification)
        .join(UserNotification, UserNotification.notification_id == Notification.id)
        .filter(UserNotification.user_id == current_user.id)
    )

    # Apply filter
    if filter_type == 'active':
        query = query.filter(UserNotification.is_archived == False)
    elif filter_type == 'archived':
        query = query.filter(UserNotification.is_archived == True)

    # Apply search
    if search_query:
        query = query.filter(
            db.or_(
                Notification.title.ilike(f'%{search_query}%'),
                Notification.message.ilike(f'%{search_query}%')
            )
        )

    # Apply pagination
    pagination = query.order_by(Notification.date_sent.desc()).paginate(page=page, per_page=per_page)
    notifications = pagination.items

    # Mark notifications as read
    for _, user_notification in notifications:
        if not user_notification.is_read:
            user_notification.is_read = True
    db.session.commit()

    farmers_form = FarmersForm()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for dynamic search or AJAX calls
        notifications_list = [
            {
                "title": n.title,
                "message": n.message,
                "date_sent": n.date_sent.strftime('%b %d, %Y'),
                "is_archived": un.is_archived,
            }
            for n, un in notifications
        ]
        return jsonify(notifications_list)

    # Render template
    return render_template(
        'notifications.html',
        notifications=notifications,
        filter_type=filter_type,
        search_query=search_query,
        farmers_form=farmers_form,
        pagination=pagination  # Pass the pagination object to the template
    )


@main.route('/notifications/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_notification():
    form = NotificationForm()
    if form.validate_on_submit():
        notification = Notification(
            title=form.title.data,
            message=form.message.data,
            admin_id=current_user.id,
        )
        db.session.add(notification)
        db.session.flush()  # Get the notification ID before committing

        # Query all users and check their notification settings
        all_users = User.query.all()
        for user in all_users:
            # Fetch the user's notification settings
            settings = user.notification_settings

            # Default to push_notifications=True if no settings exist
            if settings is None or settings.push_notifications:
                user_notification = UserNotification(
                    user_id=user.id,
                    notification_id=notification.id
                )
                db.session.add(user_notification)

        db.session.commit()
        flash('Notification created successfully!', 'success')
        return redirect(url_for('main.dashboard_notifications'))

    return render_template('create_notification.html', form=form)


# Route for managing user notification settings
@main.route('/notifications/settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    settings = UserNotificationSetting.query.filter_by(user_id=current_user.id).first()
    farmers_form = FarmersForm()
    if not settings:
        settings = UserNotificationSetting(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    form = NotificationSettingsForm(
        email_notifications=settings.email_notifications,
        push_notifications=settings.push_notifications
    )

    if form.validate_on_submit():
        settings.email_notifications = form.email_notifications.data
        settings.push_notifications = form.push_notifications.data
        db.session.commit()
        flash('Notification settings updated successfully!', 'success')
        return redirect(url_for('main.notification_settings'))

    return render_template('notification_settings.html', form=form, farmers_form=farmers_form)


@main.route('/notifications/<int:notification_id>/archive', methods=['POST'])
@login_required
def archive_notification(notification_id):
    user_notification = UserNotification.query.filter_by(
        user_id=current_user.id, notification_id=notification_id
    ).first()
    if user_notification:
        user_notification.is_archived = True
        db.session.commit()
        flash('Notification archived.', 'success')
    else:
        flash('Notification not found.', 'danger')
    return redirect(url_for('main.view_notifications'))


@main.route('/notifications/<int:notification_id>/unarchive', methods=['POST'])
@login_required
def unarchive_notification(notification_id):
    user_notification = UserNotification.query.filter_by(
        user_id=current_user.id, notification_id=notification_id
    ).first()
    if user_notification:
        user_notification.is_archived = False
        db.session.commit()
        flash('Notification unarchived.', 'success')
    else:
        flash('Notification not found.', 'danger')
    return redirect(url_for('main.view_notifications'))


@main.route('/notifications/unread_count', methods=['GET'])
@login_required
def unread_notification_count():
    unread_count = (
        UserNotification.query
        .join(Notification, UserNotification.notification_id == Notification.id)
        .filter(UserNotification.user_id == current_user.id, UserNotification.is_read == False, Notification.is_active == True)
        .count()
    )
    return jsonify({'unread_count': unread_count})


@main.route('/dashboard/notifications', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard_notifications():
    farmers_form = FarmersForm()
    # Pagination setup
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of notifications per page
    pagination = Notification.query.order_by(Notification.date_sent.desc()).paginate(page=page, per_page=per_page)
    notifications = pagination.items

    notification_form = NotificationForm()
    form = EmptyForm()

    return render_template(
        'dashboard_notifications.html',
        notifications=notifications,
        notification_form=notification_form,
        farmers_form=farmers_form,
        form=form,
        pagination=pagination
    )


@main.route('/dashboard/notifications/edit/<int:notification_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    form = NotificationForm(obj=notification)
    farmers_form = FarmersForm()

    if form.validate_on_submit():
        notification.title = form.title.data
        notification.message = form.message.data
        db.session.commit()
        flash("Notification updated successfully!", "success")
        return redirect(url_for('main.dashboard_notifications'))

    return render_template('edit_notification.html', form=form, notification=notification, farmers_form=farmers_form)


@main.route('/dashboard/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
@admin_required
def delete_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    # Explicitly delete UserNotification entries
    UserNotification.query.filter_by(notification_id=notification_id).delete()

    db.session.delete(notification)
    db.session.commit()
    flash("Notification deleted successfully!", "success")
    return redirect(url_for('main.dashboard_notifications'))


@main.route('/user_settings')
@login_required
def user_settings():
    farmers_form = FarmersForm()
    return render_template('user_settings.html', farmers_form=farmers_form)
