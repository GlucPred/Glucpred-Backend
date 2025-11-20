from app.models import GlucoseRecord
from app.extensions import db
from app.events.kafka_producer import GlucoseEventProducer
from datetime import datetime, timedelta
from config.settings import Config
import logging

logger = logging.getLogger(__name__)


class RecordsService:
    """Service for managing glucose records"""
    
    @staticmethod
    def classify_glucose(value):
        """
        Classify glucose level based on value
        
        Args:
            value (float): Glucose value in mg/dL
            
        Returns:
            str: Classification ('bajo', 'normal', 'alto', 'critico')
        """
        if value < Config.GLUCOSE_LOW_THRESHOLD:
            return 'bajo'
        elif value <= Config.GLUCOSE_NORMAL_MAX:
            return 'normal'
        elif value <= 180:
            return 'alto'
        else:
            return 'critico'
    
    @staticmethod
    def create_record(user_id, glucose_value, measurement_time=None):
        """
        Create a new glucose measurement record from CGM
        
        Args:
            user_id (int): Patient's user ID
            glucose_value (float): Glucose value in mg/dL from CGM
            measurement_time (datetime, optional): Time of measurement from CGM. Defaults to now.
            
        Returns:
            tuple: (record_dict, error_message)
        """
        try:
            if glucose_value is None or glucose_value < 0:
                return None, 'Valor de glucosa inválido'
            
            # Parse measurement time if provided as string
            if measurement_time and isinstance(measurement_time, str):
                try:
                    measurement_time = datetime.fromisoformat(measurement_time.replace('Z', '+00:00'))
                except ValueError:
                    return None, 'Formato de fecha/hora inválido. Use ISO 8601 format'
            
            if measurement_time is None:
                measurement_time = datetime.utcnow()
            
            # Classify glucose level
            classification = RecordsService.classify_glucose(glucose_value)
            
            # Create record
            record = GlucoseRecord(
                user_id=user_id,
                glucose_value=glucose_value,
                measurement_time=measurement_time,
                classification=classification
            )
            
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"Created glucose record for user {user_id}: {glucose_value} mg/dL ({classification})")
            
            # Publish Kafka event for alerts-service
            try:
                producer = GlucoseEventProducer()
                producer.publish_glucose_recorded(
                    user_id=user_id,
                    record_id=record.id,
                    glucose_value=glucose_value,
                    classification=classification,
                    measurement_time=measurement_time
                )
            except Exception as e:
                logger.error(f"Failed to publish glucose event to Kafka: {e}")
                # No fallar la creación del registro si Kafka falla
            
            return record.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating glucose record: {e}")
            return None, str(e)
    
    @staticmethod
    def get_latest_record(user_id):
        """
        Get the most recent glucose record for a user
        
        Args:
            user_id (int): Patient's user ID
            
        Returns:
            tuple: (record_dict, error_message)
        """
        try:
            record = GlucoseRecord.query.filter_by(user_id=user_id)\
                .order_by(GlucoseRecord.measurement_time.desc())\
                .first()
            
            if not record:
                return None, 'No se encontraron registros de glucosa'
            
            return record.to_dict(), None
            
        except Exception as e:
            logger.error(f"Error getting latest record: {e}")
            return None, str(e)
    
    @staticmethod
    def get_records_by_timerange(user_id, hours=12):
        """
        Get glucose records for a specific time range
        
        Args:
            user_id (int): Patient's user ID
            hours (int): Number of hours to look back. Default 12.
            
        Returns:
            tuple: (list_of_records, error_message)
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            records = GlucoseRecord.query.filter(
                GlucoseRecord.user_id == user_id,
                GlucoseRecord.measurement_time >= cutoff_time
            ).order_by(GlucoseRecord.measurement_time.asc()).all()
            
            return [r.to_dict() for r in records], None
            
        except Exception as e:
            logger.error(f"Error getting records by timerange: {e}")
            return None, str(e)
    
    @staticmethod
    def get_records_history(user_id, limit=100, offset=0, start_date=None, end_date=None):
        """
        Get paginated glucose history with optional date filters
        
        Args:
            user_id (int): Patient's user ID
            limit (int): Number of records per page
            offset (int): Offset for pagination
            start_date (datetime, optional): Filter from this date
            end_date (datetime, optional): Filter until this date
            
        Returns:
            tuple: (dict with records and pagination info, error_message)
        """
        try:
            query = GlucoseRecord.query.filter_by(user_id=user_id)
            
            # Apply date filters if provided
            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(GlucoseRecord.measurement_time >= start_date)
            
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(GlucoseRecord.measurement_time <= end_date)
            
            # Get total count
            total = query.count()
            
            # Get paginated records
            records = query.order_by(GlucoseRecord.measurement_time.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return {
                'records': [r.to_dict() for r in records],
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }, None
            
        except Exception as e:
            logger.error(f"Error getting records history: {e}")
            return None, str(e)
    
    @staticmethod
    def get_statistics(user_id, hours=24):
        """
        Get glucose statistics for a time period
        
        Args:
            user_id (int): Patient's user ID
            hours (int): Number of hours to analyze
            
        Returns:
            tuple: (statistics_dict, error_message)
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            records = GlucoseRecord.query.filter(
                GlucoseRecord.user_id == user_id,
                GlucoseRecord.measurement_time >= cutoff_time
            ).all()
            
            if not records:
                return None, 'No hay suficientes datos para calcular estadísticas'
            
            values = [r.glucose_value for r in records]
            
            # Count by classification
            classifications = {}
            for r in records:
                classifications[r.classification] = classifications.get(r.classification, 0) + 1
            
            stats = {
                'period_hours': hours,
                'total_readings': len(records),
                'average': round(sum(values) / len(values), 1),
                'min': min(values),
                'max': max(values),
                'classifications': classifications,
                'last_reading': records[-1].to_dict() if records else None
            }
            
            return stats, None
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return None, str(e)
    
    @staticmethod
    def delete_record(record_id, user_id):
        """
        Delete a glucose record (only if it belongs to the user)
        
        Args:
            record_id (int): Record ID to delete
            user_id (int): User ID (for security)
            
        Returns:
            tuple: (success_bool, error_message)
        """
        try:
            record = GlucoseRecord.query.filter_by(id=record_id, user_id=user_id).first()
            
            if not record:
                return False, 'Registro no encontrado o no pertenece a este usuario'
            
            db.session.delete(record)
            db.session.commit()
            
            logger.info(f"Deleted glucose record {record_id} for user {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting record: {e}")
            return False, str(e)
