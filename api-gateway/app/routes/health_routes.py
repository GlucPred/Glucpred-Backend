from flask import Blueprint, jsonify
from app.utils import ServiceProxy
from config.settings import Config

bp = Blueprint('health', __name__)


@bp.route('/', methods=['GET'])
def root():
    """
    API Gateway Root
    ---
    tags:
      - Health
    responses:
      200:
        description: Información general de la API
        schema:
          type: object
          properties:
            message:
              type: string
            version:
              type: string
            documentation:
              type: string
            endpoints:
              type: object
    """
    return jsonify({
        'message': 'Glucpred API Gateway',
        'version': '1.0.0',
        'documentation': '/docs',
        'endpoints': {
            'authentication': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login'
            },
            'profile': {
                'create': 'POST /api/profile',
                'get': 'GET /api/profile/<user_id>',
                'update': 'PUT /api/profile/<user_id>'
            }
        }
    }), 200


@bp.route('/health', methods=['GET'])
def health():
    """
    Health Check del API Gateway
    ---
    tags:
      - Health
    responses:
      200:
        description: Estado del API Gateway
        schema:
          type: object
          properties:
            status:
              type: string
            service:
              type: string
            services:
              type: object
    """
    return jsonify({
        'status': 'healthy',
        'service': 'api-gateway',
        'services': {
            'auth': Config.AUTH_SERVICE_URL,
            'profile': Config.PROFILE_SERVICE_URL,
            'doctor_profile': Config.DOCTOR_PROFILE_SERVICE_URL,
            'doctor_patient': Config.DOCTOR_PATIENT_SERVICE_URL,
            'records': Config.RECORDS_SERVICE_URL,
            'alerts': Config.ALERTS_SERVICE_URL,
            'analysis': Config.ANALYSIS_SERVICE_URL,
        }
    }), 200


@bp.route('/api/auth/health', methods=['GET'])
def auth_health():
    """
    Health Check del Authentication Service
    ---
    tags:
      - Health
    responses:
      200:
        description: Estado del servicio de autenticación
      503:
        description: Servicio no disponible
    """
    return ServiceProxy.forward_request(
        Config.AUTH_SERVICE_URL,
        '/api/auth/health',
        method='GET'
    )


@bp.route('/api/profile/health', methods=['GET'])
def profile_health():
    """
    Health Check del Profile Service
    ---
    tags:
      - Health
    responses:
      200:
        description: Estado del servicio de perfiles
      503:
        description: Servicio no disponible
    """
    return ServiceProxy.forward_request(
        Config.PROFILE_SERVICE_URL,
        '/api/profile/health',
        method='GET'
    )


@bp.route('/api/doctor-profile/health', methods=['GET'])
def doctor_profile_health():
    return ServiceProxy.forward_request(
        Config.DOCTOR_PROFILE_SERVICE_URL,
        '/api/profile/medico/health',
        method='GET'
    )


@bp.route('/api/doctor-patient/health', methods=['GET'])
def doctor_patient_health():
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        '/api/doctor-patient/health',
        method='GET'
    )


@bp.route('/api/records/health', methods=['GET'])
def records_health():
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        '/api/records/health',
        method='GET'
    )


@bp.route('/api/alerts/health', methods=['GET'])
def alerts_health():
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        '/health',
        method='GET'
    )


@bp.route('/api/analysis/health', methods=['GET'])
def analysis_health():
    return ServiceProxy.forward_request(
        Config.ANALYSIS_SERVICE_URL,
        '/api/analysis/health',
        method='GET'
    )
