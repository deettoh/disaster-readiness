"""Inference module for the risk imputation model.

Loads a trained XGBoost model and predicts vulnerability scores
for grid cells from a feature CSV.
"""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path("ai/imputation/models/vulnerability_model.joblib")
DEFAULT_FEATURES_PATH = Path("data/processed/imputation_features.csv")
DEFAULT_PREDICTIONS_PATH = Path("ai/imputation/artifacts/cell_predictions.csv")

FEATURE_COLS = [
    "mean_elevation",
    "mean_slope",
    "dist_to_river_m",
    "dist_to_hotspot_m",
    "road_density",
    "travel_time_to_shelter_s",
]


def load_model(model_path: Path) -> object:
    """Load the trained XGBoost model from a joblib file."""
    if not model_path.exists():
        msg = f"Model file not found: {model_path}"
        raise FileNotFoundError(msg)
    model = joblib.load(model_path)
    logger.info("Loaded model from %s", model_path)
    return model


def predict_vulnerability(
    model: object,
    features_path: Path,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Run inference on feature data and return predictions.

    Args:
        model: Trained XGBoost model.
        features_path: Path to the feature CSV with one row per cell.
        output_path: Optional path to save predictions CSV.

    Returns:
        DataFrame with columns [cell_id, predicted_vulnerability].
    """
    if not features_path.exists():
        msg = f"Features file not found: {features_path}"
        raise FileNotFoundError(msg)

    df = pd.read_csv(features_path)
    logger.info("Loaded %d cells from %s", len(df), features_path)

    X = df[FEATURE_COLS].fillna(0).values

    raw_predictions = model.predict(X)
    predictions = np.clip(raw_predictions, 0.0, 1.0)

    result = pd.DataFrame(
        {
            "cell_id": df["cell_id"].astype(int),
            "predicted_vulnerability": predictions.round(4),
        }
    )

    logger.info(
        "Predictions: min=%.4f, max=%.4f, mean=%.4f",
        predictions.min(),
        predictions.max(),
        predictions.mean(),
    )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False)
        logger.info("Saved predictions to %s", output_path)

    return result


def run_inference(
    project_root: Path,
    model_path: Path | None = None,
    features_path: Path | None = None,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """End-to-end inference: load model, predict, save results.

    Args:
        project_root: Project root directory.
        model_path: Path to model file. Defaults to standard location.
        features_path: Path to features CSV. Defaults to standard location.
        output_path: Path to save predictions. Defaults to standard location.

    Returns:
        DataFrame with predictions.
    """
    _model_path = model_path or (project_root / DEFAULT_MODEL_PATH)
    _features_path = features_path or (project_root / DEFAULT_FEATURES_PATH)
    _output_path = output_path or (project_root / DEFAULT_PREDICTIONS_PATH)

    model = load_model(_model_path)
    return predict_vulnerability(model, _features_path, _output_path)
