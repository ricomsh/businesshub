from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user

def role_required(*roles):
    """
    Decorator that checks if a user has at least one of the specified roles.
    - An 'admin' role bypasses the check.
    - If the check fails, it flashes an error message and redirects the user.
    """
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("You must be logged in to access this page.", "warning")
                return redirect(url_for('auth.login', next=request.url))

            # Admin has access to everything
            if 'admin' in current_user.roles:
                return f(*args, **kwargs)

            # Check if the user has any of the required roles
            if not any(role in current_user.roles for role in roles):
                role_str = " or ".join(f"'{r}'" for r in roles)
                flash(f"Access Denied. This action requires the {role_str} role.", 'danger')
                return redirect(request.referrer or url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
 
