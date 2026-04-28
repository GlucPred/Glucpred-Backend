from flask import Blueprint, request, jsonify
import requests
import os
from datetime import datetime

ANALYSIS_SERVICE_URL = os.getenv('ANALYSIS_SERVICE_URL', 'http://analysis-service:5000')
RECORDS_SERVICE_URL = os.getenv('RECORDS_SERVICE_URL', 'http://records-service:8085')

bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@bp.route('/predict', methods=['POST'])
def predict():
    """
    Predice episodio de glucosa en los próximos 10 minutos
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - glucose
            - insulin_30min
            - carbs_30min
          properties:
            glucose:
              type: number
              description: Nivel actual de glucosa (mg/dL)
              example: 120
            insulin_30min:
              type: number
              description: Insulina administrada en últimos 30 min (unidades)
              example: 5
            carbs_30min:
              type: number
              description: Carbohidratos consumidos en últimos 30 min (gramos)
              example: 30
            heart_rate:
              type: number
              description: Ritmo cardíaco actual (bpm)
              example: 75
              default: 70
            calories_15min:
              type: number
              description: Calorías quemadas últimos 15 min
              example: 5
              default: 5
            steps_15min:
              type: integer
              description: Pasos dados últimos 15 min
              example: 50
              default: 50
            hour:
              type: integer
              description: Hora del día (0-23)
              example: 14
    responses:
      200:
        description: Predicción exitosa
        schema:
          type: object
          properties:
            prediction:
              type: string
              enum: [Normal, Hipoglucemia, Hiperglucemia]
            probabilities:
              type: object
              properties:
                Normal:
                  type: number
                Hipoglucemia:
                  type: number
                Hiperglucemia:
                  type: number
            alert_level:
              type: string
              enum: [Bajo, Medio, Alto]
            recommendation:
              type: string
            input_summary:
              type: object
      400:
        description: Datos inválidos
      401:
        description: No autenticado
      500:
        description: Error en predicción
      502:
        description: Servicio no disponible
    """
    # Copiar headers (incluido Authorization)
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    data = request.get_json()
    
    # Validar que glucose esté presente
    if 'glucose' not in data:
        return jsonify({'error': 'El campo glucose es requerido'}), 400
    
    try:
        # 1. Guardar la lectura de glucosa en records-service
        glucose_data = {
            'glucose_value': data['glucose'],
            'measurement_time': datetime.utcnow().isoformat() + 'Z'
        }
        
        glucose_resp = requests.post(
            f"{RECORDS_SERVICE_URL}/api/records/",
            json=glucose_data,
            headers=headers,
            timeout=10,
            allow_redirects=False,
        )
        
        # Continuar incluso si falla el guardado de glucosa (logging)
        if glucose_resp.status_code != 201:
            print(f"Warning: Failed to save glucose record: {glucose_resp.status_code}")
        else:
            print(f"Glucose record saved successfully")
        
        # 2. Realizar la predicción en analysis-service
        resp = requests.post(
            f"{ANALYSIS_SERVICE_URL}/api/analysis/predict",
            json=data,
            headers=headers,
            timeout=10
        )
        return (resp.content, resp.status_code, resp.headers.items())
        
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Timeout al conectar con los servicios'
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'No se pudo conectar a los servicios'
        }), 502
    except Exception as e:
        return jsonify({
            'error': 'Error inesperado'
        }), 502
