import os
import time
import json
import csv
import paho.mqtt.client as mqtt
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# MQTT Konfiguration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
SOUND_LEVEL_TOPIC = "topic/getSound"
GRAPH_TOPIC = "topic/getGraph/sound"

# CSV Datei
CSV_FILE = "audio_logs/audio_log.csv"
GRAPH_FILE = "audio_logs/audio_plot.png"



def get_latest_sound_level():
    print("sound requesting via mqtt")
    try:
        df = pd.read_csv(CSV_FILE)
        latest_row = df.iloc[-1]  # Letzte Zeile
        sound_level = latest_row["Actual SPL (dB)"]
        timestamp = latest_row["Timestamp"]
        return {"sound_level": sound_level, "timestamp": timestamp}
    except Exception as e:
        return {"error": str(e)}

def generate_sound_graph():
    try:
        df = pd.read_csv(CSV_FILE)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values(by='Timestamp')
        
        plt.figure(figsize=(10, 5))
        plt.plot(df['Timestamp'], df['Actual SPL (dB)'], label='SPL (dB)', color='b')
        plt.xlabel('Time')
        plt.ylabel('Decibel (dB)')
        plt.title('Sound Level Over Time')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid()
        
        plt.savefig(GRAPH_FILE, bbox_inches='tight')
        plt.close()
        return GRAPH_FILE
    except Exception as e:
        return None

def on_message(client, userdata, msg):
    topic = msg.topic
    print(f"Received message on {topic}")

    if topic == SOUND_LEVEL_TOPIC:
        latest_sound = get_latest_sound_level()
        client.publish("sensor/sound_reading", json.dumps(latest_sound))
        print("Published latest sound level to sensor/sound_reading")
    
    elif topic == GRAPH_TOPIC:
        image_path = generate_sound_graph()
        if image_path:
            with open(image_path, "rb") as f:
                image_data = f.read()
                client.publish("sensor/sound_graph", image_data)
                print("Published sound graph to sensor/sound_graph")

# MQTT Client Setup
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.on_message = on_message
client.subscribe(SOUND_LEVEL_TOPIC)
client.subscribe(GRAPH_TOPIC)
client.subscribe([(GRAPH_TOPIC, 0), (SOUND_LEVEL_TOPIC, 0)])

print("MQTT Listener running.")

client.loop_forever()
