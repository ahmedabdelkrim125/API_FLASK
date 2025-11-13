from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from translations import translate

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()

def get_language():
    """Get language from request headers or default to English"""
    lang = request.headers.get('Accept-Language', 'en')
    # Extract primary language (e.g., 'en-US' -> 'en')
    if '-' in lang:
        lang = lang.split('-')[0]
    # Support only 'en' and 'ar' for now
    if lang not in ['en', 'ar']:
        lang = 'en'
    return lang

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.fields import fields_bp
    from routes.bookings import bookings_bp
    from routes.reviews import reviews_bp
    from routes.teams import teams_bp
    from routes.payments import payments_bp
    from routes.clubs import clubs_bp
    from routes.notifications import notifications_bp
    from routes.analytics import analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(fields_bp, url_prefix='/api')
    app.register_blueprint(bookings_bp, url_prefix='/api')
    app.register_blueprint(reviews_bp, url_prefix='/api')
    app.register_blueprint(teams_bp, url_prefix='/api')
    app.register_blueprint(payments_bp, url_prefix='/api')
    app.register_blueprint(clubs_bp, url_prefix='/api')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    
    # Add language support to app context
    @app.before_request
    def before_request():
        # Make language available in request context
        pass
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Create tables within app context
    with app.app_context():
        db.create_all()
    app.run(debug=True)