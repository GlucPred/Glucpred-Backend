from app.extensions import db
from datetime import datetime


class GlucoseRecord(db.Model):
    """Model for glucose measurements"""
    __tablename__ = 'glucose_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    glucose_value = db.Column(db.Float, nullable=False)  # mg/dL from CGM
    measurement_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    classification = db.Column(db.String(20), nullable=False)  # 'bajo', 'normal', 'alto', 'critico'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When record was stored in DB
    
    # Índices compuestos para queries eficientes
    __table_args__ = (
        db.Index('idx_user_measurement_time', 'user_id', 'measurement_time'),
        db.Index('idx_user_classification', 'user_id', 'classification'),
    )
    
    def to_dict(self):
        """Convert record to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'glucose_value': self.glucose_value,
            'measurement_time': self.measurement_time.isoformat() if self.measurement_time else None,
            'classification': self.classification,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<GlucoseRecord user={self.user_id} value={self.glucose_value} time={self.measurement_time}>'
