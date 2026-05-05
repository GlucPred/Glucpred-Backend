import os
from urllib.parse import quote_plus


class Config:
    """Application configuration"""
    
    # Database Configuration
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'doctor_patient_db')
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}'
        f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQL_ECHO', 'False').lower() == 'true'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-IN-PRODUCTION')
    
    # Internal API key for service-to-service calls
    INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', 'change-this-internal-key')
    
    # Service URLs for inter-service communication
    PROFILE_SERVICE_URL = os.getenv('PROFILE_SERVICE_URL', 'http://profile-service:8082')
    DOCTOR_PROFILE_SERVICE_URL = os.getenv('DOCTOR_PROFILE_SERVICE_URL', 'http://doctor-profile-service:8083')
