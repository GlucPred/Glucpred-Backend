import logging
import firebase_admin
from firebase_admin import credentials, messaging
from config.settings import Config

logger = logging.getLogger(__name__)

_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def send_notification(token: str, title: str, body: str, data: dict = None) -> bool:
    """
    Envía una notificación FCM a un token específico.

    Args:
        token: FCM registration token del dispositivo
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Payload de datos adicionales (dict de strings)

    Returns:
        True si se envió correctamente, False si hubo error
    """
    try:
        _get_firebase_app()

        payload_data = {k: str(v) for k, v in (data or {}).items()}

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=payload_data,
            token=token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    channel_id='glucpred_alerts',
                ),
            ),
        )

        response = messaging.send(message)
        logger.info(f"FCM sent successfully: {response}")
        return True

    except Exception as e:
        logger.error(f"FCM send failed for token={token[:20]}...: {e}")
        return False


def send_alert_to_users(user_ids: list, title: str, body: str, data: dict = None):
    """
    Envía una notificación FCM a una lista de usuarios.
    Busca el FCM token de cada usuario y envía la notificación.

    Args:
        user_ids: Lista de user_id enteros
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Payload adicional
    """
    from app.models.fcm_token import FcmToken

    for uid in user_ids:
        fcm_record = FcmToken.query.filter_by(user_id=uid).first()
        if not fcm_record:
            logger.debug(f"No FCM token for user {uid}, skipping")
            continue
        send_notification(fcm_record.token, title, body, data)
