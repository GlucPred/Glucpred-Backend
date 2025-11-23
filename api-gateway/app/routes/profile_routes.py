from flask import Blueprint, request, jsonify
from app.utils import ServiceProxy
from app.middleware import extract_auth_header
from config.settings import Config
import jwt

bp = Blueprint('patient_profile', __name__, url_prefix='/api/profile/paciente')


@bp.route('', methods=['POST'])
@extract_auth_header
def create_profile(headers):
    """
    Crear perfil de paciente
    ---
    tags:
      - Profile
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        description: Datos del perfil del paciente
        required: true
        schema:
          type: object
          properties:
            edad:
              type: integer
              example: 45
            peso:
              type: number
              format: float
              example: 75.5
              description: Peso en kilogramos
            altura:
              type: number
              format: float
              example: 170
              description: Altura en centímetros
            medicamentos:
              type: string
              example: "Metformina 500mg 2 veces al día"
            antecedentes:
              type: string
              example: "Diabetes tipo 2, hipertensión"
            fecha_diagnostico:
              type: string
              format: date
              example: "2020-05-15"
    responses:
      201:
        description: Perfil creado exitosamente
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
        Config.PROFILE_SERVICE_URL,
        '/api/profile/paciente',
        method='POST',
        data=data,
        headers=headers
    )


@bp.route('', methods=['GET'])
@extract_auth_header
def get_profile(headers):
    """
    Obtener perfil completo de paciente autenticado (datos de usuario + perfil médico)
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
                edad:
                  type: integer
                peso:
                  type: number
                altura:
                  type: number
                imc:
                  type: number
                medicamentos:
                  type: string
                antecedentes:
                  type: string
                fecha_diagnostico:
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
        
        # 2. Get profile data from profile-service
        profile_data, profile_status = ServiceProxy.forward_request(
            Config.PROFILE_SERVICE_URL,
            '/api/profile/paciente',
            method='GET',
            headers=headers
        )
        
        # If profile doesn't exist, return user data with empty profile
        if profile_status == 404:
            return jsonify({
                'user': user_data.get('user', {}),
                'profile': None,
                'message': 'Usuario sin perfil médico creado'
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
def update_profile(headers):
    """
    Actualizar perfil completo de paciente autenticado (datos de usuario + perfil médico)
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
              example: "Juan Pérez García"
            email:
              type: string
              example: "juan.perez@example.com"
            username:
              type: string
              example: "juanperez2024"
            numero_celular:
              type: string
              example: "987654321"
            # Datos de perfil médico (profile-service)
            edad:
              type: integer
              example: 46
            peso:
              type: number
              format: float
              example: 73.0
            altura:
              type: number
              format: float
              example: 172
            medicamentos:
              type: string
              example: "Metformina 500mg 3 veces al día"
            antecedentes:
              type: string
              example: "Diabetes tipo 2, hipertensión, colesterol alto"
            fecha_diagnostico:
              type: string
              format: date
              example: "2020-05-15"
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
        profile_fields = ['edad', 'peso', 'altura', 'medicamentos', 'antecedentes', 'fecha_diagnostico']
        
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
                Config.PROFILE_SERVICE_URL,
                '/api/profile/paciente',
                method='PUT',
                data=profile_data,
                headers=headers
            )
            
            if profile_status != 200:
                return jsonify(profile_result), profile_status
            
            responses['profile'] = profile_result.get('profile', {})
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            **responses
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al actualizar perfil: {str(e)}'}), 500
