import pandas as pd
import numpy as np

# --- Configuration ---
NUM_ROWS = 4000  # Generate 4000 data points (1000 per approach)
JUNCTION_ID = 1
DIRECTIONS = ['North', 'South', 'East', 'West']
START_DATE = '2025-10-01 00:00:00'

# --- Generate Timestamps ---
# Create a timestamp for every 15 minutes for each of the 4 approaches
num_time_steps = NUM_ROWS // len(DIRECTIONS)
timestamps = pd.to_datetime(pd.date_range(start=START_DATE, periods=num_time_steps, freq='15min'))
timestamps = np.repeat(timestamps, len(DIRECTIONS))

# --- Create DataFrame ---
df = pd.DataFrame({
    'timestamp': timestamps
})

# --- Feature Engineering ---
df['junction_id'] = JUNCTION_ID
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['approach_direction'] = np.tile(DIRECTIONS, num_time_steps)

# --- Simulate Realistic Vehicle Counts ---
# Create a base traffic flow that peaks at rush hours (8-9 AM and 5-6 PM)
peak_hours = (np.sin(np.pi * (df['hour'] - 1.5) / 12) + 1) / 2
base_traffic = peak_hours * 80  # Max traffic of 80
# Add randomness to make it more realistic
random_noise = np.random.randint(-15, 15, size=NUM_ROWS)
df['vehicle_count'] = (base_traffic + random_noise).astype(int)
df['vehicle_count'] = df['vehicle_count'].clip(5) # Ensure a minimum of 5 vehicles

# --- Calculate Target Variable ---
# Create congestion score based on vehicle count, adding slight noise
df['congestion_score'] = (df['vehicle_count'] / 10) + np.random.normal(0, 0.5, size=NUM_ROWS)
df['congestion_score'] = df['congestion_score'].clip(0, 10).round(2) # Ensure score is between 0 and 10

# --- Save to CSV ---
output_filename = 'traffic_data_large.csv'
df.to_csv(output_filename, index=False)

print(f"Successfully generated a dataset with {NUM_ROWS} rows.")
print(f"File saved as '{output_filename}'")
print("\nDataset preview:")
print(df.head())