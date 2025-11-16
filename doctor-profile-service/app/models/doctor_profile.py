from app.extensions import db
from datetime import datetime


class DoctorProfile(db.Model):
    """Profile model for doctor data"""
    __tablename__ = 'doctor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    numero_colegiatura = db.Column(db.String(50), nullable=False)
    especialidad = db.Column(db.String(100), nullable=False)
    centro_trabajo = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert doctor profile to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'numero_colegiatura': self.numero_colegiatura,
            'especialidad': self.especialidad,
            'centro_trabajo': self.centro_trabajo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DoctorProfile user_id={self.user_id} especialidad={self.especialidad}>'
