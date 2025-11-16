from kafka import KafkaProducer
import json
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Kafka producer
bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

try:
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    logger.info(f"Kafka producer initialized with servers: {bootstrap_servers}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka producer: {e}")
    producer = None


class EventProducer:
    """Kafka event producer for publishing domain events"""
    
    @classmethod
    def publish_doctor_profile_created(cls, user_id, profile_data):
        """
        Publish DoctorProfileCreated event
        
        Args:
            user_id (int): User ID
            profile_data (dict): Doctor profile data
        """
        if not producer:
            logger.warning("Kafka producer not available, event not published")
            return
        
        try:
            event = {
                'event_type': 'DoctorProfileCreated',
                'user_id': user_id,
                'profile': profile_data,
                'timestamp': profile_data.get('created_at')
            }
            
            # Send to profile-events topic
            future = producer.send(
                topic='profile-events',
                key=str(user_id),
                value=event
            )
            
            # Wait for confirmation (optional, for debugging)
            record_metadata = future.get(timeout=10)
            logger.info(f"DoctorProfileCreated event published for user {user_id} to topic {record_metadata.topic}")
            
        except Exception as e:
            logger.error(f"Error publishing DoctorProfileCreated event: {e}")
