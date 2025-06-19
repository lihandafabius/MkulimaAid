from mkulimaaid import create_app, db  # Import db
from flask_wtf import CSRFProtect

# Initialize CSRF protection
csrf = CSRFProtect()

app = create_app()

# Register CSRF protection with the app
csrf.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()  # This creates the database tables

if __name__ == '__main__':
    app.run(debug=False)
