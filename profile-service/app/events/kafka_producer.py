from kafka import KafkaProducer
import json
import logging
import os

logger = logging.getLogger(__name__)


class EventProducer:
    """Kafka event producer for publishing domain events"""
    
    _producer = None
    
    @classmethod
    def get_producer(cls):
        """Get or create Kafka producer instance"""
        if cls._producer is None:
            try:
                bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
                cls._producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas
                    retries=3
                )
                logger.info(f"Kafka producer connected to {bootstrap_servers}")
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                cls._producer = None
        return cls._producer
    
    @classmethod
    def publish_profile_created(cls, user_id, profile_data):
        """
        Publish ProfileCreated event
        
        Args:
            user_id (int): User ID
            profile_data (dict): Profile information
        """
        producer = cls.get_producer()
        if not producer:
            logger.warning("Kafka producer not available, event not published")
            return
        
        event = {
            'event_type': 'ProfileCreated',
            'user_id': user_id,
            'profile': profile_data,
            'timestamp': profile_data.get('created_at')
        }
        
        try:
            future = producer.send(
                topic='profile-events',
                key=str(user_id),
                value=event
            )
            # Wait for confirmation (optional, for reliability)
            future.get(timeout=10)
            logger.info(f"Published ProfileCreated event for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to publish ProfileCreated event: {e}")
    
    @classmethod
    def close(cls):
        """Close Kafka producer connection"""
        if cls._producer:
            cls._producer.close()
            cls._producer = None
