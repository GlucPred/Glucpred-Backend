import os


class Config:
    """Application configuration"""
    
    # Database Configuration
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'records_db')
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQL_ECHO', 'False').lower() == 'true'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key-change-in-production')
    
    # Glucose level thresholds (mg/dL)
    GLUCOSE_LOW_THRESHOLD = 70
    GLUCOSE_NORMAL_MIN = 70
    GLUCOSE_NORMAL_MAX = 140
    GLUCOSE_HIGH_THRESHOLD = 140
