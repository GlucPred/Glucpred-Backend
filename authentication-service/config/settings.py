import os
from datetime import timedelta


class Config:
    """Application configuration"""
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:password@auth-db:3306/auth_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-IN-PRODUCTION')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRATION_HOURS', 24)))
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-flask-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
