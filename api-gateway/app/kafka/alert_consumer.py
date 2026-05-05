import json
import logging
import queue as stdlib_queue
from kafka import KafkaConsumer
from config.settings import Config

logger = logging.getLogger(__name__)


class AlertKafkaConsumer:
    """
    Consume el topic alert.created publicado por alerts-service
    y emite el evento alert:new vía Socket.IO a las salas correspondientes.

    Arquitectura de dos capas para compatibilidad con eventlet:
    - _consume() corre en un thread nativo OS via tpool (necesario para kafka-python
      bloqueante, que es incompatible con eventlet.monkey_patch).
    - _emit_worker() corre como greenlet en el event loop de eventlet, que es el
      único contexto donde socketio.emit() puede ejecutarse sin "Cannot switch to
      a different thread".
    - stdlib_queue.Queue actúa como puente thread-safe entre ambas capas.
    """

    def __init__(self, socketio):
        self.socketio = socketio
        self.running = False
        self._emit_queue = stdlib_queue.Queue()

    def start(self):
        if self.running:
            return
        self.running = True
        import eventlet
        # Emit worker: greenlet en el event loop de eventlet (seguro para socketio.emit)
        eventlet.spawn(self._emit_worker)
        # Kafka consumer: thread nativo OS via tpool (seguro para kafka-python)
        eventlet.spawn(self._run_in_tpool)
        logger.info("Alert Kafka consumer started (eventlet tpool + queue bridge)")

    def _emit_worker(self):
        """Greenlet en el event loop de eventlet — único contexto seguro para socketio.emit()."""
        import eventlet
        while self.running:
            try:
                item = self._emit_queue.get_nowait()
                room = item['room']
                data = item['data']
                self.socketio.emit('alert:new', data, room=room)
                logger.info(f"Emitted alert:new to room {room}: {data.get('title', '')}")
            except stdlib_queue.Empty:
                eventlet.sleep(0.05)  # cede el event loop sin quemar CPU
            except Exception as e:
                logger.error(f"Error emitting socket event: {e}")

    def _run_in_tpool(self):
        from eventlet import tpool
        tpool.execute(self._consume)

    def _consume(self):
        """Corre en thread nativo OS — NO llamar socketio.emit() aquí directamente."""
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

                    # Encolar emit al paciente (el greenlet _emit_worker lo ejecutará)
                    self._emit_queue.put({'room': f"user_{user_id}", 'data': data})

                    # Encolar emit a cada médico asignado
                    for doctor_id in data.get('doctor_ids', []):
                        self._emit_queue.put({'room': f"user_{doctor_id}", 'data': data})

                except Exception as e:
                    logger.error(f"Error queuing socket event: {e}")

        except Exception as e:
            logger.error(f"Alert Kafka consumer error: {e}")
