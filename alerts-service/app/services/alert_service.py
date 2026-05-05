from datetime import datetime, timedelta
from app.models.alert import Alert
from app.extensions import db
import logging
import requests
from config.settings import Config

logger = logging.getLogger(__name__)


def _get_doctor_ids_for_patient(patient_user_id: int) -> list:
    """Consulta doctor-patient-service para obtener los médicos del paciente."""
    try:
        url = f"{Config.DOCTOR_PATIENT_SERVICE_URL}/internal/doctors-by-patient/{patient_user_id}"
        resp = requests.get(url, headers={'X-Internal-Api-Key': Config.INTERNAL_API_KEY}, timeout=3)
        if resp.status_code == 200:
            return resp.json().get('doctor_ids', [])
    except Exception as e:
        logger.warning(f"Could not fetch doctors for patient {patient_user_id}: {e}")
    return []


def _notify_realtime(alert, patient_user_id: int):
    """
    Tras crear una alerta:
    1. Publica alert.created en Kafka → api-gateway emitirá vía Socket.IO
    2. Envía FCM push al paciente y a sus médicos asignados
    """
    try:
        from app.events.kafka_producer import publish_alert_created
        publish_alert_created(
            alert_id=alert.id,
            user_id=patient_user_id,
            title=alert.title,
            message=alert.message,
            severity=alert.severity,
            alert_type=alert.alert_type,
        )
    except Exception as e:
        logger.error(f"Kafka publish failed for alert {alert.id}: {e}")

    try:
        from app.services.fcm_service import send_alert_to_users
        recipient_ids = [patient_user_id] + _get_doctor_ids_for_patient(patient_user_id)
        send_alert_to_users(
            user_ids=recipient_ids,
            title=alert.title,
            body=alert.message,
            data={
                'alert_id': str(alert.id),
                'severity': alert.severity,
                'alert_type': alert.alert_type,
            }
        )
    except Exception as e:
        logger.error(f"FCM notification failed for alert {alert.id}: {e}")

class AlertService:
    """
    Servicio para crear y gestionar alertas automáticas basadas en 
    las mediciones de glucosa.
    """
    
    # Configuración de mensajes por tipo de alerta
    ALERT_TEMPLATES = {
        'hiperglucemia_critica': {
            'title': 'Hiperglucemia detectada',
            'message': 'Revisar medicación y consultar médico.',
            'severity': 'critico',
            'alert_type': 'critica'
        },
        'hiperglucemia_alta': {
            'title': 'Glucosa elevada',
            'message': 'Nivel de glucosa alto. Monitorear y evitar carbohidratos.',
            'severity': 'advertencia',
            'alert_type': 'critica'
        },
        'hipoglucemia_critica': {
            'title': 'Hipoglucemia severa',
            'message': 'Consumir 15g de carbohidratos rápidos inmediatamente.',
            'severity': 'critico',
            'alert_type': 'critica'
        },
        'hipoglucemia_leve': {
            'title': 'Hipoglucemia leve',
            'message': 'Consumir 15g de carbohidratos rápidos.',
            'severity': 'advertencia',
            'alert_type': 'critica'
        }
    }
    
    @staticmethod
    def create_alert_from_glucose(user_id, glucose_value, glucose_record_id, classification):
        """
        Crea una alerta basada en la clasificación de glucosa.
        
        Clasificaciones:
        - critico: > 180 mg/dL (Hiperglucemia crítica)
        - alto: 140-180 mg/dL (Hiperglucemia alta)
        - bajo: < 70 mg/dL (Hipoglucemia)
        - normal: 70-140 mg/dL (Sin alerta)
        
        Args:
            user_id: ID del usuario
            glucose_value: Valor de glucosa medido
            glucose_record_id: ID del registro de glucosa
            classification: 'critico', 'alto', 'bajo', 'normal'
        
        Returns:
            Alert object o None si no requiere alerta
        """
        template = None
        
        # Determinar tipo de alerta según clasificación
        if classification == 'critico' and glucose_value > 180:
            template = AlertService.ALERT_TEMPLATES['hiperglucemia_critica']
        elif classification == 'alto':
            template = AlertService.ALERT_TEMPLATES['hiperglucemia_alta']
        elif classification == 'bajo' and glucose_value < 50:
            template = AlertService.ALERT_TEMPLATES['hipoglucemia_critica']
        elif classification == 'bajo':
            template = AlertService.ALERT_TEMPLATES['hipoglucemia_leve']
        else:
            # No crear alerta para niveles normales
            return None
        
        # Verificar si ya existe una alerta similar reciente (última hora)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        existing_alert = Alert.query.filter(
            Alert.user_id == user_id,
            Alert.title == template['title'],
            Alert.created_at >= one_hour_ago,
            Alert.is_dismissed == False
        ).first()
        
        if existing_alert:
            # No duplicar alertas del mismo tipo en la última hora
            return existing_alert
        
        # Crear nueva alerta
        alert = Alert(
            user_id=user_id,
            glucose_record_id=glucose_record_id,
            glucose_value=glucose_value,
            alert_type=template['alert_type'],
            severity=template['severity'],
            title=template['title'],
            message=template['message']
        )
        
        db.session.add(alert)
        db.session.commit()
        
        _notify_realtime(alert, user_id)
        
        return alert
    
    @staticmethod
    def create_alert_from_prediction(user_id, prediction, alert_level, probabilities, recommendation, glucose_value):
        """
        Crea una alerta basada en la predicción del modelo ML.
        
        Args:
            user_id: ID del usuario
            prediction: "Normal", "Hipoglucemia" o "Hiperglucemia"
            alert_level: "Bajo", "Medio" o "Alto"
            probabilities: Dict con probabilidades de cada clase
            recommendation: Mensaje de recomendación
            glucose_value: Valor de glucosa usado en la predicción
        
        Returns:
            Alert object o None si alert_level es Bajo
        """
        # No crear alerta si es nivel Bajo
        if alert_level == "Bajo":
            return None
        
        # Mapear predicción a tipo de alerta
        alert_type = 'critica'
        
        # Determinar severidad
        if alert_level == "Alto":
            severity = 'critico'
        elif alert_level == "Medio":
            severity = 'advertencia'
        else:
            severity = 'info'
        
        # Generar título basado en la predicción
        if prediction == "Hiperglucemia":
            title = "Posible Hiperglucemia"
        elif prediction == "Hipoglucemia":
            title = "Posible Hipoglucemia"
        else:
            title = f"Predicción: {prediction}"
        
        # Construir mensaje con probabilidades
        prob_text = "\n".join([
            f"• {clase}: {prob*100:.1f}%"
            for clase, prob in probabilities.items()
        ])
        
        message = f"{recommendation}\n\nProbabilidades:\n{prob_text}\n\nNivel de glucosa actual: {glucose_value} mg/dL"
        
        # No verificar duplicados - cada predicción es única y debe registrarse
        # El usuario puede tener múltiples predicciones del mismo tipo en diferentes momentos
        
        # Crear nueva alerta
        alert = Alert(
            user_id=user_id,
            glucose_record_id=None,  # Las predicciones no tienen record_id
            glucose_value=glucose_value,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message
        )
        
        db.session.add(alert)
        db.session.commit()
        
        _notify_realtime(alert, user_id)
        
        return alert
    
    @staticmethod
    def create_reminder(user_id, title, message):
        """
        Crea un recordatorio manual (no basado en glucosa).
        
        Args:
            user_id: ID del usuario
            title: Título del recordatorio
            message: Mensaje del recordatorio
        
        Returns:
            Alert object
        """
        alert = Alert(
            user_id=user_id,
            alert_type='recordatorio',
            severity='info',
            title=title,
            message=message
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return alert
    
    @staticmethod
    def get_user_alerts(user_id, alert_type=None, severity=None, is_read=None, limit=100, offset=0):
        """
        Obtiene las alertas de un usuario con filtros opcionales.
        
        Args:
            user_id: ID del usuario
            alert_type: Filtrar por tipo ('critica', 'recordatorio', None=todas)
            severity: Filtrar por severidad ('critico', 'advertencia', 'info', None=todas)
            is_read: Filtrar por leídas (True, False, None=todas)
            limit: Número máximo de resultados
            offset: Desplazamiento para paginación
        
        Returns:
            Lista de alertas
        """
        query = Alert.query.filter(
            Alert.user_id == user_id,
            Alert.is_dismissed == False
        )
        
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        if is_read is not None:
            query = query.filter(Alert.is_read == is_read)
        
        # Ordenar por más recientes primero
        query = query.order_by(Alert.created_at.desc())
        
        total = query.count()
        alerts = query.limit(limit).offset(offset).all()
        
        return alerts, total
    
    @staticmethod
    def mark_as_read(alert_id, user_id):
        """
        Marca una alerta como leída.
        """
        alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()
        
        if not alert:
            return None
        
        alert.is_read = True
        alert.read_at = datetime.utcnow()
        db.session.commit()
        
        return alert
    
    @staticmethod
    def mark_all_as_read(user_id):
        """
        Marca todas las alertas de un usuario como leídas.
        """
        alerts = Alert.query.filter_by(user_id=user_id, is_read=False).all()
        
        for alert in alerts:
            alert.is_read = True
            alert.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return len(alerts)
    
    @staticmethod
    def dismiss_alert(alert_id, user_id):
        """
        Descarta/elimina una alerta.
        """
        alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()
        
        if not alert:
            return None
        
        alert.is_dismissed = True
        alert.dismissed_at = datetime.utcnow()
        db.session.commit()
        
        return alert
    
    @staticmethod
    def get_unread_count(user_id):
        """
        Obtiene el número de alertas no leídas de un usuario.
        """
        count = Alert.query.filter_by(
            user_id=user_id,
            is_read=False,
            is_dismissed=False
        ).count()
        
        return count
    
    @staticmethod
    def get_critical_alerts_count(user_id, hours=24):
        """
        Obtiene el número de alertas críticas en las últimas X horas.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        count = Alert.query.filter(
            Alert.user_id == user_id,
            Alert.alert_type == 'critica',
            Alert.severity == 'critico',
            Alert.created_at >= cutoff_time,
            Alert.is_dismissed == False
        ).count()
        
        return count
