from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp, Optional
from mkulimaaid.models import User
import re
from wtforms import StringField, PasswordField, SubmitField, DecimalField, FileField, BooleanField, TextAreaField
from flask_wtf.file import FileAllowed
from wtforms import IntegerField
from config import Config
from flask_login import current_user
from mkulimaaid import bcrypt


class UploadForm(FlaskForm):
    image = FileField('Upload Image', validators=[DataRequired()])
    submit = SubmitField('Upload')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message="Please enter a valid email address.")])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    fullname = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100),
        Regexp('^[A-Za-z ]*$', 0, 'Full name must contain only letters and spaces')
    ])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=10)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    # Existing custom validators for username and email
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

    # New custom validator for phone number
    def validate_phone(self, phone):
        if not re.match(r'^\d{10}$', phone.data):
            raise ValidationError('Phone number must contain exactly 10 digits and only numbers.')
class AdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Add Admin')


class DiseaseForm(FlaskForm):
    name = StringField('Disease Name', validators=[DataRequired()])
    scientific_name = StringField('Scientific Name', validators=[Optional()])
    symptoms = TextAreaField('Symptoms', validators=[DataRequired()])
    causes = TextAreaField('Causes', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    organic_control = TextAreaField('Organic Control Methods', validators=[Optional()])
    chemical_control = TextAreaField('Chemical Control Methods', validators=[Optional()])
    preventive_measures = TextAreaField('Preventive Measures', validators=[Optional()])
    image = FileField('Disease Image', validators=[Optional(), FileAllowed(Config.ALLOWED_EXTENSIONS, 'Images only!')])


# Profile update form
class ProfileForm(FlaskForm):
    fullname = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(max=15)])
    submit = SubmitField('Update Profile')
    avatar = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'jfif'], 'Images only!')])

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already in use. Please choose a different one.')

# Password change form
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

    def validate_current_password(self, current_password):
        if not bcrypt.check_password_hash(current_user.password, current_password.data):
            raise ValidationError('Current password is incorrect.')


class CommentForm(FlaskForm):
    comment = TextAreaField('Add a Comment', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Post Comment')


class VideoForm(FlaskForm):
    title = StringField('Video Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    url = StringField('YouTube Video URL', validators=[DataRequired(), Length(max=200)])
    published = BooleanField('Published')
    submit = SubmitField('Submit')

    def validate_url(self, url):
        # Enhanced regex to match YouTube URL formats including query parameters
        youtube_regex = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/|.+)?([a-zA-Z0-9_-]{11})(\S+)?$'
        if not re.match(youtube_regex, url.data):
            raise ValidationError('Please enter a valid YouTube URL.')


class TopicForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    is_trending = BooleanField('Trending')
    submit = SubmitField('Submit')

