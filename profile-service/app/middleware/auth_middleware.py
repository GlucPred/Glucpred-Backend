import jwt
from flask import request, jsonify
from functools import wraps
from config.settings import Config


class JWTAuthMiddleware:
    """Middleware for JWT authentication"""
    
    @staticmethod
    def token_required(f):
        """
        Decorator to verify JWT token
        
        Usage:
            @token_required
            def protected_route():
                # Access request.current_user for user info
                pass
        """
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                # Accept both "Bearer <token>" and just "<token>"
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(" ")[1]
                else:
                    token = auth_header
            
            if not token:
                return jsonify({'error': 'Token no proporcionado'}), 401
            
            try:
                # Decode token
                payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
                request.current_user = payload
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expirado'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Token inválido'}), 401
            
            return f(*args, **kwargs)
        
        return decorated
