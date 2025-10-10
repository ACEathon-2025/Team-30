# ML/predictor.py
import joblib
import numpy as np
from datetime import datetime

MODEL_PATH = "ML/traffic_model.joblib"

# Load the trained model once
model = joblib.load(MODEL_PATH)

def calculate_green_time(congestion_score: float) -> int:
    """
    Convert predicted congestion score (0–10) into green light duration (10–60s)
    """
    return int(np.clip((congestion_score / 10) * 60, 10, 60))

def predict_green_time(vehicle_count: int) -> int:
    """
    Predict green time based on vehicle count and current time/day
    """
    now = datetime.now()
    hour = now.hour
    day = now.weekday()  # Monday = 0, Sunday = 6

    # Input features
    features = np.array([[vehicle_count, hour, day]])
    congestion_score = model.predict(features)[0]
    green_time = calculate_green_time(congestion_score)

    return green_time
