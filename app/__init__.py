# FILE: app/__init__.py

import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from .database import get_mongo_db, close_connections
from .models import User
from apscheduler.schedulers.background import BackgroundScheduler
from .sync import sync_data_from_sql
import logging

# Initialize extensions in the global scope
login_manager = LoginManager()
mail = Mail()
# We do not call get_mongo_db() here anymore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """
    Creates and configures the Flask application.
    This is the application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    # With the new database setup, 'app.db' can be accessed via get_mongo_db()
    # within a request context, which is safer.
    
    # --- Register Blueprints ---
    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from .qc_module.routes import qc_bp
    app.register_blueprint(qc_bp)

    from .ir_module.routes import ir_bp
    app.register_blueprint(ir_bp)

    from .cc_module.routes import cc_bp
    app.register_blueprint(cc_bp)

    from .dispatch_module.routes import dispatch_bp
    app.register_blueprint(dispatch_bp)
    
    from .api_routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # --- Scheduler for background tasks ---
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        scheduler = BackgroundScheduler(daemon=True)
        def sync_with_context():
            with app.app_context():
                sync_data_from_sql()
        
        scheduler.add_job(id='sync_sql_job', func=sync_with_context, trigger='interval', hours=1)
        scheduler.start()
        logger.info("Background scheduler started.")

    # I have registered the teardown function correctly.
    @app.teardown_appcontext
    def teardown_db(exception):
        close_connections(exception)

    return app

@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database. Must be done within an app context."""
    # We must use get_mongo_db() here to ensure we have a context.
    db = get_mongo_db()
    user_doc = db.users.find_one({'_id': user_id})
    if user_doc:
        return User(user_doc)
    return None
