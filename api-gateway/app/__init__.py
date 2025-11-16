from flask import Flask
from flask_cors import CORS
from app.routes import auth_routes, profile_routes, doctor_profile_routes, health_routes
from app.swagger_config import init_swagger
from config.settings import Config


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize CORS
    CORS(app)
    
    # Initialize Swagger
    init_swagger(app)
    
    # Register blueprints
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(profile_routes.bp)
    app.register_blueprint(doctor_profile_routes.bp)
    app.register_blueprint(health_routes.bp)
    
    return app
