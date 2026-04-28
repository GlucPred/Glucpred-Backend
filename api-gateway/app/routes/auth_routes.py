from flask import Blueprint, request
from app.utils import ServiceProxy
from config.settings import Config
from flasgger import swag_from

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """
    Registrar un nuevo usuario — Paso 1: envía código OTP al email
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
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
              example: "Password123"
            confirmar_password:
              type: string
              example: "Password123"
            rol:
              type: string
              enum: ["Paciente", "Medico"]
              example: "Paciente"
    responses:
      200:
        description: Código OTP enviado al correo electrónico
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


@bp.route('/register/verify', methods=['POST'])
def register_verify():
    """
    Registrar un nuevo usuario — Paso 2: verificar OTP y crear cuenta
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - code
          properties:
            email:
              type: string
              example: "juan@example.com"
            code:
              type: string
              example: "123456"
    responses:
      201:
        description: Usuario creado y JWT generado
      400:
        description: Código inválido o expirado
    """
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.AUTH_SERVICE_URL,
        '/api/auth/register/verify',
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
              properties:
                id:
                  type: integer
                nombre_completo:
                  type: string
                username:
                  type: string
                email:
                  type: string
                rol:
                  type: string
                primer_inicio_sesion:
                  type: boolean
                  description: Indica si el usuario aún no ha configurado su perfil
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


@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Recuperar contraseña — Paso 1: enviar OTP al correo registrado"""
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.AUTH_SERVICE_URL,
        '/api/auth/forgot-password',
        method='POST',
        data=data
    )


@bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Recuperar contraseña — Paso 2: verificar OTP y establecer nueva contraseña"""
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.AUTH_SERVICE_URL,
        '/api/auth/reset-password',
        method='POST',
        data=data
    )


@bp.route('/change-password', methods=['PUT'])
def change_password():
    data = request.get_json()
    return ServiceProxy.forward_request(
        Config.AUTH_SERVICE_URL,
        '/api/auth/change-password',
        method='PUT',
        data=data,
        headers=dict(request.headers)
    )
