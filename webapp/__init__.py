from flask import Flask
from flask_bootstrap import Bootstrap
from flask_dropzone import Dropzone
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy


REQUIRED_PIXEL_COLOR = (34, 34, 34)  # 222222
EXPECTED_PIXELS_PER_LINE = 250

# Globally accessible libraries
db = SQLAlchemy()
sess = Session()
dropzone = Dropzone()


def create_app(configfile=None):
    # We are using the "Application Factory"-pattern here, which is described
    # in detail inside the Flask docs:
    # http://flask.pocoo.org/docs/patterns/appfactories/
    """Initialize the core application."""
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    # Initialize Plugins
    Bootstrap(app)  # Install Bootstrap extension
    db.init_app(app)
    sess.init_app(app)

    with app.app_context():
        # Include our Routes
        from .uploader import routes as uploader_routes
        from .auth import routes as auth_routes

        # Register Blueprints
        app.register_blueprint(uploader_routes.uploader_bp)
        app.register_blueprint(auth_routes.auth_bp)
        dropzone.init_app(app)

    return app
