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
        data=request.get_json(),
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
        data=request.get_json(),
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


# ==================== PATIENT SUMMARY ENDPOINTS ====================

@bp.route('/available-patients', methods=['GET'])
def get_available_patients():
    """Obtener pacientes disponibles (sin médico asignado)
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    description: |
      Obtiene lista completa de pacientes que NO tienen médico asignado con:
      - Información completa del perfil (edad, peso, altura, medicamentos, etc.)
      - Última medición de glucosa
      - Cantidad de alertas críticas en últimas 24 horas
      
      Este endpoint se usa para que un médico pueda ver y seleccionar pacientes disponibles para asignar.
    responses:
      200:
        description: Lista de pacientes disponibles
        schema:
          type: object
          properties:
            available_patients:
              type: array
              items:
                type: object
                properties:
                  patient_user_id:
                    type: integer
                  nombre_completo:
                    type: string
                  edad:
                    type: integer
                  peso:
                    type: number
                  altura:
                    type: number
                  genero:
                    type: string
                  medicamentos:
                    type: string
                  antecedentes:
                    type: string
                  fecha_diagnostico:
                    type: string
                  ultima_glucosa:
                    type: number
                  alertas_count:
                    type: integer
            total:
              type: integer
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        '/api/doctor-patient/available-patients',
        method='GET',
        headers=request.headers
    )


@bp.route('/patients-summary', methods=['GET'])
def get_patients_summary():
    """Obtener resumen de todos los pacientes del médico
    ---
    tags:
      - Doctor-Patient
    security:
      - Bearer: []
    description: |
      Obtiene resumen completo de todos los pacientes asignados al médico con:
      - Información básica del perfil
      - Última medición de glucosa
      - Estado actual (Estable/Moderada/Critica)
      - Cantidad de alertas críticas en últimas 24 horas
      
      Este endpoint se usa en la pantalla principal del médico.
    responses:
      200:
        description: Lista de pacientes con resumen
        schema:
          type: object
          properties:
            doctor_user_id:
              type: integer
            patients:
              type: array
              items:
                type: object
                properties:
                  patient_user_id:
                    type: integer
                  nombre_completo:
                    type: string
                  edad:
                    type: integer
                  ultima_glucosa:
                    type: number
                  estado:
                    type: string
                    enum: ['Estable', 'Moderada', 'Critica', 'Desconocido']
                  alertas_count:
                    type: integer
                  fecha_asignacion:
                    type: string
                    format: date-time
            total:
              type: integer
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        '/api/doctor-patient/patients-summary',
        method='GET',
        headers=request.headers
    )


@bp.route('/patient/<int:patient_user_id>/detail', methods=['GET'])
def get_patient_detail(patient_user_id):
    """Obtener detalle completo de un paciente
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
        name: period
        type: string
        enum: ['day', 'week', 'month']
        default: 'day'
        description: Periodo para estadísticas y gráfica
    description: |
      Obtiene información completa del paciente para la vista detallada del médico:
      - Perfil completo del paciente
      - Estadísticas de glucosa (promedio, % en rango)
      - Tendencia de glucosa para gráfica
      - Última observación médica del doctor
    responses:
      200:
        description: Detalle completo del paciente
        schema:
          type: object
          properties:
            patient_user_id:
              type: integer
            profile:
              type: object
            glucose_stats:
              type: object
            glucose_trend:
              type: array
              items:
                type: object
            latest_observation:
              type: object
              nullable: true
      403:
        description: No autorizado o sin acceso a este paciente
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        f'/api/doctor-patient/patient/{patient_user_id}/detail',
        method='GET',
        params=request.args,
        headers=request.headers
    )


# ==================== MEDICAL OBSERVATIONS ENDPOINTS ====================

@bp.route('/patient/<int:patient_user_id>/observations', methods=['POST'])
def create_observation(patient_user_id):
    """Crear observación médica para un paciente
    ---
    tags:
      - Medical Observations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: patient_user_id
        type: integer
        required: true
        description: ID del paciente
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - observation_text
          properties:
            observation_text:
              type: string
              example: "Control estable, mantener dosis actual."
    responses:
      201:
        description: Observación creada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            observation:
              type: object
      400:
        description: Error en la petición
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        f'/api/doctor-patient/patient/{patient_user_id}/observations',
        method='POST',
        data=request.get_json(),
        headers=request.headers
    )


@bp.route('/patient/<int:patient_user_id>/observations', methods=['GET'])
def get_patient_observations(patient_user_id):
    """Obtener observaciones médicas de un paciente
    ---
    tags:
      - Medical Observations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: patient_user_id
        type: integer
        required: true
        description: ID del paciente
      - in: query
        name: limit
        type: integer
        default: 100
        description: Número máximo de resultados
      - in: query
        name: offset
        type: integer
        default: 0
        description: Desplazamiento para paginación
    responses:
      200:
        description: Lista de observaciones médicas
        schema:
          type: object
          properties:
            patient_user_id:
              type: integer
            observations:
              type: array
              items:
                type: object
            total:
              type: integer
            limit:
              type: integer
            offset:
              type: integer
      403:
        description: No autorizado (solo médicos)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        f'/api/doctor-patient/patient/{patient_user_id}/observations',
        method='GET',
        params=request.args,
        headers=request.headers
    )


@bp.route('/observations/<int:observation_id>', methods=['PUT'])
def update_observation(observation_id):
    """Actualizar observación médica
    ---
    tags:
      - Medical Observations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: observation_id
        type: integer
        required: true
        description: ID de la observación
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - observation_text
          properties:
            observation_text:
              type: string
              example: "Ajuste de medicación, programar seguimiento."
    responses:
      200:
        description: Observación actualizada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            observation:
              type: object
      400:
        description: Error en la petición
      403:
        description: No autorizado (solo el médico que creó la observación)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        f'/api/doctor-patient/observations/{observation_id}',
        method='PUT',
        data=request.get_json(),
        headers=request.headers
    )


@bp.route('/observations/<int:observation_id>', methods=['DELETE'])
def delete_observation(observation_id):
    """Eliminar observación médica
    ---
    tags:
      - Medical Observations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: observation_id
        type: integer
        required: true
        description: ID de la observación
    responses:
      200:
        description: Observación eliminada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Error en la petición
      403:
        description: No autorizado (solo el médico que creó la observación)
    """
    return ServiceProxy.forward_request(
        Config.DOCTOR_PATIENT_SERVICE_URL,
        f'/api/doctor-patient/observations/{observation_id}',
        method='DELETE',
        headers=request.headers
    )

