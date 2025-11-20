from flask import Blueprint, request, jsonify
from app.services.predict_service import predict_episode
import os
import json
from kafka import KafkaProducer

predict_bp = Blueprint('predict', __name__)

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
EVENT_TOPIC = os.getenv('EVENT_TOPIC', 'event-bus')

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@predict_bp.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    required_fields = ['glucose', 'insulin_30min', 'carbs_30min', 'user_id']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Faltan campos requeridos: {', '.join(missing)}"}), 400
    try:
        glucose = float(data['glucose'])
        insulin_30min = float(data['insulin_30min'])
        carbs_30min = float(data['carbs_30min'])
        user_id = data['user_id']
        heart_rate = float(data.get('heart_rate', 70))
        calories_15min = float(data.get('calories_15min', 5))
        steps_15min = int(data.get('steps_15min', 50))
        hour = int(data.get('hour')) if 'hour' in data else None
    except Exception as e:
        return jsonify({"error": f"Error en el formato de entrada: {str(e)}"}), 400
    result = predict_episode(
        glucose=glucose,
        insulin_30min=insulin_30min,
        carbs_30min=carbs_30min,
        heart_rate=heart_rate,
        calories_15min=calories_15min,
        steps_15min=steps_15min,
        hour=hour
    )
    # Emitir evento de alerta
    alert_event = {
        "type": "alert.created",
        "user_id": user_id,
        "alert": {
            "prediction": result.get('prediction'),
            "alert_level": result.get('alert_level'),
            "recommendation": result.get('recommendation'),
            "probabilities": result.get('probabilities'),
            "timestamp": data.get('timestamp')
        }
    }
    producer.send(EVENT_TOPIC, alert_event)
    # Emitir evento de registro
    record_event = {
        "type": "record.created",
        "user_id": user_id,
        "record": {
            "glucose": glucose,
            "insulin_30min": insulin_30min,
            "carbs_30min": carbs_30min,
            "heart_rate": heart_rate,
            "calories_15min": calories_15min,
            "steps_15min": steps_15min,
            "hour": hour,
            "prediction": result.get('prediction'),
            "probabilities": result.get('probabilities'),
            "timestamp": data.get('timestamp')
        }
    }
    producer.send(EVENT_TOPIC, record_event)
    return jsonify(result)
