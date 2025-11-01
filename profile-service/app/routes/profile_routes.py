from flask import Blueprint, request, jsonify
from app.services import ProfileService
from app.middleware import JWTAuthMiddleware


bp = Blueprint('profile', __name__, url_prefix='/api/profile')
token_required = JWTAuthMiddleware.token_required


@bp.route('', methods=['POST'])
@token_required
def create_profile():
    """
    Create a new profile
    Expected JSON:
    {
        "user_id": int,
        "edad": int (optional),
        "peso": float (optional),
        "altura": float (optional),
        "medicamentos": string (optional),
        "antecedentes": string (optional),
        "fecha_diagnostico": string "YYYY-MM-DD" (optional)
    }
    """
    try:
        data = request.get_json()
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


@bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_profile(user_id):
    """Get profile by user_id"""
    try:
        profile_dict, error = ProfileService.get_profile(user_id)
        
        if profile_dict is None:
            return jsonify({'error': error}), 404
        
        return jsonify({'profile': profile_dict}), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500


@bp.route('/<int:user_id>', methods=['PUT'])
@token_required
def update_profile(user_id):
    """
    Update profile by user_id
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
