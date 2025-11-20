from flask import Blueprint, request, jsonify
from app.middleware.auth_middleware import token_required, doctor_required
from app.services.alert_service import AlertService

bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@bp.route('/', methods=['GET'])
@token_required
def get_alerts():
    """
    Obtiene las alertas del usuario autenticado con filtros opcionales.
    
    Query params:
    - type: 'critica', 'recordatorio', o 'todas' (default: 'todas')
    - severity: 'critico', 'advertencia', 'info' (opcional)
    - is_read: 'true', 'false' (opcional)
    - limit: número de resultados (default: 100)
    - offset: desplazamiento (default: 0)
    """
    user_id = request.user_id
    
    # Parsear filtros
    alert_type_param = request.args.get('type', 'todas')
    alert_type = None if alert_type_param == 'todas' else alert_type_param
    
    severity = request.args.get('severity')
    
    is_read_param = request.args.get('is_read')
    is_read = None
    if is_read_param == 'true':
        is_read = True
    elif is_read_param == 'false':
        is_read = False
    
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Obtener alertas
    alerts, total = AlertService.get_user_alerts(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        is_read=is_read,
        limit=limit,
        offset=offset
    )
    
    return jsonify({
        'alerts': [alert.to_dict() for alert in alerts],
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': (offset + len(alerts)) < total
    }), 200

@bp.route('/unread-count', methods=['GET'])
@token_required
def get_unread_count():
    """
    Obtiene el número de alertas no leídas.
    """
    user_id = request.user_id
    count = AlertService.get_unread_count(user_id)
    
    return jsonify({
        'unread_count': count
    }), 200

@bp.route('/critical-count', methods=['GET'])
@token_required
def get_critical_count():
    """
    Obtiene el número de alertas críticas en las últimas X horas.
    
    Query params:
    - hours: número de horas (default: 24)
    """
    user_id = request.user_id
    hours = int(request.args.get('hours', 24))
    
    count = AlertService.get_critical_alerts_count(user_id, hours)
    
    return jsonify({
        'critical_count': count,
        'period_hours': hours
    }), 200

@bp.route('/<int:alert_id>/read', methods=['PUT'])
@token_required
def mark_alert_as_read(alert_id):
    """
    Marca una alerta como leída.
    """
    user_id = request.user_id
    
    alert = AlertService.mark_as_read(alert_id, user_id)
    
    if not alert:
        return jsonify({'error': 'Alerta no encontrada'}), 404
    
    return jsonify({
        'message': 'Alerta marcada como leída',
        'alert': alert.to_dict()
    }), 200

@bp.route('/read-all', methods=['PUT'])
@token_required
def mark_all_as_read():
    """
    Marca todas las alertas como leídas.
    """
    user_id = request.user_id
    
    count = AlertService.mark_all_as_read(user_id)
    
    return jsonify({
        'message': f'{count} alertas marcadas como leídas',
        'count': count
    }), 200

@bp.route('/<int:alert_id>', methods=['DELETE'])
@token_required
def dismiss_alert(alert_id):
    """
    Descarta/elimina una alerta.
    """
    user_id = request.user_id
    
    alert = AlertService.dismiss_alert(alert_id, user_id)
    
    if not alert:
        return jsonify({'error': 'Alerta no encontrada'}), 404
    
    return jsonify({
        'message': 'Alerta descartada exitosamente'
    }), 200

@bp.route('/reminder', methods=['POST'])
@token_required
def create_reminder():
    """
    Crea un recordatorio manual.
    
    Body:
    {
        "title": "Tomar medicación",
        "message": "Recuerda tomar tu insulina"
    }
    """
    user_id = request.user_id
    data = request.get_json()
    
    if not data or 'title' not in data or 'message' not in data:
        return jsonify({'error': 'Faltan campos requeridos: title, message'}), 400
    
    alert = AlertService.create_reminder(
        user_id=user_id,
        title=data['title'],
        message=data['message']
    )
    
    return jsonify({
        'message': 'Recordatorio creado exitosamente',
        'alert': alert.to_dict()
    }), 201

# ========== ENDPOINTS PARA MÉDICOS ==========

@bp.route('/patient/<int:patient_id>', methods=['GET'])
@token_required
@doctor_required
def get_patient_alerts(patient_id):
    """
    Médicos pueden ver las alertas de sus pacientes.
    
    Query params: type, severity, limit, offset (igual que GET /)
    """
    # Parsear filtros
    alert_type_param = request.args.get('type', 'todas')
    alert_type = None if alert_type_param == 'todas' else alert_type_param
    
    severity = request.args.get('severity')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Obtener alertas del paciente
    alerts, total = AlertService.get_user_alerts(
        user_id=patient_id,
        alert_type=alert_type,
        severity=severity,
        limit=limit,
        offset=offset
    )
    
    return jsonify({
        'patient_id': patient_id,
        'alerts': [alert.to_dict() for alert in alerts],
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200

@bp.route('/patient/<int:patient_id>/critical-count', methods=['GET'])
@token_required
@doctor_required
def get_patient_critical_count(patient_id):
    """
    Médicos pueden ver el número de alertas críticas de sus pacientes.
    """
    hours = int(request.args.get('hours', 24))
    count = AlertService.get_critical_alerts_count(patient_id, hours)
    
    return jsonify({
        'patient_id': patient_id,
        'critical_count': count,
        'period_hours': hours
    }), 200
