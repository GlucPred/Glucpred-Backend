from flask import Blueprint, request, jsonify
from app.services.predict_service import PredictionService
from app.middleware.auth_middleware import require_auth
from app.events.kafka_producer import publish_prediction_event
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('predict', __name__)

@bp.route('/predict', methods=['POST'])
@require_auth
def predict():
    """
    Predice episodio de glucosa en los próximos 10 minutos
    ---
    Requiere autenticación JWT
    
    Body:
    {
        "glucose": 120,           # mg/dL (obligatorio)
        "insulin_30min": 5,       # unidades (obligatorio)
        "carbs_30min": 30,        # gramos (obligatorio)
        "heart_rate": 75,         # bpm (opcional, default 70)
        "calories_15min": 5,      # kcal (opcional, default 5)
        "steps_15min": 50,        # pasos (opcional, default 50)
        "hour": 14                # hora del día (opcional, default actual)
    }
    
    Returns:
    {
        "prediction": "Normal",
        "probabilities": {...},
        "alert_level": "Bajo",
        "recommendation": "...",
        "input_summary": {...}
    }
    """
    data = request.get_json()
    
    # Validar campos obligatorios
    required_fields = ['glucose', 'insulin_30min', 'carbs_30min']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({
            "error": f"Faltan campos requeridos: {', '.join(missing)}"
        }), 400
    
    # Extraer y validar datos
    try:
        glucose = float(data['glucose'])
        insulin_30min = float(data['insulin_30min'])
        carbs_30min = float(data['carbs_30min'])
        heart_rate = float(data.get('heart_rate', 70))
        calories_15min = float(data.get('calories_15min', 5))
        steps_15min = int(data.get('steps_15min', 50))
        hour = int(data['hour']) if 'hour' in data else None
    except (ValueError, TypeError) as e:
        return jsonify({
            "error": f"Error en el formato de entrada: {str(e)}"
        }), 400
    
    # Realizar predicción
    result = PredictionService.predict_episode(
        glucose=glucose,
        insulin_30min=insulin_30min,
        carbs_30min=carbs_30min,
        heart_rate=heart_rate,
        calories_15min=calories_15min,
        steps_15min=steps_15min,
        hour=hour
    )
    
    # Si hay error en la predicción
    if 'error' in result:
        logger.error(f"Error en predicción: {result['error']}")
        return jsonify(result), 500
    
    # Obtener user_id del token JWT
    user_id = request.user_id
    
    # Emitir evento si hay alerta (no Normal o nivel > Bajo)
    if result['prediction'] != 'Normal' or result['alert_level'] != 'Bajo':
        try:
            publish_prediction_event(
                user_id=user_id,
                prediction=result['prediction'],
                alert_level=result['alert_level'],
                probabilities=result['probabilities'],
                recommendation=result['recommendation'],
                glucose=glucose,
                insulin_30min=insulin_30min,
                carbs_30min=carbs_30min
            )
            logger.info(f"Evento de predicción publicado para user_id={user_id}")
        except Exception as e:
            logger.error(f"Error al publicar evento: {str(e)}")
            # No fallar la request si falla Kafka
    
    return jsonify(result), 200


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Verificar que el modelo se puede cargar
        PredictionService.get_model()
        return jsonify({
            'status': 'healthy',
            'service': 'analysis-service',
            'model': 'loaded'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'analysis-service',
            'error': str(e)
        }), 503
