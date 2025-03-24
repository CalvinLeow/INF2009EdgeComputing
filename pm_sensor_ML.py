# %%
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load the dataset
df = pd.read_csv('psi_df_2016_2019.csv')

# Convert the 'timestamp' column to datetime format
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Extract useful time-based features
df['year'] = df['timestamp'].dt.year
df['month'] = df['timestamp'].dt.month
df['day'] = df['timestamp'].dt.day
df['hour'] = df['timestamp'].dt.hour
df['weekday'] = df['timestamp'].dt.weekday  # Add weekday for potential weekly patterns

# Drop any rows with NaN values from rolling averages (first few rows will have NaN due to rolling)
df = df.dropna()

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
# Real-time prediction logic using up to 3 past readings
past_readings = []

def predict_pm25_realtime(new_sensor_reading):
    """
    Use up to 3 recent readings to predict PM2.5 level.
    new_sensor_reading: [national, month, day, hour]
    """
    global past_readings
    national, month, day, hour = new_sensor_reading
    year = 2025  # or use datetime.now().year

    reading = [national, year, month, day, hour]
    past_readings.append(reading)

    # Keep only the latest 3 readings
    if len(past_readings) > 3:
        past_readings = past_readings[-3:]

    # Pad with oldest reading if fewer than 3
    padded = past_readings.copy()
    while len(padded) < 3:
        padded.insert(0, padded[0])

    # Flatten to single feature row
    feature_input = pd.DataFrame([sum(padded, [])])

    predicted = model.predict(feature_input)[0]
    print(f"\nPredicted PM2.5 for next 5 hour(s): {predicted:.2f}")

    if predicted > 50:
        print("⚠️ Dangerous levels are predicted! Please wear your mask now! ⚠️")

    return predicted

# %%
# Example real-time prediction usage
predict_pm25_realtime([30, 3, 24, 15]) # [PM2.5 Level, month, day, hour]
predict_pm25_realtime([45, 3, 24, 16])
predict_pm25_realtime([60, 3, 24, 17])
predict_pm25_realtime([70, 3, 24, 18])  # This will use the latest 3 readings


