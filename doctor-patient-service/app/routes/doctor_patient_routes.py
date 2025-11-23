from flask import Blueprint, request, jsonify
from app.services import DoctorPatientService, MedicalObservationService, PatientSummaryService
from app.middleware.auth_middleware import doctor_required, token_required
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('doctor_patient', __name__, url_prefix='/api/doctor-patient')


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'service': 'doctor-patient-service',
        'status': 'healthy'
    }), 200


@bp.route('/assign', methods=['POST'])
@doctor_required
def assign_patient(current_user_id, user_role):
    """
    Assign a patient to the authenticated doctor
    
    Body:
        {
            "patient_user_id": 123
        }
    """
    data = request.get_json()
    
    if not data or 'patient_user_id' not in data:
        return jsonify({'error': 'patient_user_id es requerido'}), 400
    
    patient_user_id = data['patient_user_id']
    
    # current_user_id is the doctor (from JWT token)
    result, error = DoctorPatientService.assign_patient_to_doctor(
        doctor_user_id=current_user_id,
        patient_user_id=patient_user_id
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Paciente asignado exitosamente',
        'relation': result
    }), 201


@bp.route('/deactivate', methods=['POST'])
@doctor_required
def deactivate_patient(current_user_id, user_role):
    """
    Deactivate relationship with a patient
    
    Body:
        {
            "patient_user_id": 123
        }
    """
    data = request.get_json()
    
    if not data or 'patient_user_id' not in data:
        return jsonify({'error': 'patient_user_id es requerido'}), 400
    
    patient_user_id = data['patient_user_id']
    
    result, error = DoctorPatientService.deactivate_relation(
        doctor_user_id=current_user_id,
        patient_user_id=patient_user_id
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Relación desactivada exitosamente',
        'relation': result
    }), 200


@bp.route('/my-patients', methods=['GET'])
@doctor_required
def get_my_patients(current_user_id, user_role):
    """
    Get all patients assigned to the authenticated doctor
    
    Query params:
        - estado: 'A' (active) or 'I' (inactive) or empty (all)
    """
    estado = request.args.get('estado', None)
    
    result, error = DoctorPatientService.get_doctor_patients(
        doctor_user_id=current_user_id,
        estado=estado
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'doctor_user_id': current_user_id,
        'patients': result,
        'total': len(result)
    }), 200


@bp.route('/patient/<int:patient_user_id>/doctors', methods=['GET'])
@token_required
def get_patient_doctors(current_user_id, user_role, patient_user_id):
    """
    Get all doctors assigned to a patient
    
    Query params:
        - estado: 'A' (active) or 'I' (inactive) or empty (all)
    """
    estado = request.args.get('estado', None)
    
    result, error = DoctorPatientService.get_patient_doctors(
        patient_user_id=patient_user_id,
        estado=estado
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'patient_user_id': patient_user_id,
        'doctors': result,
        'total': len(result)
    }), 200


@bp.route('/patient/<int:patient_user_id>/availability', methods=['GET'])
@doctor_required
def check_patient_availability(current_user_id, user_role, patient_user_id):
    """
    Check if a patient is available to be assigned
    """
    result, error = DoctorPatientService.check_patient_availability(patient_user_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(result), 200


@bp.route('/unavailable-patients', methods=['GET'])
@doctor_required
def get_unavailable_patients(current_user_id, user_role):
    """
    Get list of patients that are already actively assigned to other doctors
    """
    result, error = DoctorPatientService.get_all_patients_available_for_doctor(current_user_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(result), 200


# ==================== PATIENT SUMMARY ENDPOINTS ====================

@bp.route('/available-patients', methods=['GET'])
@doctor_required
def get_available_patients(current_user_id, user_role):
    """
    Obtener lista de pacientes disponibles (sin médico asignado) con información completa.
    Este endpoint se usa para que un médico pueda ver y seleccionar pacientes disponibles.
    
    Muestra:
    - Información completa del perfil
    - Última medición de glucosa
    - Cantidad de alertas críticas
    """
    # Obtener token del header para pasarlo a otros servicios
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token no proporcionado'}), 401
    
    auth_token = auth_header.replace('Bearer ', '')
    
    result, error = PatientSummaryService.get_available_patients(
        auth_token=auth_token
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'available_patients': result,
        'total': len(result)
    }), 200


@bp.route('/patients-summary', methods=['GET'])
@doctor_required
def get_patients_summary(current_user_id, user_role):
    """
    Obtener resumen de todos los pacientes del doctor con:
    - Información básica del perfil
    - Última medición de glucosa
    - Estado actual (Estable/Moderada/Critica)
    - Cantidad de alertas en últimas 24h
    
    Este endpoint se usa en la pantalla principal del doctor.
    """
    # Obtener token del header para pasarlo a otros servicios
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token no proporcionado'}), 401
    
    auth_token = auth_header.replace('Bearer ', '')
    
    result, error = PatientSummaryService.get_patients_summary(
        doctor_user_id=current_user_id,
        auth_token=auth_token
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'doctor_user_id': current_user_id,
        'patients': result,
        'total': len(result)
    }), 200


@bp.route('/patient/<int:patient_user_id>/detail', methods=['GET'])
@doctor_required
def get_patient_detail(current_user_id, user_role, patient_user_id):
    """
    Obtener detalle completo de un paciente para la vista de doctor:
    - Perfil completo
    - Estadísticas de glucosa (promedio diario, % en rango)
    - Tendencia de glucosa (para gráfica)
    - Última observación médica
    
    Query params:
        - period: 'day' (default), 'week', 'month'
    """
    period = request.args.get('period', 'day')
    
    # Obtener token del header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token no proporcionado'}), 401
    
    auth_token = auth_header.replace('Bearer ', '')
    
    result, error = PatientSummaryService.get_patient_detail(
        patient_user_id=patient_user_id,
        doctor_user_id=current_user_id,
        auth_token=auth_token,
        period=period
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(result), 200


# ==================== MEDICAL OBSERVATIONS ENDPOINTS ====================

@bp.route('/patient/<int:patient_user_id>/observations', methods=['POST'])
@doctor_required
def create_observation(current_user_id, user_role, patient_user_id):
    """
    Crear una nueva observación médica para un paciente
    
    Body:
        {
            "observation_text": "Control estable, mantener dosis actual."
        }
    """
    data = request.get_json()
    
    if not data or 'observation_text' not in data:
        return jsonify({'error': 'observation_text es requerido'}), 400
    
    result, error = MedicalObservationService.create_observation(
        doctor_user_id=current_user_id,
        patient_user_id=patient_user_id,
        observation_text=data['observation_text']
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Observación creada exitosamente',
        'observation': result
    }), 201


@bp.route('/patient/<int:patient_user_id>/observations', methods=['GET'])
@doctor_required
def get_patient_observations(current_user_id, user_role, patient_user_id):
    """
    Obtener todas las observaciones médicas de un paciente
    
    Query params:
        - limit: número de resultados (default: 100)
        - offset: desplazamiento (default: 0)
    """
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    observations, total, error = MedicalObservationService.get_patient_observations(
        patient_user_id=patient_user_id,
        doctor_user_id=current_user_id,
        limit=limit,
        offset=offset
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'patient_user_id': patient_user_id,
        'observations': observations,
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200


@bp.route('/observations/<int:observation_id>', methods=['PUT'])
@doctor_required
def update_observation(current_user_id, user_role, observation_id):
    """
    Actualizar una observación médica existente
    
    Body:
        {
            "observation_text": "Ajuste de medicación, programar seguimiento."
        }
    """
    data = request.get_json()
    
    if not data or 'observation_text' not in data:
        return jsonify({'error': 'observation_text es requerido'}), 400
    
    result, error = MedicalObservationService.update_observation(
        observation_id=observation_id,
        doctor_user_id=current_user_id,
        observation_text=data['observation_text']
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Observación actualizada exitosamente',
        'observation': result
    }), 200


@bp.route('/observations/<int:observation_id>', methods=['DELETE'])
@doctor_required
def delete_observation(current_user_id, user_role, observation_id):
    """
    Eliminar una observación médica
    """
    success, error = MedicalObservationService.delete_observation(
        observation_id=observation_id,
        doctor_user_id=current_user_id
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Observación eliminada exitosamente'
    }), 200

