import os


class Config:
    """Application configuration"""
    
    # Service URLs
    AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://authentication-service:8081')
    PROFILE_SERVICE_URL = os.getenv('PROFILE_SERVICE_URL', 'http://profile-service:8082')
    
    # Request configuration
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-api-gateway-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
