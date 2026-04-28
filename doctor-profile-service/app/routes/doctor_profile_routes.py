from flask import Blueprint, request, jsonify
from app.services import DoctorProfileService
from app.middleware import JWTAuthMiddleware
import logging

logger = logging.getLogger(__name__)


bp = Blueprint('doctor_profile', __name__, url_prefix='/api/profile/medico')
token_required = JWTAuthMiddleware.token_required


@bp.route('', methods=['POST'])
@token_required
def create_doctor_profile():
    """
    Create a new doctor profile
    Expected JSON:
    {
        "numero_colegiatura": string (required),
        "especialidad": string (required),
        "centro_trabajo": string (required)
    }
    """
    try:
        # Get user_id from JWT token (set by middleware)
        user_id = request.current_user.get('user_id')
        
        data = request.get_json()
        # Add user_id from token to data
        data['user_id'] = user_id
        
        profile_dict, error = DoctorProfileService.create_doctor_profile(data)
        
        if profile_dict is None:
            status_code = 400 if 'requerido' in error or 'requerida' in error else 409
            return jsonify({'error': error}), status_code
        
        return jsonify({
            'message': 'Perfil de médico creado exitosamente',
            'profile': profile_dict
        }), 201
        
    except Exception as e:
        logger.error(f'Error al crear perfil de médico: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('', methods=['GET'])
@token_required
def get_doctor_profile():
    """Get doctor profile for authenticated user"""
    try:
        user_id = request.current_user.get('user_id')
        
        profile_dict, error = DoctorProfileService.get_doctor_profile(user_id)
        
        if profile_dict is None:
            return jsonify({'error': error}), 404
        
        return jsonify({'profile': profile_dict}), 200
        
    except Exception as e:
        logger.error(f'Error al obtener perfil de médico: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('', methods=['PUT'])
@token_required
def update_doctor_profile():
    """
    Update doctor profile
    Expected JSON (all optional):
    {
        "numero_colegiatura": string,
        "especialidad": string,
        "centro_trabajo": string
    }
    """
    try:
        user_id = request.current_user.get('user_id')
        data = request.get_json()
        
        profile_dict, error = DoctorProfileService.update_doctor_profile(user_id, data)
        
        if profile_dict is None:
            return jsonify({'error': error}), 404
        
        return jsonify({
            'message': 'Perfil de médico actualizado exitosamente',
            'profile': profile_dict
        }), 200
        
    except Exception as e:
        logger.error(f'Error al actualizar perfil de médico: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor'
        }), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'doctor-profile-service'}), 200
