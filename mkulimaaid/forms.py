from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from mkulimaaid.models import User
from wtforms import StringField, PasswordField, SubmitField, BooleanField,FileField
import re

class UploadForm(FlaskForm):
    image = FileField('Upload Image', validators=[DataRequired()])
    submit = SubmitField('Upload')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
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
