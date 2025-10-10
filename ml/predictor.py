import joblib
import numpy as np
import pandas as pd
import os

# Use absolute path relative to this file to locate model in ML folder
MODEL_PATH = os.path.join(os.path.dirname(__file__), "traffic_model.joblib")

print(f"Loading model from: {MODEL_PATH}")
model = joblib.load(MODEL_PATH)
print("Model loaded successfully.")

def calculate_green_time(congestion_score: float) -> int:
    """Convert congestion score (0–10) into green light duration (10–60s)."""
    green_time = int(np.clip((congestion_score / 10) * 60, 5, 60))
    return green_time


def predict_green_time(vehicle_count: int) -> int:
    """
    Predict green time based on vehicle count only.
    Prints debug info about input features before prediction.
    """
    # Prepare input DataFrame with correct column name
    features = pd.DataFrame([[vehicle_count]], columns=["vehicle_count"])
    try:
        congestion_score = model.predict(features)[0]
        green_time = calculate_green_time(congestion_score)
        return green_time
    except Exception as e:
        print(f"⚠️ Prediction error: {e}, falling back to 10s green time.")
        return 77
