from flask import jsonify
from flasgger import Swagger


def init_swagger(app):
    """Initialize Swagger documentation"""
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Glucpred API Gateway",
            "description": "API Gateway para el sistema de predicción de glucosa para pacientes con diabetes tipo 2",
            "version": "1.0.0",
            "contact": {
                "name": "Glucpred Team",
                "url": "https://github.com/GlucPred"
            }
        },
        "host": "localhost:5000",
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header usando el esquema Bearer. Ejemplo: 'Bearer {token}'"
            }
        }
    }
    
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    return swagger
