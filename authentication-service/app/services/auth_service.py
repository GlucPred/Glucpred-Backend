from app.models import User
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from app.utils.security import JWTHandler
from app.utils.validators import AuthValidator


class AuthService:
    """Service layer for authentication business logic"""
    
    @staticmethod
    def register_user(data):
        """
        Register a new user
        
        Args:
            data (dict): User registration data
            
        Returns:
            tuple: (user_dict, token) or (None, {'error': message, 'status_code': code})
        """
        # Validate input data
        is_valid, error = AuthValidator.validate_registration(data)
        if not is_valid:
            return None, {'error': error, 'status_code': 400}
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return None, {'error': 'El nombre de usuario ya está en uso', 'status_code': 409}
        
        if User.query.filter_by(email=data['email']).first():
            return None, {'error': 'El correo electrónico ya está registrado', 'status_code': 409}
        
        try:
            # Create new user
            new_user = User(
                nombre_completo=data['nombre_completo'],
                username=data['username'],
                email=data['email'],
                numero_celular=data.get('numero_celular'),
                rol=data.get('rol', 'Paciente')
            )
            new_user.set_password(data['password'])
            
            db.session.add(new_user)
            db.session.commit()
            
            # Generate JWT token
            token = JWTHandler.generate_token(new_user)
            
            return new_user.to_dict(), token
            
        except IntegrityError:
            db.session.rollback()
            return None, {'error': 'Error al registrar el usuario. Verifique que los datos sean únicos.', 'status_code': 409}
        except Exception as e:
            db.session.rollback()
            import logging
            logging.getLogger(__name__).error(f'Error en registro: {str(e)}', exc_info=True)
            return None, {'error': 'Error interno del servidor', 'status_code': 500}
    
    @staticmethod
    def login_user(username_or_email, password):
        """
        Authenticate user and generate token
        
        Args:
            username_or_email (str): Username or email
            password (str): User password
            
        Returns:
            tuple: (user_dict, token) or (None, {'error': message, 'status_code': code})
        """
        # Validate input
        if not username_or_email or not password:
            return None, {'error': 'Usuario/correo y contraseña son requeridos', 'status_code': 400}
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user:
            return None, {'error': 'Credenciales inválidas', 'status_code': 401}
        
        # Verify password
        if not user.check_password(password):
            return None, {'error': 'Credenciales inválidas', 'status_code': 401}
        
        # Generate token
        token = JWTHandler.generate_token(user)
        
        # Return user info (primer_inicio_sesion will be changed when profile is created/updated)
        return user.to_dict(), token
    
    @staticmethod
    def mark_profile_complete(user_id):
        """
        Mark user as having completed initial profile setup
        
        Args:
            user_id (int): User ID
            
        Returns:
            tuple: (success, error_message)
        """
        try:
            user = User.query.get(user_id)
            
            if not user:
                return False, 'Usuario no encontrado'
            
            if user.primer_inicio_sesion:
                user.primer_inicio_sesion = False
                db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            import logging
            logging.getLogger(__name__).error(f'Error al actualizar usuario: {str(e)}', exc_info=True)
            return False, 'Error al actualizar usuario'
    
    @staticmethod
    def get_user_data(user_id):
        """
        Get user data by ID
        
        Args:
            user_id (int): User ID
            
        Returns:
            tuple: (user_dict, None) or (None, error_message)
        """
        user = User.query.get(user_id)
        
        if not user:
            return None, 'Usuario no encontrado'
        
        return user.to_dict(), None
    
    @staticmethod
    def update_user_data(user_id, data):
        """
        Update user data
        
        Args:
            user_id (int): User ID
            data (dict): Data to update
            
        Returns:
            tuple: (user_dict, None) or (None, error_message)
        """
        user = User.query.get(user_id)
        
        if not user:
            return None, 'Usuario no encontrado'
        
        try:
            # Check for unique constraints if updating username or email
            if 'username' in data and data['username'] != user.username:
                existing = User.query.filter_by(username=data['username']).first()
                if existing:
                    return None, 'El nombre de usuario ya está en uso'
                user.username = data['username']
            
            if 'email' in data and data['email'] != user.email:
                existing = User.query.filter_by(email=data['email']).first()
                if existing:
                    return None, 'El correo electrónico ya está registrado'
                user.email = data['email']
            
            # Update other fields
            if 'nombre_completo' in data:
                user.nombre_completo = data['nombre_completo']
            
            if 'numero_celular' in data:
                user.numero_celular = data['numero_celular']
            
            db.session.commit()
            
            return user.to_dict(), None
            
        except IntegrityError:
            db.session.rollback()
            return None, 'Error: datos duplicados'
        except Exception as e:
            db.session.rollback()
            import logging
            logging.getLogger(__name__).error(f'Error al actualizar usuario: {str(e)}', exc_info=True)
            return None, 'Error al actualizar usuario'
    
    @staticmethod
    def get_all_users():
        """
        Get all users with basic information
        
        Returns:
            tuple: (list_of_users, error_message)
        """
        try:
            users = User.query.all()
            return [u.to_dict() for u in users], None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Error al obtener usuarios: {str(e)}', exc_info=True)
            return None, 'Error al obtener usuarios'
