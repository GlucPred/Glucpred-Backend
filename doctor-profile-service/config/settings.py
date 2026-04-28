import os
from urllib.parse import quote_plus


class Config:
    """Application configuration"""
    
    # Database configuration
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root_password')
    DB_HOST = os.getenv('DB_HOST', 'doctor-profile-db')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'doctor_profile_db')
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}'
        f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-IN-PRODUCTION')
    
    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
