import numpy as np
import sounddevice as sd
import datetime
import csv
import os
import paho.mqtt.client as mqtt
import time
import json

# Konfiguration
MQTT_BROKER = "172.20.10.2"
MQTT_PORT = 1883
MQTT_TOPIC_RETRAIN = "audio/retrain"  
MQTT_TOPIC_ALERT = "sensor/SoundAlert" 
NOISE_STATUS_ALERT = "sensor/noise_status" 
MAX_LOG_ENTRIES = 1000  
DELETE_ENTRIES = 100  

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

samplerate = 44100
frame_length = 2048

# Log-Datei
log_folder = "audio_logs"
os.makedirs(log_folder, exist_ok=True)
log_filename = os.path.join(log_folder, "audio_log.csv")

if not os.path.exists(log_filename):
    with open(log_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Actual SPL (dB)", "Rate of Change", "Label (1=problematic,0=not problematic)", "Target Value"])

warning_sent = False
alert_sent = False
prev_spl_actual = None  # vorheriger SPL-Wert

def maintain_log_size():
    with open(log_filename, mode='r', newline='') as file:
        lines = file.readlines()
    
    if len(lines) > MAX_LOG_ENTRIES:
        with open(log_filename, mode='w', newline='') as file:
            file.writelines(lines[:1] + lines[(DELETE_ENTRIES + 1):])  
        
        client.publish(MQTT_TOPIC_RETRAIN, "Retrain model")
        print("MQTT: Retrain model message sent")

def audio_callback(indata, frames, time_info, status):
    global warning_sent, alert_sent, prev_spl_actual
    
    if status:
        print(status)

    y = np.mean(indata, axis=1)
    rms = np.sqrt(np.mean(y**2))
    spl_actual = 20 * np.log10(rms + 1e-12) + 60

    roc = 0.0 if prev_spl_actual is None else spl_actual - prev_spl_actual
    prev_spl_actual = spl_actual

    # Label
    label = 1 if spl_actual >= 55 else 0

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, spl_actual, roc, label, spl_actual])  # spl_actual als Target Value speichern

    maintain_log_size()

   # print(f"{timestamp} | actual: {spl_actual:.2f} dB | RoC: {roc:.2f} | label: {label}")
    # Alert at 50 dB
    if spl_actual > 50 and alert_sent == False:
        noise_payload = {
            "status": "HIGH",
            "db": round(float(spl_actual), 2),
            "timestamp": timestamp
            }
        client.publish(NOISE_STATUS_ALERT, json.dumps(noise_payload))
        #client.publish(MQTT_TOPIC_ALERT, f"Alert, decibel reached now {spl_actual:.2f} dB")
        alert_sent = True
        print("Alert sent: SPL over 50 dB")
    
    elif spl_actual <= 50 and alert_sent == True:
        noise_payload = {
            "status": "LOW",
            "db": round(float(spl_actual), 2),
            "timestamp": timestamp
            }
        #client.publish(MQTT_TOPIC_ALERT, "Everything clear. Decibel is now {spl_actual:.2f} dB")
        client.publish(NOISE_STATUS_ALERT, json.dumps(noise_payload))
        alert_sent = False  
        print("Clear message sent")
    print(spl_actual)
    #time.sleep(0.5)
with sd.InputStream(callback=audio_callback, channels=1, samplerate=samplerate, blocksize=frame_length):
    print("Audio monitoring is running. Stop with Ctrl+C.")
    while True:
        sd.sleep(100)
