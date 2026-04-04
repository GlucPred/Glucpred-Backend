from app.models import DoctorProfile
from app.extensions import db
from app.events import EventProducer
import logging

logger = logging.getLogger(__name__)


class DoctorProfileService:
    """Service for doctor profile operations"""
    
    @staticmethod
    def create_doctor_profile(data):
        """
        Create a new doctor profile
        
        Args:
            data (dict): Dictionary with profile data including user_id
            
        Returns:
            tuple: (profile_dict, error_message)
        """
        try:
            user_id = data.get('user_id')
            
            if not user_id:
                return None, 'user_id es requerido'
            
            # Check if profile already exists
            existing = DoctorProfile.query.filter_by(user_id=user_id).first()
            if existing:
                return None, 'El perfil de médico ya existe para este usuario'
            
            # Validate required fields
            numero_colegiatura = data.get('numero_colegiatura')
            especialidad = data.get('especialidad')
            centro_trabajo = data.get('centro_trabajo')
            
            if not numero_colegiatura:
                return None, 'numero_colegiatura es requerido'
            if not especialidad:
                return None, 'especialidad es requerida'
            if not centro_trabajo:
                return None, 'centro_trabajo es requerido'
            
            # Create profile
            doctor_profile = DoctorProfile(
                user_id=user_id,
                numero_colegiatura=numero_colegiatura,
                especialidad=especialidad,
                centro_trabajo=centro_trabajo
            )
            
            db.session.add(doctor_profile)
            db.session.commit()
            
            logger.info(f"Doctor profile created for user {user_id}")
            
            # Publish event
            profile_dict = doctor_profile.to_dict()
            EventProducer.publish_doctor_profile_created(user_id, profile_dict)
            
            return profile_dict, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating doctor profile: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def get_doctor_profile(user_id):
        """
        Get doctor profile by user_id
        
        Args:
            user_id (int): User ID
            
        Returns:
            tuple: (profile_dict, error_message)
        """
        try:
            profile = DoctorProfile.query.filter_by(user_id=user_id).first()
            
            if not profile:
                return None, 'Perfil de médico no encontrado'
            
            return profile.to_dict(), None
            
        except Exception as e:
            logger.error(f"Error getting doctor profile: {e}", exc_info=True)
            return None, 'Error interno del servidor'
    
    @staticmethod
    def update_doctor_profile(user_id, data):
        """
        Update doctor profile
        
        Args:
            user_id (int): User ID
            data (dict): Dictionary with fields to update
            
        Returns:
            tuple: (profile_dict, error_message)
        """
        try:
            profile = DoctorProfile.query.filter_by(user_id=user_id).first()
            
            if not profile:
                return None, 'Perfil de médico no encontrado'
            
            # Update only provided fields
            if 'numero_colegiatura' in data:
                profile.numero_colegiatura = data['numero_colegiatura']
            if 'especialidad' in data:
                profile.especialidad = data['especialidad']
            if 'centro_trabajo' in data:
                profile.centro_trabajo = data['centro_trabajo']
            
            db.session.commit()
            
            logger.info(f"Doctor profile updated for user {user_id}")
            
            return profile.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating doctor profile: {e}", exc_info=True)
            return None, 'Error interno del servidor'
