from app.models import MedicalObservation
from app.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MedicalObservationService:
    """Servicio para gestionar observaciones médicas"""
    
    @staticmethod
    def create_observation(doctor_user_id, patient_user_id, observation_text):
        """
        Crear una nueva observación médica
        
        Args:
            doctor_user_id (int): ID del doctor
            patient_user_id (int): ID del paciente
            observation_text (str): Texto de la observación
            
        Returns:
            tuple: (observation_dict, error_message)
        """
        try:
            if not observation_text or not observation_text.strip():
                return None, 'El texto de la observación no puede estar vacío'
            
            observation = MedicalObservation(
                doctor_user_id=doctor_user_id,
                patient_user_id=patient_user_id,
                observation_text=observation_text.strip()
            )
            
            db.session.add(observation)
            db.session.commit()
            
            logger.info(f"Created observation: Doctor {doctor_user_id} for Patient {patient_user_id}")
            return observation.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating observation: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def get_patient_observations(patient_user_id, doctor_user_id=None, limit=100, offset=0):
        """
        Obtener observaciones de un paciente
        
        Args:
            patient_user_id (int): ID del paciente
            doctor_user_id (int, optional): Filtrar por doctor específico
            limit (int): Número de resultados
            offset (int): Desplazamiento
            
        Returns:
            tuple: (observations_list, total_count, error_message)
        """
        try:
            query = MedicalObservation.query.filter_by(patient_user_id=patient_user_id)
            
            if doctor_user_id:
                query = query.filter_by(doctor_user_id=doctor_user_id)
            
            total = query.count()
            
            observations = query.order_by(
                MedicalObservation.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return [obs.to_dict() for obs in observations], total, None
            
        except Exception as e:
            logger.error(f"Error getting patient observations: {e}", exc_info=True)
            return None, 0, 'Error interno del servidor'
    
    @staticmethod
    def update_observation(observation_id, doctor_user_id, observation_text):
        """
        Actualizar una observación médica (solo el doctor que la creó)
        
        Args:
            observation_id (int): ID de la observación
            doctor_user_id (int): ID del doctor (para verificar permisos)
            observation_text (str): Nuevo texto
            
        Returns:
            tuple: (observation_dict, error_message)
        """
        try:
            observation = MedicalObservation.query.filter_by(
                id=observation_id,
                doctor_user_id=doctor_user_id
            ).first()
            
            if not observation:
                return None, 'Observación no encontrada o no tienes permiso para editarla'
            
            if not observation_text or not observation_text.strip():
                return None, 'El texto de la observación no puede estar vacío'
            
            observation.observation_text = observation_text.strip()
            observation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Updated observation {observation_id} by Doctor {doctor_user_id}")
            return observation.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating observation: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def delete_observation(observation_id, doctor_user_id):
        """
        Eliminar una observación médica (solo el doctor que la creó)
        
        Args:
            observation_id (int): ID de la observación
            doctor_user_id (int): ID del doctor (para verificar permisos)
            
        Returns:
            tuple: (success_bool, error_message)
        """
        try:
            observation = MedicalObservation.query.filter_by(
                id=observation_id,
                doctor_user_id=doctor_user_id
            ).first()
            
            if not observation:
                return False, 'Observación no encontrada o no tienes permiso para eliminarla'
            
            db.session.delete(observation)
            db.session.commit()
            
            logger.info(f"Deleted observation {observation_id} by Doctor {doctor_user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting observation: {e}", exc_info=True)
            return False, 'Error interno del servidor'
    
    @staticmethod
    def get_observation_by_id(observation_id, doctor_user_id):
        """
        Obtener una observación específica
        
        Args:
            observation_id (int): ID de la observación
            doctor_user_id (int): ID del doctor (para verificar permisos)
            
        Returns:
            tuple: (observation_dict, error_message)
        """
        try:
            observation = MedicalObservation.query.filter_by(
                id=observation_id,
                doctor_user_id=doctor_user_id
            ).first()
            
            if not observation:
                return None, 'Observación no encontrada'
            
            return observation.to_dict(), None
            
        except Exception as e:
            logger.error(f"Error getting observation: {e}", exc_info=True)
            return None, 'Error interno del servidor'
