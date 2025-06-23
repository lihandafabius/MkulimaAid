from mkulimaaid import create_app, db
from flask_wtf import CSRFProtect

# Initialize CSRF protection
csrf = CSRFProtect()

app = create_app()

# Register CSRF protection with the app
csrf.init_app(app)

if __name__ == "__main__":
    # Create database tables and run the app
    with app.app_context():
        db.create_all()
    app.run(debug=True)



