import re


class AuthValidator:
    """Validator for authentication data"""
    
    @staticmethod
    def validate_registration(data):
        """Validate user registration data"""
        required_fields = ['nombre_completo', 'username', 'email', 'password']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f'El campo {field} es requerido'
        
        # Validate password strength
        password = data['password']
        if len(password) < 8:
            return False, 'La contraseña debe tener al menos 8 caracteres'
        if not re.search(r'[A-Z]', password):
            return False, 'La contraseña debe contener al menos una letra mayúscula'
        if not re.search(r'[a-z]', password):
            return False, 'La contraseña debe contener al menos una letra minúscula'
        if not re.search(r'[0-9]', password):
            return False, 'La contraseña debe contener al menos un número'
        
        # Validate role
        rol = data.get('rol', 'Paciente')
        if rol not in ['Paciente', 'Medico']:
            return False, 'El rol debe ser "Paciente" o "Medico"'
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return False, 'Formato de correo electrónico inválido'
        
        return True, None
