import paho.mqtt.client as mqtt
import json
import time

# MQTT setup
broker = "localhost"
port = 1883

client = mqtt.Client()
client.connect(broker, port, 60)

# Simulate sending HIGH PM2.5 status
pm_payload = {
    "status": "HIGH",
    "pm2_5": 150
}
client.publish("sensor/pm_status", json.dumps(pm_payload))
print("Sent HIGH PM2.5 message")

# Simulate sending HIGH noise status (optional)
client.publish("sensor/noise_status", "HIGH")
print("Sent HIGH noise status")

client.disconnect()
