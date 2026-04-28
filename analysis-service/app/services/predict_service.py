"""
Servicio de predicción de episodios de glucosa.

Modelo: XGBoost dos etapas — F1-macro = 0.9095
  Stage1: Normal vs Episodio  |  Stage2: Hipoglucemia vs Hiperglucemia

Integración con Health Connect:
- heart_rate: Promedio últimos 5 min
- steps_15min: Pasos acumulados en últimos 15 min
- calories_15min: Calorías quemadas en últimos 15 min

Datos manuales del usuario:
- glucose: Último valor de glucosa (mg/dL)
- insulin_30min: Insulina total en últimos 30 min (unidades)
- carbs_30min: Carbohidratos totales en últimos 30 min (gramos)

Frecuencia: Ejecutado cada 5 minutos desde la app móvil.
"""

import logging
from datetime import datetime

from config.settings import Config
from app.ml.predictor import EpisodePredictor

logger = logging.getLogger(__name__)

# Etiquetas internas del modelo → etiquetas que espera el API
_LABEL_MAP = {
    "Sin episodio": "Normal",
    "Futura hipoglucemia": "Hipoglucemia",
    "Futura hiperglucemia": "Hiperglucemia",
    # Compatibilidad si el predictor ya devuelve etiquetas en español
    "Normal": "Normal",
    "Hipoglucemia": "Hipoglucemia",
    "Hiperglucemia": "Hiperglucemia",
}


class PredictionService:
    """Servicio para predecir episodios de glucosa usando EpisodePredictor."""

    _predictor: EpisodePredictor | None = None

    @classmethod
    def get_predictor(cls) -> EpisodePredictor:
        """Carga el predictor de forma lazy (singleton)."""
        if cls._predictor is None:
            try:
                cls._predictor = EpisodePredictor(Config.MODEL_PATH)
                logger.info("Predictor cargado desde %s", Config.MODEL_PATH)
            except Exception as exc:
                logger.error("Error al cargar predictor: %s", exc)
                raise
        return cls._predictor

    @classmethod
    def predict_episode(
        cls,
        glucose: float,
        insulin_30min: float,
        carbs_30min: float,
        heart_rate: float = 70,
        calories_15min: float = 5,
        steps_15min: int = 50,
        hour: int = None,
    ) -> dict:
        """
        Predice un episodio de glucosa en los próximos 10 minutos.

        Args:
            glucose: Nivel actual de glucosa (mg/dL)
            insulin_30min: Insulina administrada en los últimos 30 min (UI)
            carbs_30min: Carbohidratos consumidos en los últimos 30 min (g)
            heart_rate: Ritmo cardíaco actual (bpm); default 70
            calories_15min: Calorías quemadas en los últimos 15 min; default 5
            steps_15min: Pasos dados en los últimos 15 min; default 50
            hour: Hora del día (0-23); default hora actual del sistema

        Returns:
            dict con prediction, probabilities, alert_level, recommendation,
            input_summary.
        """
        try:
            predictor = cls.get_predictor()
        except Exception:
            return {"error": "No se pudo cargar el modelo de predicción"}

        if hour is None:
            hour = datetime.now().hour

        try:
            raw_label, probs_dict = predictor.predict_single(
                glucose=float(glucose),
                heart_rate=float(heart_rate),
                calories=float(calories_15min),
                steps=float(steps_15min),
                hour=int(hour),
                carbs=float(carbs_30min),
                insulin=float(insulin_30min),
            )
        except Exception as exc:
            logger.error("Error durante la predicción: %s", exc)
            return {"error": f"Error al predecir: {exc}"}

        prediction = _LABEL_MAP.get(raw_label, raw_label)

        # Clinical override: if glucose is already outside safe range the patient
        # is in an active episode regardless of the model's future-trajectory output.
        HYPO_THRESHOLD = 70.0
        HYPER_THRESHOLD = 180.0
        if glucose < HYPO_THRESHOLD:
            prediction = "Hipoglucemia"
            # Redistribute probabilities to reflect active hypoglycemia
            p_normal = probs_dict.get("Normal", 0.0)
            probs_dict = {
                "Normal": 0.0,
                "Hipoglucemia": probs_dict.get("Hipoglucemia", 0.0) + p_normal,
                "Hiperglucemia": probs_dict.get("Hiperglucemia", 0.0),
            }
        elif glucose > HYPER_THRESHOLD:
            prediction = "Hiperglucemia"
            # Redistribute probabilities to reflect active hyperglycemia
            p_normal = probs_dict.get("Normal", 0.0)
            probs_dict = {
                "Normal": 0.0,
                "Hipoglucemia": probs_dict.get("Hipoglucemia", 0.0),
                "Hiperglucemia": probs_dict.get("Hiperglucemia", 0.0) + p_normal,
            }

        # Nivel de alerta basado en probabilidad máxima de episodio (v6)
        max_ep_prob = max(probs_dict.get("Hipoglucemia", 0.0), probs_dict.get("Hiperglucemia", 0.0))
        if max_ep_prob >= 0.6:
            alert_level = "Alto"
        elif max_ep_prob >= 0.3:
            alert_level = "Medio"
        else:
            alert_level = "Bajo"

        # Recomendación clínica
        hypo_pct = probs_dict.get("Hipoglucemia", 0.0) * 100
        hyper_pct = probs_dict.get("Hiperglucemia", 0.0) * 100
        normal_pct = probs_dict.get("Normal", 0.0) * 100

        if prediction == "Hipoglucemia":
            recommendation = (
                f"⚠️ RIESGO DE HIPOGLUCEMIA ({hypo_pct:.1f}%)\n"
                "→ Consumir 15-20 g de carbohidratos de acción rápida\n"
                "→ Verificar glucosa en 15 minutos"
            )
        elif prediction == "Hiperglucemia":
            recommendation = (
                f"⚠️ RIESGO DE HIPERGLUCEMIA ({hyper_pct:.1f}%)\n"
                "→ Revisar administración de insulina\n"
                "→ Considerar actividad física ligera\n"
                "→ Monitorear glucosa cada 30 minutos"
            )
        else:
            recommendation = (
                f"✅ Glucosa se mantendrá NORMAL ({normal_pct:.1f}%)\n"
                "→ Continuar monitoreo regular"
            )

        return {
            "prediction": prediction,
            "probabilities": probs_dict,
            "alert_level": alert_level,
            "recommendation": recommendation,
            "input_summary": {
                "glucose": glucose,
                "insulin_30min": insulin_30min,
                "carbs_30min": carbs_30min,
                "hour": hour,
            },
        }
