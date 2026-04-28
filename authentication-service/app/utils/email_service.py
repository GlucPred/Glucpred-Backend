import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = os.getenv('EMAIL_USER', '***REMOVED***')
SMTP_PASS = os.getenv('EMAIL_PASS', '***REMOVED***')


class EmailService:
    """Handles transactional email sending via Gmail SMTP."""

    @staticmethod
    def send_verification_code(to_email: str, code: str, purpose: str) -> bool:
        """
        Send a 6-digit OTP to the given email address.

        Args:
            to_email: Recipient email
            code: 6-digit numeric code (plain text, not hashed)
            purpose: 'registration' | 'password_reset'

        Returns:
            True on success, False on failure
        """
        if purpose == 'registration':
            subject = 'GlucPred — Código de verificación'
            action = 'completar tu registro'
        else:
            subject = 'GlucPred — Recuperación de contraseña'
            action = 'restablecer tu contraseña'

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 30px;">
            <div style="max-width: 480px; margin: 0 auto; background: #ffffff;
                        border-radius: 12px; padding: 36px; box-shadow: 0 2px 8px rgba(0,0,0,.08);">
              <h2 style="color: #1565C0; margin-bottom: 8px;">GlucPred</h2>
              <p style="color: #555; font-size: 15px;">
                Usa el siguiente código para {action}. Expira en <strong>10 minutos</strong>.
              </p>
              <div style="text-align: center; margin: 28px 0;">
                <span style="display: inline-block; font-size: 40px; font-weight: bold;
                             letter-spacing: 10px; color: #1565C0; background: #E3F2FD;
                             padding: 16px 28px; border-radius: 10px;">{code}</span>
              </div>
              <p style="color: #888; font-size: 13px;">
                Si no solicitaste este código, ignora este correo. Tu cuenta permanece segura.
              </p>
            </div>
          </body>
        </html>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'GlucPred <{SMTP_USER}>'
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, to_email, msg.as_string())
            logger.info(f'Verification email sent to {to_email} (purpose={purpose})')
            return True
        except Exception as exc:
            logger.error(f'Failed to send email to {to_email}: {exc}', exc_info=True)
            return False
