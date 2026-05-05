import json
import logging
from kafka import KafkaProducer
from config.settings import Config

logger = logging.getLogger(__name__)

_producer = None


def _get_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
    return _producer


def publish_alert_created(alert_id: int, user_id: int, doctor_ids: list,
                          title: str, message: str, severity: str, alert_type: str):
    """
    Publica el evento alert.created en Kafka para que el api-gateway
    lo redistribuya vía Socket.IO al paciente y a sus médicos asignados.
    """
    try:
        payload = {
            'alert_id': alert_id,
            'user_id': user_id,
            'doctor_ids': doctor_ids,
            'title': title,
            'message': message,
            'severity': severity,
            'alert_type': alert_type,
        }
        _get_producer().send(Config.KAFKA_TOPIC_ALERT_CREATED, value=payload)
        _get_producer().flush()
        logger.info(f"Published alert.created for user {user_id}, alert {alert_id}")
    except Exception as e:
        logger.error(f"Failed to publish alert.created: {e}")
