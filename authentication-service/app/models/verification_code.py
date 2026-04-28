import hashlib
import json
from app.extensions import db
from datetime import datetime, timedelta


class VerificationCode(db.Model):
    """
    Stores OTP codes for registration and password-reset flows.

    Lifecycle:
      - Created when user requests an OTP (register or forgot-password).
      - Marked used=True after successful verification.
      - expires_at is set to 10 minutes from creation.
    """
    __tablename__ = 'verification_codes'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    code_hash = db.Column(db.String(64), nullable=False)
    purpose = db.Column(db.Enum('registration', 'password_reset'), nullable=False)
    pending_user_data = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def hash_code(plain_code: str) -> str:
        return hashlib.sha256(plain_code.encode()).hexdigest()

    @classmethod
    def create(cls, email: str, plain_code: str, purpose: str,
               pending_user_data: dict | None = None) -> 'VerificationCode':
        """Factory — invalidates any previous active code for the same email+purpose."""
        cls.query.filter_by(email=email, purpose=purpose, used=False).update({'used': True})
        db.session.flush()

        record = cls(
            email=email,
            code_hash=cls.hash_code(plain_code),
            purpose=purpose,
            pending_user_data=json.dumps(pending_user_data) if pending_user_data else None,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.session.add(record)
        db.session.commit()
        return record

    def is_valid(self, plain_code: str) -> bool:
        """True if code matches, not used, and not expired."""
        if self.used:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return self.code_hash == self.hash_code(plain_code)

    def get_pending_data(self) -> dict | None:
        if self.pending_user_data:
            return json.loads(self.pending_user_data)
        return None

    def mark_used(self):
        self.used = True
        db.session.commit()

    def __repr__(self):
        return f'<VerificationCode email={self.email} purpose={self.purpose} used={self.used}>'
