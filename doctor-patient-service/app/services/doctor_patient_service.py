from app.models import DoctorPatientRelation
from app.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DoctorPatientService:
    """Service for managing doctor-patient relationships"""
    
    @staticmethod
    def assign_patient_to_doctor(doctor_user_id, patient_user_id):
        """
        Assign a patient to a doctor (create active relationship)
        
        Business Rules:
        - If patient is already ACTIVELY assigned to another doctor, return error
        - If same doctor-patient relation exists but is INACTIVE, reactivate it
        - Otherwise, create new active relationship
        
        Args:
            doctor_user_id (int): Doctor's user ID
            patient_user_id (int): Patient's user ID
            
        Returns:
            tuple: (relation_dict, error_message)
        """
        try:
            # Check if patient is already actively assigned to another doctor
            active_relation = DoctorPatientRelation.query.filter_by(
                patient_user_id=patient_user_id,
                estado='A'
            ).first()
            
            if active_relation and active_relation.doctor_user_id != doctor_user_id:
                return None, f'El paciente ya está siendo atendido activamente por otro médico (Doctor ID: {active_relation.doctor_user_id})'
            
            # Check if this exact doctor-patient relation already exists
            existing_relation = DoctorPatientRelation.query.filter_by(
                doctor_user_id=doctor_user_id,
                patient_user_id=patient_user_id
            ).first()
            
            if existing_relation:
                if existing_relation.estado == 'A':
                    return None, 'Esta relación médico-paciente ya está activa'
                else:
                    # Reactivate inactive relation
                    existing_relation.estado = 'A'
                    existing_relation.fecha_asignacion = datetime.utcnow()
                    existing_relation.fecha_inactivacion = None
                    db.session.commit()
                    logger.info(f"Reactivated relation: Doctor {doctor_user_id} - Patient {patient_user_id}")
                    return existing_relation.to_dict(), None
            
            # Create new active relationship
            new_relation = DoctorPatientRelation(
                doctor_user_id=doctor_user_id,
                patient_user_id=patient_user_id,
                estado='A',
                fecha_asignacion=datetime.utcnow()
            )
            
            db.session.add(new_relation)
            db.session.commit()
            
            logger.info(f"Created new active relation: Doctor {doctor_user_id} - Patient {patient_user_id}")
            return new_relation.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning patient to doctor: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def deactivate_relation(doctor_user_id, patient_user_id):
        """
        Deactivate a doctor-patient relationship
        
        Args:
            doctor_user_id (int): Doctor's user ID
            patient_user_id (int): Patient's user ID
            
        Returns:
            tuple: (relation_dict, error_message)
        """
        try:
            relation = DoctorPatientRelation.query.filter_by(
                doctor_user_id=doctor_user_id,
                patient_user_id=patient_user_id
            ).first()
            
            if not relation:
                return None, 'Relación médico-paciente no encontrada'
            
            if relation.estado == 'I':
                return None, 'La relación ya está inactiva'
            
            relation.estado = 'I'
            relation.fecha_inactivacion = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Deactivated relation: Doctor {doctor_user_id} - Patient {patient_user_id}")
            return relation.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deactivating relation: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def get_doctor_patients(doctor_user_id, estado=None):
        """
        Get all patients assigned to a doctor
        
        Args:
            doctor_user_id (int): Doctor's user ID
            estado (str, optional): Filter by estado ('A' or 'I'). If None, returns all.
            
        Returns:
            tuple: (list_of_relations, error_message)
        """
        try:
            query = DoctorPatientRelation.query.filter_by(doctor_user_id=doctor_user_id)
            
            if estado:
                if estado not in ['A', 'I']:
                    return None, "Estado debe ser 'A' (Activo) o 'I' (Inactivo)"
                query = query.filter_by(estado=estado)
            
            relations = query.order_by(DoctorPatientRelation.fecha_asignacion.desc()).all()
            
            return [r.to_dict() for r in relations], None
            
        except Exception as e:
            logger.error(f"Error getting doctor's patients: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def get_patient_doctors(patient_user_id, estado=None):
        """
        Get all doctors assigned to a patient
        
        Args:
            patient_user_id (int): Patient's user ID
            estado (str, optional): Filter by estado ('A' or 'I'). If None, returns all.
            
        Returns:
            tuple: (list_of_relations, error_message)
        """
        try:
            query = DoctorPatientRelation.query.filter_by(patient_user_id=patient_user_id)
            
            if estado:
                if estado not in ['A', 'I']:
                    return None, "Estado debe ser 'A' (Activo) o 'I' (Inactivo)"
                query = query.filter_by(estado=estado)
            
            relations = query.order_by(DoctorPatientRelation.fecha_asignacion.desc()).all()
            
            return [r.to_dict() for r in relations], None
            
        except Exception as e:
            logger.error(f"Error getting patient's doctors: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def get_all_patients_available_for_doctor(doctor_user_id):
        """
        Get all patients that a doctor CAN assign (patients not actively assigned to other doctors)
        
        Args:
            doctor_user_id (int): Doctor's user ID
            
        Returns:
            tuple: (list_of_patient_user_ids, error_message)
        """
        try:
            # Get all patients actively assigned to OTHER doctors
            patients_with_active_doctor = db.session.query(
                DoctorPatientRelation.patient_user_id
            ).filter(
                DoctorPatientRelation.estado == 'A',
                DoctorPatientRelation.doctor_user_id != doctor_user_id
            ).all()
            
            unavailable_patient_ids = [p[0] for p in patients_with_active_doctor]
            
            return {
                'unavailable_patients': unavailable_patient_ids,
                'message': f'Estos pacientes ya están siendo atendidos activamente por otros médicos'
            }, None
            
        except Exception as e:
            logger.error(f"Error getting available patients: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def check_patient_availability(patient_user_id):
        """
        Check if a patient is available to be assigned to a new doctor
        
        Args:
            patient_user_id (int): Patient's user ID
            
        Returns:
            tuple: (availability_dict, error_message)
        """
        try:
            active_relation = DoctorPatientRelation.query.filter_by(
                patient_user_id=patient_user_id,
                estado='A'
            ).first()
            
            if active_relation:
                return {
                    'available': False,
                    'patient_user_id': patient_user_id,
                    'assigned_to_doctor_id': active_relation.doctor_user_id,
                    'fecha_asignacion': active_relation.fecha_asignacion.isoformat()
                }, None
            else:
                return {
                    'available': True,
                    'patient_user_id': patient_user_id,
                    'assigned_to_doctor_id': None
                }, None
                
        except Exception as e:
            logger.error(f"Error checking patient availability: {e}", exc_info=True)
            return None, 'Error interno del servidor'
