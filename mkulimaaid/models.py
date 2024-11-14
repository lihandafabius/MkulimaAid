# models.py
from mkulimaaid import db  # Import db from mkulimaaid where it is initialized
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):  # Use db.Model for SQLAlchemy models
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(100), nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with farmers if every farmer is also a user
    farmers = db.relationship('Farmer', backref='user', lazy=True)

    # Relationship with ContactMessages
    contact_messages = db.relationship('ContactMessage', backref='user', lazy=True)


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


class Diseases(db.Model):
    __tablename__ = 'diseases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Disease name
    scientific_name = db.Column(db.String(150), nullable=True)  # Scientific name
    symptoms = db.Column(db.Text, nullable=False)
    causes = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    organic_control = db.Column(db.Text, nullable=True)
    chemical_control = db.Column(db.Text, nullable=True)
    preventive_measures = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(100), nullable=True)  # Filepath for the image
    is_trending = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Disease {self.name}>'


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self):
        return f'<Subscriber {self.email}>'


class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('comments', lazy=True))



class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    published = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Video '{self.title}'>"


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_trending = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image = db.Column(db.String(120), nullable=True)

    author = db.relationship('User', backref=db.backref('topics', lazy=True))

    def __repr__(self):
        return f'<Topic {self.title}>'


class TopicComment(db.Model):
    __tablename__ = 'topic_comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    topic = db.relationship('Topic', backref=db.backref('comments', lazy=True, cascade="all, delete-orphan"))
    author = db.relationship('User', backref=db.backref('topic_comments', lazy=True))


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # Question title
    content = db.Column(db.Text, nullable=False)  # Question content
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Time of posting
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Author of the question

    author = db.relationship('User', backref=db.backref('questions', lazy=True))  # Relationship with User

    def __repr__(self):
        return f'<Question {self.title}>'

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # Answer content
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Time of posting
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)  # Related question
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Author of the answer

    question = db.relationship('Question', backref=db.backref('answers', lazy=True, cascade="all, delete-orphan"))  # Link answer to question
    author = db.relationship('User', backref=db.backref('answers', lazy=True))  # Link answer to user

    def __repr__(self):
        return f'<Answer by {self.author.username}>'



class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
    seen = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to User


    def __repr__(self):
        return f"ContactMessage('{self.name}', '{self.email}', '{self.subject}')"


class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    photo = db.Column(db.String(100), nullable=True)  # Photo file name
    contact_info = db.Column(db.String(200), nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    published = db.Column(db.Boolean, default=False)


    def __repr__(self):
        return f'<TeamMember {self.name}>'


class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_name = db.Column(db.String(100), nullable=False)
    farm_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    farm_size = db.Column(db.Float, nullable=False)
    crop_types = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    contact_info = db.Column(db.String(15), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to User

