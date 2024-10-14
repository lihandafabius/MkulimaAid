from flask import Flask
from flask_wtf import CSRFProtect
from mkulimaaid import create_app

# Initialize CSRF protection
csrf = CSRFProtect()

app = create_app()

# Register CSRF protection with the app
csrf.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
