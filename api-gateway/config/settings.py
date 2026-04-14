import os


class Config:
    """Application configuration"""
    
    # Service URLs
    AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://authentication-service:8081')
    PROFILE_SERVICE_URL = os.getenv('PROFILE_SERVICE_URL', 'http://profile-service:8082')
    DOCTOR_PROFILE_SERVICE_URL = os.getenv('DOCTOR_PROFILE_SERVICE_URL', 'http://doctor-profile-service:8083')
    DOCTOR_PATIENT_SERVICE_URL = os.getenv('DOCTOR_PATIENT_SERVICE_URL', 'http://doctor-patient-service:8084')
    RECORDS_SERVICE_URL = os.getenv('RECORDS_SERVICE_URL', 'http://records-service:8085')
    ALERTS_SERVICE_URL = os.getenv('ALERTS_SERVICE_URL', 'http://alerts-service:8086')
    ANALYSIS_SERVICE_URL = os.getenv('ANALYSIS_SERVICE_URL', 'http://analysis-service:5000')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-IN-PRODUCTION')
    
    # Request configuration
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-api-gateway-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
