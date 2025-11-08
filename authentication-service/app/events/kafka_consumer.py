from kafka import KafkaConsumer
import json
import logging
import os
import threading
from app.services import AuthService

logger = logging.getLogger(__name__)


class EventConsumer:
    """Kafka event consumer for subscribing to domain events"""
    
    _consumer = None
    _consumer_thread = None
    _running = False
    
    @classmethod
    def start(cls):
        """Start Kafka consumer in background thread"""
        if cls._running:
            logger.warning("Event consumer already running")
            return
        
        cls._running = True
        cls._consumer_thread = threading.Thread(target=cls._consume_events, daemon=True)
        cls._consumer_thread.start()
        logger.info("Event consumer thread started")
    
    @classmethod
    def _consume_events(cls):
        """Consume events from Kafka"""
        try:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            consumer = KafkaConsumer(
                'profile-events',
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='authentication-service-group',
                consumer_timeout_ms=1000  # Check running status every second
            )
            cls._consumer = consumer
            logger.info(f"Kafka consumer connected to {bootstrap_servers}, subscribed to 'profile-events'")
            
            while cls._running:
                try:
                    # Poll for messages
                    messages = consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, records in messages.items():
                        for record in records:
                            cls._handle_event(record.value)
                            
                except Exception as e:
                    logger.error(f"Error consuming message: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
        finally:
            if cls._consumer:
                cls._consumer.close()
                cls._consumer = None
    
    @classmethod
    def _handle_event(cls, event):
        """
        Handle incoming event
        
        Args:
            event (dict): Event data
        """
        event_type = event.get('event_type')
        
        if event_type == 'ProfileCreated':
            cls._handle_profile_created(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    @classmethod
    def _handle_profile_created(cls, event):
        """
        Handle ProfileCreated event
        
        Args:
            event (dict): Event data containing user_id and profile info
        """
        user_id = event.get('user_id')
        if not user_id:
            logger.error("ProfileCreated event missing user_id")
            return
        
        logger.info(f"Received ProfileCreated event for user {user_id}")
        
        # Mark user as having completed profile setup
        success, error = AuthService.mark_profile_complete(user_id)
        
        if success:
            logger.info(f"Successfully marked user {user_id} as profile complete")
        else:
            logger.error(f"Failed to mark user {user_id} as profile complete: {error}")
    
    @classmethod
    def stop(cls):
        """Stop Kafka consumer"""
        cls._running = False
        if cls._consumer_thread:
            cls._consumer_thread.join(timeout=5)
        if cls._consumer:
            cls._consumer.close()
            cls._consumer = None
        logger.info("Event consumer stopped")
