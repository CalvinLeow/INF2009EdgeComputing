# %%
import pandas as pd
import time
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load the dataset
df = pd.read_csv('psi_df_2016_2019.csv')

# Load the sensor data
sensor_df = pd.read_csv('sensor_readings.csv', on_bad_lines='skip')

# Convert the 'timestamp' column to datetime format
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Concatenate the new data with the existing DataFrame
df = pd.concat([df, sensor_df], ignore_index=True)

# Extract useful time-based features
df['year'] = df['timestamp'].dt.year
df['month'] = df['timestamp'].dt.month
df['day'] = df['timestamp'].dt.day
df['hour'] = df['timestamp'].dt.hour

# Display the first few rows of the dataset to check the features
df.head()


# %%
# Create lag features from 3 previous readings to predict 5 hours ahead
def create_lag_features(df, window=3, horizon=5):
    X, y = [], []
    for i in range(len(df) - window - horizon):
        chunk = df.iloc[i:i + window].values.flatten()
        X.append(chunk)
        y.append(df.iloc[i + window + horizon]['national'])
    return pd.DataFrame(X), pd.Series(y)

# Use only selected features
feature_cols = ['national', 'year', 'month', 'day', 'hour']
X, y = create_lag_features(df[feature_cols], window=3, horizon=5)

# %%
# Split into training (80%) and testing (20%) sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a Random Forest model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate model performance
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# Display evaluation metrics
print(f"MAE: {mae}, MSE: {mse}, R2: {r2}")

# %%
# Visualize actual vs predicted values
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color='red', linestyle='--', label="Ideal Prediction")
plt.xlabel('Actual PM2.5 Levels')
plt.ylabel('Predicted PM2.5 Levels')
plt.title('Actual vs Predicted PM2.5 Levels for Next 5 Hour(s)')
plt.legend()
plt.grid(True)
plt.show()

# %%
# Function to read the last 3 rows from sensor_readings.csv without relying on timestamp
def get_last_3_readings():
    # Read the sensor readings CSV file
    sensor_df = pd.read_csv('sensor_readings.csv')

    # Assuming that the most recent readings are at the end of the file
    # Get the last 3 readings (if available)
    last_3_readings = sensor_df[['national', 'year', 'month', 'day', 'hour']].tail(3).values.tolist()
    
    return last_3_readings

# Real-time prediction logic using last 3 readings
def predict_pm25_realtime():
    # Get the last 3 readings from the sensor_readings.csv
    last_3_readings = get_last_3_readings()

    # Initialize the feature set with the last 3 readings
    feature_input = []

    # Append each reading's national, month, day, hour
    for reading in last_3_readings:
        national, year, month, day, hour = reading
        # Prepare a feature row with national, year, month, day, hour
        year = 2025  # or use datetime.now().year if needed
        feature_row = [national, year, month, day, hour]
        feature_input.append(feature_row)

    # Flatten the feature input for prediction
    feature_input_flat = pd.DataFrame([sum(feature_input, [])])

    # Predict PM2.5 level using the feature input
    predicted = model.predict(feature_input_flat)[0]

    print(f"\nPredicted PM2.5 for next 5 hour(s): {predicted:.2f}")
    
    if predicted > 50:
        print("⚠️ Dangerous levels are predicted! Please wear your mask now! ⚠️")


# %%
# Run the prediction every 10 seconds in an infinite loop
while True:
    predict_pm25_realtime()  # Call the real-time prediction function
    time.sleep(10)  # Wait for 10 seconds before running the function again


