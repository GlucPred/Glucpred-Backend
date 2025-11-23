from functools import wraps
from flask import request, jsonify
import jwt
import os
import logging

logger = logging.getLogger(__name__)

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key-change-in-production')


def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Token mal formado'}), 401
        
        if not token:
            return jsonify({'error': 'Token de autenticación requerido'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user_id = data.get('user_id')
            user_role = data.get('rol')  # El token usa 'rol' no 'role'
            
            if not current_user_id:
                return jsonify({'error': 'Token inválido'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Pass user info to the route
        return f(current_user_id, user_role, *args, **kwargs)
    
    return decorated


def doctor_required(f):
    """Decorator to ensure only doctors can access the route"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Token mal formado'}), 401
        
        if not token:
            return jsonify({'error': 'Token de autenticación requerido'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user_id = data.get('user_id')
            user_role = data.get('rol')  # El token usa 'rol' no 'role'
            
            if not current_user_id:
                return jsonify({'error': 'Token inválido'}), 401
            
            if user_role != 'Medico':  # El rol en la DB es 'Medico' con mayúscula
                return jsonify({'error': 'Acceso denegado. Solo médicos pueden acceder a este recurso'}), 403
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_user_id, user_role, *args, **kwargs)
    
    return decorated
