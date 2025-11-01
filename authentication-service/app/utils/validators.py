class AuthValidator:
    """Validator for authentication data"""
    
    @staticmethod
    def validate_registration(data):
        """
        Validate user registration data
        
        Args:
            data (dict): Registration data
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['nombre_completo', 'username', 'email', 'password']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f'El campo {field} es requerido'
        
        # Validate password length
        if len(data['password']) < 6:
            return False, 'La contraseña debe tener al menos 6 caracteres'
        
        # Validate role
        rol = data.get('rol', 'Paciente')
        if rol not in ['Paciente', 'Medico']:
            return False, 'El rol debe ser "Paciente" o "Medico"'
        
        # Validate email format (basic)
        if '@' not in data['email'] or '.' not in data['email']:
            return False, 'Formato de correo electrónico inválido'
        
        return True, None
