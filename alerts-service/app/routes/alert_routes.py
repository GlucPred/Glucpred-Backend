from flask import Blueprint, request, jsonify
from app.middleware.auth_middleware import token_required, doctor_required
from app.services.alert_service import AlertService
from app.models.fcm_token import FcmToken
from app.extensions import db
import requests
import os

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

@bp.route('/my-patients', methods=['GET'])
@token_required
@doctor_required
def get_all_my_patients_alerts():
    """
    Médicos pueden ver todas las alertas de todos sus pacientes asignados.
    
    Query params: type, severity, limit, offset
    """
    from config.settings import Config
    
    doctor_user_id = request.user_id
    
    # Obtener lista de pacientes asignados del doctor-patient-service
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        headers = {'Authorization': f'Bearer {token}'}
        
        # Llamar al doctor-patient-service para obtener los patient_ids
        response = requests.get(
            f'http://doctor-patient-service:8084/api/doctor-patient/my-patients',
            headers=headers,
            timeout=5
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'No se pudieron obtener los pacientes asignados'}), 500
        
        patients_data = response.json()
        patient_ids = [p['patient_user_id'] for p in patients_data.get('patients', [])]
        
        if not patient_ids:
            return jsonify({
                'alerts': [],
                'total': 0,
                'limit': 0,
                'offset': 0
            }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error al obtener pacientes'}), 500
    
    # Parsear filtros
    alert_type_param = request.args.get('type', 'todas')
    alert_type = None if alert_type_param == 'todas' else alert_type_param
    
    severity = request.args.get('severity')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Obtener alertas de todos los pacientes
    all_alerts = []
    for patient_id in patient_ids:
        alerts, _ = AlertService.get_user_alerts(
            user_id=patient_id,
            alert_type=alert_type,
            severity=severity,
            limit=None,  # Sin límite para obtener todas
            offset=0
        )
        all_alerts.extend(alerts)
    
    # Ordenar por fecha de creación (más recientes primero)
    all_alerts.sort(key=lambda x: x.created_at, reverse=True)
    
    # Aplicar paginación
    total = len(all_alerts)
    paginated_alerts = all_alerts[offset:offset + limit]
    
    # Obtener información de pacientes (nombres) del authentication-service
    try:
        auth_response = requests.get(
            'http://authentication-service:8081/api/auth/users',
            headers={
                **headers,
                'X-Internal-Api-Key': os.getenv('INTERNAL_API_KEY', 'glucpred-internal-key-change-in-production')
            },
            timeout=5
        )
        
        if auth_response.status_code == 200:
            users = auth_response.json().get('users', [])
            users_map = {u['id']: u['nombre_completo'] for u in users}
        else:
            users_map = {}
    except:
        users_map = {}
    
    # Enriquecer alertas con nombre del paciente
    alerts_with_patient = []
    for alert in paginated_alerts:
        alert_dict = alert.to_dict()
        alert_dict['patient_name'] = users_map.get(alert.user_id, 'Desconocido')
        alert_dict['patient_id'] = alert.user_id
        alerts_with_patient.append(alert_dict)
    
    return jsonify({
        'alerts': alerts_with_patient,
        'total': total,
        'limit': limit,
        'offset': offset,
        'patients_count': len(patient_ids)
    }), 200


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


@bp.route('/fcm-token', methods=['POST'])
@token_required
def register_fcm_token():
    """
    Registra o actualiza el FCM token del dispositivo del usuario autenticado.

    Body:
        { "token": "<fcm_registration_token>", "platform": "android" }
    """
    user_id = request.user_id
    data = request.get_json()

    if not data or not data.get('token'):
        return jsonify({'error': 'El campo token es requerido'}), 400

    token = data['token'].strip()
    platform = data.get('platform', 'android')

    existing = FcmToken.query.filter_by(user_id=user_id).first()
    if existing:
        existing.token = token
        existing.platform = platform
    else:
        db.session.add(FcmToken(user_id=user_id, token=token, platform=platform))

    db.session.commit()
    return jsonify({'message': 'FCM token registrado correctamente'}), 200
