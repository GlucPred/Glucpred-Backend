import random
import logging
from app.models import User, VerificationCode
from app.extensions import db
from app.utils.email_service import EmailService
from app.utils.security import JWTHandler
from app.utils.validators import AuthValidator
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class VerificationService:
    """Handles OTP generation, sending, and verification."""

    @staticmethod
    def _generate_code() -> str:
        return f'{random.randint(0, 999999):06d}'

    # ------------------------------------------------------------------
    # Registration flow
    # ------------------------------------------------------------------

    @staticmethod
    def initiate_registration(data: dict) -> tuple:
        """
        Validate registration data, store it pending, send OTP to email.

        Returns:
            (email, None) on success
            (None, {'error': str, 'status_code': int}) on failure
        """
        is_valid, error = AuthValidator.validate_registration(data)
        if not is_valid:
            return None, {'error': error, 'status_code': 400}

        if User.query.filter_by(username=data['username']).first():
            return None, {'error': 'El nombre de usuario ya está en uso', 'status_code': 409}

        if User.query.filter_by(email=data['email']).first():
            return None, {'error': 'El correo electrónico ya está registrado', 'status_code': 409}

        code = VerificationService._generate_code()
        email = data['email']

        VerificationCode.create(
            email=email,
            plain_code=code,
            purpose='registration',
            pending_user_data=data,
        )

        sent = EmailService.send_verification_code(email, code, 'registration')
        if not sent:
            return None, {'error': 'No se pudo enviar el correo de verificación. Intente de nuevo.', 'status_code': 502}

        return email, None

    @staticmethod
    def confirm_registration(email: str, code: str) -> tuple:
        """
        Verify OTP and create the user account.

        Returns:
            (user_dict, token) on success
            (None, {'error': str, 'status_code': int}) on failure
        """
        record = VerificationCode.query.filter_by(
            email=email, purpose='registration', used=False
        ).order_by(VerificationCode.created_at.desc()).first()

        if not record or not record.is_valid(code):
            return None, {'error': 'Código inválido o expirado', 'status_code': 400}

        pending = record.get_pending_data()
        if not pending:
            return None, {'error': 'Datos de registro no encontrados. Inicie el proceso nuevamente.', 'status_code': 400}

        try:
            new_user = User(
                nombre_completo=pending['nombre_completo'],
                username=pending['username'],
                email=pending['email'],
                numero_celular=pending.get('numero_celular'),
                rol=pending.get('rol', 'Paciente'),
            )
            new_user.set_password(pending['password'])
            db.session.add(new_user)
            record.mark_used()
            db.session.commit()

            token = JWTHandler.generate_token(new_user)
            return new_user.to_dict(), token

        except IntegrityError:
            db.session.rollback()
            return None, {'error': 'El usuario ya existe. Intente iniciar sesión.', 'status_code': 409}
        except Exception as exc:
            db.session.rollback()
            logger.error(f'Error confirming registration for {email}: {exc}', exc_info=True)
            return None, {'error': 'Error interno del servidor', 'status_code': 500}

    # ------------------------------------------------------------------
    # Password-reset flow
    # ------------------------------------------------------------------

    @staticmethod
    def send_password_reset_code(username_or_email: str) -> tuple:
        """
        Find the user by username or email, send OTP to their registered email.

        Always returns success to avoid revealing whether the account exists.

        Returns:
            (masked_email, None) on success (even when user not found)
            (None, {'error': str, 'status_code': int}) on hard failure
        """
        if not username_or_email:
            return None, {'error': 'Usuario o correo es requerido', 'status_code': 400}

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user:
            # Security: don't reveal user existence
            return 'correo registrado', None

        code = VerificationService._generate_code()
        VerificationCode.create(
            email=user.email,
            plain_code=code,
            purpose='password_reset',
        )

        sent = EmailService.send_verification_code(user.email, code, 'password_reset')
        if not sent:
            return None, {'error': 'No se pudo enviar el correo. Intente de nuevo.', 'status_code': 502}

        # Return masked email for UX feedback
        parts = user.email.split('@')
        masked = parts[0][:2] + '***@' + parts[1] if len(parts) == 2 else 'correo registrado'
        return masked, None

    @staticmethod
    def confirm_password_reset(email_or_username: str, code: str, new_password: str) -> tuple:
        """
        Verify OTP and update the user's password.

        Returns:
            (True, None) on success
            (None, {'error': str, 'status_code': int}) on failure
        """
        if not new_password or len(new_password) < 8:
            return None, {'error': 'La contraseña debe tener al menos 8 caracteres', 'status_code': 400}

        user = User.query.filter(
            (User.username == email_or_username) | (User.email == email_or_username)
        ).first()

        if not user:
            return None, {'error': 'Usuario no encontrado', 'status_code': 404}

        record = VerificationCode.query.filter_by(
            email=user.email, purpose='password_reset', used=False
        ).order_by(VerificationCode.created_at.desc()).first()

        if not record or not record.is_valid(code):
            return None, {'error': 'Código inválido o expirado', 'status_code': 400}

        try:
            user.set_password(new_password)
            user.reset_failed_attempts()
            record.mark_used()
            db.session.commit()
            return True, None
        except Exception as exc:
            db.session.rollback()
            logger.error(f'Error resetting password for {user.email}: {exc}', exc_info=True)
            return None, {'error': 'Error al actualizar contraseña', 'status_code': 500}
