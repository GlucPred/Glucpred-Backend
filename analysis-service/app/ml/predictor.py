"""
predictor.py — Self-contained inference module for GlucPred analysis-service.

Handles all model artifact formats:
  - Two-stage binary-split (v6+): {stage1, stage2_hypo, stage2_hyper, s2_mode="binary_split"}
  - Two-stage 3-class (v4-v5): {stage1, stage2, s2_mode="3class"}
  - Single-stage dict (v1-v3): {model, thresholds}
  - Legacy raw XGBClassifier (v0)
"""

import datetime
import logging

import joblib
import numpy as np
import pandas as pd

from app.ml.features import create_features, get_feature_columns

logger = logging.getLogger(__name__)

PRED_LABELS = {0: "Sin episodio", 1: "Futura hipoglucemia", 2: "Futura hiperglucemia"}
ALERT_THRESHOLDS = {"Bajo": 0.3, "Medio": 0.6}


class EpisodePredictor:
    """Load a trained GlucPred XGBoost model and make single-reading predictions."""

    def __init__(self, model_path: str):
        artifact = joblib.load(model_path)
        self.s2_mode = None

        if isinstance(artifact, dict) and "stage1" in artifact:
            self.two_stage = True
            self.stage1 = artifact["stage1"]
            self.s1_threshold = artifact.get("s1_threshold", 0.5)
            self.s2_thresholds = artifact.get("s2_thresholds", {"hypo": 0.5, "hyper": 0.5})
            self.s2_mode = artifact.get("s2_mode", "3class")
            self.model = None

            if self.s2_mode == "binary_split":
                raw_hypo = artifact["stage2_hypo"]
                raw_hyper = artifact["stage2_hyper"]
                self.stage2_hypo = raw_hypo if isinstance(raw_hypo, list) else [raw_hypo]
                self.stage2_hyper = raw_hyper if isinstance(raw_hyper, list) else [raw_hyper]
                self.stage2 = None
                self.s2_use_s1_proba = artifact.get("s2_use_s1_proba", False)
            else:
                self.stage2 = artifact.get("stage2")
                self.stage2_hypo = None
                self.stage2_hyper = None
                self.s2_use_s1_proba = False

        elif isinstance(artifact, dict) and "model" in artifact:
            self.two_stage = False
            self.model = artifact["model"]
            self.thresholds = artifact.get("thresholds", {0: 0.5, 1: 0.5, 2: 0.5})
            self.stage1 = self.stage2 = self.stage2_hypo = self.stage2_hyper = None
        else:
            self.two_stage = False
            self.model = artifact
            self.thresholds = {0: 0.5, 1: 0.5, 2: 0.5}
            self.stage1 = self.stage2 = self.stage2_hypo = self.stage2_hyper = None

        logger.info("Loaded model (two_stage=%s, s2_mode=%s)", self.two_stage, self.s2_mode)

    def predict_single(
        self,
        glucose: float,
        heart_rate: float = 70.0,
        calories: float = 5.0,
        steps: float = 50.0,
        hour: int = None,
        dayofweek: int = None,
        carbs: float = 0.0,
        insulin: float = 0.0,
    ) -> tuple:
        """
        Predict from a single current glucose reading + optional context.

        Builds a synthetic 2-hour history so that rolling-window features
        are computed correctly, then returns the last row's prediction.

        Returns:
            (label: str, probabilities: dict)
        """
        now = datetime.datetime.now()
        if hour is None:
            hour = now.hour
        if dayofweek is None:
            dayofweek = now.weekday()

        # Build 120-row synthetic history (1 row = 1 minute)
        timestamps = pd.date_range(end=now, periods=120, freq="1min")
        df = pd.DataFrame({
            "time": timestamps,
            "glucose": np.linspace(max(70.0, glucose - 5.0), glucose, 120),
            "heart_rate": float(heart_rate),
            "steps": float(steps),
            "calories": float(calories),
            "carbs": [float(carbs) if i >= 115 else 0.0 for i in range(120)],
            "insulin": [float(insulin) if i >= 115 else 0.0 for i in range(120)],
            "patient_id": "live",
            "dataset": "live",
        })

        try:
            df = create_features(df)
        except Exception as exc:
            logger.error("Feature engineering failed: %s", exc)
            return "Sin episodio", {"Normal": 1.0, "Hipoglucemia": 0.0, "Hiperglucemia": 0.0}

        # Add `index` column (present in training data via reset_index)
        df["index"] = df.index.astype(float)

        # Features added to features.py after v6 training — exclude from inference
        _POST_V6_FEATURES = {
            "dawn_hyper_risk", "dayofweek", "glucose_safe_range_position",
            "hour", "hyper_context_strength", "uncompensated_meal_rise",
        }

        feature_cols = [c for c in get_feature_columns(df) if c not in _POST_V6_FEATURES]
        X = df[feature_cols].fillna(0).values.astype(np.float32)

        if X.shape[0] == 0:
            return "Sin episodio", {"Normal": 1.0, "Hipoglucemia": 0.0, "Hiperglucemia": 0.0}

        # Use only the last row (most recent state)
        X_last = X[-1:, :]

        if self.two_stage:
            y_pred, probabilities = self._predict_two_stage(X_last)
            label = PRED_LABELS[int(y_pred[0])]
        else:
            probabilities = self.model.predict_proba(X_last)
            if self.thresholds:
                thresholds = np.array([self.thresholds.get(i, 0.5) for i in range(3)])
                scaled = probabilities / thresholds
                label = PRED_LABELS[int(np.argmax(scaled, axis=1)[0])]
            else:
                label = PRED_LABELS[int(np.argmax(probabilities, axis=1)[0])]

        probs = probabilities[0]
        probs_dict = {
            "Normal": float(probs[0]),
            "Hipoglucemia": float(probs[1]),
            "Hiperglucemia": float(probs[2]),
        }
        return label, probs_dict

    def _predict_two_stage(self, X: np.ndarray) -> tuple:
        proba_s1 = self.stage1.predict_proba(X)[:, 1]
        ep_mask = proba_s1 >= self.s1_threshold

        y_pred = np.zeros(len(X), dtype=int)
        prob_normal = 1.0 - proba_s1
        prob_hypo = np.zeros(len(X))
        prob_hyper = np.zeros(len(X))

        if ep_mask.sum() > 0:
            if self.s2_mode == "binary_split":
                t_hypo = self.s2_thresholds.get("hypo", 0.5)
                t_hyper = self.s2_thresholds.get("hyper", 0.5)
                X_ep = X[ep_mask]
                if self.s2_use_s1_proba:
                    X_ep = np.hstack([X_ep, proba_s1[ep_mask].reshape(-1, 1)])
                p_h = np.mean([m.predict_proba(X_ep)[:, 1] for m in self.stage2_hypo], axis=0)
                p_hr = np.mean([m.predict_proba(X_ep)[:, 1] for m in self.stage2_hyper], axis=0)

                ep_preds = np.zeros(ep_mask.sum(), dtype=int)
                ep_preds[p_hr >= t_hyper] = 2
                ep_preds[p_h >= t_hypo] = 1  # hypo overrides hyper
                y_pred[ep_mask] = ep_preds
                prob_hypo[ep_mask] = proba_s1[ep_mask] * p_h
                prob_hyper[ep_mask] = proba_s1[ep_mask] * p_hr
            else:
                proba_s2 = self.stage2.predict_proba(X[ep_mask])
                n_s2 = proba_s2.shape[1]
                if n_s2 == 3:
                    t_n = self.s2_thresholds.get("normal", 0.5)
                    t_h = self.s2_thresholds.get("hypo", 0.5)
                    t_hr = self.s2_thresholds.get("hyper", 0.5)
                    scaled = proba_s2 / np.array([t_n, t_h, t_hr])
                    y_pred[ep_mask] = np.argmax(scaled, axis=1)
                    prob_hypo[ep_mask] = proba_s1[ep_mask] * proba_s2[:, 1]
                    prob_hyper[ep_mask] = proba_s1[ep_mask] * proba_s2[:, 2]
                else:
                    t_h = self.s2_thresholds.get("hypo", 0.5)
                    t_hr = self.s2_thresholds.get("hyper", 0.5)
                    s2_pred = np.where(proba_s2[:, 0] / t_h >= proba_s2[:, 1] / t_hr, 0, 1)
                    y_pred[ep_mask] = s2_pred + 1
                    prob_hypo[ep_mask] = proba_s1[ep_mask] * proba_s2[:, 0]
                    prob_hyper[ep_mask] = proba_s1[ep_mask] * proba_s2[:, 1]

        return y_pred, np.column_stack([prob_normal, prob_hypo, prob_hyper])
