from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    numero_celular = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('Paciente', 'Medico'), nullable=False, default='Paciente')
    primer_inicio_sesion = db.Column(db.Boolean, nullable=False, default=True)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        from datetime import datetime
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def increment_failed_attempts(self):
        from datetime import datetime, timedelta
        self.failed_attempts = (self.failed_attempts or 0) + 1
        if self.failed_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()

    def reset_failed_attempts(self):
        self.failed_attempts = 0
        self.locked_until = None
        db.session.commit()

    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            'id': self.id,
            'nombre_completo': self.nombre_completo,
            'username': self.username,
            'email': self.email,
            'numero_celular': self.numero_celular,
            'rol': self.rol,
            'primer_inicio_sesion': self.primer_inicio_sesion,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
