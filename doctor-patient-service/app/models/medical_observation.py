from app.extensions import db
from datetime import datetime


class MedicalObservation(db.Model):
    """
    Modelo para observaciones médicas que los doctores escriben sobre sus pacientes
    """
    __tablename__ = 'medical_observations'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_user_id = db.Column(db.Integer, nullable=False, index=True)
    patient_user_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Contenido de la observación
    observation_text = db.Column(db.Text, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices para queries eficientes
    __table_args__ = (
        db.Index('idx_patient_created', 'patient_user_id', 'created_at'),
        db.Index('idx_doctor_patient', 'doctor_user_id', 'patient_user_id'),
    )
    
    def to_dict(self):
        """Convertir observación a diccionario"""
        return {
            'id': self.id,
            'doctor_user_id': self.doctor_user_id,
            'patient_user_id': self.patient_user_id,
            'observation_text': self.observation_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MedicalObservation id={self.id} doctor={self.doctor_user_id} patient={self.patient_user_id}>'
