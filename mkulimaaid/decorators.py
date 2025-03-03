from flask import abort, flash, redirect, url_for
from flask_login import current_user
from functools import wraps


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin:  # Check if the user is not an admin
            flash('You do not have access to this page.', 'danger')
            return redirect(url_for('main.upload'))  # Redirect to a safe page (e.g., dashboard)
        return func(*args, **kwargs)
    return decorated_view