import os
from urllib.parse import quote_plus

class Config:
    # Database
    DB_USER = os.getenv('DB_USER', 'alerts_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'alerts_pass')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3312')
    DB_NAME = os.getenv('DB_NAME', 'alerts_db')
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}'
        f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-IN-PRODUCTION')
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_GLUCOSE_RECORDED = 'glucose.recorded'
    KAFKA_GROUP_ID = 'alerts-service-group'
    
    # Server
    PORT = int(os.getenv('PORT', 8086))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
