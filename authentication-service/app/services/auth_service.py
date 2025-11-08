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
            tuple: (user_dict, token) or (None, error_message)
        """
        # Validate input data
        is_valid, error = AuthValidator.validate_registration(data)
        if not is_valid:
            return None, error
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return None, 'El nombre de usuario ya está en uso'
        
        if User.query.filter_by(email=data['email']).first():
            return None, 'El correo electrónico ya está registrado'
        
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
            return None, 'Error al registrar el usuario. Verifique que los datos sean únicos.'
        except Exception as e:
            db.session.rollback()
            return None, f'Error interno del servidor: {str(e)}'
    
    @staticmethod
    def login_user(username_or_email, password):
        """
        Authenticate user and generate token
        
        Args:
            username_or_email (str): Username or email
            password (str): User password
            
        Returns:
            tuple: (user_dict, token) or (None, error_message)
        """
        # Validate input
        if not username_or_email or not password:
            return None, 'Usuario/correo y contraseña son requeridos'
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user:
            return None, 'Credenciales inválidas'
        
        # Verify password
        if not user.check_password(password):
            return None, 'Credenciales inválidas'
        
        # Check if it's the first login and update the flag
        is_first_login = user.primer_inicio_sesion
        if is_first_login:
            try:
                user.primer_inicio_sesion = False
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                # Continue even if update fails, it's not critical
        
        # Generate token
        token = JWTHandler.generate_token(user)
        
        # Include first login info in response
        user_dict = user.to_dict()
        user_dict['es_primer_inicio'] = is_first_login
        
        return user_dict, token
