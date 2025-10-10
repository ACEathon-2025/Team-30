import pandas as pd
import numpy as np

# Configuration 
NUM_ROWS = 4000 
JUNCTION_ID = 1
DIRECTIONS = ['North', 'South', 'East', 'West']
START_DATE = '2025-10-01 00:00:00'

# Generate Timestamps 
num_time_steps = NUM_ROWS // len(DIRECTIONS)
timestamps = pd.to_datetime(pd.date_range(start=START_DATE, periods=num_time_steps, freq='15min'))
timestamps = np.repeat(timestamps, len(DIRECTIONS))

df = pd.DataFrame({
    'timestamp': timestamps
})

df['junction_id'] = JUNCTION_ID
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['approach_direction'] = np.tile(DIRECTIONS, num_time_steps)

peak_hours = (np.sin(np.pi * (df['hour'] - 1.5) / 12) + 1) / 2
base_traffic = peak_hours * 80  

random_noise = np.random.randint(-15, 15, size=NUM_ROWS)
df['vehicle_count'] = (base_traffic + random_noise).astype(int)
df['vehicle_count'] = df['vehicle_count'].clip(5)

df['congestion_score'] = (df['vehicle_count'] / 10) + np.random.normal(0, 0.5, size=NUM_ROWS)
df['congestion_score'] = df['congestion_score'].clip(0, 10).round(2)

output_filename = 'traffic_data_large.csv'
df.to_csv(output_filename, index=False)

print(f"Successfully generated a dataset with {NUM_ROWS} rows.")
print(f"File saved as '{output_filename}'")
print("\nDataset preview:")
print(df.head())