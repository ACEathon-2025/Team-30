import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
import joblib

# Load your dataset
DATA_PATH = "ML/csv_generator/traffic_data_large.csv"
data = pd.read_csv(DATA_PATH)

# Select features and target
features = data[['vehicle_count']]
target = data['congestion_score']

# Optional: balance the dataset if needed
# (Example: undersample dominant low congestion scores or oversample sparse ranges)
# For now, we'll just proceed with full data.

# Split data
X_train, X_val, y_train, y_val = train_test_split(features, target, test_size=0.2, random_state=42)

# Model and hyperparameter grid for tuning
model = RandomForestRegressor(random_state=42)
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2]
}

grid_search = GridSearchCV(model, param_grid, cv=3, scoring='r2', n_jobs=-1, verbose=2)
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_

# Evaluate best model
print("Best hyperparameters:", grid_search.best_params_)
print("Training R2 score:", best_model.score(X_train, y_train))
print("Validation R2 score:", best_model.score(X_val, y_val))

# Save the best model
MODEL_PATH = "ML/traffic_model.joblib"
joblib.dump(best_model, MODEL_PATH)
print("Retrained model saved at:", MODEL_PATH)
