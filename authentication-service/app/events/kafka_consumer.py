from kafka import KafkaConsumer
import json
import logging
import os
import threading

logger = logging.getLogger(__name__)


class EventConsumer:
    """Kafka event consumer for subscribing to domain events"""
    
    _consumer = None
    _consumer_thread = None
    _running = False
    _app = None
    
    @classmethod
    def start(cls, app):
        """
        Start Kafka consumer in background thread
        
        Args:
            app: Flask application instance (needed for app context)
        """
        if cls._running:
            logger.warning("Event consumer already running")
            return
        
        cls._app = app
        cls._running = True
        cls._consumer_thread = threading.Thread(target=cls._consume_events, daemon=True)
        cls._consumer_thread.start()
        logger.info("Event consumer thread started")
    
    @classmethod
    def _consume_events(cls):
        """Consume events from Kafka"""
        try:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            logger.info(f"Attempting to connect to Kafka at {bootstrap_servers}")
            
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
            logger.info(f"Kafka consumer connected successfully, subscribed to 'profile-events'")
            
            while cls._running:
                try:
                    # Poll for messages
                    messages = consumer.poll(timeout_ms=1000)
                    
                    if messages:
                        logger.info(f"Received {sum(len(records) for records in messages.values())} message(s)")
                    
                    for topic_partition, records in messages.items():
                        for record in records:
                            logger.info(f"Processing message from offset {record.offset}")
                            # Process each message with app context
                            if cls._app:
                                with cls._app.app_context():
                                    cls._handle_event(record.value)
                            else:
                                logger.error("Flask app not available")
                            
                except Exception as e:
                    logger.error(f"Error consuming message: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}", exc_info=True)
        finally:
            if cls._consumer:
                cls._consumer.close()
                cls._consumer = None
                logger.info("Kafka consumer closed")
    
    @classmethod
    def _handle_event(cls, event):
        """
        Handle incoming event
        
        Args:
            event (dict): Event data
        """
        event_type = event.get('event_type')
        logger.info(f"Handling event: {event_type}")
        
        if event_type == 'ProfileCreated':
            cls._handle_profile_created(event)
        elif event_type == 'DoctorProfileCreated':
            cls._handle_profile_created(event)  # Same logic for doctor profiles
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
        logger.info(f"ProfileCreated event data: {event}")
        
        if not user_id:
            logger.error("ProfileCreated event missing user_id")
            return
        
        logger.info(f"Processing ProfileCreated event for user {user_id}")
        
        # Import here to avoid circular imports
        from app.services import AuthService
        
        try:
            # Mark user as having completed profile setup
            logger.info(f"Calling mark_profile_complete for user {user_id}")
            success, error = AuthService.mark_profile_complete(user_id)
            
            if success:
                logger.info(f"✅ Successfully marked user {user_id} as profile complete")
            else:
                logger.error(f"❌ Failed to mark user {user_id} as profile complete: {error}")
        except Exception as e:
            logger.error(f"Exception while handling ProfileCreated: {e}", exc_info=True)
    
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
