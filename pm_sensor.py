import serial
import struct
import paho.mqtt.client as mqtt
import time
import json
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone

# Serial connection details
SERIAL_PORT = "/dev/serial0"  # Use "/dev/ttyS0" if needed
BAUD_RATE = 9600
PM_THRESHOLD = 5  #for testing purpose, actual dangerous level is above 55

# MQTT details
MQTT_BROKER = "localhost"  # Change if using an external broker
MQTT_PORT = 1883
PM_STATUS_TOPIC = "sensor/pm_status"

CSV_FILE = "pm_readings.csv" # to save readings and generate graphs

# Setup MQTT client
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def on_message(client, userdata, msg):
    topic = msg.topic
    print(f"Received message on {topic}")

    if topic == "topic/getPM":
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
        df = df.sort_values(by="timestamp")
        last_5 = df.tail(5).to_dict(orient="records")

        # Convert Timestamp objects to strings
        for row in last_5:
            if isinstance(row["timestamp"], pd.Timestamp):
                row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        client.publish("sensor/pm_reading", json.dumps(last_5))
        print("Published last 5 PM readings to sensor/pm_reading")

    elif topic == "topic/getGraph/pm":
        df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
        df = df.sort_values(by="timestamp")
        df = df.tail(30)

        # Save graph
        plt.figure(figsize=(10, 5))
        plt.plot(df["timestamp"], df["pm2_5"], marker='o', linestyle='-')
        plt.title("PM2.5 Readings Over Time")
        plt.xlabel("Time")
        plt.ylabel("PM2.5 (ug/m3)")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("pm_graph.png")
        plt.close()

        with open("pm_graph.png", "rb") as f:
            image_data = f.read()
            client.publish("sensor/pm_graph", image_data)
            print("Published graph image to sensor/pm_graph")

client.on_message = on_message
client.subscribe("topic/getPM")
client.subscribe("topic/getGraph/pm")
client.loop_start()

# Create CSV file with headers if it doesn't exist
if not os.path.isfile(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "status", "pm2_5"])

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
    print("Listening for PMS5003 sensor data... Press Ctrl+C to stop.")

    while True:
        header = ser.read(2)
        if header == b'\x42\x4D':  # Valid header detected
            frame = ser.read(30)
            if len(frame) != 30:
                print("Error: Incomplete frame received. Skipping...")
                continue

            try:
                data = struct.unpack(">HHHHHHHHHHHHHH", frame[:28])  # Unpack 28 bytes
                pm2_5_atm = data[4]  # Extract PM2.5 (ATM)

                print("PM2.5 (ATM):", pm2_5_atm, "ug/m3")

                # Determine status based on PM2.5 threshold
                status = "HIGH" if pm2_5_atm > PM_THRESHOLD else "LOW"

                # Get current time in Singapore timezone (UTC+8)
                sg_time = datetime.now(timezone(timedelta(hours=8)))
                timestamp = sg_time.strftime("%Y-%m-%d %H:%M:%S")

                # Create JSON payload
                payload = {
                    "status": status,
                    "pm2_5": pm2_5_atm,
                    "timestamp": timestamp
                }

                # Publish PM2.5 status
                client.publish(PM_STATUS_TOPIC, json.dumps(payload))
                print(f"Published to {PM_STATUS_TOPIC}: {payload}")

                # Append readings to CSV file
                with open(CSV_FILE, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, status, pm2_5_atm])

            except struct.error:
                print("Error: Unable to unpack data. Skipping frame...")
                continue

        time.sleep(5)  # prints out readings every 5 seconds

except KeyboardInterrupt:
    print("Exiting...")
    ser.close()
