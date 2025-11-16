from flask import Blueprint, request, jsonify
from app.utils import ServiceProxy
from app.middleware import extract_auth_header
from config.settings import Config
import jwt

bp = Blueprint('doctor_profile', __name__, url_prefix='/api/profile/medico')


@bp.route('', methods=['POST'])
@extract_auth_header
def create_doctor_profile(headers):
    """
    Crear perfil de médico
    ---
    tags:
      - Profile
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        description: Datos del perfil del médico
        required: true
        schema:
          type: object
          required:
            - numero_colegiatura
            - especialidad
            - centro_trabajo
          properties:
            numero_colegiatura:
              type: string
              example: "CMP-12345"
            especialidad:
              type: string
              example: "Endocrinología"
            centro_trabajo:
              type: string
              example: "Hospital Nacional"
    responses:
      201:
        description: Perfil de médico creado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            profile:
              type: object
      400:
        description: Datos inválidos
      401:
        description: Token inválido o no proporcionado
      409:
        description: El perfil ya existe
    """
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.DOCTOR_PROFILE_SERVICE_URL,
        '/api/profile/medico',
        method='POST',
        data=data,
        headers=headers
    )


@bp.route('', methods=['GET'])
@extract_auth_header
def get_doctor_profile(headers):
    """
    Obtener perfil completo de médico autenticado (datos de usuario + perfil médico)
    ---
    tags:
      - Profile
    security:
      - Bearer: []
    responses:
      200:
        description: Perfil encontrado
        schema:
          type: object
          properties:
            user:
              type: object
              properties:
                nombre_completo:
                  type: string
                username:
                  type: string
                email:
                  type: string
                numero_celular:
                  type: string
            profile:
              type: object
              properties:
                numero_colegiatura:
                  type: string
                especialidad:
                  type: string
                centro_trabajo:
                  type: string
      401:
        description: Token inválido o no proporcionado
      404:
        description: Perfil no encontrado
    """
    try:
        # Extract user_id from token
        token = headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        # Decode to get user_id (without verification, just to extract user_id)
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get('user_id')
        
        # Call both services
        # 1. Get user data from auth-service
        user_data, user_status = ServiceProxy.forward_request(
            Config.AUTH_SERVICE_URL,
            f'/api/auth/internal/user/{user_id}',
            method='GET'
        )
        
        if user_status != 200:
            return jsonify(user_data), user_status
        
        # 2. Get doctor profile data from doctor-profile-service
        profile_data, profile_status = ServiceProxy.forward_request(
            Config.DOCTOR_PROFILE_SERVICE_URL,
            '/api/profile/medico',
            method='GET',
            headers=headers
        )
        
        # If profile doesn't exist, return user data with empty profile
        if profile_status == 404:
            return jsonify({
                'user': user_data.get('user', {}),
                'profile': None,
                'message': 'Usuario sin perfil de médico creado'
            }), 200
        
        if profile_status != 200:
            return jsonify(profile_data), profile_status
        
        # Combine responses
        return jsonify({
            'user': user_data.get('user', {}),
            'profile': profile_data.get('profile', {})
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener perfil: {str(e)}'}), 500


@bp.route('', methods=['PUT'])
@extract_auth_header
def update_doctor_profile(headers):
    """
    Actualizar perfil completo de médico autenticado (datos de usuario + perfil médico)
    ---
    tags:
      - Profile
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        description: Datos a actualizar (todos opcionales)
        schema:
          type: object
          properties:
            # Datos de usuario (auth-service)
            nombre_completo:
              type: string
              example: "Dr. Juan Pérez García"
            email:
              type: string
              example: "dr.perez@example.com"
            username:
              type: string
              example: "drperez2024"
            numero_celular:
              type: string
              example: "987654321"
            # Datos de perfil médico (profile-service)
            numero_colegiatura:
              type: string
              example: "CMP-12345"
            especialidad:
              type: string
              example: "Endocrinología"
            centro_trabajo:
              type: string
              example: "Hospital Nacional"
    responses:
      200:
        description: Perfil actualizado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
            profile:
              type: object
      400:
        description: Datos inválidos
      401:
        description: Token inválido o no proporcionado
      404:
        description: Perfil no encontrado
    """
    try:
        data = request.get_json() or {}
        
        # Extract user_id from token
        token = headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get('user_id')
        
        # Separate user data from profile data
        user_fields = ['nombre_completo', 'email', 'username', 'numero_celular']
        profile_fields = ['numero_colegiatura', 'especialidad', 'centro_trabajo']
        
        user_data = {k: v for k, v in data.items() if k in user_fields}
        profile_data = {k: v for k, v in data.items() if k in profile_fields}
        
        responses = {}
        
        # Update user data if provided
        if user_data:
            user_result, user_status = ServiceProxy.forward_request(
                Config.AUTH_SERVICE_URL,
                f'/api/auth/internal/user/{user_id}',
                method='PUT',
                data=user_data
            )
            
            if user_status != 200:
                return jsonify(user_result), user_status
            
            responses['user'] = user_result.get('user', {})
        
        # Update profile data if provided
        if profile_data:
            profile_result, profile_status = ServiceProxy.forward_request(
                Config.DOCTOR_PROFILE_SERVICE_URL,
                '/api/profile/medico',
                method='PUT',
                data=profile_data,
                headers=headers
            )
            
            if profile_status != 200:
                return jsonify(profile_result), profile_status
            
            responses['profile'] = profile_result.get('profile', {})
        
        return jsonify({
            'message': 'Perfil de médico actualizado exitosamente',
            **responses
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al actualizar perfil: {str(e)}'}), 500
