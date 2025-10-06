# predictor.py

# --- Step 1: Import Necessary Libraries ---
import joblib
import sys
import datetime
import os
import numpy as np
import pandas as pd


# --- Step 2: Define the Green Light Calculation Logic ---
# This function converts the model's prediction (a score from 0-10)
# into a practical green light duration in seconds.
def calculate_green_time(congestion_score):
    """
    Calculates the green light duration based on a congestion score.
    Maps a score of 0-10 to a time of 10-60 seconds.
    """
    MIN_GREEN_TIME = 10  # seconds
    MAX_GREEN_TIME = 60  # seconds

    # Ensure the score is within the expected 0-10 range
    congestion_score = max(0, min(10, congestion_score))

    # Linearly map the score to the time range
    green_time = MIN_GREEN_TIME + (congestion_score / 10) * (MAX_GREEN_TIME - MIN_GREEN_TIME)
    
    # Return the result as an integer
    return int(green_time)

# --- Step 3: Main Execution Block ---
if __name__ == "__main__":
    
    # --- Input Validation ---
    # Check if the vehicle_count argument was provided
    if len(sys.argv) != 2:
        print("Error: Please provide the vehicle count as an argument.")
        print("Usage: python predictor.py <vehicle_count>")
        sys.exit(1)

    try:
        vehicle_count = int(sys.argv[1])
    except ValueError:
        print("Error: Vehicle count must be an integer.")
        sys.exit(1)

    # --- Load the Trained Model ---
    MODEL_FILENAME = os.path.join(os.path.dirname(__file__), 'traffic_model.joblib')
    if not os.path.exists(MODEL_FILENAME):
        print(f"Error: Model file '{MODEL_FILENAME}' not found.", file=sys.stderr)
        print("Please run the train_model.py script first.", file=sys.stderr)
        sys.exit(1)

    model = joblib.load(MODEL_FILENAME)

    # --- Prepare Input Data for Prediction ---
    # The model was trained on ['hour', 'day_of_week', 'vehicle_count'].
    # We need to provide the data in the same order.
    now = datetime.datetime.now()
    current_hour = now.hour
    current_day_of_week = now.weekday() # Monday=0, Sunday=6

    # Create the input array for the model's predict function
    # Note: The model expects a 2D array-like input, so we wrap it in a list.
    input_features = pd.DataFrame(
    [[current_hour, current_day_of_week, vehicle_count]],
    columns=['hour', 'day_of_week', 'vehicle_count']
)

    # --- Make the Prediction ---
    predicted_congestion_score = model.predict(input_features)[0] # Get the first (and only) prediction

    # --- Calculate Green Light Time ---
    green_light_duration = calculate_green_time(predicted_congestion_score)

    # --- Output the Final Result ---
    # This is the most important line. The Node.js script will read this output.
    print(green_light_duration)