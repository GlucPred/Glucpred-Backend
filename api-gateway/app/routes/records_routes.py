from flask import Blueprint, request
from flasgger import swag_from
from app.utils.service_proxy import ServiceProxy
from config.settings import Config

bp = Blueprint('records', __name__, url_prefix='/api/records')


@bp.route('/', methods=['POST'])
def create_record():
    """Registrar nueva medición de glucosa desde CGM
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - glucose_value
          properties:
            glucose_value:
              type: number
              example: 105.5
              description: Valor de glucosa en mg/dL desde el CGM
            measurement_time:
              type: string
              format: date-time
              example: "2025-11-16T14:30:00Z"
              description: Fecha y hora de la medición del CGM (opcional, por defecto ahora)
    responses:
      201:
        description: Registro creado exitosamente
      400:
        description: Error en los datos
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        '/api/records/',
        flask_request=request
    )


@bp.route('/latest', methods=['GET'])
def get_latest():
    """Obtener última medición de glucosa del usuario autenticado
    ---
    tags:
      - Records
    security:
      - Bearer: []
    responses:
      200:
        description: Última medición de glucosa
      404:
        description: No se encontraron registros
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        '/api/records/latest',
        flask_request=request
    )


@bp.route('/user/<int:user_id>/latest', methods=['GET'])
def get_latest_for_user(user_id):
    """Obtener última medición de un paciente específico
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: ID del usuario/paciente
    responses:
      200:
        description: Última medición de glucosa
      404:
        description: No se encontraron registros
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        f'/api/records/user/{user_id}/latest',
        flask_request=request
    )


@bp.route('/trend', methods=['GET'])
def get_trend():
    """Obtener tendencia de glucosa del usuario autenticado
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: query
        name: hours
        type: integer
        default: 12
        description: Número de horas hacia atrás (1-720)
    responses:
      200:
        description: Lista de mediciones en el período
        schema:
          type: object
          properties:
            user_id:
              type: integer
            period_hours:
              type: integer
            records:
              type: array
              items:
                type: object
            total:
              type: integer
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        '/api/records/trend',
        flask_request=request
    )


@bp.route('/user/<int:user_id>/trend', methods=['GET'])
def get_trend_for_user(user_id):
    """Obtener tendencia de glucosa de un paciente específico
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: ID del usuario/paciente
      - in: query
        name: hours
        type: integer
        default: 12
        description: Número de horas hacia atrás (1-720)
    responses:
      200:
        description: Lista de mediciones en el período
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        f'/api/records/user/{user_id}/trend',
        flask_request=request
    )


@bp.route('/history', methods=['GET'])
def get_history():
    """Obtener historial paginado de mediciones del usuario autenticado
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: query
        name: limit
        type: integer
        default: 100
        description: Registros por página (máx 500)
      - in: query
        name: offset
        type: integer
        default: 0
        description: Desplazamiento para paginación
      - in: query
        name: start_date
        type: string
        format: date-time
        description: Fecha inicial (ISO 8601)
      - in: query
        name: end_date
        type: string
        format: date-time
        description: Fecha final (ISO 8601)
    responses:
      200:
        description: Historial paginado
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        '/api/records/history',
        flask_request=request
    )


@bp.route('/user/<int:user_id>/history', methods=['GET'])
def get_history_for_user(user_id):
    """Obtener historial paginado de un paciente específico
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: query
        name: limit
        type: integer
        default: 100
      - in: query
        name: offset
        type: integer
        default: 0
      - in: query
        name: start_date
        type: string
        format: date-time
      - in: query
        name: end_date
        type: string
        format: date-time
    responses:
      200:
        description: Historial paginado
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        f'/api/records/user/{user_id}/history',
        flask_request=request
    )


@bp.route('/my-patients', methods=['GET'])
def get_all_my_patients_records():
    """Obtener registros de todos los pacientes asignados (solo médicos)
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        description: Número de registros a devolver
        default: 100
      - name: offset
        in: query
        type: integer
        description: Desplazamiento para paginación
        default: 0
      - name: start_date
        in: query
        type: string
        description: Fecha de inicio (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        description: Fecha de fin (YYYY-MM-DD)
    responses:
      200:
        description: Lista de registros de todos los pacientes asignados
      403:
        description: Acceso denegado
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        '/api/records/my-patients',
        flask_request=request
    )


@bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Obtener estadísticas de glucosa del usuario autenticado
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: query
        name: hours
        type: integer
        default: 24
        description: Período en horas (1-720)
    responses:
      200:
        description: Estadísticas calculadas
        schema:
          type: object
          properties:
            period_hours:
              type: integer
            total_readings:
              type: integer
            average:
              type: number
            min:
              type: number
            max:
              type: number
            classifications:
              type: object
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        '/api/records/statistics',
        flask_request=request
    )


@bp.route('/user/<int:user_id>/statistics', methods=['GET'])
def get_statistics_for_user(user_id):
    """Obtener estadísticas de glucosa de un paciente específico
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: query
        name: hours
        type: integer
        default: 24
    responses:
      200:
        description: Estadísticas calculadas
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        f'/api/records/user/{user_id}/statistics',
        flask_request=request
    )


@bp.route('/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """Eliminar un registro de glucosa propio
    ---
    tags:
      - Records
    security:
      - Bearer: []
    parameters:
      - in: path
        name: record_id
        type: integer
        required: true
        description: ID del registro a eliminar
    responses:
      200:
        description: Registro eliminado exitosamente
      404:
        description: Registro no encontrado
    """
    return ServiceProxy.forward_request(
        Config.RECORDS_SERVICE_URL,
        f'/api/records/{record_id}',
        flask_request=request
    )
