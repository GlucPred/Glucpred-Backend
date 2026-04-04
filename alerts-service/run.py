from flask import Flask
from app.extensions import db, cors
from app.routes import alert_routes
from app.events.kafka_consumer import GlucoseEventConsumer
from config.settings import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, origins=[
        'http://localhost:*',
        'http://127.0.0.1:*',
    ], supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(alert_routes.bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
    
    # Start Kafka consumer
    consumer = GlucoseEventConsumer(app)
    consumer.start()
    
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'healthy', 'service': 'alerts-service'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
