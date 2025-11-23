import json
import threading
from kafka import KafkaConsumer
from config.settings import Config
from app.services.alert_service import AlertService
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

class GlucoseEventConsumer:
    """
    Consumidor de Kafka que escucha eventos de nuevas mediciones de glucosa
    y predicciones del modelo ML, creando alertas automáticamente cuando es necesario.
    """
    
    def __init__(self, app):
        self.app = app
        self.consumer = None
        self.running = False
    
    def start(self):
        """Inicia el consumidor en un thread separado"""
        if self.running:
            logger.warning("Consumer already running")
            return
        
        self.running = True
        consumer_thread = threading.Thread(target=self._consume, daemon=True)
        consumer_thread.start()
        logger.info("Kafka consumer thread started")
    
    def _consume(self):
        """Loop principal del consumidor"""
        try:
            # Suscribirse a múltiples topics
            topics = [
                Config.KAFKA_TOPIC_GLUCOSE_RECORDED,
                'event-bus'  # Topic general para eventos de predicción
            ]
            
            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=Config.KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            logger.info(f"Connected to Kafka, listening to topics: {topics}")
            
            for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    event_data = message.value
                    event_type = event_data.get('type')
                    
                    # Manejar según tipo de evento
                    if event_type == 'prediction.created':
                        self._handle_prediction_event(event_data)
                    else:
                        # Evento de glucosa (sin field 'type')
                        self._handle_glucose_event(event_data)
                        
                except Exception as e:
                    logger.error(f"Error handling event: {e}")
        
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
    
    def _handle_prediction_event(self, event_data):
        """
        Procesa un evento de predicción del modelo ML.
        
        event_data esperado:
        {
            "type": "prediction.created",
            "user_id": 5,
            "timestamp": "2025-11-21T14:30:00",
            "data": {
                "prediction": "Hiperglucemia",
                "alert_level": "Alto",
                "probabilities": {...},
                "recommendation": "...",
                "inputs": {
                    "glucose": 185.0,
                    ...
                }
            }
        }
        """
        logger.info(f"Received prediction event: {event_data.get('type')}")
        
        user_id = event_data.get('user_id')
        data = event_data.get('data', {})
        
        prediction = data.get('prediction')
        alert_level = data.get('alert_level')
        probabilities = data.get('probabilities', {})
        recommendation = data.get('recommendation', '')
        glucose_value = data.get('inputs', {}).get('glucose')
        
        if not all([user_id, prediction, alert_level, glucose_value]):
            logger.warning(f"Incomplete prediction event data: {event_data}")
            return
        
        # Crear alerta solo si no es nivel Bajo
        with self.app.app_context():
            alert = AlertService.create_alert_from_prediction(
                user_id=user_id,
                prediction=prediction,
                alert_level=alert_level,
                probabilities=probabilities,
                recommendation=recommendation,
                glucose_value=glucose_value
            )
            
            if alert:
                logger.info(f"Prediction alert created: {alert.title} for user {user_id}")
            else:
                logger.debug(f"No alert needed for prediction level: {alert_level}")
    
    def _handle_glucose_event(self, event_data):
        """
        Procesa un evento de nueva medición de glucosa.
        
        event_data esperado:
        {
            "user_id": 5,
            "record_id": 123,
            "glucose_value": 185.0,
            "classification": "critico",
            "measurement_time": "2025-11-16T10:30:00"
        }
        """
        logger.info(f"Received glucose event: {event_data}")
        
        user_id = event_data.get('user_id')
        record_id = event_data.get('record_id')
        glucose_value = event_data.get('glucose_value')
        classification = event_data.get('classification')
        
        if not all([user_id, record_id, glucose_value, classification]):
            logger.warning(f"Incomplete event data: {event_data}")
            return
        
        # Alertas de glucosa deshabilitadas - solo usar predicciones ML
        # Las alertas se crean únicamente desde el analysis-service con predicciones
        logger.debug(f"Glucose event received but alert creation disabled: {glucose_value} mg/dL ({classification})")
        
        # with self.app.app_context():
        #     alert = AlertService.create_alert_from_glucose(
        #         user_id=user_id,
        #         glucose_value=glucose_value,
        #         glucose_record_id=record_id,
        #         classification=classification
        #     )
        #     
        #     if alert:
        #         logger.info(f"Alert created: {alert.title} for user {user_id}")
        #     else:
        #         logger.debug(f"No alert needed for normal glucose level: {glucose_value}")
    
    def stop(self):
        """Detiene el consumidor"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer stopped")
