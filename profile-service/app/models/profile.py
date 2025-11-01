from app.extensions import db
from datetime import datetime


class Profile(db.Model):
    """Profile model for patient data"""
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    edad = db.Column(db.Integer, nullable=True)
    peso = db.Column(db.Float, nullable=True)  # en kg
    altura = db.Column(db.Float, nullable=True)  # en cm
    medicamentos = db.Column(db.Text, nullable=True)
    antecedentes = db.Column(db.Text, nullable=True)
    fecha_diagnostico = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_imc(self):
        """Calculate Body Mass Index (IMC)"""
        if self.peso and self.altura and self.altura > 0:
            altura_metros = self.altura / 100
            return round(self.peso / (altura_metros ** 2), 2)
        return None
    
    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'edad': self.edad,
            'peso': self.peso,
            'altura': self.altura,
            'imc': self.calculate_imc(),
            'medicamentos': self.medicamentos,
            'antecedentes': self.antecedentes,
            'fecha_diagnostico': self.fecha_diagnostico.isoformat() if self.fecha_diagnostico else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Profile user_id={self.user_id}>'
