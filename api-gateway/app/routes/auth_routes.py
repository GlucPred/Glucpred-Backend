from flask import Blueprint, request
from app.utils import ServiceProxy
from config.settings import Config
from flasgger import swag_from

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """
    Registrar un nuevo usuario
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        description: Datos del nuevo usuario
        required: true
        schema:
          type: object
          required:
            - nombre_completo
            - username
            - email
            - password
            - confirmar_password
          properties:
            nombre_completo:
              type: string
              example: "Juan Pérez"
            username:
              type: string
              example: "juanperez"
            email:
              type: string
              example: "juan@example.com"
            numero_celular:
              type: string
              example: "1234567890"
            password:
              type: string
              example: "password123"
            confirmar_password:
              type: string
              example: "password123"
            rol:
              type: string
              enum: ["Paciente", "Medico"]
              example: "Paciente"
    responses:
      201:
        description: Usuario registrado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
            access_token:
              type: string
      400:
        description: Datos inválidos
      409:
        description: Usuario ya existe
    """
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.AUTH_SERVICE_URL,
        '/api/auth/register',
        method='POST',
        data=data
    )


@bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        description: Credenciales de acceso
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: Nombre de usuario o correo electrónico
              example: "juanperez"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: Login exitoso
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
            access_token:
              type: string
      401:
        description: Credenciales inválidas
    """
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.AUTH_SERVICE_URL,
        '/api/auth/login',
        method='POST',
        data=data
    )
