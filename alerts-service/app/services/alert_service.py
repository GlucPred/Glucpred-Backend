from datetime import datetime, timedelta
from app.models.alert import Alert
from app.extensions import db

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
