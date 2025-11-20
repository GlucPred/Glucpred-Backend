import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../models/episode_predictor.joblib')

def get_model():
    if not hasattr(get_model, "model"):
        get_model.model = joblib.load(MODEL_PATH)
    return get_model.model

def predict_episode(
    glucose: float,
    insulin_30min: float,
    carbs_30min: float,
    heart_rate: float = 70,
    calories_15min: float = 5,
    steps_15min: int = 50,
    hour: int = None,
    model_path: str = MODEL_PATH
):
    try:
        model = get_model()
    except Exception as e:
        return {"error": f"No se pudo cargar el modelo: {str(e)}"}
    if hour is None:
        hour = datetime.now().hour
    glucose_change = -2 if insulin_30min > carbs_30min/10 else (3 if carbs_30min > insulin_30min*10 else 0)
    features = {
        'glucose_15min': glucose,
        'glucose_30min': glucose,
        'glucose_60min': glucose,
        'glucose_moderately_low': 1 if 70 <= glucose < 80 else 0,
        'glucose_trend_negative': 1 if glucose < 100 or insulin_30min > 5 else 0,
        'glucose_velocity': glucose_change,
        'glucose_change_15min': glucose_change * 15,
        'glucose_dropping_fast': 1 if glucose < 70 else 0,
        'glucose_low_range': 1 if glucose < 90 else 0,
        'glucose_trend': glucose_change,
        'glucose_dropping_moderate': 1 if glucose < 90 else 0,
        'glucose_range_15min': 10,
        'glucose_unstable': 0,
        'glucose_change_30min': glucose_change * 30,
        'glucose_std_15min': 5,
        'glucose_acceleration': 0,
        'glucose_acceleration_negative': 0,
        'glucose_rising_fast': 1 if glucose > 180 else 0,
        'glucose_hr_ratio': glucose / heart_rate if heart_rate > 0 else 0,
        'glucose_per_calorie': glucose / (calories_15min + 0.1),
        'glucose_per_steps': glucose / (steps_15min + 1),
        'calories': calories_15min * 4,
        'high_calorie_burn': 1 if calories_15min >= 15 else 0,
        'calories_15min': calories_15min,
        'calories_30min': calories_15min * 2,
        'calories_60min': calories_15min * 4,
        'calories_velocity': 0,
        'moderate_activity': 1 if 100 <= steps_15min < 200 else 0,
        'steps_60min': steps_15min * 4,
        'steps_30min': steps_15min * 2,
        'steps': steps_15min * 4,
        'steps_15min': steps_15min,
        'steps_velocity': 0,
        'high_activity': 1 if steps_15min >= 200 else 0,
        'low_activity': 1 if steps_15min < 50 else 0,
        'calorie_per_step': calories_15min / (steps_15min + 1),
        'heart_rate': heart_rate,
        'hr_30min': heart_rate,
        'hr_60min': heart_rate,
        'hr_very_low': 1 if heart_rate < 60 else 0,
        'hr_15min': heart_rate,
        'hr_elevated': 1 if 100 <= heart_rate < 120 else 0,
        'hr_activity_intensity': heart_rate / 180 if heart_rate > 0 else 0,
        'hr_std_15min': 3,
        'hr_trend': 0,
        'hour_sin': np.sin(2 * np.pi * hour / 24),
        'is_weekend': 1 if datetime.now().weekday() >= 5 else 0,
        'hour_cos': np.cos(2 * np.pi * hour / 24),
        'hour': hour,
        'dayofweek': datetime.now().weekday(),
        'hypo_risk_score': (insulin_30min / 10) - (carbs_30min / 50) + (1 if glucose < 100 else 0),
        'hypo_activity_risk': (1 if glucose < 100 else 0) * (1 if calories_15min > 10 else 0),
        'hypo_sedentary_risk': 0,
    }
    feature_order = [
        'calories', 'heart_rate', 'steps', 'hour', 'dayofweek', 'is_weekend',
        'hour_sin', 'hour_cos', 'glucose_15min', 'glucose_30min', 'glucose_60min',
        'glucose_std_15min', 'glucose_trend', 'glucose_velocity', 'glucose_acceleration',
        'glucose_unstable', 'glucose_dropping_fast', 'glucose_rising_fast',
        'glucose_low_range', 'glucose_moderately_low', 'glucose_dropping_moderate',
        'glucose_trend_negative', 'glucose_acceleration_negative', 'glucose_change_15min',
        'glucose_change_30min', 'glucose_range_15min', 'hypo_risk_score',
        'hr_15min', 'hr_30min', 'hr_60min', 'hr_std_15min', 'hr_trend',
        'hr_elevated', 'hr_very_low', 'steps_15min', 'steps_30min', 'steps_60min',
        'steps_velocity', 'low_activity', 'moderate_activity', 'high_activity',
        'calories_15min', 'calories_30min', 'calories_60min', 'calories_velocity',
        'high_calorie_burn', 'glucose_per_calorie', 'glucose_per_steps',
        'glucose_hr_ratio', 'calorie_per_step', 'hr_activity_intensity',
        'hypo_activity_risk', 'hypo_sedentary_risk'
    ]
    df = pd.DataFrame([features])[feature_order]
    try:
        prediction_class = model.predict(df)[0]
        probabilities = model.predict_proba(df)[0]
    except Exception as pred_error:
        return {
            "error": f"Error al predecir - Features incompatibles: {str(pred_error)}",
            "note": "El modelo requiere todas las features con las que fue entrenado"
        }
    class_labels = ['Normal', 'Hipoglucemia', 'Hiperglucemia']
    prediction = class_labels[prediction_class]
    probs_dict = {
        'Normal': float(probabilities[0]),
        'Hipoglucemia': float(probabilities[1]),
        'Hiperglucemia': float(probabilities[2])
    }
    max_prob = max(probabilities[1], probabilities[2])
    if max_prob > 0.7:
        alert_level = "Alto"
    elif max_prob > 0.4:
        alert_level = "Medio"
    else:
        alert_level = "Bajo"
    if prediction == 'Hipoglucemia':
        recommendation = f"⚠️ RIESGO DE HIPOGLUCEMIA ({probs_dict['Hipoglucemia']*100:.1f}%)\n"
        recommendation += "→ Consumir 15-20g carbohidratos de acción rápida\n"
        recommendation += "→ Verificar glucosa en 15 minutos"
    elif prediction == 'Hiperglucemia':
        recommendation = f"⚠️ RIESGO DE HIPERGLUCEMIA ({probs_dict['Hiperglucemia']*100:.1f}%)\n"
        recommendation += "→ Revisar administración de insulina\n"
        recommendation += "→ Considerar actividad física ligera\n"
        recommendation += "→ Monitorear glucosa cada 30 minutos"
    else:
        recommendation = f"✅ Glucosa se mantendrá NORMAL ({probs_dict['Normal']*100:.1f}%)\n"
        recommendation += "→ Continuar monitoreo regular"
    return {
        'prediction': prediction,
        'probabilities': probs_dict,
        'alert_level': alert_level,
        'recommendation': recommendation,
        'input_summary': {
            'glucose': glucose,
            'insulin_30min': insulin_30min,
            'carbs_30min': carbs_30min,
            'hour': hour
        }
    }
