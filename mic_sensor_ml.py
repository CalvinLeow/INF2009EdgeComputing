import numpy as np
import pandas as pd
import joblib
import time
import paho.mqtt.client as mqtt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# MQTT Config
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_TOPIC_RETRAIN = "audio/retrain"
MQTT_TOPIC_ALERT = "sensor/SoundAlert"
PREDICTION_TOPIC = "sensor/sound_prediction"

# CSV file path & model filename
CSV_FILE = "audio_logs/audio_log.csv"
MODEL_FILE = "db_model_regression.pkl"

def train_model():
    """Trains the regression model and saves it."""
    print("Retraining regression model...")
    try:
        data = pd.read_csv(CSV_FILE)
        required_columns = ['Actual SPL (dB)', 'Rate of Change', 'Timestamp']
        
        if not all(col in data.columns for col in required_columns):
            print("Missing required columns in CSV.")
            return

        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Minutes'] = (data['Timestamp'] - data['Timestamp'].min()).dt.total_seconds() / 60
        
        feature_cols = ['Actual SPL (dB)', 'Rate of Change', 'Minutes']
        X, y = create_lag_features(data[feature_cols], window=3, horizon=5)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        joblib.dump(model, MODEL_FILE)
        
        model = joblib.load(MODEL_FILE)
        print(model)
        
        y_pred = model.predict(X_test)
        print(f"Model evaluation: MAE: {mean_absolute_error(y_test, y_pred):.2f}, MSE: {mean_squared_error(y_test, y_pred):.2f}, R2: {r2_score(y_test, y_pred):.2f}")
        
    except Exception as e:
        print(f"Error during training: {str(e)}")
    predict_time_to_50dB()

def create_lag_features(df, window=3, horizon=5):
    X, y = [], []
    for i in range(len(df) - window - horizon):
        chunk = df.iloc[i:i + window].values.flatten()
        X.append(chunk)
        y.append(df.iloc[i + window + horizon]['Actual SPL (dB)'])
    return pd.DataFrame(X), pd.Series(y)

def get_last_3_readings():
    data = pd.read_csv(CSV_FILE)
    
    if 'Timestamp' in data.columns:
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Minutes'] = (data['Timestamp'] - data['Timestamp'].min()).dt.total_seconds() / 60
    else:
        print("Error: 'Timestamp' column missing in CSV file.")
        return []
    
    return data[['Actual SPL (dB)', 'Rate of Change', 'Minutes']].tail(3).values.tolist()


def predict_time_to_50dB():
    print("Do forecastin")
    print(get_last_3_readings())
    try:
        model = joblib.load(MODEL_FILE)
        last_3_readings = get_last_3_readings()
        
        input_data = np.array([np.array(last_3_readings).flatten()])
        predicted_time = 0
        
        while input_data[0, 0] < 50:
            predicted_spl = model.predict(input_data)[0]
            predicted_time += 1  # Increase time step
            input_data[0, 2] += 1  # Update time feature
            input_data[0, 0] = predicted_spl  # Update SPL value

            if predicted_time > 120:  # Limit to 2 hours max
                print("Prediction too far in the future, aborting.")
                return
        
        message = f"SPL predicted to exceed 50 dB in {predicted_time} minutes."
        client.publish(MQTT_TOPIC_ALERT, message)
        print(f"MQTT Alert sent: {message}")
        client.publish(PREDICTION_TOPIC, message)
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC_RETRAIN and msg.payload.decode() == "Retrain model":
        train_model()

# MQTT Client Setup
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC_RETRAIN)

print("Listening for retrain requests...")

# Run prediction loop
#time.sleep(5)
#while True:
 #   predict_time_to_50dB()
  #  time.sleep(10)

client.loop_forever()
