from flask import Blueprint, request
from flasgger import swag_from
from app.utils.service_proxy import ServiceProxy
from config.settings import Config

bp = Blueprint('doctor_patient', __name__, url_prefix='/api/doctor-patient')


@bp.route('/assign', methods=['POST'])
def assign_patient():
    """Asignar paciente a médico
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - patient_user_id
          properties:
            patient_user_id:
              type: integer
              example: 123
    responses:
      201:
        description: Paciente asignado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            relation:
              type: object
      400:
        description: Error en la petición
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        '/api/doctor-patient/assign',
        method='POST',
        json=request.get_json(),
        headers=request.headers
    )


@bp.route('/deactivate', methods=['POST'])
def deactivate_patient():
    """Desactivar relación médico-paciente
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - patient_user_id
          properties:
            patient_user_id:
              type: integer
              example: 123
    responses:
      200:
        description: Relación desactivada exitosamente
      400:
        description: Error en la petición
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        '/api/doctor-patient/deactivate',
        method='POST',
        json=request.get_json(),
        headers=request.headers
    )


@bp.route('/my-patients', methods=['GET'])
def get_my_patients():
    """Obtener pacientes del médico autenticado
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    parameters:
      - in: query
        name: estado
        type: string
        enum: ['A', 'I']
        description: Filtrar por estado (A=Activo, I=Inactivo)
    responses:
      200:
        description: Lista de pacientes del médico
        schema:
          type: object
          properties:
            doctor_user_id:
              type: integer
            patients:
              type: array
              items:
                type: object
            total:
              type: integer
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        '/api/doctor-patient/my-patients',
        method='GET',
        params=request.args,
        headers=request.headers
    )


@bp.route('/patient/<int:patient_user_id>/doctors', methods=['GET'])
def get_patient_doctors(patient_user_id):
    """Obtener médicos de un paciente
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    parameters:
      - in: path
        name: patient_user_id
        type: integer
        required: true
        description: ID del paciente
      - in: query
        name: estado
        type: string
        enum: ['A', 'I']
        description: Filtrar por estado (A=Activo, I=Inactivo)
    responses:
      200:
        description: Lista de médicos del paciente
        schema:
          type: object
          properties:
            patient_user_id:
              type: integer
            doctors:
              type: array
              items:
                type: object
            total:
              type: integer
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        f'/api/doctor-patient/patient/{patient_user_id}/doctors',
        method='GET',
        params=request.args,
        headers=request.headers
    )


@bp.route('/patient/<int:patient_user_id>/availability', methods=['GET'])
def check_patient_availability(patient_user_id):
    """Verificar disponibilidad de un paciente
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    parameters:
      - in: path
        name: patient_user_id
        type: integer
        required: true
        description: ID del paciente
    responses:
      200:
        description: Estado de disponibilidad del paciente
        schema:
          type: object
          properties:
            available:
              type: boolean
            patient_user_id:
              type: integer
            assigned_to_doctor_id:
              type: integer
              nullable: true
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        f'/api/doctor-patient/patient/{patient_user_id}/availability',
        method='GET',
        headers=request.headers
    )


@bp.route('/unavailable-patients', methods=['GET'])
def get_unavailable_patients():
    """Obtener pacientes no disponibles (ya asignados a otros médicos)
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de pacientes no disponibles
        schema:
          type: object
          properties:
            unavailable_patients:
              type: array
              items:
                type: integer
            message:
              type: string
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        '/api/doctor-patient/unavailable-patients',
        method='GET',
        headers=request.headers
    )
