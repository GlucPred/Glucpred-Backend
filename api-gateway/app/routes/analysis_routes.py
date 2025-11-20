from flask import Blueprint, request, jsonify
import requests
import os
from flask import current_app

ANALYSIS_SERVICE_URL = os.getenv('ANALYSIS_SERVICE_URL', 'http://analysis-service:5000')

bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@bp.route('/predict', methods=['POST'])
def predict():
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    try:
        resp = requests.post(f"{ANALYSIS_SERVICE_URL}/api/analysis/predict", json=request.get_json(), headers=headers, timeout=10)
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        return jsonify({'error': f'No se pudo conectar a analysis-service: {str(e)}'}), 502
