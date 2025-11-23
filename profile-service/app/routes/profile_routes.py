from flask import Blueprint, request, jsonify
from app.services import ProfileService
from app.middleware import JWTAuthMiddleware


bp = Blueprint('patient_profile', __name__, url_prefix='/api/profile/paciente')
bp_admin = Blueprint('profile_admin', __name__, url_prefix='/api/profile')
token_required = JWTAuthMiddleware.token_required


@bp.route('', methods=['POST'])
@token_required
def create_profile():
    """
    Create a new profile
    Expected JSON:
    {
        "edad": int (optional),
        "peso": float (optional),
        "altura": float (optional),
        "medicamentos": string (optional),
        "antecedentes": string (optional),
        "fecha_diagnostico": string "YYYY-MM-DD" (optional)
    }
    """
    try:
        # Get user_id from JWT token (set by middleware)
        user_id = request.current_user.get('user_id')
        
        data = request.get_json()
        # Add user_id from token to data
        data['user_id'] = user_id
        
        profile_dict, error = ProfileService.create_profile(data)
        
        if profile_dict is None:
            status_code = 400 if 'requerido' in error or 'inválido' in error else 409
            return jsonify({'error': error}), status_code
        
        return jsonify({
            'message': 'Perfil creado exitosamente',
            'profile': profile_dict
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500


@bp.route('', methods=['GET'])
@token_required
def get_profile():
    """Get profile of authenticated user"""
    try:
        # Get user_id from JWT token (set by middleware)
        user_id = request.current_user.get('user_id')
        
        profile_dict, error = ProfileService.get_profile(user_id)
        
        if profile_dict is None:
            return jsonify({'error': error}), 404
        
        return jsonify({'profile': profile_dict}), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500


@bp.route('', methods=['PUT'])
@token_required
def update_profile():
    """
    Update profile of authenticated user
    Expected JSON (all fields optional):
    {
        "edad": int,
        "peso": float,
        "altura": float,
        "medicamentos": string,
        "antecedentes": string,
        "fecha_diagnostico": string "YYYY-MM-DD"
    }
    """
    try:
        # Get user_id from JWT token (set by middleware)
        user_id = request.current_user.get('user_id')
        
        data = request.get_json()
        profile_dict, error = ProfileService.update_profile(user_id, data)
        
        if profile_dict is None:
            status_code = 400 if 'inválido' in error else 404
            return jsonify({'error': error}), status_code
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'profile': profile_dict
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
        'service': 'profile-service'
    }), 200


@bp_admin.route('/all', methods=['GET'])
@token_required
def get_all_profiles():
    """
    Get all patient profiles (for doctor to view available patients)
    Only accessible by doctors or admins
    """
    try:
        # Verificar que el usuario tenga rol de doctor (el token usa 'rol' y el valor es 'Medico')
        user_role = request.current_user.get('rol')
        if user_role != 'Medico':
            return jsonify({'error': 'Acceso denegado. Solo médicos pueden ver todos los perfiles'}), 403
        
        profiles, error = ProfileService.get_all_profiles()
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'profiles': profiles,
            'total': len(profiles)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
