import json
import threading
import logging
from kafka import KafkaConsumer
from config.settings import Config

logger = logging.getLogger(__name__)


class AlertKafkaConsumer:
    """
    Consume el topic alert.created publicado por alerts-service
    y emite el evento alert:new vía Socket.IO a las salas correspondientes.
    """

    def __init__(self, socketio):
        self.socketio = socketio
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._consume, daemon=True)
        thread.start()
        logger.info("Alert Kafka consumer thread started")

    def _consume(self):
        try:
            consumer = KafkaConsumer(
                Config.KAFKA_TOPIC_ALERT_CREATED,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=Config.KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
            )
            logger.info(f"Listening to Kafka topic: {Config.KAFKA_TOPIC_ALERT_CREATED}")

            for message in consumer:
                if not self.running:
                    break
                try:
                    data = message.value
                    user_id = data.get('user_id')
                    if not user_id:
                        continue

                    # Emit to patient's room
                    patient_room = f"user_{user_id}"
                    self.socketio.emit('alert:new', data, room=patient_room)
                    logger.info(f"Emitted alert:new to room {patient_room}: {data.get('title')}")

                    # Emit to all assigned doctor rooms
                    for doctor_id in data.get('doctor_ids', []):
                        doctor_room = f"user_{doctor_id}"
                        self.socketio.emit('alert:new', data, room=doctor_room)
                        logger.info(f"Emitted alert:new to doctor room {doctor_room}")

                except Exception as e:
                    logger.error(f"Error emitting socket event: {e}")

        except Exception as e:
            logger.error(f"Alert Kafka consumer error: {e}")
