import numpy as np
import pandas as pd
import joblib
import paho.mqtt.client as mqtt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import datetime

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_RETRAIN = "audio/retrain"
MQTT_TOPIC_ALERT = "sensor/SoundAlert"

# CSV file path & model filename
CSV_FILE = "audio_logs/audio_log.csv"
MODEL_FILE = "db_model_regression.pkl"

def train_model():
    """Trains the regression model and saves it."""
    print("Retraining regression model...")

    try:
        # Load CSV file
        data = pd.read_csv(CSV_FILE)

        # Ensure required columns exist
        required_columns = ['Actual SPL (dB)', 'Rate of Change', 'Timestamp']
        for col in required_columns:
            if col not in data.columns:
                print(f"Missing column in CSV: {col}")
                return

        # Convert timestamp to minutes
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Minutes'] = (data['Timestamp'] - data['Timestamp'].min()).dt.total_seconds() / 60

        # Define features & target variable
        X = data[['Actual SPL (dB)', 'Rate of Change', 'Minutes']]
        y = data['Actual SPL (dB)'].shift(-1)  # Predicting for the next minute

        # Remove NaN values (last entry may have NaN)
        X, y = X[:-1], y[:-1]

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Save the trained model
        joblib.dump(model, MODEL_FILE)
        print(f"Model saved as {MODEL_FILE}")

        # Calculate and print model error
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"Model Mean Squared Error: {mse:.2f}")

        # After training, predict time until SPL exceeds 50 dB
        predict_time_to_50dB(model)

    except Exception as e:
        print(f"Error during training: {str(e)}")

def predict_time_to_50dB(model):
    """Predicts how long it will take for SPL to exceed 50 dB."""
    try:
        # Load data from CSV
        data = pd.read_csv(CSV_FILE)

        if data.empty:
            print("No data available for prediction.")
            return

        # Use the latest measurement as the starting point for prediction
        latest_data = data.iloc[-1].copy()
        spl_current = latest_data['Actual SPL (dB)']
        rate_of_change = latest_data['Rate of Change']
        minutes_current = latest_data['Timestamp']

        # Ensure Timestamp is correctly formatted
        latest_data['Timestamp'] = pd.to_datetime(latest_data['Timestamp'])
        minutes_current = (latest_data['Timestamp'] - data['Timestamp'].min()).total_seconds() / 60

        # Prepare initial input for prediction
        input_data = np.array([[spl_current, rate_of_change, minutes_current]])

        # Stepwise prediction until SPL exceeds 50 dB
        predicted_time = 0
        while input_data[0, 0] < 50:
            predicted_spl = model.predict(input_data)[0]
            predicted_time += 1  # Move 1 minute into the future
            input_data[0, 2] += 1  # Increase time step
            input_data[0, 0] = predicted_spl  # Update SPL value

            if predicted_time > 120:  # Limit prediction to a maximum of 2 hours
                print("Prediction too far in the future, aborting.")
                return

        # Time until exceeding 50 dB calculated -> send alert message
        message = f"SPL predicted to exceed 50 dB in {predicted_time} minutes."
        client.publish(MQTT_TOPIC_ALERT, message)
        print(f"MQTT Alert sent: {message}")

    except Exception as e:
        print(f"Error during prediction: {str(e)}")

def on_message(client, userdata, msg):
    """Callback function triggered by incoming MQTT messages."""
    if msg.topic == MQTT_TOPIC_RETRAIN and msg.payload.decode() == "Retrain model":
        train_model()

# Set up MQTT client
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC_RETRAIN)

print("Listening for retrain requests...")
client.loop_forever()
