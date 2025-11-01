import jwt
from datetime import datetime, timedelta
from config.settings import Config


class JWTHandler:
    """Handle JWT token generation and verification"""
    
    @staticmethod
    def generate_token(user):
        """
        Generate JWT token for user
        
        Args:
            user: User model instance
            
        Returns:
            str: JWT token
        """
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'rol': user.rol,
            'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
        }
        token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
        return token
    
    @staticmethod
    def decode_token(token):
        """
        Decode and verify JWT token
        
        Args:
            token (str): JWT token
            
        Returns:
            dict: Token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
