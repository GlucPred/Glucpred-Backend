from datetime import datetime
from app.extensions import db

class Alert(db.Model):
    """
    Modelo de Alerta generado automáticamente por el sistema
    basado en las mediciones de glucosa.
    
    Tipos de alertas:
    - critica: Hiperglucemia (>180) o Hipoglucemia (<70)
    - recordatorio: Recordatorios de medicación, medición, etc.
    
    Severidades:
    - critico: Requiere atención inmediata (rojo)
    - advertencia: Requiere precaución (amarillo)
    - info: Informativo (azul)
    """
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Relación con el registro de glucosa que generó la alerta
    glucose_record_id = db.Column(db.Integer, nullable=True, index=True)
    glucose_value = db.Column(db.Float, nullable=True)  # Valor que disparó la alerta
    
    # Tipo de alerta
    alert_type = db.Column(db.String(20), nullable=False, index=True)  # 'critica', 'recordatorio'
    
    # Severidad
    severity = db.Column(db.String(20), nullable=False)  # 'critico', 'advertencia', 'info'
    
    # Contenido de la alerta
    title = db.Column(db.String(200), nullable=False)  # "Hiperglucemia detectada"
    message = db.Column(db.Text, nullable=False)  # "Revisar medicación y consultar médico"
    
    # Estado
    is_read = db.Column(db.Boolean, default=False, index=True)  # Si el usuario ya la vio
    is_dismissed = db.Column(db.Boolean, default=False)  # Si el usuario la descartó
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    
    # Índices compuestos para queries eficientes
    __table_args__ = (
        db.Index('idx_user_type_created', 'user_id', 'alert_type', 'created_at'),
        db.Index('idx_user_read', 'user_id', 'is_read'),
        db.Index('idx_user_severity', 'user_id', 'severity'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'glucose_record_id': self.glucose_record_id,
            'glucose_value': self.glucose_value,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None
        }
