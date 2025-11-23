from flask import Blueprint, request, jsonify
from app.services import RecordsService
from app.middleware.auth_middleware import token_required
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('records', __name__, url_prefix='/api/records')


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'service': 'records-service',
        'status': 'healthy'
    }), 200


@bp.route('/', methods=['POST'])
@token_required
def create_record(current_user_id, user_role):
    """
    Create a new glucose measurement record from CGM
    
    Body:
        {
            "glucose_value": 105.5,
            "measurement_time": "2025-11-16T14:30:00Z"  # Optional, defaults to now
        }
    """
    data = request.get_json()
    
    if not data or 'glucose_value' not in data:
        return jsonify({'error': 'glucose_value es requerido'}), 400
    
    try:
        glucose_value = float(data['glucose_value'])
    except (ValueError, TypeError):
        return jsonify({'error': 'glucose_value debe ser un número'}), 400
    
    # Patients can only create records for themselves
    # Doctors can create records for their patients (we trust the token for now)
    user_id = current_user_id
    
    result, error = RecordsService.create_record(
        user_id=user_id,
        glucose_value=glucose_value,
        measurement_time=data.get('measurement_time')
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Registro de glucosa creado exitosamente',
        'record': result
    }), 201


@bp.route('/latest', methods=['GET'])
@token_required
def get_latest(current_user_id, user_role):
    """Get the most recent glucose record for authenticated user"""
    result, error = RecordsService.get_latest_record(current_user_id)
    
    if error:
        return jsonify({'error': error}), 404
    
    return jsonify(result), 200


@bp.route('/user/<int:user_id>/latest', methods=['GET'])
@token_required
def get_latest_for_user(current_user_id, user_role, user_id):
    """Get the most recent glucose record for a specific user (doctors only)"""
    # For now, anyone authenticated can query any user
    # TODO: Add doctor-patient relationship validation
    
    result, error = RecordsService.get_latest_record(user_id)
    
    if error:
        return jsonify({'error': error}), 404
    
    return jsonify(result), 200


@bp.route('/trend', methods=['GET'])
@token_required
def get_trend(current_user_id, user_role):
    """
    Get glucose trend for authenticated user
    
    Query params:
        hours: Number of hours to look back (default: 12)
    """
    hours = request.args.get('hours', 12, type=int)
    
    if hours < 1 or hours > 720:  # Max 30 days
        return jsonify({'error': 'hours debe estar entre 1 y 720'}), 400
    
    result, error = RecordsService.get_records_by_timerange(current_user_id, hours)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'user_id': current_user_id,
        'period_hours': hours,
        'records': result,
        'total': len(result)
    }), 200


@bp.route('/user/<int:user_id>/trend', methods=['GET'])
@token_required
def get_trend_for_user(current_user_id, user_role, user_id):
    """Get glucose trend for a specific user (doctors can view their patients)"""
    hours = request.args.get('hours', 12, type=int)
    
    if hours < 1 or hours > 720:
        return jsonify({'error': 'hours debe estar entre 1 y 720'}), 400
    
    result, error = RecordsService.get_records_by_timerange(user_id, hours)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'user_id': user_id,
        'period_hours': hours,
        'records': result,
        'total': len(result)
    }), 200


@bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user_id, user_role):
    """
    Get paginated glucose history for authenticated user
    
    Query params:
        limit: Records per page (default: 100, max: 500)
        offset: Page offset (default: 0)
        start_date: ISO 8601 datetime (optional)
        end_date: ISO 8601 datetime (optional)
    """
    limit = min(request.args.get('limit', 100, type=int), 500)
    offset = request.args.get('offset', 0, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result, error = RecordsService.get_records_history(
        user_id=current_user_id,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(result), 200


@bp.route('/user/<int:user_id>/history', methods=['GET'])
@token_required
def get_history_for_user(current_user_id, user_role, user_id):
    """Get paginated glucose history for a specific user"""
    limit = min(request.args.get('limit', 100, type=int), 500)
    offset = request.args.get('offset', 0, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result, error = RecordsService.get_records_history(
        user_id=user_id,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(result), 200


@bp.route('/my-patients', methods=['GET'])
@token_required
def get_all_my_patients_records(current_user_id, user_role):
    """
    Get records from all assigned patients (for doctors only)
    
    Query params:
    - limit: número de registros (default: 100)
    - offset: desplazamiento (default: 0)
    - start_date: fecha inicio (opcional)
    - end_date: fecha fin (opcional)
    """
    import requests
    from config.settings import Config
    
    if user_role != 'Medico':
        return jsonify({'error': 'Acceso denegado. Solo médicos pueden usar este endpoint'}), 403
    
    # Obtener lista de pacientes asignados
    try:
        # Extraer el token del header
        auth_header = request.headers.get('Authorization', '')
        
        response = requests.get(
            f'http://doctor-patient-service:8084/api/doctor-patient/my-patients',
            headers={'Authorization': auth_header}
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Error al obtener lista de pacientes'}), 500
            
        patients_data = response.json()
        patient_ids = [p['patient_user_id'] for p in patients_data.get('patients', [])]
        
        if not patient_ids:
            return jsonify({
                'records': [],
                'total': 0,
                'limit': request.args.get('limit', 100, type=int),
                'offset': request.args.get('offset', 0, type=int)
            }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener pacientes asignados: {str(e)}")
        return jsonify({'error': 'Error al conectar con el servicio de pacientes'}), 500
    
    # Obtener registros de todos los pacientes
    limit = min(request.args.get('limit', 100, type=int), 500)
    offset = request.args.get('offset', 0, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    all_records = []
    
    for patient_id in patient_ids:
        result, error = RecordsService.get_records_history(
            user_id=patient_id,
            limit=limit,
            offset=0,
            start_date=start_date,
            end_date=end_date
        )
        
        if not error and result.get('records'):
            # Agregar patient_id a cada registro
            for record in result['records']:
                record['patient_id'] = patient_id
            all_records.extend(result['records'])
    
    # Ordenar por fecha descendente
    all_records.sort(key=lambda x: x.get('measurement_time', ''), reverse=True)
    
    # Aplicar paginación
    total = len(all_records)
    paginated_records = all_records[offset:offset + limit]
    
    return jsonify({
        'records': paginated_records,
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200


@bp.route('/statistics', methods=['GET'])
@token_required
def get_statistics(current_user_id, user_role):
    """
    Get glucose statistics for authenticated user
    
    Query params:
        hours: Time period in hours (default: 24)
    """
    hours = request.args.get('hours', 24, type=int)
    
    if hours < 1 or hours > 720:
        return jsonify({'error': 'hours debe estar entre 1 y 720'}), 400
    
    result, error = RecordsService.get_statistics(current_user_id, hours)
    
    if error:
        return jsonify({'error': error}), 404
    
    return jsonify(result), 200


@bp.route('/user/<int:user_id>/statistics', methods=['GET'])
@token_required
def get_statistics_for_user(current_user_id, user_role, user_id):
    """Get glucose statistics for a specific user"""
    hours = request.args.get('hours', 24, type=int)
    
    if hours < 1 or hours > 720:
        return jsonify({'error': 'hours debe estar entre 1 y 720'}), 400
    
    result, error = RecordsService.get_statistics(user_id, hours)
    
    if error:
        return jsonify({'error': error}), 404
    
    return jsonify(result), 200


@bp.route('/<int:record_id>', methods=['DELETE'])
@token_required
def delete_record(current_user_id, user_role, record_id):
    """Delete a glucose record (only own records)"""
    success, error = RecordsService.delete_record(record_id, current_user_id)
    
    if error:
        return jsonify({'error': error}), 404
    
    return jsonify({'message': 'Registro eliminado exitosamente'}), 200
