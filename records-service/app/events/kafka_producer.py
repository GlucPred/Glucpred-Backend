import json
import logging
from kafka import KafkaProducer
from config.settings import Config

logger = logging.getLogger(__name__)

class GlucoseEventProducer:
    """
    Productor de Kafka que publica eventos cuando se registra una nueva medición de glucosa.
    """
    
    _instance = None
    _producer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlucoseEventProducer, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._producer is None:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',
                    retries=3
                )
                logger.info("Kafka producer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Kafka producer: {e}")
                self._producer = None
    
    def publish_glucose_recorded(self, user_id, record_id, glucose_value, classification, measurement_time):
        """
        Publica un evento cuando se registra una nueva medición de glucosa.
        
        Args:
            user_id: ID del usuario
            record_id: ID del registro de glucosa
            glucose_value: Valor de glucosa
            classification: Clasificación (bajo, normal, alto, critico)
            measurement_time: Hora de la medición
        """
        if not self._producer:
            logger.warning("Kafka producer not available, skipping event")
            return
        
        event = {
            'user_id': user_id,
            'record_id': record_id,
            'glucose_value': glucose_value,
            'classification': classification,
            'measurement_time': measurement_time.isoformat() if measurement_time else None
        }
        
        try:
            future = self._producer.send(Config.KAFKA_TOPIC_GLUCOSE_RECORDED, value=event)
            future.get(timeout=10)  # Esperar confirmación
            logger.info(f"Published glucose event for user {user_id}: {glucose_value} mg/dL ({classification})")
        except Exception as e:
            logger.error(f"Failed to publish glucose event: {e}")
    
    def close(self):
        """Cierra el productor"""
        if self._producer:
            self._producer.close()
            logger.info("Kafka producer closed")
