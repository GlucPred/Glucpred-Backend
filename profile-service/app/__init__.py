from flask import Flask
from flask_cors import CORS
from app.extensions import db
from app.routes import profile_routes
from config.settings import Config
import time
import logging

logger = logging.getLogger(__name__)


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(profile_routes.bp)
    
    # Create tables with retry logic
    with app.app_context():
        max_retries = 30
        retry_interval = 2
        
        for attempt in range(max_retries):
            try:
                db.create_all()
                logger.info("Database tables created successfully")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {retry_interval}s...")
                    time.sleep(retry_interval)
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts")
                    raise
    
    return app
