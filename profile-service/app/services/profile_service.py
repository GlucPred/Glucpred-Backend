from app.models import Profile
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime


class ProfileService:
    """Service layer for profile business logic"""
    
    @staticmethod
    def create_profile(data):
        """
        Create a new profile
        
        Args:
            data (dict): Profile data
            
        Returns:
            tuple: (profile_dict, None) or (None, error_message)
        """
        # Validate required fields
        if 'user_id' not in data:
            return None, 'El campo user_id es requerido'
        
        # Check if profile already exists
        existing_profile = Profile.query.filter_by(user_id=data['user_id']).first()
        if existing_profile:
            return None, 'Ya existe un perfil para este usuario'
        
        # Parse fecha_diagnostico if provided
        fecha_diagnostico = None
        if data.get('fecha_diagnostico'):
            fecha_diagnostico = ProfileService._parse_date(data['fecha_diagnostico'])
            if fecha_diagnostico is None:
                return None, 'Formato de fecha inválido. Use YYYY-MM-DD'
        
        try:
            # Create new profile
            new_profile = Profile(
                user_id=data['user_id'],
                edad=data.get('edad'),
                peso=data.get('peso'),
                altura=data.get('altura'),
                medicamentos=data.get('medicamentos'),
                antecedentes=data.get('antecedentes'),
                fecha_diagnostico=fecha_diagnostico
            )
            
            db.session.add(new_profile)
            db.session.commit()
            
            return new_profile.to_dict(), None
            
        except IntegrityError:
            db.session.rollback()
            return None, 'Error al crear el perfil. El usuario ya tiene un perfil.'
        except Exception as e:
            db.session.rollback()
            return None, f'Error interno del servidor: {str(e)}'
    
    @staticmethod
    def get_profile(user_id):
        """
        Get profile by user_id
        
        Args:
            user_id (int): User ID
            
        Returns:
            tuple: (profile_dict, None) or (None, error_message)
        """
        profile = Profile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            return None, 'Perfil no encontrado'
        
        return profile.to_dict(), None
    
    @staticmethod
    def update_profile(user_id, data):
        """
        Update profile by user_id
        
        Args:
            user_id (int): User ID
            data (dict): Profile data to update
            
        Returns:
            tuple: (profile_dict, None) or (None, error_message)
        """
        profile = Profile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            return None, 'Perfil no encontrado'
        
        try:
            # Update fields if provided
            if 'edad' in data:
                profile.edad = data['edad']
            if 'peso' in data:
                profile.peso = data['peso']
            if 'altura' in data:
                profile.altura = data['altura']
            if 'medicamentos' in data:
                profile.medicamentos = data['medicamentos']
            if 'antecedentes' in data:
                profile.antecedentes = data['antecedentes']
            if 'fecha_diagnostico' in data:
                if data['fecha_diagnostico']:
                    fecha = ProfileService._parse_date(data['fecha_diagnostico'])
                    if fecha is None:
                        return None, 'Formato de fecha inválido. Use YYYY-MM-DD'
                    profile.fecha_diagnostico = fecha
                else:
                    profile.fecha_diagnostico = None
            
            db.session.commit()
            
            return profile.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            return None, f'Error interno del servidor: {str(e)}'
    
    @staticmethod
    def _parse_date(date_string):
        """
        Parse date string to date object
        
        Args:
            date_string (str): Date in YYYY-MM-DD format
            
        Returns:
            date or None: Parsed date or None if invalid
        """
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            return None
