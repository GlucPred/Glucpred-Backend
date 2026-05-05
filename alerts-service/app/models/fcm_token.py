from datetime import datetime
from app.extensions import db


class FcmToken(db.Model):
    """
    Almacena los FCM registration tokens de los dispositivos de cada usuario.
    Se actualiza con upsert cada vez que la app inicia sesión o el token se refresca.
    """
    __tablename__ = 'fcm_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True, unique=True)
    token = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(20), default='android')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'platform': self.platform,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
