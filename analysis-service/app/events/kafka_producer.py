"""
Kafka Producer para publicar eventos de predicción
"""

from kafka import KafkaProducer
from config.settings import Config
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Productor global (singleton)
_producer = None

def get_producer():
    """Obtener o crear productor de Kafka"""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Kafka producer conectado a {Config.KAFKA_BROKER}")
        except Exception as e:
            logger.error(f"Error al conectar con Kafka: {str(e)}")
            raise
    return _producer


def publish_prediction_event(
    user_id: int,
    prediction: str,
    alert_level: str,
    probabilities: dict,
    recommendation: str,
    glucose: float,
    insulin_30min: float,
    carbs_30min: float
):
    """
    Publica evento de predicción al event bus
    
    Args:
        user_id: ID del usuario
        prediction: "Normal", "Hipoglucemia" o "Hiperglucemia"
        alert_level: "Bajo", "Medio" o "Alto"
        probabilities: Diccionario con probabilidades
        recommendation: Mensaje de recomendación
        glucose: Nivel de glucosa usado
        insulin_30min: Insulina usada
        carbs_30min: Carbohidratos usados
    """
    try:
        producer = get_producer()
        
        # Construir evento
        event = {
            "type": "prediction.created",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "data": {
                "prediction": prediction,
                "alert_level": alert_level,
                "probabilities": probabilities,
                "recommendation": recommendation,
                "inputs": {
                    "glucose": glucose,
                    "insulin_30min": insulin_30min,
                    "carbs_30min": carbs_30min
                }
            }
        }
        
        # Publicar evento
        future = producer.send(Config.EVENT_TOPIC, value=event)
        future.get(timeout=10)  # Esperar confirmación
        
        logger.info(f"Evento publicado: {event['type']} para user_id={user_id}")
        
    except Exception as e:
        logger.error(f"Error al publicar evento: {str(e)}")
        raise
