"""
features.py — Feature engineering for GlucPred v2.

Ported and cleaned from v1 data_utils.py. Creates ~52 features
from the unified 1-minute resampled CGM + wearable DataFrame.

Input:  preprocessed DataFrame with columns:
        [patient_id, time, glucose, heart_rate, steps, calories, carbs, insulin, dataset]

Output: same DataFrame + feature columns + target columns
"""

import logging
import math

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Medical thresholds
HYPO_THRESHOLD = 70.0      # mg/dL
HYPER_THRESHOLD = 180.0    # mg/dL
CAUTION_LOW = 80.0         # mg/dL — approaching hypo
CAUTION_HIGH = 160.0       # mg/dL — approaching hyper

# Prediction horizon
DEFAULT_HORIZON_MINUTES = 10   # minutes ahead to predict

# Rolling window sizes (in minutes = rows at 1-min resolution)
WINDOWS = {
    "15min":  15,
    "30min":  30,
    "60min":  60,
    "120min": 120,
}


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create all features for the XGBoost model.
    Processes each patient separately to avoid cross-patient leakage.

    Args:
        df: Preprocessed DataFrame (1-min resampled, one row per minute per patient).

    Returns:
        DataFrame with all feature columns appended.
    """
    patient_frames = []
    for pid, group in df.groupby("patient_id"):
        try:
            group = group.sort_values("time").copy()
            group = _add_temporal_features(group)
            group = _add_glucose_features(group)
            group = _add_heart_rate_features(group)
            group = _add_activity_features(group)
            group = _add_context_features(group)
            group = _add_interaction_features(group)
            patient_frames.append(group)
        except Exception as exc:
            logger.warning("Feature engineering failed for patient %s: %s", pid, exc)

    if not patient_frames:
        raise RuntimeError("Feature engineering produced no output.")

    result = pd.concat(patient_frames, ignore_index=True)

    # Fill remaining NaNs from rolling windows at edges with column medians
    feature_cols = get_feature_columns(result)
    medians = result[feature_cols].median()
    result[feature_cols] = result[feature_cols].fillna(medians)

    logger.info("Features created: %d rows, %d feature columns", len(result), len(feature_cols))
    return result


def create_targets(
    df: pd.DataFrame,
    horizon_minutes: int = DEFAULT_HORIZON_MINUTES,
) -> pd.DataFrame:
    """
    Create target variable for supervised learning.

    Looks `horizon_minutes` ahead and labels:
        0 = Normal (glucose stays 70–180)
        1 = Future hypoglycemia (glucose will drop below 70)
        2 = Future hyperglycemia (glucose will rise above 180)

    Also adds `is_predictive` flag: only rows where CURRENT glucose is
    in 70–180 range are used for training (we're predicting transitions).

    Args:
        df: DataFrame with features and a 'glucose' column.
        horizon_minutes: Number of minutes ahead to check.

    Returns:
        DataFrame with 'target', 'will_hypo', 'will_hyper', 'is_predictive' columns.
    """
    frames = []
    for pid, group in df.groupby("patient_id"):
        group = group.sort_values("time").copy()
        group = _add_targets_for_patient(group, horizon_minutes)
        frames.append(group)

    return pd.concat(frames, ignore_index=True)


def _add_targets_for_patient(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """
    Add target columns to a single patient's DataFrame.

    Uses the MINIMUM glucose over the next `horizon` minutes for hypo detection
    and MAXIMUM for hyper — this is more clinically meaningful than checking only
    at exactly t+horizon. A brief dip at t+5 that recovers by t+10 is still a
    real hypoglycemic event and should be labeled as such.
    """
    # Stack shifted glucose for all offsets 1..horizon in one concat
    future_cols = [df["glucose"].shift(-i) for i in range(1, horizon + 1)]
    future_df = pd.concat(future_cols, axis=1)

    future_min = future_df.min(axis=1)   # worst-case low across the window
    future_max = future_df.max(axis=1)   # worst-case high across the window

    df["will_hypo"]  = (future_min < HYPO_THRESHOLD).astype(int)
    df["will_hyper"] = (future_max > HYPER_THRESHOLD).astype(int)

    # Target: 0=normal, 1=hypo ahead, 2=hyper ahead (hypo takes priority if both)
    df["target"] = 0
    df.loc[df["will_hyper"] == 1, "target"] = 2
    df.loc[df["will_hypo"]  == 1, "target"] = 1   # hypo overrides hyper

    # Only train on rows where current glucose is in normal range
    df["is_predictive"] = df["glucose"].between(HYPO_THRESHOLD, HYPER_THRESHOLD).astype(int)

    # Drop last `horizon` rows (no future data available)
    df.iloc[-horizon:, df.columns.get_loc("target")] = np.nan
    df.iloc[-horizon:, df.columns.get_loc("is_predictive")] = 0

    return df


# ─────────────────────────────────────────────
# Feature groups
# ─────────────────────────────────────────────

def _add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """5 temporal features from the timestamp."""
    t = df["time"]
    df["hour"] = t.dt.hour
    df["dayofweek"] = t.dt.dayofweek
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df["hour_sin"] = np.sin(2 * math.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * math.pi * df["hour"] / 24)
    return df


def _add_glucose_features(df: pd.DataFrame) -> pd.DataFrame:
    """~45 glucose-based features including extrapolation, margin, and rolling min signals."""
    g = df["glucose"]

    # Rolling means
    for name, w in WINDOWS.items():
        df[f"glucose_{name}"] = g.rolling(w, min_periods=max(1, w // 2)).mean()

    # Rolling std (volatility)
    for name, w in [("15min", 15), ("30min", 30)]:
        df[f"glucose_std_{name}"] = g.rolling(w, min_periods=max(1, w // 2)).std()

    # Rolling min/max — critical: if glucose already dipped low, risk is real
    for name, w in [("15min", 15), ("30min", 30), ("60min", 60)]:
        df[f"glucose_min_{name}"] = g.rolling(w, min_periods=max(1, w // 2)).min()
        df[f"glucose_max_{name}"] = g.rolling(w, min_periods=max(1, w // 2)).max()

    # Coefficient of variation
    for name, w in [("15min", 15), ("30min", 30)]:
        roll_mean = g.rolling(w, min_periods=max(1, w // 2)).mean()
        roll_std = g.rolling(w, min_periods=max(1, w // 2)).std()
        df[f"glucose_cv_{name}"] = (roll_std / roll_mean.replace(0, np.nan)).fillna(0)

    # Trend (first derivative: change per minute)
    df["glucose_trend"] = g.diff(1)

    # Velocity (5-min slope)
    df["glucose_velocity"] = g.diff(5) / 5.0

    # Acceleration (second derivative)
    df["glucose_acceleration"] = df["glucose_trend"].diff(1)

    # Jerk (third derivative)
    df["glucose_jerk"] = df["glucose_acceleration"].diff(1)

    # Raw lags — give the model direct trajectory history
    for lag in [5, 10, 15, 30]:
        df[f"glucose_lag_{lag}"] = g.shift(lag)

    # Rate of change over windows
    for name, w in [("15min", 15), ("30min", 30), ("60min", 60)]:
        df[f"glucose_roc_{name}"] = (g - g.shift(w)) / w

    # Distance from current to past values
    for name, w in [("15min", 15), ("30min", 30), ("60min", 60)]:
        df[f"glucose_dist_{name}"] = (g - g.shift(w)).abs()

    # Linear extrapolation: current + velocity * horizon
    # This is the strongest predictive signal — directly estimates future glucose
    vel = df["glucose_velocity"]
    accel = df["glucose_acceleration"].fillna(0)
    df["glucose_extrap_5"]  = g + vel * 5
    df["glucose_extrap_10"] = g + vel * 10                     # matches prediction horizon
    df["glucose_extrap_15"] = g + vel * 15
    # Second-order extrapolation (with acceleration)
    df["glucose_extrap_10_accel"] = g + vel * 10 + 0.5 * accel * 100

    # Margin to thresholds — how far from danger zone
    df["margin_to_hypo"]  = g - HYPO_THRESHOLD          # negative → already hypo
    df["margin_to_hyper"] = HYPER_THRESHOLD - g          # negative → already hyper
    df["extrap_margin_to_hypo"]  = df["glucose_extrap_10"] - HYPO_THRESHOLD
    df["extrap_margin_to_hyper"] = HYPER_THRESHOLD - df["glucose_extrap_10"]

    # Minutes to threshold at current velocity (clipped to 60)
    safe_vel_down = vel.clip(upper=-0.01)   # only when declining
    safe_vel_up   = vel.clip(lower=0.01)    # only when rising
    df["minutes_to_hypo"]  = ((g - HYPO_THRESHOLD) / (-safe_vel_down)).clip(0, 60)
    df["minutes_to_hyper"] = ((HYPER_THRESHOLD - g) / safe_vel_up).clip(0, 60)
    # Set to 60 when velocity doesn't point toward threshold
    df.loc[vel >= 0, "minutes_to_hypo"]  = 60.0
    df.loc[vel <= 0, "minutes_to_hyper"] = 60.0

    # Direct prediction flags from extrapolation
    df["extrap_will_hypo"]  = (df["glucose_extrap_10"] < HYPO_THRESHOLD).astype(int)
    df["extrap_will_hyper"] = (df["glucose_extrap_10"] > HYPER_THRESHOLD).astype(int)

    # Extrapolation confidence — how far past the threshold (0 if not crossing)
    df["extrap_confidence_hypo"]  = (HYPO_THRESHOLD  - df["glucose_extrap_10"]).clip(lower=0)
    df["extrap_confidence_hyper"] = (df["glucose_extrap_10"] - HYPER_THRESHOLD).clip(lower=0)

    # Multi-horizon agreement — all 3 extrapolations agree on danger
    df["extrap_multi_agree_hypo"]  = (
        (df["glucose_extrap_5"]  < HYPO_THRESHOLD + 5) &
        (df["glucose_extrap_10"] < HYPO_THRESHOLD) &
        (df["glucose_extrap_15"] < HYPO_THRESHOLD - 5)
    ).astype(int)
    df["extrap_multi_agree_hyper"] = (
        (df["glucose_extrap_5"]  > HYPER_THRESHOLD - 5) &
        (df["glucose_extrap_10"] > HYPER_THRESHOLD) &
        (df["glucose_extrap_15"] > HYPER_THRESHOLD + 5)
    ).astype(int)

    # Rolling min proximity — if glucose recently dipped near threshold it's high risk
    df["glucose_min_15min_near_hypo"]  = (df["glucose_min_15min"] < CAUTION_LOW).astype(int)
    df["glucose_min_30min_near_hypo"]  = (df["glucose_min_30min"] < CAUTION_LOW + 5).astype(int)
    df["glucose_max_15min_near_hyper"] = (df["glucose_max_15min"] > CAUTION_HIGH).astype(int)

    # Consecutive direction
    diff1 = g.diff(1)
    df["consecutive_drops"] = (
        (diff1 < 0).astype(int)
        .groupby((diff1 >= 0).astype(int).cumsum())
        .cumsum()
    )
    df["consecutive_rises"] = (
        (diff1 > 0).astype(int)
        .groupby((diff1 <= 0).astype(int).cumsum())
        .cumsum()
    )

    # Risk indicators (binary flags)
    df["glucose_low_range"] = (g < CAUTION_LOW).astype(int)
    df["glucose_moderately_low"] = g.between(HYPO_THRESHOLD, CAUTION_LOW).astype(int)
    df["glucose_dropping_fast"] = (vel < -2.0).astype(int)
    df["glucose_dropping_moderate"] = vel.between(-2.0, -0.5).astype(int)
    df["glucose_rising_fast"] = (vel > 2.0).astype(int)
    df["glucose_trend_negative"] = (df["glucose_trend"] < 0).astype(int)

    # Momentum
    df["glucose_momentum"] = vel * df["consecutive_drops"]

    # Composite risk scores
    df["hypo_risk_score"] = (
        df["glucose_low_range"] * 3
        + df["glucose_moderately_low"] * 2
        + df["glucose_dropping_fast"] * 2
        + df["glucose_dropping_moderate"]
        + df["extrap_will_hypo"] * 5          # strong signal from extrapolation
    )
    df["hyper_risk_score"] = (
        (g > CAUTION_HIGH).astype(int) * 2
        + df["glucose_rising_fast"] * 2
        + (vel > 1.0).astype(int)
        + df["extrap_will_hyper"] * 5         # strong signal from extrapolation
    )

    return df


def _add_heart_rate_features(df: pd.DataFrame) -> pd.DataFrame:
    """9 heart rate features."""
    hr = df.get("heart_rate", pd.Series(70.0, index=df.index))
    hr = hr.fillna(70.0)

    for name, w in [("15min", 15), ("30min", 30), ("60min", 60)]:
        df[f"hr_{name}"] = hr.rolling(w, min_periods=1).mean()

    df["hr_std_15min"] = hr.rolling(15, min_periods=1).std().fillna(0)
    df["hr_variability"] = df["hr_std_15min"]

    df["hr_elevated"] = (hr > 100).astype(int)
    df["hr_very_low"] = (hr < 50).astype(int)

    df["hr_sudden_increase"] = (hr.diff(5) > 20).astype(int)
    df["hr_rapid_change"] = (hr.diff(1).abs() > 10).astype(int)

    return df


def _add_activity_features(df: pd.DataFrame) -> pd.DataFrame:
    """11 activity features (steps + calories)."""
    steps = df.get("steps", pd.Series(0.0, index=df.index)).fillna(0.0)
    cals = df.get("calories", pd.Series(0.0, index=df.index)).fillna(0.0)

    for name, w in [("15min", 15), ("30min", 30), ("60min", 60)]:
        df[f"steps_{name}"] = steps.rolling(w, min_periods=1).sum()
        df[f"calories_{name}"] = cals.rolling(w, min_periods=1).sum()

    df["steps_velocity"] = steps.diff(5) / 5.0
    df["calories_velocity"] = cals.diff(5) / 5.0

    df["low_activity"] = (df["steps_15min"] < 10).astype(int)
    df["moderate_activity"] = df["steps_15min"].between(10, 100).astype(int)
    df["high_activity"] = (df["steps_15min"] > 100).astype(int)
    df["high_calorie_burn"] = (df["calories_15min"] > 50).astype(int)

    return df


def _add_context_features(df: pd.DataFrame) -> pd.DataFrame:
    """Insulin and carbohydrate context features."""
    insulin = df.get("insulin", pd.Series(0.0, index=df.index)).fillna(0.0)
    carbs = df.get("carbs", pd.Series(0.0, index=df.index)).fillna(0.0)

    for name, w in [("30min", 30), ("60min", 60), ("120min", 120)]:
        df[f"insulin_{name}"] = insulin.rolling(w, min_periods=1).sum()
        df[f"carbs_{name}"] = carbs.rolling(w, min_periods=1).sum()

    df["recent_bolus"] = (insulin > 0).astype(int)
    df["recent_meal"] = (carbs > 5).astype(int)

    g = df["glucose"]
    df["insulin_glucose_ratio"] = df["insulin_60min"] / (g + 1.0)
    df["carbs_glucose_ratio"] = df["carbs_60min"] / (g + 1.0)

    return df


def _add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-feature interaction signals."""
    g = df["glucose"]
    vel = df["glucose_velocity"]

    # Insulin-carb balance
    df["insulin_carb_balance"] = df["insulin_60min"] - (df["carbs_60min"] / 10.0)

    # Hypo context: insulin active + low carbs + dropping
    df["hypo_context_signal"] = (
        (df["insulin_60min"] > 1).astype(int)
        & (df["carbs_60min"] < 10).astype(int)
        & (vel < 0).astype(int)
    ).astype(int)

    # Hyper context: high carbs + no insulin + rising
    df["hyper_context_signal"] = (
        (df["carbs_60min"] > 30).astype(int)
        & (df["insulin_60min"] < 1).astype(int)
        & (vel > 0).astype(int)
    ).astype(int)

    # Glucose per activity (normalized)
    df["glucose_per_calorie"] = g / (df["calories_60min"] + 1.0)
    df["glucose_hr_ratio"] = g / (df.get("hr_15min", pd.Series(70.0, index=df.index)) + 1.0)

    # Activity during drop
    df["glucose_drop_during_activity"] = (
        (df["glucose_dropping_fast"] == 1) & (df["high_activity"] == 1)
    ).astype(int)

    # HR spike without activity (possible hypoglycemia response)
    df["hr_spike_no_activity"] = (
        (df["hr_sudden_increase"] == 1) & (df["low_activity"] == 1)
    ).astype(int)

    # ── Hyper-specific continuous features ────────────────────────────
    # Magnitude of meal × rise × no-insulin signal (continuous, not binary)
    df["hyper_context_strength"] = (
        df["carbs_60min"] * vel.clip(lower=0)
    ) / (df["insulin_60min"] + 1.0)

    # Recent meal (30min) actively causing a glucose rise
    df["uncompensated_meal_rise"] = df["carbs_30min"] * vel.clip(lower=0)

    # Relative position within the safe glucose range [0=near hypo, 1=near hyper]
    df["glucose_safe_range_position"] = (g - 70.0) / 110.0

    # Dawn phenomenon: early-morning rise not explained by recent food
    df["dawn_hyper_risk"] = (
        ((df["hour"] >= 4) & (df["hour"] <= 8)).astype(float)
        * vel.clip(lower=0)
        / (df["carbs_60min"] + 1.0)
    )

    return df


def get_feature_columns(df: pd.DataFrame) -> list:
    """Return list of feature column names (excludes metadata and targets)."""
    exclude = {
        "patient_id", "time", "glucose", "dataset",
        "heart_rate", "steps", "calories", "carbs", "insulin",
        "target", "will_hypo", "will_hyper", "is_predictive",
    }
    return [c for c in df.columns if c not in exclude and df[c].dtype in [np.float64, np.int64, float, int]]


def prepare_training_matrix(df: pd.DataFrame) -> tuple:
    """
    Extract X (feature matrix) and y (target) from a features+targets DataFrame.

    Filters to only rows where is_predictive==1 (current glucose in normal range).
    Removes rows where target is NaN.

    Returns:
        (X, y, feature_names)
    """
    predictive = df[(df["is_predictive"] == 1) & df["target"].notna()].copy()

    if len(predictive) == 0:
        raise ValueError("No predictive rows found. Check preprocessing and target creation.")

    feature_names = get_feature_columns(predictive)
    X = predictive[feature_names].values.astype(np.float32)
    y = predictive["target"].values.astype(int)

    logger.info(
        "Training matrix: %d samples | class dist — Normal: %d, Hypo: %d, Hyper: %d",
        len(y),
        (y == 0).sum(), (y == 1).sum(), (y == 2).sum(),
    )
    return X, y, feature_names
