# train_model.py

# --- Step 1: Import Necessary Libraries ---
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

print("Script started...")

# --- Step 2: Load the Dataset ---
DATASET_PATH = './csv_generator/traffic_data_large.csv'

if not os.path.exists(DATASET_PATH):
    print(f"Error: Dataset not found at '{DATASET_PATH}'")
    print("Please make sure you have generated the dataset and it is in the same folder as this script.")
    exit()

print(f"Loading dataset from '{DATASET_PATH}'...")
df = pd.read_csv(DATASET_PATH)

# --- Step 3: Feature Engineering & Preparation ---
# We will use these columns to predict the 'congestion_score'
features = ['hour', 'day_of_week', 'vehicle_count']
target = 'congestion_score'

X = df[features]
y = df[target]

print("Features and target variable prepared.")
print(f"Shape of features (X): {X.shape}")
print(f"Shape of target (y): {y.shape}")

# --- Step 4: Split Data into Training and Testing Sets ---
# We'll use 80% of the data for training and 20% for testing.
# random_state ensures we get the same split every time, making our results reproducible.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Data split into training and testing sets.")

# --- Step 5: Initialize and Train the Random Forest Model ---
# n_estimators is the number of decision trees in the forest.
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1) # n_jobs=-1 uses all available CPU cores

print("Training the Random Forest model... (This might take a moment)")
model.fit(X_train, y_train)
print("Model training complete.")

# --- Step 6: Evaluate the Model ---
print("Evaluating model performance on the test set...")
y_pred = model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
# This tells you, on average, how far off the model's predictions are from the actual values.
mae = mean_absolute_error(y_test, y_pred)
print(f"Mean Absolute Error (MAE): {mae:.2f}")

# Calculate R-squared (R²)
# This tells you what proportion of the variance in the target is predictable from the features.
# A score closer to 1.0 is better.
r2 = r2_score(y_test, y_pred)
print(f"R-squared (R²): {r2:.2f}")

# --- Step 7: Save the Trained Model ---
MODEL_FILENAME = 'traffic_model.joblib'
joblib.dump(model, MODEL_FILENAME)

print(f"\nModel successfully trained and saved as '{MODEL_FILENAME}'")
print("You can now use this file in your backend application to make predictions.")