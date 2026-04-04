import os

class Config:
    """Configuration for Analysis Service"""
    
    # Flask
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    PORT = int(os.getenv('PORT', 5000))
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-IN-PRODUCTION')
    
    # Kafka
    KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:29092')
    EVENT_TOPIC = os.getenv('EVENT_TOPIC', 'event-bus')
    
    # Model
    MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/episode_predictor.joblib')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
