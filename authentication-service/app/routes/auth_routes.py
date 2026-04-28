from flask import Blueprint, request, jsonify
from app.services import AuthService
from functools import wraps
import jwt as pyjwt
import os
import logging

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', 'glucpred-internal-key-change-in-production')


def internal_service_required(f):
    """Decorator to validate internal service API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-Internal-Api-Key')
        if not api_key or api_key != INTERNAL_API_KEY:
            return jsonify({'error': 'Acceso no autorizado - Se requiere API key interna'}), 403
        return f(*args, **kwargs)
    return decorated


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'Token de acceso requerido'}), 401
        try:
            secret = os.getenv('JWT_SECRET_KEY', 'glucpred-secret-key-change-in-production')
            payload = pyjwt.decode(token, secret, algorithms=['HS256'])
            request.current_user_id = payload.get('user_id')
        except pyjwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        return f(*args, **kwargs)
    return decorated


bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Expected JSON:
    {
        "nombre_completo": "string",
        "username": "string",
        "email": "string",
        "numero_celular": "string" (optional),
        "password": "string",
        "confirmar_password": "string",
        "rol": "Paciente" or "Medico" (default: "Paciente")
    }
    """
    try:
        data = request.get_json()
        user_dict, token = AuthService.register_user(data)
        
        if user_dict is None:
            return jsonify({'error': token['error']}), token.get('status_code', 500)
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': user_dict,
            'access_token': token
        }), 201
        
    except Exception as e:
        logger.error(f'Error en registro: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    Expected JSON:
    {
        "username": "string" (can be username or email),
        "password": "string"
    }
    """
    try:
        data = request.get_json()
        username_or_email = data.get('username')
        password = data.get('password')
        
        user_dict, token = AuthService.login_user(username_or_email, password)
        
        if user_dict is None:
            return jsonify({'error': token['error']}), token.get('status_code', 500)
        
        return jsonify({
            'message': 'Login exitoso',
            'user': user_dict,
            'access_token': token
        }), 200
        
    except Exception as e:
        logger.error(f'Error en login: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'authentication-service'
    }), 200


@bp.route('/internal/mark-profile-complete/<int:user_id>', methods=['POST'])
@internal_service_required
def mark_profile_complete(user_id):
    """
    Internal endpoint to mark user as having completed initial profile setup
    This should only be called by other microservices (profile-service)
    """
    try:
        success, error = AuthService.mark_profile_complete(user_id)
        
        if not success:
            return jsonify({'error': error}), 404
        
        return jsonify({
            'message': 'Usuario marcado como configurado'
        }), 200
        
    except Exception as e:
        logger.error(f'Error en mark_profile_complete: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('/internal/user/<int:user_id>', methods=['GET'])
@internal_service_required
def get_user_data(user_id):
    """
    Internal endpoint to get user data
    Used by API Gateway to combine with profile data
    """
    try:
        user_dict, error = AuthService.get_user_data(user_id)
        
        if user_dict is None:
            return jsonify({'error': error}), 404
        
        return jsonify({'user': user_dict}), 200
        
    except Exception as e:
        logger.error(f'Error en get_user_data: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('/internal/user/<int:user_id>', methods=['PUT'])
@internal_service_required
def update_user_data(user_id):
    """
    Internal endpoint to update user data
    Used by API Gateway when updating profile
    Expected JSON (all optional):
    {
        "nombre_completo": "string",
        "email": "string",
        "username": "string",
        "numero_celular": "string"
    }
    """
    try:
        data = request.get_json()
        user_dict, error = AuthService.update_user_data(user_id, data)
        
        if user_dict is None:
            if 'uso' in error or 'registrado' in error:
                status_code = 400
            else:
                status_code = 404
            return jsonify({'error': error}), status_code
        
        return jsonify({
            'message': 'Datos de usuario actualizados',
            'user': user_dict
        }), 200
        
    except Exception as e:
        logger.error(f'Error en update_user_data: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('/users', methods=['GET'])
@internal_service_required
def get_all_users():
    """
    Get all users (for internal microservice use)
    Returns basic user information including rol
    """
    try:
        users, error = AuthService.get_all_users()
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'users': users,
            'total': len(users)
        }), 200
        
    except Exception as e:
        logger.error(f'Error en get_all_users: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Restablecer contraseña (flujo simplificado sin verificación de correo)"""
    try:
        data = request.get_json()
        username_or_email = data.get('username_or_email') if data else None
        new_password = data.get('new_password') if data else None
        
        success, error = AuthService.reset_password(username_or_email, new_password)
        
        if success is None:
            return jsonify({'error': error['error']}), error.get('status_code', 500)
        
        return jsonify({'message': 'Contraseña restablecida exitosamente'}), 200
        
    except Exception as e:
        logger.error(f'Error en forgot_password: {str(e)}', exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500


@bp.route('/change-password', methods=['PUT'])
@token_required
def change_password():
    """Cambiar contraseña del usuario autenticado"""
    try:
        data = request.get_json()
        new_password = data.get('new_password') if data else None
        user_id = request.current_user_id
        
        success, error = AuthService.change_password(user_id, new_password)
        
        if success is None:
            return jsonify({'error': error['error']}), error.get('status_code', 500)
        
        return jsonify({'message': 'Contraseña actualizada exitosamente'}), 200
        
    except Exception as e:
        logger.error(f'Error en change_password: {str(e)}', exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500
