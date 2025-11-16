from flask import Blueprint, request, jsonify
from app.services import DoctorPatientService
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
