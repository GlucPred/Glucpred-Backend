from flask import Blueprint, request, jsonify
from app.services import AuthService


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
            return jsonify({'error': token}), 400 if 'requerido' in token or 'coinciden' in token else 409
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': user_dict,
            'access_token': token
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
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
            return jsonify({'error': token}), 400 if 'requeridos' in token else 401
        
        return jsonify({
            'message': 'Login exitoso',
            'user': user_dict,
            'access_token': token
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'authentication-service'
    }), 200


@bp.route('/internal/mark-profile-complete/<int:user_id>', methods=['POST'])
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
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
