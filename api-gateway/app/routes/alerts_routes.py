from flask import Blueprint, request
from app.utils.service_proxy import ServiceProxy
from config.settings import Config

bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@bp.route('/', methods=['GET'])
def get_alerts():
    """
    Obtener alertas del usuario autenticado
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - name: type
        in: query
        type: string
        enum: [todas, critica, recordatorio]
        default: todas
        description: Filtrar por tipo de alerta
      - name: severity
        in: query
        type: string
        enum: [critico, advertencia, info]
        description: Filtrar por severidad
      - name: is_read
        in: query
        type: string
        enum: [true, false]
        description: Filtrar por leídas/no leídas
      - name: limit
        in: query
        type: integer
        default: 100
        description: Número de resultados
      - name: offset
        in: query
        type: integer
        default: 0
        description: Desplazamiento para paginación
    responses:
      200:
        description: Lista de alertas
        schema:
          type: object
          properties:
            alerts:
              type: array
              items:
                type: object
            total:
              type: integer
            limit:
              type: integer
            offset:
              type: integer
      401:
        description: Token inválido o faltante
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        '/api/alerts/',
        flask_request=request
    )

@bp.route('/unread-count', methods=['GET'])
def get_unread_count():
    """
    Obtener número de alertas no leídas
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    responses:
      200:
        description: Contador de alertas no leídas
        schema:
          type: object
          properties:
            unread_count:
              type: integer
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        '/api/alerts/unread-count',
        flask_request=request
    )

@bp.route('/critical-count', methods=['GET'])
def get_critical_count():
    """
    Obtener número de alertas críticas en las últimas X horas
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - name: hours
        in: query
        type: integer
        default: 24
        description: Período en horas
    responses:
      200:
        description: Contador de alertas críticas
        schema:
          type: object
          properties:
            critical_count:
              type: integer
            period_hours:
              type: integer
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        '/api/alerts/critical-count',
        flask_request=request
    )

@bp.route('/<int:alert_id>/read', methods=['PUT'])
def mark_alert_as_read(alert_id):
    """
    Marcar alerta como leída
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - name: alert_id
        in: path
        type: integer
        required: true
        description: ID de la alerta
    responses:
      200:
        description: Alerta marcada como leída
      404:
        description: Alerta no encontrada
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        f'/api/alerts/{alert_id}/read',
        flask_request=request
    )

@bp.route('/read-all', methods=['PUT'])
def mark_all_as_read():
    """
    Marcar todas las alertas como leídas
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    responses:
      200:
        description: Todas las alertas marcadas como leídas
        schema:
          type: object
          properties:
            message:
              type: string
            count:
              type: integer
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        '/api/alerts/read-all',
        flask_request=request
    )

@bp.route('/<int:alert_id>', methods=['DELETE'])
def dismiss_alert(alert_id):
    """
    Descartar/eliminar alerta
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - name: alert_id
        in: path
        type: integer
        required: true
        description: ID de la alerta
    responses:
      200:
        description: Alerta descartada
      404:
        description: Alerta no encontrada
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        f'/api/alerts/{alert_id}',
        flask_request=request
    )

@bp.route('/reminder', methods=['POST'])
def create_reminder():
    """
    Crear recordatorio manual
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - message
          properties:
            title:
              type: string
              example: "Tomar medicación"
            message:
              type: string
              example: "Recuerda tomar tu insulina"
    responses:
      201:
        description: Recordatorio creado
      400:
        description: Datos inválidos
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        '/api/alerts/reminder',
        flask_request=request
    )

# ========== ENDPOINTS PARA MÉDICOS ==========

@bp.route('/my-patients', methods=['GET'])
def get_my_patients_alerts():
    """
    Ver todas las alertas de todos los pacientes asignados al médico
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: query
        name: type
        type: string
        description: Tipo de alerta (todas, hipoglucemia, hiperglucemia, tendencia, recordatorio)
      - in: query
        name: severity
        type: string
        description: Severidad (critico, advertencia)
      - in: query
        name: limit
        type: integer
        description: Número de alertas a retornar
      - in: query
        name: offset
        type: integer
        description: Offset para paginación
    responses:
      200:
        description: Lista de alertas de todos los pacientes
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        '/api/alerts/my-patients',
        flask_request=request
    )

@bp.route('/patient/<int:patient_id>', methods=['GET'])
def get_patient_alerts(patient_id):
    """
    Ver alertas de un paciente (solo médicos)
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - name: patient_id
        in: path
        type: integer
        required: true
        description: ID del paciente
      - name: type
        in: query
        type: string
        enum: [todas, critica, recordatorio]
        default: todas
      - name: severity
        in: query
        type: string
        enum: [critico, advertencia, info]
      - name: limit
        in: query
        type: integer
        default: 100
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Alertas del paciente
      403:
        description: Acceso denegado (no es médico)
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        f'/api/alerts/patient/{patient_id}',
        flask_request=request
    )

@bp.route('/patient/<int:patient_id>/critical-count', methods=['GET'])
def get_patient_critical_count(patient_id):
    """
    Ver número de alertas críticas de un paciente (solo médicos)
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - name: patient_id
        in: path
        type: integer
        required: true
        description: ID del paciente
      - name: hours
        in: query
        type: integer
        default: 24
        description: Período en horas
    responses:
      200:
        description: Contador de alertas críticas del paciente
      403:
        description: Acceso denegado (no es médico)
    """
    return ServiceProxy.forward_request(
        Config.ALERTS_SERVICE_URL,
        f'/api/alerts/patient/{patient_id}/critical-count',
        flask_request=request
    )
