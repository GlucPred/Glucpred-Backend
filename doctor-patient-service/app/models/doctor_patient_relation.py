from app.extensions import db
from datetime import datetime


class DoctorPatientRelation(db.Model):
    """Model for doctor-patient relationship"""
    __tablename__ = 'doctor_patient_relations'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_user_id = db.Column(db.Integer, nullable=False, index=True)
    patient_user_id = db.Column(db.Integer, nullable=False, index=True)
    estado = db.Column(db.String(1), nullable=False, default='A')  # 'A' = Activo, 'I' = Inactivo
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_inactivacion = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: un doctor no puede tener múltiples relaciones con el mismo paciente
    __table_args__ = (
        db.UniqueConstraint('doctor_user_id', 'patient_user_id', name='unique_doctor_patient'),
        db.Index('idx_doctor_estado', 'doctor_user_id', 'estado'),
        db.Index('idx_patient_estado', 'patient_user_id', 'estado'),
    )
    
    def to_dict(self):
        """Convert relation to dictionary"""
        return {
            'id': self.id,
            'doctor_user_id': self.doctor_user_id,
            'patient_user_id': self.patient_user_id,
            'estado': self.estado,
            'fecha_asignacion': self.fecha_asignacion.isoformat() if self.fecha_asignacion else None,
            'fecha_inactivacion': self.fecha_inactivacion.isoformat() if self.fecha_inactivacion else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DoctorPatientRelation doctor={self.doctor_user_id} patient={self.patient_user_id} estado={self.estado}>'
