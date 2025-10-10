import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

# === Step 1: Load your dataset ===
# Replace with your actual dataset path
DATA_PATH = "ML/csv_generator/traffic_data_large.csv"

data = pd.read_csv(DATA_PATH)

# === Step 2: Prepare features and target ===
# Use only 'vehicle_count' as feature
features = data[['vehicle_count']]  # Ensure this column exists in your CSV
target = data['congestion_score']   # Replace with your actual target column name

# === Step 3: Split dataset into train and validation sets ===
X_train, X_val, y_train, y_val = train_test_split(
    features, target, test_size=0.2, random_state=42
)

# === Step 4: Train Random Forest Regressor ===
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# === Step 5: Evaluate model performance ===
print("Training R2 score:", model.score(X_train, y_train))
print("Validation R2 score:", model.score(X_val, y_val))

# === Step 6: Save the trained model ===
MODEL_PATH = "ML/traffic_model.joblib"
joblib.dump(model, MODEL_PATH)
print("Model retrained and saved at", MODEL_PATH)
