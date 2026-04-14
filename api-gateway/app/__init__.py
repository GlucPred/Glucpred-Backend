from flask import Flask
from flask_cors import CORS
from app.routes import auth_routes, profile_routes, doctor_profile_routes, doctor_patient_routes, records_routes, alerts_routes, health_routes, analysis_routes
from app.swagger_config import init_swagger
from config.settings import Config


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize CORS
    CORS(app, origins=[
        'http://localhost:*',
        'http://127.0.0.1:*',
    ], supports_credentials=True)
    
    # Initialize Swagger
    init_swagger(app)
    
    # Register blueprints
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(profile_routes.bp)
    app.register_blueprint(doctor_profile_routes.bp)
    app.register_blueprint(doctor_patient_routes.bp)
    app.register_blueprint(records_routes.bp)
    app.register_blueprint(alerts_routes.bp)
    app.register_blueprint(analysis_routes.bp)
    app.register_blueprint(health_routes.bp)

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    return app
