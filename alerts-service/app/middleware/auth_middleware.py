from functools import wraps
from flask import request, jsonify
import jwt
from config.settings import Config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Token malformado'}), 401
        
        if not token:
            return jsonify({'error': 'Token faltante'}), 401
        
        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            request.user_id = data['user_id']
            request.user_role = data.get('role', 'paciente')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def doctor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.user_role != 'medico':
            return jsonify({'error': 'Acceso denegado. Solo médicos'}), 403
        return f(*args, **kwargs)
    
    return decorated
