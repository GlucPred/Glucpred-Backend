from flask import Flask
from app.extensions import cors
from app.routes.predict_routes import bp as predict_bp
from config.settings import Config
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    cors.init_app(app, origins=Config.CORS_ORIGINS)
    
    # Registrar blueprints
    app.register_blueprint(predict_bp, url_prefix='/api/analysis')
    
    logger.info("Analysis Service iniciado correctamente")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG
    )
