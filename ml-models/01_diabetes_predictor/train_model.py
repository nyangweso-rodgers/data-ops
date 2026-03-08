
# train_model.py
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import os


# Load the diabetes dataset
diabetes = load_diabetes()
X, y = diabetes.data, diabetes.target
 
print(f"Dataset shape: {X.shape}")
print(f"Features: {diabetes.feature_names}")
print(f"Target range: {y.min():.1f} to {y.max():.1f}")

# Prepare the data

# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
 
print(f"Training samples: {X_train.shape[0]}")
print(f"Test samples: {X_test.shape[0]}")

# Traing the model

# Train Random Forest model
"""
We’ve set max_depth=10 to prevent overfitting on this relatively small dataset. With 100 trees, we get good performance without excessive computation time.
"""
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    max_depth=10
)
 
model.fit(X_train, y_train)

# Evaluate the model
# Make predictions and evaluate
""""
The R² score tells what percentage of variance in disease progression our model explains. Anything above 0.4 is pretty good for this dataset!
"""
y_pred = model.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse:.2f}")
print(f"R² Score: {r2:.3f}")

# Save the trained model
# Create models directory and save model
os.makedirs('models', exist_ok=True)

with open('models/diabetes_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")