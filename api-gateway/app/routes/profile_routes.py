from flask import Blueprint, request
from app.utils import ServiceProxy
from app.middleware import extract_auth_header
from config.settings import Config

bp = Blueprint('profile', __name__, url_prefix='/api/profile')


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
          required:
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
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
        '/api/profile',
        method='POST',
        data=data,
        headers=headers
    )


@bp.route('/<int:user_id>', methods=['GET'])
@extract_auth_header
def get_profile(user_id, headers):
    """
    Obtener perfil de paciente
    ---
    tags:
      - Profile
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Perfil encontrado
        schema:
          type: object
          properties:
            profile:
              type: object
              properties:
                id:
                  type: integer
                user_id:
                  type: integer
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
    return ServiceProxy.forward_request(
        Config.PROFILE_SERVICE_URL,
        f'/api/profile/{user_id}',
        method='GET',
        headers=headers
    )


@bp.route('/<int:user_id>', methods=['PUT'])
@extract_auth_header
def update_profile(user_id, headers):
    """
    Actualizar perfil de paciente
    ---
    tags:
      - Profile
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: ID del usuario
      - in: body
        name: body
        description: Datos a actualizar (todos opcionales)
        schema:
          type: object
          properties:
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
            profile:
              type: object
      400:
        description: Datos inválidos
      401:
        description: Token inválido o no proporcionado
      404:
        description: Perfil no encontrado
    """
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.PROFILE_SERVICE_URL,
        f'/api/profile/{user_id}',
        method='PUT',
        data=data,
        headers=headers
    )
