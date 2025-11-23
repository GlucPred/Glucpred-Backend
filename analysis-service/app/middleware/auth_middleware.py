from functools import wraps
from flask import request, jsonify
import jwt
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    """
    Middleware para validar token JWT
    Extrae user_id del token y lo agrega al request
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Obtener token del header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Formato de token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        try:
            # Decodificar token
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload.get('user_id')
            
            if not request.user_id:
                return jsonify({'error': 'Token inválido: user_id no encontrado'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        except Exception as e:
            logger.error(f"Error al validar token: {str(e)}")
            return jsonify({'error': 'Error al validar token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
