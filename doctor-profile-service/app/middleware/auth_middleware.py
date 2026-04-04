from functools import wraps
from flask import request, jsonify
import jwt
from config.settings import Config


class JWTAuthMiddleware:
    """Middleware for JWT authentication"""
    
    @staticmethod
    def token_required(f):
        """Decorator to validate JWT token"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if auth_header:
                # Handle both "Bearer <token>" and "<token>" formats
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                else:
                    token = auth_header
            
            if not token:
                return jsonify({'error': 'Token no proporcionado'}), 401
            
            try:
                # Decode token (without verification for now, as we trust the gateway)
                payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
                
                # Store user info in request context
                request.current_user = payload
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expirado'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Token inválido'}), 401
            
            return f(*args, **kwargs)
        
        return decorated
