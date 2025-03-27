import pandas as pd
import time
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import paho.mqtt.client as mqtt


# MQTT Config
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
PREDICTION_TOPIC = "sensor/pm_prediction"

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

print(f"Model evaluation:\nMAE: {mae}, MSE: {mse}, R2: {r2}")

# Function to read the last 3 rows from sensor_readings.csv without relying on timestamp
def get_last_3_readings():
    sensor_df = pd.read_csv('sensor_readings.csv')
    last_3_readings = sensor_df[['national', 'year', 'month', 'day', 'hour']].tail(3).values.tolist()
    return last_3_readings


# Setup MQTT client
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def predict_pm25_realtime():
    last_3_readings = get_last_3_readings()

    updated_readings = []
    for r in last_3_readings:
        national, _, month, day, hour = r
        updated_readings.append([national, 2025, month, day, hour])

    feature_input_flat = np.array([np.array(updated_readings).flatten()])
    predicted = model.predict(feature_input_flat)[0]

    print(f"\nPredicted PM2.5 for next 5 hour(s): {predicted:.2f}")

    if predicted > 10:
        print("PM2.5 is predicted to rise. Sending warning to MQTT...")
        payload = f"{predicted:.2f}"
        client.publish(PREDICTION_TOPIC, payload)



# Run the prediction every 10 seconds in an infinite loop
while True:
    predict_pm25_realtime()
    time.sleep(10)

